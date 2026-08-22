"""
End-to-end smoke test for state machine.
Walks through 17 states + 23 commands with mock evidence.

Front-half (Discovery D0-D3 → Domain → Design → Plan → Review) gate check artifact
trên disk; smoke test verify TRANSITION nên dùng force-bypass (nội dung gate test riêng
ở gates.py / discovery_gate.py selftest). Force ghi audit tracking/decisions.md → hermetic restore.

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
    s["review_results"] = []
    s["spawn"] = {"active": None}
    s["workflow"] = {"last_completed": None}
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
    # decisions.md: force-bypass ghi audit row → save/restore hermetic
    decisions_file = REPO / "tracking" / "decisions.md"
    decisions_existed = decisions_file.exists()
    decisions_original = decisions_file.read_text(encoding="utf-8") if decisions_existed else None
    # infra_proof + health_proof artifacts (gate dev-handoff/test-plan) — tạo/cleanup hermetic
    proof_dir = REPO / "tracking" / "wave-001"
    proof_file = proof_dir / "docker-ps.json"
    health_file = proof_dir / "health-proof.json"
    registry_file = proof_dir / "test-case-registry.md"
    proof_dir_existed = proof_dir.exists()
    proof_existed = proof_file.exists()
    health_existed = health_file.exists()
    registry_existed = registry_file.exists()
    passed = []
    failed = []

    try:
        # Hermetic MATRIX fixture: 2 boundary (backend + web), wave 1 — test multi-boundary.
        seed_matrix([
            {"boundary_id": "order-management", "kind": "backend", "prefix": "demo",
             "wave": 1, "features": ["FEAT-001", "FEAT-002"]},
            {"boundary_id": "storefront", "kind": "web", "prefix": "demo",
             "wave": 1, "features": ["FEAT-003"]},
        ])

        # ============================================================
        # Happy path: BOOTSTRAP -> ... -> DONE -> BOOTSTRAP
        # ============================================================
        print("\n## 1. Happy path (full cycle)\n")
        reset_state()
        FB = {"force": True, "reason": "smoke-test transition walk"}  # bypass disk-gate

        # BOOTSTRAP -> DISC_D0 (discovery-start)
        ok = step("BOOTSTRAP -> DISC_D0 (start D0)", "discovery-start", {"wave": "D0"}, "DISC_D0")
        passed.append(ok) if ok else failed.append("BOOTSTRAP->DISC_D0")

        # Cơ chế mới: discovery-start TIẾN D0->D1->D2->D3 (gate wave trước qua discovery_advance → force bypass)
        for w, to in [("D1", "DISC_D1"), ("D2", "DISC_D2"), ("D3", "DISC_D3")]:
            ok = step(f"start {w} -> {to}", "discovery-start", {"wave": w, **FB}, to)
            passed.append(ok) if ok else failed.append(f"discovery-start advance {w}")

        # DISC_D3 -> DOMAIN_AUTHORING (discovery-end chốt, gate D3 → force bypass + service_prefix)
        ok = step("DISC_D3 -> DOMAIN_AUTHORING (end)", "discovery-end",
                  {"service_prefix": "demo", **FB}, "DOMAIN_AUTHORING")
        passed.append(ok) if ok else failed.append("discovery-end -> DOMAIN")

        # DOMAIN: po/ba author business (self) → approve (ký) → translate (dịch eng) → domain-end → DESIGN
        ok = step("DOMAIN po (author FEATURE)", "domain-po", {"mode": "FEATURE"}, "DOMAIN_AUTHORING")
        passed.append(ok) if ok else failed.append("domain-po")
        ok = step("DOMAIN ba (author BR)", "domain-ba", {"mode": "BR"}, "DOMAIN_AUTHORING")
        passed.append(ok) if ok else failed.append("domain-ba")
        ok = step("DOMAIN approve (ký all)", "domain-approve", {}, "DOMAIN_AUTHORING")  # no docs/domain → no-jargon vacuous pass
        passed.append(ok) if ok else failed.append("domain-approve")
        ok = step("DOMAIN translate (dịch eng)", "domain-translate",
                  {"force": True, "reason": "smoke (chưa author business docs/domain → domain_signed bypass)"}, "DOMAIN_AUTHORING")
        passed.append(ok) if ok else failed.append("domain-translate")
        ok = step("DOMAIN_AUTHORING -> DESIGN", "domain-end", FB, "DESIGN")
        passed.append(ok) if ok else failed.append("domain-end")

        # DESIGN self-loop (design refine) ; DESIGN -> PLAN (design-end) ; PLAN -> REVIEW (plan)
        ok = step("DESIGN self (design refine)", "design", {}, "DESIGN")
        passed.append(ok) if ok else failed.append("design self-loop")
        ok = step("DESIGN self (design-ux refine)", "design-ux", {}, "DESIGN")
        passed.append(ok) if ok else failed.append("design-ux self-loop")
        ok = step("DESIGN -> PLAN", "design-end", FB, "PLAN")
        passed.append(ok) if ok else failed.append("design-end")
        ok = step("PLAN -> REVIEW", "plan", FB, "REVIEW")
        passed.append(ok) if ok else failed.append("plan")

        # REVIEW -> REVIEW (review-document, revision loop)
        ok = step("review-document feedback", "review-document", {"feedback_processed": True}, "REVIEW")
        passed.append(ok) if ok else failed.append("review-document")

        # REVIEW -> REVIEW (approve-document, set approved flag) — gate doc_review (findings sanity-check) → force bypass
        ok = step("approve-document", "approve-document", {"approved": True, **FB}, "REVIEW")
        passed.append(ok) if ok else failed.append("approve-document")

        # REVIEW -> WAVE_OPEN (start-wave) — derive wave_boundaries/features từ MATRIX
        ok = step(
            "REVIEW -> WAVE_OPEN",
            "start-wave",
            {"approved": True, "wave_n": 1},
            "WAVE_OPEN",
        )
        passed.append(ok) if ok else failed.append("start-wave")

        # apply_effects must populate wave + wave_boundaries + wave_features from MATRIX (NO manual seed).
        st = state_mod.load_state()
        wb = st.get("wave_boundaries")
        wf = st.get("wave_features")
        wave_ok = st.get("wave", {}).get("id") == "wave-001" and wb == ["order-management", "storefront"]
        print(f"  [{'OK  ' if wave_ok else 'FAIL'}] start-wave derives wave_boundaries (MATRIX)  -> {wb}")
        passed.append(wave_ok) if wave_ok else failed.append("start-wave boundaries")
        feat_ok = wf == ["FEAT-001", "FEAT-002", "FEAT-003"]
        print(f"  [{'OK  ' if feat_ok else 'FAIL'}] start-wave derives wave_features (MATRIX)    -> {wf}")
        passed.append(feat_ok) if feat_ok else failed.append("start-wave features")

        # WAVE_OPEN -> DEV (start-dev boundary 1) — gate reads derived wave_boundaries
        ok = step("WAVE_OPEN -> DEV (start-dev order)", "start-dev", {"boundary": "order-management"}, "DEV")
        passed.append(ok) if ok else failed.append("start-dev order")

        st = state_mod.load_state()
        ab_ok = st.get("active_boundary") == "order-management"
        print(f"  [{'OK  ' if ab_ok else 'FAIL'}] start-dev sets active_boundary              -> {st.get('active_boundary')}")
        passed.append(ab_ok) if ab_ok else failed.append("start-dev effects")

        # DEV -> DEV (start-dev boundary 2: multi-boundary trong cùng wave)
        ok = step("DEV -> DEV (start-dev storefront)", "start-dev", {"boundary": "storefront"}, "DEV")
        passed.append(ok) if ok else failed.append("start-dev storefront (multi-boundary)")

        # DEV -> REVIEW_DEV (wave-scoped: review_results cho CẢ 2 boundary, mỗi cái theo kind)
        # challenge_passed đọc tracking/challenge-log.md THẬT (test riêng ở gates selftest) →
        # smoke force-bypass, đúng triết lý: smoke verify TRANSITION, nội dung gate test hermetic.
        ok = step(
            "DEV -> REVIEW_DEV (wave review)",
            "review-dev",
            {"review_results": [
                {"boundary": "order-management", "kind": "backend", "review_result": "pass", "coverage_pct": 85},
                {"boundary": "storefront", "kind": "web", "review_result": "pass", "coverage_pct": 62},
            ],
             "force": True,
             "reason": "smoke transition walk (challenge-log content tested in gates selftest)"},
            "REVIEW_DEV",
        )
        passed.append(ok) if ok else failed.append("review-dev wave")

        # infra proof: dev-handoff PHẢI có docker-ps.json chứng minh wave services lên THẬT
        # (content-validated). Gate infra_proof giờ chạy ở CẢ dev-handoff lẫn test-plan →
        # tạo proof TRƯỚC dev-handoff, content = order-management + storefront running.
        proof_dir.mkdir(parents=True, exist_ok=True)
        proof_file.write_text(
            '[{"Service":"order-management","State":"running","Health":"healthy"},'
            '{"Service":"storefront","State":"running","Health":""}]',
            encoding="utf-8",
        )
        # health_proof: app reachable (HARNESS curl /health/ready) — mỗi wave service 1 probe ok
        health_file.write_text(
            '{"probes":[{"boundary":"order-management","http_status":200,"ok":true},'
            '{"boundary":"storefront","http_status":200,"ok":true}]}',
            encoding="utf-8",
        )

        # REVIEW_DEV -> DEV_HANDOFF (gate: all_boundaries_reviewed + infra_proof + health_proof content-validated)
        ok = step("REVIEW_DEV -> DEV_HANDOFF", "dev-handoff", {}, "DEV_HANDOFF")
        passed.append(ok) if ok else failed.append("dev-handoff")

        # registry fixture: test-plan gate ui_test_present (web boundary storefront phải có auto UI TC)
        # + registry_scope (repo design không có docs/plans/wave-*.md → scope vacuous pass).
        registry_file.write_text(
            "| TC | group | type | boundary | feature | AC | tags |\n"
            "|----|-------|------|----------|---------|----|------|\n"
            "| TC-I01 | integration | auto | order-management | FEAT-001 | AC-1 | @FEAT-001 |\n"
            "| TC-U01 | e2e | auto | storefront | FEAT-003 | AC-1 | @FEAT-003 |\n",
            encoding="utf-8",
        )

        # DEV_HANDOFF -> TEST_PLAN
        ok = step(
            "DEV_HANDOFF -> TEST_PLAN",
            "test-plan",
            {"docker_compose_ok": True, "connectivity_ok": True},
            "TEST_PLAN",
        )
        passed.append(ok) if ok else failed.append("test-plan")

        # TEST_PLAN -> TEST_EXECUTE -> (auto) MANUAL_TEST
        # state.complete() now chains auto-transition when test_result=pass
        # test_evidence gate đọc registry/report THẬT (test riêng ở gates.py selftest) → smoke
        # dùng force-bypass (đúng triết lý: smoke verify TRANSITION; nội dung gate test hermetic).
        ok = step(
            "TEST_PLAN -> TEST_EXECUTE -(auto)-> MANUAL_TEST",
            "test-execute",
            {"test_cases_count": 5, "test_result": "pass",
             "force": True, "reason": "smoke transition walk (test-evidence content tested in gates selftest)"},
            "MANUAL_TEST",
        )
        passed.append(ok) if ok else failed.append("test-execute + auto")

        # MANUAL_TEST -> MANUAL_TEST (dogfood: 6 lăng kính x 2 đợt, in-state)
        # health_proof đọc proof file THẬT (test riêng ở gates.py selftest) → smoke force-bypass,
        # đúng triết lý: smoke verify TRANSITION, nội dung gate test hermetic.
        ok = step(
            "MANUAL_TEST dogfood (loop)",
            "dogfood",
            {"batches_done": 2, "force": True,
             "reason": "smoke transition walk (health-proof + dogfood report tested in gates selftest)"},
            "MANUAL_TEST",
        )
        passed.append(ok) if ok else failed.append("dogfood")

        # MANUAL_TEST -> DONE (end-wave)
        # Không còn sổ bug: TC fail chặn qua test_passed (derive từ test-report.md).
        # dogfood_done đọc tracking/{wave}/dogfood-report.md THẬT → force-bypass như trên.
        ok = step(
            "MANUAL_TEST -> DONE",
            "end-wave",
            {"uat_signed": True, "force": True,
             "reason": "smoke transition walk (dogfood-report content tested in gates selftest)"},
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

        # Gate fail: dev-handoff khi coverage dưới ngưỡng kind (gate wave-scoped đọc STATE.review_results)
        # Đưa nhanh về WAVE_OPEN qua force-bypass front-half rồi start-wave.
        FB = {"force": True, "reason": "smoke negative-case setup"}
        state_mod.complete("discovery-start", {"wave": "D0"})
        for w in ["D1", "D2", "D3"]:
            state_mod.complete("discovery-start", {"wave": w, **FB})
        state_mod.complete("discovery-end", {"service_prefix": "demo", **FB})
        state_mod.complete("domain-end", FB)
        state_mod.complete("design-end", FB)
        state_mod.complete("plan", FB)
        state_mod.complete("approve-document", {"approved": True, "force": True, "reason": "smoke setup"})
        state_mod.complete("start-wave", {"approved": True, "wave_n": 1})
        patch_state({"wave_boundaries": ["x"], "wave": {"id": "wave-001", "number": 1}})
        state_mod.complete("start-dev", {"boundary": "x"})
        # force: đây là SETUP cho phép thử coverage, không phải phép thử challenge.
        state_mod.complete("review-dev", {"review_results": [
            {"boundary": "x", "kind": "backend", "review_result": "pass", "coverage_pct": 50}],
            "force": True, "reason": "smoke setup — phép thử là coverage, không phải challenge"})

        result = state_mod.complete("dev-handoff", {})
        ok = not result["ok"] and "coverage" in result.get("error", "").lower()
        print(f"  [{'OK  ' if ok else 'FAIL'}] reject low coverage          {result.get('error', '')[:60]}")
        passed.append(ok) if ok else failed.append("reject low coverage")

        # Gate fail: dev-handoff khi còn boundary chưa review (missing trong review_results)
        patch_state({"wave_boundaries": ["x", "y"], "review_results": [
            {"boundary": "x", "kind": "backend", "review_result": "pass", "coverage_pct": 85}]})
        result = state_mod.complete("dev-handoff", {})
        ok = not result["ok"] and "review" in result.get("error", "").lower()
        print(f"  [{'OK  ' if ok else 'FAIL'}] reject boundary chưa review  {result.get('error', '')[:60]}")
        passed.append(ok) if ok else failed.append("reject boundary chưa review")

        # Gate fail: start-wave with a wave that maps to no boundary in MATRIX
        reset_state()
        FB2 = {"force": True, "reason": "smoke unknown-wave setup"}
        state_mod.complete("discovery-start", {"wave": "D0"})
        for w in ["D1", "D2", "D3"]:
            state_mod.complete("discovery-start", {"wave": w, **FB2})
        state_mod.complete("discovery-end", {"service_prefix": "demo", **FB2})
        state_mod.complete("domain-end", FB2)
        state_mod.complete("design-end", FB2)
        state_mod.complete("plan", FB2)
        state_mod.complete("approve-document", {"approved": True, "force": True, "reason": "smoke setup"})
        result = state_mod.complete("start-wave", {"approved": True, "wave_n": 99})
        ok = not result["ok"] and "wave 99" in result.get("error", "")
        print(f"  [{'OK  ' if ok else 'FAIL'}] reject start-wave unknown wave {result.get('error', '')[:50]}")
        passed.append(ok) if ok else failed.append("reject unknown wave")

        # ============================================================
        # Back-edges: lùi sửa upstream doc (PLAN→DESIGN, DESIGN→DOMAIN)
        # ============================================================
        print("\n## 3. Back-edges (lùi sửa doc đã frozen)\n")
        reset_state()
        FB3 = {"force": True, "reason": "smoke back-edge setup"}
        state_mod.complete("discovery-start", {"wave": "D0"})
        for w in ["D1", "D2", "D3"]:
            state_mod.complete("discovery-start", {"wave": w, **FB3})
        state_mod.complete("discovery-end", {"service_prefix": "demo", **FB3})
        state_mod.complete("domain-end", FB3)
        state_mod.complete("design-end", FB3)  # giờ ở PLAN
        ok = step("PLAN -> DESIGN (lùi /design)", "design", {}, "DESIGN")
        passed.append(ok) if ok else failed.append("back-edge PLAN->DESIGN")
        ok = step("DESIGN -> DOMAIN (lùi /domain-po)", "domain-po", {"mode": "FEATURE"}, "DOMAIN_AUTHORING")
        passed.append(ok) if ok else failed.append("back-edge DESIGN->DOMAIN")

    finally:
        # Restore original STATE + MATRIX + decisions.md (force-bypass ghi audit)
        STATE_FILE.write_text(original, encoding="utf-8")
        MATRIX_FILE.write_text(matrix_original, encoding="utf-8")
        if decisions_existed:
            decisions_file.write_text(decisions_original, encoding="utf-8")
        elif decisions_file.exists():
            decisions_file.unlink()
        # cleanup infra_proof + health_proof artifacts (hermetic — chỉ xoá cái test tạo ra)
        if not proof_existed and proof_file.exists():
            proof_file.unlink()
        if not health_existed and health_file.exists():
            health_file.unlink()
        if not registry_existed and registry_file.exists():
            registry_file.unlink()
        if not proof_dir_existed and proof_dir.exists():
            try:
                proof_dir.rmdir()
            except OSError:
                pass
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
