---
name: technical-design
description: Thiết kế API, schema, sự kiện, và độ bền dữ liệu.
---

# Technical Design Skill

## Khi dùng

Trước implementation hoặc khi thay đổi kiến trúc.

## Hoạt động

1. **ADR** — `docs/architecture/adr/ADR-001` … `005` (stack, BE arch, auth, UI, PDF).
2. Mỗi boundary: `hld/`, `api/`, `data-model/`, `ux/ux-{id}.md` (mỗi FE boundary một file UX).
3. `integrations-matrix.md` + `infra/docker-compose.yml` skeleton.
4. KG per boundary — planner materialize `knowledge-base/{id}.knowledge-graph.yaml`.

## Done

- ADR accepted; integrations có ít nhất một hàng thật.
