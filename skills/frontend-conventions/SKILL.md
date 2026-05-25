---
name: frontend-conventions
description: Quy ước FE theo boundary frontend — app surface, API contract, cấu trúc.
---

# Frontend Conventions Skill

## Khi dùng

Boundary `layer: fe` / `kind: fe` (ví dụ `fe-web`, `fe-admin`). Mỗi boundary FE **phục vụ** một hoặc nhiều backend — ghi trong agent roster cột `serves_boundaries`.

## Một boundary FE = một app surface

| `fe_surface` | Thư mục gợi ý | Ghi chú |
|--------------|---------------|---------|
| `web-app` | `apps/{boundary_id}/` hoặc `apps/web/` | SPA chính |
| `web-admin` | `apps/admin/` | Portal nội bộ |
| `mobile` | `apps/mobile/` | React Native / Flutter |

Agent file: `agents/{boundary_id}-agent.md` — **không** gom chung `fe-agent.md` trừ khi roster chỉ có một boundary `fe`.

## Quy ước bắt buộc

1. **UX** — implement theo `docs/architecture/ux/ux-{boundary_id}.md`.
2. **API** — chỉ gọi contract `api-{backend}.md` của backend trong `serves_boundaries`.
3. **State** — feature state theo FEAT; shared UI kit theo ADR-004.
4. **Auth** — theo ADR-003 (token, refresh, route guard).
5. **Không** sửa `services/*` backend trừ BFF thuộc boundary FE (nếu có).

## Cấu trúc (React/Vue gợi ý)

```text
apps/{app}/
  src/
    features/       # theo FEAT
    shared/         # components, hooks
    api/            # client generated hoặc hand-written
    routes/
  package.json
packages/             # design system dùng chung (nếu ADR cho phép)
```

## Done

- `serves_boundaries` khớp roster và `integrations-matrix.md`.
- Build/lint FE pass trước `review-dev`.
