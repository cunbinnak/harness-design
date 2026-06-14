# docs/architecture — Spec sản phẩm & thiết kế kỹ thuật

Product (DOMAIN author) + technical design (DESIGN author) sống ở đây. PROJECT.md derive ở Discovery D3.

## Cấu trúc

```
docs/architecture/
├── PROJECT.md              Vision + scope + NFR + glossary (Discovery D3)
├── ARCHITECTURE-PRINCIPLES.md  Invariants thiết kế (layering/contract-first/decision-traceability/anti-patterns)
├── SEVERITY-TEST-TAXONOMY.md   SSOT severity (bug/finding/TC) + test_type + tag
├── infra/TEMPLATE.service-repo-*  Scaffold guardrail repo con (CLAUDE.md/settings.json/gitignore)
├── epics/                  EP-*.md (DOMAIN — capability grouping, ≥2 FEAT/epic)
├── feat/                   FEAT-*.md (DOMAIN — AC BDD + business_rule_refs)
├── journeys/               JOURNEY-*.md (DOMAIN — hành trình người dùng)
├── personas/               PERSONA-*.md (DOMAIN — persona chi tiết)
├── business-rules/         BR-*.md (DOMAIN — ràng buộc nghiệp vụ)
├── adr/                    ADR-NNN-*.md (DESIGN — architecture decision records)
├── hld/                    hld-{boundary}.md (DESIGN — high-level design per boundary)
├── api/                    api-{boundary}.md (DESIGN — REST/GraphQL contract)
├── data-model/             data-model-{boundary}.md (DESIGN — DB schema, per backend boundary)
├── ux/                     ux-{boundary}.md (DESIGN — flows + screens, per FE boundary)
├── events/                 {boundary}-events.md (DESIGN — async event contracts)
├── integrations/           INTEG-EXT-* + INTEG-INT-* (DESIGN — sync cross-system/cross-boundary)
└── infra/
    └── docker-compose.yml  (DESIGN — local dev infra)
```

## Khi nào tạo

| Stage | Command / Agent | Files |
|-------|-----------------|-------|
| Discovery D3 | `/discovery-start D3` charter-author | PROJECT.md (PRD) + BOUNDARY-MAP + CHARTER |
| DOMAIN | `/domain-start` po/ba-author | epics/ + feat/ + journeys/ + personas/ + business-rules/ |
| DESIGN | `/design` solution-architect | ADR + HLD + API + data-model + UX + events + integrations + infra/docker-compose |
| PLAN | `/plan` program-planner | (none here — đọc; ghi docs/plans/ + MATRIX) |
| `/review-document` | review-document-agent | Revise theo user feedback hoặc sanity check |
| `/apply-cr` | apply-cr-agent | Edit liên quan CR scope change (DESIGN amendment) |

## Boundary types

- **Backend** (`kind: backend`): có HLD + API + data-model + (optional) events
- **BFF** (`kind: bff`): có HLD + API (GraphQL schema) + **bff-aggregation-{boundary}.md** (nếu fan-out ≥2 backend) + (optional) events
- **Web** (`kind: web`): có HLD + UX + (NO data-model own, consume BFF)
- **Mobile** (`kind: mobile`): có HLD + UX + (NO data-model own, consume BFF)

## Templates

> **Template là để TUÂN THEO.** Mọi artifact PHẢI theo đúng cấu trúc template tương ứng — KHÔNG tự do format, KHÔNG mỗi boundary 1 kiểu. Skill DOMAIN/DESIGN trỏ "theo `TEMPLATE.X`"; reviewer check artifact khớp template. Sửa convention → sửa template (1 nơi), không sửa lẻ từng file.

| File | Template |
|------|----------|
| PROJECT.md | [TEMPLATE.project.md](TEMPLATE.project.md) |
| EP-*.md | [epics/TEMPLATE.epic.md](epics/TEMPLATE.epic.md) |
| FEAT-*.md | [feat/TEMPLATE.feat.md](feat/TEMPLATE.feat.md) |
| JOURNEY-*.md | [journeys/TEMPLATE.journey.md](journeys/TEMPLATE.journey.md) |
| PERSONA-*.md | [personas/TEMPLATE.persona.md](personas/TEMPLATE.persona.md) |
| BR-*.md | [business-rules/TEMPLATE.business-rule.md](business-rules/TEMPLATE.business-rule.md) |
| ADR-*.md | [adr/TEMPLATE.adr.md](adr/TEMPLATE.adr.md) |
| HLD | [hld/TEMPLATE.hld.md](hld/TEMPLATE.hld.md) |
| API | [api/TEMPLATE.api.md](api/TEMPLATE.api.md) |
| BFF aggregation | [api/TEMPLATE.bff-aggregation.md](api/TEMPLATE.bff-aggregation.md) |
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
