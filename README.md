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

## Workflow (13 commands, 10 states)

```
BOOTSTRAP → /intake-requirement "<project description>"
INTAKE    → /review-document "<feedback>" (revise loop)
            /approve-document
            /start-wave <N>
WAVE_OPEN → /start-dev <boundary>
DEV       → /review-dev
REVIEW_DEV → /dev-handoff (coverage>=80, infra ok)
DEV_HANDOFF → /test-plan
TEST_PLAN → /test-execute (auto, internal fix loop)
TEST_EXECUTE → (auto) MANUAL_TEST
MANUAL_TEST → /fix-bugs <bug-id> (loop)
              /end-wave (UAT signed)
DONE      → /done-wave → BOOTSTRAP (next wave)
            /apply-cr <CR-ID> → INTAKE (amendment)
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
│   ├── commands/                  13 slash commands (synced from commands/)
│   └── skills/                    On-demand skills (project-customizable)
├── harness/
│   ├── STATE.json                 Current stage + workflow history
│   ├── STATE-MACHINE.json         10 states + 14 transitions
│   ├── SERVICE-BOUNDARY-MATRIX.json  Boundary metadata + owned_paths
│   └── PROTOCOL.md                Orchestrator ↔ sub-agent protocol
├── agents/
│   ├── _template-{dev,fix}-agent.md   Materialize templates
│   ├── {intake,review,ops,side}-agents (16 singletons)
│   └── dev-{prefix}-{boundary}-agent  (materialized per boundary)
├── commands/                       13 slash command sources
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
│   ├── architecture/              PROJECT + FEAT + ADR + HLD + API + data-model + UX + events + integrations + infra
│   └── plans/                     WAVE-SEQUENCE.md + wave-{N}.md
├── tracking/
│   ├── _templates/                5 templates (test/bugs/signoff/cr)
│   └── wave-{N}/                  Per-wave: test cases + report + bugs + signoff + CR
├── knowledge-base/
│   ├── TEMPLATE.boundary-kg.yaml
│   └── {prefix}-{boundary}.knowledge-graph.yaml  (per boundary)
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
py scripts/smoke_test.py       # E2E state machine (18 cases)
```

Pass cả 3 → setup OK.
