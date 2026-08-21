## OMC Skill Config — codex:review / codex:adversarial-review (plugin native)

`codex:review`와 `codex:adversarial-review`는 **codex-plugin-cc의 native slash command**이다. codex-plugin-cc는 두 명령을 모두 `disable-model-invocation: true`로 정의했고 subagent로 노출하지 않으므로, **Bash 직접 호출만 가능**.

(`codex:critic`은 별개 — OMC custom 호출 패턴, `50-critic.md` 참조)

### 호출 매트릭스 (MANDATORY)

| 호출 | 방식 | 출처 |
|---|---|---|
| `codex:review` | **Direct codex CLI 호출 (companion wrapper 우회)**: `codex review --base <ref>` (run_in_background=true 권장). `--base <ref>`는 아래 "scope 선택 규칙" 참조. **Skill 도구 호출 불가** (`disable-model-invocation: true`). **Task subagent 호출 불가**. | codex-plugin-cc `commands/review.md` |
| `codex:adversarial-review` | **Bash 직접 호출만 허용**: `node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" adversarial-review "<args> [focus]"` (run_in_background=true 권장). adversarial prompt는 codex 플러그인 내부 `prompts/adversarial-review.md`에 번들 내장 (사용자 주입 불요). focus text 인자 추가 가능. `<args>`는 **free-text prompt** (companion이 자체적으로 git diff 비교 수행, raw CLI flag 형식 아님 — `"--scope branch --base main"` 같은 문자열도 prompt로 무난히 수용됨). **Skill 도구 호출 불가**. **Task subagent 호출 불가**. | codex-plugin-cc `commands/adversarial-review.md` |

**MANDATORY 호출 원칙**:
- 둘 다 plugin native reviewer 사용 — `task` subcommand로 .md 파일 주입 시 잘못된 호출.
- 장시간 실행 대비 `run_in_background=true` 또는 `--background` 플래그 사용.
- 두 호출은 단일 메시지에서 병렬 호출 가능 (Phase 4 16-reviewer 3-stage gate — Stage 0 3개 → Stage 1 4개 → Stage 2 9개, Stage 별 단일 메시지 mandate. 이 두 호출은 Stage 1 메시지에 속하며 Stage 0 호출(`55-stage0-gate.md`)과 같은 메시지에 섞지 않는다).

---

### review 대상 flag 선택 규칙 (MANDATORY)

⚠️ **주의**: 본 표는 **raw `codex review` CLI 옵션**에 매핑된다. raw CLI는 `--scope` flag **미지원**, `--base/--uncommitted/--commit` 셋 중 하나로 review 대상을 명시한다 (`codex review --help`로 확인). (codex-plugin-cc `/codex:review` slash command wrapper는 `--scope` 옵션을 받지만 `disable-model-invocation: true`라 raw CLI로 호출해야 하므로 본 매핑이 정답.)

**raw CLI 옵션** (`codex review --help`):
- `--uncommitted`: uncommitted 변경 (staged + unstaged + untracked)
- `--base <BRANCH>`: 작업 브랜치 vs base ref 차이 — `git diff --shortstat <base>...HEAD` 기반. 이미 커밋된 N개도 한꺼번에 리뷰됨.
- `--commit <SHA>`: 특정 commit이 도입한 변경만 리뷰.
- (셋 다 없이 호출하면 review 대상 명시 누락으로 처리됨. `--scope` 인자 전달 시 exit 2)

**MANDATORY 대상 선택 절차**:
1. `git status --short --untracked-files=all` 실행 → uncommitted 변경 유무 확인.
2. `git rev-parse --abbrev-ref HEAD` + 기준 ref(보통 `main` 또는 PR base)로 `git diff --shortstat <base>...HEAD` 실행 → 커밋된 변경 유무 확인.
3. 분기:
   - uncommitted만 있음 → `--uncommitted`
   - 커밋된 것만 있음 → `--base <ref>`
   - 둘 다 있음 → `--base <ref>` (브랜치 전체가 더 포괄적, uncommitted는 별도 stash/commit 권장)
   - 둘 다 없음 → 호출 skip (리뷰 대상 없음)
4. `<ref>` 결정: PR 컨텍스트가 있으면 PR base, 없으면 `main` (또는 repo의 default branch).

**MANDATORY — 대상 flag 자체 검증 체크리스트 출력**: codex:review 호출 직전 다음 출력 (codex:adversarial-review는 companion이 자체적으로 branch 비교 수행하므로 free-text prompt만 전달).
- [ ] `git status --short` 결과 요약 (uncommitted 파일 수)
- [ ] `git diff --shortstat <base>...HEAD` 결과 요약 (커밋된 변경 파일/줄 수)
- [ ] 선택한 flag: [--uncommitted / --base <ref> / --commit <SHA>]
- [ ] 선택 사유: 위 분기 규칙 1~4 중 어느 케이스인가?
- [ ] base ref가 PR base 또는 default branch와 일치하는가? (--base 선택 시)

---

### 잘못된 호출 금지 (anti-patterns, MANDATORY)

- ❌ `Skill(skill="codex:review")` / `Skill(skill="codex:adversarial-review")` — 두 slash command 모두 frontmatter에 `disable-model-invocation: true`. 모델 invocation 불가.
- ❌ `Task(subagent_type="codex:review")` / `Task(subagent_type="codex:adversarial-review")` — codex-plugin-cc는 review/adversarial-review를 subagent로 노출하지 않음. (`codex:codex-rescue`만 subagent — `52-codex-rescue.md` 참조)
- ❌ OMC agents 디렉토리(`~/.claude/plugins/marketplaces/omc/agents/`)에서 `review.md` / `adversarial-review.md`를 찾으려 시도 → 거기 있을 파일 아님. **파일 부재를 N/A 사유로 삼지 말 것.** codex-plugin-cc native command라 codex-companion.mjs 자체가 처리. adversarial prompt도 codex 플러그인 내부에 번들 내장.
- ❌ "prompt 파일 부재"를 codex:review/adversarial-review 미실행 사유로 결론 → 호출 시도조차 안 한 채 N/A 처리 금지. 무조건 위 표의 Bash 호출 시도.
- ❌ `task` subcommand로 .md 파일 주입 — codex:critic용 패턴. codex:review/adversarial-review에는 부적합.
- ❌ raw `codex review` CLI에 `--scope` 전달 → **exit 2** (CLI 미지원). raw CLI는 `--base/--uncommitted/--commit` 중 하나 명시 필수. `--scope` 형식은 plugin slash command wrapper용이지만 wrapper는 `disable-model-invocation: true`라 raw CLI로 가야 함.
- ❌ raw CLI 호출 시 review 대상 flag(`--base/--uncommitted/--commit`) 모두 누락 → 대상 명시 누락. 작업 브랜치에 커밋 내역이 있으면 `--base <ref>` 사용.
- ❌ uncommitted+커밋된 변경 둘 다 있는데 `--uncommitted`만 호출 → 커밋된 부분 누락. `--base <ref>`로 통합 리뷰 (uncommitted는 별도 stash/commit).
- ❌ "리뷰 대상 없음"을 자의 판정해 호출 skip → 위 scope 선택 절차 1~3 실제 실행 후에만 결정. git 명령 없이 skip 금지.
- ❌ `/review` (Anthropic 빌트인)을 "PR 없음" 사유로 N/A 처리 → `/review`는 git diff 기반으로도 동작. PR 부재가 skip 사유 아님.
- ❌ codex 호출 결과 회수 실패(BashOutput 미수신)를 "타임아웃 N/A"로 카운트 → 회수 완료까지 대기 또는 재호출.
- ❌ **compaction·세션 재개 후 호출 형태를 이전 대화 트랜스크립트에서 복원** — 트랜스크립트에는 프롬프트 본문만 남기 쉬워 `--base` 같은 대상 flag 나 래퍼 종류가 누락되고, 그 빈칸을 기본값·기억으로 채우게 된다. **호출 형태의 SSOT 는 이 config 파일이다.** 세션이 재개됐으면 호출 전에 이 파일을 Read 하라 (2026-08-07 실제 위반: `codex:review` 를 raw CLI 대신 companion wrapper 로 호출 → 커스텀 focus text 를 받지 못해 exit 1).
