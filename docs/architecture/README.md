# docs/architecture — Sản phẩm & thiết kế kỹ thuật

## Cấu trúc

```text
docs/architecture/
  PROJECT.md              # Tổng quan dự án (intake bước 1–2)
  feat/                   # FEAT-*.md — capability, AC
  adr/                    # ADR-001 …
  hld/   api/   data-model/   ux/   # per boundary_id
  integrations-matrix.md
  infra/
    docker-compose.yml
```

| Vùng | Nội dung |
|------|----------|
| **PROJECT.md** | Vision, phạm vi, glossary — **cả dự án** |
| **feat/** | `FEAT-*.md` — deliverable chi tiết |
| **adr/, hld/, …** | Thiết kế kỹ thuật (intake bước 3+) |

Template: [TEMPLATE.project.md](TEMPLATE.project.md) · [feat/TEMPLATE.feat.md](feat/TEMPLATE.feat.md)

```bash
py scripts/materialize_ux_documents.py --from-roster docs/plans/project/agent-roster.md
```

## Boundary & FE

- **Backend:** `customer`, `sales`, … → `hld-{id}.md`, `api-{id}.md`, `data-model-{id}.md`.
- **Frontend:** mỗi app = một `boundary_id` (`fe-web`, `fe-admin`).
- **UX:** `ux-{boundary_id}.md` bắt buộc cho mọi FE boundary.

## ADR & conventions

| Tài liệu | Skill |
|----------|--------|
| `adr/ADR-*.md` | `tech-stack` |
| Layered / DDD | `backend-conventions` |
| FE structure | `frontend-conventions` |

## Matrix & KG

- `harness/SERVICE-BOUNDARY-MATRIX.json` — sync khi `start-wave`.
- `knowledge-base/{boundary_id}.knowledge-graph.yaml` — intake bước 4.
