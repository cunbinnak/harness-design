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

import discovery_gate
import planning_lint

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


def _matrix_boundary(boundary_id: str | None, root: Path | None = None) -> dict | None:
    """Trả full dict của 1 boundary trong MATRIX (kind + prefix + ...)."""
    if not boundary_id:
        return None
    root = root or REPO_ROOT
    mf = root / "harness" / "SERVICE-BOUNDARY-MATRIX.json"
    if not mf.is_file():
        return None
    try:
        data = json.loads(mf.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    bs = data.get("boundaries", []) if isinstance(data, dict) else data
    for b in bs:
        if isinstance(b, dict) and b.get("boundary_id") == boundary_id:
            return b
    return None


_WEB_STYLE_EXTS = (".css", ".scss", ".sass", ".less")
_CSS_IN_JS_MARKERS = ("styled.", "styled(", "@emotion", "makeStyles", "createUseStyles", "css`", "sx={")


def _web_styling_signals(src_dir: Path) -> dict:
    """Quét src của 1 web boundary → tín hiệu styling: file CSS, tailwind, CSS-in-JS, có className."""
    sig = {"css_files": 0, "has_className": False, "has_css_in_js": False, "has_tailwind": False}
    if not src_dir.is_dir():
        return sig
    for p in src_dir.rglob("*"):
        if not p.is_file():
            continue
        suf = p.suffix.lower()
        if suf in _WEB_STYLE_EXTS:
            sig["css_files"] += 1
            continue
        if suf in (".tsx", ".ts", ".jsx", ".js"):
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if "className=" in txt:
                sig["has_className"] = True
            if any(m in txt for m in _CSS_IN_JS_MARKERS):
                sig["has_css_in_js"] = True
            if "@tailwind" in txt:
                sig["has_tailwind"] = True
    boundary_root = src_dir.parent
    for tw in ("tailwind.config.js", "tailwind.config.ts", "tailwind.config.cjs", "tailwind.config.mjs"):
        if (boundary_root / tw).is_file():
            sig["has_tailwind"] = True
    return sig


def check_web_styling(state: dict, evidence: dict | None = None, root: Path | None = None) -> tuple[bool, str]:
    """Mỗi web boundary phải có CƠ CHẾ STYLING thật (CSS file / tailwind / CSS-in-JS).

    Chặn defect FE chưa-style (unstyled): component dùng `className=` nhưng 0 stylesheet → render HTML
    không màu/layout, KHÔNG đúng `ux-{boundary}.md §design tokens` (rules-web rule 1 + 43-47). Test query
    role/text + review tĩnh đều mù với lỗi này → cần gate tự động. force=true → bypass (audit decisions.md).
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    wave_boundaries = state.get("wave_boundaries") or []
    proj_prefix = ((state.get("project") or {}).get("service_prefix")) or ""
    problems: list[str] = []
    for bid in wave_boundaries:
        b = _matrix_boundary(bid, root)
        kind = (b or {}).get("kind") or _kind_of(bid, root)
        if kind != "web":
            continue
        prefix = (b or {}).get("prefix") or proj_prefix
        src = root / "services" / f"{prefix}-{bid}" / "src"
        if not src.is_dir():
            continue  # chưa scaffold → để infra_proof bắt, không double-fail ở đây
        sig = _web_styling_signals(src)
        styled = sig["css_files"] > 0 or sig["has_tailwind"] or sig["has_css_in_js"]
        if sig["has_className"] and not styled:
            problems.append(
                f"{bid}: dùng className nhưng 0 styling (CSS/tailwind/CSS-in-JS) → FE unstyled "
                f"(không màu/layout), không theo ux-{bid}.md §4 design tokens"
            )
    if problems:
        return False, "; ".join(problems) + " — implement CSS theo ux §4 (design tokens → CSS var) rồi rebuild"
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


_CLOSED_STATUSES = ("closed", "fixed", "wontfix")


def _bugs_open_from_table(text: str) -> list[str] | None:
    """Format BẢNG: header có cột 'bug' (hoặc 'id') + 'status'; mỗi bug = 1 row.
    Trả list bug-id có status ∉ closed/fixed; None nếu KHÔNG tìm thấy bảng hợp lệ."""
    bug_idx = status_idx = None
    open_bugs: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        low = [c.lower() for c in cells]
        if status_idx is None:  # tìm header row
            if "status" in low and ("bug" in low or "id" in low):
                status_idx = low.index("status")
                bug_idx = low.index("bug") if "bug" in low else low.index("id")
            continue
        if all(set(c) <= set("-: ") for c in cells if c):  # separator |---|
            continue
        if len(cells) > max(bug_idx, status_idx):
            bug, st = cells[bug_idx], cells[status_idx].lower()
            if re.fullmatch(r"bug-\d+", bug, re.IGNORECASE) and st not in _CLOSED_STATUSES:
                open_bugs.append(bug)
    return open_bugs if status_idx is not None else None


def _bugs_open_from_headings(text: str) -> list[str]:
    """Format cũ: '## BUG-NNN' + dòng 'status: ...' (fallback tương thích ngược)."""
    pattern = re.compile(r"^##\s+(BUG-\d+)[^\n]*\n(?:.*\n)*?status:\s*(\w+)", re.MULTILINE)
    return [m.group(1) for m in pattern.finditer(text) if m.group(2).lower() not in _CLOSED_STATUSES]


def check_no_open_bugs(state: dict) -> tuple[bool, str]:
    """Parse tracking/wave-{N}/bugs.md (format bảng, fallback heading cũ), count bug status ∉ closed/fixed."""
    wave_id = (state.get("wave") or {}).get("id")
    if not wave_id:
        return True, ""  # no wave → no bugs
    bugs_file = REPO_ROOT / "tracking" / wave_id / "bugs.md"
    if not bugs_file.exists():
        return True, ""  # no bugs.md → no open bugs
    text = bugs_file.read_text(encoding="utf-8")
    open_bugs = _bugs_open_from_table(text)
    if open_bugs is None:  # không phải bảng → thử format heading cũ
        open_bugs = _bugs_open_from_headings(text)
    if open_bugs:
        return False, f"còn {len(open_bugs)} bug open: {open_bugs}"
    return True, ""


_FINDING_CLOSED_STATUSES = ("resolved", "accepted", "wontfix", "closed", "fixed")
_FINDING_BLOCKING_SEV = ("blocker", "major")


def _findings_open_from_table(text: str) -> list[str] | None:
    """Format BẢNG review-findings: header có cột 'finding'(/'id') + 'status' + 'severity'.
    Trả list finding-id `severity ∈ {blocker, major}` và `status` chưa đóng; None nếu không thấy bảng."""
    fid_idx = status_idx = sev_idx = None
    open_findings: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        low = [c.lower() for c in cells]
        if status_idx is None:  # header row
            if "status" in low and "severity" in low and ("finding" in low or "id" in low):
                status_idx = low.index("status")
                sev_idx = low.index("severity")
                fid_idx = low.index("finding") if "finding" in low else low.index("id")
            continue
        if all(set(c) <= set("-: ") for c in cells if c):  # separator |---|
            continue
        if len(cells) > max(fid_idx, status_idx, sev_idx):
            fid, st, sev = cells[fid_idx], cells[status_idx].lower(), cells[sev_idx].lower()
            if (
                re.fullmatch(r"rf-\d+", fid, re.IGNORECASE)
                and sev in _FINDING_BLOCKING_SEV
                and st not in _FINDING_CLOSED_STATUSES
            ):
                open_findings.append(fid)
    return open_findings if status_idx is not None else None


def check_test_passed(state: dict) -> tuple[bool, str]:
    """end-wave: lần /test-execute cuối phải `pass` (đọc `STATE.test_result`).

    Sau /fix-bugs, field này GIỮ NGUYÊN `fail` của lần test trước (fix không đụng) → buộc
    re-run /test-execute cho xanh mới end-wave được. Ép vòng fix ↔ re-run tới khi suite xanh hẳn."""
    tr = state.get("test_result")
    if tr == "pass":
        return True, ""
    return False, (
        f"test_result hiện = {tr!r} (cần 'pass'). Re-run /test-execute cho full suite xanh "
        "trước khi /end-wave (sau fix phải test lại)."
    )


def check_no_open_findings(state: dict) -> tuple[bool, str]:
    """Parse tracking/wave-{N}/review-findings.md → reject nếu còn finding BLOCKER/MAJOR status=open.

    Lưới an toàn ép MAIN spawn fix tới sạch trước khi /review-dev complete (rời REVIEW_DEV)."""
    wave_id = (state.get("wave") or {}).get("id")
    if not wave_id:
        return True, ""
    findings_file = REPO_ROOT / "tracking" / wave_id / "review-findings.md"
    if not findings_file.exists():
        return True, ""  # chưa có file → review chưa phát hiện gì (hoặc chưa chạy)
    open_findings = _findings_open_from_table(findings_file.read_text(encoding="utf-8"))
    if open_findings:
        return False, f"còn {len(open_findings)} finding BLOCKER/MAJOR chưa fix: {open_findings} — MAIN spawn fix Mode B tới resolved"
    return True, ""


def check_discovery_wave(evidence: dict, state: dict) -> tuple[bool, str]:
    """Gate /discovery-end (clone ZIP): gate wave ĐANG RỜI (outgoing = state.stage) → tiến wave kế.

    DISC_D0 --discovery-end--> DISC_D1: gate D0. ... DISC_D3 --discovery-end--> DOMAIN: gate D3.
    force=true → bypass (audit ghi ở decisions.md).
    """
    if evidence.get("force") is True:
        return True, ""
    wave = discovery_gate.STAGE_TO_GATE.get(state.get("stage")) or evidence.get("wave")
    if not wave:
        return False, "không xác định wave (state.stage không phải DISC_*; evidence.wave thiếu)"
    passed, errors = discovery_gate.check_gate(str(wave))
    if passed:
        return True, ""
    return False, f"discovery gate {wave} fail: " + "; ".join(errors)


def _phase_gate(evidence: dict, checks: list[dict], label: str) -> tuple[bool, str]:
    """Gate theo artifact disk (artifact_glob/file_exists). evidence.force=true → bypass (audit decisions.md)."""
    if evidence.get("force") is True:
        return True, ""
    errs: list[str] = []
    for c in checks:
        if c["kind"] == "artifact_glob":
            ok, m = check_artifact_glob(c["pattern"], c.get("min_count", 1))
        else:
            ok, m = check_file_exists(c["path"])
        if not ok:
            errs.append(m)
    return (not errs), (f"{label} gate fail: " + "; ".join(errs) if errs else "")


def check_domain_gate(evidence: dict) -> tuple[bool, str]:
    """Gate /domain-end (DOMAIN_AUTHORING → DESIGN): product chia nhỏ ở docs/architecture/.

    Như ZIP (Epic/Feature/BR) nhưng author thẳng docs/architecture/ (single-repo, no translate, no docs/domain).
    """
    return _phase_gate(evidence, [
        {"kind": "artifact_glob", "pattern": "docs/architecture/epics/EP-*.md", "min_count": 1},
        {"kind": "artifact_glob", "pattern": "docs/architecture/feat/FEAT-*.md", "min_count": 1},
        {"kind": "artifact_glob", "pattern": "docs/architecture/business-rules/BR-*.md", "min_count": 1},
    ], "domain")


def _boundaries_from_boundary_map(root: Path | None = None) -> list[tuple[str, str]]:
    """Parse docs/discovery/BOUNDARY-MAP.md → [(boundary_id, kind)] non-placeholder.

    §1 'Backend boundaries' → kind 'backend' (gồm cả bff — phân biệt set ở DESIGN/MATRIX,
       chưa biết lúc /design → gom 'backend-family', chỉ ép HLD+API).
    §2 'Web experiences' → kind 'web'. §3 'Mobile experiences' → kind 'mobile'.
    id nằm trong backtick cột đầu. Bỏ row placeholder (_TBD / không có `id`).
    """
    root = root or REPO_ROOT
    bmap = root / "docs" / "discovery" / "BOUNDARY-MAP.md"
    if not bmap.is_file():
        return []
    text = bmap.read_text(encoding="utf-8", errors="ignore")
    section_kind = {
        r"^##\s+1\.": "backend",
        r"^##\s+2\.": "web",
        r"^##\s+3\.": "mobile",
    }
    out: list[tuple[str, str]] = []
    cur_kind: str | None = None
    for line in text.splitlines():
        for pat, kind in section_kind.items():
            if re.match(pat, line):
                cur_kind = kind
                break
        else:
            if cur_kind and line.lstrip().startswith("|"):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if not cells:
                    continue
                first = cells[0]
                if first.lower() in ("boundary", "experience") or re.match(r"^[\s\-:]+$", first):
                    continue  # header / separator
                m = re.search(r"`([a-z0-9][a-z0-9-]*)`", first)
                if not m:
                    continue  # placeholder row (_TBD, không có `id` backtick)
                out.append((m.group(1), cur_kind))
    return out


def _required_design_files(boundary_id: str, kind: str) -> list[str]:
    """File design BẮT BUỘC theo kind (per-boundary completeness)."""
    if kind in ("web", "mobile"):
        return [
            f"docs/architecture/hld/hld-{boundary_id}.md",
            f"docs/architecture/ux/ux-{boundary_id}.md",
        ]
    # backend-family (backend/bff): HLD + API. data-model để skill/aggregate lo
    # (bff có thể không own data → không hard-gate ở đây).
    return [
        f"docs/architecture/hld/hld-{boundary_id}.md",
        f"docs/architecture/api/api-{boundary_id}.md",
    ]


def check_design_gate(evidence: dict) -> tuple[bool, str]:
    """Gate /design (DESIGN → PLAN): ADR≥3 + INTEG≥1 + **per-boundary kind-aware completeness**.

    Aggregate (cũ): ADR≥3, INTEG≥1. Mới (chắt lọc ZIP per-target MANIFEST): MỖI boundary
    trong BOUNDARY-MAP phải có artifact đúng kind — backend→HLD+API; web/mobile→HLD+UX.
    Đóng gap e2e: web boundary lên PLAN với 0 UX mà gate vẫn xanh.
    """
    if evidence.get("force") is True:
        return True, ""
    # 1. Aggregate floors (cross-cutting, không per-boundary)
    ok, msg = _phase_gate(evidence, [
        {"kind": "artifact_glob", "pattern": "docs/architecture/adr/ADR-*.md", "min_count": 3},
        {"kind": "artifact_glob", "pattern": "docs/architecture/integrations/INTEG-*.md", "min_count": 1},
    ], "design")
    errs: list[str] = [] if ok else [msg]
    # 2. Per-boundary completeness theo BOUNDARY-MAP
    boundaries = _boundaries_from_boundary_map()
    if not boundaries:
        errs.append("design gate: BOUNDARY-MAP.md không có boundary nào (D3 chưa xong?) — không kiểm được per-boundary completeness")
    for bid, kind in boundaries:
        for rel in _required_design_files(bid, kind):
            if not (REPO_ROOT / rel).is_file():
                errs.append(f"boundary {bid!r} (kind={kind}) thiếu {rel}")
    return (not errs), ("; ".join(errs) if errs else "")


def check_plan_gate(evidence: dict) -> tuple[bool, str]:
    """Gate /plan (PLAN → REVIEW): WAVE-SEQUENCE + MATRIX + wave files + KG."""
    return _phase_gate(evidence, [
        {"kind": "file_exists", "path": "docs/plans/WAVE-SEQUENCE.md"},
        {"kind": "file_exists", "path": "harness/SERVICE-BOUNDARY-MATRIX.json"},
        {"kind": "artifact_glob", "pattern": "docs/plans/wave-*.md", "min_count": 1},
        {"kind": "artifact_glob", "pattern": "knowledge-base/*.knowledge-graph.yaml", "min_count": 1},
    ], "plan")


def check_planning_lint(evidence: dict) -> tuple[bool, str]:
    """Lint planning artifacts (epic feature_refs≥2 / feat epic_ref+feat_type / BR related_features≥1
    / ADR ≥2 alternatives / ref-integrity epic↔feat↔BR) qua scripts/planning_lint.py.
    Force-bypass: evidence.force=true → audit."""
    if evidence.get("force") is True:
        return True, ""
    ok, errors = planning_lint.run_lint()
    if ok:
        return True, ""
    return False, "planning-lint fail: " + "; ".join(errors)


def check_plan_integrity(evidence: dict) -> tuple[bool, str]:
    """PLAN-stage referential integrity: mọi FEAT-id trong MATRIX features[] có backing
    FEAT-*.md + depends_on không chu trình / dangling. Catch phantom FEAT-id + bad wave dep
    (single-repo planning quality, không phải plumbing). Force-bypass: evidence.force=true."""
    if evidence.get("force") is True:
        return True, ""
    ok, errors = planning_lint.run_plan_integrity()
    if ok:
        return True, ""
    return False, "plan-integrity fail: " + "; ".join(errors)


# Status (cột cuối row BOUNDARY-MAP) loại bỏ khỏi yêu-cầu-coverage MATRIX (đã chốt không làm).
_BMAP_EXCLUDED_STATUSES = ("deferred", "out-of-scope", "out of scope", "dropped")


def _boundary_map_statuses(root: Path | None = None) -> dict[str, str]:
    """Parse docs/discovery/BOUNDARY-MAP.md → {boundary_id: status_lower} cho row non-placeholder.

    Đọc cột 'Status' (header cuối) per-section. id trong backtick cột đầu. Row placeholder
    (_TBD / không có `id`) bỏ qua — khớp _boundaries_from_boundary_map. Thiếu Status → ''.
    """
    root = root or REPO_ROOT
    bmap = root / "docs" / "discovery" / "BOUNDARY-MAP.md"
    if not bmap.is_file():
        return {}
    text = bmap.read_text(encoding="utf-8", errors="ignore")
    section_pat = (r"^##\s+1\.", r"^##\s+2\.", r"^##\s+3\.")
    out: dict[str, str] = {}
    in_section = False
    status_idx: int | None = None
    for line in text.splitlines():
        if any(re.match(p, line) for p in section_pat):
            in_section = True
            status_idx = None  # reset per-section: header lại
            continue
        if line.startswith("## "):  # rời sang section khác (vd '## 4. Change log')
            in_section = False
            status_idx = None
            continue
        if not in_section or not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells:
            continue
        first = cells[0]
        low = [c.lower() for c in cells]
        if "status" in low and (first.lower() in ("boundary", "experience")):
            status_idx = low.index("status")  # header row của section
            continue
        if re.match(r"^[\s\-:]+$", first):
            continue  # separator |---|
        m = re.search(r"`([a-z0-9][a-z0-9-]*)`", first)
        if not m:
            continue  # placeholder row
        st = cells[status_idx] if (status_idx is not None and status_idx < len(cells)) else ""
        out[m.group(1)] = st.strip().lower()
    return out


def _matrix_boundaries(root: Path | None = None) -> dict[str, str]:
    """Đọc harness/SERVICE-BOUNDARY-MATRIX.json → {boundary_id: kind}."""
    root = root or REPO_ROOT
    matrix_file = root / "harness" / "SERVICE-BOUNDARY-MATRIX.json"
    if not matrix_file.is_file():
        return {}
    try:
        data = json.loads(matrix_file.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}
    boundaries = data.get("boundaries", []) if isinstance(data, dict) else data
    out: dict[str, str] = {}
    for b in boundaries:
        bid = b.get("boundary_id")
        if bid:
            out[bid] = b.get("kind")
    return out


# kind BOUNDARY-MAP section → kind MATRIX chấp nhận được (section1 backend-family = backend|bff).
_COMPATIBLE_KINDS = {
    "backend": ("backend", "bff"),
    "web": ("web",),
    "mobile": ("mobile",),
}


def check_matrix_boundary_coherence(evidence: dict, root: Path | None = None) -> tuple[bool, str]:
    """Gate /plan: MATRIX phải phủ MỌI boundary/experience khai báo ở BOUNDARY-MAP (đúng kind).

    Catch planner âm thầm bỏ rơi boundary đã khai báo (vd web experience không vào MATRIX
    → không bao giờ scaffold/scheduled). Mỗi entry BOUNDARY-MAP non-placeholder mà Status
    KHÔNG phải DEFERRED/OUT-OF-SCOPE/DROPPED → buộc có MATRIX entry cùng id + kind tương thích
    (section1 backend chấp nhận backend|bff; section2 web; section3 mobile).
    MATRIX entry KHÔNG có trong BOUNDARY-MAP → chỉ INFO, không fail.
    Force-bypass: evidence.force=true → audit ghi decisions.md.
    """
    if evidence.get("force") is True:
        return True, ""
    declared = _boundaries_from_boundary_map(root)
    if not declared:
        return False, (
            "matrix-coherence: BOUNDARY-MAP.md không có boundary nào (D3 chưa xong?) — "
            "không kiểm được độ phủ MATRIX"
        )
    statuses = _boundary_map_statuses(root)
    matrix = _matrix_boundaries(root)
    missing: list[str] = []
    mismatch: list[str] = []
    for bid, kind in declared:
        if statuses.get(bid, "") in _BMAP_EXCLUDED_STATUSES:
            continue  # khai báo nhưng đã defer/out-of-scope/dropped → không buộc vào MATRIX
        if bid not in matrix:
            missing.append(f"{bid}({kind})")
            continue
        accepted = _COMPATIBLE_KINDS.get(kind, (kind,))
        if matrix[bid] not in accepted:
            mismatch.append(f"{bid}: BOUNDARY-MAP kind={kind}, MATRIX kind={matrix[bid]!r} (cần ∈ {list(accepted)})")
    extra = sorted(set(matrix) - {b for b, _ in declared})  # INFO only
    errs: list[str] = []
    if missing:
        errs.append("thiếu trong MATRIX (boundary khai báo nhưng planner bỏ rơi): " + ", ".join(sorted(missing)))
    if mismatch:
        errs.append("kind không khớp: " + "; ".join(sorted(mismatch)))
    if errs:
        info = f" [INFO: MATRIX có boundary ngoài BOUNDARY-MAP: {extra}]" if extra else ""
        return False, "matrix-coherence fail: " + "; ".join(errs) + info
    return True, ""


def _parse_docker_ps(text: str) -> list[dict]:
    """Parse output `docker compose ps --format json`.

    Chấp nhận 3 dạng: (a) JSON array; (b) JSON-lines (mỗi container 1 object/dòng);
    (c) object dính nhau `}{` (do `Out-File -NoNewline` trên Windows). Trả list dict.
    """
    text = text.lstrip("﻿").strip()  # bỏ BOM (PowerShell Out-File utf8 thêm BOM)
    if not text:
        return []
    try:
        data = json.loads(text)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        pass
    objs: list[dict] = []
    decoder = json.JSONDecoder()
    idx, n = 0, len(text)
    while idx < n:
        while idx < n and text[idx] in " \t\r\n":
            idx += 1
        if idx >= n:
            break
        try:
            obj, end = decoder.raw_decode(text, idx)
        except json.JSONDecodeError:
            break
        if isinstance(obj, dict):
            objs.append(obj)
        idx = end
    return objs


def check_infra_proof(state: dict, evidence: dict | None = None) -> tuple[bool, str]:
    """Bằng chứng wave services ĐÃ CHẠY THẬT — content-validated, không chỉ file tồn tại.

    Parse tracking/{wave}/docker-ps.json → MỌI boundary trong `wave_boundaries` phải có
    container `State=running` (và Health != unhealthy). Chặn fake kiểu chỉ up Postgres/Redis
    rồi capture file (loophole cũ: `proof.is_file()` pass mọi file). Compose `Service` == boundary_id.

    force=true → bypass (env-block thật, vd không có Docker); audit ghi decisions.md ở apply_effects.
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    wave_id = (state.get("wave") or {}).get("id")
    if not wave_id:
        return False, "chưa có wave (chạy /start-wave trước)"
    proof = REPO_ROOT / "tracking" / wave_id / "docker-ps.json"
    if not proof.is_file():
        return False, (
            f"thiếu proof infra 'tracking/{wave_id}/docker-ps.json' — dev-handoff phải "
            "`docker compose up -d --build` wave services + capture `docker compose ps --format json` ra file này"
        )
    entries = _parse_docker_ps(proof.read_text(encoding="utf-8"))
    if not entries:
        return False, (
            f"'tracking/{wave_id}/docker-ps.json' rỗng/không parse được — "
            "capture lại bằng `docker compose ps --format json`"
        )
    running = {(e.get("Service") or "").strip(): (e.get("State") or "").strip().lower() for e in entries}
    health = {(e.get("Service") or "").strip(): (e.get("Health") or "").strip().lower() for e in entries}
    wave_boundaries = state.get("wave_boundaries") or []
    problems: list[str] = []
    for b in wave_boundaries:
        st = running.get(b)
        if st is None:
            problems.append(f"{b}: KHÔNG có container (service chưa lên)")
        elif st != "running":
            problems.append(f"{b}: State={st!r} (cần 'running')")
        elif health.get(b) == "unhealthy":
            problems.append(f"{b}: Health=unhealthy")
    if problems:
        joined = " ".join(wave_boundaries)
        return False, (
            "docker-ps.json KHÔNG chứng minh wave services chạy: "
            + "; ".join(problems)
            + f" — `docker compose up -d --build {joined}` rồi capture lại docker-ps.json"
        )
    return True, ""


# ========================================================================
# G13 — health-proof (app-readiness, HARNESS-captured — không phải agent tự khai)
# ========================================================================

def _ok_http(status: Any) -> bool:
    try:
        s = int(status)
    except (TypeError, ValueError):
        return False
    return 200 <= s < 400


def check_health_proof(state: dict, evidence: dict | None = None, root: Path | None = None) -> tuple[bool, str]:
    """Mọi wave service phải TRẢ LỜI health probe THẬT — đọc tracking/{wave}/health-proof.json.

    Khác `infra_proof` (container State=running, agent tự ghi docker-ps.json): health-proof.json do
    `scripts/capture_infra_proof.py` (HARNESS chạy, curl /health/ready từng service) sinh ra → chống
    loophole "State=running nhưng app chưa UP / Health='' vì compose không khai healthcheck". Mỗi
    wave boundary phải có 1 probe ok (http 2xx/3xx). force=true → bypass (env không Docker), audit.
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    wave_id = (state.get("wave") or {}).get("id")
    if not wave_id:
        return False, "chưa có wave (chạy /start-wave trước)"
    proof = root / "tracking" / wave_id / "health-proof.json"
    if not proof.is_file():
        return False, (
            f"thiếu 'tracking/{wave_id}/health-proof.json' — chạy "
            f"`py scripts/capture_infra_proof.py` (HARNESS curl /health/ready mỗi wave service) trước /dev-handoff"
        )
    try:
        data = json.loads(proof.read_text(encoding="utf-8").lstrip("﻿"))
    except (ValueError, OSError):
        return False, f"'tracking/{wave_id}/health-proof.json' parse lỗi — capture lại bằng capture_infra_proof.py"
    probes = data.get("probes", data) if isinstance(data, dict) else data
    by_boundary: dict[str, dict] = {}
    for p in (probes or []):
        if isinstance(p, dict) and p.get("boundary"):
            by_boundary[p["boundary"]] = p
    problems: list[str] = []
    for b in (state.get("wave_boundaries") or []):
        p = by_boundary.get(b)
        if p is None:
            problems.append(f"{b}: KHÔNG có probe (capture chưa curl service này)")
        elif not (p.get("ok") is True or _ok_http(p.get("http_status"))):
            problems.append(f"{b}: probe FAIL (http_status={p.get('http_status')!r}, ok={p.get('ok')!r})")
    if problems:
        return False, (
            "health-proof KHÔNG chứng minh app UP: " + "; ".join(problems)
            + " — service phải trả 2xx ở /health/ready (start service thật rồi capture lại)"
        )
    return True, ""


# ========================================================================
# G12 — test-evidence (parse report+log thật, DERIVE test_result) + G1 deferred-scope
# ========================================================================

_NETWORK_CALL_RE = re.compile(
    r"\b(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b\s+\S+\s*(?:->|→|=>)\s*\d{3}"
)
_NETWORK_GROUPS = ("integration", "e2e", "performance", "perf", "security")
_SKIP_DOWN_MARKERS = (
    "service chưa up", "chưa up", "service down", "down", "unreachable",
    "connection refused", "econnrefused", "not running", "unavailable", "no such host",
)


def _parse_md_table_rows(text: str, required_cols: tuple[str, ...]) -> list[dict]:
    """Parse MỌI markdown table có header chứa đủ required_cols (lower) → list dict {col_lower: cell}.

    Header reset ở dòng non-pipe (cho nhiều bảng trong 1 file — vd test-report có bảng theo nhóm).
    """
    rows: list[dict] = []
    header: list[str] | None = None
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            header = None
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells if c):  # separator |---|
            continue
        low = [c.lower() for c in cells]
        if header is None:
            if all(rc in low for rc in required_cols):
                header = low
            continue
        rows.append({header[i]: cells[i] for i in range(min(len(header), len(cells)))})
    return rows


def _registry_auto_rows(text: str) -> list[dict]:
    """Rows type=auto của test-case-registry (header có tc/group/type)."""
    out: list[dict] = []
    for r in _parse_md_table_rows(text, ("tc", "group", "type")):
        tc = (r.get("tc") or "").strip()
        if not re.fullmatch(r"tc-[\w-]+", tc, re.IGNORECASE):
            continue
        if (r.get("type") or "").strip().lower() != "auto":
            continue
        out.append(r)
    return out


def _report_results(text: str) -> dict[str, str]:
    """TC-ID(upper) → result (pass/fail/skip) từ test-report.md (bảng tc+result + dòng 'TC-x: pass')."""
    res: dict[str, str] = {}
    for r in _parse_md_table_rows(text, ("tc", "result")):
        tc = (r.get("tc") or "").strip()
        if not re.fullmatch(r"tc-[\w-]+", tc, re.IGNORECASE):
            continue
        val = (r.get("result") or "").lower()
        norm = "pass" if "pass" in val else "fail" if "fail" in val else "skip" if "skip" in val else ""
        if norm:
            res[tc.upper()] = norm
    for m in re.finditer(r"^\s*(TC-[\w-]+)\s*[:=]\s*(pass|fail|skip)\b", text, re.IGNORECASE | re.MULTILINE):
        res[m.group(1).upper()] = m.group(2).lower()
    return res


def _wave_deferred_tokens(wave_id: str, root: Path) -> set[str]:
    """Token deferred từ docs/plans/{wave_id}.md (heading chứa 'defer') → {FEAT/AC/BR} upper.

    SoT cho phép defer = wave plan (planner control + REVIEW approve). TC chỉ được coi deferred nếu
    feature/AC khớp danh sách này → tag @deferred đơn lẻ KHÔNG đủ (đóng loophole né test bằng tag).
    """
    plan = root / "docs" / "plans" / f"{wave_id}.md"
    if not plan.is_file():
        return set()
    text = plan.read_text(encoding="utf-8", errors="ignore")
    tokens: set[str] = set()
    in_sec = False
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            in_sec = "defer" in line.lower()
            continue
        if not in_sec:
            continue
        for m in re.finditer(r"\b(FEAT-[\w-]+(?::AC-\d+)?|BR-[\w-]+|AC-\d+)\b", line, re.IGNORECASE):
            tokens.add(m.group(1).upper())
    return tokens


def _row_is_deferred(row: dict, deferred: set[str]) -> bool:
    """Row deferred khi tag/note có 'deferred' VÀ feature/AC khớp wave-plan deferred-scope."""
    blob = ((row.get("tags") or "") + " " + (row.get("note") or "")).lower()
    if "deferred" not in blob:
        return False
    if not deferred:
        return False  # wave plan không khai báo deferred-scope → KHÔNG cho defer
    feat = (row.get("feature") or "").strip().upper()
    ac = (row.get("ac") or "").strip().upper()
    combo = f"{feat}:{ac}" if feat and ac else ""
    return bool(({feat, ac, combo} - {""}) & deferred)


def _test_log_text(wave_id: str, tc: str, root: Path) -> str:
    log = root / "tracking" / wave_id / "test-logs" / f"{tc}.log"
    try:
        return log.read_text(encoding="utf-8", errors="ignore") if log.is_file() else ""
    except OSError:
        return ""


def check_test_evidence(state: dict, evidence: dict | None = None, root: Path | None = None) -> tuple[bool, str]:
    """test-execute: bằng chứng auto-TC ĐÃ CHẠY THẬT (không cho tự khai pass — chống "test ảo").

    Đọc registry (auto TC + group + deferred) + test-report.md (result) + test-logs/. Mỗi auto-TC
    in-scope: phải có result trong report; group mạng (integration/e2e/perf/security) khi pass|fail
    phải có network-call `METHOD path -> sts` trong log; skip phải nêu lý do service-down trong log
    (cấm silent-skip). Deferred-TC (khai báo ở wave plan + tag @deferred) → bỏ qua. KHÔNG fail vì
    TC=fail (đó là bug hợp lệ) — chỉ fail khi THIẾU bằng chứng đã chạy. force=true → bypass (audit).
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    wave_id = (state.get("wave") or {}).get("id")
    if not wave_id:
        return False, "chưa có wave"
    reg = root / "tracking" / wave_id / "test-case-registry.md"
    if not reg.is_file():
        return False, f"thiếu 'tracking/{wave_id}/test-case-registry.md' — chạy /test-plan trước"
    rep = root / "tracking" / wave_id / "test-report.md"
    if not rep.is_file():
        return False, f"thiếu 'tracking/{wave_id}/test-report.md' — test-execute phải ghi report (không tự khai)"
    auto_rows = _registry_auto_rows(reg.read_text(encoding="utf-8", errors="ignore"))
    if not auto_rows:
        return True, ""  # wave manual-only → không có gì để verify
    results = _report_results(rep.read_text(encoding="utf-8", errors="ignore"))
    deferred = _wave_deferred_tokens(wave_id, root)
    problems: list[str] = []
    inscope = ran = 0
    for r in auto_rows:
        if _row_is_deferred(r, deferred):
            continue
        inscope += 1
        tc = (r.get("tc") or "").strip().upper()
        group = (r.get("group") or "").strip().lower()
        res = results.get(tc)
        if res is None:
            problems.append(f"{tc}: KHÔNG có trong test-report (chưa chạy?)")
            continue
        if res == "skip":
            if not any(m in _test_log_text(wave_id, tc, root).lower() for m in _SKIP_DOWN_MARKERS):
                problems.append(f"{tc}: skip nhưng log không nêu lý do service-down (silent-skip bị cấm)")
            continue
        ran += 1
        if group in _NETWORK_GROUPS:
            if not _NETWORK_CALL_RE.search(_test_log_text(wave_id, tc, root)):
                problems.append(
                    f"{tc} (group={group}): {res} nhưng log thiếu network-call 'METHOD path -> status' (nghi test ảo)"
                )
        elif not _test_log_text(wave_id, tc, root).strip():
            problems.append(f"{tc} (group={group}): {res} nhưng log rỗng/không có (thiếu bằng chứng đã chạy)")
    if inscope > 0 and ran == 0 and not problems:
        problems.append("0 auto-TC in-scope thực sự chạy (tất cả skip) — test ảo, service phải UP để test")
    if problems:
        return False, "test-evidence fail: " + "; ".join(problems)
    return True, ""


def derive_test_result(state: dict, root: Path | None = None) -> str | None:
    """DERIVE test_result từ test-report.md (KHÔNG tin agent tự khai).

    Chỉ tính auto-TC in-scope (bỏ deferred): mọi cái pass → 'pass'; có fail/skip/thiếu → 'fail'.
    Trả None nếu thiếu registry/report (vd force-bypass) → caller fallback evidence.test_result.
    """
    root = root or REPO_ROOT
    wave_id = (state.get("wave") or {}).get("id")
    if not wave_id:
        return None
    reg = root / "tracking" / wave_id / "test-case-registry.md"
    rep = root / "tracking" / wave_id / "test-report.md"
    if not reg.is_file() or not rep.is_file():
        return None
    auto_rows = _registry_auto_rows(reg.read_text(encoding="utf-8", errors="ignore"))
    if not auto_rows:
        return None
    results = _report_results(rep.read_text(encoding="utf-8", errors="ignore"))
    deferred = _wave_deferred_tokens(wave_id, root)
    inscope = [r for r in auto_rows if not _row_is_deferred(r, deferred)]
    if not inscope:
        return None
    for r in inscope:
        if results.get((r.get("tc") or "").strip().upper()) != "pass":
            return "fail"
    return "pass"


# ========================================================================
# G11 — code-compliance backend (đối xứng web_styling: cấm H2, bắt Dockerfile + config)
# ========================================================================

_H2_BUILD_MARKERS = ("com.h2database", "h2database")
_DDL_CREATE_DROP_RE = re.compile(r"ddl-auto\s*[:=]\s*create-drop", re.IGNORECASE)
_JDBC_H2_RE = re.compile(r"jdbc:h2:", re.IGNORECASE)
_APP_CONFIG_NAMES = ("application.yml", "application.yaml", "application.properties")


def check_code_compliance(state: dict, evidence: dict | None = None, root: Path | None = None) -> tuple[bool, str]:
    """Backend boundary phải runnable + KHÔNG dùng H2 che lỗi prod (đối xứng web_styling).

    Bắt đúng chuỗi defect e2e mà 'test xanh nhờ H2' che (flyway-postgres thiếu, TIMESTAMP vs TIMESTAMPTZ,
    app chạy in-mem khác prod): mỗi backend boundary đã scaffold phải (a) có `Dockerfile` (dev-done ≠
    runnable nếu thiếu); (b) KHÔNG khai H2 trong build (`com.h2database`); (c) config main KHÔNG
    `jdbc:h2:` và KHÔNG `ddl-auto: create-drop`; (d) có ≥1 `application.{yml,yaml,properties}`.
    Test (black-box) + review tĩnh không bắt được → cần gate. force=true → bypass (audit decisions.md).
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    proj_prefix = ((state.get("project") or {}).get("service_prefix")) or ""
    problems: list[str] = []
    for bid in (state.get("wave_boundaries") or []):
        b = _matrix_boundary(bid, root)
        kind = (b or {}).get("kind") or _kind_of(bid, root)
        if kind != "backend":
            continue
        prefix = (b or {}).get("prefix") or proj_prefix
        svc = root / "services" / f"{prefix}-{bid}"
        if not svc.is_dir():
            continue  # chưa scaffold → infra_proof bắt, không double-fail
        # (a) Dockerfile
        if not (svc / "Dockerfile").is_file():
            problems.append(f"{bid}: thiếu Dockerfile (service không build/run được → handoff giả)")
        # (b) H2 trong build file
        for bf in ("pom.xml", "build.gradle", "build.gradle.kts"):
            p = svc / bf
            if p.is_file():
                txt = p.read_text(encoding="utf-8", errors="ignore")
                if any(m in txt for m in _H2_BUILD_MARKERS):
                    problems.append(f"{bid}: {bf} khai H2 (`com.h2database`) — dùng Postgres + Testcontainers (H2 che bug prod)")
        # (c)(d) config main
        cfg_dir = svc / "src" / "main" / "resources"
        cfgs = [cfg_dir / n for n in _APP_CONFIG_NAMES if (cfg_dir / n).is_file()]
        # cũng quét profile config application-*.yml
        if cfg_dir.is_dir():
            cfgs += [p for p in cfg_dir.glob("application-*.*") if p.suffix.lower() in (".yml", ".yaml", ".properties")]
        if not cfgs:
            problems.append(f"{bid}: thiếu application.yml/properties trong src/main/resources (config không tách env)")
        for cfg in cfgs:
            ctxt = cfg.read_text(encoding="utf-8", errors="ignore")
            if _JDBC_H2_RE.search(ctxt):
                problems.append(f"{bid}: {cfg.name} có `jdbc:h2:` — app chạy in-memory khác prod (dùng Postgres)")
            if _DDL_CREATE_DROP_RE.search(ctxt):
                problems.append(f"{bid}: {cfg.name} có `ddl-auto: create-drop` — schema tự sinh che migration drift (dùng Flyway/Liquibase)")
    if problems:
        return False, "code-compliance backend fail: " + "; ".join(problems)
    return True, ""


# ========================================================================
# G4/G6-A — contract_test_present (cặp depends_on phải có TC integration/contract)
# ========================================================================

_CONTRACT_TC_GROUPS = ("contract", "integration", "e2e")


def check_contract_test_present(state: dict, evidence: dict | None = None, root: Path | None = None) -> tuple[bool, str]:
    """Mỗi consumer boundary (có depends_on trong wave) phải có ≥1 auto-TC integration/contract/e2e.

    Đóng gap "thiếu liên kết BE-FE → bug" (BUG-010/011/012): contract FE↔BE chỉ là prose, không gate
    nào ép phải CÓ test cross-boundary. Đọc MATRIX depends_on (cặp trong wave) + registry → consumer
    nào thiếu TC nối → fail. (test_evidence sau đó ép TC ấy chạy THẬT.) force=true → bypass (audit).
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    wave_id = (state.get("wave") or {}).get("id")
    if not wave_id:
        return False, "chưa có wave"
    wave_b = set(state.get("wave_boundaries") or [])
    if not wave_b:
        return True, ""
    # consumer = boundary có ≥1 depends_on cũng nằm trong wave
    consumers: list[str] = []
    for bid in wave_b:
        b = _matrix_boundary(bid, root) or {}
        deps = [d for d in (b.get("depends_on") or []) if d in wave_b]
        if deps:
            consumers.append(bid)
    if not consumers:
        return True, ""  # wave 1-boundary / không cross-boundary → không cần contract TC
    reg = root / "tracking" / wave_id / "test-case-registry.md"
    if not reg.is_file():
        return False, f"thiếu 'tracking/{wave_id}/test-case-registry.md' — /test-plan phải sinh trước"
    rows = _parse_md_table_rows(reg.read_text(encoding="utf-8", errors="ignore"), ("tc", "group", "type"))
    missing: list[str] = []
    for c in consumers:
        has = False
        for r in rows:
            if (r.get("type") or "").strip().lower() != "auto":
                continue
            if (r.get("group") or "").strip().lower() not in _CONTRACT_TC_GROUPS:
                continue
            blob = f"{r.get('boundary','')} {r.get('tags','')}".lower()
            if c.lower() in blob:
                has = True
                break
        if not has:
            missing.append(c)
    if missing:
        return False, (
            "contract/integration TC thiếu cho consumer (cross-boundary không được test): "
            + ", ".join(sorted(missing))
            + " — test-plan thêm ≥1 TC group=contract|integration|e2e nối consumer↔provider"
        )
    return True, ""


# ========================================================================
# G6-B — api transport-consistency (tenant-id qua header/JWT claim, KHÔNG query)
# ========================================================================

# Theo convention api template §2: tenant scope mang `X-Tenant-ID` (hoặc JWT claim).
# Đặt tenant-id vào query string → drift (gốc BUG-012). Path/body resource-id khác → không bắt.
_TENANT_QUERY_RE = re.compile(
    r"[?&](?:tenant|clinic|organization|organisation|org|company|workspace)[_-]?id\b", re.IGNORECASE
)
_TENANT_ID_NAME_RE = re.compile(
    r"\b(?:tenant|clinic|organization|organisation|org|company|workspace)[_-]?id\b", re.IGNORECASE
)


def check_api_transport_consistency(evidence: dict | None = None, root: Path | None = None) -> tuple[bool, str]:
    """API spec KHÔNG được truyền tenant-id qua query string — phải header `X-Tenant-ID`/JWT claim.

    Convention api template §2 (Tenant scope). Gốc BUG-012: endpoint đọc clinic_id chỗ query chỗ body
    → FE interceptor lệch → 400. Lint quét `docs/architecture/api/api-*.md`: tenant-ish id trong query
    string (`?clinic_id=`) hoặc dòng 'Query param' nêu tenant-id → fail. force=true → bypass (audit).
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    api_dir = root / "docs" / "architecture" / "api"
    if not api_dir.is_dir():
        return True, ""
    problems: list[str] = []
    for f in sorted(api_dir.glob("api-*.md")):
        text = f.read_text(encoding="utf-8", errors="ignore")
        hits: set[str] = set()
        for line in text.splitlines():
            if _TENANT_QUERY_RE.search(line):
                hits.add(line.strip()[:80])
            elif "query param" in line.lower() and _TENANT_ID_NAME_RE.search(line):
                hits.add(line.strip()[:80])
        if hits:
            problems.append(f"{f.name}: tenant-id truyền qua query ({len(hits)} chỗ) — phải `X-Tenant-ID` header/JWT")
    if problems:
        return False, (
            "api transport-consistency fail: " + "; ".join(problems)
            + " — chuyển tenant-id sang header/JWT claim (api template §2), nhất quán mọi endpoint"
        )
    return True, ""


# ========================================================================
# Rule dispatch
# ========================================================================

# Per-command gate rules. Each rule = {kind, ...params}.
# kind ∈ {flag, all_boundaries_reviewed, int_min, non_empty, artifact_glob, in_state_list,
#         file_exists, wave_in_matrix, no_open_bugs, no_open_findings, infra_proof, test_passed,
#         discovery_wave, domain_gate, design_gate, plan_gate, matrix_coherence}.
# (coverage per-kind nay gộp trong all_boundaries_reviewed — check_coverage* giữ làm helper unit-tested.)

GATE_RULES: dict[str, list[dict]] = {
    "discovery-start": [
        {"kind": "non_empty", "field": "wave"},
    ],
    "discovery-end": [
        {"kind": "discovery_wave"},  # đọc evidence.wave (D0..D3) → discovery_gate.check_gate
    ],
    "domain-start": [
        {"kind": "non_empty", "field": "mode"},
    ],
    "domain-end": [
        {"kind": "domain_gate"},     # epic+feat+BR ở docs/architecture/ (force bypass + audit)
        {"kind": "planning_lint"},   # epic feature_refs≥2 / feat epic_ref+feat_type / BR related_features≥1 (force bypass)
    ],
    "design": [],   # self-loop re-spawn solution-architect (refine) — KHÔNG gate, KHÔNG advance
    "design-end": [
        {"kind": "design_gate"},   # ADR≥3 + INTEG + per-boundary completeness (force bypass + audit). Advance DESIGN→PLAN
    ],
    "plan": [
        {"kind": "plan_gate"},       # WAVE-SEQUENCE + MATRIX + wave files + KG (force bypass + audit)
        {"kind": "planning_lint"},   # re-check + ADR ≥2 alternatives (ADR có sau DESIGN) (force bypass)
        {"kind": "plan_integrity"},  # MATRIX FEAT-id backing + depends_on no-cycle/no-dangling (force bypass)
        {"kind": "matrix_coherence"},  # MATRIX phủ mọi boundary BOUNDARY-MAP đúng kind (force bypass)
        {"kind": "api_transport"},   # tenant-id qua header/JWT, KHÔNG query (G6 — chống drift BUG-012) (force bypass)
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
    "review-dev": [
        {"kind": "no_open_findings"},  # complete bị chặn tới khi findings BLOCKER/MAJOR fix sạch
    ],
    "dev-handoff": [
        {"kind": "all_boundaries_reviewed"},
        {"kind": "infra_proof"},   # wave services PHẢI lên thật (docker-ps.json content-validated) — chặn handoff khi service chưa chạy
        {"kind": "health_proof"},  # app PHẢI trả 2xx ở /health/ready (health-proof.json HARNESS capture) — State=running chưa đủ
        {"kind": "code_compliance"},  # backend boundary: cấm H2 + bắt Dockerfile/config (G11) — chặn 'test xanh nhờ H2'
        {"kind": "web_styling"},   # web boundary PHẢI có styling thật (CSS/tailwind/CSS-in-JS) — chặn FE unstyled (0 CSS) không theo ux §4
    ],
    "test-plan": [
        {"kind": "flag", "field": "docker_compose_ok", "expected": True},
        {"kind": "flag", "field": "connectivity_ok", "expected": True},
        {"kind": "infra_proof"},
        {"kind": "health_proof"},  # stack còn UP + app reachable (kế thừa từ /dev-handoff)
        {"kind": "contract_test_present"},  # consumer cross-boundary phải có TC contract/integration (G4/G6)
    ],
    "test-execute": [
        {"kind": "int_min", "field": "test_cases_count", "min": 1},
        {"kind": "test_evidence"},  # auto-TC phải có bằng chứng đã chạy thật (report+log+network-call); deferred bỏ qua
    ],
    "fix-bugs": [
        {"kind": "non_empty", "field": "bug_id"},
    ],
    "log-bug": [
        {"kind": "non_empty", "field": "bug_id"},  # log-bug-agent ghi row → trả bug_id
    ],
    "end-wave": [
        {"kind": "flag", "field": "uat_signed", "expected": True},
        {"kind": "test_passed"},  # lần test-execute cuối phải pass (STATE) → ép re-run sau fix
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
        if kind == "no_open_findings":
            return check_no_open_findings(state)
        if kind == "test_passed":
            return check_test_passed(state)
        if kind == "infra_proof":
            return check_infra_proof(state, evidence)
        if kind == "health_proof":
            return check_health_proof(state, evidence)
        if kind == "test_evidence":
            return check_test_evidence(state, evidence)
        if kind == "code_compliance":
            return check_code_compliance(state, evidence)
        if kind == "contract_test_present":
            return check_contract_test_present(state, evidence)
        if kind == "api_transport":
            return check_api_transport_consistency(evidence)
        if kind == "web_styling":
            return check_web_styling(state, evidence)
        if kind == "discovery_wave":
            return check_discovery_wave(evidence, state)
        if kind == "domain_gate":
            return check_domain_gate(evidence)
        if kind == "design_gate":
            return check_design_gate(evidence)
        if kind == "plan_gate":
            return check_plan_gate(evidence)
        if kind == "planning_lint":
            return check_planning_lint(evidence)
        if kind == "plan_integrity":
            return check_plan_integrity(evidence)
        if kind == "matrix_coherence":
            return check_matrix_boundary_coherence(evidence)
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
    # (isolate rule all_boundaries_reviewed — dev-handoff full gate còn có infra_proof, test riêng dưới)
    ok, msg = check_all_boundaries_reviewed(st_pass)
    assert ok, f"all_boundaries_reviewed pass fail: {msg}"

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

    # wave_in_matrix: hermetic — seed MATRIX tạm (wave 1), restore (KHÔNG phụ thuộc file committed)
    import json as _json
    _mf = REPO_ROOT / "harness" / "SERVICE-BOUNDARY-MATRIX.json"
    _orig = _mf.read_text(encoding="utf-8") if _mf.exists() else None
    try:
        _mf.write_text(_json.dumps({"version": 1, "boundaries": [
            {"boundary_id": "x", "kind": "backend", "prefix": "d", "wave": 1}]}), encoding="utf-8")
        assert check_wave_in_matrix({"wave_n": 1})[0] is True
        assert check_wave_in_matrix({"wave_n": 99})[0] is False
        assert check_wave_in_matrix({"wave_n": "x"})[0] is False
    finally:
        if _orig is not None:
            _mf.write_text(_orig, encoding="utf-8")

    # no_open_bugs: parse bảng (bug=row) — đếm status ∉ closed/fixed
    tbl = (
        "# Bugs\n\n"
        "| BUG | title | status | origin | boundary |\n"
        "|-----|-------|--------|--------|----------|\n"
        "| BUG-001 | a | closed | auto | order |\n"
        "| BUG-002 | b | open | manual | order |\n"
        "| BUG-003 | c | fixed | auto | web |\n"
        "| BUG-004 | d | wontfix | manual | web |\n"   # S3/S4 defer — KHÔNG chặn end-wave
    )
    assert _bugs_open_from_table(tbl) == ["BUG-002"], _bugs_open_from_table(tbl)
    # cột đảo thứ tự vẫn parse đúng (theo header)
    tbl2 = "| status | bug |\n|--|--|\n| open | BUG-009 |\n| closed | BUG-010 |\n"
    assert _bugs_open_from_table(tbl2) == ["BUG-009"], _bugs_open_from_table(tbl2)
    # không có bảng → None (để fallback)
    assert _bugs_open_from_table("no table here") is None
    # fallback heading cũ vẫn hoạt động
    old = "## BUG-007 — x\nstatus: open\n\n## BUG-008 — y\nstatus: closed\n"
    assert _bugs_open_from_headings(old) == ["BUG-007"], _bugs_open_from_headings(old)

    # no_open_findings: chỉ BLOCKER/MAJOR status=open mới chặn; MINOR/accepted/resolved bỏ qua
    ftbl = (
        "# Review Findings\n\n"
        "| FINDING | severity | status | boundary | file |\n"
        "|---------|----------|--------|----------|------|\n"
        "| RF-001 | BLOCKER | resolved | order | A.java |\n"
        "| RF-002 | MAJOR | open | order | B.java |\n"
        "| RF-003 | MINOR | open | order | C.java |\n"
        "| RF-004 | BLOCKER | open | web | D.tsx |\n"
        "| RF-005 | MAJOR | accepted | web | E.tsx |\n"
    )
    assert _findings_open_from_table(ftbl) == ["RF-002", "RF-004"], _findings_open_from_table(ftbl)
    assert _findings_open_from_table("no table") is None

    # test_passed: end-wave cần STATE.test_result == pass
    assert check_test_passed({"test_result": "pass"})[0] is True
    assert check_test_passed({"test_result": "fail"})[0] is False
    assert check_test_passed({})[0] is False  # chưa test → chặn

    # infra_proof: content-validated — docker-ps.json phải chứng minh MỌI wave service State=running.
    # Hermetic — ghi file proof tạm vào tracking/<wave tạm>, dọn sau.
    _wid = "wave-zzt"
    _pdir = REPO_ROOT / "tracking" / _wid
    _pfile = _pdir / "docker-ps.json"
    _st_infra = {"wave": {"id": _wid}, "wave_boundaries": ["scheduling", "patient-web"]}
    try:
        _pdir.mkdir(parents=True, exist_ok=True)
        # parser: array, JSON-lines, và object dính nhau }{ đều đọc được
        assert len(_parse_docker_ps('[{"Service":"a","State":"running"}]')) == 1
        assert len(_parse_docker_ps('{"Service":"a"}\n{"Service":"b"}')) == 2
        assert len(_parse_docker_ps('{"Service":"a"}{"Service":"b"}')) == 2
        # (a) LOOPHOLE CŨ: chỉ postgres+redis → phải FAIL (trước đây pass vì chỉ check is_file)
        _pfile.write_text(
            '{"Service":"postgres","State":"running","Health":"healthy"}'
            '{"Service":"redis","State":"running","Health":"healthy"}',
            encoding="utf-8",
        )
        ok, msg = check_infra_proof(_st_infra)
        assert not ok and "scheduling" in msg, f"infra_proof phải chặn fake postgres-only: {msg}"
        # (b) đủ wave services running → pass
        _pfile.write_text(
            '{"Service":"scheduling","State":"running","Health":"healthy"}'
            '{"Service":"patient-web","State":"running","Health":""}'
            '{"Service":"postgres","State":"running","Health":"healthy"}',
            encoding="utf-8",
        )
        assert check_infra_proof(_st_infra)[0] is True, "infra_proof phải pass khi đủ wave services running"
        # (c) service có nhưng unhealthy → fail
        _pfile.write_text(
            '{"Service":"scheduling","State":"running","Health":"unhealthy"}'
            '{"Service":"patient-web","State":"running","Health":""}',
            encoding="utf-8",
        )
        assert check_infra_proof(_st_infra)[0] is False, "infra_proof phải chặn khi service unhealthy"
        # (d) force=true → bypass (env-block thật)
        assert check_infra_proof(_st_infra, {"force": True})[0] is True
        # (e) thiếu file → fail
        _pfile.unlink()
        assert check_infra_proof(_st_infra)[0] is False
    finally:
        if _pfile.exists():
            _pfile.unlink()
        if _pdir.exists():
            _pdir.rmdir()

    # web_styling: web boundary dùng className mà 0 styling → FAIL; có CSS → PASS; force → bypass.
    import tempfile as _tf_ws, shutil as _sh_ws
    _wroot = Path(_tf_ws.mkdtemp(prefix="gates_ws_"))
    try:
        (_wroot / "harness").mkdir(parents=True, exist_ok=True)
        (_wroot / "harness" / "SERVICE-BOUNDARY-MATRIX.json").write_text(
            json.dumps({"version": 1, "boundaries": [
                {"boundary_id": "web1", "kind": "web", "prefix": "demo"},
                {"boundary_id": "api1", "kind": "backend", "prefix": "demo"},
            ]}), encoding="utf-8")
        _wsrc = _wroot / "services" / "demo-web1" / "src"
        _wsrc.mkdir(parents=True, exist_ok=True)
        _ws_state = {"wave_boundaries": ["web1", "api1"], "project": {"service_prefix": "demo"}}
        (_wsrc / "App.tsx").write_text('export const A = () => <div className="x">hi</div>', encoding="utf-8")
        ok, msg = check_web_styling(_ws_state, root=_wroot)
        assert not ok and "web1" in msg, f"web_styling phải chặn FE unstyled: {msg}"
        (_wsrc / "App.css").write_text(".x{color:red}", encoding="utf-8")
        assert check_web_styling(_ws_state, root=_wroot)[0] is True, "web_styling phải pass khi có CSS"
        assert check_web_styling(_ws_state, {"force": True}, root=_wroot)[0] is True
    finally:
        _sh_ws.rmtree(_wroot, ignore_errors=True)
    # cột đảo thứ tự vẫn đúng theo header
    ftbl2 = "| status | severity | finding |\n|--|--|--|\n| open | blocker | RF-009 |\n| open | nit | RF-010 |\n"
    assert _findings_open_from_table(ftbl2) == ["RF-009"], _findings_open_from_table(ftbl2)

    # matrix_coherence: MATRIX phải phủ mọi boundary BOUNDARY-MAP đúng kind.
    # Hermetic — dựng root tạm (BOUNDARY-MAP + MATRIX fixture), không đụng file committed.
    import tempfile as _tempfile

    def _mk_root(bmap_body: str, matrix_boundaries: list[dict]) -> Path:
        d = Path(_tempfile.mkdtemp(prefix="gates_mc_"))
        (d / "docs" / "discovery").mkdir(parents=True, exist_ok=True)
        (d / "harness").mkdir(parents=True, exist_ok=True)
        (d / "docs" / "discovery" / "BOUNDARY-MAP.md").write_text(bmap_body, encoding="utf-8")
        (d / "harness" / "SERVICE-BOUNDARY-MATRIX.json").write_text(
            __import__("json").dumps({"version": 1, "boundaries": matrix_boundaries}), encoding="utf-8"
        )
        return d

    # BOUNDARY-MAP: 2 backend (1 ACTIVE + 1 DEFERRED) + 1 web + 1 mobile placeholder.
    _bmap = (
        "# BOUNDARY-MAP\n\n"
        "## 1. Backend boundaries\n\n"
        "| Boundary | Mission | Owned data | Wave introduced | Status |\n"
        "|---|---|---|---|---|\n"
        "| `order` | x | A | W1 | PROPOSED |\n"
        "| `legacy` | y | B | W9 | DEFERRED |\n\n"
        "## 2. Web experiences\n\n"
        "| Experience | Persona pool | Capabilities exposed | Wave introduced | Status |\n"
        "|---|---|---|---|---|\n"
        "| `store-web` | P1 | cap | W2 | PROPOSED |\n\n"
        "## 3. Mobile experiences\n\n"
        "| Experience | Platform | Persona pool | Wave introduced | Status |\n"
        "|---|---|---|---|---|\n"
        "| _TBD — defer_ | | | | |\n\n"
        "## 4. Change log\n\n"
        "| Date | Wave | Change | DECISION-REF |\n"
        "|---|---|---|---|\n"
        "| 2026-06-13 | D3 | init | — |\n"
    )
    # coherent: order(backend) + store-web(web) đủ; legacy DEFERRED bỏ qua; MATRIX có extra → INFO.
    _r_ok = _mk_root(_bmap, [
        {"boundary_id": "order", "kind": "backend"},
        {"boundary_id": "store-web", "kind": "web"},
        {"boundary_id": "shared-lib", "kind": "backend"},  # ngoài BOUNDARY-MAP → INFO only
    ])
    ok, msg = check_matrix_boundary_coherence({}, root=_r_ok)
    assert ok, f"coherent case nên pass: {msg}"

    # missing: store-web khai báo nhưng MATRIX thiếu → fail, cite store-web.
    _r_missing = _mk_root(_bmap, [{"boundary_id": "order", "kind": "backend"}])
    ok, msg = check_matrix_boundary_coherence({}, root=_r_missing)
    assert (not ok) and "store-web" in msg and "thiếu" in msg, msg

    # kind-mismatch: store-web vào MATRIX nhưng kind=mobile (cần web) → fail.
    _r_mismatch = _mk_root(_bmap, [
        {"boundary_id": "order", "kind": "backend"},
        {"boundary_id": "store-web", "kind": "mobile"},
    ])
    ok, msg = check_matrix_boundary_coherence({}, root=_r_mismatch)
    assert (not ok) and "store-web" in msg and "không khớp" in msg, msg

    # backend section chấp nhận bff cho backend-family (compatible kind).
    _r_bff = _mk_root(_bmap, [
        {"boundary_id": "order", "kind": "bff"},
        {"boundary_id": "store-web", "kind": "web"},
    ])
    ok, _ = check_matrix_boundary_coherence({}, root=_r_bff)
    assert ok, "backend section nên chấp nhận MATRIX kind=bff"

    # force-bypass: ngay cả khi MATRIX rỗng → pass.
    _r_empty = _mk_root(_bmap, [])
    assert check_matrix_boundary_coherence({"force": True}, root=_r_empty) == (True, "")
    assert check_matrix_boundary_coherence({}, root=_r_empty)[0] is False  # no-force → fail

    import shutil as _shutil
    for _d in (_r_ok, _r_missing, _r_mismatch, _r_bff, _r_empty):
        _shutil.rmtree(_d, ignore_errors=True)

    # health_proof (G13): mỗi wave service phải có probe ok; thiếu/down → fail; force bypass.
    import tempfile as _tf_hp
    _hroot = Path(_tf_hp.mkdtemp(prefix="gates_hp_"))
    try:
        _hp_state = {"wave": {"id": "wave-001"}, "wave_boundaries": ["scheduling", "patient-web"]}
        _hpdir = _hroot / "tracking" / "wave-001"
        _hpdir.mkdir(parents=True, exist_ok=True)
        _hpf = _hpdir / "health-proof.json"
        # (a) thiếu file → fail
        assert check_health_proof(_hp_state, root=_hroot)[0] is False
        # (b) đủ probe ok → pass
        _hpf.write_text(json.dumps({"probes": [
            {"boundary": "scheduling", "http_status": 200, "ok": True},
            {"boundary": "patient-web", "http_status": 200, "ok": True},
        ]}), encoding="utf-8")
        assert check_health_proof(_hp_state, root=_hroot)[0] is True, "health_proof phải pass khi đủ probe 2xx"
        # (c) 1 service probe fail (502) → fail, cite boundary
        _hpf.write_text(json.dumps({"probes": [
            {"boundary": "scheduling", "http_status": 502, "ok": False},
            {"boundary": "patient-web", "http_status": 200, "ok": True},
        ]}), encoding="utf-8")
        ok, msg = check_health_proof(_hp_state, root=_hroot)
        assert (not ok) and "scheduling" in msg, msg
        # (d) thiếu probe cho 1 service → fail
        _hpf.write_text(json.dumps({"probes": [
            {"boundary": "scheduling", "http_status": 200, "ok": True},
        ]}), encoding="utf-8")
        ok, msg = check_health_proof(_hp_state, root=_hroot)
        assert (not ok) and "patient-web" in msg, msg
        # (e) force → bypass
        assert check_health_proof(_hp_state, {"force": True}, root=_hroot)[0] is True
    finally:
        _shutil.rmtree(_hroot, ignore_errors=True)

    # test_evidence (G12) + deferred-scope (G1): bằng chứng đã chạy thật; deferred bỏ qua; derive.
    _troot = Path(_tf_hp.mkdtemp(prefix="gates_te_"))
    try:
        _twave = "wave-001"
        _tw = _troot / "tracking" / _twave
        _tlogs = _tw / "test-logs"
        _tlogs.mkdir(parents=True, exist_ok=True)
        (_troot / "docs" / "plans").mkdir(parents=True, exist_ok=True)
        _te_state = {"wave": {"id": _twave}}
        # wave plan khai báo deferred-scope: FEAT-002:AC-3
        (_troot / "docs" / "plans" / f"{_twave}.md").write_text(
            "# Wave 1\n\n## Deferred to later waves\n\n- FEAT-002:AC-3 (auth → wave-2)\n", encoding="utf-8")
        _reg = (
            "| TC | group | type | boundary | feature | AC | BR | pri | tags | note |\n"
            "|----|-------|------|----------|---------|----|----|-----|------|------|\n"
            "| TC-I01 | integration | auto | api | FEAT-001 | AC-1 | — | P0 | @FEAT-001 | |\n"
            "| TC-I02 | security | auto | api | FEAT-002 | AC-3 | — | P0 | @FEAT-002 @deferred | deferred wave-2 |\n"
            "| TC-M01 | uat | manual | api | FEAT-001 | AC-2 | — | P1 | @manual | |\n"
        )
        (_tw / "test-case-registry.md").write_text(_reg, encoding="utf-8")
        # (a) thiếu report → fail
        ok, msg = check_test_evidence(_te_state, root=_troot)
        assert (not ok) and "test-report" in msg, msg
        # (b) report pass nhưng log integration thiếu network-call → fail (nghi test ảo)
        (_tw / "test-report.md").write_text(
            "| TC | Result |\n|----|--------|\n| TC-I01 | PASS |\n", encoding="utf-8")
        (_tlogs / "TC-I01.log").write_text("ran something but no network line\n", encoding="utf-8")
        ok, msg = check_test_evidence(_te_state, root=_troot)
        assert (not ok) and "TC-I01" in msg and "network-call" in msg, msg
        # (c) log có network-call → pass (TC-I02 deferred nên bỏ qua, không đòi bằng chứng)
        (_tlogs / "TC-I01.log").write_text("POST /v1/holds -> 200\nOK\n", encoding="utf-8")
        assert check_test_evidence(_te_state, root=_troot)[0] is True, "in-scope có network-call + deferred bỏ qua → pass"
        # derive: in-scope TC-I01 pass → 'pass' (TC-I02 deferred không tính)
        assert derive_test_result(_te_state, root=_troot) == "pass"
        # (d) TC-I01 FAIL trong report → evidence VẪN pass (có network-call = đã chạy thật, fail là bug hợp lệ)
        (_tw / "test-report.md").write_text(
            "| TC | Result |\n|----|--------|\n| TC-I01 | FAIL |\n", encoding="utf-8")
        assert check_test_evidence(_te_state, root=_troot)[0] is True, "TC fail có bằng chứng → evidence pass"
        # nhưng derive = 'fail' (in-scope không all-pass) → end-wave sẽ chặn
        assert derive_test_result(_te_state, root=_troot) == "fail"
        # (e) tag @deferred nhưng KHÔNG khai báo wave plan → coi in-scope → đòi bằng chứng (đóng loophole)
        _reg_abuse = _reg.replace("| @FEAT-001 | |", "| @FEAT-001 @deferred | deferred (né test) |")
        (_tw / "test-case-registry.md").write_text(_reg_abuse, encoding="utf-8")
        (_tw / "test-report.md").write_text(
            "| TC | Result |\n|----|--------|\n| TC-I01 | SKIP |\n", encoding="utf-8")
        (_tlogs / "TC-I01.log").write_text("skipped by agent\n", encoding="utf-8")
        ok, msg = check_test_evidence(_te_state, root=_troot)
        assert (not ok) and "TC-I01" in msg, f"defer-không-khai-báo phải bị coi in-scope: {msg}"
        # (f) force → bypass
        assert check_test_evidence(_te_state, {"force": True}, root=_troot)[0] is True
    finally:
        _shutil.rmtree(_troot, ignore_errors=True)

    # code_compliance (G11): backend cấm H2 + bắt Dockerfile/config.
    _croot = Path(_tf_hp.mkdtemp(prefix="gates_cc_"))
    try:
        (_croot / "harness").mkdir(parents=True, exist_ok=True)
        (_croot / "harness" / "SERVICE-BOUNDARY-MATRIX.json").write_text(json.dumps({"version": 1, "boundaries": [
            {"boundary_id": "scheduling", "kind": "backend", "prefix": "demo"},
            {"boundary_id": "web1", "kind": "web", "prefix": "demo"},
        ]}), encoding="utf-8")
        _cc_state = {"wave_boundaries": ["scheduling", "web1"], "project": {"service_prefix": "demo"}}
        _svc = _croot / "services" / "demo-scheduling"
        _res = _svc / "src" / "main" / "resources"
        _res.mkdir(parents=True, exist_ok=True)
        # (a) thiếu Dockerfile + pom có H2 + config jdbc:h2 + create-drop → fail nhiều lý do
        (_svc / "pom.xml").write_text("<project><dependency><groupId>com.h2database</groupId></dependency></project>", encoding="utf-8")
        (_res / "application.yml").write_text("spring:\n  datasource:\n    url: jdbc:h2:mem:test\n  jpa:\n    hibernate:\n      ddl-auto: create-drop\n", encoding="utf-8")
        ok, msg = check_code_compliance(_cc_state, root=_croot)
        assert (not ok) and "Dockerfile" in msg and "H2" in msg and "jdbc:h2" in msg and "create-drop" in msg, msg
        # (b) sửa hết → pass: Dockerfile + pom Postgres + config postgres + flyway
        (_svc / "Dockerfile").write_text("FROM eclipse-temurin:21-jre\n", encoding="utf-8")
        (_svc / "pom.xml").write_text("<project><dependency><groupId>org.postgresql</groupId></dependency></project>", encoding="utf-8")
        (_res / "application.yml").write_text("spring:\n  datasource:\n    url: jdbc:postgresql://db:5432/app\n  jpa:\n    hibernate:\n      ddl-auto: validate\n", encoding="utf-8")
        assert check_code_compliance(_cc_state, root=_croot)[0] is True, "code_compliance phải pass khi Postgres + Dockerfile + config"
        # (c) web boundary bỏ qua (chỉ backend); chưa scaffold → bỏ qua (không double-fail)
        # (d) force bypass
        (_res / "application.yml").write_text("url: jdbc:h2:mem:x\n", encoding="utf-8")
        assert check_code_compliance(_cc_state, {"force": True}, root=_croot)[0] is True
    finally:
        _shutil.rmtree(_croot, ignore_errors=True)

    # contract_test_present (G4/G6-A): consumer cross-boundary phải có TC integration/contract.
    _kroot = Path(_tf_hp.mkdtemp(prefix="gates_ct_"))
    try:
        (_kroot / "harness").mkdir(parents=True, exist_ok=True)
        (_kroot / "harness" / "SERVICE-BOUNDARY-MATRIX.json").write_text(json.dumps({"version": 1, "boundaries": [
            {"boundary_id": "scheduling", "kind": "backend", "prefix": "demo"},
            {"boundary_id": "patient-web", "kind": "web", "prefix": "demo", "depends_on": ["scheduling"]},
        ]}), encoding="utf-8")
        _ct_state = {"wave": {"id": "wave-001"}, "wave_boundaries": ["scheduling", "patient-web"]}
        _ctw = _kroot / "tracking" / "wave-001"
        _ctw.mkdir(parents=True, exist_ok=True)
        _regf = _ctw / "test-case-registry.md"
        # (a) registry chỉ có functional của backend → thiếu TC nối patient-web → fail
        _regf.write_text(
            "| TC | group | type | boundary | feature | AC | tags |\n"
            "|----|-------|------|----------|---------|----|------|\n"
            "| TC-I01 | integration | auto | scheduling | FEAT-001 | AC-1 | @FEAT-001 |\n",
            encoding="utf-8")
        ok, msg = check_contract_test_present(_ct_state, root=_kroot)
        assert (not ok) and "patient-web" in msg, msg
        # (b) thêm e2e TC nối patient-web → pass
        _regf.write_text(
            "| TC | group | type | boundary | feature | AC | tags |\n"
            "|----|-------|------|----------|---------|----|------|\n"
            "| TC-I01 | integration | auto | scheduling | FEAT-001 | AC-1 | @FEAT-001 |\n"
            "| TC-E01 | e2e | auto | patient-web | FEAT-001 | AC-1 | @FEAT-001 @platform:web |\n",
            encoding="utf-8")
        assert check_contract_test_present(_ct_state, root=_kroot)[0] is True, "có e2e nối consumer → pass"
        # (c) force bypass
        _regf.write_text("no tc\n", encoding="utf-8")
        assert check_contract_test_present(_ct_state, {"force": True}, root=_kroot)[0] is True
    finally:
        _shutil.rmtree(_kroot, ignore_errors=True)

    # api_transport (G6-B): tenant-id qua query → fail; header/JWT → pass.
    _aroot = Path(_tf_hp.mkdtemp(prefix="gates_at_"))
    try:
        _api = _aroot / "docs" / "architecture" / "api"
        _api.mkdir(parents=True, exist_ok=True)
        # (a) drift: clinic_id trong query string → fail
        (_api / "api-scheduling.md").write_text(
            "## 3.1 Cancel\n| Method · Path | `POST /api/v1/appointments/{id}/cancel?clinic_id=` |\n", encoding="utf-8")
        ok, msg = check_api_transport_consistency(root=_aroot)
        assert (not ok) and "api-scheduling.md" in msg, msg
        # (b) convention: tenant qua header → pass
        (_api / "api-scheduling.md").write_text(
            "## 2. Transport\n| Tenant scope | Mọi request mang `X-Tenant-ID` (hoặc JWT claim) |\n"
            "## 3.1 Cancel\n| Method · Path | `POST /api/v1/appointments/{id}/cancel` |\n", encoding="utf-8")
        assert check_api_transport_consistency(root=_aroot)[0] is True, "tenant qua header → pass"
        # (c) force bypass
        (_api / "api-scheduling.md").write_text("?tenant_id=x\n", encoding="utf-8")
        assert check_api_transport_consistency({"force": True}, root=_aroot)[0] is True
    finally:
        _shutil.rmtree(_aroot, ignore_errors=True)

    print("OK: gates.py selftest passed")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
