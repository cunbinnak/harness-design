# Harness hooks

Rule: [`HOOK-RULES.json`](../HOOK-RULES.json) · Bridge: `scripts/hooks/ide_bridge.py`

## Cursor (project)

[`.cursor/hooks.json`](../../.cursor/hooks.json) — dùng `py` (Python 3.14+), `failClosed: false`.

| Event | Check |
|-------|--------|
| Write/Edit | `owned_paths` |
| Shell | gate khi `harness.py complete` |
| stop | RETURN schema nếu spawn.active |

## Chạy tay

```bash
py scripts/hooks/run_hook.py owned_paths --payload "{\"path\":\"docs/x.md\"}"
```

## CLI complete

`py scripts/harness.py <cmd> complete` — gates trong `workflow_engine` (không phụ thuộc hook IDE).
