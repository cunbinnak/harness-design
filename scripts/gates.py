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


# Ngưỡng coverage theo kind boundary (per-kind gate cho dev-handoff).
COVERAGE_THRESHOLD_PER_KIND = {
    "backend": 80,
    "bff": 70,
    "web": 60,
    "mobile": 60,
}
DEFAULT_COVERAGE_MIN = 80  # fallback khi không xác định được kind (strictest)


def _kind_of(boundary_id: str | None, root: Path | None = None) -> str | None:
    """Tra kind của 1 boundary từ harness/SERVICE-BOUNDARY-MATRIX.json."""
    if not boundary_id:
        return None
    root = root or REPO_ROOT
    matrix_file = root / "harness" / "SERVICE-BOUNDARY-MATRIX.json"
    if not matrix_file.is_file():
        return None
    try:
        data = json.loads(matrix_file.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    boundaries = data.get("boundaries", []) if isinstance(data, dict) else data
    for b in boundaries:
        if b.get("boundary_id") == boundary_id:
            return b.get("kind")
    return None


def _active_boundary_kind(state: dict, root: Path | None = None) -> str | None:
    """Tra kind của active_boundary từ MATRIX."""
    return _kind_of(state.get("active_boundary"), root)


def check_all_boundaries_reviewed(state: dict, root: Path | None = None) -> tuple[bool, str]:
    """Mọi boundary trong wave_boundaries phải có review_result=pass + coverage đạt ngưỡng theo kind.

    Nguồn: STATE.review_results (lưu bởi apply_effects khi /review-dev complete) — wave-scoped.
    """
    wave_boundaries = state.get("wave_boundaries") or []
    if not wave_boundaries:
        return False, "wave_boundaries rỗng — chưa /start-wave?"
    results = {
        r.get("boundary"): r
        for r in (state.get("review_results") or [])
        if isinstance(r, dict)
    }
    missing, failed, low_cov = [], [], []
    for bid in wave_boundaries:
        r = results.get(bid)
        if not r:
            missing.append(bid)
            continue
        if r.get("review_result") != "pass":
            failed.append(bid)
            continue
        kind = _kind_of(bid, root) or r.get("kind")
        min_pct = COVERAGE_THRESHOLD_PER_KIND.get(kind, DEFAULT_COVERAGE_MIN)
        cov = r.get("coverage_pct", 0)
        if not (isinstance(cov, (int, float)) and cov >= min_pct):
            low_cov.append(f"{bid}({kind}):{cov}<{min_pct}")
    problems = []
    if missing:
        problems.append(f"chưa review: {missing}")
    if failed:
        problems.append(f"review fail: {failed}")
    if low_cov:
        problems.append(f"coverage thiếu: {low_cov}")
    if problems:
        return False, "; ".join(problems)
    return True, ""


def check_coverage_per_kind(
    evidence: dict, state: dict, field: str = "coverage_pct"
) -> tuple[bool, str]:
    """Check coverage_pct >= ngưỡng theo kind active_boundary (BE80/BFF70/web60/mobile60)."""
    kind = evidence.get("kind") or _active_boundary_kind(state)
    min_pct = COVERAGE_THRESHOLD_PER_KIND.get(kind, DEFAULT_COVERAGE_MIN)
    val = evidence.get(field, 0)
    if isinstance(val, (int, float)) and val >= min_pct:
        return True, ""
    return False, f"evidence.{field}={val} < {min_pct} (kind={kind or 'unknown'})"


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


def check_wave_in_matrix(evidence: dict, field: str = "wave_n", root: Path | None = None) -> tuple[bool, str]:
    """Check wave_n maps to ≥1 boundary trong MATRIX (wave phải tồn tại để mở)."""
    try:
        wave_n = int(evidence.get(field))
    except (TypeError, ValueError):
        return False, f"evidence.{field}={evidence.get(field)!r} không phải int"
    root = root or REPO_ROOT
    matrix_file = root / "harness" / "SERVICE-BOUNDARY-MATRIX.json"
    if not matrix_file.is_file():
        return False, "MATRIX không tồn tại"
    try:
        data = json.loads(matrix_file.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return False, "MATRIX parse lỗi"
    boundaries = data.get("boundaries", []) if isinstance(data, dict) else data
    waves: set[int] = set()
    for b in boundaries:
        if b.get("wave") is not None:
            waves.add(b.get("wave"))
        for w in (b.get("waves") or []):
            waves.add(w)
    if wave_n in waves:
        return True, ""
    return False, f"wave {wave_n} không có boundary nào trong MATRIX (waves có sẵn: {sorted(waves)})"


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
        {"kind": "wave_in_matrix", "field": "wave_n"},
    ],
    "start-dev": [
        {"kind": "in_state_list", "field": "boundary", "state_field": "wave_boundaries"},
    ],
    "review-dev": [],  # entry only, no evidence required
    "dev-handoff": [
        {"kind": "all_boundaries_reviewed"},
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
        if kind == "coverage_per_kind":
            return check_coverage_per_kind(evidence, state, rule.get("field", "coverage_pct"))
        if kind == "all_boundaries_reviewed":
            return check_all_boundaries_reviewed(state)
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
        if kind == "wave_in_matrix":
            return check_wave_in_matrix(evidence, rule.get("field", "wave_n"))
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

    # dev-handoff: wave-scoped — mọi wave_boundary phải pass + coverage theo kind
    st_pass = {
        "wave_boundaries": ["order", "web1"],
        "review_results": [
            {"boundary": "order", "kind": "backend", "review_result": "pass", "coverage_pct": 85},
            {"boundary": "web1", "kind": "web", "review_result": "pass", "coverage_pct": 62},
        ],
    }
    ok, errs = check_for_command("dev-handoff", state=st_pass, evidence={})
    assert ok, f"dev-handoff wave pass fail: {errs}"

    # thiếu 1 boundary chưa review
    st_missing = {"wave_boundaries": ["order", "web1"],
                  "review_results": [{"boundary": "order", "kind": "backend", "review_result": "pass", "coverage_pct": 85}]}
    ok, errs = check_for_command("dev-handoff", state=st_missing, evidence={})
    assert not ok and "chưa review" in errs[0], errs

    # coverage dưới ngưỡng kind (backend cần 80)
    st_low = {"wave_boundaries": ["order"],
              "review_results": [{"boundary": "order", "kind": "backend", "review_result": "pass", "coverage_pct": 75}]}
    ok, errs = check_for_command("dev-handoff", state=st_low, evidence={})
    assert not ok and "coverage" in errs[0], errs

    # per-kind coverage thresholds (BE80 / BFF70 / web60 / mobile60)
    assert check_coverage_per_kind({"coverage_pct": 65, "kind": "web"}, {})[0] is True
    assert check_coverage_per_kind({"coverage_pct": 72, "kind": "bff"}, {})[0] is True
    assert check_coverage_per_kind({"coverage_pct": 60, "kind": "mobile"}, {})[0] is True
    assert check_coverage_per_kind({"coverage_pct": 65, "kind": "backend"}, {})[0] is False
    assert check_coverage_per_kind({"coverage_pct": 79, "kind": None}, {})[0] is False  # default 80

    # wave_in_matrix: seed MATRIX has wave 1, not wave 99
    assert check_wave_in_matrix({"wave_n": 1})[0] is True
    assert check_wave_in_matrix({"wave_n": 99})[0] is False
    assert check_wave_in_matrix({"wave_n": "x"})[0] is False

    print("OK: gates.py selftest passed")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
