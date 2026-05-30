"""
Single-entry hook dispatcher for ADLC Design Harness.

Claude Code invokes this script with --event <name> and stdin JSON payload.
Dispatcher routes to handlers in policies.py, formats output per Claude Code spec.

Events handled:
  SessionStart, UserPromptSubmit, Notification, PreCompact, SessionEnd
  PreToolUse (Bash | Write|Edit|MultiEdit | Task)
  PostToolUse (Bash)
  SubagentStop, Stop

Error policy: fail-open. If hook code crashes, allow tool call through.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
REPO_ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(HERE))

import policies  # noqa: E402
import state as state_mod  # noqa: E402


# ========================================================================
# Output helpers (Claude Code spec)
# ========================================================================

def _print_json(obj: dict) -> None:
    """Print JSON to stdout (no BOM). Used for Claude Code hook responses."""
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.flush()


def allow_silent() -> int:
    """Default allow: exit 0 with no output."""
    return 0


def pre_tool_deny(reason: str) -> int:
    """PreToolUse hook deny output (Claude Code spec)."""
    _print_json({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    })
    return 0


def stop_block(reason: str) -> int:
    """Stop / SubagentStop block output."""
    _print_json({"decision": "block", "reason": reason})
    return 0


def inject_context(text: str) -> int:
    """SessionStart / UserPromptSubmit / Notification / PreCompact context injection."""
    _print_json({"additionalContext": text})
    return 0


# ========================================================================
# Payload accessors
# ========================================================================

def _read_payload() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw}


def _tool_name(payload: dict) -> str:
    return str(
        payload.get("tool_name")
        or payload.get("toolName")
        or ""
    )


def _tool_input(payload: dict) -> dict:
    ti = payload.get("tool_input") or payload.get("toolInput") or {}
    return ti if isinstance(ti, dict) else {}


def _bash_command(payload: dict) -> str:
    ti = _tool_input(payload)
    return str(ti.get("command") or "")


def _edit_path(payload: dict) -> str:
    ti = _tool_input(payload)
    for key in ("file_path", "filePath", "path"):
        if ti.get(key):
            return policies.safe_rel_path(str(ti[key]))
    return ""


def _task_prompt(payload: dict) -> str:
    ti = _tool_input(payload)
    return str(ti.get("prompt") or ti.get("description") or "")


def _last_assistant_text(payload: dict) -> str:
    for key in (
        "last_assistant_message",
        "lastAssistantMessage",
        "text",
        "response",
        "output",
    ):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return str(payload.get("_raw") or "")


# ========================================================================
# Handlers
# ========================================================================

def handle_session_start(payload: dict) -> int:
    state = state_mod.load_state()
    allowed = state_mod.allowed_commands(state)
    brief = policies.format_state_brief(state, allowed)
    return inject_context(brief)


def handle_user_prompt_submit(payload: dict) -> int:
    state = state_mod.load_state()
    allowed = state_mod.allowed_commands(state)
    return inject_context(policies.state_header_line(state, allowed))


def handle_notification(payload: dict) -> int:
    state = state_mod.load_state()
    allowed = state_mod.allowed_commands(state)
    return inject_context(policies.state_header_line(state, allowed))


def handle_pre_compact(payload: dict) -> int:
    state = state_mod.load_state()
    allowed = state_mod.allowed_commands(state)
    history_tail = state.get("workflow", {}).get("history", [])
    return inject_context(policies.memory_marker(state, allowed, history_tail))


def handle_session_end(payload: dict) -> int:
    """Cleanup: clear stale spawn.active if any."""
    try:
        state = state_mod.load_state()
        spawn = state.get("spawn") or {}
        if spawn.get("active"):
            state["spawn"]["active"] = None
            state_mod.save_state(state, updated_by="session_end_cleanup")
    except Exception:
        pass
    return allow_silent()


# --------- PreToolUse routing ---------

def handle_pre_tool_use(payload: dict) -> int:
    tool = _tool_name(payload)
    if tool == "Bash":
        return _pre_bash(payload)
    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        return _pre_write_edit(payload)
    if tool in ("Task", "Agent", "Subagent"):
        return _pre_task(payload)
    return allow_silent()


def _pre_bash(payload: dict) -> int:
    cmd = _bash_command(payload)
    parsed = policies.parse_harness_complete(cmd)
    if parsed is None:
        return allow_silent()  # not a harness complete call

    command_id = parsed["command"]
    evidence = parsed["evidence"]
    state = state_mod.load_state()

    if not state_mod.can_run(command_id, state):
        allowed = state_mod.allowed_commands(state)
        return pre_tool_deny(
            f"Command '{command_id}' không allowed ở stage '{state['stage']}'. "
            f"Allowed: {allowed}"
        )

    # Gate pre-check (best effort; final gate runs inside state.complete)
    import gates
    ok, errors = gates.check_for_command(command_id, state, evidence)
    if not ok:
        return pre_tool_deny("Gate sẽ fail:\n  - " + "\n  - ".join(errors))

    return allow_silent()


def _pre_write_edit(payload: dict) -> int:
    path = _edit_path(payload)
    if policies.is_protected_file(path):
        return pre_tool_deny(
            f"'{path}' là kernel file. KHÔNG sửa tay — dùng `py scripts/harness.py <cmd> complete '...'` để transition state."
        )
    return allow_silent()


def _pre_task(payload: dict) -> int:
    """Inject reminder for dev-spawn; never block."""
    state = state_mod.load_state()
    spawn = state.get("spawn") or {}
    if spawn.get("active"):
        return pre_tool_deny(
            f"spawn.active != null (currently: {spawn['active'].get('command') if isinstance(spawn['active'], dict) else spawn['active']}). "
            "Wait for current sub-agent to finish, hoặc clear bằng `state.py reset-spawn`."
        )
    # Inject reminder via additionalContext (non-blocking)
    prompt = _task_prompt(payload)
    matched = policies.detect_dev_spawn(prompt)
    if matched:
        boundary = state.get("active_boundary")
        reminder = policies.boundary_reminder(boundary)
        # PreToolUse can also use additionalContext for inject without deny
        _print_json({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "additionalContext": reminder,
            }
        })
        return 0
    return allow_silent()


# --------- PostToolUse (Bash) ---------

def handle_post_tool_use(payload: dict) -> int:
    """After a successful harness complete bash, append checkpoint summary."""
    tool = _tool_name(payload)
    if tool != "Bash":
        return allow_silent()
    cmd = _bash_command(payload)
    parsed = policies.parse_harness_complete(cmd)
    if parsed is None:
        return allow_silent()
    # state.complete() already appends history; nothing more to do here
    # Could log to file for redundancy if needed
    return allow_silent()


# --------- SubagentStop ---------

def handle_subagent_stop(payload: dict) -> int:
    text = _last_assistant_text(payload)
    parsed = policies.extract_json_object(text)
    if parsed is None:
        # Sub-agent didn't return JSON — warn soft (not block per v4 plan)
        return allow_silent()
    ok, errors = policies.validate_return_schema(parsed)
    if not ok:
        # Soft warn — log but don't block (could change to block later)
        sys.stderr.write(
            f"WARN: SubagentStop RETURN SCHEMA invalid: {'; '.join(errors)}\n"
        )
    # Clear spawn.active
    try:
        state = state_mod.load_state()
        state["spawn"]["active"] = None
        state_mod.save_state(state, updated_by="subagent_stop")
    except Exception:
        pass
    return allow_silent()


# --------- Stop (STUB) ---------

def handle_stop(payload: dict) -> int:
    """
    STUB: return allow always.
    TODO: implement build/lint/test runner per kind when service code exists.
    Spec:
      - If stage in [DEV, TEST_EXECUTE] AND turn changed files in services/{prefix-boundary}/,
        run scoped build/lint/test for that kind.
      - On fail: stop_block("<last 40 lines>").
      - On pass: cache git hash to skip on next clean turn.
    """
    return allow_silent()


# ========================================================================
# Main
# ========================================================================

HANDLERS = {
    "SessionStart": handle_session_start,
    "UserPromptSubmit": handle_user_prompt_submit,
    "Notification": handle_notification,
    "PreCompact": handle_pre_compact,
    "SessionEnd": handle_session_end,
    "PreToolUse": handle_pre_tool_use,
    "PostToolUse": handle_post_tool_use,
    "SubagentStop": handle_subagent_stop,
    "Stop": handle_stop,
}


def main() -> int:
    # UTF-8 console on Windows
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--event", required=True, choices=sorted(HANDLERS))
    args = ap.parse_args()

    payload = _read_payload()
    handler = HANDLERS[args.event]

    try:
        return handler(payload)
    except Exception as e:
        # Fail-open: log to stderr, exit 0 (allow tool through)
        sys.stderr.write(f"hook dispatcher error [{args.event}]: {e}\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
