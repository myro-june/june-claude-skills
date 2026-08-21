## OMC Skill Config — SDD 착수 흐름 (deep-interview → ralplan → 이슈 → 브랜치 → 푸시)

**적용 대상**: Delivery 작업(feat 작업 이슈·small-feat·fix)의 스펙~플랜~착수 구간. 플레이북 `docs/playbook/product-dev/07-workflow.md` Gate 1·PLAN 검토, `04-docs-and-ssot.md` 선작성 원칙의 **실행 형태 SSOT** (플레이북은 규칙을, 본 파일은 세션이 실제로 밟는 순서를 정한다 — 둘이 어긋나면 본 파일을 고치지 말고 플레이북과 같이 맞춘다).

**주입 경로**: 훅 `omc-config-inject.py`가 `deep-interview`·`ralplan` 키워드 **및 `PR`·`pull request`·`머지`·`merge`**(체크리스트 ③ 시점)에서 본 파일을 자동 주입한다. 주입 블록이 없으면(compaction·세션 재개) `00-overrides.md` 2차 백스톱에 따라 Read.

---

### 순서 (MANDATORY — 고정, 단계 삽입·순서 변경 금지)

1. **deep-interview** → `-spec.md` 로컬 작성 (`71-deep-interview.md`). 이슈 ID가 없으므로 로컬 임시 위치에 둔다.
2. **ralplan** → `-plan.md` 로컬 작성 (`30-ralplan.md`).
   - **ralplan이 플레이북 Gate 1(Spec Review)과 PLAN 검토를 한 번에 겸한다. 별도 Spec Review 단계 개설 금지.**
   - 1라운드 양 Critic(OMC + codex) 프롬프트의 리뷰 대상 앞에 Gate 1 체크 항목(`07-workflow.md` "Gate 1 — Spec Review" 절 — 요구사항 테스트 가능성 · 인수 조건 개수 · 파트별 완전성(API 스키마/FE 의존·Mock/Design 상태/Scraping 수집·재시도·데이터 계약) · 인수 조건↔TC 1:1 매핑)을 **"스펙 완성도 사전 점검"** 블록으로 주입한다. 스펙 결함은 plan 결함과 같은 등급 체계로 판정한다.
   - Gate 1 증거 = ralplan 결과(plan 파일 URL + 양 Critic 최종 판정 요약). PLAN 검토 증거와 **동일 링크**.
3. **Linear 이슈 발급** → ID 확정. 본문 4단계 체크리스트 1(SDD 스펙)·2(PLAN 검토)를 체크하되 증거 링크는 5단계 URL 확보 후 채운다.
4. **브랜치 생성 + 리모트 푸시** (`feat/STAT-N-…`, 플레이북 브랜치 규칙).
5. **md 각각 커밋·푸시** — `docs/tickets/STAT-N/`에 spec 1커밋 → plan 1커밋, 브랜치에 푸시. References에 **브랜치 blob URL**(`blob/feat/STAT-N-…/docs/...`) 즉시 추가 + 4단계 체크리스트 증거 링크 채움.
   - 구현 PR 머지 시 References·체크리스트의 `blob/<브랜치>/` → `blob/main/` 교체 (머지 체크리스트 항목 — 브랜치 삭제 후 404 방지).
6. **구현** (이후는 `10-autopilot.md` 등 기존 흐름).

---

### 자체 검증 체크리스트 ① (MANDATORY — 2단계 ralplan **1라운드 양 Critic 호출 직전** 출력)

- [ ] 양 Critic 프롬프트의 리뷰 대상 앞에 **"스펙 완성도 사전 점검"(Gate 1 체크 항목) 블록**이 들어 있는가 (OMC critic Task · codex critic Bash 둘 다)
- [ ] 리뷰 대상에 `-spec.md` 전문과 `-plan.md` 전문이 **둘 다** 포함됐는가 (plan만 보내면 Gate 1 미수행)
- [ ] `50-critic.md` 호출 전 체크리스트(동일 메시지·critic.md 전문·환경 컨텍스트·최소 변경 1줄)도 함께 통과했는가

### 자체 검증 체크리스트 ② (MANDATORY — 3단계 이슈 발급 직전 출력)

- [ ] `-spec.md`·`-plan.md` 둘 다 로컬에 존재하는가
- [ ] ralplan consensus 도달(= Gate 1 + PLAN 검토 증거 확보)했는가
- [ ] Gate 1 체크 항목을 ralplan 1라운드 양 Critic 프롬프트에 주입했는가
- [ ] 별도 Spec Review 단계를 열지 않았는가
- [ ] (5단계 직후) References·체크리스트 링크가 브랜치 URL이고, 머지 시 main 교체 항목을 남겼는가

### 자체 검증 체크리스트 ③ (MANDATORY — 6단계 이후, 구현 PR **머지 직후** 출력 — 머지를 수행한 세션 책임. 항목 정의 SSOT = 플레이북 `07-workflow.md` §12 "머지 직후 체크리스트")

- [ ] ① Linear References·4단계 체크리스트 증거 링크 **+ PR description의 References**의 `blob/<브랜치>/` → `blob/main/` 전건 교체했는가 (이슈 본문 grep으로 `blob/<브랜치>` 잔존 0건, 정합 안 맞는 링크는 갱신·제거)
- [ ] ① 교체 후 main 링크가 실제로 열리는가 (머지 커밋에 md가 포함됐는지 — squash 머지 파일 목록 확인)
- [ ] ② 이슈 본문 브랜치 줄에 머지 완료 1줄(날짜·PR 번호·squash SHA)을 기록했는가 (구현이 본문 인수 조건·스펙과 어긋나 있으면 08 변경 대응)
- [ ] ③ 이번 변경이 바꾼 사실을 기록한 다른 SSOT 문서(데이터 카탈로그·정책·README 등)를 갱신했는가 (사후 문서 PR은 이슈 상태를 바꾸지 않음 — In Progress 오처리 시 수동 복구)
- [ ] ④ 관련 이슈를 정리했는가 — 팔로업 이슈화(`→ STAT-XXX` 링크)·Blocked 해제·부모 Issue/파트 허브 롤업·hotfix `-report.md` 24h 시작
- [ ] ⑤ 브랜치 삭제는 ① 교체와 같은 호흡으로 처리했는가 (`--delete-branch` 동시 삭제 시 교체를 즉시 수행)
- [ ] ⑥ (CI 미가동 기간) 머지 직후 로컬 CI를 실행해 결과를 기록했는가 (07 Gate 3 한시 조항 — PR 생성 직후에도 동일: CI 미가동 확인 즉시 로컬 CI 자동 실행)

---

### 잘못된 진행 금지 (anti-patterns, MANDATORY)

- ❌ 스펙 푸시 후 ralplan 전에 Spec Review(양 Critic)를 **별도 실행** — 2026-08-19 STAT-586 실사례 (플레이북 구 문면 "Spec Review 통과 후 PLAN 검토"·"plan은 선작성 대상 아님"을 문자 그대로 읽은 결과. 개정 후 문면이 SSOT, 실제 선례 STAT-572도 ralplan 1회로 두 게이트를 함께 채웠다)
- ❌ plan 작성을 이슈 발급 뒤로 미룸
- ❌ spec·plan md를 main에 직접 푸시 (브랜치 경유 → 구현 PR로 main 진입)
- ❌ References에 main URL을 미리 적어 머지 전 404 방치
- ❌ Gate 1 체크 항목 주입 없이 "ralplan이 겸한다"고만 기재 — 이름만 겸함. 주입 없으면 Gate 1 미수행
