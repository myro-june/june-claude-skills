---
description: 네이버 웍스(LINE WORKS) 출근 체크. Chrome 브라우저로 출근 상태를 변경합니다. (macOS 전용)
---

네이버 웍스 출근 체크를 실행합니다.

1. `bash "${CLAUDE_PLUGIN_ROOT}/scripts/naver-works-checkin.sh"` 를 실행한다.
2. 결과를 확인하고 사용자에게 알려준다.
   - `ALREADY: HH:MM` → 현재 한국 시간(KST)과 출근 시간의 차이를 계산하여 "이미 출근 상태입니다. HH:MM에 출근하셨습니다. (현재 N시간 M분 근무 중)" 형식으로 알려준다.
   - `ALREADY: (시간 확인 불가` → "이미 출근 상태입니다."
   - `SUCCESS` → "출근 처리 완료되었습니다!"
   - `FAIL` → 에러 내용을 분석하고 사용자에게 상황을 설명한다.
