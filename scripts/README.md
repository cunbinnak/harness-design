# Scripts (v4 kernel)

Python kernel cho ADLC Design Harness. ~10 file core.

## Inventory

| Script | Mục đích | LOC |
|--------|----------|-----|
| `harness.py` | CLI thin wrapper (gọi state.py) | ~60 |
| `state.py` | STATE manager: load/save/validate/transition + history | ~280 |
| `gates.py` | Pure gate functions per command (no side effect) | ~280 |
| `build_prompt.py` | Build self-contained spawn prompt per command | ~430 |
| `materialize.py` | Per-boundary artifact generator (dev/fix/KG từ MATRIX) | ~210 |
| `smoke_test.py` | E2E state machine walkthrough (18 cases) | ~190 |
| `sync_commands.py` | Sync `commands/*.md` → `.claude/commands/` | ~60 |
| `reset_for_new_project.py` | Clear v4 artifacts khi fork repo | ~200 |
| `hooks/dispatcher.py` | Single entry route 9 hook events | ~310 |
| `hooks/policies.py` | Pure check functions cho hooks | ~200 |

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

# Materialize (sau intake step 4)
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
