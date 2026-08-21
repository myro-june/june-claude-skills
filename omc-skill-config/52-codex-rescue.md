## OMC Skill Config — codex:rescue 호출 우선순위 (MANDATORY)

`codex:rescue`는 두 가지 path로 호출 가능. **우선순위**:

1. **1순위: parent 세션 직접 Bash** — `node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" task [--fresh|--resume-last] [--write] "<prompt>"`. 명시적 flag 제어 가능, 빠르고 단순.
2. **2순위 (1순위 실패 시): subagent 경유** — `Agent(subagent_type="codex:codex-rescue", prompt=...)`. plugin의 forwarding wrapper로 flag 처리 자동. permission/환경 이슈로 1순위 실패 시 fallback.

codex-rescue subagent 자체는 내부에서 동일한 `Bash` + `codex-companion.mjs task`를 호출하는 forwarder (`~/.claude/plugins/marketplaces/openai-codex/plugins/codex/agents/codex-rescue.md` 참조). 두 path는 같은 결과.

**단, codex:critic 호출은 예외**: critic.md 주입이 필요한 OMC custom 패턴이라 parent Bash + task subcommand만 사용 — subagent 경유는 codex:critic 용도에는 부적합. 그건 `50-critic.md` 참조.
