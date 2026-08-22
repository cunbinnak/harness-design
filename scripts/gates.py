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
import wave_sequence_lint

REPO_ROOT = Path(__file__).resolve().parent.parent


# ========================================================================
# Đọc tài liệu — DÙNG CHUNG
# ========================================================================

# Hai bước, và thứ tự có lý do: khối comment chiếm TRỌN dòng phải bay cả dòng, không để lại
# dòng trắng. Parser bảng của mình reset header ở dòng non-pipe, nên một dòng trắng chen giữa
# header và hàng đầu tiên làm mất luôn cả bảng — vá lỗ này mà đẻ lỗ kia thì không được.
_COMMENT_LINE_RE = re.compile(r"^[ \t]*<!--.*?-->[ \t]*\r?\n", re.DOTALL | re.MULTILINE)
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def live(text: str) -> str:
    """Nội dung THẬT của tài liệu — đã bỏ khối `<!-- -->`.

    VÌ SAO — template của mình để dòng MẪU trong comment cho người điền dễ bắt chước
    (`<!-- | TC-001 | FEAT-A-001 | AC-1 | ... | -->`). Đếm mà không bỏ chúng ra thì gate
    tính cả ví dụ, và **xanh khi chưa ai viết gì** — đúng kiểu hỏng tệ nhất: gate còn đó,
    báo qua, mà không gác gì.

    Một primitive dùng chung, không strip lẻ ở từng gate: strip lẻ thì gate viết sau quên,
    và không có gì nhắc.
    """
    return COMMENT_RE.sub("", _COMMENT_LINE_RE.sub("", text))


def read_live(p: Path) -> str:
    """Đọc file tài liệu qua `live()`. File không đọc được → chuỗi rỗng (gọi bên ngoài tự xử)."""
    try:
        return live(p.read_text(encoding="utf-8", errors="ignore"))
    except OSError:
        return ""


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


# Coverage report parse — số ĐO THẬT thắng số tự khai (mirror derive test_result).
_JACOCO_LINE_RE = re.compile(r'<counter[^>]*type="LINE"[^>]*missed="(\d+)"[^>]*covered="(\d+)"')


def derive_coverage_pct(boundary_id: str, state: dict, root: Path | None = None) -> float | None:
    """Đọc coverage report THẬT của boundary → pct; None nếu service chưa scaffold / không có report.

    Nguồn theo stack: jacoco XML (Gradle `build/reports/jacoco/**` / Maven `target/site/jacoco/`),
    vitest/jest `coverage/coverage-summary.json`, lcov `coverage/lcov.info` (web/mobile).
    """
    root = root or REPO_ROOT
    b = _matrix_boundary(boundary_id, root) or {}
    prefix = b.get("prefix") or ((state.get("project") or {}).get("service_prefix")) or ""
    svc = root / "services" / f"{prefix}-{boundary_id}"
    if not svc.is_dir():
        return None
    # jacoco XML — counter LINE cuối cùng = tổng report-level
    candidates = sorted(svc.glob("build/reports/jacoco/**/*.xml")) + [svc / "target" / "site" / "jacoco" / "jacoco.xml"]
    for p in candidates:
        if not p.is_file():
            continue
        matches = _JACOCO_LINE_RE.findall(p.read_text(encoding="utf-8", errors="ignore"))
        if matches:
            missed, covered = (int(x) for x in matches[-1])
            total = missed + covered
            if total:
                return round(100.0 * covered / total, 1)
    # vitest/jest coverage-summary.json
    cs = svc / "coverage" / "coverage-summary.json"
    if cs.is_file():
        try:
            pct = (json.loads(cs.read_text(encoding="utf-8")).get("total") or {}).get("lines", {}).get("pct")
            if isinstance(pct, (int, float)):
                return float(pct)
        except (ValueError, OSError):
            pass
    # lcov.info (flutter/web fallback)
    lc = svc / "coverage" / "lcov.info"
    if lc.is_file():
        lf = lh = 0
        for line in lc.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith("LF:"):
                lf += int(line[3:] or 0)
            elif line.startswith("LH:"):
                lh += int(line[3:] or 0)
        if lf:
            return round(100.0 * lh / lf, 1)
    return None


def check_all_boundaries_reviewed(state: dict, evidence: dict | None = None, root: Path | None = None) -> tuple[bool, str]:
    """Mọi boundary trong wave_boundaries phải có review_result=pass + coverage đạt ngưỡng theo kind.

    Nguồn review: STATE.review_results (lưu bởi apply_effects khi review-dev complete). List này chỉ
    khoá theo BOUNDARY nên tự nó KHÔNG mang chiều wave — dấu wave nằm ở `review_results_wave`, đối
    chiếu qua `results_stale()`. Trước đây docstring này khai là "wave-scoped" trong khi thực tế không
    phải: vòng wave không-reset thì boundary review pass ở wave N sẽ xanh hộ wave N+1.
    Coverage KHÔNG tin số tự khai: service đã scaffold → HARNESS derive từ coverage report thật
    (jacoco/coverage-summary/lcov); có report → số đo thắng số khai; scaffold rồi mà KHÔNG có report
    → fail (chạy test với coverage rồi review lại). Chưa scaffold → fallback số khai (hermetic/smoke).
    force=true → bypass (đồng bộ họ force-bypass dev-handoff: env-block, audit decisions.md ở apply_effects).
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    base = root or REPO_ROOT
    wave_boundaries = state.get("wave_boundaries") or []
    if not wave_boundaries:
        return False, "wave_boundaries rỗng — chưa mở wave?"
    stale = results_stale(state, "review_results")
    if stale and (state.get("review_results") or []):
        return False, stale + " — review lại code của wave này (/run-wave)"
    results = {
        r.get("boundary"): r
        for r in (state.get("review_results") or [])
        if isinstance(r, dict)
    }
    proj_prefix = ((state.get("project") or {}).get("service_prefix")) or ""
    missing, failed, low_cov, no_report = [], [], [], []
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
        derived = derive_coverage_pct(bid, state, base)
        src = "tự khai"
        if derived is not None:
            cov, src = derived, "đo từ report"
        else:
            b = _matrix_boundary(bid, base) or {}
            svc = base / "services" / f"{(b.get('prefix') or proj_prefix)}-{bid}"
            if svc.is_dir():
                no_report.append(
                    f"{bid}: service đã scaffold nhưng KHÔNG có coverage report "
                    f"(jacoco XML / coverage-summary.json / lcov.info) — số tự khai không được tin; "
                    f"chạy test kèm coverage rồi review-dev lại"
                )
                continue
        if not (isinstance(cov, (int, float)) and cov >= min_pct):
            low_cov.append(f"{bid}({kind}):{cov}<{min_pct} ({src})")
    problems = []
    if missing:
        problems.append(f"chưa review: {missing}")
    if failed:
        problems.append(f"review fail: {failed}")
    if low_cov:
        problems.append(f"coverage thiếu: {low_cov}")
    if no_report:
        problems.append("; ".join(no_report))
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
# Component library trưởng thành (chốt qua ADR ui-kit) — có theme system riêng → miễn yêu cầu
# var(--...) như tailwind/CSS-in-JS (token map qua theme, vd antd ConfigProvider).
_UI_LIB_MARKERS = ("from 'antd'", 'from "antd"', "@ant-design/", "antd/dist",
                   "@mui/", "from '@chakra-ui", 'from "@chakra-ui', "from 'primereact", 'from "primereact')


_TOKEN_DEF_RE = re.compile(r"--[\w-]+\s*:")  # định nghĩa CSS custom property (`--color-x: #...`)


def _web_styling_signals(src_dir: Path) -> dict:
    """Quét src của 1 web boundary → tín hiệu styling: file CSS, tailwind, CSS-in-JS, className,
    dùng design-token (`var(--...)`), và ĐỊNH NGHĨA token (`:root { --x: ... }` / import design-tokens)."""
    sig = {"css_files": 0, "has_className": False, "has_css_in_js": False,
           "has_tailwind": False, "has_ui_lib": False, "uses_token": False, "defines_token": False}
    if not src_dir.is_dir():
        return sig
    for p in src_dir.rglob("*"):
        if not p.is_file():
            continue
        suf = p.suffix.lower()
        if suf in _WEB_STYLE_EXTS:
            sig["css_files"] += 1
            try:
                ctxt = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            # G15: dùng design token (CSS var) thay vì hardcode; hoặc import shared design-tokens.
            if "var(--" in ctxt or "@import" in ctxt and "design-tokens" in ctxt:
                sig["uses_token"] = True
            # token phải ĐƯỢC ĐỊNH NGHĨA trong bundle (copy :root hoặc @import design-tokens.css)
            # — dùng var(--...) mà không định nghĩa → resolve rỗng → UI vẫn unstyled.
            if _TOKEN_DEF_RE.search(ctxt) or "design-tokens" in ctxt:
                sig["defines_token"] = True
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
            if any(m in txt for m in _UI_LIB_MARKERS):
                sig["has_ui_lib"] = True
            if "@tailwind" in txt:
                sig["has_tailwind"] = True
            if "var(--" in txt or "design-tokens" in txt:
                sig["uses_token"] = True
            if "design-tokens" in txt:  # import 'design-tokens.css' ở entry = định nghĩa token vào bundle
                sig["defines_token"] = True
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
        styled = sig["css_files"] > 0 or sig["has_tailwind"] or sig["has_css_in_js"] or sig["has_ui_lib"]
        if sig["has_className"] and not styled:
            problems.append(
                f"{bid}: dùng className nhưng 0 styling (CSS/tailwind/CSS-in-JS/component-library) → FE unstyled "
                f"(không màu/layout), không theo ux-{bid}.md design tokens"
            )
            continue
        # G15: style bằng PLAIN CSS (không tailwind/CSS-in-JS/UI-library) thì phải dùng design token
        # (var(--...)) — chống FE bịa màu/spacing rời design-tokens.css. Tailwind/CSS-in-JS/component
        # library (antd/MUI... — token map qua theme, vd ConfigProvider) có cơ chế token riêng → miễn.
        plain_css_only = (sig["css_files"] > 0 and not sig["has_tailwind"]
                          and not sig["has_css_in_js"] and not sig["has_ui_lib"])
        if styled and plain_css_only and not sig["uses_token"]:
            problems.append(
                f"{bid}: CSS không dùng design token `var(--color-/--font-/--space-...)` (hardcode hex/px) "
                f"→ không theo `docs/architecture/ux/design-tokens.css` (G15). Import token + style qua var(--...)"
            )
            continue
        # var(--...) mà token KHÔNG được định nghĩa/import trong bundle → resolve rỗng → UI vẫn
        # unstyled (browser default) dù gate uses_token xanh. Bắt buộc copy/import design-tokens.css.
        if styled and plain_css_only and sig["uses_token"] and not sig["defines_token"]:
            problems.append(
                f"{bid}: CSS dùng var(--...) nhưng KHÔNG định nghĩa/import token nào (thiếu "
                f"`design-tokens.css` copy vào src hoặc `@import`) → var() resolve rỗng, UI vẫn unstyled "
                f"— copy `docs/architecture/ux/design-tokens.css` vào src + import ở entry (main.tsx/index.css)"
            )
    if problems:
        return False, "; ".join(problems) + " — implement CSS theo ux §4 / design-tokens.css (token → CSS var) rồi rebuild"
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


_FINDING_CLOSED_STATUSES = ("resolved", "accepted", "wontfix", "closed", "fixed")
_FINDING_BLOCKING_SEV = ("blocker", "major")




def _findings_open_from_table(text: str, id_pattern: str = r"rf-\d+") -> list[str] | None:
    """Format BẢNG findings: header có cột 'finding'(/'id') + 'status' + 'severity'.
    Trả list finding-id (khớp `id_pattern`) `severity ∈ {blocker, major}` và `status` chưa đóng;
    None nếu không thấy bảng. `id_pattern` mặc định `rf-\\d+` (review-dev); doc-review dùng `dr-\\d+`."""
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
                re.fullmatch(id_pattern, fid, re.IGNORECASE)
                and sev in _FINDING_BLOCKING_SEV
                and st not in _FINDING_CLOSED_STATUSES
            ):
                open_findings.append(fid)
    return open_findings if status_idx is not None else None


def check_doc_review(state: dict, evidence: dict | None = None, root: Path | None = None) -> tuple[bool, str]:
    """Gate /approve-document: doc-review sanity-check phải ĐÃ chạy + KHÔNG còn gap BLOCKER/MAJOR open.

    Mode sanity-check của review-document (gọi KHÔNG argument) quét toàn bộ doc đã author
    (discovery + domain + design + plan): mâu thuẫn cross-doc · thiếu độ phủ (capability-map +
    persona + journey phải có FEAT phủ → bắt thiếu năng lực nền như auth/login) · AC không testable ·
    cross-ref gãy · "Câu hỏi cho Author" chưa chốt → ghi tracking/doc-review-findings.md
    (DR-NNN + severity + status). Gate này ép vá gap BLOCKER/MAJOR trước khi approve → start-wave
    (mirror review-dev no_open_findings, nhưng cho TÀI LIỆU thay vì code).

    Thiếu file → review CHƯA chạy → chặn (ép chạy review-document no-arg trước approve).
    force=true → bypass (audit decisions.md ở apply_effects)."""
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    base = root or REPO_ROOT
    findings_file = base / "tracking" / "doc-review-findings.md"
    if not findings_file.exists():
        return False, (
            "chưa chạy doc-review: thiếu `tracking/doc-review-findings.md` — chạy `review-document` "
            "(KHÔNG argument) để quét gap/mâu thuẫn/thiếu-độ-phủ trước khi approve"
        )
    open_findings = _findings_open_from_table(
        findings_file.read_text(encoding="utf-8"), id_pattern=r"dr-\d+"
    )
    if open_findings is None:
        return False, (
            "doc-review-findings.md không có bảng findings hợp lệ (cần cột finding/severity/status) — "
            "re-run `review-document` no-arg"
        )
    if open_findings:
        return False, (
            f"còn {len(open_findings)} gap tài liệu BLOCKER/MAJOR chưa xử: {open_findings} — sửa qua "
            "`review-document \"<feedback>\"` (hoặc lùi `domain-po`·`domain-ba` author bổ sung → "
            "`domain-approve` → `domain-translate`) tới sạch rồi approve"
        )
    return True, ""


# Doc design/contract sau /approve-document phải mang status đã duyệt (stamp bởi approve_document.py).
_DOC_STAMP_PLAN = [
    ("docs/architecture/adr", ("APPROVED",)),
    ("docs/architecture/hld", ("APPROVED",)),
    ("docs/architecture/data-model", ("APPROVED",)),
    ("docs/architecture/ux", ("APPROVED",)),
    ("docs/architecture/integrations", ("APPROVED",)),
    ("docs/architecture/api", ("ACTIVE", "DEPRECATED")),
    ("docs/architecture/events", ("ACTIVE", "DEPRECATED")),
]
_FM_STATUS_RE = re.compile(r"^\s*status\s*:\s*[\"']?([A-Za-z-]+)", re.MULTILINE)


def check_doc_stamped(evidence: dict | None = None, root: Path | None = None) -> tuple[bool, str]:
    """Gate /approve-document: doc design/contract phải ĐÃ stamp status duyệt trên disk lúc complete.

    Chặn "approve chay" cho lớp DESIGN (mirror domain_stamped của lớp business): approve xong mà
    frontmatter vẫn DRAFT = script `scripts/approve_document.py` chưa chạy. adr/hld/data-model/ux/
    integrations → APPROVED; api/events (contract) → ACTIVE (DEPRECATED giữ nguyên hợp lệ).
    Doc không frontmatter / thư mục rỗng → bỏ qua. force=true → bypass (audit).
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    problems: list[str] = []
    for rel, accepted in _DOC_STAMP_PLAN:
        d = root / rel
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.md")):
            if _is_scaffold_md(p.name):
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            if not text.startswith("---"):
                continue
            end = text.find("\n---", 3)
            m = _FM_STATUS_RE.search(text[:end] if end > 0 else text[:400])
            status = (m.group(1).upper() if m else "")
            if status not in accepted:
                problems.append(f"{rel}/{p.name}: status={status or '(thiếu)'} (cần {'/'.join(accepted)})")
    if problems:
        return False, (
            "doc chưa stamp trạng thái duyệt: " + "; ".join(problems)
            + " — chạy `py scripts/approve_document.py` TRƯỚC khi complete (không approve chay)"
        )
    return True, ""


def results_stale(state: dict, field: str) -> str | None:
    """None = kết quả thuộc ĐÚNG wave hiện tại; str = lý do không tính.

    VÌ SAO CÓ HÀM NÀY — `test_result` và `review_results` là KẾT QUẢ, và trước đây chúng là field
    PHẲNG: chỉ khoá theo boundary/giá trị, không mang dấu wave nào. Chúng vô hại chừng nào `done-wave`
    còn reset STATE về BOOTSTRAP — nhưng vòng wave kiểu VIPER **không reset gì**, nên nếu không đóng
    dấu thì wave N+1 thừa hưởng nguyên `pass` của wave N:
      · test_result=pass của wave N  → /next-wave wave N+1 xanh trước khi chạy test nào;
      · review_results[payment]=pass → wave N+1 lại đụng `payment` là đi thẳng tới dev-handoff mà
        chưa review dòng code nào của wave đó.
    Dấu wave đi kèm ngay lúc GHI (state.apply_effects), gate đối chiếu lúc ĐỌC.

    FAIL-CLOSED có chủ ý: thiếu dấu (STATE cũ, script gãy giữa chừng) → coi như của wave khác. Đếm
    trên vết không rõ nguồn chính là cách kết quả wave cũ xanh hộ wave mới.
    """
    cur = (state.get("wave") or {}).get("id")
    if not cur:
        return None                       # ngoài phạm vi wave → gate khác lo
    stamp = state.get(f"{field}_wave")
    if stamp == cur:
        return None
    if not stamp:
        return f"{field} không mang dấu wave (STATE cũ?) — chạy lại cho wave {cur}"
    return f"{field} là kết quả của {stamp}, không phải {cur} — chạy lại cho wave này"


def check_test_passed(state: dict) -> tuple[bool, str]:
    """end-wave: lần test-execute cuối phải `pass` VÀ thuộc đúng wave hiện tại.

    Sau một lượt sửa, field này GIỮ NGUYÊN `fail` của lần test trước (sửa không đụng) → buộc
    re-run test-execute cho xanh mới end-wave được. Ép vòng fix ↔ re-run tới khi suite xanh hẳn."""
    stale = results_stale(state, "test_result")
    if stale:
        return False, stale + " (/run-wave sẽ chạy lại test cho wave này)"
    tr = state.get("test_result")
    if tr == "pass":
        return True, ""
    return False, (
        f"test_result hiện = {tr!r} (cần 'pass'). Re-run test-execute cho full suite xanh "
        "trước khi đóng wave (sau fix phải test lại)."
    )


def check_no_open_findings(state: dict) -> tuple[bool, str]:
    """Parse tracking/wave-{N}/review-findings.md → reject nếu còn finding BLOCKER/MAJOR status=open.

    Lưới an toàn ép MAIN spawn fix tới sạch trước khi review-dev complete (rời REVIEW_DEV)."""
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
    """Gate discovery-end (clone ZIP): gate wave ĐANG RỜI (outgoing = state.stage) → tiến wave kế.

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


def check_discovery_advance(evidence: dict, state: dict) -> tuple[bool, str]:
    """Gate discovery-start (cơ chế mới start D0→Dn): khi NHẢY TIẾN sang wave kế → gate wave hiện tại.

    arg (evidence.wave) > wave hiện tại (state.stage) = advancing → verify gate wave đang rời.
    arg == wave hiện tại = refine (không gate). BOOTSTRAP→D0 = first-entry (không gate). force bypass.
    """
    if evidence.get("force") is True:
        return True, ""
    cur = discovery_gate.STAGE_TO_GATE.get(state.get("stage"))  # None nếu BOOTSTRAP
    arg = (evidence.get("wave") or "").upper()
    if not cur or arg == cur:
        return True, ""  # first-entry D0 / refine cùng wave → không gate
    passed, errors = discovery_gate.check_gate(str(cur))
    if passed:
        return True, ""
    return False, f"discovery gate {cur} fail (phải đạt trước khi sang {arg}): " + "; ".join(errors)


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
    """Gate domain-end (DOMAIN_AUTHORING → DESIGN): ENG product chia nhỏ ở docs/architecture/.

    docs/architecture/ là ĐẦU RA eng (do domain-translate sinh từ business docs/domain/ đã ký).
    """
    return _phase_gate(evidence, [
        {"kind": "artifact_glob", "pattern": "docs/architecture/epics/EP-*.md", "min_count": 1},
        {"kind": "artifact_glob", "pattern": "docs/architecture/feat/FEAT-*.md", "min_count": 1},
        {"kind": "artifact_glob", "pattern": "docs/architecture/business-rules/BR-*.md", "min_count": 1},
    ], "domain")


# ========================================================================
# #2/#3 — DOMAIN business layer (docs/domain/) + ký (approve) + translate + no-jargon
# ========================================================================
# A1: business plain-VN ở docs/domain/{epics,feat,journeys,business-rules,personas}/ (PO/BA viết + KÝ)
# → domain-translate dịch sang docs/architecture/ (eng). Ký TRƯỚC, dịch SAU.

_DOMAIN_BUSINESS_GLOBS = (
    "docs/domain/epics/EP-*.md",
    "docs/domain/feat/FEAT-*.md",
    "docs/domain/business-rules/BR-*.md",
    "docs/domain/journeys/JOURNEY-*.md",
    "docs/domain/personas/PERSONA-*.md",
)
# Jargon kỹ thuật KHÔNG được lọt vào lớp business (giữ chủ-nghiệp-vụ đọc/ký được). Bảo thủ:
# chỉ token RÕ-RÀNG-kỹ-thuật để tránh false-positive với văn xuôi nghiệp vụ.
_JARGON_RES = [
    re.compile(r"```"),                                  # code fence
    re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE|JOIN|WHERE|FROM)\b\s", re.IGNORECASE),  # SQL
    re.compile(r"/api/|/v\d+/"),                          # API path
    re.compile(r"@\w+\("),                                # annotation @Valid(...)
    re.compile(r"\b\w+(Entity|Repository|Controller|DTO|Service|Dao)\b"),  # class suffix kỹ thuật
    re.compile(r"\b(varchar|bpchar|uuid|jsonb|bigint|timestamptz)\b", re.IGNORECASE),  # SQL type
    re.compile(r"\bHTTP\s*\d{3}\b|\b[2-5]\d{2}\s+(OK|Created|Bad|Unauthorized|Forbidden|Not Found)"),  # status code
]


def _frontmatter_signed(text: str) -> bool:
    """True nếu business doc đã KÝ — frontmatter `status: APPROVED` (ZIP-faithful sign-off)."""
    if not text.startswith("---"):
        return False
    end = text.find("\n---", 3)
    fm = text[:end] if end > 0 else text[:400]
    return re.search(r"^\s*status\s*:\s*[\"']?APPROVED[\"']?\s*$", fm, re.MULTILINE) is not None


def _domain_business_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for g in _DOMAIN_BUSINESS_GLOBS:
        out.extend(root.glob(g))
    return [p for p in out if p.is_file()]


def check_domain_signed(evidence: dict | None = None, root: Path | None = None) -> tuple[bool, str]:
    """Gate domain-translate: MỌI business doc ở docs/domain/ phải `status: APPROVED` (ký TRƯỚC, dịch SAU).

    Chưa author business doc nào → fail. Còn doc chưa ký → fail (liệt kê). force bypass (audit).
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    files = _domain_business_files(root)
    if not files:
        return False, "chưa có business doc nào ở docs/domain/ — domain-po · domain-ba author trước"
    unsigned = [str(p.relative_to(root)).replace("\\", "/") for p in files
                if not _frontmatter_signed(p.read_text(encoding="utf-8", errors="ignore"))]
    if unsigned:
        return False, ("còn business doc CHƯA KÝ (status!=APPROVED): " + ", ".join(sorted(unsigned))
                       + " — domain-approve <id|all> rồi mới domain-translate")
    return True, ""


def check_domain_stamped(evidence: dict | None = None, root: Path | None = None) -> tuple[bool, str]:
    """Gate domain-approve: doc thuộc target phải ĐÃ stamp `status: APPROVED` trên disk lúc complete.

    Chặn "approve chay": MAIN chạy `complete` mà quên chạy `scripts/domain_approve.py` → state nói đã
    ký nhưng file vẫn DRAFT (về sau `domain_signed` fail khó hiểu ở domain-translate). Không có doc
    nào khớp target → vacuous pass (chưa author gì — hermetic/smoke). force=true → bypass (audit).
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    target = (evidence.get("target") or "all").strip()
    files = _domain_business_files(root)
    if target.lower() != "all":
        files = [p for p in files if p.stem == target or p.stem.startswith(target)]
    unsigned = [str(p.relative_to(root)).replace("\\", "/") for p in files
                if not _frontmatter_signed(p.read_text(encoding="utf-8", errors="ignore"))]
    if unsigned:
        return False, (
            "doc CHƯA được stamp `status: APPROVED`: " + ", ".join(sorted(unsigned))
            + f" — chạy `py scripts/domain_approve.py {target}` (script stamp) TRƯỚC khi complete; "
            "KHÔNG complete chay (state nói đã ký mà file vẫn DRAFT)"
        )
    return True, ""


def check_domain_no_jargon(evidence: dict | None = None, root: Path | None = None) -> tuple[bool, str]:
    """Gate domain-approve: doc business KHÔNG được chứa jargon kỹ thuật (giữ chủ-nghiệp-vụ ký được).

    evidence.target = id doc (vd EP-x) hoặc 'all'/rỗng = mọi business doc. Quét token kỹ thuật rõ ràng.
    force bypass (audit).
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    target = (evidence.get("target") or "all").strip()
    files = _domain_business_files(root)
    if target.lower() != "all":
        files = [p for p in files if p.stem == target or p.stem.startswith(target)]
        if not files:
            return False, f"không thấy business doc '{target}' ở docs/domain/"
    problems: list[str] = []
    for p in files:
        txt = p.read_text(encoding="utf-8", errors="ignore")
        # bỏ frontmatter khỏi phạm vi quét (frontmatter có thể có field kỹ thuật hợp lệ)
        body = txt.split("\n---", 1)[1] if txt.startswith("---") and "\n---" in txt else txt
        hits = [rx.pattern for rx in _JARGON_RES if rx.search(body)]
        if hits:
            rel = str(p.relative_to(root)).replace("\\", "/")
            problems.append(f"{rel}: jargon kỹ thuật ({len(hits)} loại)")
    if problems:
        return False, ("business doc CÓ jargon kỹ thuật (phải plain nghiệp vụ để ký): " + "; ".join(problems)
                       + " — bỏ code/SQL/API/class-name; chi tiết kỹ thuật để domain-translate sinh ở eng layer")
    return True, ""


def _boundaries_from_boundary_map(root: Path | None = None) -> list[tuple[str, str]]:
    """Parse docs/discovery/BOUNDARY-MAP.md → [(boundary_id, kind)] non-placeholder.

    §1 'Backend boundaries' → kind 'backend' (gồm cả bff — phân biệt set ở DESIGN/MATRIX,
       chưa biết lúc design → gom 'backend-family', chỉ ép HLD+API).
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
        if re.match(r"^##\s", line):
            # Bất kỳ heading level-2 nào: set kind nếu là §1/2/3, RESET None nếu khác
            # (§4 BFF / §5 Dependency / … KHÔNG phải boundary — tránh parse row của
            #  chúng thành boundary kind=mobile do cur_kind sót lại từ §3).
            cur_kind = next(
                (k for pat, k in section_kind.items() if re.match(pat, line)), None
            )
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


def _screen_map_problems(boundaries: list[tuple[str, str]], root: Path | None = None) -> list[str]:
    """Thiết kế theo MÀN: SCREEN-MAP.md là mục lục gắn màn ↔ boundary ↔ FEAT ↔ mockup.

    Có FE boundary (web/mobile) → `docs/architecture/ux/SCREEN-MAP.md` phải tồn tại với bảng
    (cột tối thiểu `screen | boundary | feat | mockup`):
      (a) MỖI web boundary có ≥1 row (màn được gán rõ, không boundary nào trắng design);
      (b) cột `boundary` của row phải là FE boundary hợp lệ (không gán màn cho boundary ma);
      (c) MỖI row: file mockup tồn tại + (html) dùng design token (var(--)design-tokens.css);
      (d) màn TUÂN THỦ FEAT (khi docs/architecture/feat/ đã có): FEAT-id trong cột `feat` phải có
          file thật (không trace FEAT ma); chiều ngược — MỌI FEAT `has_ui_touchpoint: true`
          (không deferred/dropped) phải xuất hiện ở ≥1 row (FEAT có UI mà 0 màn = bị bỏ rơi).
    Nhiều FE boundary → đây chính là chỗ làm rõ "màn nào thuộc boundary nào, đọc tài liệu nào".
    """
    root = root or REPO_ROOT
    fe = [(b, k) for b, k in boundaries if k in ("web", "mobile")]
    if not fe:
        return []
    fe_ids = {b for b, _ in fe}
    web_ids = {b for b, k in fe if k == "web"}
    smap = root / "docs" / "architecture" / "ux" / "SCREEN-MAP.md"
    if not smap.is_file():
        return [
            "thiếu `docs/architecture/ux/SCREEN-MAP.md` — thiết kế theo MÀN: mục lục screen ↔ boundary ↔ "
            "FEAT ↔ mockup (bảng cột `screen|route|boundary|feat|mockup`; design-ux sinh TRƯỚC khi vẽ)"
        ]
    rows = _parse_md_table_rows(smap.read_text(encoding="utf-8", errors="ignore"), ("screen", "boundary", "mockup"))
    if not rows:
        return ["SCREEN-MAP.md không có bảng hợp lệ (cần cột `screen | boundary | feat | mockup`)"]
    feat_dir = root / "docs" / "architecture" / "feat"
    problems: list[str] = []
    covered: set[str] = set()
    mapped_feats: set[str] = set()
    for r in rows:
        sid = (r.get("screen") or "").strip().strip("`")
        bid = (r.get("boundary") or "").strip().strip("`")
        cell = (r.get("mockup") or "").strip()
        if not sid or sid == "—":
            continue
        # màn tuân thủ FEAT: token cột feat phải trace FEAT thật (chỉ check khi feat/ đã author)
        for m_f in _FEAT_TOKEN_RE.finditer(r.get("feat") or ""):
            fid = m_f.group(0).upper()
            mapped_feats.add(fid)
            if feat_dir.is_dir() and _feat_file_for(fid, root) is None:
                problems.append(f"SCREEN-MAP: màn `{sid}` trace {fid} KHÔNG có file FEAT (màn phục vụ feature ma)")
        if bid not in fe_ids:
            problems.append(f"SCREEN-MAP: màn `{sid}` gán boundary {bid!r} không phải FE boundary nào trong BOUNDARY-MAP")
            continue
        covered.add(bid)
        # mockup cell: `path` / [text](path) / path trần — lấy path .html đầu tiên
        m = re.search(r"[\w./-]+\.html", cell)
        if not m:
            problems.append(f"SCREEN-MAP: màn `{sid}` ({bid}) thiếu đường dẫn mockup .html")
            continue
        rel = m.group(0).lstrip("./")
        p = root / rel
        if not p.is_file():
            p = root / "docs" / "architecture" / "ux" / rel  # cho phép path relative từ ux/
        if not p.is_file():
            problems.append(f"SCREEN-MAP: màn `{sid}` ({bid}) trỏ mockup `{rel}` KHÔNG tồn tại — màn chưa được thiết kế")
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        if "design-tokens.css" not in t and "var(--" not in t:
            problems.append(f"mockup `{rel}` (màn `{sid}`) KHÔNG dùng design token (link design-tokens.css / var(--...))")
    for bid in sorted(web_ids - covered):
        problems.append(
            f"boundary {bid!r} (web) KHÔNG có màn nào trong SCREEN-MAP (boundary trắng design — "
            f"gán màn + mockup ở `ux/mockups/{bid}/`)"
        )
    # Chiều ngược: FEAT có UI (has_ui_touchpoint: true, không deferred/dropped) phải có ≥1 màn
    if feat_dir.is_dir():
        for fp in sorted(feat_dir.glob("FEAT-*.md")):
            if fp.name.startswith("TEMPLATE"):
                continue
            fm = planning_lint.parse_frontmatter(fp.read_text(encoding="utf-8", errors="ignore"))
            if str(fm.get("has_ui_touchpoint") or "").strip().lower() != "true":
                continue
            # opt-out status dùng CHUNG 1 nguồn với plan_integrity (planning_lint) — không chép tay
            if str(fm.get("status") or "").strip().lower() in planning_lint._FEAT_OPTOUT_STATUSES:
                continue
            fid = str(fm.get("id") or fp.stem).upper()
            if fid not in mapped_feats and fp.stem.upper() not in mapped_feats:
                problems.append(
                    f"{fp.name}: FEAT có UI (has_ui_touchpoint) nhưng KHÔNG xuất hiện ở màn nào trong "
                    f"SCREEN-MAP — feature bị bỏ rơi khỏi design (thêm màn hoặc gắn vào màn dùng chung)"
                )
    return problems


def check_design_gate(evidence: dict) -> tuple[bool, str]:
    """Gate design (DESIGN → PLAN): ADR≥3 + INTEG≥1 + **per-boundary kind-aware completeness**.

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
    # Thiết kế theo MÀN: SCREEN-MAP gắn màn ↔ boundary ↔ FEAT ↔ mockup (mockup phải tồn tại + dùng token)
    errs.extend(_screen_map_problems(boundaries))
    # Có web boundary → shared design tokens (SoT) phải tồn tại — mọi web FE consume chung 1 palette,
    # không boundary nào tự bịa màu/spacing (gate web_styling downstream enforce việc DÙNG token).
    if any(k == "web" for _, k in boundaries) and not (
        REPO_ROOT / "docs" / "architecture" / "ux" / "design-tokens.css"
    ).is_file():
        errs.append(
            "có web boundary nhưng thiếu docs/architecture/ux/design-tokens.css "
            "(SoT design token — skill ux-design tạo theo TEMPLATE.design-tokens.css)"
        )
    return (not errs), ("; ".join(errs) if errs else "")


def check_plan_gate(evidence: dict) -> tuple[bool, str]:
    """Gate plan (PLAN → REVIEW): WAVE-SEQUENCE + MATRIX + wave files + KG."""
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
    """Gate plan: MATRIX phải phủ MỌI boundary/experience khai báo ở BOUNDARY-MAP (đúng kind).

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
        return False, "chưa có wave (chạy start-wave trước)"
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
        return False, "chưa có wave (chạy start-wave trước)"
    proof = root / "tracking" / wave_id / "health-proof.json"
    if not proof.is_file():
        return False, (
            f"thiếu 'tracking/{wave_id}/health-proof.json' — chạy "
            f"`py scripts/capture_infra_proof.py` (HARNESS curl /health/ready mỗi wave service) trước dev-handoff"
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
# Marker skip-vì-service-down phải CỤ THỂ (cụm từ, không phải từ đơn): trước đây "down"/"unavailable"
# match cả "dropdown"/"markdown"/"Playwright unavailable" → skip khống lọt như service-down hợp lệ.
_SKIP_DOWN_MARKERS = (
    "service chưa up", "chưa up", "service down", "unreachable",
    "connection refused", "econnrefused", "not running", "no such host",
)
_SCREENSHOT_EXTS = (".png", ".jpg", ".jpeg")
_IMG_MAGIC = (b"\x89PNG", b"\xff\xd8\xff")  # PNG / JPEG


def _parse_md_table_rows(text: str, required_cols: tuple[str, ...]) -> list[dict]:
    """Parse MỌI markdown table có header chứa đủ required_cols (lower) → list dict {col_lower: cell}.

    Header reset ở dòng non-pipe (cho nhiều bảng trong 1 file — vd test-report có bảng theo nhóm).
    """
    rows: list[dict] = []
    header: list[str] | None = None
    for line in live(text).splitlines():   # bỏ dòng MẪU trong <!-- --> trước khi đếm
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


def _row_matches_deferred(row: dict, deferred: set[str]) -> bool:
    """Feature/AC của row có nằm trong deferred-scope wave plan không (bất kể tag)."""
    if not deferred:
        return False
    feat = (row.get("feature") or "").strip().upper()
    ac = (row.get("ac") or "").strip().upper()
    combo = f"{feat}:{ac}" if feat and ac else ""
    return bool(({feat, ac, combo} - {""}) & deferred)


def _row_is_deferred(row: dict, deferred: set[str]) -> bool:
    """Row deferred khi tag/note có 'deferred' VÀ feature/AC khớp wave-plan deferred-scope."""
    blob = ((row.get("tags") or "") + " " + (row.get("note") or "")).lower()
    if "deferred" not in blob:
        return False
    return _row_matches_deferred(row, deferred)


def _health_ok_boundaries(wave_id: str, root: Path) -> set[str]:
    """Boundary có probe ok=true trong health-proof.json (bằng chứng service UP lần capture gần nhất).

    Dùng để đối chiếu skip-vì-service-down: proof nói UP mà TC skip 'service down' = mâu thuẫn
    → hoặc chạy TC thật, hoặc re-run capture_infra_proof.py chứng minh service chết thật.
    """
    f = root / "tracking" / wave_id / "health-proof.json"
    if not f.is_file():
        return set()
    try:
        data = json.loads(f.read_text(encoding="utf-8").lstrip("﻿"))
    except (ValueError, OSError):
        return set()
    probes = data.get("probes", data) if isinstance(data, dict) else data
    return {
        p.get("boundary") for p in (probes or [])
        if isinstance(p, dict) and p.get("boundary") and p.get("ok") is True
    }


def _screenshot_for_tc(wave_id: str, tc: str, root: Path) -> bool:
    """Có screenshot THẬT (PNG/JPEG magic bytes, ≥1KB) cho TC ở tracking/{wave}/screenshots/{TC}*?"""
    d = root / "tracking" / wave_id / "screenshots"
    if not d.is_dir():
        return False
    tcl = tc.lower()
    for p in d.iterdir():
        if not p.is_file() or p.suffix.lower() not in _SCREENSHOT_EXTS:
            continue
        if not p.name.lower().startswith(tcl):
            continue
        try:
            if p.stat().st_size >= 1024 and p.read_bytes()[:4].startswith(_IMG_MAGIC):
                return True
        except OSError:
            continue
    return False


def _test_log_text(wave_id: str, tc: str, root: Path) -> str:
    log = root / "tracking" / wave_id / "test-logs" / f"{tc}.log"
    try:
        return log.read_text(encoding="utf-8", errors="ignore") if log.is_file() else ""
    except OSError:
        return ""


def _failure_documented(wave_id: str, tc: str, root: Path) -> bool:
    """TC FAIL đã ghi được NGUYÊN NHÂN chưa — đọc log của chính TC đó.

    Trước đây phép này đòi mỗi FAIL có một row `BUG-NNN` trong `bugs.md`. Sổ bug đã bỏ: kết quả
    test vốn đã nằm ở `test-report.md`, sổ bug chỉ là bản sao thứ hai của cùng một sự thật và hai
    bản sao thì sớm muộn lệch nhau. Thứ thật sự cần chặn vẫn còn nguyên — "FAIL rồi để đó, không
    ai biết vì sao" — nên đổi sang đòi **log của TC đó có dấu vết lỗi thật**, và `test_passed`
    @end-wave vẫn chặn đóng wave khi còn FAIL. Sửa xong thì chạy lại, report tự xanh.
    """
    txt = _test_log_text(wave_id, tc, root).lower()
    return any(k in txt for k in (
        "error", "exception", "traceback", "assert", "expected", "status: 5", "status: 4",
        "-> 5", "-> 4", "lỗi", "nguyên nhân"))


def check_test_evidence(state: dict, evidence: dict | None = None, root: Path | None = None) -> tuple[bool, str]:
    """test-execute: bằng chứng auto-TC ĐÃ CHẠY THẬT (không cho tự khai pass — chống "test ảo").

    Đọc registry (auto TC + group + deferred) + test-report.md (result) + test-logs/. Mỗi auto-TC
    in-scope: phải có result trong report; group mạng (integration/e2e/perf/security) khi pass|fail
    phải có network-call `METHOD path -> sts` trong log; skip phải nêu lý do service-down trong log
    (cấm silent-skip) VÀ không mâu thuẫn health-proof (proof nói service UP → skip service-down bị
    chặn); TC trên WEB boundary khi pass|fail phải có screenshot thật (PNG/JPEG) ở
    tracking/{wave}/screenshots/ — bằng chứng UI thật render, chống UI-test khống. Deferred-TC
    (khai báo ở wave plan + tag @deferred) → bỏ qua. KHÔNG fail vì TC=fail (đó là bug hợp lệ) —
    chỉ fail khi THIẾU bằng chứng đã chạy. force=true → bypass (audit).
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
        return False, f"thiếu 'tracking/{wave_id}/test-case-registry.md' — chạy test-plan trước"
    rep = root / "tracking" / wave_id / "test-report.md"
    if not rep.is_file():
        return False, f"thiếu 'tracking/{wave_id}/test-report.md' — test-execute phải ghi report (không tự khai)"
    auto_rows = _registry_auto_rows(reg.read_text(encoding="utf-8", errors="ignore"))
    if not auto_rows:
        return True, ""  # wave manual-only → không có gì để verify
    results = _report_results(rep.read_text(encoding="utf-8", errors="ignore"))
    deferred = _wave_deferred_tokens(wave_id, root)
    health_ok = _health_ok_boundaries(wave_id, root)
    problems: list[str] = []
    inscope = ran = 0
    for r in auto_rows:
        if _row_is_deferred(r, deferred):
            continue
        inscope += 1
        tc = (r.get("tc") or "").strip().upper()
        group = (r.get("group") or "").strip().lower()
        boundary = (r.get("boundary") or "").strip()
        res = results.get(tc)
        if res is None:
            problems.append(f"{tc}: KHÔNG có trong test-report (chưa chạy?)")
            continue
        if res == "skip":
            if not any(m in _test_log_text(wave_id, tc, root).lower() for m in _SKIP_DOWN_MARKERS):
                problems.append(f"{tc}: skip nhưng log không nêu lý do service-down (silent-skip bị cấm)")
            elif boundary in health_ok:
                problems.append(
                    f"{tc}: skip 'service-down' MÂU THUẪN health-proof ({boundary} UP ở lần capture gần nhất) "
                    f"— service chết thật thì re-run `py scripts/capture_infra_proof.py` cập nhật proof, "
                    f"còn UP thì phải chạy TC thật"
                )
            continue
        ran += 1
        if group in _NETWORK_GROUPS:
            if not _NETWORK_CALL_RE.search(_test_log_text(wave_id, tc, root)):
                problems.append(
                    f"{tc} (group={group}): {res} nhưng log thiếu network-call 'METHOD path -> status' (nghi test ảo)"
                )
        elif not _test_log_text(wave_id, tc, root).strip():
            problems.append(f"{tc} (group={group}): {res} nhưng log rỗng/không có (thiếu bằng chứng đã chạy)")
        # TC trên WEB boundary → bắt buộc screenshot thật (UI được MỞ thật, không chỉ log text tự viết)
        if _kind_of(boundary, root) == "web" and not _screenshot_for_tc(wave_id, tc, root):
            problems.append(
                f"{tc} (boundary={boundary}, web): {res} nhưng thiếu screenshot "
                f"`tracking/{wave_id}/screenshots/{tc}*.png` (Playwright page.screenshot — bằng chứng UI thật render)"
            )
        # FAIL phải để lại NGUYÊN NHÂN trong log — chống "fail rồi để đó, không ai biết vì sao".
        # (Trước đây đòi một row BUG-NNN; sổ bug đã bỏ vì trùng với test-report.)
        if res == "fail" and not _failure_documented(wave_id, tc, root):
            problems.append(
                f"{tc}: FAIL nhưng log không có dấu vết lỗi (error/exception/assert/status) — "
                "FAIL phải đọc ra được NGUYÊN NHÂN, nếu không thì không ai sửa được. "
                "Sửa xong chạy lại test-execute, report tự xanh")
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
# Feature-state (L05/L07/L08) — DERIVE trạng thái từng FEAT từ bằng chứng, KHÔNG agent tự khai.
# Ghép các mảnh có sẵn: _feat_file_for + _AC_HEADING_RE (AC của FEAT) · registry (TC↔AC) ·
# _report_results (TC→result) · _wave_deferred_tokens (defer). Không parser mới.
# ========================================================================

# State enum (L07 giới hạn 4 — bỏ 'blocked' vì single-repo không có blocker-raise; +'no-file' cho FEAT-id ma).
_FEAT_STATE_ORDER = ("not_started", "active", "passing", "deferred", "no-file")


def derive_feature_states(state: dict, root: Path | None = None) -> list[dict]:
    """DERIVE trạng thái mỗi FEAT in-scope wave → [{feat, state, ac_pass, ac_total, tcs, note}].

    `passing`  = mọi AC in-scope (`### AC-n`, trừ deferred) có ≥1 TC trace + MỌI TC đó pass ở report.
    `active`   = một phần AC pass (0 < ac_pass < ac_total) — feature đang dở.
    `not_started` = 0 AC pass (chưa có TC pass / chưa test).
    `deferred` = FEAT khai deferred ở wave plan. `no-file` = FEAT-id không có file (plan_integrity lo).

    Không cần registry/report tồn tại: thiếu → mọi feat `not_started` (baseline lúc DEV, trước test).
    Đây là VIEW (như derive_test_result); nguồn sự thật là phép derive, không phải file materialized.
    """
    root = root or REPO_ROOT
    wave_id = (state.get("wave") or {}).get("id")
    feats = list(state.get("wave_features") or [])
    if not feats:
        for b in (state.get("wave_boundaries") or []):
            feats += list((_matrix_boundary(b, root) or {}).get("features") or [])
    if not wave_id or not feats:
        return []
    reg_f = root / "tracking" / wave_id / "test-case-registry.md"
    rep_f = root / "tracking" / wave_id / "test-report.md"
    deferred = _wave_deferred_tokens(wave_id, root)
    # (feat, ac) → set TC-id trace nó (từ registry)
    ac_tcs: dict[tuple[str, str], set[str]] = {}
    if reg_f.is_file():
        for r in _parse_md_table_rows(reg_f.read_text(encoding="utf-8", errors="ignore"), ("tc", "feature", "ac")):
            tc = (r.get("tc") or "").strip().upper()
            if not re.fullmatch(r"tc-[\w-]+", tc, re.IGNORECASE):
                continue
            fids = {m.group(0).upper() for m in _FEAT_TOKEN_RE.finditer(r.get("feature") or "")}
            acs = {m.group(0).upper() for m in _AC_TOKEN_RE.finditer(r.get("ac") or "")}
            for f in fids:
                for a in acs:
                    ac_tcs.setdefault((f, a), set()).add(tc)
    results = _report_results(rep_f.read_text(encoding="utf-8", errors="ignore")) if rep_f.is_file() else {}
    out: list[dict] = []
    for fid in feats:
        fidU = str(fid).upper()
        if fidU in deferred:
            out.append({"feat": fidU, "state": "deferred", "ac_pass": 0, "ac_total": 0, "tcs": [], "note": "wave plan defer"})
            continue
        fp = _feat_file_for(fidU, root)
        if fp is None:
            out.append({"feat": fidU, "state": "no-file", "ac_pass": 0, "ac_total": 0, "tcs": [], "note": "FEAT-id không có file"})
            continue
        acs = [a.upper() for a in _AC_HEADING_RE.findall(read_live(fp))]
        acs = [a for a in acs if a not in deferred and f"{fidU}:{a}" not in deferred]
        ac_total = len(acs)
        ac_pass = 0
        tcs_all: set[str] = set()
        for a in acs:
            tcs = ac_tcs.get((fidU, a), set())
            tcs_all |= tcs
            if tcs and all(results.get(t) == "pass" for t in tcs):
                ac_pass += 1
        if ac_total == 0:
            st = "not_started"  # file có nhưng 0 AC — ac_coverage đã fail riêng; ở đây coi chưa khởi động
        elif ac_pass == 0:
            st = "not_started"
        elif ac_pass == ac_total:
            st = "passing"
        else:
            st = "active"
        out.append({"feat": fidU, "state": st, "ac_pass": ac_pass, "ac_total": ac_total,
                    "tcs": sorted(tcs_all), "note": ""})
    return out


def render_feature_state_md(state: dict, root: Path | None = None) -> str:
    """Format derive_feature_states → bảng markdown máy-đọc + người-đọc (clock-in artifact L05)."""
    rows = derive_feature_states(state, root)
    wave_id = (state.get("wave") or {}).get("id") or "-"
    passing = sum(1 for r in rows if r["state"] == "passing")
    scoped = sum(1 for r in rows if r["state"] not in ("deferred", "no-file"))
    lines = [
        f"# Feature State — {wave_id}",
        "",
        "> HARNESS-derived (capture_feature_state.py) — KHÔNG sửa tay (FM-PROOF-FORGE). Nguồn sự thật = "
        "derive từ FEAT `### AC-n` + registry (TC↔AC) + test-report (TC pass). Là clock-in artifact: "
        "session mới đọc để biết feat nào `passing`/`active`/`not_started` mà không cần dò lại.",
        "",
        f"**Tiến độ: {passing}/{scoped} feat in-scope `passing`.**",
        "",
        "| FEAT | state | AC pass/total | TCs |",
        "|---|---|---|---|",
    ]
    for r in rows:
        tcs = ", ".join(r["tcs"]) if r["tcs"] else "—"
        note = f" ({r['note']})" if r["note"] else ""
        lines.append(f"| {r['feat']} | {r['state']}{note} | {r['ac_pass']}/{r['ac_total']} | {tcs} |")
    return "\n".join(lines) + "\n"


def check_features_complete(state: dict, evidence: dict | None = None, root: Path | None = None) -> tuple[bool, str]:
    """Gate end-wave (L07 WIP=1 → enforcement ở điểm SHIP): KHÔNG feat nào được `active` (làm dở).

    `active` = một phần AC pass, phần khác chưa (feature dở dang — chính là overreach: mở feat mới khi
    feat cũ chưa xong). Đây là điều harness quan sát ĐƯỢC bằng máy (derive từ report), thay cho lời-dặn
    WIP=1 trong prompt. CHỈ chặn `active` — KHÔNG chặn `not_started` (AC chỉ-manual chưa ghi report =
    not_started; test_passed/ac_coverage/uat_signed đã phủ). Khác test_passed (auto-TC pass) + ac_coverage
    (AC↔TC design-time): cái này bắt "feat verify được NỬA" ở run-time. force=true → bypass (audit).
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    active = [r for r in derive_feature_states(state, root) if r["state"] == "active"]
    if active:
        detail = "; ".join(f"{r['feat']} ({r['ac_pass']}/{r['ac_total']} AC verified)" for r in active)
        return False, (
            "còn feature LÀM DỞ (state=active — WIP=1: xong hẳn 1 feat mới sang feat kế, L07): " + detail
            + " — hoàn thành nốt AC còn thiếu (mọi AC có TC pass trong report) rồi end-wave"
        )
    return True, ""


# ========================================================================
# design_system_closed (design-end) — có thứ để tuân thủ, trước khi ép tuân thủ
# ========================================================================

DESIGN_SYSTEM = "docs/architecture/ux/DESIGN-SYSTEM.md"
_HEX = re.compile(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")
CONTRAST_MIN = {"thường": 4.5, "lớn": 3.0, "thành phần": 3.0}


def _rgb(hexs: str) -> tuple[int, int, int]:
    h = hexs.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _luminance(rgb: tuple[int, int, int]) -> float:
    def ch(v: float) -> float:
        v /= 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: str, bg: str) -> float:
    a, b = _luminance(_rgb(fg)), _luminance(_rgb(bg))
    hi, lo = max(a, b), min(a, b)
    return round((hi + 0.05) / (lo + 0.05), 2)


def check_design_system_closed(evidence: dict | None = None,
                               root: Path | None = None) -> tuple[bool, str]:
    """`design --end`: có boundary web/mobile → DESIGN-SYSTEM.md phải đủ và ĐÓNG.

    VÌ SAO — harness đang ép tuân thủ một design system chưa được định nghĩa đủ: gate `web_styling`
    bắt FE dùng token, vai `picky` ở `/dogfood` đi kiểm "component thiếu trạng thái bắt buộc" —
    nhưng **không chỗ nào khai trạng thái bắt buộc là gì**, nên nó không có gì để đối chiếu.

    Kiểm bốn thứ máy KHÔNG suy được từ `design-tokens.css`:
      §1 ý đồ thị giác (ba tính từ + neo tham chiếu thật — chỗ để đối chiếu khi cãi nhau đẹp/xấu)
      §3 cặp tương phản — **tự tính tỉ số WCAG từ hex**, không tin lời khai
      §4 kho component ĐÓNG — mỗi dòng có màn dùng + trạng thái bắt buộc, không ô trống
      §5 ba khuôn rỗng/lỗi/đang tải (năm màn không được đẻ ra năm kiểu báo lỗi)

    Backend-only → vacuous pass.
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    if not ({k for _, k in _boundaries_from_boundary_map(root)} & {"web", "mobile"}):
        return True, ""
    f = root / DESIGN_SYSTEM
    if not f.is_file():
        return False, (f"có boundary web/mobile nhưng thiếu {DESIGN_SYSTEM} — chép từ "
                       "TEMPLATE.DESIGN-SYSTEM.md và chốt TRƯỚC khi vẽ mockup "
                       "(token rút ra từ mockup đã vẽ chỉ là bản mô tả màu đã lỡ chọn)")
    text = re.sub(r"<!--.*?-->", "", f.read_text(encoding="utf-8", errors="ignore"), flags=re.S)
    errs: list[str] = []

    def rows(header: str) -> list[list[str]]:
        m = re.search(rf"^##\s*{header}.*?$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
        if not m:
            return []
        out, seen_sep = [], False
        for line in m.group(1).splitlines():
            s = line.strip()
            if not s.startswith("|"):
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                seen_sep = True
                continue
            if seen_sep and not any("{{" in c for c in cells):
                out.append(cells)
        return out

    # §1 ý đồ — phải có nội dung thật, không còn placeholder
    intent = rows(r"1\.")
    if not intent:
        errs.append("§1 ý đồ thị giác chưa điền (ba tính từ + neo tham chiếu THẬT user chỉ ra)")

    # §3 tương phản — TÍNH, không tin lời khai
    pairs = rows(r"3\.")
    if not pairs:
        errs.append("§3 chưa khai cặp tương phản nào")
    for c in pairs:
        if len(c) < 4:
            continue
        fg, bg = _HEX.search(c[1]), _HEX.search(c[2])
        if not (fg and bg):
            errs.append(f"§3 '{c[0]}' thiếu mã hex — không tính được tỉ số")
            continue
        loai = next((k for k in CONTRAST_MIN if k in c[3].lower()), "thường")
        r_ = contrast_ratio(fg.group(0), bg.group(0))
        if r_ < CONTRAST_MIN[loai]:
            errs.append(f"§3 '{c[0]}' tương phản {r_} < {CONTRAST_MIN[loai]} ({loai}) "
                        f"— {fg.group(0)} trên {bg.group(0)}: chữ này người dùng đọc không ra")

    # §4 kho component — đóng, không ô trống
    comps = rows(r"4\.")
    if not comps:
        errs.append("§4 kho component chưa có dòng nào — vai `picky` sẽ không có gì để đối chiếu")
    for c in comps:
        if len(c) < 4 or not c[2] or not c[3]:
            errs.append(f"§4 '{c[1] if len(c) > 1 else '?'}' thiếu 'dùng ở màn' hoặc "
                        "'trạng thái bắt buộc' — component không dùng ở màn nào thì XOÁ dòng")

    # §5 ba khuôn
    khuon = {c[0].lower() for c in rows(r"5\.") if c}
    for need in ("rỗng", "lỗi", "đang tải"):
        if not any(need in k for k in khuon):
            errs.append(f"§5 thiếu khuôn '{need}'")

    return (not errs), ("; ".join(errs) if errs else "")


# ========================================================================
# production_ready (next-wave) — bảy chỗ vận hành trước đây không gate nào chạm
# ========================================================================

PROD_READY = "tracking/PRODUCTION-READY.md"
PER_WAVE = "(mỗi wave)"       # /next-wave bỏ tick khi mở wave
LATER = "(sau môi trường thật)"  # gate KHÔNG đếm — harness chưa có bước deploy
BLANK = "_CHƯA ĐIỀN_"


def check_production_ready(state: dict, evidence: dict | None = None,
                           root: Path | None = None) -> tuple[bool, str]:
    """Đóng wave: checklist sẵn-sàng-vận-hành không còn dòng bỏ trống.

    VÌ SAO — bảy thứ này trước đây KHÔNG gate nào của harness chạm tới: backup · rate limit ·
    error tracking · structured log · secret · HTTPS · rollback. Harness gác rất chặt "code có
    đúng thiết kế không" mà không hỏi "cái này vận hành được chưa".

    KHÔNG đếm mục gắn `(sau môi trường thật)` — backup đã-thử-khôi-phục, HTTPS, push-là-deploy,
    analytics đang-đếm chỉ làm được khi có nơi chạy thật, mà harness dừng ở `/next-wave`. Ép chúng
    thì gate thành gate chết bị force-bypass mãi mãi, và gate chết tệ hơn không có gate. Chúng vẫn
    nằm trong file để không ai quên; chỗ ghi nhận là bảng "Đã cố tình bỏ qua" (cột **Làm lại khi**
    phân biệt *hoãn* với *bỏ*).

    Đếm THEO TỪNG NHÓM, không gộp một con số: "còn 18 mục" không nói được là đang hổng ở bảo mật
    hay ở đo đạc. Mục `(mỗi wave)` bị `/next-wave` bỏ tick khi mở wave — đúng cho code cũ không tự
    đúng cho code mới.
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    f = root / PROD_READY
    if not f.is_file():
        return False, (f"thiếu {PROD_READY} — chép từ "
                       "tracking/_templates/TEMPLATE.production-ready.md rồi rà. "
                       "Bảy chỗ vận hành (backup · rate limit · error tracking · structured log · "
                       "secret · HTTPS · rollback) hiện không gate nào khác chạm tới")
    text = read_live(f)

    group, todo = None, {}
    for line in text.splitlines():
        if line.startswith("## "):
            group = line[3:].strip() if line.startswith("## Nhóm") else None
            continue
        if group and line.strip().startswith("- [ ]") and LATER not in line:
            item = line.strip()[5:].strip()
            m = re.match(r"\*\*(.+?)\*\*", item)  # chỉ lấy TÊN mục, bỏ phần giải thích
            todo.setdefault(group, []).append(m.group(1) if m else item[:60])

    bad = [f"{g}: còn {len(v)} mục — {v[0][:70]}" + (f" (+{len(v) - 1} nữa)" if len(v) > 1 else "")
           for g, v in todo.items()]
    if BLANK in text:
        bad.append(f"khối Rollback còn {text.count(BLANK)} chỗ {BLANK} — điền TRƯỚC khi hỏng, "
                   "lúc đó không ai còn bình tĩnh đọc tài liệu dài")
    if not bad:
        return True, ""
    return False, (
        f"chưa sẵn sàng vận hành ({PROD_READY}):\n      "
        + "\n      ".join(bad)
        + f"\n      Mục `{LATER}` KHÔNG bị đếm. Cố tình bỏ mục khác → ghi bảng "
          '"Đã cố tình bỏ qua" kèm cột **Làm lại khi** rồi mới tick'
    )


# ========================================================================
# mockup_signed (approve-document) — giao diện phải được NGƯỜI xem và chốt
# ========================================================================

SCREEN_MAP = "docs/architecture/ux/SCREEN-MAP.md"
_SIGNED_RE = re.compile(r"^Chốt bởi user\s*:\s*(\d{4}-\d{2}-\d{2})", re.MULTILINE)


def check_mockup_signed(evidence: dict | None = None,
                        root: Path | None = None) -> tuple[bool, str]:
    """Có boundary web/mobile → mockup phải có dòng `Chốt bởi user: <ISO>` ở SCREEN-MAP.

    VÌ SAO — cả một tầng cơ chế đang ép code bám mockup: `design-tokens.css` là SoT màu/nhịp,
    gate `web_styling` chặn FE không dùng token, vai dogfood `picky` đo computed style so với
    token. Tất cả bảo vệ một bản thiết kế mà **chưa ai xem và duyệt**.

    Skill `ux-design` vốn đã dặn "user duyệt đẹp/xấu TRÊN MOCKUP trước khi build" — nhưng lời dặn
    không để lại hiện vật, nên không phân biệt được "đã duyệt" với "chưa ai mở ra xem".

    Backend-only → vacuous pass (không có gì để duyệt).
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    kinds = {k for _, k in _boundaries_from_boundary_map(root)}
    if not (kinds & {"web", "mobile"}):
        return True, ""
    f = root / SCREEN_MAP
    if not f.is_file():
        return False, (f"có boundary web/mobile nhưng thiếu {SCREEN_MAP} "
                       "(mục lục màn — skill `ux-design` sinh trước khi vẽ)")
    if not _SIGNED_RE.search(f.read_text(encoding="utf-8", errors="ignore")):
        return False, (
            f"{SCREEN_MAP} chưa có dòng `Chốt bởi user: <ISO>` — giao diện CHƯA ai xem và duyệt.\n"
            "      Mở mockup cho user bấm thử (`docs/architecture/ux/mockups/{boundary}/*.html`, "
            "mở thẳng bằng trình duyệt), sửa theo phản hồi, rồi ghi ngày chốt.\n"
            "      Phản hồi về hình thức (chữ nhỏ, màu chìm) → sửa TOKEN ở `design-tokens.css` để "
            "nó lan ra mọi màn, KHÔNG sửa tay từng file mockup."
        )
    return True, ""


# ========================================================================
# regression_tc_present (test-plan, wave ≥2) — suite wave cũ phải GIỮ XANH
# ========================================================================

def _delivered_feats(root: Path, before_wave: int) -> dict[str, str]:
    """{FEAT-id: wave đã giao} lấy từ archive/wave-*/DELIVERED.md của các wave TRƯỚC.

    Đọc DELIVERED.md chứ không đọc plan: plan nói ĐỊNH giao gì, DELIVERED nói THẬT SỰ giao được gì
    (máy derive từ registry+report lúc đóng wave). Chỉ lấy dòng `passing` — FEAT hoãn hoặc dở dang
    không phải hợp đồng, ép regression cho chúng là ép sai.
    """
    out: dict[str, str] = {}
    d = root / "archive"
    if not d.is_dir():
        return out
    for f in sorted(d.glob("wave-*/DELIVERED.md")):
        try:
            n = int(re.sub(r"\D", "", f.parent.name) or 0)
        except ValueError:
            continue
        if n >= before_wave:
            continue
        for line in read_live(f).splitlines():
            s = line.strip()
            if not s.startswith("|"):
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) >= 4 and re.fullmatch(r"FEAT-[A-Za-z0-9-]+", cells[0]) \
                    and cells[-1].lower().startswith("passing"):
                out.setdefault(cells[0], f.parent.name)
    return out


def check_regression_tc_present(state: dict, evidence: dict | None = None,
                                root: Path | None = None) -> tuple[bool, str]:
    """test-plan wave ≥2: registry phải có auto-TC cho MỌI FEAT các wave trước đã giao.

    VÌ SAO — registry nằm ở `tracking/{wave}/`, tức MỖI WAVE MỘT FILE MỚI. Không có gì mang TC wave
    cũ sang, nên wave 2 sinh registry sạch là `test-execute` chỉ chạy TC wave 2: **không gì chạy lại
    test wave 1**. Regression lúc đó chỉ còn trông vào dogfood — một lượt soi thủ công, không phải
    suite chạy mọi lần.

    Đây là bất biến VIPER phát biểu thẳng: *smoke test vòng cũ đi theo `make test` và phải GIỮ XANH*.
    Với mình `make test` chính là registry, nên nó phải mang theo TC wave cũ.

    Chỉ đòi FEAT `passing` trong DELIVERED.md — FEAT hoãn/dở dang không phải hợp đồng.
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    wave = state.get("wave") or {}
    n = wave.get("number") or 0
    wave_id = wave.get("id")
    if n < 2 or not wave_id:
        return True, ""
    delivered = _delivered_feats(root, n)
    if not delivered:
        return True, ""      # chưa wave nào đóng đúng cách → không có hợp đồng nào để giữ
    reg = root / "tracking" / wave_id / "test-case-registry.md"
    if not reg.is_file():
        return False, f"thiếu tracking/{wave_id}/test-case-registry.md"
    text = reg.read_text(encoding="utf-8", errors="ignore")
    missing = [f"{f} (giao ở {w})" for f, w in sorted(delivered.items())
               if not re.search(rf"{re.escape(f)}(?![\w-])", text)]
    if missing:
        return False, (
            f"registry wave {n} thiếu TC regression cho FEAT wave trước đã giao: "
            + ", ".join(missing[:6]) + ("…" if len(missing) > 6 else "")
            + f"\n      Registry là file MỚI mỗi wave (`tracking/{wave_id}/`), không tự mang TC cũ "
              "sang — không có TC nào của wave trước thì không gì chạy lại chúng, và regression chỉ "
              "còn trông vào dogfood. Mang ≥1 auto-TC luồng lõi mỗi FEAT sang, tag `@regression`. "
              "Nguồn: archive/wave-*/DELIVERED.md + registry của wave đó trong archive"
        )
    return True, ""


# ========================================================================
# edge_cases_decided (design-end) — ca biên phải ĐƯỢC QUYẾT, không để agent đoán
# ========================================================================

_EDGE_HDR = re.compile(r"^##\s*6\.1\s", re.MULTILINE)


def _edge_rows_unanswered(text: str) -> list[str]:
    """Dòng ca biên chưa có câu trả lời trong §6.1 — trả list mã (E1, B2…).

    "Chưa trả lời" = ô Xử lý rỗng, hoặc còn `{{…}}`. `n/a` TÍNH LÀ đã trả lời — mục đích của
    checklist đóng là ép RÀ QUA hết, không phải ép làm hết (mirror BC-LEDGER §3 và ma trận quyền).
    """
    doc = live(text)
    m = _EDGE_HDR.search(doc)
    if not m:
        return ["<thiếu mục §6.1>"]
    body = doc[m.end():]
    nxt = re.search(r"^##\s", body, re.MULTILINE)
    if nxt:
        body = body[: nxt.start()]
    bad: list[str] = []
    for line in body.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 3 or not re.fullmatch(r"[EB]\d+", cells[0]):
            continue
        answer = cells[2]
        if not answer or re.search(r"\{\{.*?\}\}", answer):
            bad.append(cells[0])
    return bad


def check_edge_cases_decided(evidence: dict | None = None,
                             root: Path | None = None) -> tuple[bool, str]:
    """`design --end`: mỗi HLD phải có §6.1 Ca biên đã quyết, KHÔNG dòng nào bỏ trống.

    VÌ SAO — ca biên kỹ thuật (gửi hai lần · sửa đồng thời · xoá mềm hay cứng · gọi sai thứ tự ·
    hỏng nửa chừng · đọc bản cũ · rỗng · quyền thu hồi giữa chừng) là thứ AC hạnh phúc gần như không
    bao giờ nói tới, mà hệ có trạng thái nào cũng gặp. Không khai ở HLD thì lúc code agent PHẢI đoán
    — và mỗi boundary sẽ đoán một kiểu.

    `n/a — <lý do>` tính là đã trả lời: checklist đóng ép RÀ QUA hết, không ép LÀM hết. Ô trống mới
    là lỗi, vì trống nghĩa là chưa ai quyết chứ không phải không cần.
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    d = root / "docs" / "architecture" / "hld"
    if not d.is_dir():
        return True, ""
    problems: list[str] = []
    for p in sorted(d.glob("hld-*.md")):
        if _is_scaffold_md(p.name):
            continue
        bad = _edge_rows_unanswered(p.read_text(encoding="utf-8", errors="ignore"))
        if bad:
            problems.append(f"{p.name}: {', '.join(bad[:6])}")
    if not problems:
        return True, ""
    return False, (
        "ca biên chưa quyết (HLD §6.1) — " + " · ".join(problems)
        + "\n      Ô `Xử lý` trống = CHƯA AI QUYẾT, và lúc code agent sẽ quyết thay. "
          "Không áp dụng thì ghi `n/a — <lý do>` (rà qua là đủ, không phải làm hết). "
          "Cột `Enforce ở đâu` phải trỏ thứ chặn được (unique index, version, idempotency key), "
          "không phải 'validate ở service'"
    )


# ========================================================================
# discovery_stamped (chốt D3) — Discovery phải được KÝ trước khi sang DOMAIN
# ========================================================================

def check_discovery_stamped(evidence: dict | None = None,
                            root: Path | None = None) -> tuple[bool, str]:
    """Chốt `/discover` (D3 → DOMAIN): doc discovery phải ĐÃ stamp `status: APPROVED`.

    VÌ SAO CÓ GATE NÀY — discovery từng là lớp DUY NHẤT không có chữ ký: domain ký bằng
    `domain_approve.py`, design ký bằng `approve_document.py`, còn discovery thì template có sẵn
    field `status:` mà không script nào stamp. Xác nhận của user nằm trong chat, không thành hiện
    vật — đúng thứ harness bắt mọi chỗ khác phải có ("lời khai không phải bằng chứng"), lại thiếu
    ở lớp THƯỢNG NGUỒN nhất.

    Và ký ở ĐÂY chứ không đợi `/approve-document`: domain + design + plan đều xây trên discovery.
    Đợi tới REVIEW mới đọc chéo nghĩa là phát hiện lỗ ở hypothesis-log sau khi đã dựng ba tầng lên
    trên, phải tháo ngược cả ba. Cùng lý do challenge đặt TRƯỚC khi code.

    Chưa author gì → vacuous pass (`discovery_wave` lo phần "có artifact chưa").
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    import approve_document as _ad
    files = [p for pat, _, _ in _ad.STAMP_PLANS["discovery"] for p in sorted(root.glob(pat))
             if p.is_file() and not _is_scaffold_md(p.name)]
    if not files:
        return True, ""
    unsigned = [str(p.relative_to(root)).replace("\\", "/") for p in files
                if not _frontmatter_signed(p.read_text(encoding="utf-8", errors="ignore"))]
    if unsigned:
        return False, (
            "doc discovery CHƯA ký `status: APPROVED`: " + ", ".join(sorted(unsigned))
            + " — rà chéo một lượt (hypothesis ↔ capability ↔ persona ↔ ES ↔ boundary), trình user, "
              "user OK thì chạy `py scripts/approve_document.py --layer discovery` rồi mới complete. "
              "KHÔNG complete chay: chữ ký trong chat không phải hiện vật"
        )
    return True, ""


# ========================================================================
# backward_compat (end-wave, wave ≥2) — legacy là hợp đồng
# ========================================================================

BC_LEDGER = "tracking/BC-LEDGER.md"


def _bc_section3(text: str) -> list[str] | None:
    """Dòng thuộc §3 của sổ — None khi mất heading '## 3'.

    Phạm vi §3 là hợp đồng chung của HAI chỗ: gate này (đếm) và `next_wave.py` (bỏ tick khi mở wave).
    Đếm cả file thì một checkbox ghi chú ở §1/§4 chặn đóng wave vĩnh viễn mà không chỗ nào re-arm nó.
    """
    out: list[str] | None = None
    for line in live(text).splitlines():
        if re.match(r"## 3(?!\d)", line):      # đúng §3 — "## 30. Ghi chú" không tính
            out = []
            continue
        if out is not None and line.startswith("## "):
            break
        if out is not None:
            out.append(line)
    return out


def check_backward_compat(state: dict, evidence: dict | None = None,
                          root: Path | None = None) -> tuple[bool, str]:
    """Đóng wave ≥2: §3 sổ tương thích ngược phải rà xong.

    Vì sao cần gate riêng dù đã có dogfood regression: dogfood đi lại LUỒNG (bấm được không), gate
    này soi HÌNH DẠNG (endpoint/cột/khoá cache/event có đổi shape không). Luồng vẫn chạy trơn trong
    khi field response bị đổi tên — client ngoài gãy, dogfood không thấy vì nó dùng đúng client mới.

    Wave 1 bỏ qua: chưa giao gì thì chưa có hợp đồng nào để giữ.
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    n = (state.get("wave") or {}).get("number") or 0
    if n < 2:
        return True, ""
    f = root / BC_LEDGER
    if not f.is_file():
        return False, (
            f"wave {n} (≥2) mà chưa có {BC_LEDGER} — chép từ "
            "tracking/_templates/TEMPLATE.bc-ledger.md rồi điền §1 (surface đã giao) + rà §3. "
            "Từ wave 2 có thứ đã giao cho người dùng thật, và không sổ nào ghi lại thì "
            "'chỉ được THÊM' chỉ là lời dặn không đối chiếu được"
        )
    sec3 = _bc_section3(f.read_text(encoding="utf-8", errors="ignore"))
    if sec3 is None:
        return False, (f"{BC_LEDGER} mất heading '## 3' — chép lại §3 từ template; "
                       "gate đếm và next_wave.py re-arm đúng mục đó")
    todo = [l.strip() for l in sec3 if l.strip().startswith("- [ ]")]
    if not todo:
        return True, ""
    return False, (
        f"còn {len(todo)} mục tương thích ngược chưa rà ({BC_LEDGER} §3):\n      "
        + "\n      ".join(todo[:4]) + ("\n      …" if len(todo) > 4 else "")
        + "\n      Rà từng mục theo luật §2 (đối chiếu sổ hợp đồng §1). Mục không áp dụng → "
          "tick kèm 'n/a'. Chỗ buộc phải phá mà user CHƯA chốt → DỪNG, hỏi user"
    )


# ========================================================================
# challenge_passed (review-dev) — đối kháng nội bộ TRƯỚC khi code
# ========================================================================

CHALLENGE_LOG = "tracking/challenge-log.md"
DECISIONS_LOG = "tracking/decisions.md"
# Stage của lượt LÀM TÀI LIỆU — nơi agent KHÔNG được hỏi user, nên buộc phải để lại vết
# ở sổ quyết định. `decide.py` ghi stage vào cột `Stage · Wave` nên đối chiếu được.
DOC_STAGES = ("DOMAIN_AUTHORING", "DESIGN", "PLAN", "REVIEW")
WAVE_MARK_RE = re.compile(r"quyết định của (wave-\d+) nằm DƯỚI dòng này", re.IGNORECASE)


def _challenge_rows(root: Path, wave_id: str | None, phase: str) -> list[list[str]] | None:
    """Dòng challenge của `phase` ('tài liệu' | 'code'), lọc theo wave. None = chưa có file."""
    f = root / CHALLENGE_LOG
    if not f.is_file():
        return None
    out = []
    for line in read_live(f).splitlines():
        s = line.strip()
        if not s.startswith("|") or "{{" in s or set(s) <= set("|- "):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 7 or cells[0].lower().startswith("ngày"):
            continue
        if cells[2].lower() != phase:
            continue
        if wave_id and cells[1] != wave_id:
            continue
        out.append(cells)
    return out


def check_challenge_doc(state: dict, evidence: dict | None = None,
                        root: Path | None = None) -> tuple[bool, str]:
    """KHOÁ SCOPE: phải có ≥3 challenge `tài liệu` PASS trước khi duyệt.

    VÌ SAO CÓ LƯỢT RIÊNG cho tài liệu, dù đã có `challenge_passed` trước khi code: hai lượt bắt hai
    loại lỗi khác nhau, và lượt tài liệu là lượt ĐẮT NHẤT khi bỏ. Khoá scope xong thì mọi lỗ trong
    tài liệu phải trả bằng code sai — challenge trước-khi-code chỉ bắt được "tôi đọc hiểu lệch",
    không bắt được "tài liệu này chưa hề nói tới chuyện đó".

    Luật chấm: trả lời **CHỈ bằng những gì đã ghi trong tài liệu**. Câu nào phải viện tới kiến thức
    ngoài hay phải đoán = **một lỗ tài liệu** → vá rồi mới chấm PASS. Chấm PASS bằng kiến thức
    ngoài là biến phép thử thành nghi thức.

    ≥3 vì một câu dễ trúng chỗ mình vốn đã nắm; ba câu mới buộc phải đi tìm chỗ mình chưa chắc.
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    wave_id = (state.get("wave") or {}).get("id")
    rows = _challenge_rows(root, wave_id, "tài liệu")
    hint = ("Nguồn câu hỏi tốt: mâu thuẫn giữa hai AC · ca biên HLD chưa chặn được · ô `cấm` trong "
            "ma trận vai × hành động mà thiết kế chưa chặn ở server · trạng thái bắt buộc của "
            "component mà API chưa phân biệt nổi · thứ trong FEAT nhưng NGOÀI scope wave này")
    if rows is None:
        return False, (f"chưa có {CHALLENGE_LOG} — chép từ "
                       f"tracking/_templates/TEMPLATE.challenge-log.md. {hint}")
    if len(rows) < 3:
        return False, (
            f"{CHALLENGE_LOG} mới có {len(rows)}/3 challenge `tài liệu`"
            + (f" của {wave_id}" if wave_id else "")
            + ". Trước khi KHOÁ SCOPE phải tự ra **3 câu khó nhất** và trả lời **chỉ bằng những "
              "gì đã ghi trong tài liệu**.\n      "
            + hint
            + "\n      Câu nào phải đoán hoặc phải viện kiến thức ngoài = MỘT LỖ TÀI LIỆU — vá "
              "rồi mới chấm PASS. Một câu dễ trúng chỗ mình vốn đã nắm; ba câu mới buộc đi tìm "
              "chỗ mình chưa chắc"
        )
    failed = [r for r in rows if "fail" in r[-1].lower()]
    passed = [r for r in rows if "pass" in r[-1].lower()]
    if len(passed) < 3:
        return False, (
            f"{CHALLENGE_LOG}: {len(failed)} challenge `tài liệu` FAIL, mới {len(passed)}/3 PASS. "
            "FAIL nghĩa là tài liệu chưa trả lời được — vá tài liệu, ra câu khác, trả lời lại. "
            "KHÔNG khoá scope trên một bộ tài liệu chưa đứng nổi trước câu hỏi của chính mình"
        )
    return True, ""


HYPO_LOG = "docs/discovery/hypothesis-log.md"
_NUM_RE = re.compile(r"\d")


def check_hypothesis_measurable(state: dict, evidence: dict | None = None,
                                root: Path | None = None) -> tuple[bool, str]:
    """KHOÁ SCOPE: mọi giả thuyết còn `TESTABLE` phải có NGƯỠNG BẰNG SỐ + CÁCH ĐO + WAVE ĐO.

    VÌ SAO — `hypothesis-log` khai vòng đời `TESTABLE → PROVEN | DISPROVEN`, nhưng trong cả repo
    chuỗi `PROVEN` chỉ xuất hiện đúng một lần: ở chính cái template khai ra nó. Không gì đo, nên
    không gì chuyển trạng thái, nên sổ giả thuyết là **danh sách phỏng đoán không ai đối chứng** —
    một tài liệu trông như đang gác mà không gác gì.

    Gate này KHÔNG đòi "đã đo" — harness dừng ở `/next-wave`, chưa có production thì chưa có số.
    Nó đòi đúng ba thứ NẰM TRONG TẦM TAY lúc khoá scope:

      NGƯỠNG BẰNG SỐ   "tăng đáng kể" không bác bỏ được cái gì; giả thuyết nào cũng đúng nếu ngưỡng
                       viết sau khi nhìn số. Có số thì mới sai được, mà sai được mới là giả thuyết.
      CÁCH ĐO          trỏ tới thứ có thật (event ở PRODUCTION-READY nhóm 4 / một truy vấn cụ thể).
                       Không cài chỗ đo thì ngưỡng cũng chỉ là con số trang trí.
      WAVE ĐO          gắn vào một wave, để `/next-wave` còn biết lúc nào phải hỏi lại.
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    f = root / HYPO_LOG
    if not f.is_file():
        return True, ""      # chưa có sổ giả thuyết → không phải phạm vi gate này (discovery gác)
    bad: list[str] = []
    for r in _parse_md_table_rows(read_live(f), ("id", "status")):
        hid = (r.get("id") or "").strip()
        if not hid or "{{" in hid or not hid.upper().startswith("H"):
            continue
        if (r.get("status") or "").strip().upper() != "TESTABLE":
            continue                                  # đã kết luận rồi thì thôi
        miss = []
        thr = (r.get("ngưỡng (số, ghi trước)") or r.get("ngưỡng") or "").strip()
        how = (r.get("cách đo") or "").strip()
        wave = (r.get("wave đo") or "").strip()
        if not thr or "{{" in thr:
            miss.append("thiếu Ngưỡng")
        elif not _NUM_RE.search(thr):
            miss.append(f"Ngưỡng không có SỐ ({thr[:32]!r})")
        if not how or "{{" in how:
            miss.append("thiếu Cách đo")
        if not wave or "{{" in wave:
            miss.append("thiếu Wave đo")
        if miss:
            bad.append(f"{hid}: {' · '.join(miss)}")
    if not bad:
        return True, ""
    return False, (
        f"{HYPO_LOG} — {len(bad)} giả thuyết chưa đo được:\n      "
        + "\n      ".join(bad[:6])
        + ("\n      …" if len(bad) > 6 else "")
        + "\n      Ngưỡng phải là **SỐ** và ghi TRƯỚC khi nhìn dữ liệu: \"tăng đáng kể\" thì giả "
          "thuyết nào cũng đúng, mà đúng-mọi-đằng nghĩa là không bác bỏ được, tức là không phải "
          "giả thuyết.\n      Cách đo phải trỏ tới thứ có thật (event ở PRODUCTION-READY nhóm 4 / "
          "một truy vấn cụ thể) — không cài chỗ đo thì ngưỡng chỉ là số trang trí"
    )


def check_decisions_min(state: dict, evidence: dict | None = None,
                        root: Path | None = None) -> tuple[bool, str]:
    """KHOÁ SCOPE: ≥2 quyết định đã ghi, đếm DƯỚI mốc wave hiện tại.

    VÌ SAO — `decide.py` tồn tại nhưng KHÔNG chỗ nào đòi. Một lượt làm tài liệu trọn vẹn (khám phá →
    nghiệp vụ → thiết kế → chia wave) mà không ghi nổi hai chỗ mơ hồ là chuyện khó tin: nghĩa là
    agent đã ĐOÁN IM LẶNG. Sổ rỗng không chứng minh được là không có mơ hồ, nó chỉ chứng minh
    không ai ghi.

    Đếm DƯỚI MỐC `(wave-N)` — `/next-wave` ghi mốc khi mở wave. Không có mốc thì đếm cả sổ (wave 1
    chưa có mốc nào). Thiếu cơ chế này thì hai quyết định của wave 1 xanh hộ mọi wave về sau.
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    f = root / DECISIONS_LOG
    tip = ("`py scripts/decide.py --what \"...\" --why \"... (FEAT-X-001 §3)\" "
           "--assume \"...\" --reversible yes|hard|no`")
    if not f.is_file():
        return False, (f"chưa có {DECISIONS_LOG} — cả lượt làm tài liệu không ghi nổi một chỗ mơ hồ "
                       f"nào? Ghi bằng {tip}")
    lines = read_live(f).splitlines()
    start = 0
    for i, line in enumerate(lines):
        if WAVE_MARK_RE.search(line):
            start = i + 1                      # chỉ đếm dưới MỐC CUỐI
    rows = [l for l in lines[start:]
            if l.strip().startswith("|") and "{{" not in l
            and not set(l.strip()) <= set("|- ")
            and not l.strip("| ").lower().startswith("ngày")
            and not WAVE_MARK_RE.search(l)]
    if len(rows) >= 2:
        # Đếm ĐỦ SỐ thôi thì chưa đủ: hai quyết định của `/discover` làm gate xanh, còn cả lượt
        # `/domain` (nghiệp vụ → dịch → thiết kế → chia wave) đoán im lặng vẫn qua. Mà `/domain`
        # mới là chỗ **không được hỏi user** — nó buộc phải để lại vết ở đây, nếu không thì cơ chế
        # "thay việc hỏi bằng việc ghi" chỉ tồn tại trên giấy.
        doc_rows = [r for r in rows if any(s in r for s in DOC_STAGES)]
        if doc_rows:
            return True, ""
        return False, (
            f"{DECISIONS_LOG} có {len(rows)} quyết định nhưng **không dòng nào của lượt làm tài "
            "liệu** (cột `Stage · Wave` không có DOMAIN_AUTHORING/DESIGN/PLAN/REVIEW).\n      "
            "`/domain` là chỗ KHÔNG ĐƯỢC hỏi user — mơ hồ thì phải ghi lại. Đi trọn nghiệp vụ → "
            "dịch → thiết kế → chia wave mà không vướng chỗ nào đáng ghi là chuyện khó tin; "
            "nhiều khả năng đã đoán im lặng.\n      "
            f"Ghi bằng {tip}"
        )
    scope = "dưới mốc wave hiện tại" if start else "trong sổ"
    return False, (
        f"{DECISIONS_LOG} mới có {len(rows)}/2 quyết định {scope}. Cả một lượt làm tài liệu mà "
        "không ghi nổi hai chỗ mơ hồ nghĩa là đã ĐOÁN IM LẶNG — sổ rỗng không chứng minh được "
        "là không có mơ hồ, nó chỉ chứng minh không ai ghi.\n      "
        "Tối thiểu nên có: lý do chọn stack (ADR nào, vì sao không phương án kia) + một chỗ spec "
        f"mơ hồ đã tự quyết.\n      Ghi bằng {tip}"
    )


def check_challenge_passed(state: dict, evidence: dict | None = None,
                           root: Path | None = None) -> tuple[bool, str]:
    """Rời DEV: phải có ≥1 challenge PASS của ĐÚNG wave này.

    Đối kháng nội bộ thay reviewer ngoài (VIPER luật #8): trước khi viết dòng code đầu tiên, agent
    tự ra một câu hỏi khó dựa trên spec THẬT rồi tự chấm. review-dev bắt lỗi SAU khi code xong —
    lúc đó cái giá đã trả. Challenge bắt đúng chỗ "tưởng đã hiểu mà chưa".

    Lọc theo wave: dòng PASS của wave trước KHÔNG gánh hộ wave này — cùng cơ chế đếm-theo-wave với
    test_result/review_results. FAIL gần nhất mà không có PASS sau nó → đỏ (FAIL nghĩa là CHƯA được
    code, nên nó không phải là gate đã qua).
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    wave_id = (state.get("wave") or {}).get("id")
    if not wave_id:
        return True, ""
    f = root / CHALLENGE_LOG
    if not f.is_file():
        return False, (
            f"chưa có {CHALLENGE_LOG} — chép từ tracking/_templates/TEMPLATE.challenge-log.md. "
            "Trước khi code, agent phải tự ra MỘT câu hỏi khó dựa trên spec thật (mâu thuẫn giữa "
            "hai AC · ca biên HLD chưa chặn · ô `cấm` trong ma trận quyền · surface wave trước sắp "
            "đụng) rồi tự chấm PASS/FAIL"
        )
    rows = [l for l in read_live(f).splitlines()
            if l.strip().startswith("|") and wave_id in l and "{{" not in l]
    if not rows:
        return False, (
            f"{CHALLENGE_LOG} chưa có dòng challenge nào của {wave_id} "
            "(dòng của wave trước không tính — mỗi wave có spec riêng để chất vấn)"
        )
    if not any(re.search(r"\bPASS\b", r) for r in rows):
        return False, (
            f"{CHALLENGE_LOG}: {wave_id} có {len(rows)} dòng nhưng chưa dòng nào PASS. "
            "FAIL nghĩa là CHƯA được code — đọc lại spec, ra câu khác, trả lời lại"
        )
    return True, ""


# ========================================================================
# dogfood_done (end-wave) — đã soi bằng 6 lăng kính, không chỉ chạy TC đã viết
# ========================================================================

DOGFOOD_LENSES = ("edge", "newbie", "picky", "rushed", "breaker", "mobile")


def check_dogfood_done(state: dict, evidence: dict | None = None,
                       root: Path | None = None) -> tuple[bool, str]:
    """end-wave: wave phải đã qua MỘT lượt dogfood đủ 2 đợt trên hệ đang chạy.

    Vì sao cần gate riêng dù đã có test_passed: nó chỉ nói "test-case ĐÃ VIẾT
    thì pass". Chúng mù với thứ không ai viết TC cho — cảnh rỗng câm, lỗi bị nuốt im lặng, bấm hai
    lần ra hai bản ghi, vai A chạm dữ liệu vai B. Một wave có thể xanh sạch cả ba gate kia mà chưa
    ai từng mở sản phẩm ra dùng thử.

    Bằng chứng đọc từ report của chính lượt dogfood (`tracking/{wave}/dogfood-report.md`) chứ không
    từ evidence agent tự khai: agent khai `dogfood_done: true` thì gate chỉ đo được lời khai.
    Đòi báo cáo nêu ĐỦ 6 lăng kính + đủ 2 đợt — chạy 3 vai rồi bảo xong là dogfood nửa vời, và nửa
    đợt 1 (DB sạch) chính là nửa bắt được lỗi trạng thái rỗng.
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    wave_id = (state.get("wave") or {}).get("id")
    if not wave_id:
        return True, ""      # không có wave → không phải phạm vi gate này
    rel = f"tracking/{wave_id}/dogfood-report.md"
    f = root / rel
    if not f.is_file():
        return False, (
            f"chưa có {rel} — wave chưa qua lượt /dogfood nào. "
            "test_passed chỉ nói 'TC đã viết thì pass', nó mù với thứ không ai "
            "viết TC cho (cảnh rỗng câm, lỗi nuốt im lặng, bấm hai lần ra hai bản ghi, "
            "vai A chạm dữ liệu vai B). Chạy /dogfood rồi end-wave lại"
        )
    text = read_live(f).lower()
    missing = [l for l in DOGFOOD_LENSES if l not in text]
    if missing:
        return False, (
            f"{rel} thiếu lăng kính: {', '.join(missing)} — /dogfood phải chạy đủ 6 vai. "
            "Vai thiếu = một loại lỗi không ai đi tìm"
        )
    if not (("đợt 1" in text or "dot 1" in text) and ("đợt 2" in text or "dot 2" in text)):
        return False, (
            f"{rel} không nêu đủ 2 đợt. Đợt 1 cần DB SẠCH (trạng thái rỗng chết ngay khi có bản "
            "ghi đầu tiên), đợt 2 cần DB CÓ DỮ LIỆU (bảng dài mới tràn) — gộp một đợt là mất "
            "một nửa phép thử"
        )

    # Mỗi phát hiện phải có QUYẾT ĐỊNH XỬ. Đây là thứ thay chỗ cho sổ bug: không cần vòng đời
    # BUG-NNN, nhưng "đã thấy rồi bỏ đó" thì phải phân biệt được với "đã cân nhắc và hoãn".
    # Từ vựng ĐÓNG — ô trống nghĩa là chưa ai quyết, không phải "không đáng".
    rows = _parse_md_table_rows(read_live(f), ("xử",))
    blank, later_no_ref, open_now = [], [], []
    for r in rows:
        rid = (r.get("#") or r.get("id") or "?").strip()
        if "{{" in rid or not rid or rid == "?":
            continue                                   # dòng mẫu của template
        if not any(v.strip() for k, v in r.items() if k not in ("#", "id")):
            continue                                   # dòng rỗng trơn — artefact bảng, không phải phát hiện
        v = (r.get("xử") or "").strip().lower()
        where = (r.get("ở đâu") or "").strip()
        if not v:
            blank.append(rid)
        elif v.startswith("sửa ngay") and not where:
            open_now.append(rid)                       # khai sửa ngay mà không dẫn được vết sửa
        elif v.startswith("wave sau") and not where:
            # KHÔNG đòi dẫn tới WAVE-SEQUENCE.md ở đây: `docs/plans/**` bị phase-lock chặn ở
            # MANUAL_TEST (chỗ /dogfood chạy), nên đòi vậy là ra luật không tuân thủ nổi.
            # Ghi ở đây (không khoá) — NHẬN ở chốt chia-wave của /domain (khoá mở). /next-wave
            # đếm dòng `wave sau` chưa có mặt trong WAVE-SEQUENCE và cảnh báo lúc mở wave.
            later_no_ref.append(rid)
    bad = []
    if blank:
        bad.append(f"{len(blank)} phát hiện chưa có ô `Xử` ({', '.join(blank[:6])}) — "
                   "ô trống = chưa ai quyết, không phải 'không đáng'")
    if open_now:
        bad.append(f"{len(open_now)} dòng khai `sửa ngay` mà cột `Ở đâu` trống "
                   f"({', '.join(open_now[:6])}) — sửa rồi thì dẫn được ra commit/TC")
    if later_no_ref:
        bad.append(f"{len(later_no_ref)} dòng đẩy `wave sau` mà cột `Ở đâu` trống "
                   f"({', '.join(later_no_ref[:6])}) — phải nói **vì sao ngoài scope** và **cần "
                   "gì để làm**, nếu không thì wave sau đọc một dòng cụt, không dựng lại nổi "
                   "bối cảnh. `/next-wave` sẽ đối chiếu các dòng này với WAVE-SEQUENCE.md")
    if bad:
        return False, f"{rel}:\n      " + "\n      ".join(bad)
    return True, ""


# ========================================================================
# ui_test_present + registry_scope (test-plan) — UI phải được test thật + TC không over-scope
# ========================================================================

def check_ui_test_present(state: dict, evidence: dict | None = None, root: Path | None = None) -> tuple[bool, str]:
    """test-plan: MỖI web boundary trong wave phải có ≥1 auto-TC UI in-scope (boundary = web boundary).

    Đóng gap "UI test luôn manual/vắng → giao diện không bao giờ được mở thật → lỗi visual lọt":
    registry toàn API-TC vẫn đạt test_result=pass dù FE chưa từng render. TC UI này chạy bằng
    Playwright ở test-execute (load màn hình chính + assert style token áp dụng + screenshot —
    test_evidence enforce bằng chứng). TC tag @deferred KHÔNG được tính (chống né bằng tag).
    force=true → bypass (audit).
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    wave_id = (state.get("wave") or {}).get("id")
    if not wave_id:
        return False, "chưa có wave"
    webs = [b for b in (state.get("wave_boundaries") or []) if _kind_of(b, root) == "web"]
    if not webs:
        return True, ""  # wave không có web boundary → không áp dụng
    reg = root / "tracking" / wave_id / "test-case-registry.md"
    if not reg.is_file():
        return False, f"thiếu 'tracking/{wave_id}/test-case-registry.md' — test-plan phải sinh trước"
    rows = _registry_auto_rows(reg.read_text(encoding="utf-8", errors="ignore"))
    deferred = _wave_deferred_tokens(wave_id, root)
    missing: list[str] = []
    for w in webs:
        has = any(
            (r.get("boundary") or "").strip().lower() == w.lower() and not _row_is_deferred(r, deferred)
            for r in rows
        )
        if not has:
            missing.append(w)
    if missing:
        return False, (
            "web boundary KHÔNG có auto-TC UI nào (giao diện không bao giờ được mở thật → lỗi visual lọt): "
            + ", ".join(sorted(missing))
            + " — thêm ≥1 TC type=auto group=e2e boundary=<web> (Playwright: load màn hình chính "
            "+ assert style token áp dụng + screenshot)"
        )
    return True, ""


_FEAT_TOKEN_RE = re.compile(r"\bFEAT-[\w-]+\b", re.IGNORECASE)
_WAVE_NUM_RE = re.compile(r"wave-0*(\d+)", re.IGNORECASE)


def _wave_number(wave_id: str) -> int | None:
    m = _WAVE_NUM_RE.search(wave_id or "")
    return int(m.group(1)) if m else None


def _feats_planned_upto(wave_id: str, root: Path) -> set[str]:
    """FEAT token từ MỌI wave plan có số wave ≤ wave hiện tại (registry tích luỹ: FEAT wave trước
    đã ship vẫn hợp lệ để regression-test). FEAT chỉ xuất hiện ở wave TƯƠNG LAI = over-scope."""
    cur = _wave_number(wave_id)
    out: set[str] = set()
    for p in (root / "docs" / "plans").glob("wave-*.md"):
        if p.name.startswith("TEMPLATE"):
            continue
        n = _wave_number(p.stem)
        if n is None or (cur is not None and n > cur):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        out.update(m.group(0).upper() for m in _FEAT_TOKEN_RE.finditer(text))
    return out


def check_registry_scope(state: dict, evidence: dict | None = None, root: Path | None = None) -> tuple[bool, str]:
    """test-plan: auto-TC chỉ được trace FEAT thuộc scope tới wave hiện tại; FEAT deferred phải tag @deferred.

    Đóng gap "registry over-scope": test-plan sinh TC cho feature CHƯA build (wave sau / chưa plan)
    → test-execute chạy vào feature không tồn tại → bug rác chặn end-wave. 2 luật:
    (a) FEAT của TC phải xuất hiện trong wave plan nào đó số ≤ wave hiện tại (không phải tương lai/phantom);
    (b) feature/AC nằm trong `## Deferred to later waves` của wave plan mà row KHÔNG tag @deferred
        → fail (test-execute sẽ coi in-scope và chạy vào feature chưa build).
    Smoke TC không trace FEAT → miễn. force=true → bypass (audit).
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
        return False, f"thiếu 'tracking/{wave_id}/test-case-registry.md' — test-plan phải sinh trước"
    planned = _feats_planned_upto(wave_id, root)
    if not planned:
        return True, ""  # không đọc được scope từ wave plans → không kiểm được (không chặn bừa)
    deferred = _wave_deferred_tokens(wave_id, root)
    problems: list[str] = []
    for r in _registry_auto_rows(reg.read_text(encoding="utf-8", errors="ignore")):
        tc = (r.get("tc") or "").strip().upper()
        feat_cell = (r.get("feature") or "").strip()
        feat_ids = {m.group(0).upper() for m in _FEAT_TOKEN_RE.finditer(feat_cell)}
        if not feat_ids:
            continue  # smoke TC (TC-S*) không trace FEAT → miễn
        for fid in feat_ids:
            if fid not in planned:
                problems.append(
                    f"{tc}: trace {fid} KHÔNG thuộc wave plan nào ≤ {wave_id} (over-scope — feature "
                    f"chưa build) → xoá TC hoặc chuyển sang wave sở hữu feature"
                )
        if _row_matches_deferred(r, deferred) and not _row_is_deferred(r, deferred):
            problems.append(
                f"{tc}: feature/AC nằm trong `## Deferred to later waves` của wave plan nhưng row "
                f"THIẾU tag @deferred → test-execute sẽ chạy vào feature chưa build (bug rác). "
                f"Tag @deferred + note deferred wave-N"
            )
    if problems:
        return False, "registry-scope fail: " + "; ".join(problems)
    return True, ""


# ========================================================================
# Khớp-nối tài liệu (P0): translation_parity + todo_resolved + ac_coverage
# ========================================================================

_ENG_PRODUCT_KINDS = ("epics", "feat", "business-rules", "journeys", "personas")
_ENG_ORPHAN_KINDS = ("epics", "feat", "business-rules")  # lớp product bắt buộc có nguồn business


def _is_scaffold_md(name: str) -> bool:
    """File .md scaffold (KHÔNG phải artifact sản phẩm): TEMPLATE.* / _TEMPLATE* / README.md.

    Dùng CHUNG cho mọi chỗ glob docs/architecture/{kind}/*.md — chống drift kiểu 'quên loại README'
    ở 1 hàm mà hàm khác nhớ (bug translation_parity/todo_resolved: README.md bị coi là eng doc mồ côi)."""
    return name.startswith("TEMPLATE") or name.startswith("_TEMPLATE") or name == "README.md"


def _eng_docs_by_kind(root: Path) -> dict[str, list[tuple[Path, dict]]]:
    """docs/architecture/{kind}/*.md (bỏ TEMPLATE) → {kind: [(path, frontmatter)]}."""
    out: dict[str, list[tuple[Path, dict]]] = {}
    for kind in _ENG_PRODUCT_KINDS:
        d = root / "docs" / "architecture" / kind
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.md")):
            if _is_scaffold_md(p.name):
                continue
            fm = planning_lint.parse_frontmatter(p.read_text(encoding="utf-8", errors="ignore"))
            out.setdefault(kind, []).append((p, fm))
    return out


def check_translation_parity(evidence: dict | None = None, root: Path | None = None) -> tuple[bool, str]:
    """Gate domain-end: business đã KÝ ↔ eng doc phải 1-1 (translate không được bỏ sót im lặng).

    Chiều 1: MỖI business doc APPROVED (docs/domain/) phải có eng doc cùng kind ở docs/architecture/
    khớp qua frontmatter `source` (chứa tên file business) / `domain_source_id` / trùng stem.
    Chiều 2: eng doc lớp product (epics/feat/business-rules) KHÔNG có `source: docs/domain/...` và
    KHÔNG khớp business doc nào = MỒ CÔI (tự author né vòng ký) → fail. force=true → bypass (audit).
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    all_biz = _domain_business_files(root)
    signed = [p for p in all_biz if _frontmatter_signed(p.read_text(encoding="utf-8", errors="ignore"))]
    eng = _eng_docs_by_kind(root)
    if not all_biz and not any(eng.values()):
        return True, ""  # chưa author gì → domain_gate lo
    problems: list[str] = []
    for bp in signed:
        kind = bp.parent.name
        bfm = planning_lint.parse_frontmatter(bp.read_text(encoding="utf-8", errors="ignore"))
        bid = str(bfm.get("id") or bp.stem)
        hit = False
        for ep, efm in eng.get(kind, []):
            src = str(efm.get("source") or "")
            dsid = str(efm.get("domain_source_id") or "")
            if (bp.name in src) or (dsid and dsid in (bid, bp.stem)) or ep.stem == bp.stem:
                hit = True
                break
        if not hit:
            problems.append(
                f"{kind}/{bp.name}: business doc ĐÃ KÝ nhưng KHÔNG có eng doc tương ứng ở "
                f"docs/architecture/{kind}/ (translate bỏ sót — chạy lại domain-translate)"
            )
    biz_stems = {p.stem for p in all_biz}
    for kind in _ENG_ORPHAN_KINDS:
        for ep, efm in eng.get(kind, []):
            src = str(efm.get("source") or "")
            if "docs/domain" in src:
                continue
            if ep.stem in biz_stems or any(ep.stem.startswith(s) or s.startswith(ep.stem) for s in biz_stems):
                continue
            problems.append(
                f"{kind}/{ep.name}: eng doc MỒ CÔI — không có `source: docs/domain/...` và không khớp "
                f"business doc nào (product phải author ở docs/domain/ + ký + translate, không author thẳng eng)"
            )
    if problems:
        return False, "translation-parity fail: " + "; ".join(problems)
    return True, ""


# Nợ kỹ thuật translator cố ý để lại cho DESIGN — design-end phải trả hết.
_TODO_ENGINEER_RES = [
    re.compile(r"TODO[ -]engineer", re.IGNORECASE),
    re.compile(r"TBD \(DESIGN\)", re.IGNORECASE),
    re.compile(r"^\s*(enforcement_location|scope|consumes_contracts)\s*:.*\bTBD\b", re.IGNORECASE | re.MULTILINE),
]


def check_todo_resolved(evidence: dict | None = None, root: Path | None = None) -> tuple[bool, str]:
    """Gate design-end: field kỹ thuật translator để TODO/TBD phải được DESIGN điền hết.

    `enforcement_location: TBD (DESIGN)` sống sót qua design-end = BR không có nơi enforce
    → rule không bao giờ được implement, chỉ lộ ở UAT. Quét docs/architecture/{epics,feat,
    business-rules}. Chưa chốt thật sự → chuyển thành `Open question` có chủ (không phải TBD).
    force=true → bypass (audit).
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    problems: list[str] = []
    for kind in _ENG_ORPHAN_KINDS:
        d = root / "docs" / "architecture" / kind
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.md")):
            if _is_scaffold_md(p.name):
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            hits = sum(len(rx.findall(text)) for rx in _TODO_ENGINEER_RES)
            if hits:
                problems.append(f"{kind}/{p.name}: {hits} marker TODO-engineer/TBD(DESIGN) chưa điền")
    if problems:
        return False, (
            "todo-resolved fail: " + "; ".join(problems)
            + " — DESIGN phải điền enforcement_location/consumes_contracts/scope (hoặc ghi Open question có chủ)"
        )
    return True, ""


_AC_HEADING_RE = re.compile(r"^###\s*(AC-\d+)\b", re.MULTILINE | re.IGNORECASE)
_AC_TOKEN_RE = re.compile(r"\bAC-\d+\b", re.IGNORECASE)


def _feat_file_for(fid: str, root: Path) -> Path | None:
    d = root / "docs" / "architecture" / "feat"
    exact = d / f"{fid}.md"
    if exact.is_file():
        return exact
    if d.is_dir():
        for p in sorted(d.glob(f"{fid}-*.md")):
            return p
    return None


def check_ac_coverage(state: dict, evidence: dict | None = None, root: Path | None = None) -> tuple[bool, str]:
    """test-plan: traceability FEAT.AC ↔ TC 2 CHIỀU (trước đây chỉ là lời hứa trong skill).

    Chiều 1 (AC mồ côi): mỗi `### AC-n` của FEAT in-scope wave (STATE.wave_features / MATRIX)
    phải có ≥1 TC (auto hoặc manual) trace nó — trừ token đã khai deferred ở wave plan.
    Chiều 2 (TC stale): TC trace `FEAT:AC-m` mà FEAT file không còn AC đó → stale (bắt case
    lùi `/domain` đổi AC mà quên remap TC). FEAT chưa có file → bỏ qua (plan_integrity lo).
    force=true → bypass (audit).
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
        return False, f"thiếu 'tracking/{wave_id}/test-case-registry.md' — test-plan phải sinh trước"
    feats = list(state.get("wave_features") or [])
    if not feats:
        for b in (state.get("wave_boundaries") or []):
            feats += list((_matrix_boundary(b, root) or {}).get("features") or [])
    deferred = _wave_deferred_tokens(wave_id, root)
    rows = _parse_md_table_rows(reg.read_text(encoding="utf-8", errors="ignore"), ("tc", "feature", "ac"))
    covered: set[tuple[str, str]] = set()
    for r in rows:
        fids = {m.group(0).upper() for m in _FEAT_TOKEN_RE.finditer(r.get("feature") or "")}
        acs = {m.group(0).upper() for m in _AC_TOKEN_RE.finditer(r.get("ac") or "")}
        for f in fids:
            for a in acs:
                covered.add((f, a))
    problems: list[str] = []
    file_acs_cache: dict[str, set[str] | None] = {}

    def _file_acs(fid: str) -> set[str] | None:
        if fid not in file_acs_cache:
            fp = _feat_file_for(fid, root)
            file_acs_cache[fid] = (
                {a.upper() for a in _AC_HEADING_RE.findall(read_live(fp))}
                if fp else None
            )
        return file_acs_cache[fid]

    for fid in feats:
        fidU = str(fid).upper()
        acs = _file_acs(fidU)
        if acs is None:
            continue  # FEAT chưa có file — plan_integrity lo (không double-fail)
        if not acs:
            # File TỒN TẠI nhưng 0 heading `### AC-n`: feature in-scope không thể trace coverage →
            # lọt verify (planning_lint chỉ ép epic_ref/feat_type, KHÔNG ép có AC). KHÔNG bỏ qua im lặng.
            if fidU not in deferred:
                problems.append(
                    f"{fidU}: FEAT có file nhưng KHÔNG có AC `### AC-n` nào — feature không verify được "
                    f"(viết AC theo TEMPLATE.feat, hoặc khai deferred ở wave plan)"
                )
            continue
        for ac in sorted(acs):
            if fidU in deferred or f"{fidU}:{ac}" in deferred or ac in deferred:
                continue
            if (fidU, ac) not in covered:
                problems.append(f"{fidU}:{ac} KHÔNG có TC nào trace (AC mồ côi — coverage matrix hụt)")
    for r in rows:
        tc = (r.get("tc") or "").strip().upper()
        if not re.fullmatch(r"tc-[\w-]+", tc, re.IGNORECASE):
            continue
        acs_ref = {m.group(0).upper() for m in _AC_TOKEN_RE.finditer(r.get("ac") or "")}
        for fid in {m.group(0).upper() for m in _FEAT_TOKEN_RE.finditer(r.get("feature") or "")}:
            facs = _file_acs(fid)
            if not facs:
                continue
            for ac in acs_ref:
                if ac not in facs:
                    problems.append(f"{tc}: trace {fid}:{ac} nhưng FEAT không có AC đó (TC stale — remap sau khi AC đổi)")
    if problems:
        return False, "ac-coverage fail: " + "; ".join(sorted(set(problems)))
    return True, ""


# ========================================================================
# Contract graph (K1) + contract runtime proof (K2) — khớp nối contract
# ========================================================================

def _md_col_values(text: str, col_contains: str) -> list[str]:
    """Giá trị cột (backtick-id hoặc raw token đầu) của MỌI bảng có header chứa `col_contains`."""
    out: list[str] = []
    header_idx: int | None = None
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            header_idx = None
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells if c):
            continue
        low = [c.lower() for c in cells]
        if header_idx is None:
            for i, c in enumerate(low):
                if col_contains in c:
                    header_idx = i
                    break
            continue
        if header_idx < len(cells):
            cell = cells[header_idx]
            m = re.search(r"`([a-z0-9][a-z0-9-]*)`", cell)
            val = m.group(1) if m else cell.split()[0] if cell.split() else ""
            if val and "{{" not in val:
                out.append(val.strip("`"))
    return out


def _contract_edges(root: Path) -> list[tuple[str, str, str]]:
    """Đồ thị contract từ docs: [(consumer, producer, source-doc)]. Bỏ placeholder {{...}}."""
    arch = root / "docs" / "architecture"
    edges: list[tuple[str, str, str]] = []

    def _clean(v: object) -> str:
        v = str(v or "").strip()
        return "" if "{{" in v else v

    api_dir = arch / "api"
    if api_dir.is_dir():
        for p in sorted(api_dir.glob("api-*.md")):
            if p.name.startswith("TEMPLATE"):
                continue
            fm = planning_lint.parse_frontmatter(p.read_text(encoding="utf-8", errors="ignore"))
            producer = _clean(fm.get("producer")) or p.stem[len("api-"):]
            for c in (fm.get("consumers") or []) if isinstance(fm.get("consumers"), list) else []:
                c = _clean(c)
                if c:
                    edges.append((c, producer, p.name))
    integ_dir = arch / "integrations"
    if integ_dir.is_dir():
        for p in sorted(integ_dir.glob("INTEG-INT-*.md")):
            if p.name.startswith("TEMPLATE"):
                continue
            fm = planning_lint.parse_frontmatter(p.read_text(encoding="utf-8", errors="ignore"))
            c, pr = _clean(fm.get("consumer")), _clean(fm.get("producer"))
            if c and pr:
                edges.append((c, pr, p.name))
    ev_dir = arch / "events"
    if ev_dir.is_dir():
        for p in sorted(ev_dir.glob("*-events.md")):
            if p.name.startswith("TEMPLATE"):
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            fm = planning_lint.parse_frontmatter(text)
            producer = _clean(fm.get("boundary")) or p.stem[: -len("-events")]
            for sub in _md_col_values(text, "subscriber"):
                edges.append((sub, producer, p.name))
            # §9 events nhận: boundary này subscribe topic của producer khác
            for up in _md_col_values(text, "producer (boundary_id)"):
                if up != producer:
                    edges.append((producer, up, p.name))
    return edges


def check_contract_graph_parity(evidence: dict | None = None, root: Path | None = None) -> tuple[bool, str]:
    """Gate plan: đồ thị contract (api consumers[] + INTEG-INT + events subscribers) ↔ MATRIX depends_on.

    3 nguồn khai cùng 1 sự thật mà không ai đối chiếu: (a) id trong contract phải là boundary MATRIX;
    (b) cạnh contract (consumer→producer) phải có trong MATRIX (`depends_on`/`consumed_by`);
    (c) cạnh MATRIX depends_on phải được document bởi ≥1 contract doc (api consumers[]/INTEG/event)
    — cạnh không doc = FE/BE gọi nhau ngoài contract. force=true → bypass (audit).
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    boundaries = _matrix_boundaries(root)
    if not boundaries:
        return True, ""  # MATRIX chưa có → plan_gate lo
    mf = root / "harness" / "SERVICE-BOUNDARY-MATRIX.json"
    try:
        data = json.loads(mf.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return True, ""
    blist = data.get("boundaries", []) if isinstance(data, dict) else data
    dep: dict[str, set[str]] = {}
    consumed_by: dict[str, set[str]] = {}
    for b in blist:
        bid = b.get("boundary_id")
        if not bid:
            continue
        dep[bid] = {d for d in (b.get("depends_on") or []) if isinstance(d, str)}
        consumed_by[bid] = {c for c in (b.get("consumed_by") or []) if isinstance(c, str)}
    ids = set(dep)
    edges = _contract_edges(root)
    problems: list[str] = []
    doc_edges: set[tuple[str, str]] = set()
    for c, p, src in edges:
        if c not in ids or p not in ids:
            bad = [x for x in (c, p) if x not in ids]
            problems.append(f"{src}: boundary {bad} không tồn tại trong MATRIX")
            continue
        doc_edges.add((c, p))
        if p not in dep.get(c, ()) and c not in consumed_by.get(p, ()):
            problems.append(
                f"{src}: khai {c} consume {p} nhưng MATRIX không có cạnh này "
                f"(thêm depends_on/consumed_by hoặc sửa contract doc)"
            )
    for c in ids:
        for p in dep.get(c, ()):
            if p in ids and (c, p) not in doc_edges:
                problems.append(
                    f"MATRIX: {c} depends_on {p} nhưng KHÔNG contract doc nào ghi nhận "
                    f"(api-{p}.md consumers[] / INTEG-INT-*.md / events subscriber) — cạnh gọi nhau ngoài contract"
                )
    if problems:
        return False, "contract-graph fail: " + "; ".join(sorted(set(problems)))
    return True, ""


_API_ENDPOINT_RE = re.compile(r"`(GET|POST|PUT|PATCH|DELETE)\s+(/[^\s`?]+)")
# CHỈ ăn dòng KHAI BÁO bảng `| Method · Path | `VERB /path` |` (convention TEMPLATE.api.md).
# KHÔNG quét văn xuôi: câu tường thuật viết tắt (vd 'Happy: `POST /refunds`' thiếu /api/v1) không
# phải endpoint khai báo → tránh false-positive contract-drift với runtime OpenAPI.
_API_DECL_ROW_RE = re.compile(r"^\s*\|\s*Method\W+Path\s*\|", re.IGNORECASE)


def _normalize_api_path(path: str) -> str:
    p = re.sub(r"\{[^}]*\}", "{}", path.strip())
    p = re.sub(r"/:[\w-]+", "/{}", p)
    return (p.rstrip("/") or "/")


def _doc_endpoints(api_file: Path) -> set[tuple[str, str]]:
    """Endpoint khai trong api-*.md — CHỈ dòng bảng `| Method · Path | `VERB /path` |`
    (bỏ qua văn xuôi viết tắt) → {(METHOD, path-normalized)}."""
    out: set[tuple[str, str]] = set()
    for line in api_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not _API_DECL_ROW_RE.match(line):
            continue
        for m in _API_ENDPOINT_RE.finditer(line):
            out.add((m.group(1).upper(), _normalize_api_path(m.group(2))))
    return out


def check_api_contract_proof(state: dict, evidence: dict | None = None, root: Path | None = None) -> tuple[bool, str]:
    """Gate dev-handoff: endpoint khai trong api-{boundary}.md phải TỒN TẠI trong runtime OpenAPI.

    Bắt contract↔implementation drift (endpoint thiếu/rename) TRƯỚC khi test — đọc
    tracking/{wave}/api-proof.json do capture_infra_proof.py fetch `/v3/api-docs` (HARNESS đo,
    không agent tự khai). Boundary không có api doc / api doc không có endpoint REST parse được
    (GraphQL) → bỏ qua. Shape field sâu → contract TC (test-execute). force=true → bypass (audit).
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    wave_id = (state.get("wave") or {}).get("id")
    if not wave_id:
        return False, "chưa có wave"
    targets: list[tuple[str, set[tuple[str, str]]]] = []
    for b in (state.get("wave_boundaries") or []):
        if _kind_of(b, root) != "backend":
            continue
        doc = root / "docs" / "architecture" / "api" / f"api-{b}.md"
        if not doc.is_file():
            continue
        eps = _doc_endpoints(doc)
        if eps:
            targets.append((b, eps))
    if not targets:
        return True, ""
    proof = root / "tracking" / wave_id / "api-proof.json"
    if not proof.is_file():
        return False, (
            f"thiếu 'tracking/{wave_id}/api-proof.json' — chạy `py scripts/capture_infra_proof.py` "
            "(đã capture OpenAPI runtime cùng health-proof)"
        )
    try:
        specs = (json.loads(proof.read_text(encoding="utf-8").lstrip("﻿")) or {}).get("specs") or {}
    except (ValueError, OSError):
        return False, f"'tracking/{wave_id}/api-proof.json' parse lỗi — capture lại"
    problems: list[str] = []
    for b, eps in targets:
        spec = specs.get(b)
        if not isinstance(spec, dict) or not isinstance(spec.get("paths"), dict):
            problems.append(
                f"{b}: runtime OpenAPI không fetch được ({(spec or {}).get('error', 'không có entry')}) "
                f"— bật springdoc `/v3/api-docs` (ref-backend-config) rồi capture lại"
            )
            continue
        runtime = {
            (m.upper(), _normalize_api_path(pth))
            for pth, methods in spec["paths"].items()
            for m in (methods or [])
        }
        missing = sorted(f"{m} {p}" for (m, p) in eps if (m, p) not in runtime)
        if missing:
            problems.append(
                f"{b}: endpoint khai trong api-{b}.md KHÔNG có trong runtime OpenAPI (contract drift): "
                + ", ".join(missing)
            )
    if problems:
        return False, "api-contract-proof fail: " + "; ".join(problems)
    return True, ""


# ========================================================================
# G11 — code-compliance backend (đối xứng web_styling: cấm H2, bắt Dockerfile + config)
# ========================================================================

_H2_BUILD_MARKERS = ("com.h2database", "h2database")
_DDL_CREATE_DROP_RE = re.compile(r"ddl-auto\s*[:=]\s*create-drop", re.IGNORECASE)
_JDBC_H2_RE = re.compile(r"jdbc:h2:", re.IGNORECASE)
_APP_CONFIG_NAMES = ("application.yml", "application.yaml", "application.properties")
_ARCHUNIT_MARKER = "com.tngtech.archunit"  # W5: import ArchUnit = có test enforce layer rule bằng máy


def check_code_compliance(state: dict, evidence: dict | None = None, root: Path | None = None) -> tuple[bool, str]:
    """Backend boundary phải runnable + KHÔNG dùng H2 che lỗi prod (đối xứng web_styling).

    Bắt đúng chuỗi defect e2e mà 'test xanh nhờ H2' che (flyway-postgres thiếu, TIMESTAMP vs TIMESTAMPTZ,
    app chạy in-mem khác prod): mỗi backend boundary đã scaffold phải (a) có `Dockerfile` (dev-done ≠
    runnable nếu thiếu); (b) KHÔNG khai H2 trong build (`com.h2database`); (c) config main KHÔNG
    `jdbc:h2:` và KHÔNG `ddl-auto: create-drop`; (d) có ≥1 `application.{yml,yaml,properties}`;
    (e) có ≥1 ArchUnit test (`src/test/**/*.java` import `com.tngtech.archunit`) — layer/package rule
    enforce bằng test DETERMINISTIC thay vì review-agent đọc (W5/L10; PASS do gradle/Stop hook chạy).
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
        # (c)(d) config main + profile (ref-backend-config: base + per-env profile file)
        cfg_dir = svc / "src" / "main" / "resources"
        base_cfgs = [cfg_dir / n for n in _APP_CONFIG_NAMES if (cfg_dir / n).is_file()]
        profile_cfgs = []
        if cfg_dir.is_dir():
            profile_cfgs = [p for p in cfg_dir.glob("application-*.*")
                            if p.suffix.lower() in (".yml", ".yaml", ".properties")]
        if not base_cfgs:
            problems.append(f"{bid}: thiếu application.yml/properties base trong src/main/resources")
        # ref-backend-config: mỗi env 1 file (KHÔNG để all trong base + env var). Tối thiểu ≥1 profile file.
        if base_cfgs and not profile_cfgs:
            problems.append(
                f"{bid}: thiếu file PROFILE `application-<dev|sit|prod>.{{yml,properties}}` "
                f"(ref-backend-config: mỗi env 1 file riêng, không chỉ base + env var)"
            )
        cfgs = base_cfgs + profile_cfgs
        for cfg in cfgs:
            ctxt = cfg.read_text(encoding="utf-8", errors="ignore")
            if _JDBC_H2_RE.search(ctxt):
                problems.append(f"{bid}: {cfg.name} có `jdbc:h2:` — app chạy in-memory khác prod (dùng Postgres)")
            if _DDL_CREATE_DROP_RE.search(ctxt):
                problems.append(f"{bid}: {cfg.name} có `ddl-auto: create-drop` — schema tự sinh che migration drift (dùng Flyway/Liquibase)")
        # (e) ArchUnit — layer rule enforce bằng TEST CHẠY ĐƯỢC, không nhờ review-agent đọc (W5, L10).
        # Chỉ cần TỒN TẠI: việc PASS đã do gradle/Stop hook chạy (ArchUnit là JUnit test). Deterministic > LLM recall.
        test_dir = svc / "src" / "test"
        has_archunit = False
        if test_dir.is_dir():
            for jf in test_dir.rglob("*.java"):
                if _ARCHUNIT_MARKER in jf.read_text(encoding="utf-8", errors="ignore"):
                    has_archunit = True
                    break
        if not has_archunit:
            problems.append(
                f"{bid}: thiếu ArchUnit test (src/test/**/*.java import `{_ARCHUNIT_MARKER}`) — "
                f"layer/package rule phải enforce bằng test deterministic, không chỉ review đọc (ref-backend-pattern §7.5)"
            )
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
        return False, f"thiếu 'tracking/{wave_id}/test-case-registry.md' — test-plan phải sinh trước"
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
# Journey e2e — chuỗi depends_on ≥3 boundary phải có TC SPAN cả chuỗi (API-driven OK, KHÔNG đợi FE)
# ========================================================================

_JOURNEY_TC_GROUPS = ("e2e", "integration")


def _wave_depends_chains(wave_b: set, root: Path) -> list[list[str]]:
    """Liệt kê path root→leaf trong đồ thị depends_on (consumer→provider) nội bộ wave, chỉ giữ ≥3 boundary.

    depends_on acyclic (plan_integrity ép no-cycle); dfs có seen-guard phòng hờ. Path maximal (append ở leaf).
    """
    graph: dict[str, list[str]] = {}
    incoming: set[str] = set()
    for bid in wave_b:
        b = _matrix_boundary(bid, root) or {}
        deps = [d for d in (b.get("depends_on") or []) if d in wave_b]
        graph[bid] = deps
        incoming.update(deps)
    sources = [b for b in wave_b if b not in incoming]  # top consumer (không ai depends_on)
    chains: list[list[str]] = []

    def dfs(node: str, path: list[str], seen: set[str]) -> None:
        deps = [d for d in graph.get(node, []) if d not in seen]
        if not deps:
            if len(path) >= 3:
                chains.append(list(path))
            return
        for d in deps:
            dfs(d, path + [d], seen | {d})

    for s in sorted(sources):
        dfs(s, [s], {s})
    return chains


def check_journey_e2e_present(state: dict, evidence: dict | None = None, root: Path | None = None) -> tuple[bool, str]:
    """Chuỗi depends_on ≥3 boundary (journey đa-hop) phải có ≥1 auto-TC e2e|integration SPAN CẢ CHUỖI.

    `contract_test_present` chỉ ép PAIRWISE (A→B, B→C); bug seam khi A→B→C chạy LIỀN (data transform
    tích lũy / state chỉ vỡ khi cả chuỗi chạy) lọt pairwise (L10). Journey e2e KHÔNG cần FE — curl drive
    A→B→C là đủ (group e2e|integration). Chuỗi ≤2 boundary → vacuous (pairwise = full chain). force=bypass.
    """
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    root = root or REPO_ROOT
    wave_id = (state.get("wave") or {}).get("id")
    if not wave_id:
        return False, "chưa có wave"
    wave_b = set(state.get("wave_boundaries") or [])
    chains = _wave_depends_chains(wave_b, root)
    if not chains:
        return True, ""  # không có chuỗi ≥3 hop → không cần journey e2e
    reg = root / "tracking" / wave_id / "test-case-registry.md"
    if not reg.is_file():
        return False, f"thiếu 'tracking/{wave_id}/test-case-registry.md' — test-plan phải sinh trước"
    rows = _parse_md_table_rows(reg.read_text(encoding="utf-8", errors="ignore"), ("tc", "group", "type"))
    uncovered: list[str] = []
    for chain in chains:
        nodes = [c.lower() for c in chain]
        covered = False
        for r in rows:
            if (r.get("type") or "").strip().lower() != "auto":
                continue
            if (r.get("group") or "").strip().lower() not in _JOURNEY_TC_GROUPS:
                continue
            blob = f"{r.get('boundary','')} {r.get('tags','')}".lower()
            if all(n in blob for n in nodes):
                covered = True
                break
        if not covered:
            uncovered.append(" → ".join(chain))
    if uncovered:
        return False, (
            "journey e2e thiếu cho chuỗi đa-hop (pairwise không phủ luồng chạy liền): "
            + "; ".join(uncovered)
            + " — test-plan thêm ≥1 auto-TC group=e2e|integration SPAN cả chuỗi (curl API-driven, KHÔNG cần FE; "
            "boundary/tags tham chiếu ĐỦ mọi boundary trong chuỗi)"
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


def check_wave_sequence_lint(evidence: dict | None = None) -> tuple[bool, str]:
    """Gate plan: validate WAVE-SEQUENCE.md §wave-NNN (G16, port ZIP wave-sequence-validate).

    Enum class/strategy + target_count ≤ 3/layer + strategy layer-purity (horizontal-be/-fe) +
    vertical parent_epic + inherited_active file tồn tại (single-repo). Field từng là "trang trí" giờ
    được gate. force=true → bypass (audit). Warning không chặn (chỉ error)."""
    evidence = evidence or {}
    if evidence.get("force") is True:
        return True, ""
    ok, errors = wave_sequence_lint.run_lint()
    if ok:
        return True, ""
    return False, "wave-sequence-lint fail: " + "; ".join(errors)


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
#         file_exists, wave_in_matrix, no_open_findings, infra_proof, test_passed,
#         discovery_wave, domain_gate, design_gate, plan_gate, matrix_coherence,
#         ui_test_present, registry_scope, test_evidence, web_styling, ...}.
# (coverage per-kind nay gộp trong all_boundaries_reviewed — check_coverage* giữ làm helper unit-tested.)

GATE_RULES: dict[str, list[dict]] = {
    "discovery-start": [
        {"kind": "non_empty", "field": "wave"},
        {"kind": "discovery_advance"},  # nhảy tiến D{N}→D{N+1} → gate wave hiện tại (refine/first-entry: bỏ qua)
    ],
    "discovery-end": [
        # Discovery là lớp thượng nguồn nhất — ký TẠI ĐÂY, không đợi /approve-document ở REVIEW
        # (lúc đó domain+design+plan đã xây lên trên rồi, tìm ra lỗ là phải tháo ngược ba tầng).
        {"kind": "discovery_stamped"},
        {"kind": "discovery_wave"},  # chốt D3 → DOMAIN: gate D3 (chỉ còn 1 transition từ DISC_D3)
    ],
    "domain-po": [
        {"kind": "non_empty", "field": "mode"},   # EPIC|FEATURE|JOURNEY — viết business doc ở docs/domain/
    ],
    "domain-ba": [
        {"kind": "non_empty", "field": "mode"},   # BR|PERSONA — viết business doc ở docs/domain/
    ],
    "domain-approve": [
        {"kind": "domain_no_jargon"},   # ký doc business: phải plain nghiệp vụ (no jargon). Target rỗng = all
        {"kind": "domain_stamped"},     # stamp `status: APPROVED` PHẢI đã xảy ra trên disk (chạy domain_approve.py) — chặn complete chay
    ],
    "domain-translate": [
        {"kind": "domain_signed"},      # mọi business doc đã ký → dịch sang docs/architecture/ eng
    ],
    "domain-end": [
        {"kind": "domain_gate"},     # ENG epic+feat+BR ở docs/architecture/ (đầu ra translate) (force bypass + audit)
        {"kind": "planning_lint"},   # epic feature_refs≥2 / feat epic_ref+feat_type / BR related_features≥1 (force bypass)
        {"kind": "translation_parity"},  # business đã KÝ ↔ eng doc 1-1 (translate không bỏ sót; eng không mồ côi) (force bypass)
    ],
    "design": [],   # self-loop re-spawn solution-architect (refine) — KHÔNG gate, KHÔNG advance
    "design-ux": [],  # self-loop spawn ux-designer (UX/UI cho FE boundary) — KHÔNG gate, KHÔNG advance
    "design-end": [
        # Ca biên là thứ AC hạnh phúc không nói tới mà hệ nào cũng gặp — chưa quyết ở HLD thì
        # lúc code agent phải đoán, và mỗi boundary đoán một kiểu.
        {"kind": "edge_cases_decided"},
        # Có UI: phải có design system ĐỦ + ĐÓNG trước khi ép ai tuân thủ nó.
        {"kind": "design_system_closed"},
        {"kind": "design_gate"},   # ADR≥3 + INTEG + per-boundary completeness (force bypass + audit). Advance DESIGN→PLAN
        {"kind": "todo_resolved"},  # TODO-engineer/TBD(DESIGN) translator để lại phải điền hết (BR có nơi enforce) (force bypass)
    ],
    "plan": [
        {"kind": "plan_gate"},       # WAVE-SEQUENCE + MATRIX + wave files + KG (force bypass + audit)
        {"kind": "planning_lint"},   # re-check + ADR ≥2 alternatives (ADR có sau DESIGN) (force bypass)
        {"kind": "plan_integrity"},  # MATRIX FEAT-id backing + FEAT mồ côi + depends_on no-cycle/no-dangling (force bypass)
        {"kind": "matrix_coherence"},  # MATRIX phủ mọi boundary BOUNDARY-MAP đúng kind (force bypass)
        {"kind": "api_transport"},   # tenant-id qua header/JWT, KHÔNG query (G6 — chống drift BUG-012) (force bypass)
        {"kind": "wave_sequence_lint"},  # WAVE-SEQUENCE §wave-NNN: enum/cap≤3/strategy-invariant (G16) (force bypass)
        {"kind": "contract_graph_parity"},  # đồ thị contract (api consumers/INTEG/events) ↔ MATRIX depends_on (force bypass)
    ],
    "review-document": [
        {"kind": "flag", "field": "feedback_processed", "expected": True},
    ],
    "approve-document": [
        # Đây là KHOÁ SCOPE. Hai gate dưới là thứ chặn "khoá một bộ tài liệu chưa ai chất vấn":
        # challenge_doc bắt lỗ TRONG tài liệu (khác challenge_passed — cái đó bắt lỗi đọc hiểu,
        # muộn hơn và rẻ hơn); decisions_min bắt ĐOÁN IM LẶNG suốt lượt làm tài liệu.
        {"kind": "hypothesis_measurable"},
        {"kind": "challenge_doc"},
        {"kind": "decisions_min"},
        # Giao diện phải được NGƯỜI xem: cả tầng design-tokens + web_styling + vai picky đang
        # bảo vệ một bản thiết kế mà chưa ai duyệt. Backend-only → vacuous pass.
        {"kind": "mockup_signed"},
        {"kind": "doc_review"},  # doc-review sanity-check đã chạy + no open BLOCKER/MAJOR gap (force bypass + audit)
        {"kind": "doc_stamped"},  # design/contract doc phải ĐÃ stamp APPROVED/ACTIVE (approve_document.py) — chặn approve chay
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
        # Đối kháng nội bộ TRƯỚC khi code (VIPER luật #8): review-dev bắt lỗi SAU khi code xong,
        # lúc đó cái giá đã trả. Challenge bắt chỗ "tưởng đã hiểu mà chưa".
        {"kind": "challenge_passed"},
        {"kind": "non_empty", "field": "review_results"},  # ép kèm review_results — chống `complete {}` làm STATE rỗng rồi kẹt dev-handoff (#10)
        {"kind": "no_open_findings"},  # complete bị chặn tới khi findings BLOCKER/MAJOR fix sạch
    ],
    "dev-handoff": [
        {"kind": "all_boundaries_reviewed"},
        {"kind": "infra_proof"},   # wave services PHẢI lên thật (docker-ps.json content-validated) — chặn handoff khi service chưa chạy
        {"kind": "health_proof"},  # app PHẢI trả 2xx ở /health/ready (health-proof.json HARNESS capture) — State=running chưa đủ
        {"kind": "code_compliance"},  # backend boundary: cấm H2 + bắt Dockerfile/config (G11) — chặn 'test xanh nhờ H2'
        {"kind": "web_styling"},   # web boundary PHẢI có styling thật (CSS/tailwind/CSS-in-JS) — chặn FE unstyled (0 CSS) không theo ux §4
        {"kind": "api_contract_proof"},  # endpoint khai api-{b}.md phải có trong runtime OpenAPI (api-proof.json) — chặn contract drift
    ],
    "test-plan": [
        {"kind": "flag", "field": "docker_compose_ok", "expected": True},
        {"kind": "flag", "field": "connectivity_ok", "expected": True},
        {"kind": "infra_proof"},
        {"kind": "health_proof"},  # stack còn UP + app reachable (kế thừa từ dev-handoff)
        {"kind": "contract_test_present"},  # consumer cross-boundary phải có TC contract/integration (G4/G6)
        {"kind": "journey_e2e_present"},  # chuỗi depends_on ≥3 boundary phải có TC span cả chuỗi (L10, API-driven, không đợi FE)
        # Registry là file MỚI mỗi wave (tracking/{wave}/) — không tự mang TC cũ sang. Không
        # có TC wave trước thì không gì chạy lại chúng, regression chỉ còn trông vào dogfood.
        {"kind": "regression_tc_present"},
        {"kind": "ui_test_present"},  # mỗi web boundary phải có ≥1 auto-TC UI (chống UI không bao giờ được test thật)
        {"kind": "registry_scope"},   # TC chỉ trace FEAT thuộc scope ≤ wave hiện tại; deferred phải tag (chống over-scope → bug rác)
        {"kind": "ac_coverage"},      # FEAT.AC ↔ TC 2 chiều: AC in-scope phải có TC; TC trace AC không tồn tại = stale
    ],
    "test-execute": [
        {"kind": "int_min", "field": "test_cases_count", "min": 1},
        {"kind": "test_evidence"},  # auto-TC phải có bằng chứng đã chạy thật (report+log+network-call); deferred bỏ qua
    ],
    "dogfood": [
        # Hệ phải ĐANG CHẠY THẬT. Dogfood trên hệ chết còn tệ hơn không dogfood: nó không tìm ra
        # gì, nhưng để lại vết "đã kiểm" mà end-wave sẽ tin.
        {"kind": "health_proof"},
        {"kind": "int_min", "field": "batches_done", "min": 2},  # đủ 2 đợt (DB sạch + DB có dữ liệu)
    ],
    "end-wave": [
        {"kind": "flag", "field": "uat_signed", "expected": True},
        {"kind": "test_passed"},  # lần test-execute cuối phải pass (STATE) → ép re-run sau fix
        {"kind": "features_complete"},  # WIP=1 ship-gate (L07): KHÔNG feat nào `active` (làm dở) — VCR-ở-điểm-ship
        {"kind": "dogfood_done"},  # đã soi bằng 6 lăng kính persona, không chỉ chạy TC đã viết
        {"kind": "backward_compat"},
        {"kind": "production_ready"},  # wave ≥2: hình dạng surface đã giao không bị đổi (dogfood soi LUỒNG, cái này soi SHAPE)
    ],
    "next-wave": [
        # KHÔNG gate lại: end-wave chạy ngay trước đã gác đủ (uat_signed · test_passed ·
        # features_complete · dogfood_done). Gate hai lần cùng một điều kiện chỉ
        # tạo chỗ để hai bản sao lệch nhau.
        {"kind": "non_empty", "field": "wave_n"},
    ],
    "done-wave": [
        {"kind": "flag", "field": "teardown_ok", "expected": True},
    ],
}


def _run_rule(rule: dict, state: dict, evidence: dict) -> tuple[bool, str]:
    """Dispatch a single rule to its check function."""
    kind = rule.get("kind")
    try:
        if kind == "flag":
            return check_flag(evidence, rule["field"], rule["expected"])
        if kind == "all_boundaries_reviewed":
            return check_all_boundaries_reviewed(state, evidence)
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
        if kind == "hypothesis_measurable":
            return check_hypothesis_measurable(state, evidence)
        if kind == "challenge_doc":
            return check_challenge_doc(state, evidence)
        if kind == "decisions_min":
            return check_decisions_min(state, evidence)
        if kind == "no_open_findings":
            return check_no_open_findings(state)
        if kind == "doc_review":
            return check_doc_review(state, evidence)
        if kind == "doc_stamped":
            return check_doc_stamped(evidence)
        if kind == "test_passed":
            return check_test_passed(state)
        if kind == "features_complete":
            return check_features_complete(state, evidence)
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
        if kind == "journey_e2e_present":
            return check_journey_e2e_present(state, evidence)
        if kind == "ui_test_present":
            return check_ui_test_present(state, evidence)
        if kind == "registry_scope":
            return check_registry_scope(state, evidence)
        if kind == "ac_coverage":
            return check_ac_coverage(state, evidence)
        if kind == "translation_parity":
            return check_translation_parity(evidence)
        if kind == "todo_resolved":
            return check_todo_resolved(evidence)
        if kind == "contract_graph_parity":
            return check_contract_graph_parity(evidence)
        if kind == "api_contract_proof":
            return check_api_contract_proof(state, evidence)
        if kind == "api_transport":
            return check_api_transport_consistency(evidence)
        if kind == "wave_sequence_lint":
            return check_wave_sequence_lint(evidence)
        if kind == "web_styling":
            return check_web_styling(state, evidence)
        if kind == "dogfood_done":
            return check_dogfood_done(state, evidence)
        if kind == "backward_compat":
            return check_backward_compat(state, evidence)
        if kind == "discovery_stamped":
            return check_discovery_stamped(evidence)
        if kind == "edge_cases_decided":
            return check_edge_cases_decided(evidence)
        if kind == "regression_tc_present":
            return check_regression_tc_present(state, evidence)
        if kind == "mockup_signed":
            return check_mockup_signed(evidence)
        if kind == "design_system_closed":
            return check_design_system_closed(evidence)
        if kind == "production_ready":
            return check_production_ready(state, evidence)
        if kind == "challenge_passed":
            return check_challenge_passed(state, evidence)
        if kind == "discovery_wave":
            return check_discovery_wave(evidence, state)
        if kind == "discovery_advance":
            return check_discovery_advance(evidence, state)
        if kind == "domain_gate":
            return check_domain_gate(evidence)
        if kind == "domain_signed":
            return check_domain_signed(evidence)
        if kind == "domain_no_jargon":
            return check_domain_no_jargon(evidence)
        if kind == "domain_stamped":
            return check_domain_stamped(evidence)
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


# Thứ gate KHÔNG kiểm được — in ra khi chốt xanh, để "gate xanh" đừng bị đọc thành "đã phủ hết".
#
# VÌ SAO CÓ BẢNG NÀY. Gate im lặng về chỗ nó mù là dạng nói dối bằng cách bỏ sót: chốt xanh đọc như
# một lời bảo đảm, trong khi nó chỉ bảo đảm đúng phần máy đếm được. Mọi thứ dưới đây đều là thứ
# CHỈ người xác nhận được — liệt kê ra thì người biết mình còn nợ gì; giấu đi thì không ai đi làm.
MANUAL_CHECKS: dict[str, tuple[str, ...]] = {
    "approve-document": (
        "bạn đã ĐỌC tài liệu chứ không chỉ bấm duyệt — gate chỉ đếm được là file có tồn tại và có "
        "dấu đã ký",
        "có UI: đã MỞ mockup bằng trình duyệt và bấm thử một luồng, không chỉ nhìn ảnh",
    ),
    "dev-handoff": (
        "luồng lõi bấm được end-to-end ở local, không phải đọc code rồi suy ra là chạy",
    ),
    "test-execute": (
        "TC chạy trên hệ ĐANG CHẠY (gọi API/UI thật), không phải chạy unit test rồi khai là e2e",
    ),
    "dogfood": (
        "6 lăng kính thật sự MỞ và BẤM, không phải đọc code rồi suy ra — dấu hiệu giả: cả 6 báo "
        "'không thấy vấn đề gì' ngay lượt đầu",
        "phép thử phân quyền A↛B đã chạy thật ở local",
    ),
    "end-wave": (
        "đã thử khôi phục backup / rollback ít nhất một lần, nếu môi trường cho phép",
    ),
}


def manual_checks(command_id: str) -> tuple[str, ...]:
    return MANUAL_CHECKS.get(command_id, ())


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

def _print_rules() -> int:
    """In GATE_RULES cho người đọc. Thay cho việc CHÉP bảng gate vào tài liệu.

    Bảng chép tay là bản sao thứ hai của sự thật — nó trôi ngay lần đổi gate kế tiếp, và tài liệu
    trôi thì tệ hơn tài liệu thiếu (người đọc tin nó). Có lệnh in thì không cần chép.
    """
    for cmd in sorted(GATE_RULES):
        rules = GATE_RULES[cmd]
        if not rules:
            print(f"{cmd:18} (không gate — self-loop / refine)")
            continue
        parts = []
        for r in rules:
            k = r.get("kind")
            extra = ", ".join(f"{x}={r[x]}" for x in ("field", "min", "expected", "pattern", "min_count")
                              if x in r)
            parts.append(f"{k}({extra})" if extra else k)
        print(f"{cmd:18} {' · '.join(parts)}")
    return 0


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

    # #10: all_boundaries_reviewed force-bypass (env-block) → pass dù thiếu review
    assert check_all_boundaries_reviewed(st_missing, {"force": True})[0] is True
    # #10: review-dev `complete {}` (thiếu review_results) → reject (chống tạo STATE rỗng rồi kẹt)
    ok, errs = check_for_command("review-dev", state={"wave_boundaries": ["order"]}, evidence={})
    assert (not ok) and any("review_results" in e for e in errs), errs
    # có review_results → qua rule non_empty (no_open_findings tuỳ file findings)
    ok, errs = check_for_command("review-dev", state={"wave": {"id": "wave-zzz-none"}},
                                 evidence={"review_results": [{"boundary": "order", "review_result": "pass"}]})
    assert ok or all("review_results" not in e for e in errs), errs

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
    # parser tái dùng cho doc-review (id_pattern dr-\d+)
    dtbl = (
        "| finding | severity | concern | file | status |\n|---|---|---|---|---|\n"
        "| DR-001 | BLOCKER | thiếu FEAT auth/login | capability-map.md | open |\n"
        "| DR-002 | MAJOR | FEAT-003 mâu thuẫn BR-002 | FEAT-003 | resolved |\n"
    )
    assert _findings_open_from_table(dtbl, id_pattern=r"dr-\d+") == ["DR-001"], _findings_open_from_table(dtbl, id_pattern=r"dr-\d+")

    # doc_review (approve-document gate): hermetic — file findings tạm trong tmp root.
    import tempfile as _tf_dr
    _droot = Path(_tf_dr.mkdtemp(prefix="gates_dr_"))
    try:
        # (a) thiếu file → review chưa chạy → chặn
        assert check_doc_review({}, {}, root=_droot)[0] is False, "doc_review phải chặn khi thiếu findings file"
        _dr_dir = _droot / "tracking"
        _dr_dir.mkdir(parents=True, exist_ok=True)
        _dr_file = _dr_dir / "doc-review-findings.md"
        # (b) còn gap BLOCKER open → chặn
        _dr_file.write_text(dtbl, encoding="utf-8")
        ok, msg = check_doc_review({}, {}, root=_droot)
        assert ok is False and "DR-001" in msg, f"doc_review phải chặn khi còn BLOCKER open: {msg}"
        # (c) force bypass dù còn gap
        assert check_doc_review({}, {"force": True}, root=_droot)[0] is True, "doc_review force phải bypass"
        # (d) findings đều closed → pass
        _dr_file.write_text(
            "| finding | severity | concern | file | status |\n|---|---|---|---|---|\n"
            "| DR-001 | BLOCKER | thiếu FEAT auth | capability-map.md | resolved |\n",
            encoding="utf-8",
        )
        assert check_doc_review({}, {}, root=_droot)[0] is True, "doc_review pass khi mọi gap đã resolved"
    finally:
        import shutil as _sh_dr
        _sh_dr.rmtree(_droot, ignore_errors=True)

    # _screen_map_problems (thiết kế theo MÀN): SCREEN-MAP gắn màn↔boundary↔mockup, mockup tồn tại + dùng token
    _mkroot = Path(__import__("tempfile").mkdtemp(prefix="gates_mk_"))
    try:
        import shutil as _sh_mk
        _fe = [("shop-web", "web"), ("order", "backend")]
        # (a) không FE boundary → không áp dụng
        assert _screen_map_problems([("order", "backend")], _mkroot) == []
        # (b) có web boundary mà thiếu SCREEN-MAP → fail
        probs = _screen_map_problems(_fe, _mkroot)
        assert probs and "SCREEN-MAP.md" in probs[0], probs
        _uxd = _mkroot / "docs" / "architecture" / "ux"
        _uxd.mkdir(parents=True, exist_ok=True)
        # (c) màn trỏ mockup không tồn tại + màn gán boundary ma → fail cả 2
        (_uxd / "SCREEN-MAP.md").write_text(
            "# Screen map\n\n"
            "| screen | route | boundary | feat | mockup | note |\n"
            "|--------|-------|----------|------|--------|------|\n"
            "| rooms-day | /rooms | shop-web | FEAT-001 | `mockups/shop-web/rooms-day.html` | |\n"
            "| ghost-scr | /x | billing-web | FEAT-002 | `mockups/billing-web/x.html` | |\n",
            encoding="utf-8")
        probs = _screen_map_problems(_fe, _mkroot)
        blob = " ".join(probs)
        assert "KHÔNG tồn tại" in blob and "billing-web" in blob, probs
        # (d) mockup tồn tại nhưng không dùng token → fail; dùng token → sạch
        _mkd = _uxd / "mockups" / "shop-web"
        _mkd.mkdir(parents=True, exist_ok=True)
        (_mkd / "rooms-day.html").write_text("<html><body style='color:#333'>x</body></html>", encoding="utf-8")
        (_uxd / "SCREEN-MAP.md").write_text(
            "| screen | route | boundary | feat | mockup |\n|--|--|--|--|--|\n"
            "| rooms-day | /rooms | shop-web | FEAT-001 | `mockups/shop-web/rooms-day.html` |\n",
            encoding="utf-8")
        probs = _screen_map_problems(_fe, _mkroot)
        assert probs and "design token" in probs[0], probs
        (_mkd / "rooms-day.html").write_text(
            '<html><head><link rel="stylesheet" href="../..design-tokens.css"></head>'
            '<body><div style="color: var(--color-text)">x</div></body></html>', encoding="utf-8")
        assert _screen_map_problems(_fe, _mkroot) == [], _screen_map_problems(_fe, _mkroot)
        # (e) web boundary không có màn nào trong map → fail (boundary trắng design)
        _fe2 = _fe + [("admin-web", "web")]
        probs = _screen_map_problems(_fe2, _mkroot)
        assert probs and "admin-web" in probs[0] and "trắng design" in probs[0], probs
        # (f) màn tuân thủ FEAT (khi feat/ đã author): FEAT ma bị bắt + FEAT có UI 0 màn bị bắt
        _fdir = _mkroot / "docs" / "architecture" / "feat"
        _fdir.mkdir(parents=True, exist_ok=True)
        (_fdir / "FEAT-001.md").write_text('---\nid: "FEAT-001"\nhas_ui_touchpoint: true\n---\n# F\n', encoding="utf-8")
        (_fdir / "FEAT-010.md").write_text('---\nid: "FEAT-010"\nhas_ui_touchpoint: false\n---\n# BE-only\n', encoding="utf-8")
        (_fdir / "FEAT-020.md").write_text('---\nid: "FEAT-020"\nhas_ui_touchpoint: true\nstatus: "deferred"\n---\n# defer\n', encoding="utf-8")
        assert _screen_map_problems(_fe, _mkroot) == [], _screen_map_problems(_fe, _mkroot)  # FEAT-001 có màn; 010 no-UI; 020 deferred
        (_fdir / "FEAT-777.md").write_text('---\nid: "FEAT-777"\nhas_ui_touchpoint: true\n---\n# UI bị bỏ rơi\n', encoding="utf-8")
        probs = _screen_map_problems(_fe, _mkroot)
        assert probs and "FEAT-777" in probs[0] and "bỏ rơi" in probs[0], probs
        (_fdir / "FEAT-777.md").unlink()
        (_uxd / "SCREEN-MAP.md").write_text(
            "| screen | route | boundary | feat | mockup |\n|--|--|--|--|--|\n"
            "| rooms-day | /rooms | shop-web | FEAT-001, FEAT-404 | `mockups/shop-web/rooms-day.html` |\n",
            encoding="utf-8")
        probs = _screen_map_problems(_fe, _mkroot)
        assert probs and "FEAT-404" in probs[0] and "feature ma" in probs[0], probs
    finally:
        _sh_mk.rmtree(_mkroot, ignore_errors=True)

    # doc_stamped: design/contract doc phải APPROVED/ACTIVE (stamp bởi approve_document.py) — chặn approve chay
    import tempfile as _tf_ds, shutil as _sh_ds
    _dsroot = Path(_tf_ds.mkdtemp(prefix="gates_ds_"))
    try:
        (_dsroot / "docs" / "architecture" / "hld").mkdir(parents=True, exist_ok=True)
        (_dsroot / "docs" / "architecture" / "api").mkdir(parents=True, exist_ok=True)
        (_dsroot / "docs" / "architecture" / "hld" / "hld-x.md").write_text(
            "---\nstatus: DRAFT\n---\n# H\n", encoding="utf-8")
        (_dsroot / "docs" / "architecture" / "api" / "TEMPLATE.api.md").write_text(
            "---\nstatus: DRAFT\n---\n", encoding="utf-8")  # TEMPLATE bỏ qua
        ok, msg = check_doc_stamped(root=_dsroot)
        assert (not ok) and "hld-x.md" in msg and "approve_document.py" in msg, msg
        (_dsroot / "docs" / "architecture" / "hld" / "hld-x.md").write_text(
            "---\nstatus: APPROVED\n---\n# H\n", encoding="utf-8")
        assert check_doc_stamped(root=_dsroot)[0] is True, "hld APPROVED → pass"
        # contract: DRAFT fail (cần ACTIVE); DEPRECATED hợp lệ
        (_dsroot / "docs" / "architecture" / "api" / "api-x.md").write_text(
            "---\nstatus: DRAFT\n---\n# A\n", encoding="utf-8")
        ok, msg = check_doc_stamped(root=_dsroot)
        assert (not ok) and "api-x.md" in msg and "ACTIVE" in msg, msg
        (_dsroot / "docs" / "architecture" / "api" / "api-x.md").write_text(
            "---\nstatus: ACTIVE\n---\n# A\n", encoding="utf-8")
        (_dsroot / "docs" / "architecture" / "api" / "api-old.md").write_text(
            "---\nstatus: DEPRECATED\n---\n# old\n", encoding="utf-8")
        assert check_doc_stamped(root=_dsroot)[0] is True, "ACTIVE + DEPRECATED → pass"
        assert check_doc_stamped({"force": True}, root=_dsroot)[0] is True
        import approve_document as _apdoc
        assert _apdoc._selftest() == 0
    finally:
        _sh_ds.rmtree(_dsroot, ignore_errors=True)

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
        # (G15) plain CSS hardcode (không var(--)) → FAIL (không dùng design token)
        (_wsrc / "App.css").write_text(".x{color:red}", encoding="utf-8")
        ok, msg = check_web_styling(_ws_state, root=_wroot)
        assert (not ok) and "design token" in msg, f"web_styling phải chặn CSS hardcode không token: {msg}"
        # var(--...) nhưng KHÔNG định nghĩa/import token → FAIL (var resolve rỗng = vẫn unstyled)
        (_wsrc / "App.css").write_text(".x{color:var(--color-primary);padding:var(--space-md)}", encoding="utf-8")
        ok, msg = check_web_styling(_ws_state, root=_wroot)
        assert (not ok) and "định nghĩa" in msg, f"web_styling phải chặn var() không có token definition: {msg}"
        # thêm định nghĩa token (copy design-tokens vào src) → PASS
        (_wsrc / "design-tokens.css").write_text(":root{--color-primary:#1d4ed8;--space-md:16px}", encoding="utf-8")
        assert check_web_styling(_ws_state, root=_wroot)[0] is True, "web_styling phải pass khi CSS dùng + định nghĩa token"
        # component library (antd — ADR ui-kit): 0 file CSS vẫn styled, token map qua theme → PASS
        (_wsrc / "App.css").unlink(); (_wsrc / "design-tokens.css").unlink()
        (_wsrc / "App.tsx").write_text(
            "import { Button } from 'antd';\nexport const A = () => <Button className=\"x\">hi</Button>;",
            encoding="utf-8")
        assert check_web_styling(_ws_state, root=_wroot)[0] is True, "dùng component library (antd) phải pass"
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
        # (d) TC-I01 FAIL nhưng log KHÔNG đọc ra nguyên nhân → fail.
        #     Trước đây phép này đòi một row BUG-NNN trong bugs.md; sổ bug đã bỏ vì trùng với
        #     test-report. Thứ cần chặn vẫn nguyên: "FAIL rồi để đó, không ai biết vì sao".
        (_tw / "test-report.md").write_text(
            "| TC | Result |\n|----|--------|\n| TC-I01 | FAIL |\n", encoding="utf-8")
        (_tlogs / "TC-I01.log").write_text("POST /v1/holds -> 200\nchạy xong\n", encoding="utf-8")
        ok, msg = check_test_evidence(_te_state, root=_troot)
        assert (not ok) and "TC-I01" in msg and "NGUYÊN NHÂN" in msg, \
            f"FAIL không nêu nguyên nhân phải fail: {msg}"
        # (d2) log CÓ dấu vết lỗi thật → evidence pass (fail đã đọc ra được vì sao)
        (_tlogs / "TC-I01.log").write_text(
            "POST /v1/holds -> 500\nAssertionError: expected 201, got 500\n", encoding="utf-8")
        assert check_test_evidence(_te_state, root=_troot)[0] is True, \
            "FAIL có nguyên nhân → evidence pass"
        # nhưng derive = 'fail' (in-scope không all-pass) → end-wave vẫn chặn
        assert derive_test_result(_te_state, root=_troot) == "fail"
        (_tlogs / "TC-I01.log").write_text("POST /v1/holds -> 200\nOK\n", encoding="utf-8")
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
        # (g) TC trên WEB boundary: pass mà thiếu screenshot → fail; PNG giả (text) → fail; PNG thật → pass
        (_troot / "harness").mkdir(parents=True, exist_ok=True)
        (_troot / "harness" / "SERVICE-BOUNDARY-MATRIX.json").write_text(json.dumps({"version": 1, "boundaries": [
            {"boundary_id": "webapp", "kind": "web", "prefix": "demo"}]}), encoding="utf-8")
        (_tw / "test-case-registry.md").write_text(
            "| TC | group | type | boundary | feature | AC | tags |\n"
            "|----|-------|------|----------|---------|----|------|\n"
            "| TC-W01 | e2e | auto | webapp | FEAT-001 | AC-1 | @FEAT-001 |\n", encoding="utf-8")
        (_tw / "test-report.md").write_text(
            "| TC | Result |\n|----|--------|\n| TC-W01 | PASS |\n", encoding="utf-8")
        (_tlogs / "TC-W01.log").write_text("GET http://localhost:5173/ -> 200\nrendered\n", encoding="utf-8")
        ok, msg = check_test_evidence(_te_state, root=_troot)
        assert (not ok) and "screenshot" in msg, f"web TC pass không screenshot phải fail: {msg}"
        _shots = _tw / "screenshots"
        _shots.mkdir(parents=True, exist_ok=True)
        (_shots / "TC-W01.png").write_text("fake text pretending to be png" + "x" * 1100, encoding="utf-8")
        ok, msg = check_test_evidence(_te_state, root=_troot)
        assert (not ok) and "screenshot" in msg, f"PNG giả (text) phải fail magic-check: {msg}"
        (_shots / "TC-W01.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 1200)
        assert check_test_evidence(_te_state, root=_troot)[0] is True, "web TC pass + screenshot PNG thật → pass"
        # (h) skip 'service-down' mâu thuẫn health-proof (service UP) → fail
        (_tw / "test-report.md").write_text(
            "| TC | Result |\n|----|--------|\n| TC-W01 | SKIP |\n", encoding="utf-8")
        (_tlogs / "TC-W01.log").write_text("connection refused khi mở UI\n", encoding="utf-8")
        assert check_test_evidence(_te_state, root=_troot)[0] is False  # 0 in-scope chạy → vẫn fail
        (_tw / "health-proof.json").write_text(json.dumps({"probes": [
            {"boundary": "webapp", "http_status": 200, "ok": True}]}), encoding="utf-8")
        ok, msg = check_test_evidence(_te_state, root=_troot)
        assert (not ok) and "MÂU THUẪN" in msg, f"skip down khi proof nói UP phải fail: {msg}"
        # (i) marker lỏng cũ: log chứa 'dropdown' KHÔNG được tính là service-down
        (_tw / "health-proof.json").unlink()
        (_tlogs / "TC-W01.log").write_text("mở dropdown rồi skip\n", encoding="utf-8")
        ok, msg = check_test_evidence(_te_state, root=_troot)
        assert (not ok) and "silent-skip" in msg, f"'dropdown' không phải lý do service-down: {msg}"
    finally:
        _shutil.rmtree(_troot, ignore_errors=True)

    # ui_test_present: web boundary phải có ≥1 auto-TC UI in-scope (deferred không tính).
    _uroot = Path(_tf_hp.mkdtemp(prefix="gates_ui_"))
    try:
        (_uroot / "harness").mkdir(parents=True, exist_ok=True)
        (_uroot / "harness" / "SERVICE-BOUNDARY-MATRIX.json").write_text(json.dumps({"version": 1, "boundaries": [
            {"boundary_id": "scheduling", "kind": "backend", "prefix": "demo"},
            {"boundary_id": "patient-web", "kind": "web", "prefix": "demo"}]}), encoding="utf-8")
        _ui_state = {"wave": {"id": "wave-001"}, "wave_boundaries": ["scheduling", "patient-web"]}
        _uw = _uroot / "tracking" / "wave-001"
        _uw.mkdir(parents=True, exist_ok=True)
        (_uroot / "docs" / "plans").mkdir(parents=True, exist_ok=True)
        (_uroot / "docs" / "plans" / "wave-001.md").write_text(
            "# Wave 1\nFEAT-001\n\n## Deferred to later waves\n\n- FEAT-005\n", encoding="utf-8")
        # (a) registry chỉ TC backend → fail cite patient-web
        (_uw / "test-case-registry.md").write_text(
            "| TC | group | type | boundary | feature | AC | tags |\n"
            "|----|-------|------|----------|---------|----|------|\n"
            "| TC-I01 | integration | auto | scheduling | FEAT-001 | AC-1 | @FEAT-001 |\n", encoding="utf-8")
        ok, msg = check_ui_test_present(_ui_state, root=_uroot)
        assert (not ok) and "patient-web" in msg, msg
        # (b) UI TC duy nhất bị tag @deferred (khai báo hợp lệ) → vẫn fail (né bằng tag không được)
        (_uw / "test-case-registry.md").write_text(
            "| TC | group | type | boundary | feature | AC | tags |\n"
            "|----|-------|------|----------|---------|----|------|\n"
            "| TC-I01 | integration | auto | scheduling | FEAT-001 | AC-1 | @FEAT-001 |\n"
            "| TC-U01 | e2e | auto | patient-web | FEAT-005 | AC-1 | @FEAT-005 @deferred |\n", encoding="utf-8")
        ok, msg = check_ui_test_present(_ui_state, root=_uroot)
        assert (not ok) and "patient-web" in msg, f"UI TC deferred-only phải vẫn fail: {msg}"
        # (c) có auto UI TC in-scope → pass
        (_uw / "test-case-registry.md").write_text(
            "| TC | group | type | boundary | feature | AC | tags |\n"
            "|----|-------|------|----------|---------|----|------|\n"
            "| TC-U01 | e2e | auto | patient-web | FEAT-001 | AC-1 | @FEAT-001 |\n", encoding="utf-8")
        assert check_ui_test_present(_ui_state, root=_uroot)[0] is True, "có UI TC in-scope → pass"
        # (d) wave không có web boundary → không áp dụng; force bypass
        assert check_ui_test_present({"wave": {"id": "wave-001"}, "wave_boundaries": ["scheduling"]}, root=_uroot)[0] is True
        assert check_ui_test_present(_ui_state, {"force": True}, root=_uroot)[0] is True
    finally:
        _shutil.rmtree(_uroot, ignore_errors=True)

    # registry_scope: TC chỉ trace FEAT ≤ wave hiện tại; deferred phải tag @deferred.
    _sroot = Path(_tf_hp.mkdtemp(prefix="gates_rs_"))
    try:
        (_sroot / "docs" / "plans").mkdir(parents=True, exist_ok=True)
        (_sroot / "docs" / "plans" / "wave-001.md").write_text(
            "# Wave 1\n| FEAT-001 | boundaries/api | Must |\n\n"
            "## Deferred to later waves\n\n| FEAT-002:AC-3 | auth wave sau | wave-002 |\n", encoding="utf-8")
        (_sroot / "docs" / "plans" / "wave-002.md").write_text(
            "# Wave 2\n| FEAT-003 | boundaries/api | Must |\n", encoding="utf-8")
        _rs_state = {"wave": {"id": "wave-001"}}
        _sw = _sroot / "tracking" / "wave-001"
        _sw.mkdir(parents=True, exist_ok=True)
        _rs_reg = _sw / "test-case-registry.md"
        # (a) TC trace FEAT-003 (chỉ có ở wave-002 tương lai) → over-scope fail
        _rs_reg.write_text(
            "| TC | group | type | boundary | feature | AC | tags |\n"
            "|----|-------|------|----------|---------|----|------|\n"
            "| TC-A | functional | auto | api | FEAT-001 | AC-1 | @FEAT-001 |\n"
            "| TC-B | functional | auto | api | FEAT-003 | AC-1 | @FEAT-003 |\n", encoding="utf-8")
        ok, msg = check_registry_scope(_rs_state, root=_sroot)
        assert (not ok) and "TC-B" in msg and "over-scope" in msg, msg
        # (b) TC cho token deferred nhưng KHÔNG tag @deferred → fail (chính là gap bug-rác)
        _rs_reg.write_text(
            "| TC | group | type | boundary | feature | AC | tags |\n"
            "|----|-------|------|----------|---------|----|------|\n"
            "| TC-C | security | auto | api | FEAT-002 | AC-3 | @FEAT-002 |\n", encoding="utf-8")
        ok, msg = check_registry_scope(_rs_state, root=_sroot)
        assert (not ok) and "TC-C" in msg and "@deferred" in msg, msg
        # (c) tag @deferred đúng + TC in-scope + smoke không trace FEAT → pass
        _rs_reg.write_text(
            "| TC | group | type | boundary | feature | AC | tags |\n"
            "|----|-------|------|----------|---------|----|------|\n"
            "| TC-A | functional | auto | api | FEAT-001 | AC-1 | @FEAT-001 |\n"
            "| TC-C | security | auto | api | FEAT-002 | AC-3 | @FEAT-002 @deferred |\n"
            "| TC-S01 | smoke | auto | api | — | — | @smoke |\n", encoding="utf-8")
        assert check_registry_scope(_rs_state, root=_sroot)[0] is True, "in-scope + deferred-tagged + smoke → pass"
        # (d) sang wave-002: FEAT-003 thành hợp lệ (registry tích luỹ)
        _sw2 = _sroot / "tracking" / "wave-002"
        _sw2.mkdir(parents=True, exist_ok=True)
        (_sw2 / "test-case-registry.md").write_text(
            "| TC | group | type | boundary | feature | AC | tags |\n"
            "|----|-------|------|----------|---------|----|------|\n"
            "| TC-B | functional | auto | api | FEAT-003 | AC-1 | @FEAT-003 |\n", encoding="utf-8")
        assert check_registry_scope({"wave": {"id": "wave-002"}}, root=_sroot)[0] is True, "FEAT wave hiện tại hợp lệ"
        # (e) force bypass
        _rs_reg.write_text("| TC | group | type | feature |\n|--|--|--|--|\n| TC-X | e2e | auto | FEAT-099 |\n", encoding="utf-8")
        assert check_registry_scope(_rs_state, {"force": True}, root=_sroot)[0] is True
    finally:
        _shutil.rmtree(_sroot, ignore_errors=True)

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
        # (b) Dockerfile + Postgres + base config NHƯNG thiếu PROFILE file → vẫn fail (thiếu profile)
        (_svc / "Dockerfile").write_text("FROM eclipse-temurin:21-jre\n", encoding="utf-8")
        (_svc / "pom.xml").write_text("<project><dependency><groupId>org.postgresql</groupId></dependency></project>", encoding="utf-8")
        (_res / "application.yml").write_text("spring:\n  datasource:\n    url: jdbc:postgresql://db:5432/app\n  jpa:\n    hibernate:\n      ddl-auto: validate\n", encoding="utf-8")
        ok, msg = check_code_compliance(_cc_state, root=_croot)
        assert (not ok) and "PROFILE" in msg, f"thiếu profile file phải fail: {msg}"
        # (c) thêm profile file NHƯNG chưa có ArchUnit test → vẫn fail (thiếu ArchUnit)
        (_res / "application-dev.yml").write_text("spring:\n  datasource:\n    url: jdbc:postgresql://dev-db:5432/app\n", encoding="utf-8")
        ok, msg = check_code_compliance(_cc_state, root=_croot)
        assert (not ok) and "ArchUnit" in msg, f"thiếu ArchUnit test phải fail: {msg}"
        # (d) thêm ArchUnit test → pass
        _at = _svc / "src" / "test" / "java" / "arch"
        _at.mkdir(parents=True, exist_ok=True)
        (_at / "ArchitectureTest.java").write_text(
            "import com.tngtech.archunit.junit.ArchTest;\n// layer rules\n", encoding="utf-8")
        assert check_code_compliance(_cc_state, root=_croot)[0] is True, "pass khi Postgres+Dockerfile+base+profile+ArchUnit"
        # (e) web boundary bỏ qua (chỉ backend); chưa scaffold → bỏ qua. force bypass
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

    # journey_e2e_present: chuỗi depends_on ≥3 (order→payment→ledger) phải có TC span cả chuỗi.
    _jroot = Path(_tf_hp.mkdtemp(prefix="gates_je_"))
    try:
        (_jroot / "harness").mkdir(parents=True, exist_ok=True)
        (_jroot / "harness" / "SERVICE-BOUNDARY-MATRIX.json").write_text(json.dumps({"version": 1, "boundaries": [
            {"boundary_id": "order", "kind": "backend", "prefix": "demo", "depends_on": ["payment"]},
            {"boundary_id": "payment", "kind": "backend", "prefix": "demo", "depends_on": ["ledger"]},
            {"boundary_id": "ledger", "kind": "backend", "prefix": "demo"},
        ]}), encoding="utf-8")
        _je_state = {"wave": {"id": "wave-001"}, "wave_boundaries": ["order", "payment", "ledger"]}
        _jew = _jroot / "tracking" / "wave-001"
        _jew.mkdir(parents=True, exist_ok=True)
        _jreg = _jew / "test-case-registry.md"
        # (a) chỉ pairwise (order↔payment, payment↔ledger), KHÔNG span cả chuỗi → fail
        _jreg.write_text(
            "| TC | group | type | boundary | feature | AC | tags |\n"
            "|----|-------|------|----------|---------|----|------|\n"
            "| TC-I01 | integration | auto | order | FEAT-001 | AC-1 | @order @payment |\n"
            "| TC-I02 | integration | auto | payment | FEAT-002 | AC-1 | @payment @ledger |\n",
            encoding="utf-8")
        ok, msg = check_journey_e2e_present(_je_state, root=_jroot)
        assert (not ok) and "order → payment → ledger" in msg, msg
        # (b) thêm TC e2e span cả 3 → pass
        _jreg.write_text(
            "| TC | group | type | boundary | feature | AC | tags |\n"
            "|----|-------|------|----------|---------|----|------|\n"
            "| TC-E01 | e2e | auto | order | FEAT-001 | AC-1 | @order @payment @ledger |\n",
            encoding="utf-8")
        assert check_journey_e2e_present(_je_state, root=_jroot)[0] is True, "TC span cả chuỗi → pass"
        # (c) wave 2-boundary (không chuỗi ≥3) → vacuous pass
        _je_state2 = {"wave": {"id": "wave-001"}, "wave_boundaries": ["order", "payment"]}
        assert check_journey_e2e_present(_je_state2, root=_jroot)[0] is True, "≤2 boundary → vacuous"
        # (d) force bypass
        _jreg.write_text("no tc\n", encoding="utf-8")
        assert check_journey_e2e_present(_je_state, {"force": True}, root=_jroot)[0] is True
    finally:
        _shutil.rmtree(_jroot, ignore_errors=True)

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

    # domain_signed + domain_no_jargon (#2/#3): business layer docs/domain/ ký + no-jargon
    _droot = Path(_tf_hp.mkdtemp(prefix="gates_dom_"))
    try:
        for sub in ("epics", "feat", "business-rules"):
            (_droot / "docs" / "domain" / sub).mkdir(parents=True, exist_ok=True)
        ep = _droot / "docs" / "domain" / "epics" / "EP-1.md"
        ft = _droot / "docs" / "domain" / "feat" / "FEAT-1.md"
        br = _droot / "docs" / "domain" / "business-rules" / "BR-1.md"
        # (a) chưa có file → signed fail
        ok, msg = check_domain_signed(root=_droot)
        assert (not ok) and "chưa có business doc" in msg, msg
        # author 3 business doc plain, chỉ EP ký (status APPROVED)
        ep.write_text("---\nstatus: APPROVED\n---\n# Epic\nKhách đặt lịch khám.\n", encoding="utf-8")
        ft.write_text("---\nstatus: DRAFT\n---\n# Feature\nĐặt lịch trong 24h.\n", encoding="utf-8")
        br.write_text("# BR\nKhông cho đặt trùng giờ.\n", encoding="utf-8")
        ok, msg = check_domain_signed(root=_droot)
        assert (not ok) and ("FEAT-1" in msg and "BR-1" in msg), f"còn doc chưa ký phải fail: {msg}"
        # ký hết → pass
        ft.write_text("---\nstatus: APPROVED\n---\n# Feature\nĐặt lịch trong 24h.\n", encoding="utf-8")
        br.write_text("---\nstatus: APPROVED\n---\n# BR\nKhông cho đặt trùng giờ.\n", encoding="utf-8")
        assert check_domain_signed(root=_droot)[0] is True, "ký hết → signed pass"
        assert check_domain_signed({"force": True}, root=_droot)[0] is True
        # no-jargon: doc có SQL/class → fail
        ep.write_text("---\nstatus: APPROVED\n---\n# Epic\nDùng bảng SELECT * FROM appointment.\n", encoding="utf-8")
        ok, msg = check_domain_no_jargon(root=_droot)
        assert (not ok) and "EP-1" in msg, f"jargon SQL phải fail: {msg}"
        # target filter: chỉ check FEAT-1 (sạch) → pass dù EP-1 bẩn
        assert check_domain_no_jargon({"target": "FEAT-1"}, root=_droot)[0] is True
        # clean lại → pass
        ep.write_text("---\nstatus: APPROVED\n---\n# Epic\nKhách đặt lịch khám.\n", encoding="utf-8")
        assert check_domain_no_jargon(root=_droot)[0] is True
        assert check_domain_no_jargon({"force": True}, root=_droot)[0] is True
        # domain_stamped (chặn approve chay): doc chưa stamp → fail nêu script; stamp rồi → pass
        ft.write_text("---\nstatus: DRAFT\n---\n# Feature\nĐặt lịch trong 24h.\n", encoding="utf-8")
        ok, msg = check_domain_stamped({"target": "all"}, root=_droot)
        assert (not ok) and "FEAT-1" in msg and "domain_approve.py" in msg, msg
        # target lẻ: chỉ check doc đó (EP-1 đã APPROVED → pass dù FEAT-1 còn DRAFT)
        assert check_domain_stamped({"target": "EP-1"}, root=_droot)[0] is True
        ft.write_text("---\nstatus: APPROVED\n---\n# Feature\nĐặt lịch trong 24h.\n", encoding="utf-8")
        assert check_domain_stamped({"target": "all"}, root=_droot)[0] is True, "stamp đủ → pass"
        assert check_domain_stamped({"force": True}, root=_droot)[0] is True
    finally:
        _shutil.rmtree(_droot, ignore_errors=True)

    # discovery_advance (cơ chế start D0→Dn): force/refine/first-entry không gate (advance-gate đọc disk → smoke force)
    assert check_discovery_advance({"force": True}, {"stage": "DISC_D0"}) == (True, "")
    assert check_discovery_advance({"wave": "D1"}, {"stage": "DISC_D1"}) == (True, "")   # refine cùng wave
    assert check_discovery_advance({"wave": "D0"}, {"stage": "BOOTSTRAP"}) == (True, "")  # first-entry D0

    # wave_sequence_lint (G16): wiring + force-bypass (logic test đầy đủ ở wave_sequence_lint._selftest)
    assert check_wave_sequence_lint({"force": True}) == (True, "")
    assert isinstance(check_wave_sequence_lint()[0], bool)
    import wave_sequence_lint as _wsl
    assert _wsl._selftest() == 0

    # translation_parity: business đã ký ↔ eng doc 1-1; eng mồ côi bị flag.
    _tproot = Path(_tf_hp.mkdtemp(prefix="gates_tp_"))
    try:
        (_tproot / "docs" / "domain" / "feat").mkdir(parents=True, exist_ok=True)
        (_tproot / "docs" / "architecture" / "feat").mkdir(parents=True, exist_ok=True)
        _bizf = _tproot / "docs" / "domain" / "feat" / "FEAT-001.md"
        _bizf.write_text('---\nid: "FEAT-001"\nstatus: APPROVED\n---\n# F\nKhách đặt lịch.\n', encoding="utf-8")
        # (a) ký rồi nhưng chưa có eng doc → fail (translate bỏ sót)
        ok, msg = check_translation_parity(root=_tproot)
        assert (not ok) and "FEAT-001" in msg and "bỏ sót" in msg, msg
        # (b) eng doc có source trỏ về business → pass
        (_tproot / "docs" / "architecture" / "feat" / "FEAT-001.md").write_text(
            '---\nid: "FEAT-001"\nsource: docs/domain/feat/FEAT-001.md\n---\n# F eng\n', encoding="utf-8")
        assert check_translation_parity(root=_tproot)[0] is True, "eng doc khớp source → pass"
        # (c) eng doc MỒ CÔI (không source, không khớp business nào) → fail
        (_tproot / "docs" / "architecture" / "feat" / "FEAT-999.md").write_text(
            '---\nid: "FEAT-999"\n---\n# tự author thẳng eng\n', encoding="utf-8")
        ok, msg = check_translation_parity(root=_tproot)
        assert (not ok) and "FEAT-999" in msg and "MỒ CÔI" in msg, msg
        (_tproot / "docs" / "architecture" / "feat" / "FEAT-999.md").unlink()
        # (d) README.md trong folder eng KHÔNG bị coi là eng doc mồ côi (bug drift _is_scaffold_md)
        (_tproot / "docs" / "architecture" / "feat" / "README.md").write_text("# feat folder\nMô tả.\n", encoding="utf-8")
        assert check_translation_parity(root=_tproot)[0] is True, "README.md không phải eng doc — không coi mồ côi"
        # (e) force bypass
        assert check_translation_parity({"force": True}, root=_tproot)[0] is True
    finally:
        _shutil.rmtree(_tproot, ignore_errors=True)

    # todo_resolved: marker TODO-engineer/TBD(DESIGN) phải được DESIGN điền hết.
    _tdroot = Path(_tf_hp.mkdtemp(prefix="gates_td_"))
    try:
        _brd = _tdroot / "docs" / "architecture" / "business-rules"
        _brd.mkdir(parents=True, exist_ok=True)
        (_brd / "BR-001.md").write_text(
            '---\nid: "BR-001"\nenforcement_location: TBD (DESIGN)\n---\n# BR\nconsumes_contracts: [] # TODO engineer\n',
            encoding="utf-8")
        ok, msg = check_todo_resolved(root=_tdroot)
        assert (not ok) and "BR-001" in msg, msg
        (_brd / "BR-001.md").write_text(
            '---\nid: "BR-001"\nenforcement_location: "api (scheduling POST /appointments)"\n---\n# BR\n',
            encoding="utf-8")
        assert check_todo_resolved(root=_tdroot)[0] is True, "đã điền hết TBD → pass"
        assert check_todo_resolved({"force": True}, root=_tdroot)[0] is True
    finally:
        _shutil.rmtree(_tdroot, ignore_errors=True)

    # ac_coverage: AC in-scope phải có TC (2 chiều: AC mồ côi + TC stale); deferred token bỏ qua.
    _acroot = Path(_tf_hp.mkdtemp(prefix="gates_ac_"))
    try:
        (_acroot / "docs" / "architecture" / "feat").mkdir(parents=True, exist_ok=True)
        (_acroot / "docs" / "plans").mkdir(parents=True, exist_ok=True)
        _acw = _acroot / "tracking" / "wave-001"
        _acw.mkdir(parents=True, exist_ok=True)
        (_acroot / "docs" / "architecture" / "feat" / "FEAT-T01.md").write_text(
            "# F\n### AC-1: happy\n...\n### AC-2: validation\n...\n### AC-3: auth\n...\n", encoding="utf-8")
        (_acroot / "docs" / "plans" / "wave-001.md").write_text(
            "# W1\nFEAT-T01\n\n## Deferred to later waves\n\n- FEAT-T01:AC-3\n", encoding="utf-8")
        _ac_state = {"wave": {"id": "wave-001"}, "wave_features": ["FEAT-T01"]}
        _acreg = _acw / "test-case-registry.md"
        # (a) chỉ phủ AC-1 → fail cite AC-2 (AC-3 deferred nên bỏ qua)
        _acreg.write_text(
            "| TC | group | type | boundary | feature | AC | tags |\n"
            "|----|-------|------|----------|---------|----|------|\n"
            "| TC-1 | functional | auto | api | FEAT-T01 | FEAT-T01:AC-1 | @FEAT-T01 |\n", encoding="utf-8")
        ok, msg = check_ac_coverage(_ac_state, root=_acroot)
        assert (not ok) and "AC-2" in msg and "AC-3" not in msg, msg
        # (b) phủ đủ AC-1+AC-2 (manual cũng tính) → pass
        _acreg.write_text(
            "| TC | group | type | boundary | feature | AC | tags |\n"
            "|----|-------|------|----------|---------|----|------|\n"
            "| TC-1 | functional | auto | api | FEAT-T01 | FEAT-T01:AC-1 | @FEAT-T01 |\n"
            "| TC-2 | uat | manual | api | FEAT-T01 | AC-2 | @FEAT-T01 |\n", encoding="utf-8")
        assert check_ac_coverage(_ac_state, root=_acroot)[0] is True, "phủ đủ AC in-scope → pass"
        # (c) TC stale: trace AC-9 không tồn tại trong FEAT → fail
        _acreg.write_text(
            "| TC | group | type | boundary | feature | AC | tags |\n"
            "|----|-------|------|----------|---------|----|------|\n"
            "| TC-1 | functional | auto | api | FEAT-T01 | FEAT-T01:AC-1 | @FEAT-T01 |\n"
            "| TC-2 | uat | manual | api | FEAT-T01 | AC-2 | @FEAT-T01 |\n"
            "| TC-9 | functional | auto | api | FEAT-T01 | FEAT-T01:AC-9 | @FEAT-T01 |\n", encoding="utf-8")
        ok, msg = check_ac_coverage(_ac_state, root=_acroot)
        assert (not ok) and "TC-9" in msg and "stale" in msg, msg
        # (d) FEAT không có file → bỏ qua (plan_integrity lo); force bypass
        _ac_state2 = {"wave": {"id": "wave-001"}, "wave_features": ["FEAT-NOFILE"]}
        _acreg.write_text("| TC | group | type | feature | AC |\n|--|--|--|--|--|\n", encoding="utf-8")
        assert check_ac_coverage(_ac_state2, root=_acroot)[0] is True
        # (e) FEAT CÓ file nhưng 0 AC `### AC-n` → KHÔNG bỏ qua im lặng, phải fail (khe lọt verify đã vá)
        (_acroot / "docs" / "architecture" / "feat" / "FEAT-NOAC.md").write_text(
            "# Feat không đánh số AC\nBusiness prose nhưng thiếu heading AC.\n", encoding="utf-8")
        _ac_state3 = {"wave": {"id": "wave-001"}, "wave_features": ["FEAT-NOAC"]}
        ok, msg = check_ac_coverage(_ac_state3, root=_acroot)
        assert (not ok) and "FEAT-NOAC" in msg and "KHÔNG có AC" in msg, f"FEAT 0-AC phải fail: {msg}"
        assert check_ac_coverage(_ac_state, {"force": True}, root=_acroot)[0] is True

        # derive_feature_states (L05/L07/L08): trạng thái FEAT derive từ registry + report.
        # FEAT-T01 có AC-1,AC-2,AC-3(deferred) → in-scope {AC-1,AC-2}. Registry: TC-1→AC-1, TC-2→AC-2.
        _fs_state = {"wave": {"id": "wave-001"}, "wave_features": ["FEAT-T01"]}
        _acreg.write_text(
            "| TC | group | type | boundary | feature | AC | tags |\n"
            "|----|-------|------|----------|---------|----|------|\n"
            "| TC-1 | functional | auto | api | FEAT-T01 | FEAT-T01:AC-1 | @FEAT-T01 |\n"
            "| TC-2 | functional | auto | api | FEAT-T01 | FEAT-T01:AC-2 | @FEAT-T01 |\n", encoding="utf-8")
        _rep = _acw / "test-report.md"
        # (a) chưa có report → not_started
        if _rep.exists():
            _rep.unlink()
        d = derive_feature_states(_fs_state, root=_acroot)
        assert len(d) == 1 and d[0]["state"] == "not_started" and d[0]["ac_total"] == 2, d
        # (b) report: AC-1 pass, AC-2 chưa → active (1/2)
        _rep.write_text("| TC | Result |\n|----|--------|\n| TC-1 | PASS |\n", encoding="utf-8")
        d = derive_feature_states(_fs_state, root=_acroot)
        assert d[0]["state"] == "active" and d[0]["ac_pass"] == 1, d
        # (c) cả 2 AC in-scope pass → passing (AC-3 deferred không tính)
        _rep.write_text("| TC | Result |\n|----|--------|\n| TC-1 | PASS |\n| TC-2 | PASS |\n", encoding="utf-8")
        d = derive_feature_states(_fs_state, root=_acroot)
        assert d[0]["state"] == "passing" and d[0]["ac_pass"] == 2 and d[0]["ac_total"] == 2, d
        # (d) FEAT deferred toàn bộ / no-file
        assert derive_feature_states({"wave": {"id": "wave-001"}, "wave_features": ["FEAT-NOFILE"]},
                                     root=_acroot)[0]["state"] == "no-file"
        # (e) render markdown chứa tiến độ + bảng
        md = render_feature_state_md(_fs_state, root=_acroot)
        assert "1/1 feat in-scope `passing`" in md and "| FEAT-T01 | passing" in md, md
        # (f) features_complete gate (bước 2): passing → pass; active (làm dở) → chặn ship
        assert check_features_complete(_fs_state, root=_acroot)[0] is True, "mọi feat passing → end-wave ok"
        _rep.write_text("| TC | Result |\n|----|--------|\n| TC-1 | PASS |\n", encoding="utf-8")  # AC-1 pass, AC-2 chưa → active
        ok, msg = check_features_complete(_fs_state, root=_acroot)
        assert (not ok) and "FEAT-T01" in msg and "LÀM DỞ" in msg, f"feat active phải chặn end-wave: {msg}"
        assert check_features_complete(_fs_state, {"force": True}, root=_acroot)[0] is True
        # not_started (report rỗng) KHÔNG chặn (manual-AC chưa ghi report — gate khác lo)
        _rep.unlink()
        assert check_features_complete(_fs_state, root=_acroot)[0] is True, "not_started không chặn (tránh chặn oan manual)"
    finally:
        _shutil.rmtree(_acroot, ignore_errors=True)

    # contract_graph_parity: đồ thị contract ↔ MATRIX depends_on (3 nguồn 1 sự thật).
    _cgroot = Path(_tf_hp.mkdtemp(prefix="gates_cg_"))
    try:
        (_cgroot / "harness").mkdir(parents=True, exist_ok=True)
        _api_d = _cgroot / "docs" / "architecture" / "api"
        _api_d.mkdir(parents=True, exist_ok=True)
        _mx = _cgroot / "harness" / "SERVICE-BOUNDARY-MATRIX.json"
        _mx.write_text(json.dumps({"boundaries": [
            {"boundary_id": "scheduling", "kind": "backend", "depends_on": []},
            {"boundary_id": "patient-web", "kind": "web", "depends_on": ["scheduling"]},
        ]}), encoding="utf-8")
        # (a) khớp: api-scheduling consumers có patient-web = cạnh MATRIX → pass
        (_api_d / "api-scheduling.md").write_text(
            '---\nproducer: "scheduling"\nconsumers: ["patient-web"]\n---\n# API\n', encoding="utf-8")
        assert check_contract_graph_parity(root=_cgroot)[0] is True, "đồ thị khớp → pass"
        # (b) contract khai consumer không có cạnh MATRIX → fail
        (_api_d / "api-scheduling.md").write_text(
            '---\nproducer: "scheduling"\nconsumers: ["patient-web", "billing"]\n---\n# API\n', encoding="utf-8")
        ok, msg = check_contract_graph_parity(root=_cgroot)
        assert (not ok) and "billing" in msg, msg
        # (c) cạnh MATRIX không được contract doc nào ghi nhận → fail
        (_api_d / "api-scheduling.md").write_text(
            '---\nproducer: "scheduling"\nconsumers: []\n---\n# API\n', encoding="utf-8")
        ok, msg = check_contract_graph_parity(root=_cgroot)
        assert (not ok) and "depends_on" in msg and "scheduling" in msg, msg
        # (d) INTEG-INT doc cũng ghi nhận được cạnh → pass; force bypass
        _integ_d = _cgroot / "docs" / "architecture" / "integrations"
        _integ_d.mkdir(parents=True, exist_ok=True)
        (_integ_d / "INTEG-INT-patient-web-to-scheduling.md").write_text(
            '---\nconsumer: "patient-web"\nproducer: "scheduling"\nmode: "sync"\n---\n# I\n', encoding="utf-8")
        assert check_contract_graph_parity(root=_cgroot)[0] is True, "INTEG doc ghi nhận cạnh → pass"
        _mx.write_text(json.dumps({"boundaries": []}), encoding="utf-8")
        assert check_contract_graph_parity(root=_cgroot)[0] is True  # MATRIX rỗng → skip
        assert check_contract_graph_parity({"force": True}, root=_cgroot)[0] is True
    finally:
        _shutil.rmtree(_cgroot, ignore_errors=True)

    # api_contract_proof: endpoint khai api doc phải có trong runtime OpenAPI (api-proof.json).
    _aproot = Path(_tf_hp.mkdtemp(prefix="gates_ap_"))
    try:
        (_aproot / "harness").mkdir(parents=True, exist_ok=True)
        (_aproot / "harness" / "SERVICE-BOUNDARY-MATRIX.json").write_text(json.dumps({"boundaries": [
            {"boundary_id": "scheduling", "kind": "backend", "prefix": "demo"}]}), encoding="utf-8")
        _ap_state = {"wave": {"id": "wave-001"}, "wave_boundaries": ["scheduling"]}
        _apd = _aproot / "docs" / "architecture" / "api"
        _apd.mkdir(parents=True, exist_ok=True)
        _apw = _aproot / "tracking" / "wave-001"
        _apw.mkdir(parents=True, exist_ok=True)
        # api doc không tồn tại → skip → pass
        assert check_api_contract_proof(_ap_state, root=_aproot)[0] is True
        (_apd / "api-scheduling.md").write_text(
            "## 3.1\n| Method · Path | `POST /api/v1/appointments` |\n"
            "Happy: `POST /appointments` + headers → 201 (văn xuôi VIẾT TẮT — KHÔNG phải khai báo)\n"
            "## 3.2\n| Method · Path | `GET /api/v1/appointments/{id}` |\n", encoding="utf-8")
        # văn xuôi `POST /appointments` KHÔNG được trích (nếu bị trích → runtime thiếu → false fail)
        assert ("POST", "/appointments") not in _doc_endpoints(_apd / "api-scheduling.md")
        # (a) có api doc + endpoint nhưng thiếu proof → fail
        ok, msg = check_api_contract_proof(_ap_state, root=_aproot)
        assert (not ok) and "api-proof.json" in msg, msg
        # (b) proof đủ endpoint (param name khác vẫn khớp nhờ normalize {}) → pass
        (_apw / "api-proof.json").write_text(json.dumps({"specs": {"scheduling": {
            "source_url": "http://localhost:8081/v3/api-docs",
            "paths": {"/api/v1/appointments": ["GET", "POST"],
                      "/api/v1/appointments/{appointmentId}": ["GET", "PUT"]}}}}), encoding="utf-8")
        assert check_api_contract_proof(_ap_state, root=_aproot)[0] is True, "endpoint đủ → pass"
        # (c) runtime thiếu endpoint đã khai → fail (contract drift)
        (_apw / "api-proof.json").write_text(json.dumps({"specs": {"scheduling": {
            "paths": {"/api/v1/appointments": ["GET"]}}}}), encoding="utf-8")
        ok, msg = check_api_contract_proof(_ap_state, root=_aproot)
        assert (not ok) and "POST /api/v1/appointments" in msg and "drift" in msg, msg
        # (d) fetch error entry → fail nêu springdoc; force bypass
        (_apw / "api-proof.json").write_text(json.dumps({"specs": {"scheduling": {
            "error": "không fetch được OpenAPI"}}}), encoding="utf-8")
        ok, msg = check_api_contract_proof(_ap_state, root=_aproot)
        assert (not ok) and "springdoc" in msg, msg
        assert check_api_contract_proof(_ap_state, {"force": True}, root=_aproot)[0] is True
    finally:
        _shutil.rmtree(_aproot, ignore_errors=True)

    # derive_coverage_pct + all_boundaries_reviewed: số đo từ report thắng số tự khai.
    _cvroot = Path(_tf_hp.mkdtemp(prefix="gates_cv_"))
    try:
        (_cvroot / "harness").mkdir(parents=True, exist_ok=True)
        (_cvroot / "harness" / "SERVICE-BOUNDARY-MATRIX.json").write_text(json.dumps({"boundaries": [
            {"boundary_id": "order", "kind": "backend", "prefix": "demo"},
            {"boundary_id": "web1", "kind": "web", "prefix": "demo"},
        ]}), encoding="utf-8")
        _cv_state = {
            "wave_boundaries": ["order"],
            "project": {"service_prefix": "demo"},
            "review_results": [{"boundary": "order", "kind": "backend", "review_result": "pass", "coverage_pct": 95}],
        }
        _svc = _cvroot / "services" / "demo-order"
        _svc.mkdir(parents=True, exist_ok=True)
        # (a) service đã scaffold nhưng KHÔNG có report → fail dù tự khai 95
        ok, msg = check_all_boundaries_reviewed(_cv_state, root=_cvroot)
        assert (not ok) and "coverage report" in msg, f"scaffold không report phải fail: {msg}"
        # (b) jacoco nói 70% (< BE 80) → fail dù tự khai 95 (đo thắng khai); counter LINE cuối = tổng
        _jx = _svc / "build" / "reports" / "jacoco" / "test"
        _jx.mkdir(parents=True, exist_ok=True)
        (_jx / "jacocoTestReport.xml").write_text(
            '<report><package><counter type="LINE" missed="5" covered="5"/></package>'
            '<counter type="INSTRUCTION" missed="1" covered="9"/>'
            '<counter type="LINE" missed="30" covered="70"/></report>', encoding="utf-8")
        assert derive_coverage_pct("order", _cv_state, _cvroot) == 70.0
        ok, msg = check_all_boundaries_reviewed(_cv_state, root=_cvroot)
        assert (not ok) and "đo từ report" in msg, f"derived 70 < 80 phải fail: {msg}"
        # (c) jacoco 90% → pass kể cả khi tự khai 0 (số đo thắng)
        (_jx / "jacocoTestReport.xml").write_text(
            '<report><counter type="LINE" missed="10" covered="90"/></report>', encoding="utf-8")
        _cv_state["review_results"][0]["coverage_pct"] = 0
        assert check_all_boundaries_reviewed(_cv_state, root=_cvroot)[0] is True, "derived 90 ≥ 80 → pass"
        # (d) web boundary: coverage-summary.json 65% ≥ 60 → pass; lcov parse đúng
        _web = _cvroot / "services" / "demo-web1"
        (_web / "coverage").mkdir(parents=True, exist_ok=True)
        (_web / "coverage" / "coverage-summary.json").write_text(
            json.dumps({"total": {"lines": {"pct": 65.2}}}), encoding="utf-8")
        assert derive_coverage_pct("web1", _cv_state, _cvroot) == 65.2
        (_web / "coverage" / "coverage-summary.json").unlink()
        (_web / "coverage" / "lcov.info").write_text("LF:100\nLH:58\nLF:100\nLH:60\n", encoding="utf-8")
        assert derive_coverage_pct("web1", _cv_state, _cvroot) == 59.0
        # (e) chưa scaffold → None (fallback số khai — hermetic/smoke giữ hành vi cũ)
        assert derive_coverage_pct("ghost", _cv_state, _cvroot) is None
        # (f) force bypass
        _cv_state["review_results"] = []
        assert check_all_boundaries_reviewed(_cv_state, {"force": True}, root=_cvroot)[0] is True
    finally:
        _shutil.rmtree(_cvroot, ignore_errors=True)

    # --- live(): dòng MẪU trong <!-- --> KHÔNG được làm gate xanh -------------
    # Lỗ này hỏng theo kiểu tệ nhất: gate vẫn còn đó, vẫn báo qua, mà đang đếm ví dụ
    # của template chứ không đếm cái người viết. Template nào cũng để dòng mẫu trong
    # comment cho dễ bắt chước, nên nó không phải ca hiếm.
    _sample = (
        "| TC | Feature | AC | Type | Group |\n|---|---|---|---|---|\n"
        "<!-- | TC-001 | FEAT-A-001 | AC-1 | auto | core |  <- dòng mẫu, xoá khi điền -->\n"
    )
    assert _parse_md_table_rows(_sample, ("tc", "feature", "ac")) == [], \
        "dòng mẫu trong <!-- --> vẫn bị đếm là hàng thật"
    assert _parse_md_table_rows(
        _sample + "| TC-002 | FEAT-A-001 | AC-2 | auto | core |\n",
        ("tc", "feature", "ac"))[0]["tc"] == "TC-002", "hàng thật phải còn"
    assert _bc_section3("## 3. Rà\n<!-- - [ ] mẫu -->\n- [x] API\n") == \
        ["- [x] API"], "checkbox mẫu trong comment vẫn bị đếm là nợ"
    assert live("giữ <!-- bỏ --> lại") == "giữ  lại"
    assert live("a\n<!-- cả dòng -->\nb\n") == "a\nb\n", \
        "comment chiếm trọn dòng phải bay CẢ dòng — dòng trắng chen vào reset header bảng"
    print("  ok   live(): dòng mẫu trong <!-- --> không làm gate xanh (3 phép)")

    print("OK: gates.py selftest passed")
    return 0


if __name__ == "__main__":
    import sys
    # `--selftest` khai TƯỜNG MINH (dù chạy selftest là mặc định) để `selftest_all.py` dò
    # thấy — hợp đồng dò là "có chuỗi `--selftest`", không phải "đọc được ý định".
    sys.exit(_print_rules() if "--list" in sys.argv else _selftest())
