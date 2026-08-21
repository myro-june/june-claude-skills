## OMC Skill Config — Phase 4 Stage 0 정합 선행 게이트 (intent-scope · change-impact, OMC custom)

> **이 파일이 Stage 0 3슬롯의 호출 형태 SSOT다.** 슬롯 속성(등급체계·임계선·정체 규칙)은 `54-phase4-registry.md` 행 #14~#16, Stage 흐름·라운드 카운터·체크리스트는 `10-autopilot.md` 「Stage 0」 절이 SSOT — 여기 복제하지 말 것.

### 왜 Stage 0 인가 (2026-08-19 신설)

Stage 1·2 의 13슬롯은 전부 diff **안**을 읽는다. 구현이 계획 항목을 통째로 빠뜨리거나(MISSING), 계획에 없는 변경을 끼우거나(EXTRA), 자매 파일 한쪽만 고치거나(ASYMMETRY), 바뀐 심볼의 호출자를 안 고쳐도(BROKEN CALLER) 남은 코드만 보면 "좋은 코드"라 APPROVE 가 난다. 그 결함은 발견 즉시 **큰 수정**을 부르고 다른 슬롯의 판정 전제를 전부 무효화하므로, Stage 2 끝에서 발견하면 4+9 슬롯(Codex 유료 3건 포함)을 엉뚱한 코드에 쓰고 한 라운드를 통째로 버린다. 그래서 **"리뷰할 자격이 있는 코드인가"** 를 묻는 전제 조건 리뷰를 Stage 1 **앞에** 따로 두어 fail-fast 한다. (실사례: 2026-08-14 MSF↔RFM 미러 채널에서 한쪽만 고친 결함이 수정 라운드 4·6·9·10 에 반복 — 구현자 지시는 있었으나 **그것을 재검증하는 리뷰 슬롯이 없었다**. STAT-572 에서는 Stage 1 23라운드.)

외부 선례: Qodo PR-Agent `ticket_compliance`(요구사항 재진술 → 충족/미충족 분리 → 사람 확인 항목 분리 → 무관 변경 플래그 — A 의 출력 스키마로 차용) · Blast Radius Reviewer(변경 파일에서 호출자·importer·테스트 BFS — B 의 개념으로 차용. 단 그 도구가 의존한 `code-review-graph` MCP 는 이 환경에서 제거됐으므로 **재설치 금지**, `lsp_find_references`+grep 으로 대체).

### 구성 (3슬롯, 단일 메시지 병렬)

| 슬롯 | 엔진 | 호출 | 정의 파일 |
|---|---|---|---|
| **A-Claude** `intent-scope-reviewer` | Claude | `Task(subagent_type="intent-scope-reviewer")` | `~/.claude/agents/intent-scope-reviewer.md` |
| **A-Codex** `intent-scope-reviewer(codex)` | Codex | Bash `codex-companion.mjs task --fresh` (**`--write` 없음** = read-only 샌드박스) + 위 파일 **본문 전문** 주입 | 동일 파일 (frontmatter 제거) |
| **B** `change-impact-reviewer` | Claude | `Task(subagent_type="change-impact-reviewer")` | `~/.claude/agents/change-impact-reviewer.md` |

- A 는 **양 엔진 병렬이 필수**다 — `50-critic.md` 「공통 Critic 실행 규칙」의 *"OMC critic 단독 실행 금지"* 와 동형. A 는 틀리면 라운드 전체가 엉뚱한 코드에 쓰이는 **게이트의 게이트**라 단일 모델 사각을 두지 않는다. A 에는 LSP 가 필요 없어 Codex 가 잃는 것이 없다.
- B 는 **Claude 단독**으로 시작한다 — 호출자 전수 조사에 `lsp_find_references`(OMC MCP, Codex 미가용) 가 필요하고, 기계적 전수 열거라 모델 다양성 효용이 낮다. 실측 2~3회 후 호출자 누락이 보이면 Codex(rg) 추가를 사용자에게 제안한다(자율 추가 금지).
- 두 엔진이 **같은 에이전트 정의 파일의 본문**을 쓴다 — 판정 기준이 갈라지지 않게 하기 위해서다. 에이전트 파일을 고치면 두 엔진에 동시에 반영된다.

### 호출 패턴 (MANDATORY)

**0. 입력 조립 (오케스트레이터, 호출 직전)** — Stage 0 의 품질은 리뷰어가 아니라 **여기서** 갈린다. 입력이 비면 리뷰어는 자기 추론을 기준 삼는 자기참조 검증으로 퇴행한다(그게 이 슬롯이 막는 구멍이다).
1. **scope 기준 문서**: `10-autopilot.md` 「scope 기준 문서 (우선순위)」 1~5 중 실재하는 첫 문서를 **Read 해 전문**을 확보. 요약·발췌 금지. Stage 1·2 와 **같은 문서**여야 한다.
2. **diff**: `51-codex-reviews.md` scope 선택 절차의 git 결과를 재사용 — uncommitted 만 → `git diff` / 커밋만 → `git diff <base>..HEAD` / 둘 다 → base..HEAD(uncommitted 는 stash/commit 권장). **diff 본문**과 변경 파일 목록, 작업 디렉토리 절대경로(미러 레포가 있으면 그 경로도).
3. **사용자 명시 제약**: 최소 변경 · "X 건드리지 말 것" · 환경 invariant. 없으면 `제약: 없음` 명시.
4. **`.omc/deferred/` 이월 기록 전건** + **환경 컨텍스트 블록**(`50-critic.md` 「선제 환경 컨텍스트 주입」 — Stage 0 3슬롯 전부 「프롬프트 주입」=가능 이므로 대상). 없으면 `이월: 없음`.
5. **자매 축 선언 (B 전용, MANDATORY)**: 식별 소스 ⓐ plan/spec 의 미러·쌍둥이 언급 ⓑ Phase 2 구현자의 자매 확인 보고(`40-common-loop.md` 「자매 파일·미러 레포 대칭」 산출) ⓒ AGENTS.md·프로젝트 지식. 예: `MSF ↔ RFM 채널 (src/msf/** ↔ src/rfm/**)`, `etl ↔ api 동형 로더`, `stat-common ↔ stat-docs 카탈로그`. 없으면 반드시 **`자매 축: 없음 (근거: …)`** — "알아서 찾아라"는 금지(리뷰어가 축을 발명하면 형태 카운트 과대주장이 된다).
6. **옛 값 목록 (B 전용)**: 이번 변경이 개명·교체한 식별자·숫자·상태·경로·판정 문구(Phase 2 커밋 메시지·`40-common-loop.md` ⓔ 잔존 grep 기록에서). 없으면 `옛 값: 없음`.
7. (선택) Linear 이슈 본문 — SDD 흐름(`80-sdd-workflow.md`)이면 A 에 함께 첨부.

**1. A-Claude**: `Task(subagent_type="intent-scope-reviewer", prompt = "[stage0:intent-scope]" + 입력 블록(1·2·3·4·7) + override 3줄)`
**2. A-Codex**: Bash, `run_in_background=true`:
   - `node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" task --fresh "<intent-scope-reviewer.md 본문 전문(frontmatter 제거) + \n\n[stage0:intent-scope] + 입력 블록(1·2·3·4·7) + override 3줄>"`
   - `${CLAUDE_PLUGIN_ROOT}` 미해석 시 절대경로 `/Users/june/.claude/plugins/marketplaces/openai-codex/plugins/codex/scripts/codex-companion.mjs` (settings.json allowlist 등록됨 — `50-critic.md` codex:critic 과 동일 경로).
   - **`--write` 금지.** `task` 는 `--write` 없을 때 샌드박스가 `read-only` 다(codex-companion.mjs `sandbox: request.write ? "workspace-write" : "read-only"`). 리뷰어에게 쓰기 권한을 주지 않는 것이 이 슬롯의 도구 레벨 차단이다. **PreToolUse 훅(`omc-guard.py`)이 `[stage0:` 마커가 있는 `task` 호출에 `--write` 가 있으면 차단한다.** (codex:critic 이 `--write` 로 도는 것은 그 슬롯의 기존 설정 — 여기서 바꾸지 않는다.)
   - 에이전트 파일을 Read 해 첫 `---`~두 번째 `---` 를 제거한 **본문 전문**을 주입한다. 요약·발췌 금지(critic.md 주입과 같은 규율).
**3. B**: `Task(subagent_type="change-impact-reviewer", prompt = "[stage0:change-impact]" + 입력 블록(2·4·5·6) + override 3줄)`

- **허용 subagent_type (allowlist — 이 값 외 전부 위반)**: `[stage0:intent-scope]` 마커 → **`intent-scope-reviewer`** 단 하나 / `[stage0:change-impact]` 마커 → **`change-impact-reviewer`** 단 하나. 두 에이전트는 사용자 소유(`~/.claude/agents/`, 플러그인 업데이트에 덮이지 않음)이며 frontmatter `tools` 에서 Write/Edit/NotebookEdit 를 제외해 **도구 레벨로** 파일 수정을 막는다. **PreToolUse 훅(`omc-guard.py`)이 강제한다**: 마커가 있는데 subagent_type 이 allowlist 값이 아니면 차단 / 두 subagent_type 으로 호출하면서 마커가 없으면 차단(호출 형태가 이 파일을 안 거친 신호).
- **MANDATORY — override 3줄** (세 호출 모두, 하나라도 누락 시 결과 무효 + 재호출):
  1. "리뷰 전용 모드 — 외부 상태 접촉 금지 4항(공유·운영 상태 쓰기 금지 / 리뷰 대상 레포 파일 수정 금지·프로브는 격리 사본 / in-place 명령 금지 / 산출물은 스크래치패드) 준수. 끝나면 `git status --short` 로 워킹트리 불변 확인·보고."
  2. (A) "판정 규칙: CRITICAL = MISSING·VIOLATION / MAJOR = DRIFT·EXTRA(수반 제외) / APPROVE ⇔ Fully Compliant AND CRITICAL=0 AND MAJOR=0. 최종 응답에 `판정:` 라인과 `CRITICAL=__ / MAJOR=__` 카운트 필수." · (B) "판정 규칙: CRITICAL = BROKEN CALLER·COMPAT BREAK / MAJOR = ASYMMETRY(같은 원인·계약 근거)·잔존>0·빈 칸 / MINOR 는 기록만 / APPROVE ⇔ CRITICAL=0 AND MAJOR=0. 최종 응답에 `판정:` 라인과 카운트 필수."
  3. "입력 고정: 기준 문서 = `<경로>` 전문 / diff = `<범위>` / (B) 자매 축 = `<선언>` — 리뷰어가 재판단·재탐색 금지. 입력이 비면 `판정: INPUT_MISSING`."
- **단일 메시지 mandate (Stage 0)**: 위 3개(Task 2 + Bash 1)를 **한 메시지의 tool_use 블록에 모두 포함**. 분산·누락 호출 시 Stage 0 결과 무효. Stage 1 호출과 같은 메시지에 합치기 금지(Stage 0 결과 회수·audit·종합 후에만 Stage 1 메시지). **Stop 훅(`omc-stage1-audit.py`)이 이 mandate 를 사후 감사한다** — Stage 0 마커가 하나라도 보이면 3슬롯 완결성과 체크리스트 유무를 `systemMessage` 로 알린다.

### 회수 (MANDATORY)

- A-Claude·B: Task 결과 — 호출 프롬프트에 `40-common-loop.md` 「선제 이중 채널」 보고 지시(스크래치패드 리포트 경로 + 본문 전달)를 포함한다. A-Codex: BashOutput 폴링으로 stdout 회수 완료까지 대기(read-only 샌드박스라 파일 지시 제외). 회수 못 한 슬롯은 **APPROVE 카운트 금지**, 재호출. "타임아웃이라 N/A" 금지.
- 응답에 `판정:` 라인과 카운트가 없으면 **회수 실패**로 취급, 재호출.
- **`판정: INPUT_MISSING`** 은 리뷰어 판정이 아니라 **오케스트레이터의 입력 누락 신호**다 — APPROVE 도 REJECT 도 아니며, 누락 입력을 보강해 **같은 라운드 안에서 재호출**한다(라운드 카운터 미증가). 세 번째 INPUT_MISSING 이면 사용자에게 올린다.
- 워킹트리 변경 자기신고 → 결과 무효 + 제약 강화 후 재호출(`40-common-loop.md` 「외부 상태 접촉 금지」 위반 처리 — 오케스트레이터의 "실질 영향 없음" 유효 처리 금지).

### 게이트 매핑 (MANDATORY)

- **A-Claude / A-Codex 각각**: 원판정 = 리뷰어의 `판정:` 라인. APPROVE ⇔ 총괄 Fully Compliant AND CRITICAL=0 AND MAJOR=0.
- **A 합의 판정**: **두 엔진 모두 APPROVE ⇔ A 통과.** 한쪽이라도 REJECT → A REJECT. 두 엔진이 **상반**될 때:
  - **사실형 불일치**(어떤 `R#` 의 구현 존재 여부 · 어떤 hunk 의 제약 위반 여부 · 문서와 다르게 동작하는지 여부) → 오케스트레이터가 **기준 문서와 코드를 직접 대조**해 판정하고 그 근거(파일:라인·문서 절)를 audit 표에 **인용 기재**한다(`40-common-loop.md` 「리뷰어 간 실측 충돌」 준용 — 어느 쪽도 채택하지 않고 직접 닫는다).
  - **판단형 불일치**(EXTRA 인가 수반 변경인가) → **REJECT 유지**하고, 해소는 A 규칙대로 "되돌리기" 또는 "계획 문서 갱신 + 사용자 승인" 중 하나로 사용자에게 올린다. 오케스트레이터가 "별거 아님"으로 통과시키는 것은 self-approve(`10-autopilot.md` anti-patterns).
- **B**: APPROVE ⇔ CRITICAL=0 AND MAJOR=0. MINOR(형태만 동형·참고) 는 `.omc/deferred/` 기록(레지스트리 「deferred 기여」=Y).
- **Stage 0 통과 ⇔ A 통과 AND B 통과.** 그 외 REJECT → `10-autopilot.md` 「Stage 0 게이트 판정」의 재실행 규칙.
- `requires_human_verification` 항목(A·B 공통)은 차단하지 않는다. Stage 0 audit 표에 기재하고 **Stage 2 `verifier` 호출 프롬프트에 `## requires_human_verification` 헤더(문자열 그대로) 아래 항목 목록으로 인계한다(MANDATORY — 0건이어도 헤더 + "없음")** — 버려지면 A 가 "코드만으로 판정 불가" 로 뺀 항목이 아무 데서도 검증되지 않는다. Stop 훅(`omc-stage1-audit.py`)이 Stage 2 턴의 verifier 프롬프트에 이 문자열이 없으면 경고한다.
- scope 분류(`10-autopilot.md`)는 세 슬롯 모두 **scope 안·밖 임계선이 동일(CRITICAL·MAJOR)** 하므로 판정을 바꾸지 않는다 — A 는 그 자체가 scope 판정자이고, B 의 호출자 파손은 scope 밖 파일에 있어도 파손이다. 원판정 = 최종판정(레지스트리 「원판정=최종」=Y).

### Stage 1 교차 확인 (MANDATORY — Codex 의 독립 2차 확인)

Stage 0 통과 직후의 Stage 1 `codex:critic` 호출(`50-critic.md` 「codex:critic 호출 패턴」)의 **리뷰 대상에 Stage 0 A 가 받은 것과 동일한 scope 기준 문서 전문을 반드시 포함**한다. `50-critic.md:37` 은 리뷰 대상으로 "plan 전문"을 이미 **허용**하고 있다 — 여기서 **필수화**한다. 목적은 Codex 가 A 의 판정을 **모르는 채** 한 단계 뒤에서 같은 문서 대 같은 코드를 독립으로 보게 하는 것이다. 따라서 **A 의 판정·행렬은 codex:critic 프롬프트에 주입하지 않는다**(편향 방지).

- **태그 (MANDATORY)**: 기준 문서 전문 바로 앞에 한 줄 `[stage1:scope-doc] <기준 문서 경로>` 를 둔다. 훅은 프롬프트 본문이 전문인지 볼 수 없으므로 **이 태그로 대리 검사**한다 — Stop 훅(`omc-stage1-audit.py`)이 Stage 1 턴의 codex:critic 명령에 태그가 없으면 경고한다. 태그만 붙이고 전문을 빼는 것은 `40-common-loop.md` 「검증되지 않은 단언」 위반이다.

### 정체·deferred·선제 컨텍스트 (파생 규칙 — 레지스트리 컬럼에서 도출)

세 슬롯 모두 「프롬프트 주입」=가능 → **반복형 Deadlock 규칙 대상 아님**, **발산형 정체 규칙 대상**(`50-critic.md` 「Finding 발산 조기 감지」, 전 행), **선제 환경 컨텍스트 주입 대상**(`50-critic.md`). 「deferred 기여」는 A 두 슬롯 `dismiss 시만`(A 의 비차단 산출은 `requires_human_verification` 뿐이며 이는 verifier 인계 대상이지 후속 과제가 아니다) · B `Y`(MINOR). 상세는 `54-phase4-registry.md` #14~#16.

### 잘못된 호출 금지 (anti-patterns, MANDATORY)

- ❌ A 를 **한 엔진만** 호출(Claude 만 / Codex 만) → `50-critic.md` "OMC critic 단독 금지" 와 동형 위반. 결과 무효, 누락 엔진 호출 후 합의 판정.
- ❌ A-Codex 에 `--write` → read-only 샌드박스가 이 슬롯의 도구 레벨 차단이다. 훅이 막는다. `codex:critic` 의 `--write` 를 보고 따라 붙이지 말 것.
- ❌ `Task(subagent_type=...)` 를 allowlist 밖 값(`oh-my-claudecode:verifier`·`critic`·`explore`·`general-purpose` 등)으로 대체 → 역할 충돌(verifier 는 출력 형식 고정, explore 는 파일 찾기가 본업)·Write/Edit 가능·compaction 후 기본값 복원 오답 유도. 훅이 막는다.
- ❌ scope 기준 문서를 **요약·발췌**해 주입 → 리뷰어가 INPUT_MISSING 을 내야 정상이다. 전문만.
- ❌ 자매 축을 선언하지 않고 "있으면 찾아서 봐라" → 리뷰어가 형태 카운트로 축을 발명한다(2026-08-15 `err: error` 47건 Critical 오판 형태). 없으면 "없음(근거)".
- ❌ `INPUT_MISSING` 을 REJECT 로 세어 코드 수정에 들어가거나, APPROVE 로 세어 통과 → 둘 다 금지. 입력 보강 후 같은 라운드 재호출.
- ❌ A 두 엔진 불일치를 "다수결" 이나 "Claude 우선" 으로 닫음 → 2:0 구조에 다수결은 없다. 사실형은 직접 대조, 판단형은 REJECT 유지 + 사용자.
- ❌ A 의 판정·행렬을 Stage 1 codex:critic 프롬프트에 주입 → 교차 확인의 독립성 파괴.
- ❌ Stage 0 호출을 Stage 1 메시지와 합침 / Stage 0 결과 종합 전에 Stage 1 호출 → Stage 분리 mandate 위반(Stop 훅 경고).
- ❌ **Stage 0 를 건너뛰고 Stage 1 부터 시작** → PreToolUse 훅(`omc-guard.py`)이 이 세션에 정상 Stage 0 호출 기록(`/tmp/omc-stage0-seen-<session_id>`)이 없으면 Stage 1 전용 `ocr-delegate-reviewer` Task 를 **차단**한다 — Stage 1 단일 메시지 4슬롯이 성립하지 않으므로 Stage 0 로 돌아가야 한다. (세션당 1회만 보는 약한 규칙 — 라운드별 재실행 순서는 체크리스트 + Stop 훅 경고.)
- ❌ **compaction·세션 재개 후 이 호출을 이전 대화 트랜스크립트에서 복원** → `subagent_type`·마커·`--write` 유무가 기본값으로 채워진다. **호출 형태의 SSOT 는 이 파일이다.** 세션이 재개됐으면 이 파일을 먼저 Read 하라(`00-overrides.md` 2026-08-07 위반 2건과 같은 기제).
- ❌ 리뷰어가 파일 수정·워킹트리 변경을 자기신고했는데 오케스트레이터가 "실질 영향 없음" 으로 유효 처리 → 자기신고 자체가 무효 사유.
- ❌ `requires_human_verification` 을 audit 표에만 적고 Stage 2 verifier 에 인계하지 않음 → 그 항목은 아무 데서도 검증되지 않는다.
