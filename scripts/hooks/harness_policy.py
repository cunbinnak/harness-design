"""Central harness allow/deny for shell commands — no bypass."""

from __future__ import annotations

import re
from typing import Any

from harness_lib import repo_root

HARNESS_DENY_PREFIX = "HARNESS — KHÔNG ĐƯỢC PHÉP. Dừng ngay."

HARNES_COMPLETE = re.compile(
    r"(?:harness\.py|scripts/harness\.py)\s+(\S+)\s+complete\b",
    re.I,
)
BUILD_PROMPT = re.compile(
    r"build_command_prompt\.py\s+([\w-]+)",
    re.I,
)
STATE_WRITE = re.compile(
    r"state_engine\.py\s+(apply_transition|save|patch)\b",
    re.I,
)
STATE_READ = re.compile(
    r"state_engine\.py\s+(validate|show|can)\b",
    re.I,
)
HARNESS_READ = re.compile(
    r"harness\.py\s+(state|can)\b",
    re.I,
)

INTAKE_AUX = re.compile(
    r"(materialize_boundary_agents|materialize_knowledge_graphs|sync_matrix_from_roster)\.py",
    re.I,
)


def deny_message(command: str, allowed: list[str], detail: str) -> str:
    return (
        f"{HARNESS_DENY_PREFIX}\n"
        f"Bước `{command}` không được phép.\n"
        f"workflow.allowed_next = {allowed!r}\n"
        f"{detail}\n"
        "Không được: sửa harness/STATE.json thủ công, complete lệch bước, "
        "hay spawn agent của bước khác để lách gate."
    )


def _fe_boundaries_from_roster(root) -> list[str]:
    roster = root / "docs/plans/project/agent-roster.md"
    if not roster.is_file():
        return []
    from materialize_boundary_agents import parse_roster_row  # noqa: WPS433

    return [r.boundary_id for r in parse_roster_row(roster) if r.layer == "fe"]


def check_shell_allowed(cmdline: str, state: dict[str, Any]) -> tuple[bool, str]:
    cmd = (cmdline or "").strip()
    if not cmd:
        return True, "OK"

    wf = state.get("workflow") or {}
    allowed = list(wf.get("allowed_next") or ["intake-requirement"])

    if STATE_READ.search(cmd) or HARNESS_READ.search(cmd):
        return True, "OK"

    if STATE_WRITE.search(cmd):
        return False, deny_message(
            "state_engine (write)",
            allowed,
            "Chỉ harness.py complete được cập nhật STATE.",
        )

    m = HARNES_COMPLETE.search(cmd)
    if m:
        cid = m.group(1)
        if cid not in allowed:
            return False, deny_message(cid, allowed, "Chỉ được complete đúng bước trong allowed_next.")
        return True, "OK"

    m = BUILD_PROMPT.search(cmd)
    if m:
        cid = m.group(1)
        if cid == "intake-requirement" and "intake-requirement" in allowed:
            return True, "OK"
        if cid in allowed:
            return True, "OK"
        if cid in ("start-dev", "fix-bugs", "review-dev") and cid in allowed:
            return True, "OK"
        return False, deny_message(
            f"build_command_prompt {cid}",
            allowed,
            "Không spawn prompt của command chưa được phép.",
        )

    if INTAKE_AUX.search(cmd):
        if "intake-requirement" in allowed:
            return True, "OK"
        return False, deny_message(
            "materialize (intake)",
            allowed,
            "Chỉ chạy materialize trong lúc intake-requirement đang allowed.",
        )

    return True, "OK"


def fe_boundary_ids(root=None) -> list[str]:
    root = root or repo_root()
    ids = _fe_boundaries_from_roster(root)
    return ids if ids else ["fe"]
