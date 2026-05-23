from __future__ import annotations

from typing import Any

from gate_runner import check_command


def check(command_id: str, state: dict[str, Any], evidence: dict[str, Any] | None = None) -> tuple[bool, list[str]]:
    result = check_command(command_id, state, evidence)
    return result["ok"], result["errors"]
