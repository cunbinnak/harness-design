# ADLC Design Harness

Orchestrator framework cho ADLC (Architecture-Driven Lifecycle) workflow. Kết hợp AI agents + người theo state machine + slash commands. Polyrepo: harness repo này điều phối, mỗi boundary scaffolded ở `/start-dev` là 1 repo riêng.

## Quick start

```bash
pip install -r requirements-harness.txt
py scripts/harness.py state    # show current STATE (BOOTSTRAP by default)
```

Fork repo cho project mới:

```bash
py scripts/reset_for_new_project.py    # clear artifacts cũ
py scripts/harness.py state            # verify stage=BOOTSTRAP
```

## Workflow (19 commands, 17 states)

Front-half (intake tách nhỏ — clone ADLC; phủ đủ D0-D7 dạng gộp, xem `CLAUDE.md §ADLC MAPPING`):

```
BOOTSTRAP → /discovery-start D0 "<project description>"
DISC_D0..D3 → /discovery-end <D>  (D0 hypothesis · D1 persona+capability · D2 event-storming · D3 charter+PROJECT.md)
DISC_D3   → DOMAIN_AUTHORING
DOMAIN_AUTHORING → /domain-start <EPIC|FEATURE|JOURNEY|BR|PERSONA> (self-loop) → /domain-end
DESIGN    → /design   (ADR/HLD/API/data-model/UX/events/integrations)
PLAN      → /plan     (WAVE-SEQUENCE + wave-*.md + MATRIX + KG skeleton)
REVIEW    → /review-document "<feedback>" (revise loop) → /approve-document → /start-wave <N>
```

Back-half (wave execution):

```
WAVE_OPEN → /start-dev <boundary>
DEV       → /review-dev   (gate no_open_findings)
REVIEW_DEV → /dev-handoff (gate all_boundaries_reviewed: review pass + coverage theo kind)
DEV_HANDOFF → /test-plan
TEST_PLAN → /test-execute (run + log bug auto, KHÔNG fix)
TEST_EXECUTE → (auto) MANUAL_TEST (pass HAY fail)
MANUAL_TEST → /log-bug "<mô tả>" · /fix-bugs [<bug-id>] (loop) · /end-wave (UAT signed)
DONE      → /done-wave → BOOTSTRAP (next wave)
            /apply-cr <CR-ID> → DESIGN (amendment: /design → /plan → REVIEW)
```

Mỗi command có 2 lệnh:

```bash
py scripts/build_prompt.py <cmd> [opts]          # build self-contained prompt
py scripts/harness.py <cmd> complete '<json>'    # apply gate + transition
```

KHÔNG sửa `harness/STATE.json` thủ công — hook chặn.

## File structure

```
.
├── CLAUDE.md                       Router file (Claude Code primary)
├── AGENTS.md                       Cross-IDE entry (agents.md spec)
├── SETUP-GUIDE.md                  Setup + workflow detail
├── .claude/
│   ├── settings.json              9 hooks + permissions deny
│   ├── commands/                  19 slash commands (synced from commands/)
│   └── skills/                    On-demand skills (project-customizable)
├── harness/
│   ├── STATE.json                 Current stage (chỉ trạng thái hiện tại, no history)
│   ├── STATE-MACHINE.json         17 states + 29 transitions
│   ├── SERVICE-BOUNDARY-MATRIX.json  Boundary metadata + owned_paths
│   └── PROTOCOL.md                Orchestrator ↔ sub-agent protocol
├── agents/
│   ├── _template-{dev,fix}-agent.md   Materialize templates
│   ├── {discovery,domain,design,plan,review,ops,side}-agents (21 singletons)
│   └── dev-{prefix}-{boundary}-agent  (materialized per boundary)
├── commands/                       19 slash command sources
├── scripts/
│   ├── harness.py                 CLI thin wrapper
│   ├── state.py                   STATE manager
│   ├── gates.py                   Pure gate functions
│   ├── build_prompt.py            Self-contained prompt builder
│   ├── materialize.py             Per-boundary artifact generator
│   ├── smoke_test.py              E2E state machine test
│   ├── sync_commands.py           Sync commands/ → .claude/commands/
│   └── hooks/
│       ├── dispatcher.py          Single entry for 9 hook events
│       └── policies.py            Pure check functions
├── docs/
│   ├── discovery/                hypothesis-log + persona-pool + capability-map + event-storming + BOUNDARY-MAP + boundaries/CHARTER (D0-D3)
│   ├── architecture/              PROJECT + epics + feat + journeys + personas + business-rules (DOMAIN) + ADR + HLD + API + data-model + UX + events + integrations + infra (DESIGN)
│   └── plans/                     WAVE-SEQUENCE.md + wave-{N}.md
├── tracking/
│   ├── _templates/                6 templates (test-case-registry/bugs/test-report/qc-signoff/review-findings/cr)
│   └── wave-{N}/                  Per-wave: test cases + report + bugs + signoff + CR
├── knowledge-base/
│   ├── TEMPLATE.knowledge-graph.yaml
│   └── {boundary}.knowledge-graph.yaml  (per boundary)
├── handoff/                        Per-wave handoff docs
└── services/                       Polyrepo working dir (gitignored)
```

## Tài liệu chính

| File | Mục đích |
|------|----------|
| [CLAUDE.md](CLAUDE.md) | Router file cho Claude Code |
| [AGENTS.md](AGENTS.md) | Cross-IDE entry doc |
| [SETUP-GUIDE.md](SETUP-GUIDE.md) | Setup + workflow chi tiết |
| [harness/PROTOCOL.md](harness/PROTOCOL.md) | Orchestrator ↔ sub-agent protocol |
| [agents/README.md](agents/README.md) | Agent inventory |
| [commands/README.md](commands/README.md) | Slash commands flow |
| [tracking/README.md](tracking/README.md) | Per-wave tracking format |
| [knowledge-base/README.md](knowledge-base/README.md) | KG structure |
| [docs/architecture/README.md](docs/architecture/README.md) | Architecture docs |
| [docs/plans/README.md](docs/plans/README.md) | Wave plans |

## Verify install

```bash
py scripts/gates.py            # gates selftest
py scripts/state.py validate   # STATE schema validate
py scripts/smoke_test.py       # E2E state machine (28 assertions)
```

Pass cả 3 → setup OK.
