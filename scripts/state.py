"""
STATE manager for ADLC Design Harness.

Reads/writes harness/STATE.json, validates against harness/STATE-MACHINE.json,
applies transitions. STATE.json chỉ giữ TRẠNG THÁI HIỆN TẠI (không lưu audit history).

This module CONTAINS side effects (file I/O). Pure gate logic lives in gates.py.

CLI:
  py scripts/state.py show
  py scripts/state.py validate
  py scripts/state.py can <command>
  py scripts/state.py complete <command> '<evidence-json>'
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import gates

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = REPO_ROOT / "harness" / "STATE.json"
MACHINE_FILE = REPO_ROOT / "harness" / "STATE-MACHINE.json"
MATRIX_FILE = REPO_ROOT / "harness" / "SERVICE-BOUNDARY-MATRIX.json"


# ========================================================================
# I/O
# ========================================================================

def load_state() -> dict:
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def load_machine() -> dict:
    return json.loads(MACHINE_FILE.read_text(encoding="utf-8"))


def save_state(state: dict, updated_by: str = "state.py") -> None:
    meta = state.setdefault("meta", {})
    meta["revision"] = int(meta.get("revision", 0)) + 1
    meta["updated_at"] = datetime.now(timezone.utc).isoformat()
    meta["updated_by"] = updated_by
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# ========================================================================
# Validation
# ========================================================================

def validate(state: dict | None = None, machine: dict | None = None) -> list[str]:
    state = state if state is not None else load_state()
    machine = machine if machine is not None else load_machine()
    errors: list[str] = []
    if state.get("stage") not in machine.get("states", {}):
        errors.append(f"stage={state.get('stage')!r} không có trong STATE-MACHINE.states")
    if state.get("version") != machine.get("version"):
        errors.append(
            f"version mismatch: STATE.version={state.get('version')} "
            f"MACHINE.version={machine.get('version')}"
        )
    return errors


# ========================================================================
# Query
# ========================================================================

def allowed_commands(state: dict | None = None, machine: dict | None = None) -> list[str]:
    state = state if state is not None else load_state()
    machine = machine if machine is not None else load_machine()
    stage = state.get("stage")
    return machine.get("states", {}).get(stage, {}).get("allowed_commands", [])


def can_run(command: str, state: dict | None = None, machine: dict | None = None) -> bool:
    return command in allowed_commands(state, machine)


def find_transition(
    command: str, state: dict | None = None, machine: dict | None = None,
    evidence: dict | None = None,
) -> dict | None:
    """Tìm transition (from==stage, trigger==command).

    Nếu nhiều transition cùng (from,trigger) — vd `discovery-start` từ DISC_D0 vừa self-loop
    (wave=D0) vừa tiến (wave=D1) — disambiguate bằng `evidence_required` khớp `evidence`.
    Single match / evidence None → trả cái đầu (backward-compat).
    """
    state = state if state is not None else load_state()
    machine = machine if machine is not None else load_machine()
    stage = state.get("stage")
    candidates = [
        t for t in machine.get("transitions", [])
        if t.get("from") == stage and t.get("trigger") == command
    ]
    if not candidates:
        return None
    if len(candidates) == 1 or evidence is None:
        return candidates[0]
    for t in candidates:
        if _evidence_matches(evidence, t.get("evidence_required", {})):
            return t
    return candidates[0]


# ========================================================================
# Complete (transition)
# ========================================================================

def complete(command: str, evidence_str: str | dict) -> dict:
    """
    Main entry: try to apply transition for `command` with given evidence.
    Returns {ok: bool, message: str, ...}.
    """
    state = load_state()
    machine = load_machine()

    # Parse evidence
    if isinstance(evidence_str, str):
        try:
            evidence = json.loads(evidence_str)
        except json.JSONDecodeError as e:
            return _err(f"Evidence JSON invalid: {e}")
    else:
        evidence = evidence_str

    if not isinstance(evidence, dict):
        return _err(f"Evidence phải là JSON object, nhận: {type(evidence).__name__}")

    # 1. Command allowed at current stage?
    if not can_run(command, state, machine):
        return _err(
            f"Command '{command}' không allowed ở stage '{state['stage']}'. "
            f"Allowed: {allowed_commands(state, machine)}"
        )

    # 2. Transition exists? (evidence-aware: phân biệt refine vs advance cùng (from,trigger))
    transition = find_transition(command, state, machine, evidence)
    if transition is None:
        return _err(
            f"Không tìm thấy transition cho '{command}' từ stage '{state['stage']}'"
        )

    # 3. Gate check (pure)
    ok, errors = gates.check_for_command(command, state, evidence)
    if not ok:
        return _err("Gate failed:\n  - " + "\n  - ".join(errors))

    # 4. Apply transition
    old_stage = state["stage"]
    new_stage = transition["to"]
    state["previous_stage"] = old_stage
    state["stage"] = new_stage

    # 5. Ghi last_completed (KHÔNG lưu history array — STATE.json gọn, không phình)
    state.setdefault("workflow", {})["last_completed"] = command

    # 6. Project whitelisted evidence into top-level STATE runtime fields — PHẢI chạy TRƯỚC
    #    auto-transition check bên dưới: derive_test_result() (cho command "test-execute") set
    #    state["test_result"] ở đây; transition TEST_EXECUTE->MANUAL_TEST (trigger "_auto") cần
    #    đúng field này trong evidence_required. Đảo ngược thứ tự (auto-transition check trước,
    #    apply_effects sau) khiến evidence lúc check auto-transition CHƯA có test_result (evidence
    #    gọi vào chỉ có test_cases_count, đúng cách dùng bình thường — không ai tự khai test_result
    #    tay), nên auto-transition KHÔNG BAO GIỜ fire được ở lượt gọi thường, kẹt ở TEST_EXECUTE
    #    (allowed_commands rỗng theo thiết kế vì lẽ ra auto-transition đã đưa đi tiếp).
    #    (stage move only updates `stage`; runtime fields like wave/wave_boundaries
    #     /active_boundary/service_prefix are populated here.)
    apply_effects(command, evidence, state)

    # 7. Chain auto-transitions (e.g., TEST_EXECUTE -> MANUAL_TEST when test_result=pass)
    #    Evidence_required cho trigger "_auto" (vd {"test_result": "any"}) phải soi được field DERIVE
    #    ở bước 6 (vd test_result từ report, KHÔNG phải evidence gọi vào tay — không ai tự khai
    #    test_result). Merge state vào evidence (evidence override nếu trùng key) để _evidence_matches
    #    thấy được field derive, không chỉ field caller gõ tay.
    chain = _try_auto_transition(state, machine, {**state, **evidence})
    transitions_msg = f"{command}: {old_stage} -> {new_stage}"
    if chain:
        transitions_msg += f" -> {chain}"

    save_state(state, updated_by=f"complete:{command}")
    # Chốt xanh KHÔNG có nghĩa là đã phủ hết. In thẳng thứ máy không kiểm được, để "gate xanh"
    # đừng bị đọc thành lời bảo đảm — giấu chỗ mù đi thì không ai đi làm nốt phần đó.
    todo = gates.manual_checks(command)
    if todo:
        transitions_msg += ("\n\nKhông kiểm tự động được — tự xác nhận:\n  · "
                            + "\n  · ".join(todo))
    # Chốt vừa xanh thì nói luôn chốt kế — không thì mỗi lần xong một chốt lại phải đi tra
    # `allowed_commands` sang tài liệu để biết gõ gì tiếp.
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent / "hooks"))
        import policies as _pol
        _hint = _pol.next_step_hint(state)
        if _hint:
            transitions_msg += f"\n\nChốt kế: {_hint}"
    except Exception:
        pass
    return _ok(transitions_msg)


def _try_auto_transition(state: dict, machine: dict, evidence: dict) -> str | None:
    """
    After a regular transition, check if current stage has an _auto transition
    whose evidence_required is satisfied. If so, apply it. Returns the new stage
    or None if no auto-transition happened.
    """
    current = state["stage"]
    for t in machine.get("transitions", []):
        if t.get("from") != current or t.get("trigger") != "_auto":
            continue
        required = t.get("evidence_required", {})
        if _evidence_matches(evidence, required):
            old = state["stage"]
            state["previous_stage"] = old
            state["stage"] = t["to"]
            state.setdefault("workflow", {})["last_completed"] = "_auto"
            return t["to"]
    return None


def _evidence_matches(evidence: dict, required: dict) -> bool:
    """Check evidence satisfies required dict (each key=value must match)."""
    for k, v in required.items():
        if v == "any":
            if k not in evidence or evidence[k] in (None, ""):
                return False
        elif evidence.get(k) != v:
            return False
    return True


# ========================================================================
# Effects — project evidence into top-level STATE runtime fields
# ========================================================================

def _load_matrix_boundaries() -> list[dict]:
    """Read boundaries[] from SERVICE-BOUNDARY-MATRIX.json (list or {boundaries:[...]})."""
    if not MATRIX_FILE.is_file():
        return []
    try:
        data = json.loads(MATRIX_FILE.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return []
    if isinstance(data, dict):
        return data.get("boundaries", [])
    if isinstance(data, list):
        return data
    return []


def wave_boundaries_from_matrix(wave_n: int) -> list[str]:
    """Boundaries assigned to wave `wave_n` — same predicate as materialize.py filter.

    Single source of truth = MATRIX[boundaries].wave (or .waves list). Derived here
    so STATE.wave_boundaries cannot drift from what materialize.py generates.
    """
    out: list[str] = []
    for b in _load_matrix_boundaries():
        bid = b.get("boundary_id") or b.get("id")
        if not bid:
            continue
        # `features_by_wave` là SoT thật cho boundary sống qua NHIỀU wave; `wave` chỉ còn nghĩa
        # "wave đầu tiên boundary xuất hiện" (materialize_matrix KHÔNG bao giờ sinh `waves`). Thiếu
        # nhánh này thì start-dev ở wave ≥2 thấy `wave_boundaries=[]`. Port ngược từ HRM.
        if (b.get("wave") == wave_n or wave_n in (b.get("waves") or [])
                or str(wave_n) in (b.get("features_by_wave") or {})):
            out.append(bid)
    return out


def wave_features_from_matrix(wave_n: int) -> list[str]:
    """FEAT ids of every boundary in wave `wave_n` — deduped, stable (planner) order.

    Single source of truth = MATRIX[boundaries].features. Mirrors
    wave_boundaries_from_matrix so STATE.wave_features can't drift from the plan.

    BUG THẬT ĐÃ VÁ (dogfood HRM): một boundary sống qua NHIỀU wave (rất phổ biến — boundary
    không đổi, chỉ thêm feature theo từng wave) trước đây trả về TOÀN BỘ `features[]` cho MỌI
    wave nó khớp — boundary `wave=1` có `features` gồm cả FEAT của wave 2/3 (kế hoạch đã ghi rõ
    "Deferred to later waves") vẫn bị coi là feature CỦA WAVE 1, vì hàm không phân biệt được
    "feature này thuộc wave nào" trong một list phẳng. Hệ quả thật: dev/test-plan-agent code +
    sinh test cho FEAT chưa tới lượt, review/test không soi kịp vì coi là hợp lệ.

    Fix: field TUỲ CHỌN `features_by_wave` = {"<wave_n>": [feat_id,...]} trên boundary. Có field
    này → dùng ĐÚNG key wave_n (thiếu key = rỗng cho wave đó, KHÔNG fallback sang `features` —
    đã khai per-wave thì phải khai đủ, im lặng fallback lại tái tạo đúng bug này). KHÔNG có field
    này (boundary chỉ sống 1 wave, ca phổ biến nhất) → giữ nguyên hành vi cũ (đọc `features` phẳng)
    — tương thích ngược 100%, project cũ không cần sửa gì.
    """
    out: list[str] = []
    seen: set[str] = set()
    key = str(wave_n)
    for b in _load_matrix_boundaries():
        by_wave = b.get("features_by_wave")
        # BUG THẬT #2 (port ngược từ HRM): bản đầu của fix này đòi `b.wave == wave_n` TRƯỚC khi xét
        # `features_by_wave` — mà `wave` giữ nguyên `1` (first-appearance marker), nên với wave ≥2
        # guard luôn fail và hàm trả `[]` bất kể đã khai gì. Fix "chưa từng chạy được" cho đúng thứ
        # nó sinh ra để phục vụ. Selftest khi đó xanh vì dùng fixture `waves: [1, 2]` VIẾT TAY —
        # field mà `materialize_matrix` không bao giờ sinh ra.
        matches_legacy = b.get("wave") == wave_n or wave_n in (b.get("waves") or [])
        matches_by_wave = bool(by_wave) and key in by_wave
        if not (matches_legacy or matches_by_wave):
            continue
        feats = (by_wave or {}).get(key, []) if by_wave else (b.get("features") or [])
        for feat in feats:
            if feat not in seen:
                seen.add(feat)
                out.append(feat)
    return out


def _selftest() -> int:
    """Unit test wave_features_from_matrix / wave_boundaries_from_matrix trên MATRIX tạm.

    `_load_matrix_boundaries()` đọc từ global `MATRIX_FILE` (bind 1 lần lúc import) — patch
    thẳng biến đó, không patch `REPO_ROOT` (đổi `REPO_ROOT` sau import không tự cập nhật
    `MATRIX_FILE` đã bind trước đó)."""
    import tempfile

    global MATRIX_FILE
    orig_matrix_file = MATRIX_FILE
    tmp = Path(tempfile.mkdtemp(prefix="state_wf_"))
    try:
        MATRIX_FILE = tmp / "SERVICE-BOUNDARY-MATRIX.json"

        # (a) tương thích ngược: boundary 1-wave, features phẳng — hành vi CŨ giữ nguyên
        matrix = {"boundaries": [
            {"boundary_id": "auth", "kind": "backend", "wave": 1, "features": ["FEAT-1", "FEAT-2"]},
        ]}
        MATRIX_FILE.write_text(json.dumps(matrix), encoding="utf-8")
        assert wave_features_from_matrix(1) == ["FEAT-1", "FEAT-2"]
        assert wave_boundaries_from_matrix(1) == ["auth"]

        # (b) BUG THẬT: boundary sống qua nhiều wave, features phẳng gồm CẢ hai wave — hành vi cũ
        # trả cả FEAT-2 cho wave 1 lẫn wave 2 (leak). PHẢI dùng features_by_wave để tách đúng.
        #
        # Fixture DỰNG QUA `materialize_matrix.normalize_boundary` — KHÔNG viết tay. Bản trước viết
        # tay `"waves": [1, 2]`, field mà pipeline thật KHÔNG BAO GIỜ sinh ra, nên selftest xanh
        # trong khi fix hỏng hẳn ở wave ≥2 (HRM bắt được khi start-wave 2). Test phải chạy trên
        # đúng hình dạng dữ liệu người dùng thật tạo ra, không phải hình dạng làm test dễ qua.
        import materialize_matrix as _mm
        core = _mm.normalize_boundary({
            "boundary_id": "core", "kind": "backend", "prefix": "x", "wave": 1,
            "features": ["FEAT-1", "FEAT-2", "FEAT-3"],
            "features_by_wave": {"1": ["FEAT-1"], "2": ["FEAT-2", "FEAT-3"]},
        })
        assert "waves" not in core and core["wave"] == 1, core   # đúng hình dạng pipeline sinh
        MATRIX_FILE.write_text(json.dumps({"boundaries": [core]}), encoding="utf-8")
        assert wave_features_from_matrix(1) == ["FEAT-1"], wave_features_from_matrix(1)
        assert wave_features_from_matrix(2) == ["FEAT-2", "FEAT-3"], wave_features_from_matrix(2)
        assert wave_boundaries_from_matrix(1) == ["core"]
        assert wave_boundaries_from_matrix(2) == ["core"], wave_boundaries_from_matrix(2)

        # (c) features_by_wave khai nhưng THIẾU key cho wave đang hỏi → rỗng, KHÔNG fallback
        # sang `features` phẳng (fallback ngầm tái tạo đúng bug leak vừa vá). Cũng dựng qua pipeline.
        matrix = {"boundaries": [_mm.normalize_boundary({
            "boundary_id": "core", "kind": "backend", "prefix": "x", "wave": 1,
            "features": ["FEAT-1", "FEAT-9"],
            "features_by_wave": {"1": ["FEAT-1"]},   # thiếu key "3"
        })]}
        MATRIX_FILE.write_text(json.dumps(matrix), encoding="utf-8")
        assert wave_features_from_matrix(3) == [], wave_features_from_matrix(3)

        # (d) dedupe khi 2 boundary cùng wave đều đóng góp
        matrix = {"boundaries": [
            {"boundary_id": "core", "kind": "backend", "wave": 1, "features": ["FEAT-1"]},
            {"boundary_id": "web", "kind": "web", "wave": 1, "features": ["FEAT-1", "FEAT-2"]},
        ]}
        MATRIX_FILE.write_text(json.dumps(matrix), encoding="utf-8")
        assert wave_features_from_matrix(1) == ["FEAT-1", "FEAT-2"], wave_features_from_matrix(1)
    finally:
        MATRIX_FILE = orig_matrix_file
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    print("OK: state.py selftest passed (wave_features_from_matrix / features_by_wave)")
    return 0


def _append_decision(ref: str, rationale: str) -> None:
    """Append 1 audit row vào tracking/decisions.md (cho force-override gate).

    Clone cơ chế audit của ZIP: gate bypass phải để lại dấu vết.

    Dùng CHUNG bảng với `decide.py` — cùng 7 cột, cùng file. Hai sổ riêng thì phép
    đếm quyết định theo wave phải đọc hai chỗ, và cái force-bypass (thứ đáng soi nhất) lại nằm ở chỗ
    ít ai mở. Cột "Giả định" của force-bypass luôn là cùng một câu: bypass đang cược rằng gate sai
    chứ không phải việc chưa xong.
    """
    from decide import HEADER, _cell  # cùng thư mục scripts/

    path = REPO_ROOT / "tracking" / "decisions.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        path.write_text(HEADER, encoding="utf-8")
    try:
        st = load_state() or {}
    except Exception:   # audit row KHÔNG được hỏng vì đọc STATE lỗi — mất vết còn tệ hơn thiếu cột
        st = {}
    stage = st.get("stage") or "-"
    wave = (st.get("wave") or {}).get("id") or "-"
    with path.open("a", encoding="utf-8") as f:
        f.write(
            f"| {ts} | {stage} · {wave} | FORCE-BYPASS gate: {_cell(ref)} | {_cell(rationale)} | "
            f"gate báo sai, việc thật sự đã xong | Có — chạy lại gate sau khi vá | force-override |\n"
        )


def _open_replan(state: dict, layers: tuple[str, ...]) -> None:
    """Vào lượt chia lại sau khi đã chạy wave (từ WAVE_OPEN/DONE).

    Hai việc, cùng một lý do — phần sửa phải được NGƯỜI đọc lại trước khi chạy wave kế:
      · `replan_open` → gate `replan_approved` chặn start-wave tới khi /approve-document. Cờ `approved`
        của start-wave là evidence tự truyền, một mình nó không chặn được.
      · hạ dấu ký các lớp sắp sửa về DRAFT → gate `*_stamped` ở chốt ký của từng lớp đỏ tới khi ký
        lại thật. Giữ dấu cũ thì các gate đó xanh chay dù phần sửa chưa ai đọc.
    """
    import approve_document
    n = approve_document.unstamp(layers, REPO_ROOT)
    state["replan_open"] = {"from_stage": state.get("previous_stage"),
                            "wave": (state.get("wave") or {}).get("id"),
                            "unstamped": {"layers": list(layers), "files": n}}


def apply_effects(command: str, evidence: dict, state: dict) -> None:
    """Mutate `state` in place to reflect runtime fields a command establishes.

    state.complete() only moves `stage`; without this, fields gating later commands
    (e.g. wave_boundaries for start-dev) stay at their init values and block the flow.
    Keyed on the user command (not _auto). Side-effect free except a MATRIX read.
    """
    if command == "discovery-start":
        # Discovery wave entry: ghi nhận spawn active cho wave hiện tại.
        wave = evidence.get("wave")
        if wave:
            state.setdefault("spawn", {})["active"] = f"discovery-{wave}"
        # Quay lại khám phá sau khi đã chạy wave: chỗ thiếu nằm NGOÀI phạm vi đã vạch (năng lực/vai/
        # event/boundary mới) — quyết định mở rộng phạm vi, nên đi qua chỗ được hỏi user. Cả ba lớp
        # phía sau đều sẽ được ký lại khi đi qua chốt của chúng.
        if state.get("previous_stage") in ("WAVE_OPEN", "DONE"):
            _open_replan(state, ("discovery", "domain", "design"))

    elif command == "discovery-end":
        # D3 charter-author chốt service_prefix (derive PROJECT). Audit force override.
        prefix = evidence.get("service_prefix")
        if prefix:
            state.setdefault("project", {})["service_prefix"] = prefix
        if evidence.get("force") is True:
            _append_decision(
                f"discovery-end {evidence.get('wave','?')} --force",
                evidence.get("reason") or "(no reason given)",
            )

    elif command in ("domain-po", "domain-ba"):
        # Author business doc (plain VN) ở docs/domain/. spawn po (EPIC/FEATURE/JOURNEY) | ba (BR/PERSONA).
        mode = evidence.get("mode")
        if mode:
            state.setdefault("spawn", {})["active"] = f"{command}-{mode}"
        # Quay lại từ WAVE_OPEN/DONE = bổ sung trong phạm vi đã vạch + chia lại kế hoạch.
        if state.get("previous_stage") in ("WAVE_OPEN", "DONE"):
            _open_replan(state, ("domain", "design"))

    elif command == "domain-approve":
        # Ký business doc (target rỗng = all). Stamp `status: APPROVED` do scripts/domain_approve.py lo
        # (gate domain_stamped verify stamp đã xảy ra trên disk — chặn complete chay).
        if evidence.get("force") is True:
            _append_decision("domain-approve --force", evidence.get("reason") or "(no reason given)")

    elif command == "domain-translate":
        # Dịch docs/domain/ (đã ký) → docs/architecture/ eng. Audit force (bỏ qua gate domain_signed).
        if evidence.get("force") is True:
            _append_decision("domain-translate --force", evidence.get("reason") or "(no reason given)")

    elif command == "domain-end":
        # Audit force override gate DOMAIN.
        if evidence.get("force") is True:
            _append_decision(
                f"domain-end ({state.get('stage','?')}) --force",
                evidence.get("reason") or "(no reason given)",
            )

    elif command == "approve-document":
        # Duyệt xong → phần chia lại đã được đọc, start-wave hết bị chặn.
        state.pop("replan_open", None)
        # Audit force override gate doc_review (vd doc-review chưa chạy nhưng user chủ động approve).
        if evidence.get("force") is True:
            _append_decision("approve-document --force", evidence.get("reason") or "(no reason given)")

    elif command == "start-wave":
        try:
            wave_n = int(evidence.get("wave_n"))
        except (TypeError, ValueError):
            return
        state["wave"] = {"id": f"wave-{wave_n:03d}", "number": wave_n}
        derived = wave_boundaries_from_matrix(wave_n)
        if not derived:
            # MATRIX has no wave tagging → fall back to agent-provided list, if any.
            ev_b = evidence.get("wave_boundaries")
            if isinstance(ev_b, list):
                derived = ev_b
        state["wave_boundaries"] = derived
        state["wave_features"] = wave_features_from_matrix(wave_n)
        state["active_boundary"] = None

    elif command == "start-dev":
        boundary = evidence.get("boundary")
        if boundary:
            state["active_boundary"] = boundary

    elif command == "review-dev":
        # Wave-scoped review: lưu kết quả per-boundary để gate dev-handoff verify cả wave.
        # Dấu wave đi KÈM lúc ghi — list chỉ khoá theo boundary nên tự nó không mang chiều wave;
        # thiếu dấu thì boundary review pass ở wave N xanh hộ wave N+1 (vòng wave không reset).
        rr = evidence.get("review_results")
        if isinstance(rr, list):
            state["review_results"] = rr
            state["review_results_wave"] = (state.get("wave") or {}).get("id")

    elif command == "dev-handoff":
        # Audit force override gate infra_proof (vd env không có Docker → bypass có lý do).
        if evidence.get("force") is True:
            _append_decision("dev-handoff --force", evidence.get("reason") or "(no reason given)")

    elif command == "test-plan":
        # Audit force override gate infra_proof/connectivity.
        if evidence.get("force") is True:
            _append_decision("test-plan --force", evidence.get("reason") or "(no reason given)")

    elif command == "test-execute":
        # DERIVE test_result từ test-report.md (G12) — KHÔNG tin agent tự khai. Chỉ tính auto-TC
        # in-scope (bỏ deferred): all-pass → 'pass', còn lại → 'fail'. Fallback evidence khi force/thiếu file.
        # → gate end-wave (test_passed) đọc giá trị honest này, ép re-run xanh sau fix.
        derived = gates.derive_test_result(state)
        tr = derived if derived is not None else evidence.get("test_result")
        if tr:
            state["test_result"] = tr
            # Dấu wave đi KÈM lúc ghi — không có nó thì `pass` của wave N làm gate đóng wave N+1
            # xanh trước khi wave N+1 chạy test nào (vòng wave không reset).
            state["test_result_wave"] = (state.get("wave") or {}).get("id")
        tc = evidence.get("test_cases_count")
        if isinstance(tc, int):
            state["test_cases_count"] = tc
        if evidence.get("force") is True:
            _append_decision("test-execute --force", evidence.get("reason") or "(no reason given)")

    elif command == "done-wave":
        # Hard close → BOOTSTRAP: clear per-wave runtime fields so STATE is a clean slate.
        state["wave"] = {"id": None, "number": None}
        state["wave_boundaries"] = []
        state["wave_features"] = []
        state["active_boundary"] = None
        state["review_results"] = []
        state["test_result"] = None
        state["test_cases_count"] = 0



# ========================================================================
# Helpers
# ========================================================================

def _ok(msg: str, **extra) -> dict:
    return {"ok": True, "message": msg, **extra}


def _err(msg: str, **extra) -> dict:
    return {"ok": False, "error": msg, **extra}


def summary(state: dict | None = None, machine: dict | None = None) -> dict:
    state = state if state is not None else load_state()
    machine = machine if machine is not None else load_machine()
    return {
        "stage": state.get("stage"),
        "previous_stage": state.get("previous_stage"),
        "wave": state.get("wave"),
        "active_boundary": state.get("active_boundary"),
        "wave_boundaries": state.get("wave_boundaries"),
        "allowed_commands": allowed_commands(state, machine),
        "spawn_active": state.get("spawn", {}).get("active"),
        "last_completed": state.get("workflow", {}).get("last_completed"),
        "revision": state.get("meta", {}).get("revision"),
    }


# ========================================================================
# CLI
# ========================================================================

USAGE = """Usage:
  py scripts/state.py show
  py scripts/state.py validate
  py scripts/state.py can <command>
  py scripts/state.py complete <command> '<evidence-json>'
  py scripts/state.py --selftest
"""


def _print_next_step(state: dict | None = None) -> None:
    """In CHỐT KẾ + gate còn đỏ, cho NGƯỜI đọc.

    Gợi ý này vốn chỉ tới được agent: hook `UserPromptSubmit` nhồi header
    `[HARNESS stage=… | next: …]` mỗi lượt. Người gõ CLI thì nhận về JSON thuần — biết đang ở đâu
    mà không biết đi đâu, phải tự tra `allowed_commands` sang tài liệu. Cùng một sự thật, hai người
    đọc, chỉ một người được nghe.

    Kèm gate còn đỏ của chốt được phép: biết TRƯỚC còn thiếu gì, đỡ chạy rồi mới bị chặn.
    Fail-open: thiếu hooks/policies → im lặng, `show` vẫn chạy.
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent / "hooks"))
        import policies
    except Exception:
        return
    st = state if state is not None else load_state()
    try:
        hint = policies.next_step_hint(st)
    except Exception:
        return
    if hint:
        print(f"\nChốt kế: {hint}")
    try:
        for cmd_id in allowed_commands(st):
            ok, errs = gates.check_for_command(cmd_id, st, {})
            if not ok:
                head = errs[0].split("\n")[0]
                more = f" (+{len(errs) - 1} nữa)" if len(errs) > 1 else ""
                print(f"  {cmd_id}: còn đỏ — {head[:110]}{more}")
    except Exception:
        pass


def main(argv: list[str] | None = None) -> int:
    # Force UTF-8 stdout on Windows (cp1252 default breaks Unicode messages)
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(USAGE)
        return 64

    if argv[0] == "--selftest":
        return _selftest()

    cmd = argv[0]

    if cmd == "show":
        print(json.dumps(summary(), indent=2, ensure_ascii=False))
        _print_next_step()
        return 0

    if cmd == "validate":
        errors = validate()
        if errors:
            for e in errors:
                print(f"FAIL: {e}", file=sys.stderr)
            return 1
        print("OK: STATE.json valid against STATE-MACHINE.json")
        return 0

    if cmd == "can":
        if len(argv) < 2:
            print("Usage: state.py can <command>", file=sys.stderr)
            return 64
        target = argv[1]
        st = load_state()
        if can_run(target, st):
            print(f"YES: '{target}' allowed at stage={st['stage']}")
            return 0
        print(
            f"NO: '{target}' not allowed at stage={st['stage']}. "
            f"Allowed: {allowed_commands(st)}",
            file=sys.stderr,
        )
        return 1

    if cmd == "complete":
        if len(argv) < 3:
            print("Usage: state.py complete <command> '<evidence-json>'", file=sys.stderr)
            return 64
        result = complete(argv[1], argv[2])
        if result["ok"]:
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0
        print(json.dumps(result, indent=2, ensure_ascii=False), file=sys.stderr)
        return 1

    print(f"Unknown subcommand: {cmd}", file=sys.stderr)
    print(USAGE, file=sys.stderr)
    return 64


if __name__ == "__main__":
    sys.exit(main())
