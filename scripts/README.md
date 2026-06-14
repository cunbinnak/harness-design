# Scripts (v4 kernel)

Python kernel cho ADLC Design Harness. ~10 file core.

## Inventory

| Script | Mục đích |
|--------|----------|
| `harness.py` | CLI thin wrapper (gọi state.py) |
| `state.py` | STATE manager: load/save/validate/transition (no history) |
| `gates.py` | Pure gate functions per command (no side effect) |
| `build_prompt.py` | Build self-contained spawn prompt per command |
| `materialize.py` | Per-boundary artifact generator (dev/fix/KG từ MATRIX) |
| `materialize_matrix.py` | Ghi SERVICE-BOUNDARY-MATRIX.json (stage PLAN, gate stage, validate) |
| `discovery_gate.py` | Gate D0-D3 (port từ ZIP, adapt single-repo) |
| `harness_lib.py` | Shared helper (repo_root/load_json/save_json/utc_now_iso) cho tooling phụ |
| `smoke_test.py` | E2E state machine walkthrough (28 assertions) |
| `sync_commands.py` | Sync `commands/*.md` → `.claude/commands/` |
| `reset_for_new_project.py` | Clear v4 artifacts khi fork repo |
| `hooks/dispatcher.py` | Single entry route 9 hook events |
| `hooks/policies.py` | Pure check functions cho hooks |

> (LOC column bỏ — drift mỗi lần sửa, không có giá trị contract.)

## Entry points

```bash
# CLI workflow
py scripts/harness.py state                          # current STATE summary
py scripts/harness.py can <command>                  # YES/NO check command allowed
py scripts/harness.py <command> complete '<evidence>'  # apply gate + transition

# Build prompts
py scripts/build_prompt.py <command> [options]       # stdout self-contained prompt
py scripts/build_prompt.py <command> --stats         # size breakdown
py scripts/build_prompt.py <command> --save path     # write to file + stdout

# Materialize MATRIX (stage PLAN — MATRIX bị hook chặn Write tay, dùng script này)
py scripts/materialize_matrix.py <boundaries.json>   # gate stage ∈ {BOOTSTRAP,PLAN}, validate, ghi MATRIX
py scripts/materialize_matrix.py --json '[...]' --mode merge   # update theo boundary_id
py scripts/materialize_matrix.py <f>.json --dry-run  # in ra, không ghi
py scripts/materialize_matrix.py --selftest

# Materialize per-boundary artifacts (sau khi có MATRIX)
py scripts/materialize.py                            # all boundaries in MATRIX
py scripts/materialize.py --wave 1                   # filter by wave
py scripts/materialize.py --boundary X --force       # specific boundary, overwrite
py scripts/materialize.py --dry-run                  # show what would write

# Sync commands → IDE
py scripts/sync_commands.py                          # → .claude/commands/
py scripts/sync_commands.py --cursor                 # also → .cursor/commands/

# Reset for new project
py scripts/reset_for_new_project.py                  # interactive (Phase 7+)

# Tests
py scripts/gates.py                                  # gates selftest
py scripts/state.py validate                         # STATE schema validate
py scripts/smoke_test.py                             # E2E state machine
```

## Hooks

```bash
# Hook dispatcher (called by Claude Code framework, not user)
py scripts/hooks/dispatcher.py --event <name>        # event handler

# Events: SessionStart, UserPromptSubmit, Notification, PreCompact,
#         PreToolUse, PostToolUse, SubagentStop, Stop, SessionEnd
```

Detail: [hooks/README.md](hooks/README.md).

## Relationship

```
harness.py  →  state.py  →  gates.py        (CLI flow)
                ↓
            STATE.json (write)

build_prompt.py  →  state.py + load MATRIX  →  stdout prompt
                                              ↓
                                        Agent tool spawn

materialize.py  →  MATRIX + templates  →  gen agents + KG files

hooks/dispatcher.py  →  policies.py + state.py  →  Claude Code response
```

## Liên quan

- [harness/PROTOCOL.md](../harness/PROTOCOL.md) — protocol detail
- [agents/](../agents/) — agent files spawned bởi build_prompt.py
- [commands/](../commands/) — slash command source
- [hooks/README.md](hooks/README.md) — hook implementation detail
