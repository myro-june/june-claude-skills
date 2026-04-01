# june-claude-skills

Claude Code 스킬 모음 플러그인

## 스킬 목록

| 스킬 | 명령어 | 설명 |
|------|--------|------|
| 출근 | `/june-claude-skills:출근` | 네이버 웍스 출근 체크 |
| 퇴근 | `/june-claude-skills:퇴근` | 네이버 웍스 퇴근 체크 |
| 웍스홈 | `/june-claude-skills:웍스홈` | Chrome에서 네이버 웍스 홈 페이지 열기 |
| 세션요약 | `/june-claude-skills:세션요약` | 현재 세션 대화 내용 한줄 브리핑 요약 |
| 잠자기 | `/june-claude-skills:잠자기` | Mac 즉시 잠자기 모드 전환 |
| 슬랙기사링크요약 | `/june-claude-skills:슬랙기사링크요약 <링크>` | 슬랙 메시지의 원문 기사를 요약하여 스레드에 게시 |
| 바로메모 | `/june-claude-skills:바로메모 <내용>` | macOS 메모.app에 빠르게 메모 생성 (하루 인박스) |
| 바로메모폴더 | `/june-claude-skills:바로메모폴더 [폴더명]` | 메모.app 폴더 확인 및 추가 |
| 바로메모하루조회 | `/june-claude-skills:바로메모하루조회` | 하루 인박스 메모 목록 조회 |
| 바로메모주간조회 | `/june-claude-skills:바로메모주간조회` | 주간 인박스 메모 목록 조회 |
| 바로메모앱 | `/june-claude-skills:바로메모앱` | 메모.app 열기 및 포커스 |

## 요구사항

- **Claude Code CLI**
- **macOS** + **Google Chrome** (출근/퇴근/웍스홈 스킬)
- **Slack MCP 서버** (슬랙기사링크요약 스킬)
- **macOS 메모.app** (바로메모 스킬)

## 설치

```bash
# 1. 마켓플레이스 추가
/plugin marketplace add https://github.com/myro-june/june-claude-skills

# 2. 플러그인 설치
/plugin install june-claude-skills
```

## 사전 설정 (출근/퇴근/웍스홈)

Chrome에서 AppleScript 실행을 허용해야 합니다:

> Chrome 메뉴 바 → **보기** → **개발자** → **Apple Events의 자바스크립트 허용** 체크

또한 Chrome 팝업 차단 설정을 확인해주세요:

> Chrome 설정 → 개인정보 및 보안 → 사이트 설정 → 팝업 및 리디렉션 → `home.worksmobile.com` 허용 추가

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

# 잠자기 (Mac 잠자기 모드)
/june-claude-skills:잠자기

# 슬랙기사링크요약 (슬랙 메시지 기사 요약)
/june-claude-skills:슬랙기사링크요약 https://workspace.slack.com/archives/CHANNEL/pTIMESTAMP

# 바로메모 (메모.app에 빠르게 저장)
/june-claude-skills:바로메모 내일 회의 안건 정리
/june-claude-skills:바로메모 https://example.com/ 나중에 읽기

# 바로메모폴더 (폴더 확인/추가)
/june-claude-skills:바로메모폴더
/june-claude-skills:바로메모폴더 106-프로젝트

# 바로메모하루조회 (하루 인박스 메모 목록)
/june-claude-skills:바로메모하루조회

# 바로메모주간조회 (주간 인박스 메모 목록)
/june-claude-skills:바로메모주간조회

# 바로메모앱 (메모.app 열기)
/june-claude-skills:바로메모앱
```

### 단축 커맨드 설정 (선택)

`/출근`, `/퇴근`으로 짧게 사용하려면 `~/.claude/commands/`에 커맨드 파일을 추가합니다.
각 스킬의 `SKILL.md` 내용을 참고하여 작성하세요. 스크립트 경로는 아래 명령어로 확인할 수 있습니다:

```bash
find ~/.claude/plugins/cache -name "naver-works-checkin.sh"
```

## 동작 방식

### 출근 / 퇴근

1. Chrome에서 새 탭으로 네이버 웍스 홈(`home.worksmobile.com`)을 엽니다
2. 페이지 로드 및 SPA 위젯 렌더링을 대기합니다 (폴링, 각 최대 15초)
3. 출근/퇴근 버튼을 자동으로 찾아 클릭합니다
4. 확인 페이지(`commuteDetail`)로 이동하면 자동으로 확인 버튼을 클릭합니다
5. 홈으로 돌아온 후 실제 상태 변경을 검증합니다 (통합 폴링, 최대 20초)
6. 이미 출근/퇴근 상태라면 시간과 근무 시간을 알려줍니다
7. 완료 후 탭을 자동으로 닫습니다

Chrome이 꺼져 있으면 자동으로 실행합니다. 기존 로그인 세션을 그대로 사용하므로 별도 로그인이 필요 없습니다.

**결과 코드:**
- `SUCCESS` — 처리 완료
- `ALREADY` — 이미 출근/퇴근 상태 (시간 표시)
- `FAIL_UNVERIFIED` — 버튼 클릭 후 상태 변경 미확인 (네트워크 지연 또는 팝업 차단)
- `FAIL_NOT_CHECKEDIN` — 퇴근 시도 시 미출근 상태 (퇴근 전용)
- `FAIL` — 기타 오류

### 웍스홈

Chrome에서 네이버 웍스 홈 페이지를 엽니다.

### 세션요약

1. 현재 대화 컨텍스트에서 요청/완료/진행중/결정사항을 추출합니다
2. 한줄 브리핑으로 요약하여 출력합니다
3. `--detail` 옵션 사용 시 항목별 상세 정리도 함께 출력합니다

외부 도구 없이 Claude의 대화 컨텍스트만으로 동작합니다.

### 슬랙기사링크요약

1. 슬랙 메시지 링크에서 `channel_id`와 `message_ts`를 파싱합니다
2. Slack MCP로 해당 메시지를 읽고 본문에서 외부 URL을 추출합니다
3. WebFetch로 원문 기사 본문과 댓글을 병렬 수집합니다
4. 기사 제목, 핵심 내용, 결론을 요약하여 해당 메시지의 스레드에 자동 게시합니다

Slack MCP 서버가 연결되어 있어야 합니다. **백그라운드 Agent로 실행**되어 요약 중에도 대화를 이어갈 수 있습니다.

### 잠자기

Mac을 즉시 잠자기 모드로 전환합니다 (`pmset sleepnow`).

### 바로메모

macOS 메모.app에 빠르게 메모를 생성합니다. AppleScript(`osascript`)로 메모.app을 제어합니다.

- 텍스트 메모: 내용을 그대로 본문에 저장, 제목은 AI가 요약 생성
- URL 포함 시: `WebFetch`로 페이지 내용을 파악하여 제목에 반영
- URL + 텍스트: 링크 콘텐츠와 메모를 종합하여 제목 생성
- 여러 항목을 "각각 메모로" 요청하면 개별 메모로 분리 저장
- 기본 저장 폴더: `001-하루 인박스`
- **백그라운드 실행**: Agent로 위임하여 메모 저장 중에도 대화 가능

### 바로메모폴더

메모.app의 폴더 목록을 조회하고, 새 폴더를 추가합니다.

- 인자 없이 실행: 현재 폴더 목록 표시
- 인자와 함께 실행: 해당 이름의 폴더 생성
- 폴더 네이밍 컨벤션: `001/002` (인박스), `101~` (카테고리)

### 바로메모앱

메모.app을 열고 포커스합니다 (`open -a "Notes"`).

### 바로메모하루조회 / 바로메모주간조회

각각 `001-하루 인박스`, `002-주간 인박스`의 메모 목록을 번호와 함께 표시합니다.

## 주의사항

- 출근/퇴근/웍스홈: **스크립트 실행 중에는 Chrome을 조작하지 마세요** (탭 전환, 클릭 등 시 오작동 가능)
- 출근/퇴근/웍스홈: 네이버 웍스에 Chrome으로 로그인되어 있어야 합니다
- 출근/퇴근/웍스홈: 근무 시간 외에는 출근 버튼이 표시되지 않을 수 있습니다
- 출근/퇴근/웍스홈: macOS 전용입니다 (AppleScript 기반)
- 세션요약: 대화 내용이 많을수록 정확한 요약을 제공합니다
- 잠자기: macOS 전용입니다 (`pmset` 명령어 기반)
- 슬랙기사링크요약: Slack MCP 서버가 연결되어 있어야 합니다
- 슬랙기사링크요약: 원문 링크가 없는 메시지인 경우 메시지 자체 내용을 요약합니다
- 바로메모: macOS 전용입니다 (AppleScript 기반)
- 바로메모: 메모.app 폴더 이름 변경은 AppleScript로 불가하므로 앱에서 직접 변경해야 합니다
