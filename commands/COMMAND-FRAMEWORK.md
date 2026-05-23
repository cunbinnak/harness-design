# Khung Command

> Gates: [`harness/COMMAND-GATES.json`](../harness/COMMAND-GATES.json) · Hooks: [`harness/HOOK-RULES.json`](../harness/HOOK-RULES.json)

Luồng đầy đủ, intake 4 bước, CR, gate checklist: **[SETUP-GUIDE.md](../SETUP-GUIDE.md)**

Danh sách command: **[README.md](README.md)**

## Ai chạy?

| Command | Agent |
|---------|--------|
| `intake-requirement` | 4 specialist (pipeline) + orchestrator |
| `apply-cr` | apply-cr-agent → intake amendment |
| `start-wave`, `review-document`, `test-*`, `release`, `end-wave` | `agents/{command}-agent.md` |
| `start-dev` / `fix-bugs` / `review-dev` | `agents/{prefix}{boundary}-agent.md` |

```bash
py scripts/build_command_prompt.py start-wave --wave 2
py scripts/build_command_prompt.py start-dev --boundary order
py scripts/harness.py start-wave complete '{"wave_id": "2", "wave_title": "Phase 2"}'
```

Discipline: [`.cursor/rules/harness-agent-discipline.mdc`](../.cursor/rules/harness-agent-discipline.mdc) + shared KG
