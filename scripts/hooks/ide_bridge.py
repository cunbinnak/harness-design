#!/usr/bin/env python3
"""IDE hook bridge — Cursor + Claude Code → harness HOOK-RULES.

Reads JSON stdin from IDE hook event, calls harness hook logic, returns IDE-specific output.

Usage:
  python scripts/hooks/ide_bridge.py --ide auto --event pre_edit
  python scripts/hooks/ide_bridge.py --ide claude --event pre_shell
  python scripts/hooks/ide_bridge.py --ide cursor --event post_agent

Events: pre_edit | pre_shell | pre_spawn | post_agent | session_start
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPTS))

from harness_lib import load_json, repo_root  # noqa: E402
from state_engine import load_state  # noqa: E402

HARNES_CMD = re.compile(
    r"(?:harness\.py|state_engine\.py)\s+(?:complete-command\s+)?(\S+)\s+complete",
    re.I,
)
EVIDENCE_FILE = re.compile(r"([\w./\\-]+\.json)\s*$", re.I)
JSON_BLOCK = re.compile(r"\{[\s\S]*\}")


def _read_stdin() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw}


def _detect_ide(explicit: str, payload: dict[str, Any]) -> str:
    if explicit and explicit != "auto":
        return explicit
    if payload.get("hook_event_name") or payload.get("hookEventName"):
        return "claude"
    if payload.get("conversation_id") or payload.get("cursor_session_id"):
        return "cursor"
    if "tool_name" in payload and "hook_event_name" not in payload:
        # Cursor preToolUse also has tool_name — weak signal
        if payload.get("event") in ("preToolUse", "stop", "sessionStart"):
            return "cursor"
    return "claude" if payload.get("session_id") else "cursor"


def _rel_path(path: str) -> str:
    if not path:
        return ""
    p = Path(path.replace("\\", "/"))
    try:
        root = repo_root().resolve()
        return str(p.resolve().relative_to(root)).replace("\\", "/")
    except ValueError:
        s = str(p).replace("\\", "/")
        for marker in ("/adlc-design/", "adlc-design/"):
            if marker in s:
                return s.split(marker, 1)[-1]
        return s.lstrip("/")


def _tool_name(payload: dict[str, Any]) -> str:
    return str(
        payload.get("tool_name")
        or payload.get("toolName")
        or payload.get("tool")
        or ""
    )


def _tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    ti = payload.get("tool_input") or payload.get("toolInput") or payload.get("input")
    if isinstance(ti, dict):
        return ti
    return {}


def _edit_path(payload: dict[str, Any]) -> str:
    ti = _tool_input(payload)
    for key in ("file_path", "filePath", "path", "target_file", "targetFile"):
        val = ti.get(key)
        if val:
            return _rel_path(str(val))
    return ""


def _shell_command(payload: dict[str, Any]) -> str:
    ti = _tool_input(payload)
    for key in ("command", "cmd"):
        if ti.get(key):
            return str(ti[key])
    return str(payload.get("command") or payload.get("shell_command") or "")


def _hook_rules() -> dict[str, Any]:
    return load_json(repo_root() / "harness" / "HOOK-RULES.json")


def _deny(ide: str, event: str, message: str) -> None:
    msg = message.strip()
    if ide == "claude":
        if event == "pre_edit":
            out = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": msg,
                }
            }
            print(json.dumps(out, ensure_ascii=False))
            sys.exit(0)
        if event in ("post_agent",):
            print(json.dumps({"decision": "block", "reason": msg}, ensure_ascii=False))
            sys.exit(0)
        print(msg, file=sys.stderr)
        sys.exit(2)
    # Cursor
    if event == "pre_edit":
        print(
            json.dumps(
                {
                    "permission": "deny",
                    "user_message": msg,
                    "agent_message": msg,
                },
                ensure_ascii=False,
            )
        )
        sys.exit(2)
    if event == "post_agent":
        print(json.dumps({"followup_message": msg}, ensure_ascii=False))
        sys.exit(2)
    print(msg, file=sys.stderr)
    sys.exit(2)


def _allow(ide: str) -> None:
    if ide == "cursor":
        print(json.dumps({"permission": "allow"}))
    sys.exit(0)


def handle_pre_edit(payload: dict[str, Any], ide: str) -> None:
    path = _edit_path(payload)
    if not path:
        _allow(ide)
    rules = _hook_rules()
    hook = rules.get("hooks", {}).get("owned_paths", {})
    from hooks.owned_paths import check  # noqa: WPS433

    state = load_state()
    ok, msg = check(path, state, hook)
    if not ok:
        _deny(ide, "pre_edit", msg)
    _allow(ide)


def _parse_harness_complete(cmd: str) -> tuple[str, dict[str, Any]] | None:
    m = HARNES_CMD.search(cmd)
    if not m:
        return None
    command_id = m.group(1)
    evidence: dict[str, Any] = {}
    em = EVIDENCE_FILE.search(cmd.strip())
    if em:
        ev_path = repo_root() / em.group(1).replace("\\", "/")
        if ev_path.is_file():
            try:
                evidence = json.loads(ev_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
    else:
        brace = cmd.find("{")
        if brace >= 0:
            blob = _extract_json(cmd[brace:])
            if isinstance(blob, dict):
                evidence = blob
    return command_id, evidence


def _extract_json(text: str) -> dict[str, Any] | None:
    m = JSON_BLOCK.search(text)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def handle_pre_shell(payload: dict[str, Any], ide: str) -> None:
    cmd = _shell_command(payload)
    if not cmd:
        _allow(ide)

    parsed = _parse_harness_complete(cmd)
    if not parsed:
        _allow(ide)

    command_id, evidence = parsed
    state = load_state()
    rules = _hook_rules()

    from hooks.workflow_allowed import check as wf_check  # noqa: WPS433

    ok, msg = wf_check(command_id, state)
    if not ok:
        _deny(ide, "pre_shell", msg)

    from hooks.evidence_schema import check as ev_check  # noqa: WPS433

    ok, msg = ev_check(command_id, evidence, rules.get("command_evidence_schema", {}))
    if not ok:
        _deny(ide, "pre_shell", msg)

    from gate_runner import check_command  # noqa: WPS433

    result = check_command(command_id, state, evidence)
    if not result["ok"]:
        _deny(ide, "pre_shell", "Gates failed:\n" + "\n".join(result["errors"]))
    _allow(ide)


def _boundary_from_text(text: str) -> str | None:
    if not text:
        return None
    m = re.search(r"--boundary\s+([a-z][a-z0-9_-]*)", text, re.I)
    if m:
        return m.group(1).lower()
    m = re.search(r"boundary[_\s:=]+([a-z][a-z0-9_-]*)", text, re.I)
    if m:
        return m.group(1).lower()
    return None


def handle_pre_spawn(payload: dict[str, Any], ide: str) -> None:
    state = load_state()
    rules = _hook_rules()

    spawn = state.get("spawn") or {}
    if spawn.get("active"):
        _deny(ide, "pre_spawn", "spawn.active must be null before new spawn")

    ti = _tool_input(payload)
    blob = json.dumps(ti, ensure_ascii=False)
    boundary = _boundary_from_text(blob) or state.get("active_boundary")
    tool = _tool_name(payload)

    if tool in ("Task", "Agent", "Subagent", "SubagentStart") or payload.get("hook_event_name") == "SubagentStart":
        hook = rules.get("hooks", {}).get("dev_agent_spawn", {})
        from hooks.dev_agent_spawn import check as dev_check  # noqa: WPS433

        for cmd in ("start-dev", "fix-bugs", "review-dev"):
            if cmd.replace("-", "") in blob.replace("-", "").lower() or cmd in blob:
                if boundary:
                    ok, msg = dev_check(cmd, boundary, hook)
                    if not ok:
                        _deny(ide, "pre_spawn", msg)
                break

    _allow(ide)


def _last_agent_text(payload: dict[str, Any]) -> str:
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


def handle_post_agent(payload: dict[str, Any], ide: str) -> None:
    state = load_state()
    spawn = state.get("spawn") or {}
    if not spawn.get("active"):
        _allow(ide)

    text = _last_agent_text(payload)
    body = _extract_json(text)
    if body is None:
        _deny(
            ide,
            "post_agent",
            "spawn.active set: last message must be JSON RETURN SCHEMA (harness/PROTOCOL.md)",
        )

    rules = _hook_rules()
    hook = rules.get("hooks", {}).get("return_schema", {})
    from hooks.return_schema import check  # noqa: WPS433

    ok, msg = check(body, hook)
    if not ok:
        _deny(ide, "post_agent", f"RETURN SCHEMA invalid: {msg}")
    _allow(ide)


def handle_session_start(payload: dict[str, Any], ide: str) -> None:
    # Non-blocking: log harness readiness
    try:
        state = load_state()
        wf = state.get("workflow") or {}
        print(
            json.dumps(
                {
                    "harness": {
                        "stage": state.get("stage"),
                        "allowed_next": wf.get("allowed_next"),
                        "wave": (state.get("wave") or {}).get("id"),
                    }
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
    except Exception as exc:
        print(f"harness session_start: {exc}", file=sys.stderr)
    _allow(ide)


HANDLERS = {
    "pre_edit": handle_pre_edit,
    "pre_shell": handle_pre_shell,
    "pre_spawn": handle_pre_spawn,
    "post_agent": handle_post_agent,
    "session_start": handle_session_start,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ide", default="auto", choices=["auto", "cursor", "claude"])
    ap.add_argument("--event", required=True, choices=sorted(HANDLERS))
    args = ap.parse_args()

    payload = _read_stdin()
    ide = _detect_ide(args.ide, payload)
    try:
        HANDLERS[args.event](payload, ide)
    except FileNotFoundError as exc:
        _deny(ide, args.event, f"harness file missing: {exc}")
    except Exception as exc:
        _deny(ide, args.event, f"harness hook error: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
