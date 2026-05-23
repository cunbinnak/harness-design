# Knowledge base — shared memory

**Knowledge-base = shared memory** của Harness: agent và orchestrator **đọc/ghi** qua lượt làm việc, không nhét PRD dài vào đây.

## Phân vai (không trùng docs/)

| Lớp | Vai trò |
|-----|---------|
| `docs/` | Spec đã thống nhất (PRD, HLD, API, plan) |
| **`knowledge-base/`** | Trạng thái làm việc, **decisions**, learnings, domain graph |
| `handoff/` | Bàn giao wave/stage giữa agent |
| `STATE.context` | **Chỉ pointer** path file cần đọc lượt này |

## File

| File | Khi nào |
|------|---------|
| `TEMPLATE.knowledge-graph.yaml` | Copy khi tạo boundary mới |
| `shared.knowledge-graph.yaml` | Luôn có — decisions/learnings xuyên boundary |
| `{boundary_id}.knowledge-graph.yaml` | Sau khi đăng ký boundary trong matrix |

## Schema (tóm tắt)

- `domain` — entities, relationships
- `implementation` — backlog, in_progress, completed
- **`decisions`** — quyết định đã chốt (id, context, decision, rationale, status)
- **`discipline`** — `do_not_repeat`, `blockers` (rule harness — đọc trước mỗi lượt)
- `learnings` — gotchas, patterns (đồng bộ với `do_not_repeat` khi ghi qua `knowledge_writer.py do-not-repeat`)
- `integrations` — phụ thuộc boundary khác (tham chiếu matrix)

## Ghi nhận

```bash
python scripts/knowledge_writer.py decision knowledge-base/shared.knowledge-graph.yaml '{"context":"...","decision":"...","rationale":"..."}'
python scripts/knowledge_writer.py do-not-repeat knowledge-base/shared.knowledge-graph.yaml "không được ..."
python scripts/knowledge_writer.py blocker knowledge-base/shared.knowledge-graph.yaml "chờ ..."
```

Rule chung (Cursor): `.cursor/rules/harness-agent-discipline.mdc` (`alwaysApply: true`).

See [`SETUP-GUIDE.md`](../SETUP-GUIDE.md).

**Nguyên tắc:** Một decision — một entry; supersede bằng `status: superseded` + `supersedes: DEC-xxx`.
