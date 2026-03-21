# june-claude-skills

Claude Code 스킬 모음 플러그인

## 스킬 목록

| 스킬 | 명령어 | 설명 |
|------|--------|------|
| 출근 | `/june-claude-skills:출근` | 네이버 웍스 출근 체크 |
| 퇴근 | `/june-claude-skills:퇴근` | 네이버 웍스 퇴근 체크 |
| 웍스홈 | `/june-claude-skills:웍스홈` | Chrome에서 네이버 웍스 홈 페이지 열기 |
| 세션요약 | `/june-claude-skills:세션요약` | 현재 세션 대화 내용 한줄 브리핑 요약 |

## 요구사항

- **Claude Code CLI**
- **macOS** + **Google Chrome** (출근/퇴근/웍스홈 스킬)

## 설치

```bash
# 1. 마켓플레이스 추가
/plugin marketplace add june/june-claude-skills

# 2. 플러그인 설치
/plugin install june-claude-skills
```

## 사전 설정 (출근/퇴근/웍스홈)

Chrome에서 AppleScript 실행을 허용해야 합니다:

> Chrome 메뉴 바 → **보기** → **개발자** → **Apple Events의 자바스크립트 허용** 체크

## 사용법

Claude Code에서:

```bash
# 출근
/june-claude-skills:출근

# 퇴근
/june-claude-skills:퇴근

# 웍스홈 (네이버 웍스 홈 페이지 열기)
/june-claude-skills:웍스홈

# 세션요약 (현재 세션 대화 한줄 브리핑)
/june-claude-skills:세션요약

# 세션요약 상세 모드
/june-claude-skills:세션요약 --detail
```

### 단축 커맨드 설정 (선택)

`/출근`, `/퇴근`으로 짧게 사용하려면 `~/.claude/commands/`에 커맨드 파일을 추가합니다:

**~/.claude/commands/출근.md**
```markdown
네이버 웍스 출근 체크를 실행합니다.

1. `bash "<플러그인 설치 경로>/scripts/naver-works-checkin.sh"` 를 실행한다.
2. 결과를 확인하고 사용자에게 알려준다.
   - `ALREADY: HH:MM` → 현재 한국 시간(KST)과 출근 시간의 차이를 계산하여 "이미 출근 상태입니다. HH:MM에 출근하셨습니다. (현재 N시간 M분 근무 중)" 형식으로 알려준다.
   - `ALREADY: (시간 확인 불가` → "이미 출근 상태입니다."
   - `SUCCESS` → "출근 처리 완료되었습니다!"
   - `FAIL` → 에러 내용을 분석하고 사용자에게 상황을 설명한다.
```

**~/.claude/commands/퇴근.md**
```markdown
네이버 웍스 퇴근 체크를 실행합니다.

1. `bash "<플러그인 설치 경로>/scripts/naver-works-checkout.sh"` 를 실행한다.
2. 결과를 확인하고 사용자에게 알려준다.
   - `SUCCESS....|CHECKIN:HH:MM` → 출근 시간에서 현재 시간을 빼서 "퇴근 처리 완료! 오늘 총 N시간 M분 근무하셨습니다." 로 알려준다.
   - `SUCCESS` (CHECKIN 없음) → "퇴근 처리 완료되었습니다! 오늘도 수고하셨습니다."
   - `ALREADY: HH:MM|CHECKIN:HH:MM` → "이미 퇴근 상태입니다. HH:MM에 퇴근. (오늘 총 N시간 M분 근무)"
   - `FAIL` → 에러 내용을 분석하고 상황을 설명한다.
```

**~/.claude/commands/웍스홈.md**
```markdown
Chrome에서 네이버 웍스 홈 페이지를 엽니다.

1. `open -a "Google Chrome" "https://home.worksmobile.com/"` 를 실행한다.
2. "네이버 웍스 홈 페이지를 열었습니다." 라고 알려준다.
```

**~/.claude/commands/세션요약.md**

> `skills/세션요약/SKILL.md`의 내용을 그대로 복사합니다.

> 플러그인 설치 경로는 `~/.claude/plugins/cache/` 하위에 있습니다. 출근/퇴근 스크립트 경로는 `find ~/.claude/plugins/cache -name "naver-works-checkin.sh"` 로 확인할 수 있습니다.

## 동작 방식

### 출근 / 퇴근 / 웍스홈

1. Chrome에서 새 탭으로 네이버 웍스 홈(`home.worksmobile.com`)을 엽니다
2. 출근/퇴근 버튼을 자동으로 찾아 클릭합니다
3. 이미 출근/퇴근 상태라면 시간을 알려줍니다
4. 완료 후 탭을 자동으로 닫습니다

Chrome이 꺼져 있으면 자동으로 실행합니다. 기존 로그인 세션을 그대로 사용하므로 별도 로그인이 필요 없습니다.

### 세션요약

1. 현재 대화 컨텍스트에서 요청/완료/진행중/결정사항을 추출합니다
2. 한줄 브리핑으로 요약하여 출력합니다
3. `--detail` 옵션 사용 시 항목별 상세 정리도 함께 출력합니다

외부 도구 없이 Claude의 대화 컨텍스트만으로 동작합니다.

## 주의사항

- 출근/퇴근/웍스홈: 네이버 웍스에 Chrome으로 로그인되어 있어야 합니다
- 출근/퇴근/웍스홈: 근무 시간 외에는 출근 버튼이 표시되지 않을 수 있습니다
- 출근/퇴근/웍스홈: macOS 전용입니다 (AppleScript 기반)
- 세션요약: 대화 내용이 많을수록 정확한 요약을 제공합니다
