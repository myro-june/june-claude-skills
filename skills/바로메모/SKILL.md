---
name: 바로메모
description: macOS 메모.app(Notes.app)에 빠르게 메모를 생성합니다. 인자로 메모 내용을 바로 전달하거나, 대화 내용을 메모로 정리합니다.
triggers: []
argument-hint: "메모할 내용 (예: 내일 회의 안건 정리)"
---

# /바로메모 — macOS 메모.app 빠른 메모 생성

대화 중 떠오른 아이디어나 정보를 macOS 메모.app에 즉시 저장합니다.

## When to Activate

사용자가 명시적으로 `/바로메모`를 입력했을 때만 실행. 키워드 자동 감지하지 않음.

## 실행 방식: 백그라운드 Agent

**모든 메모 생성은 백그라운드 Agent로 위임한다.** 사용자가 `/바로메모`를 입력하면 즉시 Agent를 `run_in_background: true`로 스폰하고, 사용자에게 "메모 저장 중..." 한 줄만 알린 뒤 대화를 계속한다. Agent가 완료되면 자동 알림이 온다.

**Agent 스폰 시 전달할 정보:**
- 메모 본문 (사용자 입력 그대로)
- URL 포함 여부
- "각각 메모로" 등 분리 저장 지시 여부
- 이 SKILL.md의 Step 1~4 워크플로우 전체를 프롬프트로 전달

**인자가 없는 경우만 예외:** 사용자에게 내용을 질문해야 하므로 동기로 실행. 내용이 확정되면 이후는 백그라운드 Agent로 위임.

## Workflow (Agent 내부에서 실행)

### Step 1: 메모 내용 결정

**인자가 있는 경우** (`/바로메모 내일 회의 안건 정리`):
- 인자를 메모 본문으로 사용한다.
- 본문에서 핵심 키워드를 추출하여 제목을 자동 생성한다.
- 바로 Step 3으로 진행한다.

**인자가 없는 경우** (`/바로메모`):
- 현재 대화 컨텍스트를 분석하여 메모할 만한 내용이 있는지 확인한다.
- 대화에서 추출할 내용이 있으면 요약하여 제안한다.
- 없으면 사용자에게 메모 내용을 질문한다:
```
AskUserQuestion:
  question: "어떤 내용을 메모할까요?"
```

### Step 2: 메모 정리

- **제목**: 간결하게 생성 (20자 이내 권장). URL이 포함된 경우 `WebFetch`로 페이지를 조회하여 서비스/콘텐츠 내용을 파악한 뒤 제목에 반영한다.
  - URL만 있는 경우: 링크 콘텐츠를 압축하여 제목 생성 (예: `https://fireflies.ai/` → "Fireflies.ai - AI 회의록 플랫폼")
  - URL + 텍스트 메모가 있는 경우: 링크 콘텐츠와 사용자 메모를 종합하여 제목 생성 (예: `https://fireflies.ai/ 조시 추천` → "AI 회의록 Fireflies - 조시 추천")
  - URL이 없는 경우: 본문 내용을 요약하여 제목 생성
- **본문**: 사용자가 입력한 내용을 최대한 그대로 유지한다. 임의로 재구성하거나 요약하지 않는다.
  - URL이 포함되어 있으면 그대로 보존
  - 줄바꿈, 구두점 등 원문 형식을 유지
  - 단, HTML 변환에 필요한 최소한의 포맷팅만 적용 (줄바꿈 → `<br>`, URL → `<a>` 태그)

### Step 3: 메모 생성

`osascript`로 메모.app에 새 메모를 생성한다:

```bash
osascript -e '
tell application "Notes"
  activate
  set noteTitle to "TITLE_HERE"
  set noteBody to "BODY_HTML_HERE"
  make new note at folder "001-하루 인박스" with properties {name:noteTitle, body:noteBody}
end tell'
```

**HTML 변환 규칙** (메모.app은 HTML 기반):
- 줄바꿈: `<br>`
- 불릿 리스트: `<ul><li>...</li></ul>`
- 번호 리스트: `<ol><li>...</li></ol>`
- 볼드: `<b>...</b>`
- 코드: `<code>...</code>` (인라인), `<pre><code>...</code></pre>` (블록)
- 제목은 `name` 속성으로 전달 (HTML 불필요)

**AppleScript 이스케이프**:
- 본문 내 큰따옴표(`"`)는 `\"` 로 이스케이프
- 본문 내 작은따옴표(`'`)는 osascript 명령 충돌 방지를 위해 heredoc 방식 사용:

```bash
osascript <<'APPLESCRIPT'
tell application "Notes"
  activate
  set noteTitle to "TITLE_HERE"
  set noteBody to "BODY_HTML_HERE"
  make new note at folder "001-하루 인박스" with properties {name:noteTitle, body:noteBody}
end tell
APPLESCRIPT
```

### Step 4: 결과 확인

- 성공 시: "메모.app에 저장했습니다: {제목}" 한 줄로 알림
- 실패 시: 에러 내용을 설명하고, 메모 내용을 코드블록으로 표시하여 수동 복사 가능하게 함

## 주의사항

- 메모.app 폴더는 기본 "Notes"(메모) 폴더를 사용한다. 사용자가 다른 폴더를 지정하면 해당 폴더를 사용.
- AppleScript에서 특수문자 이스케이프에 주의한다.
- 메모.app이 실행 중이 아니어도 `activate`로 자동 실행된다.
- 긴 내용은 적절히 요약하되, 사용자가 "그대로" 저장을 요청하면 원문 보존.
