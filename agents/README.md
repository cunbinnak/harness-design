# Agents

Spec: [docs/AGENT-SPEC.md](../docs/AGENT-SPEC.md)

## Doc scope per agent (`role:` frontmatter)

Mỗi agent khai báo `role:` trong YAML frontmatter. Doc-scope (files agent được đọc) tự động resolve từ central registry **[harness/AGENT-DISCIPLINE.json → `agent_roles`](../harness/AGENT-DISCIPLINE.json)** với placeholder `{boundary}` và `{wave}`.

| Role | Đọc gì (tóm tắt) |
|------|--------------------|
| `intake:requirement-analyst` | PROJECT + FEAT/* (draft) |
| `intake:business-analyst` | PROJECT + FEAT/* (refine AC) |
| `intake:solution-architect` | PROJECT + FEAT/* (writes ADR/HLD/API/UX) |
| `intake:program-planner` | PROJECT + FEAT + integrations-matrix (writes plans) |
| `dev:backend` | wave.md + hld-{boundary} + api-{boundary} + data-model-{boundary} + KG |
| `dev:frontend` | wave.md + ux-{boundary} + api-*.md (contracts) + KG |
| `review:backend` | source code {boundary} + hld + api + KG |
| `review:frontend` | source code {boundary} + ux + KG |
| `fix:backend` / `fix:frontend` | tracking/waves/{wave}/bugs + source + (HLD/UX) + KG |
| `dev-handoff` | wave plan + infra + handoff doc |
| `test-plan` | handoff + FEAT + api (contracts) |
| `test-execute` | test cases + handoff + infra — **không đọc source code** |
| `release`, `end-wave`, `apply-cr`, `start-wave`, `review:document`, `cross-boundary-review` | xem registry |

`build_command_prompt.py` inject section **DOCS IN SCOPE** vào prompt agent, list các file scoped theo role.

## Luồng `/intake-requirement`

Orchestrator: [intake-orchestrator-agent.md](intake-orchestrator-agent.md)

Mỗi bước spawn **một specialist** (không gộp 4 vai một lượt):

```bash
py scripts/build_command_prompt.py intake-requirement --step 1 --input "..."
py scripts/build_command_prompt.py intake-requirement --step 2
py scripts/build_command_prompt.py intake-requirement --step 3
py scripts/build_command_prompt.py intake-requirement --step 4
```

| Bước | Agent |
|------|--------|
| 1 | [requirement-analyst-agent.md](requirement-analyst-agent.md) |
| 2 | [business-analyst-agent.md](business-analyst-agent.md) |
| 3 | [solution-architect-agent.md](solution-architect-agent.md) |
| 4 | [program-planner-agent.md](program-planner-agent.md) |

Bước 4: materialize từ [_template.agent.md](_template.agent.md) — **backend boundaries + FE (`fe`)**.

```bash
py scripts/materialize_boundary_agents.py --boundaries order,product --wave wave-001
```

## Dev agents (tạo ở bước 4)

| Layer | boundary | Dev | Fix | Review | Command |
|-------|----------|-----|-----|--------|---------|
| Backend | `{b}` | `{b}-agent.md` | `fix-{b}-agent.md` | `review-{b}-agent.md` | `start-dev --boundary {b}` |
| Frontend | `fe` | `fe-agent.md` | `fix-fe-agent.md` | `review-fe-agent.md` | `start-dev --boundary fe` |

## Command agents (cố định trong repo)

`start-wave`, `review-document`, `apply-cr`, `dev-handoff`, `test-plan`, `test-execute`, `release`, `end-wave` — mỗi command một file `*-agent.md`.
