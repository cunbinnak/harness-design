"""Hook: command must be in workflow.allowed_next."""

from __future__ import annotations

from typing import Any


def check(command: str, state: dict[str, Any]) -> tuple[bool, str]:
    wf = state.get("workflow") or {}
    allowed = wf.get("allowed_next") or ["start-wave"]
    if command not in allowed:
        return False, f"workflow_allowed_next: {command!r} not in {allowed!r} — cannot bypass sequence"
    return True, "OK"
