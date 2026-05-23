# Harness hooks (implementation)

**Cấu hình:** [`harness/HOOK-RULES.json`](../../harness/HOOK-RULES.json)  
**IDE bridge:** `ide_bridge.py` · **Chạy tay:** `run_hook.py`

## Cursor (`.cursor/hooks.json`)

| Event | Hook id | Mô tả |
|-------|---------|--------|
| `pre_edit` | `owned_paths` | Chỉ sửa owned_paths / allowlist |
| `pre_shell` | `workflow_allowed_next`, `evidence_schema`, `transition_gate`, `discipline_blockers` | Khi `harness.py … complete` |
| `pre_spawn` | `spawn_active`, `dev_agent_spawn`, `spawn_stage` | Trước sub-agent |
| `post_agent` | `return_schema`, `discipline_kg_return` | Khi `spawn.active` — JSON RETURN + kg_appended |

`failClosed: true` — vi phạm → **HARNESS — KHÔNG ĐƯỢC PHÉP**.

## Discipline + KG

- **`discipline_blockers`** — đọc `knowledge-base/shared.knowledge-graph.yaml` → `discipline.blockers`; chặn `harness complete` nếu còn blocker.
- **`discipline_kg_return`** — sub-agent có `files_changed` / `completed` thì phải có `kg_appended` hoặc `deferred[].tracked_in`.
- **`spawn_stage`** — `STATE.stage` phải thuộc `spawn.allowed_stages`.

Rule đầy đủ: [`.cursor/rules/harness-agent-discipline.mdc`](../../.cursor/rules/harness-agent-discipline.mdc).

## Chạy tay

```bash
py scripts/hooks/run_hook.py discipline_blockers
py scripts/hooks/run_hook.py return_schema --payload "{\"body\":{\"completed\":[],\"deferred\":[],\"needs_review\":[],\"files_changed\":[\"a\"],\"build\":\"pass\",\"lint\":\"pass\",\"test\":\"pass\"}}"
py scripts/hooks/run_hook.py owned_paths --payload "{\"path\":\"docs/x.md\"}"
```

CLI `py scripts/harness.py <cmd> complete` cũng gọi `discipline_blockers` trong `workflow_engine` (không phụ thuộc IDE).
