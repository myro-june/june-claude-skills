#!/bin/bash
# 네이버 웍스(LINE WORKS) 출근 자동화 스크립트
# Chrome AppleScript를 이용하여 기존 로그인 세션으로 출근 버튼 클릭
# macOS 전용

osascript <<'APPLESCRIPT'
-- Chrome이 실행 중인지 확인하고, 아니면 실행
if application "Google Chrome" is not running then
    tell application "Google Chrome" to activate
    delay 3
end if

tell application "Google Chrome"
    activate

    -- Chrome이 방금 실행되었거나 창이 없는 경우
    if (count of windows) = 0 then
        make new window
        delay 1
    end if

    -- 새 탭에서 네이버 웍스 홈 열기
    tell front window
        set newTab to make new tab with properties {URL:"https://home.worksmobile.com"}
    end tell

    -- 페이지 로드 대기 (최대 15초)
    set maxWait to 15
    set waited to 0
    repeat while waited < maxWait
        delay 1
        set waited to waited + 1
        tell active tab of front window
            set pageState to (execute javascript "document.readyState")
        end tell
        if pageState is "complete" then exit repeat
    end repeat

    -- 추가 렌더링 대기
    delay 3

    -- 출근 상태 확인 및 처리
    tell active tab of front window
        set checkinResult to (execute javascript "
            (function() {
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
                        if (style.pointerEvents !== 'none' && style.opacity !== '0') {
                            clickTargets[j].click();
                            return 'SUCCESS: 출근 버튼 클릭 완료';
                        }
                    }
                }

                // 3단계: 퇴근 버튼이 활성화되어 있으면 이미 출근한 상태
                for (var k = 0; k < clickTargets.length; k++) {
                    var t2 = clickTargets[k].textContent.trim();
                    if (t2 === '퇴근') {
                        var style2 = window.getComputedStyle(clickTargets[k]);
                        if (style2.pointerEvents !== 'none' && style2.opacity !== '0') {
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

    -- 탭 닫기
    delay 1
    tell front window
        close active tab
    end tell

    return checkinResult
end tell
APPLESCRIPT
