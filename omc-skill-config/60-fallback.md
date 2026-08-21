## OMC Skill Config — config 미정의 시 행동 (MANDATORY)

config 또는 plugin 매뉴얼이 명시 안 한 호출 패턴/매핑/prompt에 대해서:

- **자의적 매핑/prompt 결정 금지**. (예: 임의로 .md 파일 매칭, 추론 기반 호출 패턴 결정)
- 사용자에게 **명시적으로 확인 후 진행**.
- 잘못된 매핑으로 호출된 결과는 무효 처리하고 정확한 방식으로 재호출.
- plugin 자체 매뉴얼 (예: `~/.claude/plugins/marketplaces/openai-codex/plugins/codex/commands/*.md`) 우선 참조 — config 보완보다 plugin 매뉴얼이 SSOT.
- 매뉴얼/config 사이 충돌 시 사용자에게 보고 후 config 정정 협의.

**MANDATORY — 미정의 항목 발견 시 자체 검증 체크리스트 출력**:
- [ ] config(`~/.claude/omc-skill-config/`)에 명시됐는가? (Y → 그대로 따름, N → 다음 항목)
- [ ] plugin 매뉴얼에 명시됐는가? (Y → 매뉴얼 따름, N → 다음 항목)
- [ ] 자의적 추측 호출 시도하지 않고 사용자에게 확인 요청 메시지 출력했는가?
- [ ] 매뉴얼/config 충돌 발견 시 사용자에게 보고했는가?
