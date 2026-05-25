# start-dev

Spawn **dev boundary agent** (`{boundary}-agent.md`) đã tạo lúc intake bước 4.

**Slash:** `/start-dev <boundary_id>` (vd. `order`, `fe-web`)

**Agent:** `agents/{boundary}-agent.md`

```bash
py scripts/build_command_prompt.py start-dev --list-boundaries
py scripts/build_command_prompt.py start-dev --boundary order
py scripts/harness.py start-dev complete '{"features_in_flight":["FEAT-001"],"boundaries_in_flight":["order"]}'
```

**Trước khi complete:** điền `docs/plans/waves/{wave-id}/wave.md` §2 (gán FEAT → boundary) và evidence `features_in_flight` / `boundaries_in_flight`.

Hook `dev_agent_spawn`: file agent phải tồn tại trước spawn.

[SETUP-GUIDE.md](../SETUP-GUIDE.md)
