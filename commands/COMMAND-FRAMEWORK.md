# Command Framework

> Setup + flow đầy đủ: [`SETUP-GUIDE.md`](../SETUP-GUIDE.md) · Danh sách 16 command: [`README.md`](README.md) · Gates: [`harness/COMMAND-GATES.json`](../harness/COMMAND-GATES.json)

## 1 command = 2 lệnh

```bash
py scripts/build_command_prompt.py <command> [--step N] [--boundary X]   # spawn agent
py scripts/harness.py <command> complete '<json evidence>'              # gate + transition
```

## Ai chạy command nào?

| Command | Agent |
|---------|-------|
| `intake-requirement` | 4 specialist (pipeline `harness/PIPELINES.json#intake-requirement`) |
| `apply-cr` | `agents/apply-cr-agent.md` |
| `start-dev` / `fix-bugs` / `review-dev` | `agents/{prefix}{boundary}-agent.md` (materialize từ `_template.agent.md`) |
| Còn lại | `agents/{command}-agent.md` |

## Discipline

- Rule luôn bật: [`.cursor/rules/harness-agent-discipline.mdc`](../.cursor/rules/harness-agent-discipline.mdc)
- Doc scope per agent: `agent_roles` registry trong [`harness/AGENT-DISCIPLINE.json`](../harness/AGENT-DISCIPLINE.json)
- KG shared: [`knowledge-base/shared.knowledge-graph.yaml`](../knowledge-base/shared.knowledge-graph.yaml)
