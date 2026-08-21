## OMC Skill Config — ralplan

**ralplan:** deliberate=true, interactive=false, artifactName=-plan.md, maxIterations=20
- **착수 흐름 속 위치**: `80-sdd-workflow.md` 참조 — ralplan은 deep-interview `-spec.md` 직후에 돌며 **플레이북 Gate 1(Spec Review)과 PLAN 검토를 한 번에 겸한다**(1라운드 양 Critic에 Gate 1 체크 항목 주입 필수, 별도 Spec Review 단계 금지, 이슈 발급·브랜치·푸시는 ralplan 뒤). 여기 복제하지 말 것.
- Critic: `50-critic.md`의 **공통 Critic 실행 규칙** 참조.
- **MANDATORY — 수정 후 루프**: `40-common-loop.md`의 **공통 — 수정 후 루프 규칙** 참조.
- **MANDATORY — Re-review loop 한도 오버라이드**: SKILL.md(`~/.claude/plugins/cache/omc/oh-my-claudecode/<최신 버전>/skill-bodies/ralplan/SKILL.md` — 버전 디렉토리는 glob으로 탐색해 최신 선택. marketplaces 사본은 버전 드리프트 위험으로 사용 금지)에 하드코딩된 "max 5 iterations" 문구를 **본 파일 상단 maxIterations 값으로 오버라이드**할 것 (라인 위치는 omc 자동 업그레이드로 변동되므로 문구 기준으로 찾는다). Critic이 `APPROVE`를 반환하지 않은 채 maxIterations회에 도달하면 SKILL.md step 5f에 따라 best version을 사용자에게 제시 후 정지(자동 통과 처리 금지).
- **MANDATORY — artifact 저장 시 자체 검증**: plan 파일 저장 직전 다음 출력.
  - [ ] artifactName suffix `-plan.md` 적용됐는가? (저장 파일명: `<name>-plan.md`)
  - [ ] interactive=false 준수: 사용자 확인 지점 없이 Planner→Architect→Critic 자동 루프로 진행하고 최종 plan 출력 후 정지했는가? (실행 자동 invoke 금지)
  - [ ] 현재 Re-review 회차 #N (1 ≤ N ≤ maxIterations)
  - [ ] maxIterations회 도달 시: 자동 종료/통과가 아니라 사용자 보고 후 정지했는가?

---

### scope 고정 (MANDATORY)

**scope 기준**: PRD 초안의 목표/요구사항 섹션 (계획을 만드는 단계이므로 사용자 원 요청이 SSOT).

- Critic의 non-APPROVE 사유가 scope 밖이면 계획을 확장하지 말고 ADR **Follow-ups**에 기록하고 게이트에 반영하지 않는다.
  - ⚠️ **기록으로 끝내지 말 것 — 다음 라운드 Critic 프롬프트에 다시 주입한다** (`50-critic.md` 「선제 환경 컨텍스트 주입」 수집 소스 **3번**). codex critic 은 `task --fresh` 라 라운드 간 기억이 0이므로, 주입하지 않으면 **이미 판단이 끝난 항목을 매 라운드 다시 발견**한다. 2026-08-05 STAT-549 ralplan 에서 동일 finding 10회 반복으로 15라운드 한도를 소진한 사고가 정확히 이 경로였다 — 그때 대응은 탐지(Deadlock 에스컬레이션)였고 예방은 없었다.
- Critic 차단 등급: scope 안 finding은 기존 판정 로직 그대로 / scope 밖은 `CRITICAL`/`MAJOR`만 차단, 그 미만은 Follow-ups 기록 (`10-autopilot.md` finding 분류 규칙과 동일 원리).
- **차단 대상 0건이면 해당 Critic 판정을 APPROVE로 처리**한다 (원판정이 ITERATE/REJECT여도). SKILL.md step 5의 재실행 트리거는 이 최종판정 기준으로 판단한다.
- **Follow-ups 기록 추가는 계획 본문(결정·설계) 변경이 아니므로 `40-common-loop.md`의 수정 후 루프 트리거로 간주하지 않는다.** 단 Follow-ups 외 본문이 1줄이라도 함께 바뀌면 루프 대상.
- **"Alternatives considered"는 현재 scope를 달성하는 대안으로 한정.** scope를 넓히는 안은 대안이 아니라 Follow-ups.
- 계획 수립 시 **원본 코드 최대한 보존 + 가장 단순하고 효과적인 방법 우선**. 동등 효과면 변경량이 적은 안을 채택하고 근거를 ADR `Why chosen`에 기재.

**MANDATORY — Critic 판정 회수 후 자체 검증 체크리스트 출력** (양 Critic 각각):
- [ ] scope 기준 문서: __________ (PRD 목표/요구사항 섹션)
- [ ] OMC critic finding: 총 __건 → scope 안 __ / 밖 __ (밖 중 CRITICAL__ MAJOR__)
- [ ] codex critic finding: 총 __건 → scope 안 __ / 밖 __ (밖 중 CRITICAL__ MAJOR__)
- [ ] 양 Critic 각각 차단 대상 = (scope 안 기존 로직 차단분) + (scope 밖 CRITICAL/MAJOR) = __ / __건
- [ ] 양 Critic 모두 차단 대상 0건인가? (둘 다 Y → consensus / N → 루프 계속)
- [ ] scope 밖 비차단 항목 전건을 ADR Follow-ups에 기록했는가? (기록 없이 통과 금지)
- [ ] scope 밖 판정이 전건 PRD 대조인가? (추측 판정 0건)

**MANDATORY — 최종 plan 출력 직전 자체 검증** (위 artifact 체크리스트에 추가):
- [ ] ADR Follow-ups에 scope 밖 항목 전건 기록됐는가? (0건이면 "없음" 명기)
- [ ] Alternatives considered에 scope를 넓히는 안이 섞이지 않았는가?
- [ ] 동등 효과 대안 중 최소 변경안을 택했고 근거가 Why chosen에 있는가?

**잘못된 진행 금지 (anti-patterns, MANDATORY)**:
- ❌ Critic이 "이것도 넣어야 한다"고 해서 무조건 계획 확장 → scope 대조 후 Follow-ups 판단 먼저
- ❌ scope 밖 항목을 Follow-ups 기록 없이 무시 → 정보 소실. 기록 필수.
- ❌ Alternatives를 채우려고 scope 밖 방안을 대안으로 나열 → Follow-ups로
- ❌ 더 견고하다는 이유로 변경량 큰 안을 기본 채택 → 동등 효과면 최소 변경안 우선
- ❌ Follow-ups 1줄 추가를 "수정 발생"으로 보고 전체 루프 재실행 → 본 예외 적용

---

### Critic Deadlock 조기 감지 (MANDATORY — `50-critic.md` 공통 규칙 준용)

**규칙 전문은 `50-critic.md`의 "Critic Deadlock 조기 감지 (공통 — canonical)" 절을 따른다** (4조건 정의·체크리스트·보고 형식·옵션 A 처리·anti-patterns 전부). 요지: 동일 Critic이 연속 2라운드 이상 의미상 동일 finding으로 비-APPROVE를 유지하고, 타 리뷰어는 안정 승인이며, finding이 ⓐ환경 오인/ⓑscope 밖이고 근거 원문 인용 가능하면 → **자동 dismiss(기록·조정 이력 주입 포함, 2026-08-20 개정)**, ⓒ정책 이견 또는 인용 불가면 → **사용자 에스컬레이션 후 정지**.

**ralplan 특이사항**:
- 옵션 C(루프 종료)의 산출물 = 현재 버전을 **best version plan**으로 제시 (SKILL.md step 5f와 동일 형식).
- 본 규칙은 maxIterations 한도와 **독립 동작** — 한도 도달 전이라도 조건 충족 시 즉시 발동한다.
- scope 판정(ⓑ)의 기준 문서 = 본 파일 "scope 고정" 절의 PRD 기준과 동일.
