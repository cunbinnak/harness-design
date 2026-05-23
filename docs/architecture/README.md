# docs/architecture — Thiết kế kỹ thuật

## Cấu trúc

```text
docs/architecture/
  adr/                    # ADR-001 … ADR-005 (intake bước 3)
  hld/   api/   data-model/   ux/   # per boundary_id
  integrations-matrix.md  # → sync vào SERVICE-BOUNDARY-MATRIX.integrations
  infra/
    docker-compose.yml    # dev-handoff: compose chạy được
    local-dev.md          # từ TEMPLATE.local-dev.md
```

## Boundary & FE

- **Backend:** `customer`, `sales`, … → `hld-{id}.md`, `api-{id}.md`, `data-model-{id}.md`.
- **Frontend:** mỗi app = một `boundary_id` (`fe-web`, `fe-admin`) — **không** dùng chung `fe-agent` trừ khi chỉ một UI.
- **UX:** `ux-{boundary_id}.md` bắt buộc cho mọi FE boundary.

## ADR & conventions

| Tài liệu | Skill |
|----------|--------|
| `adr/ADR-*.md` | `tech-stack` |
| Layered / DDD | `backend-conventions` |
| FE structure | `frontend-conventions` |

## Matrix & KG

- `harness/SERVICE-BOUNDARY-MATRIX.json` — điền khi `start-wave` (sync roster + integrations).
- `knowledge-base/{boundary_id}.knowledge-graph.yaml` — tạo lúc intake bước 4.
