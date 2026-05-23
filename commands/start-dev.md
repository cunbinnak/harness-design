# start-dev

Spawn **dev boundary agent** (`{boundary}-agent.md`) đã tạo lúc plan.

**Agent:** `agents/{boundary}-agent.md`

```bash
python scripts/build_command_prompt.py start-dev --list-boundaries
python scripts/build_command_prompt.py start-dev --boundary order
python scripts/harness.py start-dev complete
```

Pre: [`prepare-dev`](prepare-dev.md)

Hook `dev_agent_spawn`: file agent phải tồn tại trước spawn.
