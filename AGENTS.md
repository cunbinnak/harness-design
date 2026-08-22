# AGENTS.md — ADLC Design Harness

> Entry doc cho AI coding agents (Claude Code, Cursor, Codex, ...).
> Spec: [agents.md](https://agents.md).

## Project

Orchestrator framework triển khai ADLC (Architecture-Driven Lifecycle): Discovery (D0-D3) → Domain (nghiệp vụ plain VN → ký → dịch sang bản kỹ thuật → thiết kế → chia wave) → Review → chạy wave (code/test/dogfood) → khép vòng. AI agent + người theo state machine: **17 state · 26 chốt · 7 lệnh**.

Tech: Python 3.14 (kernel), service stack per-boundary set ở DESIGN (vd Java 21 + Spring Boot, Node + Apollo, React + Vite, Flutter).

## Setup

```bash
pip install -r requirements-harness.txt
py scripts/harness.py state          # show current state
py scripts/state.py validate         # validate config
```

## Commands

**7 lệnh** — `/discover` `/domain` `/approve-document` `/run-wave` `/dogfood` `/next-wave` `/status`.
Mỗi lệnh chạy qua NHIỀU chốt (`harness <chốt> complete`); lệnh tự suy đang đứng ở chốt nào, gọi lại
thì chạy tiếp. Xem [commands/README.md](commands/README.md) để biết flow.

Mỗi command có 2 lệnh:
```bash
py scripts/build_prompt.py <cmd> [options]            # build self-contained prompt
py scripts/harness.py <cmd> complete '<evidence>'     # apply gate + transition state
```

## Code style

- **Python** (kernel): PEP 8, type hints, pure functions cho gates/policies.
- **Markdown** (docs/templates): no emoji, structured frontmatter (YAML), heading hierarchy.
- **JSON** (STATE/MATRIX): indent 2 spaces, sort keys nếu có thể.
- **YAML** (KG, frontmatter): 2 spaces, no tabs.

## Testing

```bash
py scripts/gates.py                  # gates selftest
py scripts/state.py validate         # STATE schema validate
py scripts/smoke_test.py             # E2E state machine walkthrough (36 assertions)
```

## Architecture rules

- **State machine first**: mọi transition qua `harness.py <cmd> complete`, KHÔNG sửa `harness/STATE.json` thủ công.
- **Owned paths**: sub-agent chỉ edit file trong `SERVICE-BOUNDARY-MATRIX.json` owned_paths của boundary mình.
- **Skills on-demand**: rules/conventions sống trong `.claude/skills/`, agent invoke khi cần. KHÔNG hardcode rule vào agent file.
- **Per-boundary KG** (`knowledge-base/{boundary}.knowledge-graph.yaml`): design (entities/BR/events/permissions) **đã seed ở chốt `start-wave`** từ docs; dev/fix/review chỉ **append phần kinh nghiệm** (learnings/decisions/failure_modes) + update design khi implement lệch.

## File structure

```
.
├── CLAUDE.md                       Router file (Claude Code)
├── AGENTS.md                       This file (cross-IDE)
├── .claude/                        Claude Code config
│   ├── settings.json              Hooks + permissions
│   ├── commands/                  Slash commands (synced from commands/)
│   └── skills/                    On-demand skills
├── harness/                        State + protocol kernel
│   ├── STATE.json
│   ├── STATE-MACHINE.json
│   ├── SERVICE-BOUNDARY-MATRIX.json
│   └── PROTOCOL.md
├── agents/                         23 singleton + 2 template + N materialized
├── commands/                       24 command source (synced to .claude/commands/)
├── scripts/                        Python kernel + hooks
├── docs/discovery/                 hypothesis-log + persona-pool + capability-map + event-storming + BOUNDARY-MAP + CHARTER (D0-D3)
├── docs/domain/                    Lớp BUSINESS plain VN: epics + feat + journeys + personas + business-rules (po/ba author + ký)
├── docs/architecture/              PROJECT + bản ENG (dịch từ docs/domain): epics + feat + journeys + personas + business-rules + ADR + HLD + API + data-model + UX + events + integrations (DESIGN)
├── docs/plans/                     WAVE-SEQUENCE + wave-{N}
├── tracking/                       Per-wave test-cases + report + bugs + signoff + CR
├── knowledge-base/                 Per-boundary KG
├── handoff/                        Per-wave handoff docs
└── services/                       Polyrepo working dir (gitignored)
```

## Pull requests

- Commit message: conventional (`feat:`, `fix:`, `refactor:`, `docs:`).
- Mỗi PR scope 1 boundary hoặc 1 cross-cutting concern.
- KHÔNG bypass test với `--no-verify`.
- KHÔNG hardcode secrets.

## Security

- Secrets: env var hoặc secret manager. KHÔNG commit `.env` với production values.
- `.claude/settings.local.json` (gitignored) cho personal config.
- External provider credentials: store ngoài repo, reference qua env var.

## More

- Claude Code primary reference: [CLAUDE.md](CLAUDE.md) (router file với routing table).
- State machine detail: [harness/PROTOCOL.md](harness/PROTOCOL.md).
- Agent inventory: [agents/README.md](agents/README.md).
- Setup detail: [SETUP-GUIDE.md](SETUP-GUIDE.md).
