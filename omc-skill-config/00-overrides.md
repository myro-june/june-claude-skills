## OMC Skill Config Overrides — 00 헤더 (적용 원칙)

> **CRITICAL — BLOCKING REQUIREMENT**
> 이 폴더(`~/.claude/omc-skill-config/`)의 모든 설정값은 각 스킬 SKILL.md의 기본값을 **완전히 대체(override)** 한다.
> **이 파일(00-overrides.md)만 CLAUDE.md에 상시 로드된다. 나머지 섹션 파일(10~73)은 상시 로드되지 않는다.**
> 스킬 실행 시 SKILL.md를 읽은 후, **해당 섹션 파일 전문을 Read 도구로 반드시 로드하고** 해당 스킬의 설정을 전부 적용하라.
> 컨텍스트에 이미 있다고 가정하지 말 것 — 실제 Read 없이 진행하거나 하나라도 누락하면 실행 결과가 무효다.
> 부분 적용 금지 — 전체 적용만 허용.
>
> **적용 체크리스트 (MANDATORY — 스킬 실행 전 확인):**
> 1. 이 폴더에서 해당 스킬 섹션 파일을 찾아 **Read 도구로 전문을 읽는다** (`10-autopilot.md`, `20-ralph.md`, `30-ralplan.md` 등)
> 2. 섹션 파일이 "`XX-….md` 참조"로 지목하는 공통/보조 파일(`40-common-loop.md`, `50-critic.md`, `51-codex-reviews.md`, `53-ocr-review.md`, `54-phase4-registry.md`, `55-stage0-gate.md` 등)도 그 시점에 Read한다
> 3. 모든 key=value 쌍을 SKILL.md 기본값 대신 적용한다
> 4. artifactName이 있으면 산출물 파일명 suffix로 붙인다
> 5. 불릿(-) 항목의 행동 지시도 전부 따른다
> 6. 누락 항목이 없는지 최종 확인한다
>
> ※ **자동 주입(1차 경로)**: UserPromptSubmit hook(`~/.claude/hooks/omc-config-inject.py`)이 OMC 트리거 키워드 감지 시
> 해당 섹션 파일 전문을 `<omc-config-inject>` 블록으로 컨텍스트에 자동 주입한다.
> 주입 블록이 컨텍스트에 있으면 그 내용을 그대로 적용하고(해당 파일 중복 Read 불요),
> **없으면(스킬 체인 진입·compaction 이후 등) 반드시 Read 도구로 로드하라(2차 백스톱).**
>
> ⚠️ **compaction·세션 재개 구간이 최대 취약점이다.** 훅 주입은 **사용자 프롬프트의 키워드**로 발동하는데,
> 실행 모드가 이미 진행 중이면 사용자가 키워드를 다시 치지 않으므로 **아무도 주입해 주지 않는다.**
> 이때 호출 형태를 **이전 대화 트랜스크립트에서 복원하지 마라** — 트랜스크립트에는 프롬프트 본문만 남기 쉬워
> `subagent_type`·대상 flag 같은 파라미터가 누락되고, 그 빈칸을 기본값·기억으로 채우게 된다.
> **호출 형태의 SSOT 는 언제나 이 폴더의 섹션 파일이다.** (2026-08-07 실제 위반 2건 — ocr 래퍼를 금지 목록에
> 이름이 직접 적힌 `general-purpose` 로 호출 / `codex:review` 를 raw CLI 대신 companion wrapper 로 호출.
> 둘 다 해당 섹션 파일을 그 세션에서 한 번도 Read 하지 않은 상태였다.)
>
> **MANDATORY — 프로토콜 준수 원칙:**
> 스킬의 SKILL.md에 정의된 실행 흐름(step 순서, 루프 조건, 순차/병렬 제약)을 **정확히** 따를 것.
> 편의를 위해 step을 건너뛰거나, 루프를 조기 종료하거나, 순차 제약을 병렬로 바꾸는 것을 금지한다.
> 특히: ralplan의 Critic non-APPROVE 시 full closed loop 재실행, Architect 완료 후 Critic 순차 실행,
> autopilot Phase 0 critic 미통과 시 Phase 1 진입 금지, Phase 0/1 수정 발생 시 Architect→Critic 전체 루프 재실행,
> codex critic에 critic.md 전문 포함.
> 프로토콜 위반은 결과물 무효와 동일하게 취급한다. 위반 예시: Phase 0 critic 없이 Phase 1 진입, 수정 후 루프 생략(공통 사소 수정 예외 규칙 미해당 시), OMC critic 단독 실행(codex critic 누락).

### 질문 방식 — 전역 (MANDATORY — CLAUDE.md failure_mode_guards "User input" 가드 오버라이드)

명확화·선호·설계 선택 질문에 **AskUserQuestion 박스를 사용하지 않는다.** 질문은 일반 대화 텍스트로 출력하고, 사용자의 자유 텍스트 답변을 받는다.

- 모든 질문은 **3단 구조 강제**: ① **배경 설명**(왜 묻는지, 전문용어는 반드시 풀어서) → ② **구체 예시**(답에 따라 결과가 갈리는 상황 1개 이상) → ③ **질문 + 참고 선택지**(번호 목록, 마지막에 "번호로 답해도 되고 자유롭게 설명해도 된다" 안내). 상세 정의와 출력 예시는 `71-deep-interview.md` "질문 출력 3단 구조" 절이 canonical.
- **예외 (AskUserQuestion 유지)**: 실행 게이트 — 파괴적 작업 승인, 실행 방식 승인(deep-interview Phase 5 Execution Bridge, autopilot pauseAfterExpansion/pauseAfterPlanning 승인 등) 같이 명시적 선택이 안전장치인 지점.
- **실행 모드 진행 중 「비용·진척·완주 여부」 재확인 금지 (MANDATORY — 2026-08-20 실위반)**: 사용자가 실행 모드(autopilot·Phase 4·ralph·team ralph·워크플로 등)를 이미 승인해 루프가 도는 중이면, **프로토콜이 문자로 정의한 pause 지점** — Phase 0 critic 게이트, autopilot pauseAfterExpansion/pauseAfterPlanning, 파괴적 작업 승인, PR 머지 승인 — **외의 어느 지점에서도** "비용이 큰데 계속?" · "전체 완주할까 일부만?" · "여기서 멈출까?" 류로 멈추지 않는다. **판단 기준(단 하나): 그 pause 가 해당 섹션 파일(10-autopilot 등)에 문자로 적혀 있는가.** 적혀 있으면 게이트, 적혀 있지 않으면 진행이 곧 준수다. 토큰·비용 소모량은 **승인의 근거이지 재확인 사유가 아니다** — 승인은 이미 그 비용을 받아들인 것이다. 프로토콜의 연속 단계(Stage 0→1→2, REJECT 재실행 루프, maxRounds 소진)는 barrier 없이 **완주가 기본값**. 비용 우려로 protocol 을 **줄이고 싶으면**(단계 skip·조기 종료) 줄이지 말고 그대로 실행하라 — 축소 충동의 답은 "pause 해서 묻기"가 아니라 "적힌 대로 완주"다. (실위반: Phase 4 Stage 1 직후 "남은 게이트 비용 큼, 전체 완주 vs 자체 리뷰?"로 AskUserQuestion 게이트를 걸어 사용자가 두 번 재촉 — "그냥 진행해야지" / "프로토콜에 확인하라고 멈추는 게 있었음?". 프로토콜엔 그 pause 가 없었다.)
- "같이 확인" 요청에는 before/after diff를 대화로 먼저 펼친 뒤 질문한다 (diff 생략 금지).
- anti-patterns: ❌ 설명 없이 질문만 던지기 / ❌ 예시 없이 추상 설명만 / ❌ 설명이 길다는 이유로 AskUserQuestion 박스 회귀 / ❌ 전문용어 무풀이 사용 / ❌ **이미 승인된 실행 모드를 비용·진척 우려로 AskUserQuestion 재게이트** / ❌ **프로토콜에 없는 "일부만 할까 전체 할까" 중간 pause**.

### 공통 구현 원칙 — 전역 (MANDATORY — 2026-08-20 확정)

코드 구현·수정 작업(신규 기능·버그 수정·리팩터링) 전 구간에 적용한다. **예외는 문서·설정·주석 전용 변경과 테스트 하네스가 없는 일회성 스크립트뿐**이다. 예외 해당 여부가 애매한 작업(탐색적 스파이크 포함)은 실행자가 임의 판정하지 말고 **사용자에게 묻는다** — 예외 발동권은 사용자에게 있다(테스트 없이 진행하라는 명시 지시가 있으면 그 지시가 우선).

1. **TDD — 고전파(classicist)로 진행한다.**
   - 순서: 실패하는 테스트 먼저 → 올바른 이유로 실패하는지 확인 → 최소 구현 → 리팩터.
   - 상태·결과 기반 검증을 기본으로 하고, 실제 협력 객체를 그대로 쓴다. mock/stub은 프로세스 경계(외부 API·DB·시계·랜덤·파일시스템)에만 허용. 호출 여부·횟수 assert(상호작용 검증)는 그 자체가 요구사항일 때만.
   - **DB 경계**: 기본은 가짜(fake/인메모리) 허용 — 테스트 속도(빨강→초록 리듬)를 지킨다. 단 **프로젝트에 테스트 DB 환경이 이미 존재하면**(docker-compose 테스트 서비스·테스트용 접속 설정 등 객관 조건) 쿼리를 담는 **저장소 계층에 한해** 진짜 DB 통합 테스트를 우선한다.
2. **조회(SELECT) 쿼리는 성능을 검토하고 구현한다.**
   - 구현 시점에 N+1 여부 · 인덱스 사용(실행 계획 EXPLAIN) · 필요한 컬럼만 선택 · 페이지네이션/LIMIT · 대량 스캔 회피를 확인하고, **확인 근거(실행 계획 요지)를 보고에 남긴다.** 가짜 DB로 테스트하는 경우 이 확인이 성능 검증의 유일한 통로이므로 생략 금지.
3. **위임 시 주입 (MANDATORY)**: CLAUDE.md를 받지 않는 외부 엔진 워커(codex `task --fresh`, gemini/antigravity/cursor CLI 등)에 구현을 위임할 때는 위 1·2의 요지를 위임 프롬프트에 명문 포함한다(`50-critic.md` 「선제 환경 컨텍스트 주입」 동형). Claude 서브에이전트는 CLAUDE.md 상속으로 자동 전달되므로 별도 주입 불요(2026-08-20 haiku 프로브 실측).

### 폴더 구성 인덱스 (OMC 실행 키워드 단위)

| 파일 | 적용 대상 | 주요 내용 |
|---|---|---|
| `00-overrides.md` | 전체 | 헤더, CRITICAL 블록, 적용 체크리스트, 프로토콜 준수 원칙, **질문 방식 전역 규칙(3단 구조·AskUserQuestion 금지·실행 게이트 예외·실행 모드 진행 중 비용/진척/완주여부 재확인 금지)**, **공통 구현 원칙 전역(TDD 고전파·DB 경계·조회 쿼리 성능·위임 시 주입)** |
| `10-autopilot.md` | autopilot | Phase 0/1/3/4 설정, **3-stage gate(Stage 0 → 1 → 2)** 16-reviewer 호출 체크리스트 (Stage 0 3개 + Stage 1 4개 + Stage 2 9개 — 라운드 카운터 +1 은 Stage 0 (재)시작, 코드 수정 후 다음 호출은 항상 Stage 0 부터), **scope 분류·크리티컬 임계선(2열 표)·가드 A(실측 수집 해제 절차 포함)·deferred 기록·Phase 4 선제 리뷰 컨텍스트(NOTE(review-context) 주석)·protocol exception 기록 규격**, **Phase 0/1 Critic finding scope 분류(30-ralplan 준용)**, **대상 축 「다 고치면 0이 되나」 5분류(산출물·검증 장치 공통 — 2026-08-18)·Stage 0·1 모두 REJECT 슬롯만 부분 재실행+확인 1회·주석/문서 전용 수정 단축(Stage 0·1·2 공통)·**테스트 전용 수정 단축(2026-08-20 — 프로덕션 0줄이면 Stage 0·확인 실행 생략, 최종 전체 재시작으로 보증)**·풀 게이트 웨이브당 1회**, **pauseAfterExpansion/Planning SDD 흐름 조건부 자동 스킵 + Plugin Reviewer Deadlock 근거 원문 인용 시 자동 dismiss(이번 실행 한정 — 영구 예외 등록은 종료 보고에서 제안, 2026-08-20)**, **diff 불변 슬롯 재사용(풀 재시작 한정, 판정 재료 해시 H 대조)·Stage 1/2 호출 전 경로 프리플라이트·deferred 환경 스냅샷(compaction 후 경로 재탐색 생략)+라운드 기록(웨이브당 시각·H 1줄, 파일 무조건 생성)·라운드 종료 누적 진행표 선제 출력 (2026-08-21)** + **웨이브 회수(각 Stage audit 후 팀메이트 TaskStop·audit 표 회수 행·종료 시 더미 TaskStop 전수 검증 — canonical=40-common reap)·Phase 5 PR 생성 전 diff설명 스킬 선행(--mark 단독 명령·SKILL.md 경로 폴백·PR 직전 체크 2항) (2026-08-21)** |
| `20-ralph.md` | ralph | maxIterations, defaultCritic, maxStaleRetries, postDeslopAgents |
| `21-team-ralph.md` | team ralph | maxFixLoops, 루프 회차 검증, **team ralph 종료 후 autopilot Phase 3/4 자동 체인** (outerCycleLimit=10, 검증 범위 분리 강제) |
| `30-ralplan.md` | ralplan | deliberate, interactive, artifactName=-plan.md, **scope 고정(Follow-ups 기록·루프 트리거 예외)**, Critic Deadlock(50-critic 공통 준용 + ralplan 특이사항) |
| `40-common-loop.md` | autopilot/ralph/team ralph/ralplan (공통) | 공통 수정 후 루프 + 사소 수정 예외 규칙(**애매 4종은 질문 없이 예외 미적용→전체 루프, 2026-08-20**) + **공통 작업 원칙(scope 고정+최소 변경+**자매 파일·미러 레포 대칭** — canonical, **Phase 4 포함 전 구간**(`54-phase4-registry.md`와 정합. scope 고정·최소 변경만 "Phase 4는 자체 규칙 우선"이고 자매 대칭은 **면제 대상이 아니다** — 2026-08-14 실사례: 이 문면을 면제로 읽어 Phase 4 위임 프롬프트에 9라운드 내내 자매 대조를 넣지 않았고, MSF만 고치고 RFM을 빠뜨린 결함이 라운드 4·6·9·10에 반복 발생))** + **서브에이전트 산출물 회수 규율(canonical — 3단 사다리·회수 요청에 새 과제 금지, Phase 4 포함 전 구간)** + **검증되지 않은 단언 자체 검증 ⓐ~ⓔ(ⓔ=바꾼 사실의 잔존 grep, 2026-08-18)** + **리뷰어 간 실측 충돌(canonical — 상반된 실측은 오케스트레이터가 직접 재현해 판정, Phase 4 포함 전 구간)** + **§4 구현 스타일 포인터(TDD 고전파·조회 쿼리 성능 — 정의는 00-overrides 「공통 구현 원칙 — 전역」 SSOT, 위임 프롬프트 명문 주입)** + **선제 이중 채널(위임 프롬프트에 리포트 파일 경로+본문 전달 상시 지시·사다리 0단 파일 확인·발사 전 4항 자체 검사 — '파일 쓰지 마라' 구문구 모순 해소, 2026-08-21)** + **팀메이트·백그라운드 태스크 회수(reap) canonical(웨이브 종합 직후 전원 TaskStop·더미 TaskStop 전수 검증·audit 회수 행, 2026-08-21)** |
| `50-critic.md` | autopilot/ralph/team ralph/ralplan (공통) | 공통 Critic 실행 규칙 + codex:critic 호출 패턴 (OMC custom) + **선제 환경 컨텍스트 주입(deferred 세션 간 승계 포함)** + **최소 변경 원칙 상시 주입(Phase 4 예외)** + **공통 Critic Deadlock 조기 감지(canonical — ⓐⓑ 근거 원문 인용 시 자동 dismiss·ⓒ/인용 불가만 사용자 에스컬레이션(2026-08-20), Phase 4 제외)** + **Finding 발산 조기 감지(리뷰어 축·대상 축 3라운드 / 라운드 축 4라운드 — 충족 시 자동 옵션 B + 기본 정지 기준(질문 없음·보고만, 2026-08-20) + **충족 라운드 즉시 이월·통과 집행(확인 라운드 개설 금지)**, 2회째부터 누적 보고)** + **상시 표준 항목(코드 실행 예상 리뷰어에 codex 샌드박스 EPERM=환경 아티팩트 1줄 상시 주입, 2026-08-21)** |
| `51-codex-reviews.md` | autopilot Phase 4 | codex:review + codex:adversarial-review (plugin native, scope 선택 규칙, anti-patterns) |
| `52-codex-rescue.md` | rescue 사용 시 | codex:rescue 호출 우선순위 |
| `53-ocr-review.md` | autopilot Phase 4 Stage 1 | ocr:delegate-review Task 래퍼 호출 패턴 (OMC custom, delegation mode — delegate-review.md 전문 주입, 게이트 매핑=**원판정** 주석, anti-patterns). **래퍼 allowlist = `ocr-delegate-reviewer` 단 하나** (정의: `~/.claude/agents/ocr-delegate-reviewer.md`, 도구 레벨 Write/Edit 차단) |
| `54-phase4-registry.md` | autopilot Phase 4 (Stage 0+1+2) | **Phase 4 리뷰어 16슬롯 레지스트리 — canonical SSOT.** 슬롯별 호출 방식·등급체계·scope 안/밖 차단선·deferred 기여·원판정=최종 여부·프롬프트 주입 가능 여부·정체 규칙 대상을 한 표로. **파생 규칙(가드 A · 반복형 정체 · 발산형 정체 · deferred 대상)은 명단이 아니라 표의 「속성 컬럼」에서 도출**한다 — 이름을 박아 두면 신규 reviewer가 규칙에서 누락된다. 완결성 자기검사(「정체 규칙」이 빈 행 금지) + 슬롯별 특례(code-simplifier 심사범위·pr-review-toolkit 매핑·ocr allowlist·codex 호출 제약·Stage 0 계열) |
| `55-stage0-gate.md` | autopilot Phase 4 Stage 0 | **Stage 0 정합 선행 게이트 3슬롯의 호출 형태 SSOT** — A `intent-scope-reviewer`(Claude Task + Codex `task --fresh` **read-only** 양 엔진 병렬 필수, 합의 판정) · B `change-impact-reviewer`(Claude 단독). 입력 조립 7항(기준 문서 **전문**·diff·제약·이월·**자매 축 선언**·옛 값·Linear) · 마커별 allowlist(`[stage0:intent-scope]`→`intent-scope-reviewer`, `[stage0:change-impact]`→`change-impact-reviewer`, 훅 강제) · override 3줄 · `INPUT_MISSING` 처리 · `requires_human_verification` → Stage 2 verifier 인계 · Stage 1 codex:critic 교차 확인(기준 문서 전문 필수화) · anti-patterns. 에이전트 정의: `~/.claude/agents/intent-scope-reviewer.md`·`change-impact-reviewer.md`(사용자 소유, Write/Edit 도구 제외) + **회수 절에 선제 이중 채널 포인터(A-Codex read-only 예외, 2026-08-21)** |
| `60-fallback.md` | 전체 | config 미정의 시 행동 |
| `70-ultraqa.md` | ultraqa | maxCycles |
| `71-deep-interview.md` | deepInterview | ambiguityThreshold, maxRounds, artifactName=-spec.md 등, **scope 고정(topology 잠금·승격 규칙)**, **질문 출력 3단 구조(canonical — 전역 질문 방식 규칙의 원본 정의)**, **재설명 요청 대응 형식(2026-08-20 — 실데이터 예시 의무·용어 풀이표·동일 추상 수준 반복 금지)**, 라운드 방향 자의 확정 금지 |
| `72-deep-dive.md` | deepDive | ambiguityThreshold, defaultTraceLanes |
| `73-research.md` | research | maxIterations, maxConcurrentScientists, defaultTier 등 |
| `80-sdd-workflow.md` | deep-interview · ralplan (착수 흐름) | **SDD 착수 흐름 SSOT** — `deep-interview → -spec.md → ralplan(-plan.md, 플레이북 Gate 1 Spec Review + PLAN 검토 겸함 — 1라운드 양 Critic에 Gate 1 체크 항목 주입) → Linear 이슈 발급 → 브랜치 생성·푸시 → spec·plan 각각 커밋·브랜치 푸시(References 브랜치 URL, 머지 시 main 교체) → 구현`. 별도 Spec Review 단계 개설 금지(2026-08-19 STAT-586 실사례). 훅이 두 키워드 + `PR`/`머지`(머지 직후 링크 교체 체크 ③)에 주입 |

**상호 참조**: 실행 스킬 파일(20/21/30)은 공통 규칙(`40-common-loop.md`, `50-critic.md`)을 명시 참조한다. `71-deep-interview.md`·`30-ralplan.md`는 착수 흐름을 `80-sdd-workflow.md`로 가리킨다(복제 금지). `60-fallback.md`는 개별 파일이 직접 참조하지 않으며 훅 COMMON 주입으로 공급된다 (훅이 60을 주입하지 않는 키워드(70~73)에서는 필요 시 Read). autopilot Phase 4는 추가로 `51-codex-reviews.md`(codex:review/adversarial-review 호출) · `53-ocr-review.md`(ocr:delegate-review Task 래퍼 호출) · **`54-phase4-registry.md`(리뷰어 16슬롯 레지스트리 — scope 임계선과 정체 규칙 대상이 여기서 도출되므로 Phase 4에서 누락 불가)** · **`55-stage0-gate.md`(Stage 0 3슬롯 호출 형태 — Stage 0 가 매 라운드 첫 호출이므로 누락 불가)**도 참조.

**SSOT 배치 원칙 (MANDATORY)**: 같은 사실을 두 파일에 적지 않는다 — 복제본이 생기면 한쪽만 갱신돼 규칙이 조용히 어긋난다. 정의를 한 파일에 두고, 가리키는 쪽은 **"~가 SSOT다 / 여기 복제하지 말 것"**을 명시한다.
