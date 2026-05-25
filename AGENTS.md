# AGENTS

Chi tiết: [`agents/README.md`](agents/README.md) (bảng role->docs scope) · [`agents/_template.agent.md`](agents/_template.agent.md) (template materialize)

## Luồng tóm tắt

- **`/intake-requirement` (4 step)** -> spawn 4 specialist tuần tự: `requirement-analyst`, `business-analyst`, `solution-architect`, `program-planner` (bước 4 materialize boundary agents)
- **`/start-dev | /fix-bugs | /review-dev`** -> spawn `agents/{prefix}{boundary}-agent.md` (prefix: `''`, `fix-`, `review-`) — role auto-set qua `materialize_boundary_agents.py REGISTRY_ROLE_KEY`
- **Các command khác** -> `agents/{command}-agent.md` (15 file core)

## Doc scope per agent

Mỗi agent có `role:` trong YAML frontmatter -> `harness/AGENT-DISCIPLINE.json[agent_roles]` define `reads`/`writes`. `build_command_prompt.py` auto-inject DOCS IN SCOPE.

Discipline (rule luôn bật): [`.cursor/rules/harness-agent-discipline.mdc`](.cursor/rules/harness-agent-discipline.mdc) + KG `discipline.*` trong `knowledge-base/shared.knowledge-graph.yaml`.
