## OMC Skill Config — team ralph

**team ralph:** maxFixLoops=10, outerCycleLimit=10 (나머지는 `20-ralph.md` defaults 상속)
- Critic: `50-critic.md`의 **공통 Critic 실행 규칙** 참조.
- **MANDATORY — team-fix 후 루프**: `40-common-loop.md`의 **공통 — 수정 후 루프 규칙** 참조 (team-fix → team-exec → team-verify 전체 루프 재실행).
- **MANDATORY — team-exec/team-fix 수정 작업 시 `40-common-loop.md`의 "공통 작업 원칙"(scope 고정 + 최소 변경) 적용.** scope 기준 = 사용자 원 요청 + plan.
- **MANDATORY — 루프 회차별 자체 검증**: 매 루프 회차 시작 시 다음 출력.
  - [ ] 현재 회차 #N (1 ≤ N ≤ maxFixLoops=10)
  - [ ] team-fix → team-exec → team-verify 3단계 모두 재실행 대상에 포함됐는가? (단계 생략 금지)
  - [ ] 직전 verify 실패 사유 명시

---

### team ralph 종료 후 autopilot 검증 체인 (MANDATORY)

**적용 조건**:
- team-verify가 **PASS로 종료**한 경우에만 자동 실행한다.
- team ralph가 **maxFixLoops 한도 도달로 실패 종료**한 경우 본 체인 **스킵**하고 사용자 보고 후 정지.
- opt-in 플래그 없음 — team-verify PASS 시 **항상 자동 실행**.

**체인 순서 (MANDATORY)**:

```
team-verify PASS
       ↓
autopilot Phase 3 (debugger + ultraqa)
       ↓ pass
autopilot Phase 4 (Stage 1 4개: codex 3 + ocr 1 → Stage 2 9)
       ↓ 전원 APPROVE
   최종 종료 (성공)

* Phase 3 또는 Phase 4 REJECT → team ralph의 team-fix로 복귀 (외곽 사이클 +1)
* 외곽 사이클 최대 10회 (outerCycleLimit=10), 초과 시 사용자 보고 후 정지
```

**Phase 3 구성**: `10-autopilot.md`의 Phase 3 규칙 그대로 차용.
- phase3Agents=[debugger]
- ultraqa(maxCycles는 `70-ultraqa.md` 값) 항상 실행
- Phase 3 실행 절차/카운터 규칙은 `10-autopilot.md` Phase 3 섹션과 `70-ultraqa.md` 그대로 따름

**Phase 4 구성**: `10-autopilot.md`의 Phase 4 3-stage gate(Stage 0 → 1 → 2) 규칙 그대로 차용 — Stage 0 호출 형태는 `55-stage0-gate.md`.
- Stage 1: codex:review, codex:adversarial-review, codex:critic, ocr:delegate-review (단일 메시지 병렬 — codex 3건 Bash + ocr 1건 Task 래퍼, `53-ocr-review.md` 참조)
- Stage 2: 7 OMC subagent + 2 Skill 빌트인/공식 (단일 메시지 병렬)
- maxValidationRounds·maxPartialRerunRounds는 `10-autopilot.md` 값 그대로 (**1 시도=1라운드, 리셋 없음** / Stage 2 내부 부분 재실행 제한)
- Phase 4 내부 REJECT 처리(Stage 0·1·2 모두 **REJECT한 슬롯만 부분 재실행** → Stage 0·1 은 전원 통과 시 확인 실행 1회 / Stage 1 REJECT 후 수정은 Stage 0 부터 / Stage 2 는 전원 통과 시 Stage 0부터 재시작, 카운터 +1 은 Stage 0 (재)시작·리셋 없음 · 주석/문서 전용 수정은 단독 재검증 단축)는 `10-autopilot.md` 가 SSOT — 여기 복제하지 말 것

**MANDATORY — Phase 3/4 REJECT 시 복귀 규칙**:
- **Phase 3 REJECT (debugger fail 또는 ultraqa maxCycles 도달)** → team ralph의 team-fix로 복귀. Phase 4 진입 금지.
- **Phase 4 maxValidationRounds 도달로 통과 실패** → team ralph의 team-fix로 복귀. Phase 4 자체 한도와 외곽 사이클 한도는 별개 카운트.
- **Phase 4 maxPartialRerunRounds 도달 (P=15 초과)** → team ralph의 team-fix로 복귀 (사용자 보고 포함, 외곽 사이클 +1). autopilot 단독 실행의 "사용자 보고 후 정지"와 달리, team-ralph 체인 내에서는 team-fix 복귀로 처리.
- 복귀 시 team-fix → team-exec → team-verify **3단계 전체 사이클 재실행** (단계 생략 금지).

**MANDATORY — 내부 카운터 fresh start 규칙**:
- team ralph maxFixLoops=10 → 외곽 사이클 진입마다 fresh start (0으로 리셋)
- Phase 3 ultraqa maxCycles → Phase 3 재진입마다 fresh start
- Phase 4 maxValidationRounds → **외곽 사이클당** Phase 4 재진입 시 fresh start (= 새 Phase 4 실행은 N=0부터). 단 **한 번의 Phase 4 실행 내부**에서는 `10-autopilot.md`의 '리셋 없음'이 적용됨 — 두 규칙은 적용 범위(scope)가 다름 (외곽 재진입 시 초기화 ≠ 내부 시도 누적 중 초기화)
- 카운터 합산 금지. 단계별 독립 카운트.

**MANDATORY — 외곽 사이클 한도 (outerCycleLimit=10)**:
- 외곽 사이클 1회 = team ralph 루프(PASS) → Phase 3 → Phase 4 → (REJECT 시) team-fix 복귀까지 1턴
- 최대 10회. 초과 시 **사용자 보고 후 정지** (자동 통과/재시도 금지).
- 매 외곽 사이클 진입 시 회차 번호 user-facing 텍스트에 출력: 예) `Outer Cycle 3/10`.

**MANDATORY — 외곽 사이클 진입 시 자체 검증 체크리스트 출력**: 매 단계 진입 직전(team ralph 재시작, Phase 3 진입, Phase 4 진입 시 각각) 다음을 user-facing 텍스트에 출력할 것. 누락 시 프로토콜 위반.
- [ ] 직전 단계 결과: [team-verify pass / Phase 3 pass / Phase 3 reject / Phase 4 reject (maxValidationRounds 또는 maxPartialRerunRounds 도달) / team ralph maxFixLoops 도달로 실패 종료]
- [ ] 외곽 사이클 회차 #M (1 ≤ M ≤ outerCycleLimit=10)
- [ ] M=10 도달 직전인가? (Y → 다음 REJECT 시 자동 재시도 금지, 사용자 보고 후 정지)
- [ ] 다음 행동 명시: [Phase 3 진입 / Phase 4 진입 / team-fix 복귀 (외곽 사이클 +1) / 최종 종료 (성공) / 사용자 보고 후 정지]
- [ ] 진입할 단계의 내부 카운터가 fresh start로 리셋됐는가? (team ralph maxFixLoops / Phase 3 ultraqa maxCycles / Phase 4 maxValidationRounds)
- [ ] team ralph가 maxFixLoops 도달로 실패 종료한 케이스인가? (Y → 체인 스킵, 사용자 보고 후 정지)

**MANDATORY — 검증 범위 분리 (강제, MANDATORY)**:

team-verify와 Phase 3 ultraqa는 **검증 범위가 겹치면 안 된다**. 동일 검증 케이스를 두 단계에서 중복 실행 시 결과 무효 처리하고 범위 재조정 후 재실행.

- **team-verify 범위 (결정적 정적 검증)**: 단위 테스트, 빌드 통과, 타입체크, lint, 정적 분석
- **Phase 3 ultraqa 범위 (동적 통합 검증)**: E2E, 회귀, integration, 사용자 시나리오, 부하/성능, 보안 동적 검증
- 두 범위는 **disjoint(서로소)** 여야 한다. 한 케이스를 두 단계 모두에 넣지 말 것.

**MANDATORY — 범위 분리 자체 검증 체크리스트 출력**: team-verify 시작 직전 + Phase 3 ultraqa 시작 직전 각각 다음 출력.
- [ ] team-verify에서 실행한/실행할 테스트 카테고리 명시 (예: `pytest tests/unit`, `npm run build`, `mypy`, `eslint`)
- [ ] Phase 3 ultraqa에서 실행할 테스트 카테고리 명시 (예: `pytest tests/e2e`, `playwright`, `integration suite`)
- [ ] 두 카테고리가 disjoint(서로소)인가? (겹친다면 중복 카테고리 명시 + 어느 단계로 통합할지 결정)
- [ ] 겹치는 케이스를 다른 단계에서 제외 처리했는가? (Y → 진행 / N → 범위 재조정 후 재실행)
- [ ] 범위 분리 위반 발견 시 결과 무효 처리하고 재실행 mandatory.
