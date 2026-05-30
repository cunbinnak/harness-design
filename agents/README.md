# Agents

Source of truth: 20 file trong `agents/` (16 singleton command + 2 templates + 2 sample materialized + README).

State machine: [harness/STATE-MACHINE.json](../harness/STATE-MACHINE.json) (10 states, 13 commands).

## Agent inventory

### Intake (4 specialists + main orchestrate)

`/intake-requirement` được orchestrate bởi **Claude main** (no orchestrator agent — flat pattern). Main spawn 4 specialists tuần tự:

| Step | Agent | Skill primary | Output chính |
|------|-------|---------------|--------------|
| 1 | [requirement-analyst-agent](requirement-analyst-agent.md) | `requirement-analysis` | PROJECT.md + FEAT-*.md draft + project.service_prefix |
| 2 | [business-analyst-agent](business-analyst-agent.md) | `business-analysis` | FEAT refined (AC testable + BR + boundaries_suggested) |
| 3 | [solution-architect-agent](solution-architect-agent.md) | `technical-design` | ADR + HLD + API + data-model + UX + events + integrations + infra/docker-compose |
| 4 | [program-planner-agent](program-planner-agent.md) | `implementation-plan` | WAVE-SEQUENCE + wave-001 + MATRIX + materialize per-boundary dev/fix/KG |

### Review (5 singletons)

| Agent | Command | Skill primary | Mode |
|-------|---------|---------------|------|
| [review-document-agent](review-document-agent.md) | `/review-document` | `business-analysis` | revision (feedback) + sanity-check (no arg) |
| [review-backend-agent](review-backend-agent.md) | `/review-dev` (kind=backend) | `review-backend` | Internal loop: review → spawn fix → re-review |
| [review-bff-agent](review-bff-agent.md) | `/review-dev` (kind=bff) | `review-bff` | Same |
| [review-web-agent](review-web-agent.md) | `/review-dev` (kind=web) | `review-web` | Same |
| [review-mobile-agent](review-mobile-agent.md) | `/review-dev` (kind=mobile) | `review-mobile` | Same |

> Review agents là **singleton per kind** (1 file dùng cho mọi boundary cùng kind).
> Rules/checklist cụ thể nằm trong skill (project-customizable), KHÔNG hardcode trong agent file.

### Operations (6 ops)

| Agent | Command | Skill primary | Stage transition |
|-------|---------|---------------|------------------|
| [start-wave-agent](start-wave-agent.md) | `/start-wave` | (none — pure orchestration) | INTAKE → WAVE_OPEN |
| [dev-handoff-agent](dev-handoff-agent.md) | `/dev-handoff` | `infra-local-dev` | REVIEW_DEV → DEV_HANDOFF |
| [test-plan-agent](test-plan-agent.md) | `/test-plan` | `test-plan` | DEV_HANDOFF → TEST_PLAN |
| [test-execute-agent](test-execute-agent.md) | `/test-execute` | `test-execute` | TEST_PLAN → TEST_EXECUTE → (auto) MANUAL_TEST |
| [end-wave-agent](end-wave-agent.md) | `/end-wave` | (none) | MANUAL_TEST → DONE |
| [done-wave-agent](done-wave-agent.md) | `/done-wave` | `infra-local-dev` | DONE → BOOTSTRAP |

### Side (1)

| Agent | Command | Skill primary | Stage transition |
|-------|---------|---------------|------------------|
| [apply-cr-agent](apply-cr-agent.md) | `/apply-cr <CR-ID>` | `business-analysis` | DONE → INTAKE (amendment mode) |

## Materialize per-boundary (after intake)

Sau intake step 4 + `/start-wave`, `materialize.py` gen per boundary:

| Type | File | Template |
|------|------|----------|
| Dev | `agents/dev-{prefix}-{boundary}-agent.md` | [_template-dev-agent.md](_template-dev-agent.md) |
| Fix | `agents/fix-{prefix}-{boundary}-agent.md` | [_template-fix-agent.md](_template-fix-agent.md) |
| KG | `knowledge-base/{prefix}-{boundary}.knowledge-graph.yaml` | [TEMPLATE.boundary-kg.yaml](../knowledge-base/TEMPLATE.boundary-kg.yaml) |

Sample materialized (test fixture):
- [dev-demo-order-management-agent.md](dev-demo-order-management-agent.md)
- [fix-demo-order-management-agent.md](fix-demo-order-management-agent.md)

## v4 agent file structure

Mỗi agent có 7 sections:

```yaml
---
name: <agent-name>
role: "<role-namespace>:<sub-role>"  # vd "intake:requirement-analyst", "review:backend"
command: <slash-command>              # spawn command
pipeline_step: <N|null>               # 1-4 cho intake specialist
primary_skill: <skill-name|null>      # invoke ngay khi spawn
secondary_skills: [...]               # available on-demand
stage_transition: "<from> -> <to>"    # state machine transition
---

# Title

## Identity            — role, command, stage
## Trách nhiệm         — artifacts to produce
## Workflow            — process steps
## Skills              — primary + secondary
## Owned paths         — file patterns agent có thể edit
## Forbidden           — gì NOT làm
## RETURN SCHEMA       — JSON template
```

## Workflow

1. Edit agent file ở `agents/` (root, source of truth)
2. (Optional) Test build prompt: `py scripts/build_prompt.py <command> --stats`
3. Slash command sẽ dùng agent file khi spawn sub-agent

## Liên quan

- [harness/STATE-MACHINE.json](../harness/STATE-MACHINE.json) — state + transitions
- [harness/SERVICE-BOUNDARY-MATRIX.json](../harness/SERVICE-BOUNDARY-MATRIX.json) — boundary metadata
- [commands/README.md](../commands/README.md) — slash commands
- Root [CLAUDE.md](../CLAUDE.md) — router file
