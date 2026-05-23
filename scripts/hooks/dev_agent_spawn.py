"""Hook: dev spawn commands require agent file on disk."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from harness_lib import repo_root

PREFIX = {"start-dev": "", "fix-bugs": "fix-", "review-dev": "review-"}


def check(command: str, boundary_id: str, hook: dict[str, Any]) -> tuple[bool, str]:
    if command not in (hook.get("commands") or []):
        return True, "OK"
    if not boundary_id:
        return False, "dev_agent_spawn: boundary_id required in payload"
    prefix = PREFIX.get(command, "")
    rel = f"agents/{prefix}{boundary_id}-agent.md"
    path = repo_root() / rel
    if not path.is_file():
        return False, f"dev_agent_spawn: missing {rel} — run intake/plan materialize first"
    return True, "OK"
