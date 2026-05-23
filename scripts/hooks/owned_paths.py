from __future__ import annotations

from typing import Any

from gate_runner import path_allowed_for_edit


def check(path: str, state: dict[str, Any], hook_cfg: dict[str, Any]) -> tuple[bool, str]:
    if not path:
        return False, "path required"
    if path_allowed_for_edit(path, state, hook_cfg):
        return True, "OK"
    return False, f"edit blocked outside owned_paths/allowlist: {path}"
