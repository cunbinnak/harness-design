# Harness hooks (implementation)

**Logic & checklist:** `task_check.py` · **Quy tắc:** [`harness/HOOK-RULES.json`](../../harness/HOOK-RULES.json)

## Clone repo — dùng ngay (Cursor hoặc Claude Code)

Hook **đã cấu hình sẵn** trong repo. Không cần sync, không cần chạy script phụ.

| IDE | File cấu hình | Ghi chú |
|-----|----------------|---------|
| **Cursor** | [`.cursor/hooks.json`](../../.cursor/hooks.json) | Tự load khi mở project |
| **Claude Code** | [`.claude/settings.local.json`](../../.claude/settings.local.json) → `hooks` | Ưu tiên cao hơn `~/.claude` — commit trong repo |

## Triggers (tự chạy qua IDE)

| Trigger | Cursor | Claude Code |
|---------|--------|-------------|
| `session_start` | `sessionStart` | `SessionStart` (async) |
| `pre_write_check` | Write/Edit | Write/Edit/… |
| `pre_state_transition` | Shell | Bash |
| `pre_task_check` | Task | Task/Agent + SubagentStart |
| `post_task_log` | stop | Stop + SubagentStop |

`post_state_transition` / `on_change_detected` chạy từ `workflow_engine.py` và `post_task_log` (CLI + IDE).

## 12 câu checklist (`task_check.py`)

feature · feature_stage · agent_assigned · boundary_resolve · owned_paths · task_in_stage · kg_completed · kg_in_progress · blockers · decisions · do_not_repeat · why_linked

## Sửa hook (maintainer)

Khi đổi trigger/event, cập nhật [`.cursor/hooks.json`](../../.cursor/hooks.json) và [`.claude/settings.local.json`](../../.claude/settings.local.json) cho khớp logic.

## Debug (tùy chọn — không phải workflow người dùng)

`run_hook.py` chỉ để dev test từng hook id cũ (`owned_paths`, `discipline_blockers`, …). Agent/end-user **không** cần chạy.

Ghi KG sau task (agent chạy khi cần):

```bash
py scripts/knowledge_writer.py in-progress knowledge-base/shared.knowledge-graph.yaml "FEAT-001:AC-1"
py scripts/knowledge_writer.py completed knowledge-base/shared.knowledge-graph.yaml "FEAT-001:AC-1"
```

Rule: [`.cursor/rules/harness-agent-discipline.mdc`](../../.cursor/rules/harness-agent-discipline.mdc)
