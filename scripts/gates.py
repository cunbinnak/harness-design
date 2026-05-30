"""
Pure gate functions for ADLC harness command evidence checking.

All functions are PURE: take input → return (ok: bool, message: str).
NO side effects (no file write, no STATE mutation, no logging).

Used by scripts/state.py during `complete` to verify transition is allowed.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent


# ========================================================================
# Primitive checks
# ========================================================================

def check_flag(evidence: dict, field: str, expected: Any) -> tuple[bool, str]:
    """Check evidence[field] == expected."""
    val = evidence.get(field)
    if val == expected:
        return True, ""
    return False, f"evidence.{field}={val!r}, cần {expected!r}"


def check_coverage(evidence: dict, min_pct: int, field: str = "coverage_pct") -> tuple[bool, str]:
    """Check evidence[field] >= min_pct (numeric)."""
    val = evidence.get(field, 0)
    if isinstance(val, (int, float)) and val >= min_pct:
        return True, ""
    return False, f"evidence.{field}={val} < {min_pct}"


def check_int_min(evidence: dict, field: str, min_val: int) -> tuple[bool, str]:
    """Check evidence[field] is int >= min_val."""
    val = evidence.get(field, 0)
    try:
        val = int(val)
    except (TypeError, ValueError):
        return False, f"evidence.{field}={val!r} không phải int"
    if val >= min_val:
        return True, ""
    return False, f"evidence.{field}={val} < {min_val}"


def check_non_empty(evidence: dict, field: str) -> tuple[bool, str]:
    """Check evidence[field] is truthy (non-empty string / non-zero / non-empty list)."""
    val = evidence.get(field)
    if val:
        return True, ""
    return False, f"evidence.{field} không có giá trị"


def check_artifact_glob(pattern: str, min_count: int = 1, root: Path | None = None) -> tuple[bool, str]:
    """Check số file match glob pattern >= min_count (relative to REPO_ROOT)."""
    root = root or REPO_ROOT
    files = list(root.glob(pattern))
    if len(files) >= min_count:
        return True, ""
    return False, f"glob '{pattern}' chỉ {len(files)} file, cần ≥ {min_count}"


def check_in_state_list(evidence: dict, field: str, state: dict, state_field: str) -> tuple[bool, str]:
    """Check evidence[field] ∈ state[state_field] (list)."""
    val = evidence.get(field)
    allowed = state.get(state_field, [])
    if val in allowed:
        return True, ""
    return False, f"evidence.{field}={val!r} không trong state.{state_field}={allowed}"


def check_file_exists(path: str, root: Path | None = None) -> tuple[bool, str]:
    """Check file tồn tại."""
    root = root or REPO_ROOT
    target = root / path
    if target.is_file():
        return True, ""
    return False, f"File '{path}' không tồn tại"


def check_no_open_bugs(state: dict) -> tuple[bool, str]:
    """Parse tracking/wave-{N}/bugs.md, count bug có status != closed/fixed."""
    wave_id = (state.get("wave") or {}).get("id")
    if not wave_id:
        return True, ""  # no wave → no bugs
    bugs_file = REPO_ROOT / "tracking" / wave_id / "bugs.md"
    if not bugs_file.exists():
        return True, ""  # no bugs.md → no open bugs
    text = bugs_file.read_text(encoding="utf-8")
    # Heading "## BUG-NNN ..." with frontmatter line "status: open|fixed|closed"
    pattern = re.compile(
        r"^##\s+(BUG-\d+)[^\n]*\n(?:.*\n)*?status:\s*(\w+)",
        re.MULTILINE,
    )
    open_bugs = []
    for match in pattern.finditer(text):
        bug_id, status = match.group(1), match.group(2).lower()
        if status not in ("closed", "fixed"):
            open_bugs.append(bug_id)
    if open_bugs:
        return False, f"còn {len(open_bugs)} bug open: {open_bugs}"
    return True, ""


# ========================================================================
# Rule dispatch
# ========================================================================

# Per-command gate rules. Each rule = {kind, ...params}.
# kind ∈ {flag, coverage, int_min, non_empty, artifact_glob, in_state_list, file_exists, no_open_bugs}.

GATE_RULES: dict[str, list[dict]] = {
    "intake-requirement": [
        {"kind": "int_min", "field": "step", "min": 1},
    ],
    "review-document": [
        {"kind": "flag", "field": "feedback_processed", "expected": True},
    ],
    "approve-document": [
        {"kind": "flag", "field": "approved", "expected": True},
    ],
    "start-wave": [
        {"kind": "flag", "field": "approved", "expected": True},
        {"kind": "int_min", "field": "wave_n", "min": 1},
        {"kind": "file_exists", "path": "harness/SERVICE-BOUNDARY-MATRIX.json"},
    ],
    "start-dev": [
        {"kind": "in_state_list", "field": "boundary", "state_field": "wave_boundaries"},
    ],
    "review-dev": [],  # entry only, no evidence required
    "dev-handoff": [
        {"kind": "coverage", "field": "coverage_pct", "min": 80},
        {"kind": "flag", "field": "review_result", "expected": "pass"},
    ],
    "test-plan": [
        {"kind": "flag", "field": "docker_compose_ok", "expected": True},
    ],
    "test-execute": [
        {"kind": "int_min", "field": "test_cases_count", "min": 1},
    ],
    "fix-bugs": [
        {"kind": "non_empty", "field": "bug_id"},
    ],
    "end-wave": [
        {"kind": "flag", "field": "uat_signed", "expected": True},
        {"kind": "no_open_bugs"},
    ],
    "done-wave": [
        {"kind": "flag", "field": "teardown_ok", "expected": True},
    ],
    "apply-cr": [
        {"kind": "non_empty", "field": "cr_id"},
    ],
}


def _run_rule(rule: dict, state: dict, evidence: dict) -> tuple[bool, str]:
    """Dispatch a single rule to its check function."""
    kind = rule.get("kind")
    try:
        if kind == "flag":
            return check_flag(evidence, rule["field"], rule["expected"])
        if kind == "coverage":
            return check_coverage(evidence, rule["min"], rule.get("field", "coverage_pct"))
        if kind == "int_min":
            return check_int_min(evidence, rule["field"], rule["min"])
        if kind == "non_empty":
            return check_non_empty(evidence, rule["field"])
        if kind == "artifact_glob":
            return check_artifact_glob(rule["pattern"], rule.get("min_count", 1))
        if kind == "in_state_list":
            return check_in_state_list(evidence, rule["field"], state, rule["state_field"])
        if kind == "file_exists":
            return check_file_exists(rule["path"])
        if kind == "no_open_bugs":
            return check_no_open_bugs(state)
    except KeyError as e:
        return False, f"Rule {kind} missing field: {e}"
    return False, f"Unknown gate kind: {kind!r}"


def check_for_command(
    command_id: str, state: dict, evidence: dict
) -> tuple[bool, list[str]]:
    """
    Run all gate rules for a command.
    Returns (ok=all-pass, errors=list of failure messages).
    """
    rules = GATE_RULES.get(command_id, [])
    errors: list[str] = []
    for rule in rules:
        ok, msg = _run_rule(rule, state, evidence)
        if not ok:
            errors.append(f"[{rule.get('kind')}] {msg}")
    return len(errors) == 0, errors


# ========================================================================
# Inline self-test (run: py scripts/gates.py)
# ========================================================================

def _selftest() -> int:
    """Smoke test các primitive functions."""
    assert check_flag({"a": True}, "a", True) == (True, "")
    assert check_flag({"a": False}, "a", True)[0] is False
    assert check_coverage({"coverage_pct": 85}, 80) == (True, "")
    assert check_coverage({"coverage_pct": 75}, 80)[0] is False
    assert check_int_min({"n": 5}, "n", 1) == (True, "")
    assert check_int_min({}, "n", 1)[0] is False
    assert check_non_empty({"s": "hello"}, "s") == (True, "")
    assert check_non_empty({"s": ""}, "s")[0] is False
    assert check_in_state_list({"b": "x"}, "b", {"L": ["x", "y"]}, "L") == (True, "")
    assert check_in_state_list({"b": "z"}, "b", {"L": ["x", "y"]}, "L")[0] is False

    # check_for_command
    ok, errs = check_for_command(
        "dev-handoff",
        state={},
        evidence={"coverage_pct": 85, "review_result": "pass"},
    )
    assert ok, f"dev-handoff pass case fail: {errs}"

    ok, errs = check_for_command(
        "dev-handoff",
        state={},
        evidence={"coverage_pct": 75, "review_result": "pass"},
    )
    assert not ok and "coverage_pct=75" in errs[0]

    print("OK: gates.py selftest passed")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
