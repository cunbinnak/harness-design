"""
End-to-end smoke test for state machine.
Walks through all 10 states + 12 commands with mock evidence.

Run: py scripts/smoke_test.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import state as state_mod  # noqa: E402

REPO = SCRIPTS.parent
STATE_FILE = REPO / "harness" / "STATE.json"
MATRIX_FILE = REPO / "harness" / "SERVICE-BOUNDARY-MATRIX.json"


def reset_state(extra: dict | None = None) -> None:
    """Reset STATE.json to BOOTSTRAP, optionally seed extra fields."""
    s = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    s["stage"] = "BOOTSTRAP"
    s["previous_stage"] = None
    s["wave"] = {"id": None, "number": None}
    s["active_boundary"] = None
    s["wave_boundaries"] = []
    s["wave_features"] = []
    s["spawn"] = {"active": None}
    s["workflow"] = {"last_completed": None, "history": []}
    s["meta"]["revision"] = 1
    s["meta"]["updated_by"] = "smoke_test_reset"
    if extra:
        s.update(extra)
    STATE_FILE.write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def patch_state(updates: dict) -> None:
    """Patch STATE.json with given fields (for prerequisites like wave_boundaries)."""
    s = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    s.update(updates)
    STATE_FILE.write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def seed_matrix(boundaries: list[dict]) -> None:
    """Write a deterministic test MATRIX (hermetic — backed up + restored in finally).

    Test không phụ thuộc / không làm bẩn seed MATRIX commit; mọi assertion về
    wave_boundaries / wave_features chạy trên fixture này.
    """
    data = {"version": 1, "revision": 1, "boundaries": boundaries}
    MATRIX_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def step(label: str, command: str, evidence: dict, expect_stage: str) -> bool:
    """Run one transition and assert resulting stage."""
    result = state_mod.complete(command, evidence)
    after = state_mod.load_state()
    actual = after["stage"]
    ok = result.get("ok") and actual == expect_stage
    marker = "OK  " if ok else "FAIL"
    print(f"  [{marker}] {label:40s} stage={actual:15s} {result.get('message') or result.get('error')}")
    return ok


def main() -> int:
    print("=" * 70)
    print("SMOKE TEST — full state machine walkthrough")
    print("=" * 70)

    # Save original STATE + MATRIX (restored in finally)
    original = STATE_FILE.read_text(encoding="utf-8")
    matrix_original = MATRIX_FILE.read_text(encoding="utf-8")
    passed = []
    failed = []

    try:
        # Hermetic MATRIX fixture: 1 boundary, wave 1, 2 features.
        seed_matrix([{
            "boundary_id": "order-management", "kind": "backend", "prefix": "demo",
            "wave": 1, "features": ["FEAT-001", "FEAT-002"],
        }])

        # ============================================================
        # Happy path: BOOTSTRAP -> ... -> DONE -> BOOTSTRAP
        # ============================================================
        print("\n## 1. Happy path (full cycle)\n")
        reset_state()

        # BOOTSTRAP -> INTAKE
        ok = step("BOOTSTRAP -> INTAKE", "intake-requirement", {"step": 1}, "INTAKE")
        passed.append(ok) if ok else failed.append("BOOTSTRAP->INTAKE")

        # INTAKE loop (step 2, 3, 4)
        for n in [2, 3, 4]:
            ok = step(f"INTAKE step {n}", "intake-requirement", {"step": n}, "INTAKE")
            passed.append(ok) if ok else failed.append(f"INTAKE step {n}")

        # INTAKE -> INTAKE (review-document, revision loop)
        ok = step("review-document feedback", "review-document", {"feedback_processed": True}, "INTAKE")
        passed.append(ok) if ok else failed.append("review-document")

        # INTAKE -> INTAKE (approve-document, set approved flag)
        ok = step("approve-document", "approve-document", {"approved": True}, "INTAKE")
        passed.append(ok) if ok else failed.append("approve-document")

        # INTAKE -> WAVE_OPEN (start-wave)
        # Prerequisite: MATRIX file must exist (it does from v3)
        ok = step(
            "INTAKE -> WAVE_OPEN",
            "start-wave",
            {"approved": True, "wave_n": 1},
            "WAVE_OPEN",
        )
        passed.append(ok) if ok else failed.append("start-wave")

        # apply_effects must populate wave + wave_boundaries + wave_features from MATRIX (NO manual seed).
        st = state_mod.load_state()
        wb = st.get("wave_boundaries")
        wf = st.get("wave_features")
        wave_ok = st.get("wave", {}).get("id") == "wave-001" and wb == ["order-management"]
        print(f"  [{'OK  ' if wave_ok else 'FAIL'}] start-wave derives wave_boundaries (MATRIX)  -> {wb}")
        passed.append(wave_ok) if wave_ok else failed.append("start-wave boundaries")
        feat_ok = wf == ["FEAT-001", "FEAT-002"]
        print(f"  [{'OK  ' if feat_ok else 'FAIL'}] start-wave derives wave_features (MATRIX)    -> {wf}")
        passed.append(feat_ok) if feat_ok else failed.append("start-wave features")

        # WAVE_OPEN -> DEV (start-dev) — gate reads derived wave_boundaries, no patch needed
        ok = step("WAVE_OPEN -> DEV", "start-dev", {"boundary": "order-management"}, "DEV")
        passed.append(ok) if ok else failed.append("start-dev")

        # apply_effects must set active_boundary from the start-dev evidence.
        st = state_mod.load_state()
        ab_ok = st.get("active_boundary") == "order-management"
        print(f"  [{'OK  ' if ab_ok else 'FAIL'}] start-dev sets active_boundary              -> {st.get('active_boundary')}")
        passed.append(ab_ok) if ab_ok else failed.append("start-dev effects")

        # DEV -> REVIEW_DEV
        ok = step("DEV -> REVIEW_DEV", "review-dev", {}, "REVIEW_DEV")
        passed.append(ok) if ok else failed.append("review-dev")

        # REVIEW_DEV -> DEV_HANDOFF (coverage + review_result)
        ok = step(
            "REVIEW_DEV -> DEV_HANDOFF",
            "dev-handoff",
            {"coverage_pct": 85, "review_result": "pass"},
            "DEV_HANDOFF",
        )
        passed.append(ok) if ok else failed.append("dev-handoff")

        # DEV_HANDOFF -> TEST_PLAN
        ok = step(
            "DEV_HANDOFF -> TEST_PLAN",
            "test-plan",
            {"docker_compose_ok": True},
            "TEST_PLAN",
        )
        passed.append(ok) if ok else failed.append("test-plan")

        # TEST_PLAN -> TEST_EXECUTE -> (auto) MANUAL_TEST
        # state.complete() now chains auto-transition when test_result=pass
        ok = step(
            "TEST_PLAN -> TEST_EXECUTE -(auto)-> MANUAL_TEST",
            "test-execute",
            {"test_cases_count": 5, "test_result": "pass"},
            "MANUAL_TEST",
        )
        passed.append(ok) if ok else failed.append("test-execute + auto")

        # MANUAL_TEST -> MANUAL_TEST (fix-bugs in-state)
        ok = step(
            "MANUAL_TEST fix-bugs (loop)",
            "fix-bugs",
            {"bug_id": "BUG-001"},
            "MANUAL_TEST",
        )
        passed.append(ok) if ok else failed.append("fix-bugs manual")

        # MANUAL_TEST -> DONE (end-wave, no open bugs)
        # bugs.md doesn't exist or has no entries → check_no_open_bugs returns True
        ok = step(
            "MANUAL_TEST -> DONE",
            "end-wave",
            {"uat_signed": True},
            "DONE",
        )
        passed.append(ok) if ok else failed.append("end-wave")

        # DONE -> BOOTSTRAP (done-wave teardown)
        ok = step(
            "DONE -> BOOTSTRAP",
            "done-wave",
            {"teardown_ok": True},
            "BOOTSTRAP",
        )
        passed.append(ok) if ok else failed.append("done-wave")

        # ============================================================
        # Negative tests: should fail
        # ============================================================
        print("\n## 2. Negative cases (should fail)\n")
        reset_state()

        # Wrong command at BOOTSTRAP
        result = state_mod.complete("start-dev", {"boundary": "x"})
        ok = not result["ok"] and "not allowed" not in result.get("error", "").lower()
        # Actually we expect 'không allowed' message
        ok = not result["ok"]
        print(f"  [{'OK  ' if ok else 'FAIL'}] BOOTSTRAP rejects start-dev    {result.get('error', '')[:60]}")
        passed.append(ok) if ok else failed.append("reject wrong cmd")

        # Gate fail: dev-handoff without coverage
        # First get to REVIEW_DEV
        state_mod.complete("intake-requirement", {"step": 1})
        state_mod.complete("start-wave", {"approved": True, "wave_n": 1})
        patch_state({"wave_boundaries": ["x"], "wave": {"id": "wave-001", "number": 1}})
        state_mod.complete("start-dev", {"boundary": "x"})
        state_mod.complete("review-dev", {})

        result = state_mod.complete("dev-handoff", {"coverage_pct": 50, "review_result": "pass"})
        ok = not result["ok"] and "coverage" in result.get("error", "").lower()
        print(f"  [{'OK  ' if ok else 'FAIL'}] reject low coverage          {result.get('error', '')[:60]}")
        passed.append(ok) if ok else failed.append("reject low coverage")

        # Gate fail: dev-handoff without review_result=pass
        result = state_mod.complete("dev-handoff", {"coverage_pct": 90})
        ok = not result["ok"]
        print(f"  [{'OK  ' if ok else 'FAIL'}] reject missing review_result {result.get('error', '')[:60]}")
        passed.append(ok) if ok else failed.append("reject missing review_result")

        # Gate fail: start-wave with a wave that maps to no boundary in MATRIX
        reset_state()
        state_mod.complete("intake-requirement", {"step": 1})  # BOOTSTRAP -> INTAKE
        result = state_mod.complete("start-wave", {"approved": True, "wave_n": 99})
        ok = not result["ok"] and "wave 99" in result.get("error", "")
        print(f"  [{'OK  ' if ok else 'FAIL'}] reject start-wave unknown wave {result.get('error', '')[:50]}")
        passed.append(ok) if ok else failed.append("reject unknown wave")

    finally:
        # Restore original STATE + MATRIX
        STATE_FILE.write_text(original, encoding="utf-8")
        MATRIX_FILE.write_text(matrix_original, encoding="utf-8")
        print("\n(STATE.json + MATRIX restored to pre-test snapshot)")

    # ============================================================
    # Summary
    # ============================================================
    total = len(passed) + len(failed)
    print("\n" + "=" * 70)
    print(f"RESULT: {len(passed)}/{total} passed")
    if failed:
        print(f"FAILED: {failed}")
        return 1
    print("ALL GREEN")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
