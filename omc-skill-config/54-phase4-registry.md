## OMC Skill Config — Phase 4 리뷰어 레지스트리 (canonical)

> **이 파일이 Phase 4 리뷰어 16슬롯의 SSOT다.**
> 다른 파일(`10-autopilot.md`·`50-critic.md`·`51-codex-reviews.md`·`53-ocr-review.md`·`55-stage0-gate.md`)은 **이 표를 복제하지 않고 가리키기만 한다.**
> 복제본이 생기면 한쪽만 갱신돼 사각이 난다 — 그게 이 표가 생긴 이유다(2026-08-07 실제 사고: `pr-review-toolkit`이 정체 규칙 어디에도 안 들어가 9라운드를 소진).

### 설계 원칙 (MANDATORY)

**규칙의 적용 대상을 명단·Phase로 하드코딩하지 말고 표의 「속성 컬럼」에서 도출한다.**
이름을 박아 두면 리뷰어가 추가되거나 성격이 바뀔 때 규칙이 따라가지 못하고, 어느 규칙에도 안 걸리는 슬롯이 생긴다.
안 걸리는 슬롯은 **무한 차단이 가능**하고, 그 상태는 라운드를 다 태우기 전까지 보이지 않는다.

---

### 리뷰어 레지스트리 (16슬롯 — Stage 0 3 + Stage 1 4 + Stage 2 9)

`#` 은 **등록 순**이고 실행 순서는 `St` 열(0 → 1 → 2)이다 — Stage 0 행(#14~#16)은 2026-08-19 에 추가돼 번호가 뒤지만 **가장 먼저** 실행된다.

| # | St | 슬롯 | 호출 방식 | 등급체계 | scope 안 차단 | scope 밖 차단 | deferred 기여 | 원판정=최종 | 프롬프트 주입 | 정체 규칙 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | `codex:review` | Bash raw CLI `codex review <대상 flag>` | 확인(P1/P2) | `P1` | `P1` | Y | N | **불가** | 반복형 + 발산형 |
| 2 | 1 | `codex:adversarial-review` | Bash companion `adversarial-review` | 확인(JSON: critical/high/medium/low) | `critical`·`high` | `critical`·`high` | Y | N | **불가** | 반복형 + 발산형 |
| 3 | 1 | `codex:critic` | Bash companion `task --fresh --write` + critic.md 전문 | 확인(CRITICAL/MAJOR/MINOR) | CRITICAL/MAJOR 기반 기존 판정 | `CRITICAL`·`MAJOR` | Y | N | 가능 | 발산형 |
| 4 | 1 | `ocr:delegate-review` | Task(`subagent_type="ocr-delegate-reviewer"`) — allowlist 단일 | 확인(High/Medium/Low) | High·Medium 차단, Low 폐기 | `High`만 | Y | N | 가능 | 발산형 |
| 5 | 2 | `architect` | Task(`oh-my-claudecode:architect`) | 확인(등급 부여를 프롬프트로 요구) | `CRITICAL`·`MAJOR` | `CRITICAL`·`MAJOR` | Y | N | 가능 | 발산형 |
| 6 | 2 | `security-reviewer` | Task(`oh-my-claudecode:security-reviewer`) | 확인 | CRITICAL/HIGH | 동일 | Y | N | 가능 | 발산형 |
| 7 | 2 | `code-reviewer` | Task(`oh-my-claudecode:code-reviewer`) | 확인 | CRITICAL/HIGH @HIGH confidence | 동일 | Y | N | 가능 | 발산형 |
| 8 | 2 | `test-engineer` | Task(`oh-my-claudecode:test-engineer`) | 확인 | 기존 판정 로직 | gap `Risk=High` 또는 `Test Health=CRITICAL` | Y | N | 가능 | 발산형 |
| 9 | 2 | `critic` (OMC) | Task(`oh-my-claudecode:critic`) | 확인(CRITICAL/MAJOR/MINOR) | CRITICAL/MAJOR | 동일 | Y | N | 가능 | 발산형 |
| 10 | 2 | `verifier` | Task(`oh-my-claudecode:verifier`) | 확인(Blockers) | Blockers ≥ 1 | 동일 | Y | N | 가능 | 발산형 |
| 11 | 2 | `code-simplifier` | Task(`oh-my-claudecode:code-simplifier`) + review-only 제약 | 이진(등급 없음) | 변경 라인 내 항목 ≥ 1건 | 전부 기록 | Y(scope 밖분) | N | 가능 | 발산형 |
| 12 | 2 | `Skill(security-review)` | `Skill(skill="security-review")` | **미확인** | 비-APPROVE 전건 | 동일 | dismiss 시만 | N | **불가** | 반복형 + 발산형 |
| 13 | 2 | `Skill(pr-review-toolkit:review-pr)` | `Skill(skill="pr-review-toolkit:review-pr")` | 확인(Critical/Important/Suggestions) | Critical·Important | **동일** | **N** | **Y** | 가능(args) | 발산형 |
| 14 | 0 | `intent-scope-reviewer` (A-Claude) | Task(`subagent_type="intent-scope-reviewer"`) + `[stage0:intent-scope]` 마커 — allowlist 단일 | 확인(CRITICAL/MAJOR — 에이전트 정의에 고정) | `CRITICAL`·`MAJOR` | **동일**(이 슬롯이 scope 판정자) | dismiss 시만 | **Y** | 가능 | 발산형 |
| 15 | 0 | `intent-scope-reviewer(codex)` (A-Codex) | Bash `codex-companion.mjs task --fresh` (**`--write` 금지** = read-only 샌드박스) + #14 정의 파일 본문 전문 + `[stage0:intent-scope]` 마커 | 확인(CRITICAL/MAJOR — 동일 본문) | `CRITICAL`·`MAJOR` | **동일** | dismiss 시만 | **Y** | 가능 | 발산형 |
| 16 | 0 | `change-impact-reviewer` (B) | Task(`subagent_type="change-impact-reviewer"`) + `[stage0:change-impact]` 마커 — allowlist 단일 | 확인(CRITICAL/MAJOR/MINOR — 에이전트 정의에 고정) | `CRITICAL`·`MAJOR` | **동일**(호출자 파손은 scope 밖 파일이어도 파손) | Y(MINOR) | **Y** | 가능 | 발산형 |

- **scope 안 차단** 열은 현행을 베껴 적은 것 — 새 규칙이 아니며 **오케스트레이터의 자율 완화·강화 금지**(사용자 승인 후 이 표를 고치는 것만 허용).
  - **2026-08-15 개정 ③ — `codex:review` 가드 A 해제: 「등급체계」 `미확인`→`확인(P1/P2)`, scope 안·밖 차단 `비-APPROVE 전건`→`P1`, 「deferred 기여」 `dismiss 시만`→`Y`** (사용자 승인). **해제 근거 = 서로 다른 실행 3회 일관 확인**(etl STAT-572 Phase 4 Stage 1 라운드 3·4·5 — `[P1]`/`[P2]` 라벨). 등급 부여도 타당했다: `P1` 은 데이터 부활 경로(watermark 미전진)에, `P2` 는 입력 검증·라벨 오진에 갔다. **유지 비용이 실측됐다** — 라운드 4 에서 차단으로 계산된 `P2` 는 **이미 이월 확정된 항목**이었고, 라운드 5 는 **`P1`=0 인데 `P2` 3건으로 막혔다**. 이는 아래 개정 ①이 `architect` 에서 기록한 것과 같은 형태(*"좋은 리뷰어일수록 MINOR 를 하나쯤 찾으므로 사실상 통과 불가능한 슬롯"*)다. ⚠️ **scope 안·밖을 동시에 `P1` 로 맞췄다** — 한쪽만 고치면 개정 ①이 지적한 역전(`scope 밖 P2 는 통과 / scope 안 P2 는 차단`)이 그대로 재현된다. 가드 A 는 **등급을 모를 때의 fail-safe** 이므로 전제가 해소되면 유지가 신중함이 아니라 낡은 설정이다. 「프롬프트 주입」=**불가**는 그대로이므로 **반복형 정체 규칙 대상은 유지**한다(등급 유무와 무관한 별개 사유 — 개정 ②와 동일 논리).
  - **2026-08-08 개정 ② — `codex:adversarial-review` scope 안: `finding ≥ 1건` → `critical`·`high`** (사용자 승인). architect 와 **같은 형태**(등급이 확인됐는데 scope 안만 이진)이나 옛 주석의 사유는 달랐다 — *"needs-attention 존중, 현행 유지"*, 즉 리뷰어 **자신의 판정**을 존중한다는 축이었다. 그럼에도 올리는 이유: 이 슬롯은 **「프롬프트 주입」= 불가**라 이월 결정을 영구히 인지하지 못한다(2026-08-08 실사고 — round 2 에 이월한 항목을 round 10 에 동일 요지·동일 근거로 재지적해 사용자 dismiss 로 끝났다). **주입 불가 + 임계선 최저**의 조합은 라운드를 태우는 구조이고, 등급 체계가 확인된 이상 등급으로 거르는 것이 맞다. medium 이하는 deferred 로 간다(「deferred 기여」= Y 유지). 자기 판정(`needs-attention`)은 **원판정 컬럼에 그대로 기재**되므로 감사 추적은 유지된다.
  - **2026-08-08 개정 ① — `architect` scope 안: `finding ≥ 1건` → `CRITICAL`·`MAJOR`** (사용자 승인). 사유: 이 슬롯은 원래 **등급 체계가 없어** 이진 판정이었고, scope 분류 도입 때 **scope 밖 임계선을 세우려고** 등급 부여를 새로 요구했다(옛 표 주석 *"현행 이진 유지"* / *"등급 신규 요구"*). 그 결과 **등급을 받아 놓고 scope 밖에서만 쓰고 scope 안은 옛 이진 동작으로 남아**, `scope 밖 MINOR 는 통과하는데 scope 안 MINOR 는 차단`이라는 역전이 생겼다. 같은 등급 체계를 쓰는 `critic`(CRITICAL/MAJOR)과도 어긋난다. 실사례: 2026-08-08 Round 10·#P=1 에서 architect 가 **원판정 APPROVE + scope 안 MINOR** 를 냈는데 규칙상 차단이 됐다 — 좋은 리뷰어일수록 MINOR 를 하나쯤 찾으므로 **사실상 통과 불가능한 슬롯**이 된다.
- **deferred 기여 = N**인 슬롯(#13)은 scope 분류가 판정을 바꾸지 않으므로 **원판정 = 최종판정**이다. 그래서 이 슬롯만 이월 밸브가 없고, 정체 규칙 의존도가 가장 높다.
- **Stage 0 행(#14~#16)** 은 scope 안·밖 임계선이 **동일**하므로 역시 원판정 = 최종판정이다(#14·#15 는 A 자체가 scope 판정자, #16 은 호출자 파손이 scope 와 무관). #14·#15 의 「deferred 기여」가 `dismiss 시만` 인 이유: A 의 비차단 산출은 `requires_human_verification` 뿐이고 그것은 **Stage 2 verifier 인계** 대상이지 후속 과제(deferred)가 아니다. #14 와 #15 는 **같은 정의 파일 본문을 두 엔진이 읽는** 한 쌍이며 **둘 다 APPROVE 여야 A 통과**(합의 판정·불일치 처리는 `55-stage0-gate.md` 「게이트 매핑」). 등급체계 `확인` 근거: 출력 형식이 에이전트 정의 파일에 고정돼 있어 #3 codex:critic(critic.md 주입) 과 같은 지위.
- Suggestions·ocr Low 등 **기존 비차단 등급은 기존 처리 유지** — deferred 파일 대상 아님. deferred 대상 = **scope 밖의 "차단 등급 미만" finding**.

---

### 파생 규칙 — 컬럼에서 도출한다 (MANDATORY)

| 파생 규칙 | 적용 대상 도출식 | 현재 해당 슬롯 |
|---|---|---|
| **가드 A** (등급 미확인 → 비-APPROVE 전건 차단, fail-safe) | 「등급체계」= **미확인**인 행 전부 | #12 |
| **반복형 정체**(Deadlock — 같은 지적 되풀이) | 「프롬프트 주입」= **불가**인 행 전부 | #1, #2, #12 |
| **발산형 정체**(매 라운드 새 지적) | **전 행** — Stage·Phase·주입 가능 여부 무관 | #1~#16 |
| **deferred 기록 대상** | 「deferred 기여」= **Y**인 행의 "차단 등급 미만" finding | #1~#11, #16 |
| **원판정 = 최종판정** | 「원판정=최종」= **Y**인 행 | #13, #14, #15, #16 |
| **선제 환경 컨텍스트 주입**(`50-critic.md`) | 「프롬프트 주입」= **가능**인 행 전부 | #3~#11, #13~#16 |

- **가드 A 해제**: 실제 출력에서 등급 체계가 **서로 다른 실행 2회 이상 일관 확인**되면, 이 표의 「등급체계」를 `확인`으로 바꾸고 「scope 밖 차단」에 임계선을 적는다. 자율 해제 금지 — 사용자 승인 후 표 갱신.
  - ⚠️ **해제 시 「scope 안 차단」 칸도 반드시 함께 재검토한다.** 등급이 없던 시절의 `finding ≥ 1건`(이진)이 그대로 남으면, **등급을 확인해 놓고 scope 밖에서만 쓰는 반쪽 적용**이 되어 `scope 밖 MINOR 는 통과 / scope 안 MINOR 는 차단`이라는 역전이 생긴다. 이 절차가 「scope 밖」만 지목하고 있었던 것이 2026-08-08 architect 드리프트의 **절차적 원인**이다. 재검토 결과 이진을 유지하기로 정했다면 **그 사유를 표 아래에 적는다**(예: `code-simplifier` — 등급 체계 자체가 없어 임계선이 무의미).
- **정체 규칙의 조건·보고 형식·선택지는 `50-critic.md`가 canonical.** 이 표는 **누가 대상인가**만 정한다.

---

### 완결성 자기검사 (MANDATORY)

> **「정체 규칙」 컬럼이 비어 있거나 `없음`인 행이 존재해서는 안 된다.**
> 비어 있으면 그 슬롯은 무한 차단이 가능하고, 라운드를 다 태우기 전까지 아무도 모른다.
> 「발산형」은 전 행 기본값이므로 최소값이 `발산형`이다 — 새 행을 추가할 때 이 칸을 `없음`으로 두지 말 것.

행을 추가·수정할 때 아래를 확인한다.
- [ ] 11개 컬럼이 전부 채워졌는가? (빈 칸 0개)
- [ ] 「정체 규칙」이 최소 `발산형`인가?
- [ ] 「등급체계」= 미확인이면 「scope 안/밖 차단」이 둘 다 "비-APPROVE 전건"인가? (가드 A fail-safe)
- [ ] 「deferred 기여」= N이면 「원판정=최종」= Y인가? (이월 불가 = scope 분류가 판정을 못 바꿈)
- [ ] Stage 0 행 합 = 3, Stage 1 행 합 = 4, Stage 2 행 합 = 9, 총 16인가?
- [ ] Stage 0 행의 「scope 안 차단」=「scope 밖 차단」이고 「원판정=최종」= Y 인가? (Stage 0 는 scope 분류 대상이 아니다 — `55-stage0-gate.md`)

---

### 슬롯별 특례 (호출·판정에 붙는 추가 제약)

**#11 `code-simplifier`**
- **심사 범위**: 이번 작업에서 변경/추가한 라인으로 한정. 손대지 않은 기존 코드의 단순화 지적 금지(원본 보존). 기존 코드 지적은 게이트 미반영 + deferred 기록.
- **판정**: 변경 라인 내 단순화 항목 있음 → REJECT(이진 유지, 등급 도입 안 함). "복잡함"은 크리티컬이 될 수 없어 등급 임계선이 무의미 — 범위를 좁혀 실효성을 확보한다.
- **호출 시 review-only 제약 문구 필수**(미포함 시 결과 무효 + 재호출): 코드/파일 수정 절대 금지(Edit/Write 금지) · 위치와 제안만 작성 · 판정 규칙 명시 · "심사 범위: 이번 변경 라인 한정".

**#13 `Skill(pr-review-toolkit:review-pr)`**
- **APPROVE 조건**: Critical = 0 **AND** Important = 0. 그 외 REJECT.
- Critical·Important는 **scope 안팎 불문 차단** → 원판정 = 최종판정(위 표와 정합). Suggestions만 보고서 minor 기록으로 빠지며 **deferred 기여 0건**이다.
- **내부 code-simplifier 자동 분리**: 게이트 단계에서는 자동 호출되지 않아야 한다. 결과에서 호출 정황(파일 수정, "simplified the following files" 등)이 보이면 **결과 무효** 처리하고 args에 `code errors comments tests types`를 명시해 재호출.
- **부분 재실행 단위**: 내부 서브에이전트 선택 재실행 불가 — **슬래시 전체를 1슬롯으로** 재호출한다. 단 comment-analyzer 단독 blocking이면 `10-autopilot.md`의 「comment-analyzer 단독 반려 단축 경로」가 우선.

**#4 `ocr:delegate-review`**
- `subagent_type` allowlist는 **`ocr-delegate-reviewer` 단 하나**. 호출 패턴 상세는 `53-ocr-review.md`.

**#1~#3 codex 계열**
- 전부 **Bash 직접 호출만** 허용. `Task(subagent_type="codex:*")`·`Skill(skill="codex:review"|"codex:adversarial-review")` 금지. 호출 상세는 `51-codex-reviews.md`(#1·#2), `50-critic.md`(#3).
- **#3 codex:critic 리뷰 대상에는 Stage 0 A 가 받은 것과 동일한 scope 기준 문서 전문을 포함하고 그 앞에 `[stage1:scope-doc] <경로>` 태그를 둔다**(`55-stage0-gate.md` 「Stage 1 교차 확인」 — Codex 의 독립 2차 확인. A 의 판정은 주입하지 않는다. Stop 훅이 태그 부재 경고).

**#14~#16 Stage 0 계열**
- 호출 형태·입력 조립·override 3줄·A 합의 판정·`INPUT_MISSING` 처리·`requires_human_verification` 인계는 **`55-stage0-gate.md` 가 SSOT**. 세 호출은 **단일 메시지 병렬**, Stage 1 메시지와 분리.
- `subagent_type` allowlist 는 마커별 단 하나(`[stage0:intent-scope]`→`intent-scope-reviewer`, `[stage0:change-impact]`→`change-impact-reviewer`). #15 는 `--write` 금지. PreToolUse 훅(`omc-guard.py`)이 셋 다 강제.
- #14 와 #15 는 **쌍**이다 — 한쪽만 호출하면 A 결과 무효(`50-critic.md` "OMC critic 단독 금지" 와 동형). 부분 재실행 단위는 슬롯 단위(REJECT 한 엔진만)이되, A 통과 판정은 항상 두 엔진의 동시점 APPROVE 로 한다.

---

### 회수 규율 · 리뷰어 간 실측 충돌 · 자매 대칭 · 외부 상태 접촉 금지 · 자기보고 검증

전부 Phase 4 전용이 아니라 **서브에이전트를 쓰는 전 구간 공통**이므로 `40-common-loop.md`가 canonical이다. 여기 복제하지 말 것.

- **서브에이전트 산출물 회수 규율** — 완료 신호만 오고 본문이 안 오는 경우의 3단 사다리(답장 본문 명시 → 파일 채널 → 신규 재호출), "2차까지 실패하면 방식이 아니라 경로를 의심한다" 판단 기준, **회수 요청에 새 과제 금지**. Phase 4 에서 회수 실패는 곧 "APPROVE 로 카운트 금지"이므로 이 사다리가 게이트 진행의 전제다.
- **리뷰어 간 실측 충돌** — 상반된 실측은 어느 쪽도 채택하지 않고 오케스트레이터가 격리 사본에서 직접 재현해 판정하며, 그 명령·결과를 **Stage audit 표에 인용 기재**한다.
- **자매 파일·미러 레포 대칭** — 수정 항목마다 자매 확인 결과를 보고에 기재. 병렬 위임 시 자매 파일은 같은 레인에 묶는다.
