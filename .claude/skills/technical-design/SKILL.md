---
name: technical-design
description: Thiết kế API, schema, sự kiện, và độ bền dữ liệu.
---

# Technical Design Skill

## Khi dùng

Trước implementation hoặc khi thay đổi kiến trúc.

## Hoạt động

1. **ADR** — `docs/architecture/adr/ADR-NNN-*.md` cho mỗi quyết định kiến trúc lớn (vd: tech-stack, backend-architecture, auth, ui-kit, …). Đánh số tuần tự; ≥ 3 ADR (tham chiếu theo **chủ đề**, không hardcode số).
2. Mỗi boundary: `hld/hld-{boundary}.md`, `api/api-{boundary}.md`, `data-model/data-model-{boundary}.md` (backend), `ux/ux-{boundary}.md` (mỗi FE boundary một file).
3. `integrations/INTEG-{INT|EXT}-*.md` + `infra/docker-compose.yml` skeleton.
4. KG per boundary — planner materialize `knowledge-base/{prefix}-{boundary}.knowledge-graph.yaml`.

## Done

- ADR accepted; integrations có ít nhất một hàng thật.
