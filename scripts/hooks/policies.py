"""
Pure policy functions for harness hooks.

All functions in this module are PURE: no file I/O, no state mutation,
no logging. They take parsed input and return decisions or formatted text.

Used by dispatcher.py which handles I/O.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# ========================================================================
# State formatting (SessionStart, UserPromptSubmit, Notification, PreCompact)
# ========================================================================

def format_state_brief(state: dict, allowed_cmds: list[str]) -> str:
    """Multi-line brief for SessionStart / PreCompact."""
    stage = state.get("stage", "?")
    wave = state.get("wave") or {}
    wave_id = wave.get("id") or "-"
    boundary = state.get("active_boundary") or "-"
    last = state.get("workflow", {}).get("last_completed") or "-"
    lines = [
        f"HARNESS — ADLC Design v4",
        f"  stage         = {stage}",
        f"  wave          = {wave_id}",
        f"  boundary      = {boundary}",
        f"  last_completed= {last}",
        f"  allowed_next  = {allowed_cmds}",
    ]
    return "\n".join(lines)


def state_header_line(state: dict, allowed_cmds: list[str]) -> str:
    """One-line header for UserPromptSubmit / Notification injection."""
    stage = state.get("stage", "?")
    wave = (state.get("wave") or {}).get("id") or "-"
    boundary = state.get("active_boundary") or "-"
    return f"[HARNESS stage={stage} wave={wave} boundary={boundary} allowed={','.join(allowed_cmds)}]"


def memory_marker(state: dict, allowed_cmds: list[str], history_tail: list[dict]) -> str:
    """Pinned summary for PreCompact — keeps state context after compaction."""
    brief = format_state_brief(state, allowed_cmds)
    recent = "\n".join(
        f"  - {h.get('command')}: {h.get('from_stage')} -> {h.get('to_stage')}"
        for h in (history_tail or [])[-3:]
    )
    return f"{brief}\n\nRecent transitions:\n{recent or '  (none)'}"


# ========================================================================
# Protected files (PreToolUse Write|Edit)
# ========================================================================

PROTECTED_PATHS = {
    "harness/STATE.json",
    "harness/STATE-MACHINE.json",
    "harness/SERVICE-BOUNDARY-MATRIX.json",
    ".claude/settings.json",
}


def is_protected_file(rel_path: str) -> bool:
    """Check if path is one of the kernel files that should not be hand-edited."""
    if not rel_path:
        return False
    normalized = rel_path.replace("\\", "/").lstrip("./")
    return normalized in PROTECTED_PATHS


def safe_rel_path(abs_or_rel: str) -> str:
    """Normalize a path to repo-relative if possible; pass through if outside repo."""
    if not abs_or_rel:
        return ""
    p = Path(abs_or_rel.replace("\\", "/"))
    try:
        resolved = p.resolve()
        rel = resolved.relative_to(REPO_ROOT.resolve())
        return str(rel).replace("\\", "/")
    except (ValueError, OSError):
        # Outside repo — return original; not protected
        return str(p).replace("\\", "/")


# ========================================================================
# Bash gate parsing (PreToolUse Bash, PostToolUse Bash)
# ========================================================================

HARNESS_CMD_RE = re.compile(
    r"(?:harness\.py|state\.py)\s+(?:complete\s+)?([\w-]+)\s+complete\b",
    re.IGNORECASE,
)
HARNESS_CMD_RE_ALT = re.compile(
    r"(?:harness\.py|state\.py)\s+([\w-]+)\s+complete\b",
    re.IGNORECASE,
)
JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}")


def parse_harness_complete(bash_cmd: str) -> dict | None:
    """
    Parse a bash command line like:
      py scripts/harness.py dev-handoff complete '{"coverage_pct":85,...}'

    Returns {"command": "dev-handoff", "evidence": {...}} or None.
    """
    if not bash_cmd:
        return None
    m = HARNESS_CMD_RE_ALT.search(bash_cmd)
    if not m:
        return None
    command = m.group(1)
    evidence: dict = {}
    # Try to extract JSON object from the trailing portion
    brace_idx = bash_cmd.find("{")
    if brace_idx >= 0:
        match = JSON_BLOCK_RE.search(bash_cmd[brace_idx:])
        if match:
            try:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    evidence = parsed
            except json.JSONDecodeError:
                pass
    return {"command": command, "evidence": evidence}


# ========================================================================
# RETURN SCHEMA validation (SubagentStop)
# ========================================================================

RETURN_SCHEMA_REQUIRED = [
    "completed",
    "deferred",
    "needs_review",
    "files_changed",
    "build",
    "lint",
    "test",
]


def extract_json_object(text: str) -> dict | None:
    """Find the last balanced JSON object in `text`. Returns parsed dict or None."""
    if not text:
        return None
    # Find candidate substrings; prefer the LAST balanced JSON (final message)
    best: dict | None = None
    for match in JSON_BLOCK_RE.finditer(text):
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                best = parsed
        except json.JSONDecodeError:
            continue
    return best


def validate_return_schema(parsed: dict) -> tuple[bool, list[str]]:
    """Check required fields present in sub-agent RETURN SCHEMA."""
    if not isinstance(parsed, dict):
        return False, ["Not a JSON object"]
    missing = [k for k in RETURN_SCHEMA_REQUIRED if k not in parsed]
    if missing:
        return False, [f"Missing required field: {k}" for k in missing]
    return True, []


# ========================================================================
# Task spawn analysis (PreToolUse Task)
# ========================================================================

DEV_SPAWN_KEYWORDS = ("start-dev", "fix-bugs", "review-dev")


def detect_dev_spawn(task_prompt: str) -> str | None:
    """Detect if a Task spawn looks like a dev-related sub-agent.

    Returns the matched command name or None.
    """
    if not task_prompt:
        return None
    low = task_prompt.lower()
    for kw in DEV_SPAWN_KEYWORDS:
        if kw in low or kw.replace("-", "") in low.replace("-", ""):
            return kw
    return None


def boundary_reminder(boundary: str | None) -> str:
    """One-line reminder for Task spawns of dev agents."""
    if not boundary:
        return "REMINDER: Dev-spawn — ensure boundary is in wave_boundaries."
    return f"REMINDER: Dev-spawn for boundary='{boundary}' — edit only its owned_paths."
