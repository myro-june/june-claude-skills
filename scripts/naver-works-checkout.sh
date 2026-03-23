#!/bin/bash
# 네이버 웍스(LINE WORKS) 퇴근 자동화 스크립트
# Chrome AppleScript를 이용하여 기존 로그인 세션으로 퇴근 버튼 클릭
# macOS 전용

result=$(osascript <<'APPLESCRIPT'
-- Chrome이 실행 중인지 확인하고, 아니면 실행
if application "Google Chrome" is not running then
    tell application "Google Chrome" to activate
    delay 3
end if

try
    -- 타임아웃 설정 (초 단위, 최악의 경우 총 약 52초)
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

        -- 퇴근 상태 확인 및 처리
        tell active tab of front window
            set checkoutResult to (execute javascript "
                (function() {
                    // 상태 텍스트('출근 09:30', '퇴근 18:00')는 span 등 비인터랙티브 요소에 렌더링될 수 있어 넓은 셀렉터 사용
                    var allEls = document.querySelectorAll('button, a, div, span');

                    // 출근 시간 먼저 파싱
                    var checkinTime = '';
                    for (var i = 0; i < allEls.length; i++) {
                        var text = allEls[i].textContent.trim();
                        var cm = text.match(/^출근\\s*(\\d{1,2}:\\d{2})$/);
                        if (cm) { checkinTime = cm[1]; break; }
                    }

                    // 1단계: 이미 퇴근했는지 확인 ('퇴근 HH:MM' 패턴)
                    for (var i = 0; i < allEls.length; i++) {
                        var text = allEls[i].textContent.trim();
                        var match = text.match(/^퇴근\\s*(\\d{1,2}:\\d{2})$/);
                        if (match) {
                            return 'ALREADY: ' + match[1] + (checkinTime ? '|CHECKIN:' + checkinTime : '');
                        }
                    }

                    // 2단계: 퇴근 버튼 찾아서 클릭
                    var clickTargets = document.querySelectorAll('button, a, div[role=button]');
                    for (var j = 0; j < clickTargets.length; j++) {
                        var t = clickTargets[j].textContent.trim();
                        if (t === '퇴근') {
                            var style = window.getComputedStyle(clickTargets[j]);
                            var rect = clickTargets[j].getBoundingClientRect();
                            if (style.pointerEvents !== 'none' && style.opacity !== '0' && rect.width > 0 && rect.height > 0) {
                                clickTargets[j].click();
                                return 'CLICKED_FIRST' + (checkinTime ? '|CHECKIN:' + checkinTime : '');
                            }
                        }
                    }

                    // 3단계: 출근 버튼만 있으면 아직 출근 전
                    for (var k = 0; k < clickTargets.length; k++) {
                        var t2 = clickTargets[k].textContent.trim();
                        if (t2 === '출근') {
                            var style2 = window.getComputedStyle(clickTargets[k]);
                            var rect2 = clickTargets[k].getBoundingClientRect();
                            if (style2.pointerEvents !== 'none' && style2.opacity !== '0' && rect2.width > 0 && rect2.height > 0) {
                                return 'FAIL_NOT_CHECKEDIN: 아직 출근하지 않은 상태입니다.';
                            }
                        }
                    }

                    // 찾지 못함 - 디버깅용
                    var pageInfo = document.title + ' (' + window.location.href + ')';
                    return 'FAIL: 퇴근 버튼을 찾지 못했습니다. 페이지: ' + pageInfo;
                })();
            ")
        end tell

        -- 첫 번째 퇴근 버튼 클릭 후 확인 페이지 처리
        if checkoutResult starts with "CLICKED_FIRST" then
            -- CHECKIN 정보 보존
            set checkinInfo to ""
            if checkoutResult contains "|CHECKIN:" then
                set o to offset of "|CHECKIN:" in checkoutResult
                set checkinInfo to text o thru -1 of checkoutResult
            end if

            -- 확인 팝업 대기 (폴링)
            set confirmResult to "FAIL: 확인 페이지에서 퇴근 버튼을 찾지 못했습니다."
            set confirmWait to 0
            repeat while confirmWait < popupTimeout
                delay 1
                set confirmWait to confirmWait + 1
                tell active tab of front window
                    set confirmResult to (execute javascript "
                        (function() {
                            // 모달/다이얼로그 내부에서 우선 검색
                            // 모달 컨테이너가 없으면 아직 팝업이 안 뜬 것으로 판단 (원래 버튼 재클릭 방지)
                            var containers = document.querySelectorAll('[role=dialog], [class*=modal], [class*=popup], [class*=layer], [class*=overlay]');
                            if (containers.length === 0) return 'WAITING';
                            var searchRoot = containers[containers.length - 1];
                            var buttons = searchRoot.querySelectorAll('button, a, div[role=button]');
                            for (var i = 0; i < buttons.length; i++) {
                                var t = buttons[i].textContent.trim();
                                if (t === '퇴근') {
                                    var style = window.getComputedStyle(buttons[i]);
                                    var rect = buttons[i].getBoundingClientRect();
                                    if (style.pointerEvents !== 'none' && style.opacity !== '0' && rect.width > 0 && rect.height > 0) {
                                        buttons[i].click();
                                        return 'SUCCESS';
                                    }
                                }
                            }
                            return 'WAITING';
                        })();
                    ")
                end tell
                if confirmResult is "SUCCESS" then exit repeat
            end repeat

            if confirmResult is "SUCCESS" then
                -- 실제로 퇴근이 처리되었는지 검증 (폴링)
                set verifyResult to "NOT_VERIFIED"
                set verifyWait to 0
                repeat while verifyWait < verifyTimeout
                    delay 1
                    set verifyWait to verifyWait + 1
                    tell active tab of front window
                        set verifyResult to (execute javascript "
                            (function() {
                                // 상태 텍스트는 span 등 비인터랙티브 요소에 렌더링될 수 있어 넓은 셀렉터 사용
                                var allEls = document.querySelectorAll('button, a, div, span');
                                for (var i = 0; i < allEls.length; i++) {
                                    var text = allEls[i].textContent.trim();
                                    if (text.match(/^퇴근\\s*\\d{1,2}:\\d{2}$/)) {
                                        return 'VERIFIED';
                                    }
                                }
                                return 'NOT_VERIFIED';
                            })();
                        ")
                    end tell
                    if verifyResult is "VERIFIED" then exit repeat
                end repeat

                if verifyResult is "VERIFIED" then
                    set checkoutResult to "SUCCESS: 퇴근 처리 완료" & checkinInfo
                else
                    set checkoutResult to "FAIL_UNVERIFIED: 퇴근 버튼을 클릭했지만 상태 변경이 확인되지 않았습니다. 네트워크 지연 또는 페이지 응답 지연이 원인일 수 있습니다. 수동으로 퇴근 상태를 확인해 주세요." & checkinInfo
                end if
            else if confirmResult is "WAITING" then
                set checkoutResult to "FAIL_UNVERIFIED: 확인 팝업이 표시되지 않았습니다. Chrome 팝업 차단이 원인일 수 있습니다. 수동으로 퇴근 상태를 확인해 주세요." & checkinInfo
            else
                set checkoutResult to confirmResult & checkinInfo
            end if
        end if

        -- 탭 닫기
        delay 1
        tell front window
            close active tab
        end tell

        return checkoutResult
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
