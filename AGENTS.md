# AGENTS

[agents/README.md](agents/README.md) · [docs/AGENT-SPEC.md](docs/AGENT-SPEC.md)

## Luồng

- **`/intake-requirement`** → `--step 1..4` spawn lần lượt `requirement-analyst-agent.md`, …, `program-planner-agent.md`
- **Boundary dev** → chỉ `_template.agent.md` (materialize bước 4)
- **Command khác** → `agents/{command}-agent.md` + `build_command_prompt.py <command>`

Không có `_template.intake-agent` hay `_template.command-agent`.
