"""Hook: command must be in workflow.allowed_next."""

from __future__ import annotations

from typing import Any


def check(command: str, state: dict[str, Any]) -> tuple[bool, str]:
    wf = state.get("workflow") or {}
    allowed = wf.get("allowed_next") or ["start-wave"]
    if command not in allowed:
        return (
            False,
            "HARNESS — KHÔNG ĐƯỢC PHÉP. Dừng ngay.\n"
            f"Command {command!r} không nằm trong workflow.allowed_next = {allowed!r}.\n"
            "Không được sửa STATE.json, không complete lệch bước, "
            "không spawn agent bước khác để lách gate.",
        )
    return True, "OK"
