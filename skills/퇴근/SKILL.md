---
description: 네이버 웍스(LINE WORKS) 퇴근 체크. Chrome 브라우저로 퇴근 상태를 변경합니다. (macOS 전용)
---

네이버 웍스 퇴근 체크를 실행합니다.

1. `bash "${CLAUDE_PLUGIN_ROOT}/scripts/naver-works-checkout.sh"` 를 실행한다.
2. 결과를 확인하고 사용자에게 알려준다. 결과에 `|CHECKIN:HH:MM`이 포함되어 있으면 출근 시간을 파싱하여 총 근무 시간을 계산한다.
   - `SUCCESS....|CHECKIN:HH:MM` → 현재 한국 시간(KST)에서 출근 시간을 빼서 총 근무 시간을 계산한다. "퇴근 처리 완료되었습니다! 오늘 총 N시간 M분 근무하셨습니다. 수고하셨습니다."
   - `SUCCESS` (CHECKIN 없음) → "퇴근 처리 완료되었습니다! 오늘도 수고하셨습니다."
   - `ALREADY: HH:MM|CHECKIN:HH:MM` → 출근~퇴근 시간으로 총 근무 시간을 계산한다. "이미 퇴근 상태입니다. HH:MM에 퇴근하셨습니다. (오늘 총 N시간 M분 근무)"
   - `ALREADY: HH:MM` (CHECKIN 없음) → "이미 퇴근 상태입니다. HH:MM에 퇴근하셨습니다."
   - `FAIL` → 에러 내용을 분석하고 사용자에게 상황을 설명한다.
