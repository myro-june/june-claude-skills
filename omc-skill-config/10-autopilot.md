## OMC Skill Config — autopilot

**autopilot:** maxIterations=20, maxQaCycles=7, maxValidationRounds=15, maxPartialRerunRounds=15, pauseAfterExpansion=true, pauseAfterPlanning=true, phase3Agents=[debugger], phase4Agents=[intent-scope-reviewer, intent-scope-reviewer(codex), change-impact-reviewer, codex:review, codex:adversarial-review, codex:critic, ocr:delegate-review, architect, security-reviewer, code-reviewer, test-engineer, critic, verifier, code-simplifier, builtin-slash:/security-review, builtin-slash:/pr-review-toolkit:review-pr]

- **pauseAfterExpansion/pauseAfterPlanning — SDD 흐름 조건부 자동 스킵 (2026-08-20 개정 — 멈춤 최소화)**: 사용자 승인을 이미 거친 기준 문서(deep-interview `-spec.md` · ralplan `-plan.md` — `80-sdd-workflow.md` 흐름 산출물)가 이번 실행의 scope 기준 문서로 존재하면 두 pause 를 **자동 스킵**하고 1줄 보고한다("승인된 <파일명> 감지 — pause 스킵, Phase 0/1 Critic 게이트는 그대로 실행"). 스킵되는 것은 사용자 재승인 대기뿐이다 — Phase 0/1 Critic 게이트(비통과 시 다음 Phase 진입 금지)와 Phase 4 Stage 0 `intent-scope-reviewer`의 기준 문서 전문 대조(MISSING/EXTRA/DRIFT)는 그대로 실행되어 승인 문서 이탈을 기계적으로 차단한다. 승인된 기준 문서가 없는 단독 실행은 현행 유지(두 pause 실행) — 이때의 pause 는 구현 진입 전 방향 오류를 잡는 최저비용 지점이다.
  - **스킵 시 자체 검증 체크리스트 출력 (MANDATORY)**: [ ] 승인된 기준 문서 경로 기재 / [ ] 사용자 승인 근거 기재(승인 대화·이슈·브랜치 푸시 중 하나) / [ ] 스킵 보고 1줄 출력 / [ ] Phase 0/1 Critic 게이트 실행 유지 명시 / [ ] Phase 4 Stage 0 `intent-scope-reviewer` 기준 문서 대조가 이 승인 문서를 기준으로 실행됨을 명시. 하나라도 못 채우면 스킵 금지 — 현행 pause 유지.
- Phase 0 (Expansion) Critic: `50-critic.md`의 **공통 Critic 실행 규칙** 참조.
- **MANDATORY — Phase 0 수정 후 루프**: `40-common-loop.md`의 **공통 — 수정 후 루프 규칙** 참조.
- Phase 1 (Planning) Critic: `50-critic.md`의 **공통 Critic 실행 규칙** 참조.
- **MANDATORY — Phase 1 수정 후 루프**: `40-common-loop.md`의 **공통 — 수정 후 루프 규칙** 참조.
- **MANDATORY — Phase 0/1 Critic finding scope 분류**: `30-ralplan.md`의 **scope 고정** 절 준용 (체크리스트·anti-patterns 포함). scope 기준 = Phase 0은 사용자 원 요청, Phase 1은 Phase 0 확정 spec. scope 밖 finding은 산출물(spec/plan)을 확장하지 말고 Follow-ups에 기록만 하며, scope 밖은 CRITICAL/MAJOR만 차단.
- Phase 3 실행 시 phase3Agents에 나열된 에이전트를 사용할 것. **ultraQA 모드(ultraqa)를 Phase 3에서 항상 실행**할 것.
- **MANDATORY — Phase 2 구현·Phase 3 수정(debugger/ultraqa fix 포함) 시 `40-common-loop.md`의 "공통 작업 원칙"(scope 고정 + 최소 변경 + §4 구현 스타일 — TDD 고전파·조회 쿼리 성능, 정의는 `00-overrides.md` 「공통 구현 원칙 — 전역」) 적용.** scope 밖 발견은 deferred 기록 후 배제 — QA 중 발견한 개선거리를 자의로 구현하지 말 것.

### Phase 4 — 3-Stage Gate (MANDATORY)

Phase 4는 **3-stage gate (Stage 0 → Stage 1 → Stage 2)**로 실행한다. SKILL.md 기본값(3개 병렬) 사용 금지.

**전체 흐름**:
0. **Stage 0 (3개: intent-scope A-Claude + A-Codex + change-impact B — 정합 선행 게이트)** 단일 메시지 병렬 호출 → 회수 → audit → 종합. 호출 형태는 `55-stage0-gate.md` 가 SSOT. **라운드 카운터 +1 은 여기서** (아래 「maxValidationRounds 카운트 규칙」).
1. Stage 0 **전원 APPROVE**(A 는 두 엔진 합의) 시에만 **Stage 1 (4개: Codex 팀 3 + OCR 1)** 단일 메시지 병렬 호출 → 회수 → audit → 종합
2. Stage 1 **전원 APPROVE** 시에만 Stage 2 진입. 1건이라도 REJECT/REQUEST CHANGES → Stage 1 게이트 실패.
3. **Stage 2 (나머지 9개)** 단일 메시지 병렬 호출 → 회수 → audit → 종합
4. Stage 2 전원 APPROVE 시 Phase 4 통과. (단, **부분 재실행으로 깨끗해진 경우는 종료가 아니라 Stage 0부터 재시작** — 아래 REJECT 처리 참조.)

**왜 Stage 0 가 앞인가**: Stage 0 가 잡는 결함(계획 항목 누락·계획 밖 변경·호출자 미갱신·자매 비대칭)은 발견 즉시 **큰 수정**을 부르고 다른 슬롯의 판정 전제를 전부 무효화한다. Stage 2 끝에서 발견하면 4+9 슬롯(Codex 유료 3건 포함)을 엉뚱한 코드에 쓰고 한 라운드를 버린다. 그래서 **"리뷰할 자격이 있는 코드인가"** 를 Task 2 + Bash 1 로 먼저 싸게 묻는다 — 코드가 수정된 뒤의 다음 호출은 항상 Stage 0 부터다(Stage 2 내부 부분 재실행만 예외 — 그 루프는 P 카운터로 닫히고, 클린 후 Stage 0 부터 재시작할 때 Stage 0 가 누적 수정을 한 번에 본다).

**REJECT 처리**:
- **Stage 0 REJECT** → 코드 수정 → **REJECT한 슬롯만 재실행**(A 는 REJECT 한 엔진만; 단 A 통과 판정은 항상 두 엔진의 동시점 APPROVE) → REJECT였던 슬롯 전원 APPROVE → **Stage 0 3슬롯 전체 1회 확인 실행**(동시점 일관 APPROVE 안전장치 — 여기서 REJECT 가 나오면 그 슬롯만 다시 부분 루프) → 확인 실행 전원 APPROVE 시 Stage 1 진입. `INPUT_MISSING` 은 REJECT 가 아니다(입력 보강 후 같은 라운드 재호출, 카운터 미증가 — `55-stage0-gate.md` 「회수」).
- **Stage 1 REJECT** → 코드 수정 → **Stage 0 재실행**(3슬롯 — 수정이 정합을 깨지 않았는지 먼저 확인, 카운터 +1) → Stage 0 통과 시 **Stage 1 의 REJECT한 슬롯만 재실행**(Stage 2 와 같은 방식 — Stage 2 진입 금지는 그대로). REJECT였던 슬롯 전원 APPROVE → **Stage 1 4슬롯 전체 1회 확인 실행**(동시점 일관 APPROVE 안전장치 — 이 확인 실행에서 REJECT 가 나오면 그 슬롯만 다시 부분 루프). 확인 실행 전원 APPROVE 시 Stage 2 진입. **단, 수정이 주석/문서 전용·테스트 전용이면 아래 각 「단축」 절이 본 경로에 우선한다.** (2026-08-18: STAT-572 Stage 1 23라운드 중 대다수가 1~2슬롯 차단이었는데 매번 4슬롯 전량 재호출했다 — R4 ocr 만 · R6 critic 만(codex:review finding 0) · R11 review+ocr. 부분 재실행이면 Stage 1 호출이 절반 이하. 오늘 규칙의 「4슬롯 전량」은 마지막 확인 실행 1회로 그대로 남는다.)
- **Stage 2 REJECT** → 코드 수정 → **REJECT한 reviewer만 재실행** (APPROVE한 reviewer는 재실행 안 함). 또 REJECT면 수정 → REJECT한 것만 재실행 반복 (부분 루프, 한 시도 내 최대 maxPartialRerunRounds=15회 — 초과 시 사용자 보고 후 정지). REJECT였던 reviewer 전원 APPROVE = Stage 2 통과 → **Stage 0부터 전체 재시작** (Stage 0 3개 → Stage 1 4개 → 통과 시 Stage 2 9개). 전체 9개 재실행은 Stage 0·1 복귀 후에만. **카운터 리셋 없음** (Stage 0 재시작 시 +1). 재시작 웨이브의 슬롯별 재호출 여부는 아래 **「diff 불변 슬롯 재사용」**을 따른다.
- **부분 재실행 단위 = Stage 2의 9개 호출 슬롯**: #1~#7(OMC subagent)·#8(`/security-review`)는 슬롯=호출이라 REJECT한 해당 슬롯만 재호출한다. #9(`/pr-review-toolkit:review-pr`)는 내부 6개 서브에이전트를 자동 호출하는 오케스트레이션 슬래시이므로 **슬래시 전체를 1슬롯으로 재호출**(내부 서브에이전트 선택 재실행 불가). 단 #9가 comment-analyzer 단독 blocking인 경우는 아래 **comment-analyzer 단독 반려 단축 경로**가 우선.
- **왜 부분 클린이 종료가 아닌가**: 부분 재실행 사이의 코드 수정이 이미 APPROVE한 reviewer의 판정 전제를 무효화할 수 있다. 따라서 Stage 0부터 fresh하게 전체(Stage 0 3 + Stage 1 4 + Stage 2 9)를 다시 통과해야만 '동시점 일관 APPROVE'가 보장되며, 이때만 Phase 4 통과로 인정한다. (이 안전장치를 "부분 클린이면 그냥 종료"로 단순화 금지.)

**diff 불변 슬롯 재사용 — 풀 재시작 라운드 한정 (MANDATORY — 2026-08-21 신설)**:
- **적용 시점**: 「Stage 2 부분 재실행 클린 → Stage 0부터 전체 재시작」의 **재시작 라운드에서만**. 최초 진입·REJECT 슬롯 재실행·확인 실행에는 적용하지 않는다 (그 호출들은 직전 판정이 APPROVE가 아니거나 판정 재료가 바뀐 뒤라 재사용할 것이 없다).
- **판정 기준 — 판단이 아니라 해시 대조**: 재시작 웨이브 호출 직전, 판정 재료 해시 `H = sha256(scope 기준 문서 전문 + 리뷰 대상 diff 전문)` 를 계산한다. 어떤 슬롯의 **마지막 APPROVE 시점 H와 현재 H가 동일**하면 그 슬롯은 재호출하지 않고 APPROVE를 재사용하며, audit 표 원판정에 `APPROVE(diff 불변 재사용, R<n> 판정)` 으로 기재한다. H가 다르거나 · 마지막 판정이 APPROVE가 아니거나 · 회수 실패였거나 · **H 기록이 없으면** 재호출한다 (기록 부재 시 전량 재호출이 fail-safe 기본값).
- **원리**: 전체 재시작의 근거는 위 「왜 부분 클린이 종료가 아닌가」의 "수정이 이미 APPROVE한 reviewer의 판정 전제를 무효화할 수 있다"이다. 판정 재료가 바이트 단위로 동일하면 그 전제는 무효화되지 않았다 — 본 규칙은 그 근거의 기계화이지 완화가 아니다. 잃는 것은 **비결정성 재관측**(같은 재료를 두 번 보여 첫 호출의 누락을 잡는 효과) 하나뿐이고, H는 diff 전문 기준이라 코드가 1줄이라도 변하면(테스트·주석 포함) 전 슬롯이 재호출된다 — 재사용되는 것은 **최종 diff를 이미 fresh하게 본 슬롯**뿐이다.
- **H 기록**: 매 웨이브(본 웨이브·부분 재실행 웨이브)마다 deferred 파일 「라운드 기록」 줄에 H 앞 12자리를 남긴다 (아래 「deferred 기록 파일 규격」).
- **단일 메시지 mandate와의 관계**: 재사용 슬롯이 있는 재시작 웨이브에서 각 Stage의 단일 메시지 mandate는 「**재호출 대상 슬롯 전부**를 한 메시지에」로 읽는다. 재사용 슬롯은 호출 누락이 아니다 — audit 표의 `APPROVE(diff 불변 재사용, R<n> 판정)` 표기가 그 증빙이며, Stop 훅(omc-stage1-audit.py)의 슬롯 누락 경고에는 이 표기로 답한다. (실제로 Stage 0·1은 재시작 시점에 항상 H가 달라져(직전 라운드의 수정이 그 판정 이후다) 전량 재호출된다 — 재사용은 주로 최종 수정 후 부분 재실행으로 최신 diff를 본 Stage 2 슬롯에서 발생한다.)
- (2026-08-21 STAT-589 실측: 풀 재시작 R2·R3 ~2h17m 에서 신규 차단 1건. 그 1건(test-engineer 증인부재①)도 직전 수정으로 diff가 변한 뒤라 본 규칙 하에서도 재호출 대상이었다 — 규칙이 이 finding을 놓치지 않으면서 동일 재료 재관측분만 걷어낸다.)
- ❌ anti-patterns: 해시 대조 없이 "수정이 사소했으니" 재사용 / H 불일치 슬롯 재사용 / 재시작 아닌 경로(확인 실행·REJECT 재실행·최초 진입)로의 확대 적용 / H 기록 부재 상태에서의 재사용.

**maxValidationRounds=15**: **1 시도 = 1라운드** — **Stage 0을 (재)시작할 때마다 +1** (Stage 0 단독 미통과로 재시작하든, Stage 1 미통과로 수정 후 Stage 0에 복귀하든, Stage 2 미통과로 Stage 0에 복귀하든 무조건 +1). Stage 1 4개·Stage 2 9개 호출은 그 시도의 일부라 별도 카운트 안 함. **리셋 없음** (어떤 경우에도 0 초기화 금지). 한도 15 도달 시 사용자 보고 후 정지. (Stage 2 내부 부분 재실행은 별도 `maxPartialRerunRounds=15`로 제한. Stage 0 의 `INPUT_MISSING` 재호출은 카운터 미증가.)

**Stage 간 메시지 분리**: Stage 0·Stage 1·Stage 2는 **반드시 각각 다른 메시지(순차 실행)**. 동일 메시지에 합치기 금지. 앞 Stage 결과 회수·audit·종합 완료 후에만 다음 Stage 메시지 작성.

**MANDATORY — 전 Stage(0·1·2) 호출 프롬프트에 「외부 상태 접촉 금지」 4항 포함**: `40-common-loop.md` 「공통 — 서브에이전트 외부 상태 접촉 금지」가 canonical이다(공유·운영 상태 쓰기 금지 · 리뷰 대상 레포 파일 수정 금지 · in-place 명령 금지 · 산출물은 스크래치패드 한정). 여기 복제하지 말 것. 미포함 호출은 **결과 무효 + 재호출**이며, 위반 자기신고 역시 그 자체로 무효 사유다(오케스트레이터의 "실질 영향 없음" 유효 처리 금지 — 기존 ocr review-only 규정과 동일 원리를 전 슬롯으로 확장). 리뷰어가 **차단당한 명령을 대신 실행해 달라거나 권한을 풀어 달라고 요청하면 거부하고 사용자에게 올린다.**

**MANDATORY — 리뷰어의 환경 상태 주장은 오케스트레이터가 직접 확인**: `40-common-loop.md` 「공통 — 에이전트 자기보고는 주장이지 사실이 아니다」 준용. 리뷰 **판정**은 그대로 받되 **상태 서술**(적용됨·정리됨·생성됨·롤백됨)은 읽기 전용으로 확인한 뒤에만 근거로 쓴다.

---

### Phase 4 — scope 고정 및 finding 분류 (MANDATORY)

scope를 벗어나는 finding은 게이트를 차단하지 않고 기록만 하여 Scope Creep을 방지한다. 단 크리티컬 항목은 예외로 차단한다.

#### 용어 정의

- **원판정** = reviewer가 낸 판정 그대로 (변경 금지, audit 표 기재용)
- **최종판정** = scope 분류를 거친 뒤 게이트가 실제로 쓰는 판정
- **Phase 4 전체에서 게이트 판정·재실행 규칙의 APPROVE/REJECT는 전부 최종판정 기준이다.** 위쪽 "전체 흐름"·"REJECT 처리" 항목의 `전원 APPROVE`·`REJECT`도 여기에 포함된다 (본 정의가 소급 적용). 원판정은 audit 표 기재 및 감사 추적 용도로만 쓴다.

#### scope 기준 문서 (우선순위)

1. `.omc/plans/autopilot-impl.md` (Phase 1 산출물)
2. `.omc/plans/ralplan-*.md` | `.omc/plans/consensus-*.md` (ralplan 재사용 시)
3. `.omc/specs/deep-interview-*.md`
4. `.omc/autopilot/spec.md` (Phase 0)
5. 위가 전부 없으면 사용자 원 요청 텍스트

- 위 순서로 **실재하는 첫 문서**를 기준으로 삼는다.
- **scope 안** = 기준 문서에 명시된 작업 항목/요구사항에 해당하는 것.
- **scope 밖** = 그 외 전부. **변경한 파일 내부라도 기준 문서에 없으면 scope 밖.**
- 판정은 **기준 문서 대조**로만 한다. 추측 판정 금지.

#### finding 분류 규칙

- **scope 안** → 각 reviewer의 **기존 게이트 매핑 그대로** (레지스트리 「scope 안 차단」 열. 현행을 베껴 적은 것 — 새 규칙 아님, 완화도 강화도 금지)
- **scope 밖** → 해당 reviewer **최상위 등급만 차단** (레지스트리 「scope 밖 차단」 열), 그 미만은 deferred 기록
- **차단 대상 1건 이상 → 해당 reviewer 최종판정 = REJECT / 0건 → APPROVE** (원판정이 REJECT여도)

#### 대상 축 — 「다 고치면 0 이 되나」 분류 (MANDATORY — 산출물·검증 장치 공통)

scope 축(안/밖)과 **직교**한다. scope 안이어도 아래에 해당하면 처분이 달라진다.

**대상 판정** — finding 이 가리키는 파일이:
- **산출물**(이번 작업이 만들려던 것 — 프로덕션 코드·스키마·마이그레이션·설정) **과**
- **검증 장치**(산출물을 지키려고 만든 것 — 게이트·린터·검사 스크립트·그 회귀)
  **둘 다 아래 표로 분류한다.** (2026-08-18 확장 — 원래 검증 장치 한정이었고 산출물은 「본 절 미적용」이었다. STAT-572 프로덕션 코드 Phase 4 에서 문면 ② 가 라운드마다 3~11건 새로 생겨 Stage 1 23라운드 + Stage 2 12라운드를 태웠고, 8/16 에 이 분류를 산출물에 적용하자 2라운드 만에 종료했다. 「고칠 때마다 새로 생긴다」는 성질은 그 글이 게이트를 설명하든 유스케이스를 설명하든 같다 — 스위치를 검증 장치에만 켜 둘 이유가 없다.)

| 분류 | 뜻 | 다 고치면 0 이 되나 | 처분 |
|---|---|---|---|
| **동작 결함** | **실제로 틀린 답을 낸다** — 검증 장치면 막아야 할 입력을 통과시키거나 정상 입력을 막고, 산출물이면 잘못된 값을 쓰거나·빠뜨리거나·틀린 경로로 간다 | **유한** — 구멍은 세어서 다 막을 수 있다 | **차단** |
| **증인 부재 ①** | 헤더·docblock 이 **계약으로 못박은 것**에 대조군이 하나도 없다(그 계약을 깨는 mutant 가 회귀 전건을 통과한다) | **유한** — 계약은 헤더에 적힌 것뿐 | **차단** |
| **문면 ①** | **행동을 지시하는 문면**(회수 절차·롤백 순서·런북)이 틀렸다 | **유한** — 절차 항목 수만큼 | **차단** |
| **증인 부재 ②** | 계약에 없는 축의 케이스가 얕다(*"이런 변형도 있는데 테스트가 없다"*) | 무한 | **이월** |
| **문면 ②** | **설명하는 문면**(서술·배경)이 코드와 어긋난다 | 무한 — **고칠 때마다 새로 생긴다** | **이월** |

⚠️ **판단 기준은 하나다 — 「이걸 다 고치면 0 이 되나」.** 0 이 되는 양만 종료 조건으로 쓸 수 있다. Phase 4 루프가 끝나지 않는 구조의 원인이 정확히 **0 에 도달하지 않는 양을 종료 조건으로 쓴 것**이다. 위 5분류는 그 물음의 **적용례이지 외워야 할 목록이 아니다** — 새로운 형태가 나오면 분류를 늘리지 말고 그 물음으로 판정한다.
  - **①/② 를 가르는 선**: 증인 부재는 **「그 장치가 스스로 약속했는가」**(헤더 계약 vs 그 밖), 문면은 **「그 글이 행동을 지시하는가」**(따라 하는 절차 vs 읽는 설명).
  - **①이 차단인 이유는 위험의 성질이 다르기 때문이다** — 동작 결함은 지금 뚫린 구멍이라 고치면 닫히지만, **증인 부재 ①은 미래에 구멍이 생겨도 아무도 모르는 상태**라 시간이 갈수록 나빠지고(그 장치의 SSOT 로 선언된 헤더 문장이 언제든 거짓이 될 수 있다), **문면 ①은 그대로 실행되어 손해가 난다.**
  - **2026-08-10 실사고 2건**: ⓐ 게이트 헤더가 *"스캔 자체는 `src/` 의 **모든 파일**을 대상으로 한다"* 를 계약으로 못박았는데 스캔을 `.ts` 로 좁힌 mutant 가 회귀 **74건을 전건 통과**했다(증인 부재 ①). ⓑ 게이트 **회수 절차** 목록이 `scripts/AGENTS.md` **3행**이라고만 적어, 그대로 따르면 **다른 게이트의 CI 배선 문서가 함께 사라진다**(문면 ①).

⚠️ **분류는 실측으로만 한다** — 「동작 결함이 아니다」를 근거로 이월하려면 **격리 사본에서 재현**해 그 장치가 정상 동작함을 보이고 실행한 명령과 결과를 audit 표에 인용한다. **재현이 없으면 그 finding 은 차단에 남는다.** 읽고 판단해 이월하는 것은 아래 anti-patterns 의 *"오케스트레이터가 reviewer 등급을 재판단"* 과 같은 self-approve 다. (「어느 분류인가」는 판단이 아니라 **측정**이다 — 그 장치에 그 입력을 넣어 exit code 를 보면 닫힌다. `40-common-loop.md` 「리뷰어 간 실측 충돌」과 같은 지위.) 이월분은 `.omc/deferred/` 기록 대상이다.
  - 비용을 **이월 쪽에만** 무겁게 두는 것이 이 규칙의 핵심이다. 차단은 증명 없이 유지되고 이월만 증명을 요구하므로 **귀찮아서 대충 이월하는 경로가 막힌다.**
  - **산출물의 재현** = 그 finding 이 가리키는 경로를 때리는 **최소 실행 1건**(해당 spec 1케이스 · 한 함수 호출 · 한 쿼리)으로 닫는다. **풀 스위트 재실행은 재현이 아니다** — 통과해도 그 경로를 지났다는 증명이 안 된다(2026-08-18: STAT-572 Phase 4 에서 풀 스위트 132회가 돌았고 그중 finding 경로를 증명한 것은 없다. 재현은 전부 별도의 1케이스 실행이었다).
  - **2026-08-10 실사고**: 등급이 `Medium` 이라 문면처럼 보이던 `SET SCHEMA` 미탐지가 재현 결과 **동작 결함**이었다(보호 테이블을 다른 스키마로 옮긴 뒤 동명 재생성 → rc=0). 읽고 분류했으면 영속 게이트에 우회를 남긴 채 통과했을 것이다. 같은 라운드 나머지 3건은 재현 결과 문면이었고 이월이 옳았다.

**왜 등급이 아니라 분류로 자르는가**: 리뷰어 등급은 **확신도**이지 위험 크기가 아니다(`ocr` 의 `Medium` 정의는 *"수작업 판단이 필요한 수정"*). 실제로 같은 `Medium` 안에 동작 결함과 문면이 섞여 나왔다 — 등급으로 자르면 둘이 함께 살거나 함께 죽고, 분류로 자르면 정확히 갈린다.

**왜 이월이 맞는 처분인가**: 동작 결함은 **유한**하다(세어서 다 막으면 0). 증인 부재·문면은 **고치는 행위가 새로 만들어 내므로 0 에 수렴하지 않는다**(`40-common-loop.md` 「검증되지 않은 단언」 말미). **0 에 도달하지 않는 양을 종료 조건으로 쓰면 루프가 끝나지 않는다.**

#### scope 판정 교차 확인 (MANDATORY — 적용 범위 엄격 제한)

어떤 reviewer 의 finding 이 **scope 밖 최상위 등급**으로 차단될 때, **같은 라운드 다른 reviewer 들이 그 영역에 대해 내린 scope 판정**을 audit 표에 함께 기재한다. 다수가 "scope 밖" 또는 "이월 존중"으로 **명시 판정**했으면 오케스트레이터가 사용자 에스컬레이션 없이 scope 밖 처분할 수 있다.

- **근거**: scope 소속은 **기준 문서 대조** 문제라 그 결함을 못 찾은 reviewer 도 판단할 수 있다. 같은 문서를 읽으면 같은 답이 나와야 하므로 소수 의견은 오독일 확률이 높다 — 다수결이 정보를 **정제**한다.
- ⚠️ **"침묵 = 동의" 금지.** 다른 reviewer 가 그 영역을 **명시적으로 언급**한 경우만 표에 센다. 언급이 없으면 "미판정"이며 다수 계산에서 제외한다(안 본 것과 동의한 것은 다르다).

**⛔ 이 경로로 판정해서는 안 되는 것 (위반 시 결과 무효)**

- **"이 결함이 실재하는가"** — 이것은 **깊이** 문제다. 그 일을 안 해 본 reviewer 의 표는 정보가 아니며, 다수결이 정보를 **파괴**한다. 실측으로 갈리는 분쟁은 `40-common-loop.md` 「리뷰어 간 실측 충돌」(오케스트레이터가 격리 사본에서 직접 재현)이 **우선**한다.
- **단일 reviewer 의 실측 기반 finding 을 다수결로 기각하는 것** — 한 명이 깊이 파서 찾은 것은 못 본 다수보다 맞을 확률이 높다. (2026-08-07 실측 반례: 백릴레이션 우회 Critical 은 리뷰어 6명 중 **1명만** 찾았고 오케스트레이터 재현 결과 **사실이었다** — 투표였으면 5:1 로 기각됐다. 운영 DB 에 없는 테이블을 조인하는 실제 배포 사고 경로였다.)
- **이미 이월 기록에 있는 항목** — 교차 확인조차 불필요하다. `.omc/deferred/` **기록 대조**로 끝난다(Deadlock 체크리스트 참조).

**reviewer별 임계선·deferred 기여·원판정=최종 여부는 `54-phase4-registry.md` 레지스트리 표가 SSOT다** — 여기 복제하지 말 것(두 곳에 두면 한쪽만 갱신돼 사각이 난다). deferred 대상 = 레지스트리 「deferred 기여」=Y 인 슬롯의 **scope 밖 "차단 등급 미만"** finding.

#### 가드 A — 등급 체계 미확인 reviewer (MANDATORY)

**대상 = 레지스트리의 「등급체계」가 `미확인`인 행 전부** (명단 하드코딩 금지 — 신규 reviewer가 규칙에서 누락되는 것을 막는다).

- 비-APPROVE 판정은 등급을 읽을 수 없으므로 **크리티컬로 간주하여 차단**한다 (fail-safe). **scope 밖이어도 차단.**
- **codex:review 원판정 판별**(가드 A 해제 후 — 2026-08-15): `P1` 0건 = APPROVE, `P1` 1건 이상 = 비-APPROVE. `P2` 는 차단하지 않고 **deferred 기록** 대상이다(레지스트리 #1 「deferred 기여」=Y). ⚠️ 차단하지 않는다는 것이 «고치지 않는다»는 뜻은 아니다 — 게이트는 **언제 멈출지**를 정할 뿐이고, 싸고 실체 있는 `P2` 는 등급과 무관하게 그 웨이브에서 닫는 편이 낫다.
- 안전판: 아래 **Plugin Reviewer Deadlock 조기 감지** — 무한 교착 방지.
- **해제 조건**: 실제 출력에서 등급 체계가 확인되면 가드를 해제하고 **레지스트리 해당 행**의 「등급체계」를 `확인`으로, 「scope 밖 차단」에 임계선을 적는다. ⚠️ **이때 「scope 안 차단」 칸도 반드시 함께 재검토한다** — 등급이 없던 시절의 `finding ≥ 1건`이 남으면 등급을 반쪽만 쓰게 되어 `scope 밖은 통과 / scope 안은 차단`이라는 역전이 생긴다(2026-08-08 architect 드리프트의 절차적 원인). 상세는 레지스트리 「가드 A 해제」 항.
- **실측 수집 (해제 가속, MANDATORY)**: 매 Phase 4 실행에서 가드 A 대상 reviewer의 **원출력을 확인**해 등급 표기 단서(severity 라벨, critical/high/medium 분류, 우선순위 필드 등)를 찾는다. 발견 시 원문을 audit 표와 함께 인용 기록하고, **서로 다른 실행에서 2회 이상 일관된 체계가 확인되면** 위 표 임계선 추가 + 가드 해제를 사용자에게 제안한다 (자율 해제 금지 — config 갱신은 사용자 승인 후).

#### 슬롯별 특례

**`54-phase4-registry.md` 「슬롯별 특례」 절이 SSOT다** — code-simplifier 심사 범위·판정 이진 유지, pr-review-toolkit 게이트 매핑·내부 code-simplifier 분리·부분 재실행 단위, ocr allowlist, codex 계열 호출 제약이 거기 모여 있다. 여기 복제하지 말 것.

#### deferred 기록 파일 규격 (MANDATORY)

- 경로: `.omc/deferred/<YYYY-MM-DD>-<작업명-slug>.md`
- **한 작업 = 파일 1개.** 경로는 최초 라운드에 확정 후 같은 작업 내내 재사용 (재생성 금지). team ralph 외곽 사이클 재진입 시에도 동일 파일 재사용.
- **union 누적**: 동일 파일 + 동일 요지면 재기재하지 않는다 (라인 번호는 최신으로 갱신만).
- **파일은 Phase 4 최초 라운드에 무조건 생성한다** (2026-08-21 개정 — 종전 "기록 대상 0건이면 파일 미생성" 폐지: 아래 환경 스냅샷·라운드 기록이 finding 유무와 무관하게 필요하다. finding 표만 0행일 수 있다).
- **환경 스냅샷 블록 (MANDATORY — 파일 최상단, 2026-08-21 신설)**: Phase 4 최초 라운드에 1회, 호출 경로 해석 결과를 기록한다 — codex-companion.mjs 절대 경로 · critic.md 절대 경로(활성 플러그인 버전 디렉토리) · 플러그인 버전. **compaction·세션 재개 후에는 이 블록을 우선 참조**해 경로 재탐색(find 스윕)을 생략한다. 단 섹션 파일 재Read 의무(각 Stage 진입 체크리스트)는 그대로다 — 스냅샷은 **경로만** 공급하며 호출 형태의 SSOT가 아니다(`00-overrides.md` "호출 형태의 SSOT는 섹션 파일"). (2026-08-21 STAT-589 실측: compaction 직후 codex-companion 경로 find 재탐색 Bash 3연발 ~3분 + 오경로 호출 위험.)
- **라운드 기록 (MANDATORY — 2026-08-21 신설)**: 매 웨이브(본 웨이브·부분 재실행 웨이브) 종료 시 1줄 append — `- R<N>[.P<k>] <HH:MM>→<HH:MM> 호출: [슬롯…] 판정: [요지 1줄] [H:<12hex>]`. `H` = 그 웨이브 호출 직전 판정 재료 해시 앞 12자리(위 「diff 불변 슬롯 재사용」의 입력). 시각 기록은 다음 튜닝의 재측정이 트랜스크립트 파싱 없이 파일 Read로 끝나게 한다 (2026-08-21 실측: 이번 시간 분석에 18MB 트랜스크립트 고고학이 필요했다).
- Phase 5 cleanup 대상 아님 (`.omc/state/*.json`만 삭제) → 보존됨. (주의: linked worktree에서는 worktree 삭제 시 `.omc/` 공통 규칙에 따라 함께 소실 — 보존 필요 시 `OMC_STATE_DIR` 중앙화)
- 형식:

```markdown
## 2026-07-28 로그인 API rate limit 추가
scope 기준 문서: .omc/plans/autopilot-impl.md

### 환경 스냅샷 (최초 라운드 1회)
- codex-companion: /Users/june/.claude/plugins/cache/openai-codex/codex/<ver>/scripts/codex-companion.mjs
- critic.md: /Users/june/.claude/plugins/cache/omc/oh-my-claudecode/<ver>/agents/critic.md (plugin <ver>)

### 라운드 기록
- R1 17:24→19:10 호출: [S0 3 + S1 4 + S2 9] 판정: S2 #13 REJECT → 부분 루프 [H:a1b2c3d4e5f6]
- R1.P1 19:20→19:35 호출: [#13] 판정: APPROVE — 클린, R2 재시작 [H:0f9e8d7c6b5a]

| 등급 | 지적 | 위치 | 출처 |
|---|---|---|---|
| medium | 기존 세션 검증 로직이 장황함 | auth.ts:88 | codex:adversarial |
| 불명(가드A) | 레거시 인증 로직 취약 | legacy/auth.ts:12 | 사용자 dismiss — 가드 A |
```

- 채팅 보고서에도 "후속 과제" 섹션으로 동일 내용을 출력한다.

#### 수정 방식 (MANDATORY)

REJECT를 받아 코드를 수정할 때:
- **원본 코드 최대한 보존.** 차단 사유를 해소하는 **최소 변경**을 우선한다.
- 동등한 효과라면 **가장 간단하고 단순한 방법**을 택한다.
- **풀 게이트는 웨이브당 1회** — vitest 전체·lint:check·knip·drift 류는 수정 웨이브 **커밋 직전 1회**만 돌린다. 주석/문서 전용 웨이브는 typecheck + prettier(변경 파일)만. 리뷰어가 같은 트리에서 병렬로 도는 동안 풀 스위트 실행 금지(`40-common-loop.md` 「뮤테이션 권한은 한 레인에만」과 같은 이유 — 판정이 흔들린다. 실사고: 같은 스위트가 연속 4회 36/0/1/5 failed). finding 재현은 풀 스위트가 아니라 **1케이스 실행**이다(「대상 축」 절). (2026-08-18: STAT-572 Phase 4 풀 스위트 132회 · typecheck 245회, 그중 finding 경로를 증명한 실행 0.)
- 차단 사유와 무관한 리팩터링/개선을 함께 넣지 않는다. (같은 턴에 섞이면 다음 라운드의 scope 판정이 오염된다)

#### Phase 4 scope 규칙 — 잘못된 진행 금지 (anti-patterns, MANDATORY)

- ❌ scope 기준 문서를 열지 않고 scope 안/밖 판정 → 우선순위 1~5 중 실재 문서 대조 필수
- ❌ "변경한 파일 안이니까 scope 안" 판정 → 기준 문서에 없으면 scope 밖
- ❌ deferred 파일 기록 없이 게이트 통과 → 이번 라운드 기록 대상의 **부분집합 검증** 실패 시 통과 금지
- ❌ reviewer 원판정을 지우고 최종판정만 표기 → 원판정 컬럼 필수 (감사 추적)
- ❌ 오케스트레이터가 reviewer 등급을 재판단 ("high지만 사실 별거 아님") → self-approve
- ❌ scope **안** finding에 표 오른쪽 열(최상위 등급) 적용 → 왼쪽 열(기존 매핑)만. scope 안 완화 금지
- ❌ 등급 미확인 reviewer의 finding을 임의로 낮은 등급 추정 → 가드 A로 차단
- ❌ REJECT 수정 시 차단 사유와 무관한 개선 동반 → 다음 라운드 scope 판정 오염
- ❌ 사용자 dismiss 이력이 있는 동일 finding으로 재차 Deadlock 질문 → dismiss 유지 규칙 위반

---

### Stage 0 — 정합 선행 게이트 (3개: intent-scope A-Claude·A-Codex + change-impact B)

**호출 형태·입력 조립·override·게이트 매핑·A 합의 판정·`INPUT_MISSING` 처리는 `55-stage0-gate.md` 가 SSOT** — 여기 복제하지 말 것. 이 절은 Stage 흐름 안에서의 **체크리스트·audit·판정 절차**만 정한다.

**MANDATORY — Stage 0 라운드 진입 시 자체 검증 체크리스트 출력**: Stage 0 (재)시작 직전(호출 전 체크리스트보다 먼저) 다음을 user-facing 텍스트에 출력할 것. 누락 시 프로토콜 위반.
- [ ] 누적 시도 카운트 #N (1 ≤ N ≤ maxValidationRounds=15) — **이번 Stage 0 (재)시작으로 직전 대비 +1** (`INPUT_MISSING` 재호출은 예외 — 미증가)
- [ ] 라운드 표기 출력됨: `Round N/15`
- [ ] 이번 stage = Stage 0 (3개: A-Claude · A-Codex · B)
- [ ] 진입 사유: [Phase 4 최초 진입 / Stage 0 REJECT 후 수정 → 재실행 / Stage 1 REJECT 후 수정 → Stage 0 복귀 / Stage 2 부분 재실행 클린 → Stage 0부터 재시작]
- [ ] 직전 라운드 결과 1줄 요약 (최초 진입이면 "신규")
- [ ] N=15 도달 직전인가? (Y → 다음 라운드가 마지막. REJECT 시 자동 통과 금지, 사용자 보고 후 정지)
- [ ] **이번 세션에서 `55-stage0-gate.md` 를 실제 Read 했는가?** compaction·세션 재개 후에는 컨텍스트 잔존과 무관하게 재Read — `subagent_type`·마커·`--write` 유무는 트랜스크립트 복원 시 기본값으로 채워진다. (호출 **경로** 해석은 deferred 파일 「환경 스냅샷」 블록 우선 — find 재탐색 생략)
- [ ] **입력 조립 완료** (`55-stage0-gate.md` 「호출 패턴 0」): scope 기준 문서 경로 `__________` **전문** 확보(요약 아님) / diff 범위 `______` / 사용자 제약 `__건 | 없음` / 이월 기록 `__건 | 없음` / **자매 축 선언** `__________ | 없음(근거: ____)` / 옛 값 목록 `__건 | 없음`
- [ ] 선제 환경 컨텍스트 블록 수집 완료(`50-critic.md` — Stage 0 3슬롯 전부 주입 가능이므로 대상)

**구성** (`55-stage0-gate.md` 「구성」):
- **A-Claude** `Task(subagent_type="intent-scope-reviewer")` — 사용자 소유 에이전트, Write/Edit 도구 제외
- **A-Codex** Bash `codex-companion.mjs task --fresh "<intent-scope-reviewer.md 본문 전문 + 마커 + 입력 + override>"` — **`--write` 금지**(read-only 샌드박스), `run_in_background=true`
- **B** `Task(subagent_type="change-impact-reviewer")` — 사용자 소유 에이전트, Write/Edit 도구 제외, `lsp_find_references` 보유
- A 는 **두 엔진 모두 호출이 필수**(한 엔진만 호출 = 결과 무효). B 는 Claude 단독.

**MANDATORY — Stage 0 호출 전 체크리스트 출력**: Stage 0 호출 메시지 작성 직전에 다음 3개를 줄바꿈된 체크박스 리스트로 user-facing 텍스트에 먼저 출력할 것. 출력 후 같은 턴에서 3개 호출을 모두 포함시킬 것. 체크리스트 누락 시 프로토콜 위반.
- [ ] A-Claude — **실제 사용한 `subagent_type` 값을 여기 적을 것: __________** (allowlist: **`intent-scope-reviewer`** 단 하나. prompt 선두에 `[stage0:intent-scope]` 마커 + 기준 문서 전문 + diff + 제약 + 이월 + override 3줄)
- [ ] A-Codex — Bash `node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" task --fresh "<…>"` (run_in_background=true) — **`--write` 없음 확인: [Y]** / 본문 전문(frontmatter 제거) 주입 확인: [Y] / 마커 포함: [Y]
- [ ] B — **실제 사용한 `subagent_type` 값을 여기 적을 것: __________** (allowlist: **`change-impact-reviewer`** 단 하나. prompt 선두에 `[stage0:change-impact]` 마커 + diff + **자매 축 선언** + 옛 값 + 이월 + override 3줄)

**MANDATORY — Stage 0 호출 메시지 자체 검증**: 메시지 전송 직전, 위 3개 항목이 **단일 메시지 내 tool_use 블록에 빠짐없이** 포함됐는지 확인. 3개 미만이면 전송 금지. Stage 1 호출과 같은 메시지 금지. override 3줄(리뷰 전용·판정 규칙·입력 고정) 포함 여부 별도 확인. **PreToolUse 훅(`omc-guard.py`)이 allowlist·마커·`--write` 를 차단하고, Stop 훅(`omc-stage1-audit.py`)이 3슬롯 완결성을 사후 감사한다.**

**MANDATORY — Stage 0 회수 검증**: Task 2건은 Task 결과, A-Codex 는 BashOutput 폴링으로 회수 완료까지 대기. 회수 못 한 슬롯은 **APPROVE 카운트 금지**, 재호출. `판정:` 라인·카운트 없는 응답 = 회수 실패. **`판정: INPUT_MISSING` = 오케스트레이터 입력 누락 신호** — APPROVE/REJECT 어느 쪽으로도 세지 않고 입력 보강 후 같은 라운드 재호출(카운터 미증가, 3회째면 사용자 보고).

**MANDATORY — Stage 0 종합 전 감사 (post-call audit)**: 3슬롯 결과 종합 직전, 슬롯별로 아래 표 출력.

| slot | 호출 | 회수 | 원판정 | finding(등급별) | 신규/이월 재지적 | 차단사유 | 최종 |
|---|---|---|---|---|---|---|---|

- A 두 행 아래 **`A 합의: [통과|REJECT]`** 한 줄 — 불일치 시 사실형/판단형 구분과 오케스트레이터 직접 대조 근거(파일:라인·문서 절)를 **인용 기재**(`55-stage0-gate.md` 「게이트 매핑」).
- `requires_human_verification` 항목 목록을 별도 행으로 기재 — **Stage 2 verifier 호출 프롬프트 인계 대상**(누락 금지).
- 차단사유 컬럼: 등급 + 위치만. B 의 MINOR 는 deferred 파일에.
- "안 됨"/"회수 실패" 1건이라도 있으면 종합 금지, 누락분 재호출. 워킹트리 변경 자기신고 1건이라도 있으면 해당 결과 무효 + 제약 강화 후 재호출(오케스트레이터의 "실질 영향 없음" 유효 처리 금지).

**MANDATORY — Stage 0 게이트 판정 자체 검증 체크리스트 출력**: 게이트 판정 직전(audit 표 출력 후) 다음을 user-facing 텍스트에 출력할 것. 누락 시 판정 무효.
- [ ] scope 기준 문서: __________ (Stage 1·2 에 **같은 문서**를 쓸 것 — 경로 명기)
- [ ] A-Claude — 원판정: [...] / 총괄: [Fully|Partially|Not] / CRITICAL__ (MISSING__ VIOLATION__) MAJOR__ (DRIFT__ EXTRA__) / 이월 존중__ / 최종: [통과|차단]
- [ ] A-Codex — 원판정: [...] / 총괄: [...] / CRITICAL__ MAJOR__ / 이월 존중__ / `--write` 없음 확인: [Y] / 최종: [통과|차단]
- [ ] **A 합의: [통과|REJECT]** — 불일치 시: [사실형 → 직접 대조 결과 ______ / 판단형 → REJECT 유지 + 사용자]
- [ ] B — 원판정: [...] / CRITICAL__ (BROKEN CALLER__ COMPAT__) MAJOR__ (ASYMMETRY__ 잔존__ 빈칸__) MINOR__(→deferred) / 자매 축: [선언 내용 | 없음] / 최종: [통과|차단]
- [ ] 세 슬롯 모두 review-only 준수(워킹트리 변경 자기신고 0건)인가? (1건이라도 있으면 결과 무효 + 재호출)
- [ ] `requires_human_verification` 항목 __건 → Stage 2 verifier 인계 목록에 기록했는가?
- [ ] B 의 MINOR 각각이 deferred 파일에 존재하는가? — 부분집합 검증
- [ ] 발산 조기 감지 체크(`50-critic.md` 「Finding 발산 조기 감지」 — 라운드 축) 실행했는가?
- [ ] **A 통과 AND B 통과**인가? (Y → Stage 1 진입 / N → 수정 → REJECT 슬롯만 재실행 → 전원 APPROVE 시 3슬롯 확인 실행 1회 → Stage 1)
- [ ] 다음 행동 명시: [Stage 1 진입 / Stage 0 REJECT 슬롯 재실행 (수정 → 호출) / INPUT_MISSING 보강 재호출 / maxValidationRounds 도달로 사용자 보고 후 정지]

**Stage 0 게이트 판정**:
- **A 통과(두 엔진 동시점 APPROVE) AND B APPROVE → Stage 1 진입.**
- 그 외 → 코드 수정 → **REJECT한 슬롯만 재실행** → REJECT였던 슬롯 전원 APPROVE → **3슬롯 확인 실행 1회** → 전원 APPROVE 시 Stage 1. 수정만 하고 재검증 생략 금지. 각 Stage 0 (재)시작마다 +1, maxValidationRounds=15 한도 내.
- **주석/문서 전용 수정**(코드 로직 0줄)으로 해소되면 아래 「주석/문서 전용 수정의 단축」(Stage 0·1·2 공통)을 따른다 — REJECT 슬롯만 단독 재검증, 확인 실행 생략.
- **테스트 전용 수정**(프로덕션 src 0줄·테스트 파일만)으로 해소되면 아래 「테스트 전용 수정의 단축」을 따른다 — REJECT 슬롯만 재실행, 3슬롯 확인 실행 생략.

---

### Stage 1 — Codex 팀 3개 + OCR 1개 (4개 — Stage 0 전원 APPROVE 시에만)

**MANDATORY — Stage 1 라운드 진입 시 자체 검증 체크리스트 출력**: Stage 1 라운드 시작 직전(호출 전 체크리스트보다 먼저) 다음을 user-facing 텍스트에 출력할 것. 누락 시 프로토콜 위반.
- [ ] Stage 0 직전에 3슬롯(A-Claude·A-Codex·B) **전원 APPROVE**(A 합의 통과) 확정됐는가? (Y → 진입 / N → 진입 금지, Stage 0로 복귀. PreToolUse 훅은 이 세션에 Stage 0 호출 기록이 없으면 ocr 래퍼를 차단한다. **예외**: 「테스트 전용 수정의 단축」 경로의 부분 재실행은 직전 Stage 0 APPROVE 가 유지되므로 Y 로 처리 — 수정이 프로덕션 0줄이라 정합 판정 전제가 무효화되지 않는다)
- [ ] 현재 시도 카운트 #N (1 ≤ N ≤ maxValidationRounds=15) — **이번 시도의 Stage 0 시작 때 +1된 값** (Stage 1 진입으로는 안 올림)
- [ ] 이번 stage = Stage 1 (4개: codex 3 + ocr 1)
- [ ] 진입 사유: [Stage 0 통과 직후 최초 진입 / Stage 1 REJECT 후 수정 → Stage 0 재통과 → REJECT 슬롯 재실행 / **테스트 전용 단축: Stage 0 생략 → REJECT 슬롯만 재실행** / Stage 2 부분 재실행 클린 → Stage 0·1 재시작]
- [ ] N이 이번 시도의 Stage 0 시작 시 값과 같은가? (Stage 1 진입으로 증가·리셋 없음 — 어떤 경우에도 0 초기화 금지)
- [ ] 직전 라운드 결과 1줄 요약 (최초 진입이면 "신규")
- [ ] N=15 도달 직전인가? (Y → 다음 라운드가 마지막. REJECT 시 자동 통과 금지, 사용자 보고 후 정지)
- [ ] **이번 세션에서 `51-codex-reviews.md` · `53-ocr-review.md` · `50-critic.md` · `55-stage0-gate.md` 를 실제 Read 했는가?**
      compaction·세션 재개 후에는 **컨텍스트 잔존과 무관하게 재Read**한다. "기억하고 있다"·"직전 라운드에
      호출해봤다"는 근거가 아니다 — 호출 파라미터(`subagent_type`·대상 flag)는 트랜스크립트에 온전히 남지
      않아 복원 시 기본값으로 채워진다(2026-08-07 실제 위반 2건: ocr 래퍼 오답 · codex:review companion 오용).
      호출 **경로**(codex-companion.mjs·critic.md 절대 경로) 해석은 deferred 파일 「환경 스냅샷」 블록을 우선
      참조해 find 재탐색을 생략한다 (2026-08-21 STAT-589 실측: compaction 직후 경로 재탐색 3연발 ~3분).

**구성**:
- codex:review (Bash 직접 호출, plugin native)
- codex:adversarial-review (Bash 직접 호출, plugin native)
- codex:critic (Bash 직접 호출, OMC custom — critic.md 전문 주입)
- ocr:delegate-review (Task subagent 래퍼, OMC custom — delegate-review.md 전문 주입, `53-ocr-review.md` 참조)

**호출 방식**: **codex 3건은 모두 Bash 직접 호출만 허용**. codex:review / codex:adversarial-review는 `51-codex-reviews.md`의 "호출 매트릭스" 및 "scope 선택 규칙" 참조. codex:critic은 `50-critic.md`의 "codex:critic 호출 패턴" 참조. `Task(subagent_type="codex:*")` 또는 `Skill(skill="codex:review"|"codex:adversarial-review")` 호출 **금지** (codex-plugin-cc는 review/adversarial-review를 subagent로 노출하지 않으며, 두 slash command는 `disable-model-invocation: true`라 모델 invocation 불가). **ocr:delegate-review는 Task 래퍼 호출만 허용** — `Task(subagent_type="oh-my-claudecode:code-reviewer", prompt=delegate-review.md 전문 + override 3줄 + scope 인자)`. 메인 세션 `Skill(skill="open-code-review:delegate-review")` 호출 **금지** (`53-ocr-review.md` anti-patterns 참조).

**단일 메시지 mandate (Stage 1)**: 위 4개를 **반드시 한 메시지의 tool_use 블록에 모두 포함**시켜 한 턴에 병렬 실행 (Bash 3 + Task 1 혼합 가능). 분산 호출 또는 누락 호출 시 Stage 1 결과 무효.

- **Stop 훅이 이 mandate 를 사후 감사한다** (`~/.claude/hooks/omc-stage1-audit.py`): 턴이 끝나면 그 턴의 tool_use 를 훑어 4슬롯 누락과 체크리스트 부재를 `systemMessage` 로 알린다(차단하지 않음). ⚠️ **이 검사는 PreToolUse 에 둘 수 없다** — PreToolUse 는 현재 어시스턴트 메시지가 트랜스크립트에 기록되기 **전에** 실행되므로 같은 메시지 안의 체크리스트도, 같은 메시지 안의 다른 tool_use 도 보이지 않는다(2026-08-07 실측: 규정을 정확히 지킨 호출 7건에 전부 오탐이 붙었다). 반대로 **호출 파라미터 검사**(ocr 래퍼 allowlist 등)는 `tool_input` 을 직접 보므로 PreToolUse 차단이 정확하다 — `omc-guard.py` 소관.

**MANDATORY — Stage 1 호출 전 체크리스트 출력**: Stage 1 호출 메시지 작성 직전에 다음 4개를 줄바꿈된 체크박스 리스트로 user-facing 텍스트에 먼저 출력할 것. 출력 후 같은 턴에서 4개 호출을 모두 포함시킬 것. 체크리스트 누락 시 프로토콜 위반.
- [ ] Bash: `codex review <대상 flag>` (run_in_background=true) ← codex:review (direct CLI, companion 우회. `<대상 flag>`는 `51-codex-reviews.md`의 "scope 선택 규칙"에 따라 `--uncommitted` / `--base <ref>` / `--commit <SHA>` 중 선택)
- [ ] Bash: `node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" adversarial-review "<args>"` (run_in_background=true) ← codex:adversarial-review (`<args>` 동일 규칙)
- [ ] Bash: `node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" task --fresh --write "<critic.md 전문 + 리뷰 대상>"` (run_in_background=true) ← codex:critic — **리뷰 대상에 Stage 0 A 가 받은 것과 동일한 scope 기준 문서 전문 + 그 앞 한 줄 `[stage1:scope-doc] <경로>` 태그 포함 확인: [Y]** (`55-stage0-gate.md` 「Stage 1 교차 확인」 — A 의 판정·행렬은 주입하지 않는다. Stop 훅이 태그 부재를 경고)
- [ ] ocr:delegate-review — **실제 사용한 `subagent_type` 값을 여기 적을 것: __________**
      (allowlist: **`ocr-delegate-reviewer`** 단 하나. 다른 값이면 호출 금지 — PreToolUse 훅이 차단한다.
       prompt = delegate-review.md 전문 + override 3줄 + scope 인자. `53-ocr-review.md` 호출 패턴 준수)

**MANDATORY — Stage 1 호출 메시지 자체 검증**: 메시지 전송 직전, 위 4개 항목이 **단일 메시지 내 tool_use 블록에 빠짐없이** 포함됐는지 확인. 4개 미만이면 메시지 전송 금지하고 누락분 추가 후 재작성. "이번엔 일부만 호출했고 나머지는 다음 메시지에"는 **금지**. ocr:delegate-review 호출 시 override 3줄(review-only / 판정 규칙 / scope 고정) 포함 여부 별도 확인. **경로 프리플라이트 (MANDATORY — 2026-08-21 신설)**: 호출 프롬프트에 넣은 파일 경로 전건을 `ls` 실측으로 확인(실패 0건)한 뒤 전송한다 — 오경로 1건이 그 웨이브 전체의 재확인 왕복을 만든다 (실측 근거는 Stage 2 자체 검증 절).

**MANDATORY — Stage 1 회수 검증**: `run_in_background=true`로 띄운 codex Bash 호출 3건은 BashOutput으로 stdout 회수 완료까지 대기, ocr Task 1건은 Task 결과 회수 완료까지 대기. 회수 못 한 reviewer는 **APPROVE로 카운트 금지**, maxValidationRounds 한도 내 재호출. "타임아웃이라 N/A" 처리 금지.

**MANDATORY — Stage 1 종합 전 감사 (post-call audit)**: 4명 reviewer 결과 종합 직전, 각 reviewer 항목별로 아래 표 출력.

| reviewer | 호출 | 회수 | 원판정 | finding(등급별) | scope밖→기록 | 차단사유 | 최종 |
|---|---|---|---|---|---|---|---|

- 차단사유 컬럼: 차단 대상 finding의 **등급 + 위치만** 기재. 기록 항목 상세는 deferred 파일에 (표에 중복 기재 금지).
- **`신규 __건 / 이월 재지적 __건` 컬럼 필수 (MANDATORY)** — 각 reviewer 의 finding 을 `.omc/deferred/` 와 동일 파일·동일 요지로 대조해 가른다. **질적으로 다른 두 상태가 같은 "REJECT" 로 뭉개지는 것을 막는다** — "신규 결함 0건인데 이월 재지적 1건으로 차단" 과 "신규 Critical 1건으로 차단" 은 사용자 판단이 완전히 달라진다. 이 수치는 **발산·정체 판정의 입력값**이며(발산 = 신규가 계속 나옴 / 정체 = 재지적이 반복됨), 발산·Deadlock 사용자 보고에도 그대로 싣는다.
- "안 됨" 또는 "회수 실패"가 1건이라도 있으면 종합 금지하고 누락분 재호출. **N/A 처리는 reviewer가 명시적 거부 응답을 반환한 경우만 허용** — 호출 시도조차 안 한 채 N/A 결정 절대 금지.

**MANDATORY — Stage 1 게이트 판정 자체 검증 체크리스트 출력**: 게이트 판정 직전(audit 표 출력 후) 다음을 user-facing 텍스트에 출력할 것. 누락 시 판정 무효.
- [ ] scope 기준 문서: __________ (우선순위 1~5 중 실제 사용한 것, 경로 명기)
- [ ] codex:review — 원판정(finding 0건=APPROVE 규칙): [...] / 가드A: [Y/N] / 최종: [차단|통과]
- [ ] codex:adversarial-review — 원판정: [...] / crit__ high__ med__ low__ / scope밖 기록 __건 / 차단사유: ______ / 최종: [차단|통과]
- [ ] codex:critic — 원판정: [...] / CRITICAL__ MAJOR__ 그외__ / scope밖 기록 __건 / 차단사유: ______ / 최종: [차단|통과]
- [ ] ocr:delegate-review — 원판정: [...] / High__ Medium__ / scope밖 기록 __건 / 차단사유: ______ / 최종: [차단|통과] (Low는 폐기 — 기록 불요)
- [ ] ocr:delegate-review review-only 준수 확인 (서브에이전트 파일 수정 정황 0건인가? 1건이라도 있으면 결과 무효 + 재호출)
      ⚠️ **오케스트레이터가 `git status` clean 재확인 등으로 "실질 영향 없음" 판정해 결과를 유효 처리하는 것 금지** —
      **자기신고 자체가 무효 사유**다. 사후 검증으로 규정된 처분(무효 + 재호출)을 대체할 수 없다(2026-08-07 실제 위반).
- [ ] 이번 라운드 기록 대상 각각이 deferred 파일에 존재하는가? — **부분집합 검증**. 누락 시 통과 금지. (파일 총 행 수는 라운드 건수와 무관 — 누적 union)
- [ ] scope 밖 판정이 전건 기준 문서 대조인가? (추측 판정 0건)
- [ ] N/A는 명시적 거부 응답에 한함 — 호출 누락/회수 실패에 의한 N/A는 0건인가? (1건이라도 있으면 판정 금지, 누락분 재호출)
- [ ] Deadlock 조기 감지 체크 실행했는가? (Stage 1 게이트 판정 직전 필수)
- [ ] 4명 전원 **최종** 통과인가? (Y → Stage 2 진입 / N → 수정 → Stage 0 재실행 → REJECT 슬롯만 재실행, Stage 2 진입 금지)
- [ ] 다음 행동 명시: [Stage 2 진입 / 수정 → Stage 0 재실행 → Stage 1 REJECT 슬롯 재실행 / maxValidationRounds 도달로 사용자 보고 후 정지]

**Stage 1 게이트 판정**:
- 4명 **전원 APPROVE** → Stage 2 진입.
- 1명이라도 REJECT/REQUEST CHANGES → 코드 수정 → **Stage 0 재실행**(카운터 +1, 통과 시) → **Stage 1 의 REJECT한 슬롯만 재실행** → REJECT였던 슬롯 전원 APPROVE → **4슬롯 확인 실행 1회** → 전원 APPROVE 시 Stage 2 (Stage 2 진입 금지는 그때까지 유지 — 위 「REJECT 처리」와 동일). 수정만 하고 재검증 생략 금지. maxValidationRounds=15 한도 내.

---

### Stage 2 — 나머지 9개 (Stage 1 전원 APPROVE 시에만)

**MANDATORY — Stage 2 진입 시 자체 검증 체크리스트 출력**: Stage 2 라운드 시작 직전(호출 전 체크리스트보다 먼저) 다음을 user-facing 텍스트에 출력할 것. 누락 시 프로토콜 위반.
- [ ] Stage 1 직전 라운드에서 4명(codex 3 + ocr 1) 전원 APPROVE 확정됐는가? (Y → 진입 / N → 진입 금지, Stage 1로 복귀)
- [ ] 현재 시도 카운트 #N (1 ≤ N ≤ maxValidationRounds=15) — 이번 시도의 Stage 0 시작 때 +1된 값 (Stage 1·2 진입으로는 안 올림)
- [ ] 이번 stage = Stage 2 (9개: 7 OMC subagent + 2 Skill 빌트인/공식)
- [ ] Stage 1 호출이 Stage 2 메시지에 섞이지 않았는가? (섞였으면 메시지 무효 — Stage 분리 mandate 위반)
- [ ] N=15 도달 직전인가? (Y → 다음 라운드가 마지막. REJECT 시 자동 통과 금지, 사용자 보고 후 정지)

**구성**:
- **7개 OMC subagent** (Task 호출): architect, security-reviewer, code-reviewer, test-engineer, critic, verifier, code-simplifier. **단일 메시지에서 `Task(subagent_type="oh-my-claudecode:<name>")` 병렬 스폰**.
- **MANDATORY — code-simplifier 호출 시 review-only 모드 강제**: code-simplifier는 Edit/Write 도구를 사용할 수 있는 코드 수정 에이전트다(다른 subagent와 달리 본 규칙 별도 적용). 프롬프트에 포함할 제약 문구와 판정 규칙은 **`54-phase4-registry.md` 「슬롯별 특례」 #11**이 SSOT. 미포함 호출 시 결과 무효 처리, 재호출 mandatory.
- **2개 Claude Code 빌트인/공식 슬래시 커맨드** (`/security-review`, `/pr-review-toolkit:review-pr`): 메인 세션에서 **`Skill` tool로 호출**할 것 (`Skill(skill="security-review")`, `Skill(skill="pr-review-toolkit:review-pr")`). PR 부재 시에도 git diff 기반으로 동작하므로 "PR 없으니 N/A" 처리 금지. `/security-review`는 Claude Code 본체 빌트인 (보안 특화). `/pr-review-toolkit:review-pr`은 Anthropic 공식 `pr-review-toolkit` 플러그인의 오케스트레이션 슬래시로, 내부적으로 6개 전문 서브에이전트(code-reviewer, code-simplifier, comment-analyzer, pr-test-analyzer, silent-failure-hunter, type-design-analyzer)를 git diff 기반으로 자동 호출.
- **MANDATORY — `/pr-review-toolkit:review-pr` 게이트 매핑·내부 code-simplifier 분리**: **`54-phase4-registry.md` 「슬롯별 특례」 #13**이 SSOT (APPROVE 조건, 원판정=최종판정, 내부 code-simplifier 무효 처리·재호출 args, 부분 재실행 단위). 여기 복제하지 말 것.
  - **Suggestions 처리(절차)**: 게이트 차단하지 않음. Stage 2 audit 표에 Suggestions 카운트 + 항목 목록을 별도 컬럼으로 기록하고, 사용자 보고서에 minor 이슈 섹션으로 포함해 후속 작업 트래킹 대상으로 남긴다.

**단일 메시지 mandate (Stage 2)**: 위 7+2=9개를 **반드시 한 메시지의 tool_use 블록에 모두 포함**시켜 한 턴에 병렬 실행. 분산 호출 또는 누락 호출 시 Stage 2 결과 무효. Stage 1과 동일 메시지에 합치기 금지.

**MANDATORY — Stage 2 호출 전 체크리스트 출력**: Stage 2 호출 메시지 작성 직전에 다음 9개를 줄바꿈된 체크박스 리스트로 user-facing 텍스트에 먼저 출력할 것. 출력 후 같은 턴에서 9개 호출을 모두 포함시킬 것. 체크리스트 누락 시 프로토콜 위반.
- [ ] Task(subagent_type="oh-my-claudecode:architect") — **finding에 `CRITICAL/MAJOR/MINOR` 등급 부여 요구 프롬프트 포함 필수**
- [ ] Task(subagent_type="oh-my-claudecode:security-reviewer")
- [ ] Task(subagent_type="oh-my-claudecode:code-reviewer")
- [ ] Task(subagent_type="oh-my-claudecode:test-engineer")
- [ ] Task(subagent_type="oh-my-claudecode:critic")
- [ ] Task(subagent_type="oh-my-claudecode:verifier") — **프롬프트에 `## requires_human_verification` 헤더(문자열 그대로) + Stage 0 인계 항목 목록 포함 필수**(0건이면 헤더 + "없음" — `55-stage0-gate.md` 「게이트 매핑」. Stop 훅이 문자열 부재를 경고)
- [ ] Task(subagent_type="oh-my-claudecode:code-simplifier") — **review-only 제약 + "심사 범위: 이번 변경 라인 한정, 손대지 않은 기존 코드 지적 금지" 제약 포함 필수**
- [ ] Skill(skill="security-review")
- [ ] Skill(skill="pr-review-toolkit:review-pr") — **원판정 매핑: Critical=0 AND Important=0 → APPROVE / 그 외 → REJECT** (최종판정은 scope 분류 경유 — 단 Critical·Important는 **scope 밖이어도 차단**), Suggestions은 minor 이슈로 별도 기록

**MANDATORY — Stage 2 호출 메시지 자체 검증**: 메시지 전송 직전, 위 9개 항목이 **단일 메시지 내 tool_use 블록에 빠짐없이** 포함됐는지 확인. 9개 미만이면 메시지 전송 금지하고 누락분 추가 후 재작성. "이번엔 7개만 호출했고 나머지는 다음 메시지에"는 **금지**. code-simplifier subagent 호출 시 review-only 제약 프롬프트 포함됐는지 별도 확인. Skill(pr-review-toolkit:review-pr) 호출 시 **원판정** 매핑 규칙(Critical=0 AND Important=0 → APPROVE)을 메시지 본문에 명시 포함했는지 별도 확인 (최종판정은 scope 분류 경유). **경로 프리플라이트 (MANDATORY — 2026-08-21 신설)**: 호출 프롬프트에 넣은 파일 경로 전건을 `ls` 실측으로 확인(실패 0건)한 뒤 전송한다 — 오경로 1건이 그 슬롯의 판정 전제를 오염시켜 웨이브 전체의 재확인 왕복을 만든다 (2026-08-21 STAT-589 실측: #13 웨이브에 오경로 1건 → 3개 서브에이전트 재확인 왕복 8건·10분+ 소모, 정정 확인 메시지가 라운드를 늘렸다).

**MANDATORY — Stage 2 회수 검증**: 모든 reviewer 결과 회수 완료까지 대기. 회수 못 한 reviewer는 **APPROVE로 카운트 금지**, 재호출. "타임아웃이라 N/A" 처리 금지.

**MANDATORY — Stage 2 종합 전 감사 (post-call audit)**: 9명 reviewer 결과 종합 직전, 각 reviewer 항목별로 아래 표 출력.

| reviewer | 호출 | 회수 | 원판정 | finding(등급별) | scope밖→기록 | 차단사유 | 최종 |
|---|---|---|---|---|---|---|---|

- 차단사유 컬럼: 차단 대상 finding의 **등급 + 위치만** 기재. 기록 항목 상세는 deferred 파일에 (표에 중복 기재 금지).
- **`신규 __건 / 이월 재지적 __건` 컬럼 필수 (MANDATORY)** — 각 reviewer 의 finding 을 `.omc/deferred/` 와 동일 파일·동일 요지로 대조해 가른다. **질적으로 다른 두 상태가 같은 "REJECT" 로 뭉개지는 것을 막는다** — "신규 결함 0건인데 이월 재지적 1건으로 차단" 과 "신규 Critical 1건으로 차단" 은 사용자 판단이 완전히 달라진다. 이 수치는 **발산·정체 판정의 입력값**이며(발산 = 신규가 계속 나옴 / 정체 = 재지적이 반복됨), 발산·Deadlock 사용자 보고에도 그대로 싣는다.
- "안 됨" 또는 "회수 실패"가 1건이라도 있으면 종합 금지하고 누락분 재호출. **N/A 처리는 reviewer가 명시적 거부 응답을 반환한 경우만 허용** — 호출 시도조차 안 한 채 N/A 결정 절대 금지.
- code-simplifier subagent가 review-only 제약 위반(파일 수정 발생) 시 결과 무효 처리하고 제약 강화 후 재호출.
- Skill(pr-review-toolkit:review-pr) 결과는 `finding(등급별)` 컬럼에 `Critical=__, Important=__, Suggestions=__` 카운트를 기재하고, Suggestions 항목 목록은 minor 이슈로 보고서에 별도 기록 (deferred 파일 대상 아님).

**MANDATORY — Stage 2 게이트 판정 자체 검증 체크리스트 출력**: 게이트 판정 직전(audit 표 출력 후) 다음을 user-facing 텍스트에 출력할 것. 누락 시 판정 무효.
- [ ] scope 기준 문서: __________ (Stage 1과 동일 문서인가?)
- [ ] architect — 원판정: [...] / CRITICAL__ MAJOR__ MINOR__ / scope밖 기록 __건 / 차단사유: ______ / 최종: [차단|통과]
- [ ] security-reviewer — 원판정: [...] / CRITICAL__ HIGH__ MED__ LOW__ / scope밖 기록 __건 / 차단사유: ______ / 최종: [차단|통과]
- [ ] code-reviewer — 원판정: [...] / CRITICAL__ HIGH__ (@HIGH conf) / scope밖 기록 __건 / 차단사유: ______ / 최종: [차단|통과]
- [ ] test-engineer — 원판정: [...] / Test Health: __ / gap Risk High__ Med__ Low__ / scope밖 기록 __건 / 최종: [차단|통과]
- [ ] critic (OMC) — 원판정: [...] / CRITICAL__ MAJOR__ / scope밖 기록 __건 / 차단사유: ______ / 최종: [차단|통과]
- [ ] verifier — 원판정: [...] / Blockers __ / scope밖 기록 __건 / 최종: [차단|통과] / Stage 0 `requires_human_verification` 인계 __건 중 verifier 가 닫은 __건
- [ ] code-simplifier — 변경 라인 내 항목 __건 / 기존 코드 지적 __건(→기록) / 최종: [차단|통과]
- [ ] code-simplifier 프롬프트에 "변경 라인 한정" 제약 포함됐는가? (미포함 시 결과 무효 + 재호출)
- [ ] Skill(security-review) — 원판정: [...] / 가드A: [Y/N] / 최종: [차단|통과]
- [ ] Skill(pr-review-toolkit:review-pr) 카운트: Critical=__, Important=__, Suggestions=__ → 원판정: [Critical=0 AND Important=0 → APPROVE / 그 외 → REJECT] / Critical·Important는 scope 밖이어도 차단 → **최종판정 = 원판정과 동일** / deferred 기여 0건 / 최종: [차단|통과]
- [ ] Suggestions 항목 목록을 사용자 보고서에 minor 이슈 섹션으로 기록했는가? (게이트 차단 안 함, deferred 파일 대상 아님)
- [ ] 이번 라운드 기록 대상 각각이 deferred 파일에 존재하는가? — **부분집합 검증**. 누락 시 통과 금지.
- [ ] scope 밖 판정이 전건 기준 문서 대조인가? (추측 판정 0건)
- [ ] N/A는 명시적 거부 응답에 한함 — 호출 누락/회수 실패에 의한 N/A는 0건인가? (1건이라도 있으면 판정 금지, 누락분 재호출)
- [ ] code-simplifier subagent review-only 제약 준수 확인 (파일 수정 발생 0건인가?)
- [ ] `/pr-review-toolkit:review-pr` 내부 code-simplifier 자동 호출 정황 0건인가? (1건이라도 있으면 결과 무효, args에 `code errors comments tests types` 명시하여 재호출)
- [ ] Deadlock 조기 감지 체크 실행했는가? (Stage 2 게이트 판정 직전 필수 — `/security-review` 대상)
- [ ] 9명 전원 **최종** 통과인가? (Y → Phase 4 통과 / N → 'comment-analyzer 단독 반려 단축 경로' 해당 시 그 경로, 미해당 시 REJECT한 reviewer만 부분 재실행 → 전원 통과 시 Stage 0부터 재시작)
- [ ] 부분 재실행 카운트 #P (1 ≤ P ≤ maxPartialRerunRounds=15) — 한 시도 내 부분 재실행 횟수. P가 15 초과 시 사용자 보고 후 정지
- [ ] 다음 행동 명시: [Phase 4 통과 → 다음 단계 / comment-analyzer 단독 단축 경로 / REJECT한 것만 부분 재실행 / 전원 통과로 Stage 0 재시작 / 부분 재실행 15회 초과로 정지 / maxValidationRounds 도달로 정지]

**Stage 2 게이트 판정**:
- 9명 **전원 APPROVE → Phase 4 통과** — 단, 이 '전원 APPROVE'는 **Stage 1 통과 직후 fresh하게 9개를 한 번에 돌려 전원 APPROVE된 경우에 한함**. 직전에 부분 재실행으로 일부만 다시 돌려 깨끗해진 상태는 종료가 아니라 아래 불릿(부분 재실행 → Stage 0 재시작)을 따른다. Suggestions은 게이트 차단 안 함, 사용자 보고서에 minor 이슈 섹션으로 별도 기록하여 후속 작업 트래킹.
- **예외 — comment-analyzer 단독 반려**: pr-review-toolkit(#9)만 REJECT이고 그 Critical/Important finding이 전부 `[comment-analyzer]`발이며 다른 8개 reviewer 전원 APPROVE인 경우 → 아래 **"Stage 2 — comment-analyzer 단독 반려 단축 경로"** 섹션을 따른다 (단, 수정이 주석/문서 전용일 때만). full loop·Stage 1 재실행 생략.
- 위 예외에 **해당하지 않는** 채 1명이라도 REJECT/REQUEST CHANGES → 코드 수정 → **REJECT한 reviewer만 재실행** (APPROVE한 reviewer는 재실행 안 함). 또 REJECT면 수정 → REJECT한 것만 재실행 반복 (한 시도 내 부분 재실행 최대 maxPartialRerunRounds=15회 — 초과 시 사용자 보고 후 정지). REJECT였던 reviewer 전원 APPROVE 시 → **Stage 0부터 전체 재시작** (Stage 0 3개 → Stage 1 4개 → 전원 APPROVE 시 Stage 2 9개). Stage 2 9개 전체 재실행은 Stage 0·1 복귀 후에만. **카운터 리셋 없음** (Stage 0 재시작 시 +1). 재시작 웨이브의 슬롯별 재호출 여부는 위 「diff 불변 슬롯 재사용」을 따른다.

---

### 주석/문서 전용 수정의 단축 (Stage 0·1·2 공통, MANDATORY)

REJECT 를 해소하는 수정이 **코드 로직 0줄 · 주석/문서 텍스트만**이면(= 「대상 축」 표의 문면 ① 처방), REJECT 한 슬롯만 **단독 재검증**하고 통과 시 **Stage 0·1 확인 실행·재시작을 생략**한다. 텍스트는 실행되지 않으므로 다른 슬롯이 본 판정 전제(동작)를 바꾸지 못한다 — 판단이 아니라 diff 의 코드 줄 수(0)로 결정한다. 코드가 1줄이라도 섞이면 — 그 코드가 **테스트 전용**이면 아래 「테스트 전용 수정의 단축」, **프로덕션**이 섞이면 즉시 일반 경로(부분 재실행 → 확인 실행/재시작). 아래 comment-analyzer 단축 경로는 이 규칙의 **Stage 2 특수형**이다(체크리스트는 그대로 유효). (2026-08-18: STAT-572 Wave 10 「문면·주석 전용」 · Wave 26·27 문면 정정이 Stage 1 반려에서 나와 이 예외를 못 타고 4슬롯 재호출 → 다음 라운드로 이어졌다.)

### 테스트 전용 수정의 단축 (Stage 0·1 적용, MANDATORY — 2026-08-20 신설)

REJECT 를 해소하는 수정이 **프로덕션 src 0줄 · 테스트 파일(`*.spec.ts`/`*.test.*`·테스트 픽스처)만**이면(전형: 「대상 축」 표의 증인 부재 ① 처방 — witness 추가), 위 주석/문서 단축과 일반 경로의 **중간 단축**을 탄다. 판단이 아니라 **diff 의 파일 목록**으로 결정한다 — 프로덕션 파일이 1줄이라도 섞이면 즉시 일반 경로.

- **Stage 0 REJECT 해소 시**: REJECT 슬롯만 재실행(기존과 동일), **3슬롯 확인 실행 생략**.
- **Stage 1 REJECT 해소 시**: **Stage 0 재실행 생략**, REJECT 슬롯만 재실행, **4슬롯 확인 실행 생략**. 재실행 프롬프트에 "이번 수정 = 테스트 전용(프로덕션 0줄)" 명시.
- **Stage 2**: 기존 부분 재실행 규칙 그대로 (본 절 무관 — 이미 Stage 0 복귀 없이 돈다).
- **최종 보증은 그대로 남는다**: Stage 2 통과 후 **Stage 0부터 전체 재시작 1회**(기존 규칙)는 생략하지 않는다. 동시점 일관 APPROVE·신규 witness↔스펙 추적(intent-scope)·테스트 커버리지 판정(pr-test-analyzer)은 이 마지막 풀 패스가 전부 fresh 하게 본다 — 그래서 중간 라운드의 Stage 0·확인 실행 반복이 테스트 전용 수정에서는 **중복**이다. (검사를 없애는 게 아니라 뒤로 몰아주는 구조.) 이 재시작에도 「diff 불변 슬롯 재사용」은 적용되나, 테스트 추가로 diff가 변했으므로 witness를 아직 못 본 슬롯은 전부 재호출된다 — 두 규칙은 충돌하지 않는다.
- **카운터**: 본 경로는 Stage 0 를 (재)시작하지 않으므로 maxValidationRounds 가 아니라 부분 재실행 카운터(maxPartialRerunRounds)로 센다.
- (2026-08-20 STAT-586 실측: Phase 4 5라운드 차단 지적 전원이 witness·주석 — 프로덕션은 `d0ce0f6` 이후 무변경. witness 추가가 "코드"라서 주석/문서 단축을 못 타고 매 라운드 Stage 0 3슬롯(~6분)+확인 실행 풀 경로를 반복 — 본 단축이면 라운드당 ~15-20분 × 3~4회 = **~45분-1h** 절약이었다.)

### Stage 2 — comment-analyzer 단독 반려 단축 경로 (예외, MANDATORY)

Stage 2에서 `pr-review-toolkit:review-pr`의 **comment-analyzer만** blocking이고 **주석/문서 전용 수정**으로 해소되는 경우, 일반 REJECT 처리(부분 재실행 → 전원 통과 시 Stage 0부터 재시작) 대신 comment-analyzer만 재검증하고, 통과 시 Stage 0·1 재시작도 생략한다. 단, 이 단축 경로는 **Phase 4 한정 규칙**으로 허용 범위가 `40-common-loop.md` 사소 수정 예외(3번: 주석 오타 한정)보다 넓다(주석/문서 텍스트 전용 수정 전부 허용). Phase 0/1·ralplan·team-ralph에는 미적용.

**MANDATORY — 단축 경로 자체 검증 체크리스트 출력** (pr-review-toolkit REJECT 확인 직후 + 매 단독 재호출 직전):
- [ ] 다른 8개 reviewer 전원 APPROVE인가? (즉 comment-analyzer 빼고 전부 승인 / N이면 단축 불가 → full loop)
- [ ] pr-review-toolkit의 Critical/Important finding이 전부 `[comment-analyzer]`발인가? (review-pr 출력 `- [agent-name]: ...` 기준. 다른 agent-name 1건이라도 있으면 → full loop)
- [ ] 수정이 주석/문서 텍스트 전용인가? (코드 로직 1줄이라도 변경 시 단축 무효 → 일반 REJECT 처리로: 부분 재실행 → 전원 통과 시 Stage 0부터 재시작)
- [ ] 위 3개 ALL Y → 주석만 수정 → `Task(subagent_type="pr-review-toolkit:comment-analyzer")` 단독 재호출 (review-pr/Stage 0·1/나머지 8개 재실행 금지)
- [ ] comment-analyzer 판정: "Critical Issues" 0건 → APPROVE → **Stage 2/Phase 4 통과** (Stage 0·1·나머지 재실행 생략) / ≥1건 → 주석 재수정 후 재호출 (Improvement Opportunities·Recommended Removals는 minor 기록, 게이트 차단 안 함)
- [ ] **진입-재검증 비대칭 차단**: review-pr 게이트가 `Important`로 집계해 단축 경로 진입 사유가 됐던 comment-analyzer finding은, 단독 재호출에서 `Improvement Opportunities`/`Recommended Removals`로 분류돼도 **blocking 유지**(minor 강등 금지) → 주석 재수정 후 재호출. 단독 `Critical Issues` 0건만으로 통과시켜 진입 기준(Critical=0 AND Important=0)보다 느슨해지는 것 방지.
- [ ] 단축 루프 카운터 #K (1 ≤ K ≤ maxCommentShortcutRounds=15) — maxValidationRounds 미소비·별개 누적. K=15 내 APPROVE 못 하면 **사용자 보고 후 정지** (자동 통과·자동 full loop 금지)

---

### maxValidationRounds 카운트 규칙

- **카운트 단위 = 1 시도(cycle)**: Stage 0을 **(재)시작할 때마다 +1**. Stage 0 단독 미통과로 재시작하든, Stage 1 미통과로 수정 후 Stage 0에 복귀하든, Stage 2 미통과로 Stage 0에 복귀하든 무조건 +1. (Stage 1 4개·Stage 2 9개 호출은 그 시도의 일부라 별도 카운트 안 함. Stage 0 `INPUT_MISSING` 보강 재호출도 미증가 — 리뷰어 판정이 아니라 오케스트레이터 입력 누락이다.) 예: `Round1` Stage0 통과→Stage1 통과→Stage2 일부 REJECT→부분 재실행→클린→Stage0 복귀 / `Round2` Stage0·1 통과→Stage2 전원 통과→종료.
- **리셋 없음**: **한 번의 Phase 4 실행 내부에서는** 어떤 경우에도(Stage 2 REJECT·코드 수정 포함) 카운터를 0으로 초기화하지 않는다. 시도가 누적되어 maxValidationRounds=15 도달 시 사용자 보고 후 정지(자동 통과 처리 금지). (team ralph가 외곽 사이클로 Phase 4를 **통째로 재진입**하는 경우의 fresh start는 별개 scope — `21-team-ralph.md` 참조.)
- **부분 재실행은 시도 카운터 미반영**: 한 시도 안에서 REJECT한 reviewer만 다시 돌리는 부분 재실행은 위 시도 카운트(N)를 안 올린다. 대신 별도 `maxPartialRerunRounds=15`(한 시도 내 부분 재실행 최대 횟수, P로 표기)로 제한 — P가 15 초과 시 사용자 보고 후 정지.
- 매 시도(Stage 0 재시작) 시 user-facing 텍스트에 현재 라운드 번호 표기: 예) `Round 4/15`.

**MANDATORY — 라운드 카운터 자체 검증 체크리스트 출력**: 매 Stage 0 (재)시작 직전 다음을 user-facing 텍스트에 출력할 것.
- [ ] 라운드 표기 출력됨: `Round N/15`
- [ ] N ≤ maxValidationRounds(=15)인가? (N > 15이면 호출 금지, 사용자 보고 후 정지)
- [ ] N=15인 경우 다음 시도가 마지막임을 명시 출력했는가? (자동 통과 처리 금지)
- [ ] 이번 Stage 0 시작에서 N이 직전 대비 정확히 1 증가했는가? (리셋·중복증가 없음 — `INPUT_MISSING` 보강 재호출만 예외)

---

### 라운드 종료 보고 — 누적 진행표 (MANDATORY — 2026-08-21 신설)

매 라운드의 **마지막 게이트 판정 직후**(Stage 0 REJECT로 라운드가 끝나면 그 시점, Stage 2까지 갔으면 Stage 2 판정 직후) 아래 누적 진행표를 user-facing 텍스트에 **선제 출력**한다. 사용자가 "진행표 보자"라고 요청하게 만들지 말 것 (2026-08-21 STAT-589 실측: R1 도중 사용자가 직접 요청해야 했다 — 기존에는 이 선호가 세션 메모리에만 있어 세션·모델에 따라 누락됐다).

| R | 시각(시작→판정) | Stage 도달 | 차단 슬롯(등급) | 신규/이월 | 처리 |
|---|---|---|---|---|---|

- 행은 **R1부터 전 라운드 누적** — 이번 라운드만 떼어 보고하면 추이(발산·정체·수렴)가 안 보인다. 부분 재실행은 해당 라운드 행의 「처리」에 요약.
- 「신규/이월」= 각 Stage audit 표의 `신규 __건 / 이월 재지적 __건` 합산 — 발산·Deadlock 판정과 **같은 입력값**을 쓴다(별도 집계 금지 — 두 수치가 갈리면 한쪽이 오염).
- 「시각」은 deferred 파일 「라운드 기록」 줄에서 그대로 가져온다 (이중 기록이 아니라 **같은 기록의 표시** — 라운드 기록이 SSOT).

---

### Phase 4 선제 리뷰 컨텍스트 (MANDATORY)

Plugin native reviewer(codex:review / codex:adversarial-review — prompt 주입 불가)를 위한 사전 예방. 아래 Deadlock 규칙(사후 대응)의 선제 버전으로, 유일한 전달 통로인 git diff 채널을 Phase 4 진입 **전에** 미리 채운다.

- **Phase 2(구현) 완료 → Phase 4 진입 전**에 알려진 환경 invariant(사용자 명시: 샌드박스 제약, 운영 DB 부재, 외부 API mock 등)가 있으면, 관련 코드 위치에 `// NOTE(review-context): <invariant 설명>` **신규 주석**을 추가한다. 신규 주석은 git diff에 포함되므로 두 native reviewer 모두에게 읽힘이 보장된다.
- 특정 파일에 귀속되지 않는 전역 invariant는 AGENTS.md(있으면)나 commit 메시지에 반영한다.
- **`.omc/deferred/` 기록 중 이번 변경 범위와 겹치는 항목은 같은 방식으로 반영한다 (MANDATORY)** — "사용자 dismiss" 출처만이 아니라 **오케스트레이터 scope 판정 이월분도 포함**한다. `50-critic.md` 「선제 환경 컨텍스트 주입」 수집 소스 3번이 **프롬프트 주입 가능한** 리뷰어를 덮는다면, 이 주석 통로는 **주입 불가 리뷰어**(레지스트리 「프롬프트 주입」=불가 인 행)를 덮는 유일한 경로다. 둘의 합집합이 16슬롯을 빠짐없이 덮어야 이월 결정이 라운드를 소모하지 않는다.
  - ⚠️ **항목당 최소 1줄.** 이월 사유를 길게 재서술하지 말고 `// NOTE(review-context): <요지> — .omc/deferred/ 기록(YYYY-MM-DD) 참조` 형태로 **포인터만** 둔다. 주석을 늘리면 그 주석이 다음 라운드 comment 리뷰어의 검토 대상이 되어 새 finding 을 만든다(2026-08-07 실측: 한 라운드에서 정정한 문면 거짓 4건이 전부 직전 라운드에 추가한 주석이었다).
  - **일반 규율은 `40-common-loop.md` 「공통 — 검증되지 않은 단언을 만들지 않는다」가 canonical** 이다(개수 복제 금지 · 실측에 범위·시점 · 인과에 확인 방법 · 열거 동반 갱신 · "왜"만 적기 + 산출 직전 자체 검증). 본 항은 그 원칙을 **`NOTE(review-context)` 주석에 적용한 특례**다 — 여기 복제하지 말 것.
- **비목표(non-goals) 선언 (MANDATORY — 산출물이 검증 장치일 때)**: 이번 산출물이 **무언가를 막는 코드**(게이트·린터·검사 스크립트·가드)이면, **무엇을 막지 않기로 했는지**를 Phase 4 진입 **전에** 같은 `// NOTE(review-context):` 통로로 내린다.
  - **왜 필요한가**: 검증 장치에 대한 *"이렇게 쓰면 뚫린다"* 는 지적은 **대개 사실이라 반박 근거가 없다.** 비목표가 선언돼 있지 않으면 참인 지적을 전부 수용하게 되고, 수용할 때마다 장치가 커지며 **그 새 코드가 다음 라운드의 리뷰 대상**이 된다(`40-common-loop.md` 「검증되지 않은 단언」 말미의 *"고치는 행위 자체가 새 검증 대상을 만든다"* 와 같은 기제). 선언이 있으면 같은 지적을 **결함이 아니라 사양**으로 되돌릴 수 있다.
  - **최소 형태 2줄**: ⓐ **위협 모델** — 무엇을 막는가(예: *"막을 대상은 실수로 들어오는 코드이지 의도적 우회가 아니다"*) ⓑ **그 밖의 처리** — 막지 않는 것을 무엇이 받는가(예: *"작정하고 만든 입력은 탐지 대상이 아니며 코드리뷰가 backstop 한다"*).
  - ⚠️ **미탐지 사례를 여기 열거하지 않는다.** 열거는 표본이라 빠진 항목이 곧 새 지적이 되고, 열거 자체가 다음 라운드 comment 리뷰어의 검토 대상이 된다. 사례는 **테스트의 `미탐지 사양:` 접두 케이스로 고정**하고 주석은 그쪽을 SSOT 로 가리키기만 한다.
  - **시점이 규칙의 전부다** — Phase 1(plan) 산출물에 이 절이 있으면 그대로 옮기고, 없으면 **Phase 4 진입 전에** 만든다. 라운드가 시작된 뒤에 만들면 **그 앞 라운드들이 방어선 없이 돈다** (2026-08-10 STAT-567 실사고: 게이트가 이 선언을 36커밋 중 12번째에 넣었고, 앞선 라운드들은 "작정하면 뚫린다" 류 지적을 전건 수용하며 돌았다).
- 대상 invariant 0건이면 생략. 추측성 invariant 날조 금지 — 사용자 발언·deferred 기록에 실재하는 것만. (**비목표 선언은 이 생략 대상이 아니다** — 산출물이 검증 장치이면 환경 invariant 수집 결과와 무관하게 필수다.)
- `NOTE(review-context)` 프리픽스로 일반 주석과 구분한다 (리뷰 오인 방지용임을 명시). 코드 동작 설명 주석 대용으로 남용 금지.

---

### Plugin Reviewer Deadlock 조기 감지 (MANDATORY)

**적용 대상 = `54-phase4-registry.md` 레지스트리의 「프롬프트 주입」이 `불가`인 행 전부** (명단 하드코딩 금지 — 이름을 박아 두면 신규 reviewer가 규칙에서 누락된다). 현재 해당: `codex:review`·`codex:adversarial-review`·`Skill(/security-review)`. 주입 불가면 환경 invariant를 영구 인지하지 못해 **같은 지적을 반복**할 수 있다 — adversarial-review는 등급이 확인됐어도 주입 불가는 그대로이므로 대상이다(등급 유무와 무관한 별개 사유).

⚠️ **본 규칙은 「반복형」 정체만 받는다.** 매 라운드 **새 지적**이 나오며 차단이 유지되는 「발산형」 정체는 `50-critic.md`의 **Finding 발산 조기 감지**가 받으며, 그쪽 적용 대상은 **레지스트리 전 행(Stage 0·1·2 무관, 주입 가능 여부 무관)**이다. 두 규칙의 합집합이 16슬롯을 빠짐없이 덮어야 한다 — 레지스트리 「완결성 자기검사」 참조. (2026-08-07 실사고: `pr-review-toolkit`·`code-simplifier`가 주입 가능·Phase 4라는 이유로 두 규칙 어디에도 안 들어가 9라운드를 소진했다.)

**실행 시점**: Stage 1 게이트 판정 직전 + Stage 2 게이트 판정 직전 **각각** 실행한다.

**Deadlock 정의**:

다음 조건이 **모두** 만족되면 plugin 구조적 deadlock으로 간주:

1. **연속 2 라운드 이상** 적용 대상 reviewer(codex:review / codex:adversarial-review / Skill(/security-review)) 중 하나가 REJECT/REQUEST CHANGES/needs-attention 등 비-APPROVE 판정 유지
2. 동일 reviewer의 핵심 finding이 의미상 동일 영역(예: 동일 file:line, 동일 우려 카테고리)에서 **반복** — finding 영역이 oscillating해도 의미상 동일하면 deadlock 인정
3. **다른 reviewer**(codex:critic·ocr:delegate-review + codex:review/adversarial 중 다른 한쪽)가 동일 라운드 시점에 ACCEPT 또는 ACCEPT-WITH-RESERVATIONS 등급 안정적으로 도달
4. **사용자 명시 환경 컨텍스트**(예: 운영 DB 부재, ETL worker 미가동 등)가 finding의 전제를 무효화하나 plugin reviewer가 prompt 주입 미지원으로 영구 인지 못함 — **또는** finding이 scope 기준 문서 대조 결과 **scope 밖**이며, 가드 A 대상 reviewer가 낸 것이어서 fail-safe 차단이 반복됨

**MANDATORY — Deadlock 조기 감지 자체 검증 체크리스트 출력** (매 라운드 audit 후, **Stage 1 게이트 판정 직전 + Stage 2 게이트 판정 직전 각각**):
- [ ] 이번 체크의 stage: [Stage 1 / Stage 2]
- [ ] 연속 비-APPROVE 라운드 수: [N=?]
- [ ] N >= 2인가? (Y → 다음 항목, N → 본 규칙 미적용)
- [ ] 동일 reviewer 핵심 finding이 의미상 동일 영역에서 반복인가? (Y/N)
- [ ] 다른 reviewer는 ACCEPT/ACCEPT-WITH-RESERVATIONS 안정적인가? (Y/N)
- [ ] 사용자 명시 환경 컨텍스트가 finding 전제를 무효화하는가? **또는** finding이 scope 밖이며 가드 A 대상 reviewer 발인가? (Y/N)
- [ ] 4 항목 모두 Y → 다음 항목 (Deadlock 추정)
- [ ] **조건 4의 근거를 원문 인용 가능한가?** (사용자 명시 환경 컨텍스트 문구 / scope 기준 문서·`.omc/deferred/` 이월 기록 해당 절 — 인용문을 그대로 기재) → **Y = 자동 dismiss** (아래 「자동 dismiss」 — 이번 실행 한정, 질문·정지 없음) / **N = 사용자 알림 + 선택 요청 후 정지** (근거 인용 없는 자동 dismiss/통과 금지)

**MANDATORY — 자동 dismiss (2026-08-20 개정 — 멈춤 최소화, 이번 실행 한정)**: 조건 4의 근거 — 사용자 명시 환경 컨텍스트 문구, 또는 scope 기준 문서·`.omc/deferred/` 이월 기록의 해당 절 — 를 **원문 그대로 인용**할 수 있으면 사용자 질문 없이 아래 「옵션 A 처리」를 자동 적용한다(dismiss 카운트·stage 통과 인정·deferred 기록·dismiss 유지 전부 동일). audit 표와 deferred 기록에 `자동 dismiss (plugin 한계)` + **인용 근거 원문**을 명기한다. 인용하지 못하면 자동 dismiss 불가 — 아래 에스컬레이션 보고로 폴백. 효력은 **이번 Phase 4 실행 한정** — **protocol exception 영구 등록(옵션 C)은 자동화 금지**: config 변경은 이후 모든 실행의 리뷰 그물에 영향을 주므로, 실행 종료 보고에서 이번에 자동 dismiss 된 요지 목록과 함께 등록 여부를 일괄 제안한다(실행 중 질문 금지). 채널 강화(옵션 B)도 실행 중 자동 적용하지 않는다 — 필요 시 같은 종료 보고에서 제안. (2026-08-08 실사고 — round 2 이월 항목을 round 10 에 동일 요지로 재지적: 근거가 deferred 기록에 이미 있었으므로 본 개정이면 질문 없이 닫혔다.)

**MANDATORY — 사용자 에스컬레이션 보고 형식 (근거 인용 불가 시)**:

다음 4 항목을 user-facing 텍스트에 출력하고 사용자 선택 대기:

1. **Deadlock 진단 요약**: 어느 reviewer가 몇 라운드 연속 어떤 finding 영역을 반복하는지 1-2 문장
2. **Plugin 구조적 한계 명시**: 해당 reviewer가 plugin native command(`disable-model-invocation: true`)라 prompt 주입 미지원 — git diff + 자동 read 채널만 컨텍스트 source. 단, **코드 주석은 git diff에 포함되므로 두 reviewer 모두에게 읽힘** (review native는 새로 추가된 주석만 보장 — 기존 주석은 diff 미포함으로 미보장 / adversarial-review는 collectReviewContext가 파일 내용도 수집하므로 기존 주석도 읽힐 가능성 높음). 환경 invariant를 코드 주석으로 남기면 실질적 우회 가능.
3. **다른 reviewer 통과 상태**: 다른 reviewer ACCEPT/ACCEPT-WITH-RESERVATIONS 등급 + 그 reviewer가 컨텍스트 인지한 근거 (예: critic.md instruction 주입, AGENTS.md cat 등)
4. **사용자 선택지** (최소 3개):
   - 옵션 A: deadlock reviewer finding을 plugin 한계로 명시 dismiss → Stage 2 진입 (또는 다음 단계)
   - 옵션 B: 추가 시도 (AGENTS.md/focus arg/commit 메시지/코드 주석 강화 등 가능 채널 명시) → maxValidationRounds 한도 내 재시도. **코드 주석 강화 시**: finding 관련 코드 위치에 `// NOTE(review-context): <환경 invariant 설명>` 형식 주석 추가. review native 효과 보장하려면 신규 주석으로 추가(diff 포함).
   - 옵션 C: protocol exception 영구 추가 (omc-skill-config 변경) — 본 사례 외 모든 미래 autopilot에 적용

**MANDATORY — 근거 없는 자율 dismiss 금지**: 위 「자동 dismiss」 요건(근거 원문 인용 + 기록)을 갖추지 못한 dismiss·Stage 2 진입 자율 결정 금지. 인용 불가 시 사용자 선택지 출력 후 명시 응답 대기.

**MANDATORY — Deadlock 처리 (자동 dismiss 또는 사용자 선택 후)**:
- **옵션 A 처리** (사용자 선택 또는 위 「자동 dismiss」 적용 시): deadlock reviewer finding을 명시 dismiss로 카운트하고 해당 stage 통과 인정. audit 표에 "사용자 명시 dismiss (plugin 한계)"(자동 적용 시 "자동 dismiss (plugin 한계)") 표기.
  - **deferred 기록 의무**: dismiss한 finding을 `.omc/deferred/` 파일에 기록한다 (출처에 "사용자 dismiss — 가드 A"·"사용자 dismiss — plugin 한계"·자동 적용 시 "자동 dismiss — plugin 한계" 중 해당 명기, 등급 불명 시 등급란에 `불명(가드A)`). audit 표는 채팅 출력이라 소실되므로 파일 기록이 필수.
  - **dismiss 유지**: dismiss된 finding(사용자·자동 불문)은 **동일 파일 + 동일 요지** 기준으로 이번 Phase 4 실행 내내 dismiss를 유지한다 (재차단·재질문 금지). 이후 라운드 audit 표에는 "dismiss 유지"로 표기하고, deferred 파일 기록은 최초 1회만.
- 사용자가 옵션 B 선택 시: 명시한 강화 채널 적용 후 Stage 1 재실행. maxValidationRounds 카운트 그대로 누적. (코드 주석 채널은 review/adversarial-review 모두에게 읽히므로 **1순위 권장 채널**)
- 사용자가 옵션 C 선택 시: omc-skill-config 변경 commit 후 본 라운드 dismiss로 Stage 1 통과.
  - **protocol exception 기록 규격 (MANDATORY)**: 본 파일(`10-autopilot.md`) 최하단 `#### Protocol Exceptions` 절(없으면 신설)에 1줄 추가 — `- YYYY-MM-DD | <reviewer> | <finding 요지> | <예외 사유 (사용자 결정 근거)>`.
  - 해석: 등록된 예외는 **동일 요지 finding을 이후 모든 autopilot Phase 4에서 차단 사유로 삼지 않는다** (동일 요지 판단은 Deadlock 규칙의 "의미상 동일" 기준 준용).
  - 기록 직후 ai-stack 스냅샷 반영(커밋·푸시)을 사용자에게 제안한다. 즉흥 형식·타 파일 기록 금지.

**왜 이 규칙이 필요한가**: codex:review/adversarial-review는 plugin native command로 prompt 주입 슬롯이 없다. 운영 DB 부재 같은 환경 invariant를 인지 못해 finding을 영구 반복할 수 있다. mandate "전원 APPROVE"는 본 시나리오에서 unworkable하므로 조기 감지 + 근거 인용 자동 dismiss(이번 실행 한정)·인용 불가 시 사용자 결정으로 시간/토큰 낭비 방지.

---

### Phase 4 루프 종료 규칙 — 검토했으나 보류 (2026-08-10, STAT-567)

라운드가 10회까지 가고 검증 장치가 산출물의 15배 규모로 자란 실행에서 후보 7개를 도출해 **2개만 채택**했다 — 위 「비목표 선언」과 `50-critic.md` 발산 정의의 **대상 축**. 나머지 5개는 **같은 논의를 처음부터 반복하지 않도록** 반증·근거와 함께 남긴다. **다시 꺼낼 때는 아래 반증부터 확인할 것** (반증을 안 보고 재도입하면 그때 든 비용을 다시 낸다).

⚠️ 채택 기준이 「효과 크기」가 아니라 **「효과 × 오작동 위험 × 도입 비용」** 이었다. config 의 틀린 규칙은 **이후 모든 실행에 조용히 적용되고 그것을 잡아 줄 테스트가 없다** — 그래서 아직 다듬어지지 않은 규칙은 넣지 않는 쪽이 기본이다.

| # | 후보 | 보류 사유 |
|---|---|---|
| G1 | 산출물 대비 검증 장치 **비율 임계** 경보 | **전제가 반증됐다.** 15.5배였던 그 실행에서 가장 큰 덩어리(vacuous 방어)는 스키마 드리프트를 막는 **유일 방어**였고, 오히려 **덜 만들어진 축**(비-TS 파일 스캔 대조군 부재)이 따로 있어 그 라운드의 차단 사유가 됐다 — 경보가 울렸어도 정답은 "줄여라"가 아니었다. 단일 스칼라가 *"많은데 필요한 것"* 과 *"많은데 편중된 것"* 을 같은 숫자로 만든다 |
| G2 | **회수 예정 자산**(수명 축)의 검증 장치 finding 은 차단 대신 이월 | **수명 축은 폐기, 대신 「대상 축」으로 채택됐다** — 규칙 본문은 위 `#### 대상 축` 절이 SSOT 다(여기 복제하지 말 것). ▸ **수명 축을 다시 꺼낼 때 확인할 반증**: 원안은 효과가 가장 컸으나(그 라운드가 통째로 없었을 것) *"곧 지운다"* 의 근거가 **일정 미정**이면 "임시"가 무기한이 된다. 그래서 *"회수 트리거가 날짜·확정 이벤트로 못 박힌 경우만 임시"* 로 보정했더니 **그 게이트가 영구로 분류되어 효과가 0** 이 됐다 — 안전하게 만들면 효과가 사라지고 효과를 남기면 위험한 경계다. 채택된 대상 축은 이 딜레마가 없다: **수명을 묻지 않고 「지금 뚫려 있는가」만 묻기 때문**이고, 그 물음은 재현으로 닫힌다 |
| G4 | 라운드 통과 확률 `(1−p)^슬롯수` 를 라운드마다 표시 | 종료 규칙이 아니라 **보고용 숫자**이고, 채택한 G3·G5 가 이미 보고를 만든다. ▸ 참고: 슬롯 13개일 때 리뷰어 1인당 차단 확률 5%면 라운드 통과 51%, 10%면 25%, 20%면 5.5% — **개개인이 95% 정확해도 라운드의 절반이 실패한다**는 것이 이 구조의 상수다 |
| G6 | plan 의 **비용·규모 견적**을 실제와 대조해 배수 이탈 시 보고 | G1 과 **같은 것을 다른 각도**로 본다. G1 이 잘못된 신호를 낼 뻔했으므로 이 계열 전체를 한 번 더 관측한 뒤 판단한다. ▸ 계기: 그 실행의 plan 이 *"비용은 CI 2줄 × 2레포뿐"* 이라 적고 승인받았는데 그 문장이 scope 판정에 **한 번도 쓰이지 않았다**(현행 scope 기준은 *작업 항목*만 대조하고 *규모 견적*은 대조 대상이 아니다) |
| G7 | 수정 지시를 **인스턴스가 아니라 클래스로** 하고, 인스턴스 열거는 **재실행 가능한 grep 명령으로 위임** | 수정 품질은 확실히 오르지만(그 실행의 한 부분 재실행에서 차단 9건 중 7건이 직전 수정이 남긴 같은 계열이었다) **라운드 수 영향이 작다.** `40-common-loop.md` 「자매 파일·미러 레포 대칭」이 "다른 파일" 축을 이미 덮고 있고, 이것은 "**같은 파일 안 다른 위치**" 축의 추가다. ▸ 함정: 클래스를 닫으면 **그 클래스를 서술한 문면이 새 검토 대상**이 되므로, 열거는 문장이 아니라 명령으로 남겨야 한다 ▸ **2026-08-18 부분 재개**: 「커밋 전 잔존 grep」만 `40-common-loop.md` 자체 검증 **ⓔ**로 채택(STAT-572/stat-docs #14 에서 같은 형태 5회 재발 = 5라운드 실측 — *"라운드 수 영향이 작다"* 는 그 실행에서 반증). 수정 지시의 클래스화 자체는 여전히 보류 |
