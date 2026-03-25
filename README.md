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
| 슬랙요약 | `/june-claude-skills:슬랙요약 <링크>` | 슬랙 메시지의 원문 기사를 요약하여 스레드에 게시 |

## 요구사항

- **Claude Code CLI**
- **macOS** + **Google Chrome** (출근/퇴근/웍스홈 스킬)
- **Slack MCP 서버** (슬랙요약 스킬)

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

# 슬랙요약 (슬랙 메시지 기사 요약)
/june-claude-skills:슬랙요약 https://workspace.slack.com/archives/CHANNEL/pTIMESTAMP
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

### 슬랙요약

1. 슬랙 메시지 링크에서 `channel_id`와 `message_ts`를 파싱합니다
2. Slack MCP로 해당 메시지를 읽고 본문에서 외부 URL을 추출합니다
3. WebFetch로 원문 기사 본문과 댓글을 병렬 수집합니다
4. 기사 제목, 핵심 내용, 결론을 요약하여 해당 메시지의 스레드에 자동 게시합니다

Slack MCP 서버가 연결되어 있어야 합니다.

### 잠자기

Mac을 즉시 잠자기 모드로 전환합니다 (`pmset sleepnow`).

## 주의사항

- 출근/퇴근/웍스홈: **스크립트 실행 중에는 Chrome을 조작하지 마세요** (탭 전환, 클릭 등 시 오작동 가능)
- 출근/퇴근/웍스홈: 네이버 웍스에 Chrome으로 로그인되어 있어야 합니다
- 출근/퇴근/웍스홈: 근무 시간 외에는 출근 버튼이 표시되지 않을 수 있습니다
- 출근/퇴근/웍스홈: macOS 전용입니다 (AppleScript 기반)
- 세션요약: 대화 내용이 많을수록 정확한 요약을 제공합니다
- 잠자기: macOS 전용입니다 (`pmset` 명령어 기반)
- 슬랙요약: Slack MCP 서버가 연결되어 있어야 합니다
- 슬랙요약: 원문 링크가 없는 메시지인 경우 메시지 자체 내용을 요약합니다
