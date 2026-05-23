## Boundary agents (generated at intake step 4)

| boundary_id | layer | waves_participating | serves_boundaries | fe_surface |
|-------------|-------|---------------------|-------------------|------------|
| customer | backend | 1, 2 | — | — |
| sales | backend | 1 | — | — |
| fe-web | fe | 1, 2 | customer,sales | web-app |

> **waves_participating:** số wave (`1`, `2`, `02`) hoặc `wave-001`, hoặc `1;2`, hoặc `all` (mọi wave trong roadmap). Harness chuẩn hóa → `wave-001`, `wave-002`, …
>
> Agent materialize ghi **đủ wave** vào frontmatter `agents/*-agent.md` (không chỉ wave-001).
>
> ```bash
> py scripts/materialize_boundary_agents.py --from-roster docs/plans/project/agent-roster.md
> py scripts/materialize_knowledge_graphs.py --from-roster docs/plans/project/agent-roster.md
> ```
