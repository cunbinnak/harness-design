# Agents

Source of truth: 26 file trong `agents/` (23 singleton command + 2 templates + README). Per-boundary dev/fix agent **materialize từ MATRIX** ở `start-wave` (không commit sample).

State machine: [harness/STATE-MACHINE.json](../harness/STATE-MACHINE.json) (17 states, 24 commands).

## Agent inventory

> Front-half = DISCOVERY (D0-D3) → DOMAIN_AUTHORING → DESIGN → PLAN → REVIEW. Mỗi stage spawn bởi **Claude main** (flat pattern, no orchestrator agent).

### Discovery (4 specialists)

`discovery-start <D>` spawn agent per wave (cùng wave = refine; D kế = tiến wave, gate wave đang rời); `discovery-end` (không arg, chỉ ở D3) chốt Discovery → DOMAIN_AUTHORING.

| Wave | Agent | Skill primary | Output chính |
|------|-------|---------------|--------------|
| D0 | [discovery-hypothesis-agent](discovery-hypothesis-agent.md) | `discovery-hypothesis` | `docs/discovery/hypothesis-log.md` |
| D1 | [capability-mapper-agent](capability-mapper-agent.md) | `capability-mapping` | `persona-pool.md` + `capability-map.md` |
| D2 | [event-stormer-agent](event-stormer-agent.md) | `event-storming` | `event-storming/ES-*.md` |
| D3 | [charter-author-agent](charter-author-agent.md) | `boundary-charter` | `BOUNDARY-MAP.md` + `boundaries/*/CHARTER.md` + derive `PROJECT.md` + chốt `service_prefix` |

### Domain (3 specialists — 2 lớp business ↔ eng)

`domain-po <EPIC\|FEATURE\|JOURNEY>` · `domain-ba <BR\|PERSONA>` author **BUSINESS plain VN vào `docs/domain/`** (self-loop, status DRAFT) → `domain-approve` **KÝ** (`status: APPROVED`, jargon-check — instant, không spawn) → `domain-translate` **DỊCH sang eng `docs/architecture/`** → `domain-end` (gate `domain_gate` + `planning_lint` + `translation_parity` → DESIGN).

| Agent | Mode | Skill primary | Output chính |
|-------|------|---------------|--------------|
| [domain-po-agent](domain-po-agent.md) | EPIC / FEATURE / JOURNEY | `domain-po` | `docs/domain/{epics,feat,journeys}/` (business, plain VN) |
| [domain-ba-agent](domain-ba-agent.md) | BR / PERSONA | `domain-ba` | `docs/domain/{business-rules,personas}/` (business, plain VN) |
| [domain-translator-agent](domain-translator-agent.md) | dịch toàn bộ doc đã ký | `domain-translator` | `docs/architecture/{epics,feat,business-rules,journeys,personas}/` (eng, frontmatter `source`+`domain_source_id`) |

### Design + Plan (3 specialists — UX tách vai riêng)

| Command | Agent | Skill primary | Output chính |
|---------|-------|---------------|--------------|
| `design` | [solution-architect-agent](solution-architect-agent.md) | `technical-design` | ADR + HLD + API + data-model + events + integrations + infra/docker-compose (KHÔNG UX) |
| `design-ux` | [ux-designer-agent](ux-designer-agent.md) | `ux-design` | `ux/ux-{boundary}.md` + `ux/design-tokens.css` (FE boundary — chạy SAU /domain, consume api-{be}.md) |
| `plan` | [program-planner-agent](program-planner-agent.md) | `implementation-plan` | WAVE-SEQUENCE + wave-*.md + MATRIX + materialize per-boundary dev/fix/KG |

### Review (5 singletons)

| Agent | Command | Skill primary | Mode |
|-------|---------|---------------|------|
| [review-document-agent](review-document-agent.md) | `review-document` | `business-analysis` | revision (feedback) + sanity-check (no arg) |
| [review-backend-agent](review-backend-agent.md) | `review-dev` (kind=backend) | `review-backend` | Review ghi findings + trả open_findings; MAIN spawn fix → re-review |
| [review-bff-agent](review-bff-agent.md) | `review-dev` (kind=bff) | `review-bff` | Same |
| [review-web-agent](review-web-agent.md) | `review-dev` (kind=web) | `review-web` | Same |
| [review-mobile-agent](review-mobile-agent.md) | `review-dev` (kind=mobile) | `review-mobile` | Same |

> Review agents là **singleton per kind** (1 file dùng cho mọi boundary cùng kind).
> Rules/checklist cụ thể nằm trong skill (project-customizable), KHÔNG hardcode trong agent file.

### Operations (7 ops)

| Agent | Command | Skill primary | Stage transition |
|-------|---------|---------------|------------------|
| [start-wave-agent](start-wave-agent.md) | `start-wave` | (none — pure orchestration) | REVIEW → WAVE_OPEN |
| [dev-handoff-agent](dev-handoff-agent.md) | `dev-handoff` | `infra-local-dev` | REVIEW_DEV → DEV_HANDOFF |
| [test-plan-agent](test-plan-agent.md) | `test-plan` | `test-plan` | DEV_HANDOFF → TEST_PLAN |
| [test-execute-agent](test-execute-agent.md) | `test-execute` | `test-execute` | TEST_PLAN → TEST_EXECUTE → (auto) MANUAL_TEST |
| [end-wave-agent](end-wave-agent.md) | `end-wave` | (none) | MANUAL_TEST → DONE |
| [done-wave-agent](done-wave-agent.md) | `done-wave` | `infra-local-dev` | DONE → BOOTSTRAP |

### Side (1)

| Agent | Command | Skill primary | Stage transition |
|-------|---------|---------------|------------------|

## Materialize per-boundary (after /domain)

Sau `plan` + `start-wave`, `materialize.py` gen per boundary:

| Type | File | Template |
|------|------|----------|
| Dev | `agents/dev-{prefix}-{boundary}-agent.md` | [_template-dev-agent.md](_template-dev-agent.md) |
| Fix | `agents/fix-{prefix}-{boundary}-agent.md` | [_template-fix-agent.md](_template-fix-agent.md) |
| KG | `knowledge-base/{boundary}.knowledge-graph.yaml` | [TEMPLATE.knowledge-graph.yaml](../knowledge-base/TEMPLATE.knowledge-graph.yaml) |

> Các file này **không commit sẵn** — sinh khi `start-wave` materialize từ MATRIX. Repo ship "sạch" (MATRIX rỗng cho tới khi `plan`).

## v4 agent file structure

Mỗi agent có 7 sections:

```yaml
---
name: <agent-name>
role: "<role-namespace>:<sub-role>"  # vd "design:solution-architect", "review:backend"
command: <slash-command>              # spawn command
stage: <STAGE|null>                   # stage agent chạy (vd DESIGN, PLAN)
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
