# docs/architecture — Spec sản phẩm & thiết kế kỹ thuật

Tất cả artifact intake sống ở đây. Sinh bởi solution-architect-agent (intake step 3).

## Cấu trúc

```
docs/architecture/
├── PROJECT.md              Vision + scope + NFR + glossary (intake step 1)
├── feat/                   FEAT-NNN-*.md (capability + AC)
├── adr/                    ADR-NNN-*.md (architecture decision records)
├── hld/                    hld-{boundary}.md (high-level design per boundary)
├── api/                    api-{boundary}.md (REST/GraphQL contract)
├── data-model/             data-model-{boundary}.md (DB schema, per backend boundary)
├── ux/                     ux-{boundary}.md (flows + screens, per FE boundary)
├── events/                 {boundary}-events.md (async event contracts)
├── integrations/           INTEG-EXT-* + INTEG-INT-* (sync cross-system/cross-boundary)
└── infra/
    └── docker-compose.yml  (local dev infra)
```

## Khi nào tạo

| Stage | Agent | Files |
|-------|-------|-------|
| INTAKE step 1 | requirement-analyst | PROJECT.md draft, FEAT-*.md draft |
| INTAKE step 2 | business-analyst | FEAT-*.md refine (AC + BR + boundaries_suggested) |
| INTAKE step 3 | solution-architect | ADR + HLD + API + data-model + UX + events + integrations + infra/docker-compose |
| INTAKE step 4 | program-planner | (none — chỉ đọc) |
| `/review-document` | review-document-agent | Revise theo user feedback hoặc sanity check |
| `/apply-cr` | apply-cr-agent | Edit liên quan CR scope change |

## Boundary types

- **Backend** (`kind: backend`): có HLD + API + data-model + (optional) events
- **BFF** (`kind: bff`): có HLD + API (GraphQL schema) + (optional) events
- **Web** (`kind: web`): có HLD + UX + (NO data-model own, consume BFF)
- **Mobile** (`kind: mobile`): có HLD + UX + (NO data-model own, consume BFF)

## Templates

| File | Template |
|------|----------|
| PROJECT.md | [TEMPLATE.project.md](TEMPLATE.project.md) |
| FEAT-*.md | [feat/TEMPLATE.feat.md](feat/TEMPLATE.feat.md) |
| ADR-*.md | [adr/TEMPLATE.adr.md](adr/TEMPLATE.adr.md) |
| HLD | [hld/TEMPLATE.hld.md](hld/TEMPLATE.hld.md) |
| API | [api/TEMPLATE.api.md](api/TEMPLATE.api.md) |
| data-model | [data-model/TEMPLATE.data-model.md](data-model/TEMPLATE.data-model.md) |
| UX | [ux/TEMPLATE.ux.md](ux/TEMPLATE.ux.md) |
| events | [events/TEMPLATE.events.md](events/TEMPLATE.events.md) |
| integrations EXT | [integrations/TEMPLATE.integration-external.md](integrations/TEMPLATE.integration-external.md) |
| integrations INT | [integrations/TEMPLATE.integration-internal.md](integrations/TEMPLATE.integration-internal.md) |

## Liên quan

- [docs/plans/](../plans/) — wave roadmap + per-wave plan
- [harness/SERVICE-BOUNDARY-MATRIX.json](../../harness/SERVICE-BOUNDARY-MATRIX.json) — boundary metadata (sync với hld-*, api-*)
- [knowledge-base/](../../knowledge-base/) — per-boundary KG (sync với entities + events sections)
- [agents/solution-architect-agent.md](../../agents/solution-architect-agent.md)
