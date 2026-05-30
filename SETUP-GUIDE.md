# Harness Setup Guide

ADLC Design Harness v4 — bộ khung orchestrator cho workflow ADLC.

## Prerequisites

- Python 3.14+
- Docker (cho dev/test infra)
- Git
- IDE: VSCode (recommend) hoặc Cursor

```bash
pip install -r requirements-harness.txt
py scripts/harness.py state    # show current STATE (default: BOOTSTRAP)
```

## First-time setup (fork repo)

Khi fork repo cho project mới:

```bash
# 1. Clone
git clone <fork-url>
cd <project>

# 2. (Optional) Reset state nếu có artifacts cũ
py scripts/reset_for_new_project.py

# 3. Verify state
py scripts/harness.py state
# stage: BOOTSTRAP
# allowed_commands: [intake-requirement]
```

## Daily workflow

Mỗi command có 2 lệnh:

```bash
# 1. Build self-contained prompt cho sub-agent
py scripts/build_prompt.py <command> [options]

# 2. Apply gate + transition state (sau khi sub-agent done)
py scripts/harness.py <command> complete '<json-evidence>'
```

Check state trước mỗi command:

```bash
py scripts/harness.py state
py scripts/harness.py can <command>    # YES/NO command có được allowed
```

KHÔNG sửa `harness/STATE.json` tay — hook chặn.

## Workflow sequence (13 commands)

```
BOOTSTRAP
   ↓ /intake-requirement "<project description>"
INTAKE
   ↓ /review-document "<feedback>" (revision loop)
   ↓ /approve-document (set approved=true)
   ↓ /start-wave <N>
WAVE_OPEN
   ↓ /start-dev <boundary>
DEV
   ↓ /review-dev (internal fix loop)
REVIEW_DEV
   ↓ /dev-handoff (verify infra + coverage)
DEV_HANDOFF
   ↓ /test-plan
TEST_PLAN
   ↓ /test-execute (internal fix loop)
TEST_EXECUTE
   ↓ (auto) test_result=pass
MANUAL_TEST
   ↓ /fix-bugs <bug-id> (chain fix + review verify, loop)
   ↓ /end-wave (UAT signed)
DONE
   ├ /done-wave → BOOTSTRAP (next wave)
   └ /apply-cr <CR-ID> → INTAKE (amendment)
```

## Intake (4-step pipeline)

`/intake-requirement` — Claude main spawn 4 specialists tuần tự (flat orchestration, no orchestrator agent):

| Step | Specialist | Skill | Output |
|------|-----------|-------|--------|
| 1 | requirement-analyst | requirement-analysis | PROJECT.md + FEAT-*.md draft + service_prefix |
| 2 | business-analyst | business-analysis | FEAT refined (AC + BR + boundaries_suggested) |
| 3 | solution-architect | technical-design | ADR + HLD + API + data-model + UX + events + integrations + infra/docker-compose |
| 4 | program-planner | implementation-plan | WAVE-SEQUENCE + wave-001 + MATRIX + materialize per-boundary agents/KG |

```bash
/intake-requirement "CRM cho công ty bán nhựa HDPE multi-tenant"
# → Claude main runs 4 specialists sequentially, sub-agents produce docs
# → User reviews docs
/review-document "PROJECT.md thiếu NFR security"
# → review-document-agent revises
/approve-document
# → sets approved=true
/start-wave 1
# → materialize per-boundary, transition WAVE_OPEN
```

## Dev cycle

```bash
/start-dev order-mgmt
# → spawn dev-{prefix}-order-mgmt-agent, scaffold services/, code

/review-dev
# → spawn review-backend-agent (kind detected from MATRIX)
# → internal loop: review → spawn fix sub-agent → re-review → pass

/dev-handoff
# → verify infra docker-compose + coverage + smoke functional
```

## Test cycle

```bash
/test-plan
# → spawn test-plan-agent → write tracking/wave-{N}/test-case-registry.md

/test-execute
# → build local, run auto test với proof
# → fail → log bug → spawn fix → re-test (internal loop)
# → pass → auto-transition MANUAL_TEST
```

## UAT + Close

```bash
# Stakeholder UAT manually, log results vào tracking/wave-{N}/qc-signoff.md
# Phát hiện bug?
/fix-bugs BUG-001
# → chain fix + review verify

/end-wave
# → mark UAT signed, transition DONE

/done-wave
# → teardown infra, archive, reset BOOTSTRAP
```

## Change Request flow

```bash
# 1. Tạo CR file
cp tracking/_templates/TEMPLATE.cr.md tracking/wave-002/change-requests/CR-001-add-payment.md
# Edit CR file: scope, rationale, ...

# 2. State phải = DONE (sau done-wave hoặc end-wave)
/apply-cr CR-001
# → analyze impact, transition INTAKE (amendment mode)

# 3. Re-run intake amendment
/intake-requirement
# → only updates affected files per CR
/review-document "..."
/approve-document
/start-wave 2    # next wave với scope updated
```

## Gate checklist (summary)

| Command | Main evidence |
|---------|--------------|
| `intake-requirement` | `step >= 1` |
| `review-document` | `feedback_processed: true` |
| `approve-document` | `approved: true` |
| `start-wave` | `approved: true` + `wave_n >= 1` |
| `start-dev` | `boundary` ∈ wave_boundaries |
| `dev-handoff` | `coverage_pct >= 80` + `review_result: pass` |
| `test-plan` | `docker_compose_ok: true` |
| `test-execute` | `test_cases_count >= 1` + `test_result: pass` (auto) |
| `fix-bugs` | `bug_id` non-empty |
| `end-wave` | `uat_signed: true` + `no_open_bugs` |
| `done-wave` | `teardown_ok: true` |
| `apply-cr` | `cr_id` non-empty (chỉ từ DONE state) |

Chi tiết: xem [harness/PROTOCOL.md](harness/PROTOCOL.md).

## Hooks

Hook config: `.claude/settings.json` (9 events, đã wire ở Step 9 rebuild).

| Event | Behavior |
|-------|----------|
| SessionStart | Brief STATE đầu session |
| UserPromptSubmit | Inject `[HARNESS stage=X ...]` mỗi turn |
| PreToolUse(Bash) | Check gate khi `harness <X> complete` |
| PreToolUse(Write\|Edit) | Block protected files (STATE.json, STATE-MACHINE.json, settings.json) |
| PreToolUse(Task) | KHÔNG block theo stage; inject boundary reminder |
| PostToolUse(Bash) | Append checkpoint sau complete success |
| SubagentStop | Validate RETURN SCHEMA JSON |
| PreCompact | Pin STATE summary trước compact |
| SessionEnd | Cleanup spawn.active stale |

Vi phạm → hook print error rõ và refuse.

## Key paths

| Path | Role |
|------|------|
| `harness/STATE.json` | Current stage + workflow history |
| `harness/STATE-MACHINE.json` | 10 states + 14 transitions |
| `harness/SERVICE-BOUNDARY-MATRIX.json` | Boundary metadata + owned_paths |
| `harness/PROTOCOL.md` | Orchestrator ↔ sub-agent protocol |
| `scripts/harness.py` | CLI entry |
| `scripts/state.py` | STATE manager |
| `scripts/gates.py` | Pure gate functions |
| `scripts/build_prompt.py` | Build self-contained spawn prompt |
| `scripts/materialize.py` | Per-boundary artifact generator |
| `scripts/hooks/dispatcher.py` | Hook event router |
| `agents/` | Agent inventory (singleton + materialized) |
| `commands/` | Slash command source (synced to `.claude/commands/`) |
| `.claude/skills/` | On-demand skills (project-customizable) |
| `docs/architecture/` | PROJECT + FEAT + ADR + HLD + API + data-model + UX + events + integrations |
| `docs/plans/` | WAVE-SEQUENCE + wave-{N} |
| `tracking/wave-{N}/` | Per-wave test/bugs/signoff + CR |
| `knowledge-base/` | Per-boundary KG yaml |

## Troubleshooting

### `state.py validate` fail

- Check `harness/STATE.json` schema matches `STATE-MACHINE.json[version]`.
- Compare with `git show pre-rebuild-{date}:harness/STATE.json` để biết baseline.

### Hook block command

- Read error message — hook print lý do cụ thể.
- KHÔNG bypass bằng sửa STATE.json — fix underlying issue (vd add evidence missing).

### Sub-agent return không phải JSON

- Check agent file RETURN SCHEMA section — sub-agent failed to follow.
- Hook SubagentStop warn (không block) — user manually verify return text.

### Skill không load

- Verify path: `.claude/skills/<skill-name>/SKILL.md` (không root `skills/`).
- Reload Claude Code session.
- Check skill frontmatter `name:` match.

## More

- Router file (Claude Code): [CLAUDE.md](CLAUDE.md)
- Cross-IDE entry: [AGENTS.md](AGENTS.md)
- Protocol detail: [harness/PROTOCOL.md](harness/PROTOCOL.md)
- Agent inventory: [agents/README.md](agents/README.md)
- Commands flow: [commands/README.md](commands/README.md)
