# Agent Spec

> Single source for agent structure. Doc scope per role -> [`harness/AGENT-DISCIPLINE.json[agent_roles]`](../harness/AGENT-DISCIPLINE.json).

## Template (boundary materialization)

Một template duy nhất: [`agents/_template.agent.md`](../agents/_template.agent.md) — materialize bộ 3 agent (`{id}`, `fix-{id}`, `review-{id}`) cho mỗi boundary.

```bash
py scripts/materialize.py boundary-agents --from-roster docs/plans/project/agent-roster.md
```

Role auto-set theo layer:

| Layer | dev role | fix role | review role |
|-------|---------|---------|------------|
| backend | `dev:backend` | `fix:backend` | `review:backend` |
| fe | `dev:frontend` | `fix:frontend` | `review:frontend` |

## Intake & command agents (cố định)

`/intake-requirement` spawn 4 specialist theo step (xem `harness/PIPELINES.json`). Mỗi command khác -> `agents/{command}-agent.md`.

## Cấu trúc nội dung mọi `*-agent.md`

1. **Frontmatter** — `agent_id`, `role` (key trong `agent_roles`), `command`, `kind`, `knowledge_graph`, `skills`
2. **Identity** — agent là ai, không phải ai
3. **Nhiệm vụ** — phải làm / không được
4. **Phải làm (steps)** — sequence cụ thể
5. **RETURN SCHEMA** — JSON theo [PROTOCOL.md](../harness/PROTOCOL.md)

Doc scope **KHÔNG** hardcode trong agent .md — auto-inject từ role registry vào prompt.

## Evidence

Evidence cho `harness.py <cmd> complete` = JSON CLI argument (transient — ghi vào `checkpoints[]`, không có folder lưu).
