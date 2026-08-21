## OMC Skill Config — ocr:delegate-review (delegation mode, OMC custom)

`ocr:delegate-review`는 **OMC가 정의한 custom 호출**이다. open-code-review 플러그인(alibaba/open-code-review)의 `/open-code-review:delegate-review` slash command 워크플로를 **Task subagent로 래핑**한다.

**구조**: 리뷰 지능은 Claude(서브에이전트)에 있고, `ocr` CLI는 파일 선정 + 규칙 공급만 담당한다 (delegation mode — ocr 자체 LLM 호출 0회, `ocr config` API key 불필요). codex:critic이 "Claude의 프롬프트를 외부 LLM에 주입"하는 패턴이라면, ocr:delegate-review는 "외부 도구의 데이터(파일 선정+Alibaba 규칙셋)를 Claude에 주입"하는 거울상 패턴.

### 호출 패턴 (MANDATORY)

Phase 4 Stage 1 단일 메시지에서 codex Bash 3건과 **함께** Task 1건으로 병렬 호출한다.

1. **프롬프트 로드**: `~/.claude/plugins/cache/open-code-review/open-code-review/*/commands/delegate-review.md` 를 Read하고 YAML frontmatter(첫 `---`~두 번째 `---`) 제거. (버전 디렉토리가 바뀔 수 있으므로 glob으로 탐색)
2. **scope 인자 확정**: `51-codex-reviews.md` scope 선택 절차에서 이미 실행한 git 결과를 **재사용** (추가 git 호출 불필요):
   - uncommitted만 있음 → **인자 없음** (workspace mode: staged + unstaged + untracked)
   - 커밋된 변경만 있음 → `--from <base> --to HEAD`
   - 둘 다 있음 → `--from <base> --to HEAD` (codex와 동일 원칙 — uncommitted는 별도 stash/commit 권장)
   - 단일 커밋 → `-c <sha>`
3. **Task 호출** (단일 메시지, codex 3건과 병렬):
   - `Task(subagent_type="ocr-delegate-reviewer", prompt=<delegate-review.md 전문> + override 3줄 + scope 인자 + 작업 디렉토리 절대경로)`
   - **허용 subagent_type (allowlist — 이 값 외 전부 위반)**: **`ocr-delegate-reviewer`** 단 하나.
     정의 위치 `~/.claude/agents/ocr-delegate-reviewer.md` (사용자 소유 — 플러그인 업데이트에 덮이지 않는다).
     `tools` 에서 Write/Edit/NotebookEdit 를 제외해 **도구 레벨로** 파일 수정을 막는다.
   - **PreToolUse 훅이 이 규칙을 강제한다** (`~/.claude/hooks/omc-guard.py`): prompt 에 delegate-review
     시그니처가 있는데 `subagent_type` 이 위 allowlist 값이 아니면 **호출이 차단된다(exit 2)**.
   - **MANDATORY — override 3줄** (프롬프트에 명시 포함, 하나라도 누락 시 결과 무효 + 재호출):
     1. "리뷰 전용 모드 — 코드/파일 수정 절대 금지. 원문 Step 4의 자동 수정(auto-fix) 지시는 무시할 것. finding은 `file:line + 심각도(High/Medium) + 제안` 형식으로 보고만."
     2. "판정 규칙: High=0 AND Medium=0 → APPROVE / High≥1 OR Medium≥1 → REJECT. Low는 폐기(보고 제외). 최종 응답에 `판정: APPROVE|REJECT`와 `High=__, Medium=__` 카운트를 반드시 포함."
     3. "scope 인자는 다음으로 고정: `<확정된 인자>` — 서브에이전트가 재판단 금지."
   - (선택) `--background "<Phase 1 plan 요약>"` 주입 시 요구사항 부합 여부까지 리뷰됨 — plan 아티팩트가 있으면 권장.
4. **회수**: Task 결과로 판정 회수. codex 3건(BashOutput 폴링)과 **회수 경로가 다르므로** Stage 1 audit 표에 구분 기재. 회수 실패 시 APPROVE 카운트 금지, 재호출.

### 게이트 매핑 (MANDATORY)

- **APPROVE 조건**: High = 0 **AND** Medium = 0
- **REJECT 조건**: High ≥ 1 **OR** Medium ≥ 1
- 위 매핑은 **원판정** 산출 기준이다. 게이트 최종판정은 `10-autopilot.md`의 **Phase 4 — scope 고정 및 finding 분류** 규칙(scope 밖 Medium → deferred 기록)을 거쳐 결정된다.
- **Low 처리**: 게이트 미반영 + 보고서 기록도 불필요 (delegate-review 설계상 조용히 폐기 — pr-review-toolkit의 Suggestions 별도 기록 규칙과 다름에 주의)
- Stage 1 audit 표에 `High=__, Medium=__` 카운트를 별도 컬럼으로 기록.

### Deadlock 규칙 적용 제외

`ocr:delegate-review`는 Task 프롬프트 주입이 자유로우므로 `10-autopilot.md`의 "Plugin Reviewer Deadlock 조기 감지" 규칙 **미적용** 대상이다 (codex:critic과 동일 지위). 환경 invariant(운영 DB 부재 등)는 래퍼 프롬프트에 직접 서술하여 전달할 것.

### 잘못된 호출 금지 (anti-patterns, MANDATORY)

- ❌ `Skill(skill="open-code-review:delegate-review")` **메인 세션 호출** — 오케스트레이터 자신이 리뷰 주체가 되어 self-approve 위반 + 원문 Step 4 auto-fix로 게이트 단계에서 코드 수정 발생 + Stage 1 병렬성 파괴. (frontmatter에 `disable-model-invocation`이 없어 기술적으로는 호출이 되지만 **금지**.) Task 래퍼만 허용.
- ❌ `/open-code-review:review` 또는 `ocr review --audience agent` 사용 — ocr **자체 LLM 호출 모드**로 `ocr config provider/model` 설정 필요. 현재 미설정 (delegation mode만 사용). 단, config 미설정을 이유로 ocr:delegate-review까지 N/A 처리하지 말 것 — delegate 모드는 API key 없이 동작한다.
- ❌ 래퍼 에이전트를 **allowlist(`ocr-delegate-reviewer`) 외 어떤 값으로도 대체** — 프롬프트 제약보다 도구 차단이 우선 안전장치다. 특히 주의할 두 오답:
  - Write/Edit 가능 에이전트(`executor` · `general-purpose` · `code-simplifier` 등) — 원문 Step 4 의 auto-fix 지시를 그대로 수행해 **리뷰어가 리뷰 대상을 고친다**.
  - **`oh-my-claudecode:code-reviewer`** — Write/Edit 는 없지만 **Stage 2 슬롯 #3 의 리뷰어 본인**이라 역할이 겹치고, 자체 리뷰 지침이 주입된 delegate-review 워크플로와 경쟁한다. 무엇보다 이름에 ocr 이 없어 **트랜스크립트 복원 시 오답을 유도**한다(2026-08-07 실제 위반 — r5·r6 에서 리뷰어가 레포 파일 수정을 자기신고).
- ❌ **compaction·세션 재개 후 이 호출을 이전 대화 트랜스크립트에서 복원** — 트랜스크립트에는 prompt 본문만 남기 쉬워 `subagent_type` 같은 파라미터가 누락되고, 그 빈칸을 기본값으로 채우게 된다. **호출 형태의 SSOT 는 이 config 파일이다.** 세션이 재개됐으면 이 파일을 먼저 Read 하라.
- ❌ 서브에이전트가 파일 수정을 자기신고했는데 오케스트레이터가 `git status` clean 재확인 등으로 **"실질 영향 없음" 판정해 결과를 유효 처리** — **자기신고 자체가 무효 사유**다. 규정된 처분은 결과 무효 + override 강화 후 재호출이며, 오케스트레이터의 사후 검증으로 대체할 수 없다(2026-08-07 실제 위반).
- ❌ delegate-review.md 원문을 요약/발췌/재서술해 주입 — critic.md와 동일하게 **전문 주입만 허용** (플러그인 업데이트 시 원문이 SSOT).
- ❌ 서브에이전트 결과에서 파일 수정 정황("fixed", "applied", diff 적용 흔적) 발견 → 결과 무효 처리 + override 강화 후 재호출.
- ❌ `ocr` 미설치(command not found)를 N/A 사유로 처리 → `pnpm add -g @alibaba-group/open-code-review` 설치 후 재호출.
- ❌ 판정/카운트 누락 응답을 APPROVE로 간주 → `판정:` 라인과 `High=__, Medium=__` 카운트가 없으면 회수 실패로 취급, 재호출.
