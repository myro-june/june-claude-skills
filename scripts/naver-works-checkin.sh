#!/bin/bash
# 네이버 웍스(LINE WORKS) 출근 자동화 스크립트
# Chrome AppleScript를 이용하여 기존 로그인 세션으로 출근 버튼 클릭
# macOS 전용

result=$(osascript <<'APPLESCRIPT'
-- Chrome이 실행 중인지 확인하고, 아니면 실행
if application "Google Chrome" is not running then
    tell application "Google Chrome" to activate
    delay 3
end if

try
    -- 타임아웃 설정 (초 단위, 최악의 경우 총 약 56초: Chrome 기동 3 + 페이지 15 + 위젯 15 + 렌더링 1 + 통합폴링 20 + 탭닫기 1)
    set pageLoadTimeout to 15
    set widgetTimeout to 15
    set popupTimeout to 10
    set verifyTimeout to 10

    tell application "Google Chrome"
        activate

        -- Chrome이 방금 실행되었거나 창이 없는 경우
        if (count of windows) = 0 then
            make new window
            delay 1
        end if

        -- 새 탭에서 네이버 웍스 홈 열기
        tell front window
            make new tab with properties {URL:"https://home.worksmobile.com"}
        end tell

        -- 페이지 로드 대기
        set maxWait to pageLoadTimeout
        set waited to 0
        repeat while waited < maxWait
            delay 1
            set waited to waited + 1
            tell active tab of front window
                set pageState to (execute javascript "document.readyState")
            end tell
            if pageState is "complete" then exit repeat
        end repeat

        -- 페이지 로드 타임아웃 체크
        if pageState is not "complete" then
            tell front window to close active tab
            return "FAIL: 페이지가 15초 내에 로드되지 않았습니다. 네트워크 상태를 확인해 주세요."
        end if

        -- SPA 위젯 렌더링 대기 (출근/퇴근 버튼이 나타날 때까지)
        set widgetReady to false
        set widgetWait to 0
        repeat while widgetWait < widgetTimeout
            delay 1
            set widgetWait to widgetWait + 1
            tell active tab of front window
                set hasWidget to (execute javascript "
                    (function() {
                        var btns = document.querySelectorAll('button, a, div[role=button]');
                        for (var i = 0; i < btns.length; i++) {
                            var t = btns[i].textContent.trim();
                            if (t === '출근' || t === '퇴근') return 'YES';
                        }
                        return 'NO';
                    })()
                ")
            end tell
            if hasWidget is "YES" then
                set widgetReady to true
                exit repeat
            end if
        end repeat

        -- 위젯 로드 타임아웃 체크
        if widgetReady is false then
            tell front window to close active tab
            return "FAIL: 근태 위젯이 15초 내에 로드되지 않았습니다. 네트워크 상태를 확인해 주세요."
        end if

        -- 추가 렌더링 대기
        delay 1

        -- 출근 상태 확인 및 처리
        tell active tab of front window
            set checkinResult to (execute javascript "
                (function() {
                    // 상태 텍스트('출근 09:30')는 span 등 비인터랙티브 요소에 렌더링될 수 있어 넓은 셀렉터 사용
                    var allEls = document.querySelectorAll('button, a, div, span');

                    // 1단계: 이미 출근했는지 확인 ('출근 HH:MM' 패턴)
                    for (var i = 0; i < allEls.length; i++) {
                        var text = allEls[i].textContent.trim();
                        var match = text.match(/^출근\\s*(\\d{1,2}:\\d{2})$/);
                        if (match) {
                            return 'ALREADY: ' + match[1];
                        }
                    }

                    // 2단계: 출근 버튼 찾아서 클릭
                    var clickTargets = document.querySelectorAll('button, a, div[role=button]');
                    for (var j = 0; j < clickTargets.length; j++) {
                        var t = clickTargets[j].textContent.trim();
                        if (t === '출근') {
                            var style = window.getComputedStyle(clickTargets[j]);
                            var rect = clickTargets[j].getBoundingClientRect();
                            if (style.pointerEvents !== 'none' && style.opacity !== '0' && rect.width > 0 && rect.height > 0) {
                                clickTargets[j].click();
                                return 'CLICKED_FIRST';
                            }
                        }
                    }

                    // 3단계: 퇴근 버튼이 활성화되어 있으면 이미 출근한 상태
                    for (var k = 0; k < clickTargets.length; k++) {
                        var t2 = clickTargets[k].textContent.trim();
                        if (t2 === '퇴근') {
                            var style2 = window.getComputedStyle(clickTargets[k]);
                            var rect2 = clickTargets[k].getBoundingClientRect();
                            if (style2.pointerEvents !== 'none' && style2.opacity !== '0' && rect2.width > 0 && rect2.height > 0) {
                                return 'ALREADY: (시간 확인 불가 - 이미 출근 상태)';
                            }
                        }
                    }

                    // 찾지 못함 - 디버깅용
                    var pageInfo = document.title + ' (' + window.location.href + ')';
                    return 'FAIL: 출근 버튼을 찾지 못했습니다. 페이지: ' + pageInfo;
                })();
            ")
        end tell

        -- 첫 번째 출근 버튼 클릭 후 확인 팝업 처리
        if checkinResult starts with "CLICKED_FIRST" then
            -- 통합 폴링: 상태 변경 확인 + 확인 팝업 클릭 (최대 popupTimeout + verifyTimeout 초)
            set totalTimeout to popupTimeout + verifyTimeout
            set checkinDone to false
            set elapsedTime to 0
            set confirmClicked to false
            set wasOnConfirmPage to false
            repeat while elapsedTime < totalTimeout
                delay 1
                set elapsedTime to elapsedTime + 1

                tell active tab of front window
                    -- 먼저: 상태가 이미 변경되었는지 확인
                    -- 확인 페이지(commuteDetail)에서는 홈으로 돌아온 후 검증
                    set stateCheck to (execute javascript "
                        (function() {
                            if (window.location.href.indexOf('commuteDetail') !== -1) {
                                return 'ON_CONFIRM_PAGE';
                            }
                            // 홈 페이지: 상태 텍스트는 span 등 비인터랙티브 요소에 렌더링될 수 있어 넓은 셀렉터 사용
                            var allEls = document.querySelectorAll('button, a, div, span');
                            for (var i = 0; i < allEls.length; i++) {
                                var text = allEls[i].textContent.trim();
                                if (text.match(/^출근\\s*\\d{1,2}:\\d{2}$/)) {
                                    return 'VERIFIED';
                                }
                            }
                            return 'NOT_VERIFIED';
                        })();
                    ")
                end tell

                if stateCheck is "VERIFIED" then
                    set checkinDone to true
                    exit repeat
                end if

                -- 확인 페이지 방문 추적: 홈으로 돌아오면 confirm 재클릭 방지
                if stateCheck is "ON_CONFIRM_PAGE" then
                    set wasOnConfirmPage to true
                else if wasOnConfirmPage then
                    set confirmClicked to true
                end if

                -- 아직 상태 미변경: 확인 버튼을 찾아서 클릭 시도 (아직 안 했으면)
                if confirmClicked is false then
                    tell active tab of front window
                        set tryConfirm to (execute javascript "
                            (function() {
                                // 페이지 이동 감지: 확인 페이지(workplace.worksmobile.com)로 이동하면 전체 문서 검색
                                var isConfirmPage = window.location.href.indexOf('commuteDetail') !== -1;

                                // 확인 페이지 또는 모달이 있으면 '출근' 또는 '확인' 버튼 검색
                                var allBtns = document.querySelectorAll('button, a, div[role=button]');
                                for (var i = 0; i < allBtns.length; i++) {
                                    var t = allBtns[i].textContent.trim();
                                    if (t === '출근' || (isConfirmPage && t === '확인')) {
                                        var style = window.getComputedStyle(allBtns[i]);
                                        var rect = allBtns[i].getBoundingClientRect();
                                        if (style.pointerEvents !== 'none' && style.opacity !== '0' && rect.width > 0 && rect.height > 0) {
                                            allBtns[i].click();
                                            return 'CLICKED';
                                        }
                                    }
                                }

                                return isConfirmPage ? 'WAITING_CONFIRM_PAGE' : 'WAITING';
                            })();
                        ")
                    end tell
                    if tryConfirm is "CLICKED" then set confirmClicked to true
                end if
            end repeat

            if checkinDone then
                set checkinResult to "SUCCESS: 출근 처리 완료"
            else
                set checkinResult to "FAIL_UNVERIFIED: 출근 버튼을 클릭했지만 상태 변경이 확인되지 않았습니다. 네트워크 지연 또는 팝업 차단이 원인일 수 있습니다. 수동으로 출근 상태를 확인해 주세요."
            end if
        end if

        -- 탭 닫기
        delay 1
        tell front window
            close active tab
        end tell

        return checkinResult
    end tell
on error errMsg
    -- 에러 발생 시 탭 정리 시도
    try
        tell application "Google Chrome"
            tell front window to close active tab
        end tell
    end try
    return "FAIL: 스크립트 실행 오류 - " & errMsg
end try
APPLESCRIPT
)

echo "$result"

case "$result" in
    *SUCCESS*|*ALREADY*)
        exit 0
        ;;
    *)
        exit 1
        ;;
esac
