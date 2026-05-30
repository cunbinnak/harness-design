# Hooks (v4)

Hook implementation cho ADLC Design Harness. Pure-function policies + single dispatcher entry.

## Cấu trúc

```
scripts/hooks/
├── README.md
├── __init__.py
├── dispatcher.py    Single entry — route 9 events tới handler
└── policies.py      Pure check functions (no side effect)
```

## 9 events

Tất cả route qua `dispatcher.py --event <name>`. Config trong `.claude/settings.json`.

| Event | Matcher | Behavior |
|-------|---------|----------|
| SessionStart | startup\|resume | Inject brief STATE đầu session |
| UserPromptSubmit | * | Inject `[HARNESS stage=X ...]` header mỗi turn |
| Notification | * | Inject state header |
| PreCompact | * | Pin STATE summary + 3 recent transitions trước compaction |
| PreToolUse | Bash | Check `harness <X> complete` gate; deny nếu sai |
| PreToolUse | Write\|Edit\|MultiEdit | Block protected files (STATE.json, STATE-MACHINE.json, settings.json) |
| PreToolUse | Task | KHÔNG block theo stage; inject boundary reminder cho dev-spawn |
| PostToolUse | Bash | Append checkpoint sau `harness complete` success |
| SubagentStop | * | Parse RETURN SCHEMA JSON, validate fields |
| Stop | * | (stub — sẽ implement build/lint/test runner per kind sau) |
| SessionEnd | * | Cleanup `spawn.active` nếu stale |

## Output format (Claude Code spec)

**Allow** (silent): exit 0 với stdout rỗng.

**Deny** (PreToolUse):
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "..."
  }
}
```

**Inject context** (SessionStart / UserPromptSubmit / PreCompact / Notification):
```json
{"additionalContext": "..."}
```

**Block** (Stop / SubagentStop):
```json
{"decision": "block", "reason": "..."}
```

## Fail-open policy

Hook crash → exit 0 (allow tool through). Lý do: hook v4 đang stable hóa; bug trong policy không nên block user.

```python
try:
    handler(payload)
except Exception as e:
    sys.stderr.write(f"hook dispatcher error [{event}]: {e}\n")
    return 0  # fail-open
```

## Policies (pure functions)

`policies.py` chứa 5 nhóm:

| Nhóm | Functions | Dùng ở event |
|------|-----------|--------------|
| State formatting | `format_state_brief`, `state_header_line`, `memory_marker` | SessionStart, UserPromptSubmit, PreCompact, Notification |
| Protected files | `is_protected_file`, `safe_rel_path` | PreToolUse(Write\|Edit) |
| Bash gate | `parse_harness_complete` | PreToolUse(Bash), PostToolUse(Bash) |
| Return schema | `extract_json_object`, `validate_return_schema` | SubagentStop |
| Task spawn | `detect_dev_spawn`, `boundary_reminder` | PreToolUse(Task) |

## Debug

Test 1 event với mock stdin:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"py scripts/harness.py start-dev complete {\"boundary\":\"x\"}"}}' \
  | py scripts/hooks/dispatcher.py --event PreToolUse
```

Output JSON nếu deny, empty nếu allow.

## Liên quan

- Hook config: [`../../.claude/settings.json`](../../.claude/settings.json)
- Protocol: [`../../harness/PROTOCOL.md`](../../harness/PROTOCOL.md)
- State machine: [`../../harness/STATE-MACHINE.json`](../../harness/STATE-MACHINE.json)
