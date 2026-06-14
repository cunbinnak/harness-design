"""
planning_lint.py — PLANNING-stage lint cho harness single-repo.

Clone tối giản từ ZIP {{PROJECT-CODE}}-ADLC-SPECS/scripts/planning-lint.py + enforce
_shared/definitions/planning-rules.md (§1-§4), adapt single-repo:
  - REPO_ROOT = parent của scripts/ (KHÔNG dùng repo-root-marker ADLC.md).
  - Parse docs/architecture/{epics,feat,business-rules,adr}/*.md (bỏ TEMPLATE.*).
  - Dùng field THẬT của harness template (KHÔNG field ZIP):
      EPIC: id + feature_refs[] (≥2)
      FEAT: id + epic_ref + feat_type (user_facing|platform)
      BR:   id + related_features[] (≥1)
      ADR:  adr_id + section "Alternatives considered" có ≥2 alternative (table row)
  - KHÔNG cross-repo / SPECS hub / DISCOVERY sibling (plumbing multi-repo — bỏ).
  - GIỮ referential-integrity + dependency-cycle (single-repo VẪN cần — đây KHÔNG phải
    plumbing): ref epic↔feat↔BR phải resolve về file thật; FEAT-id trong MATRIX phải có
    backing FEAT-*.md; MATRIX depends_on không được tạo chu trình / trỏ boundary không tồn tại.
    (Lúc trước gán nhầm 2 check này là "multi-repo → bỏ"; audit vs ZIP cho thấy chúng
    là planning-quality thuần single-repo — xem run_plan_integrity.)

Style: pure check function trả (ok: bool, errors: list[str]) — KHÔNG side effect,
KHÔNG mutate STATE, KHÔNG ghi file. CLI in lỗi + exit 0/1.

Fallback no-PyYAML: parse frontmatter bằng regex (như discovery_gate.py) — KHÔNG
phụ thuộc PyYAML.

Usage:
  py scripts/planning_lint.py          # lint docs/architecture/ → exit 0 (pass) / 1 (fail)
  py scripts/planning_lint.py --selftest

Dùng bởi gates.py (kind=planning_lint): wire vào GATE_RULES['domain-end'] (epic/feat/BR)
+ optionally GATE_RULES['plan']. Force-bypassable: evidence {"force":true} → gate trả ok
(audit ghi tracking/decisions.md) — xem gates.py check_planning_lint.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARCH = "docs/architecture"

# Min thresholds (planning-rules §1.1 EP ≥2 FEAT; §1.4 BR ≥1 FEAT; §1.5 ADR ≥2 option).
MIN_FEATURE_REFS_PER_EPIC = 2
MIN_RELATED_FEATS_PER_BR = 1
MIN_ADR_ALTERNATIVES = 2
FEAT_TYPE_ENUM = ("user_facing", "platform")


# ---------- Frontmatter parser (no PyYAML dependency) ----------

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict[str, object]:
    """Parse YAML frontmatter tối giản (scalar + list-inline [a, b] + list-block '- x').

    Đủ cho field harness template. KHÔNG cần PyYAML. Strip inline comment (# ...),
    quote ('/"), placeholder {{...}} giữ nguyên (caller xử lý).
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    body = m.group(1)
    out: dict[str, object] = {}
    cur_list: list[str] | None = None
    for line in body.splitlines():
        raw = line
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        # list item dưới key hiện tại
        if cur_list is not None and raw.lstrip().startswith("- "):
            cur_list.append(_clean_scalar(raw.lstrip()[2:]))
            continue
        cur_list = None
        if ":" in raw and not raw.startswith(" "):
            key, _, val = raw.partition(":")
            key = key.strip()
            val = val.split("#", 1)[0].strip()  # strip inline comment
            if not val:
                cur_list = []
                out[key] = cur_list
            elif val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                out[key] = [] if not inner else [_clean_scalar(x) for x in inner.split(",")]
            else:
                out[key] = _clean_scalar(val)
    return out


def _clean_scalar(val: str) -> str:
    return val.strip().strip('"').strip("'").strip()


# ---------- Artifact iteration ----------

def _iter_artifacts(folder: str, prefix: str) -> list[Path]:
    """File .md trong folder có stem bắt đầu bằng prefix; bỏ TEMPLATE.*."""
    d = REPO_ROOT / folder
    if not d.is_dir():
        return []
    out: list[Path] = []
    for p in sorted(d.iterdir()):
        if not p.is_file() or not p.name.endswith(".md"):
            continue
        if p.name.startswith("TEMPLATE.") or p.name.startswith("_TEMPLATE"):
            continue
        if p.stem.startswith(prefix):
            out.append(p)
    return out


def _is_placeholder(val: object) -> bool:
    """True nếu giá trị còn là placeholder template ({{...}}) hoặc rỗng."""
    if not val:
        return True
    if isinstance(val, str):
        return "{{" in val or not val.strip()
    return False


def _real_refs(val: object) -> list[str]:
    """Lọc list ref bỏ placeholder/empty. Chấp nhận scalar (wrap thành list)."""
    if val is None:
        return []
    items = val if isinstance(val, list) else [val]
    return [x for x in items if isinstance(x, str) and x.strip() and "{{" not in x]


# ---------- Per-kind checks (CLEAR-CUT rules only) ----------

def _check_epics(errors: list[str]) -> None:
    """EPIC: feature_refs ≥2 (planning-rules §1.1 cohesion: epic <2 feature → merge)."""
    for fp in _iter_artifacts(f"{ARCH}/epics", "EP-"):
        fm = parse_frontmatter(fp.read_text(encoding="utf-8", errors="ignore"))
        refs = _real_refs(fm.get("feature_refs"))
        if len(refs) < MIN_FEATURE_REFS_PER_EPIC:
            errors.append(
                f"{fp.name}: feature_refs có {len(refs)} FEAT (cần ≥{MIN_FEATURE_REFS_PER_EPIC}) "
                f"— epic <2 feature thì merge (planning-rules §1.1)."
            )


def _check_feats(errors: list[str]) -> None:
    """FEAT: có epic_ref (non-placeholder) + feat_type ∈ {user_facing, platform}.

    (planning-rules §1.2 / §3.2: missing parent_epic / feat_type sai enum = ERROR.)
    """
    for fp in _iter_artifacts(f"{ARCH}/feat", "FEAT-"):
        fm = parse_frontmatter(fp.read_text(encoding="utf-8", errors="ignore"))
        if _is_placeholder(fm.get("epic_ref")):
            errors.append(f"{fp.name}: thiếu epic_ref (FEAT phải gắn 1 epic — planning-rules §1.2).")
        ft = fm.get("feat_type")
        if _is_placeholder(ft):
            errors.append(f"{fp.name}: thiếu feat_type (cần user_facing | platform — planning-rules §1.2).")
        elif isinstance(ft, str) and ft not in FEAT_TYPE_ENUM:
            errors.append(
                f"{fp.name}: feat_type={ft!r} không hợp lệ — cần ∈ {list(FEAT_TYPE_ENUM)} (planning-rules §3.2)."
            )


def _check_business_rules(errors: list[str]) -> None:
    """BR: related_features ≥1 (planning-rules §1.4: rule chỉ 1 FEAT → đáng lẽ là AC)."""
    for fp in _iter_artifacts(f"{ARCH}/business-rules", "BR-"):
        fm = parse_frontmatter(fp.read_text(encoding="utf-8", errors="ignore"))
        refs = _real_refs(fm.get("related_features"))
        if len(refs) < MIN_RELATED_FEATS_PER_BR:
            errors.append(
                f"{fp.name}: related_features có {len(refs)} FEAT (cần ≥{MIN_RELATED_FEATS_PER_BR}) "
                f"— BR phải cross-link FEAT (planning-rules §1.4)."
            )


def _count_adr_alternatives(text: str) -> int:
    """Đếm alternative trong section 'Alternatives considered' của ADR (harness template).

    Template dùng bảng: | Alternative | Pros | Cons | Reason not chosen |. Đếm data row
    (bỏ header + separator + row toàn placeholder {{...}}). Fallback: '### Option N' list.
    """
    m = re.search(
        r"^##\s+Alternatives\s+considered\b(.*?)(?=^##\s|\Z)",
        text, re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    if not m:
        return 0
    section = m.group(1)
    rows = 0
    header_seen = False
    for line in section.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:|]+\|?\s*$", s):  # separator |---|
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        low = [c.lower() for c in cells]
        if not header_seen:
            # header row = chứa 'alternative' (hoặc 'option')
            if "alternative" in low or "option" in low:
                header_seen = True
            continue
        # data row: cell đầu non-empty + không phải placeholder {{...}}
        first = cells[0] if cells else ""
        if first and "{{" not in first:
            rows += 1
    if rows == 0:
        # Fallback: '### Option N' / '### Alternative N' subsection
        rows = len(re.findall(
            r"^###\s+(Option|Alternative|Lựa\s+chọn)\b", section, re.MULTILINE | re.IGNORECASE
        ))
    return rows


def _check_adrs(errors: list[str]) -> None:
    """ADR: section 'Alternatives considered' có ≥2 alternative (planning-rules §1.5/§3.5)."""
    for fp in _iter_artifacts(f"{ARCH}/adr", "ADR-"):
        text = fp.read_text(encoding="utf-8", errors="ignore")
        n = _count_adr_alternatives(text)
        if n < MIN_ADR_ALTERNATIVES:
            errors.append(
                f"{fp.name}: section 'Alternatives considered' có {n} alternative "
                f"(cần ≥{MIN_ADR_ALTERNATIVES} — planning-rules §1.5)."
            )


# ---------- Referential integrity (single-repo planning quality) ----------

def _ref_has_file(folder: str, ref_id: str) -> bool:
    """True nếu ref_id (vd 'FEAT-fnb-001') có file backing folder/<ref_id>.md."""
    return (REPO_ROOT / folder / f"{ref_id}.md").is_file()


def _check_persona_ref(errors: list[str], fname: str, val: object, field: str) -> None:
    """Scalar persona ref (outcome_persona/target_persona) -> PERSONA-*.md phải tồn tại (file-id).

    THỐNG NHẤT: mọi persona ref dùng file-id `PERSONA-<prefix>-NNN` (file-backed, enforce được),
    KHÔNG dùng P-id pool (P1..). P-id chỉ ở persona-pool D1; PERSONA-*.md elaborate + persona_pool_ref link ngược.
    """
    if isinstance(val, str) and not _is_placeholder(val) and not _ref_has_file(f"{ARCH}/personas", val):
        errors.append(f"{fname}: {field}={val!r} nhưng không có docs/architecture/personas/{val}.md (dùng file-id PERSONA-*, không dùng P-id pool).")


def _check_ref_integrity(errors: list[str]) -> None:
    """Mọi ref epic↔feat↔BR↔journey↔persona phải resolve về file THẬT (no dangling/phantom id).

    Single-repo planning quality (ZIP planning-lint --completeness). Chỉ check ref đã
    non-placeholder (_real_refs lọc {{...}}). Catch: epic.feature_refs trỏ FEAT không có file;
    FEAT.epic_ref/business_rule_refs/journey_refs trỏ EP/BR/JOURNEY không có file; BR.related_features/
    related_journeys trỏ FEAT/JOURNEY ma; JOURNEY.persona_refs trỏ PERSONA không có file;
    PERSONA.persona_pool_ref trỏ file pool không tồn tại. Backlink (FEAT.journey_refs/BR.related_journeys)
    rỗng = ok — nhưng KHI điền thì PHẢI trỏ journey thật → 2 chiều mới ĐÁNG TIN (không drift)."""
    for fp in _iter_artifacts(f"{ARCH}/epics", "EP-"):
        fm = parse_frontmatter(fp.read_text(encoding="utf-8", errors="ignore"))
        for ref in _real_refs(fm.get("feature_refs")):
            if not _ref_has_file(f"{ARCH}/feat", ref):
                errors.append(f"{fp.name}: feature_refs trỏ {ref!r} nhưng không có docs/architecture/feat/{ref}.md (dangling ref).")
        _check_persona_ref(errors, fp.name, fm.get("target_persona"), "target_persona")

    for fp in _iter_artifacts(f"{ARCH}/feat", "FEAT-"):
        fm = parse_frontmatter(fp.read_text(encoding="utf-8", errors="ignore"))
        epic_ref = fm.get("epic_ref")
        if not _is_placeholder(epic_ref) and not _ref_has_file(f"{ARCH}/epics", str(epic_ref)):
            errors.append(f"{fp.name}: epic_ref={epic_ref!r} nhưng không có docs/architecture/epics/{epic_ref}.md (dangling ref).")
        for ref in _real_refs(fm.get("business_rule_refs")):
            if not _ref_has_file(f"{ARCH}/business-rules", ref):
                errors.append(f"{fp.name}: business_rule_refs trỏ {ref!r} nhưng không có docs/architecture/business-rules/{ref}.md (dangling ref).")
        # persona refs THỐNG NHẤT về file-id PERSONA-*.md (KHÔNG dùng P-id pool — file-backed, enforce được)
        for ref in _real_refs(fm.get("persona_refs")):
            if not _ref_has_file(f"{ARCH}/personas", ref):
                errors.append(f"{fp.name}: persona_refs trỏ {ref!r} nhưng không có docs/architecture/personas/{ref}.md (dùng file-id PERSONA-*, không dùng P-id pool).")
        _check_persona_ref(errors, fp.name, fm.get("outcome_persona"), "outcome_persona")
        # journey_refs (backlink FEAT->journey) — enforce nếu điền (rỗng = ok), để 2 chiều ĐÁNG TIN
        for ref in _real_refs(fm.get("journey_refs")):
            if not _ref_has_file(f"{ARCH}/journeys", ref):
                errors.append(f"{fp.name}: journey_refs trỏ {ref!r} nhưng không có docs/architecture/journeys/{ref}.md (dangling ref).")

    for fp in _iter_artifacts(f"{ARCH}/business-rules", "BR-"):
        fm = parse_frontmatter(fp.read_text(encoding="utf-8", errors="ignore"))
        for ref in _real_refs(fm.get("related_features")):
            if not _ref_has_file(f"{ARCH}/feat", ref):
                errors.append(f"{fp.name}: related_features trỏ {ref!r} nhưng không có docs/architecture/feat/{ref}.md (dangling ref).")
        for ref in _real_refs(fm.get("related_journeys")):
            if not _ref_has_file(f"{ARCH}/journeys", ref):
                errors.append(f"{fp.name}: related_journeys trỏ {ref!r} nhưng không có docs/architecture/journeys/{ref}.md (dangling ref).")

    # JOURNEY.persona_refs -> PERSONA-*.md tồn tại (file-backed)
    for fp in _iter_artifacts(f"{ARCH}/journeys", "JOURNEY-"):
        fm = parse_frontmatter(fp.read_text(encoding="utf-8", errors="ignore"))
        for ref in _real_refs(fm.get("persona_refs")):
            if not _ref_has_file(f"{ARCH}/personas", ref):
                errors.append(f"{fp.name}: persona_refs trỏ {ref!r} nhưng không có docs/architecture/personas/{ref}.md (dangling ref).")

    # PERSONA.persona_pool_ref -> phần file (trước '#') tồn tại (anchor fragile, không ép)
    for fp in _iter_artifacts(f"{ARCH}/personas", "PERSONA-"):
        fm = parse_frontmatter(fp.read_text(encoding="utf-8", errors="ignore"))
        ppr = fm.get("persona_pool_ref")
        if isinstance(ppr, str) and not _is_placeholder(ppr):
            path_part = ppr.split("#", 1)[0].strip()
            if path_part and not (REPO_ROOT / path_part).is_file():
                errors.append(f"{fp.name}: persona_pool_ref trỏ file {path_part!r} nhưng không tồn tại (dangling ref).")


# ---------- Plan-stage integrity (MATRIX features backing + dep cycle) ----------

def _load_matrix_boundaries(root: Path) -> list[dict]:
    import json
    mf = root / "harness" / "SERVICE-BOUNDARY-MATRIX.json"
    if not mf.is_file():
        return []
    try:
        data = json.loads(mf.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return []
    return data.get("boundaries", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])


def _detect_cycle(graph: dict[str, list[str]]) -> list[str]:
    """DFS 3-color. Trả 1 chu trình (list node) nếu có, else []."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in graph}
    stack: list[str] = []

    def dfs(n: str) -> list[str]:
        color[n] = GRAY
        stack.append(n)
        for m in graph.get(n, []):
            if m not in color:
                continue
            if color[m] == GRAY:
                return stack[stack.index(m):] + [m]
            if color[m] == WHITE:
                c = dfs(m)
                if c:
                    return c
        stack.pop()
        color[n] = BLACK
        return []

    for n in graph:
        if color[n] == WHITE:
            c = dfs(n)
            if c:
                return c
    return []


def run_plan_integrity(root: Path | None = None) -> tuple[bool, list[str]]:
    """PLAN-stage referential integrity (single-repo). Trả (ok, errors).

    1. Mọi FEAT-id trong MATRIX `features[]` phải có backing docs/architecture/feat/<id>.md
       (catch phantom FEAT-id planner bịa khi DOMAIN chưa author đủ — bug e2e thật).
    2. MATRIX depends_on: target phải là boundary tồn tại + không tạo chu trình.
    """
    global REPO_ROOT
    if root is not None:
        REPO_ROOT = root
    errors: list[str] = []
    boundaries = _load_matrix_boundaries(REPO_ROOT)
    if not boundaries:
        return True, []  # no MATRIX yet → nothing to check (gate file_exists lo việc tồn tại)

    ids = {b.get("boundary_id") for b in boundaries if b.get("boundary_id")}
    graph: dict[str, list[str]] = {}
    for b in boundaries:
        bid = b.get("boundary_id")
        if not bid:
            continue
        graph[bid] = [d for d in (b.get("depends_on") or []) if isinstance(d, str)]
        # 1. FEAT-id backing
        for fid in (b.get("features") or []):
            if isinstance(fid, str) and fid.strip() and "{{" not in fid:
                if not _ref_has_file(f"{ARCH}/feat", fid):
                    errors.append(
                        f"MATRIX boundary {bid!r}: features liệt kê {fid!r} nhưng không có "
                        f"docs/architecture/feat/{fid}.md (FEAT-id ma — DOMAIN phải author FEAT thật, không bịa id)."
                    )
        # 2. depends_on target tồn tại
        for dep in graph[bid]:
            if dep not in ids:
                errors.append(f"MATRIX boundary {bid!r}: depends_on {dep!r} không phải boundary nào trong MATRIX.")

    cycle = _detect_cycle(graph)
    if cycle:
        errors.append("MATRIX depends_on có chu trình: " + " -> ".join(cycle))

    return len(errors) == 0, errors


# ---------- Public API ----------

def run_lint(root: Path | None = None) -> tuple[bool, list[str]]:
    """Lint docs/architecture/ theo planning-rules CLEAR-CUT. Trả (ok, errors)."""
    global REPO_ROOT
    if root is not None:
        REPO_ROOT = root
    errors: list[str] = []
    _check_epics(errors)
    _check_feats(errors)
    _check_business_rules(errors)
    _check_adrs(errors)
    _check_ref_integrity(errors)
    return len(errors) == 0, errors


# ---------- CLI ----------

def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    if "--selftest" in argv:
        return _selftest()

    ok, errors = run_lint()
    if ok:
        print("OK: planning-lint PASS (epic feature_refs/ feat epic_ref+feat_type/ BR related_features/ ADR alternatives)")
        return 0
    print("FAIL: planning-lint:", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    print(
        "\nResolution: sửa artifact thiếu field (xem planning-rules §1-§4). "
        "Hoặc override: /domain-end (hay /plan) với --force (ghi tracking/decisions.md).",
        file=sys.stderr,
    )
    return 1


# ---------- Inline self-test (run: py scripts/planning_lint.py --selftest) ----------

def _selftest() -> int:
    import tempfile

    # frontmatter parser
    fm = parse_frontmatter('---\nid: "EP-X-001"\nfeature_refs: ["FEAT-X-001", "FEAT-X-002"]\n---\nbody\n')
    assert fm["id"] == "EP-X-001", fm
    assert fm["feature_refs"] == ["FEAT-X-001", "FEAT-X-002"], fm
    fm2 = parse_frontmatter("---\nfeat_type: user_facing   # comment\nepic_ref: EP-X-001\n---\n")
    assert fm2["feat_type"] == "user_facing", fm2
    assert fm2["epic_ref"] == "EP-X-001", fm2
    # list-block form
    fm3 = parse_frontmatter("---\nrelated_features:\n  - FEAT-X-001\n  - FEAT-X-002\n---\n")
    assert fm3["related_features"] == ["FEAT-X-001", "FEAT-X-002"], fm3

    # _real_refs strips placeholder
    assert _real_refs(["FEAT-X-001", "FEAT-{{PREFIX}}-{{NNN}}"]) == ["FEAT-X-001"]
    assert _real_refs("FEAT-X-001") == ["FEAT-X-001"]
    assert _real_refs([]) == []
    assert _is_placeholder("{{PREFIX}}") is True
    assert _is_placeholder("user_facing") is False

    # ADR alternative counter (harness table form)
    adr_ok = (
        "## Alternatives considered\n\n"
        "| Alternative | Pros | Cons | Reason not chosen |\n"
        "|---|---|---|---|\n"
        "| Option-A | a | b | x |\n"
        "| Option-B | c | d | y |\n"
        "| Chosen | e | f | CHOSEN |\n\n"
        "## Consequences\n"
    )
    assert _count_adr_alternatives(adr_ok) == 3, _count_adr_alternatives(adr_ok)
    adr_placeholder = (
        "## Alternatives considered\n\n"
        "| Alternative | Pros | Cons | Reason not chosen |\n"
        "|---|---|---|---|\n"
        "| {{Option-A}} | {{...}} | {{...}} | {{reason}} |\n"
        "| {{Chosen}} | {{...}} | {{...}} | **CHOSEN** |\n"
    )
    assert _count_adr_alternatives(adr_placeholder) == 0, _count_adr_alternatives(adr_placeholder)
    assert _count_adr_alternatives("## Context\nno alternatives here\n") == 0

    # End-to-end: seed temp repo, verify pass + fail cases
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ARCH / "epics").mkdir(parents=True)
        (root / ARCH / "feat").mkdir(parents=True)
        (root / ARCH / "business-rules").mkdir(parents=True)
        (root / ARCH / "adr").mkdir(parents=True)
        # valid set
        (root / ARCH / "epics" / "EP-X-001.md").write_text(
            '---\nid: "EP-X-001"\nfeature_refs: ["FEAT-X-001", "FEAT-X-002"]\n---\n# Epic\n',
            encoding="utf-8")
        (root / ARCH / "feat" / "FEAT-X-001.md").write_text(
            '---\nid: "FEAT-X-001"\nepic_ref: "EP-X-001"\nfeat_type: "user_facing"\n---\n# Feat\n',
            encoding="utf-8")
        # FEAT-X-002 phải tồn tại (EP-X-001.feature_refs trỏ tới — ref integrity)
        (root / ARCH / "feat" / "FEAT-X-002.md").write_text(
            '---\nid: "FEAT-X-002"\nepic_ref: "EP-X-001"\nfeat_type: "user_facing"\n---\n# Feat\n',
            encoding="utf-8")
        (root / ARCH / "business-rules" / "BR-X-001.md").write_text(
            '---\nid: "BR-X-001"\nrelated_features: ["FEAT-X-001"]\n---\n# BR\n',
            encoding="utf-8")
        (root / ARCH / "adr" / "ADR-X-001.md").write_text("# ADR\n" + adr_ok, encoding="utf-8")
        # TEMPLATE phải bị bỏ qua (không lint placeholder)
        (root / ARCH / "epics" / "TEMPLATE.epic.md").write_text(
            '---\nid: "EP-{{PREFIX}}-{{NNN}}"\nfeature_refs: ["FEAT-{{PREFIX}}-{{NNN}}"]\n---\n',
            encoding="utf-8")
        ok, errs = run_lint(root)
        assert ok, f"valid set should pass, got {errs}"

        # ref-integrity: epic trỏ FEAT không có file → dangling error
        (root / ARCH / "epics" / "EP-X-DANGLE.md").write_text(
            '---\nid: "EP-X-DANGLE"\nfeature_refs: ["FEAT-X-001", "FEAT-X-404"]\n---\n', encoding="utf-8")
        okd, errsd = run_lint(root)
        blobd = " ".join(errsd)
        assert not okd and "FEAT-X-404" in blobd and "dangling" in blobd, errsd
        (root / ARCH / "epics" / "EP-X-DANGLE.md").unlink()  # restore valid set
        assert run_lint(root)[0], "valid set should pass again after removing dangling epic"

        # invalid: epic 1 feature_ref, feat sai feat_type, BR 0 related, ADR thiếu alt
        (root / ARCH / "epics" / "EP-X-002.md").write_text(
            '---\nid: "EP-X-002"\nfeature_refs: ["FEAT-X-009"]\n---\n', encoding="utf-8")
        (root / ARCH / "feat" / "FEAT-X-002.md").write_text(
            '---\nid: "FEAT-X-002"\nepic_ref: "EP-X-001"\nfeat_type: "backend-only"\n---\n', encoding="utf-8")
        (root / ARCH / "business-rules" / "BR-X-002.md").write_text(
            '---\nid: "BR-X-002"\nrelated_features: []\n---\n', encoding="utf-8")
        (root / ARCH / "adr" / "ADR-X-002.md").write_text(
            "# ADR\n## Alternatives considered\nNo table.\n## Consequences\n", encoding="utf-8")
        ok2, errs2 = run_lint(root)
        assert not ok2, "invalid set should fail"
        blob = " ".join(errs2)
        assert "EP-X-002.md" in blob and "feature_refs" in blob, errs2
        assert "FEAT-X-002.md" in blob and "feat_type" in blob, errs2
        assert "BR-X-002.md" in blob and "related_features" in blob, errs2
        assert "ADR-X-002.md" in blob and "Alternatives" in blob, errs2

    # plan-integrity: MATRIX features backing + depends_on cycle/existence
    import json as _json
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ARCH / "feat").mkdir(parents=True)
        (root / "harness").mkdir(parents=True)
        (root / ARCH / "feat" / "FEAT-X-001.md").write_text("# F\n", encoding="utf-8")
        # valid: feature có file, depends_on acyclic + target tồn tại
        (root / "harness" / "SERVICE-BOUNDARY-MATRIX.json").write_text(_json.dumps({"boundaries": [
            {"boundary_id": "a", "kind": "backend", "features": ["FEAT-X-001"], "depends_on": []},
            {"boundary_id": "b", "kind": "backend", "features": [], "depends_on": ["a"]},
        ]}), encoding="utf-8")
        okp, errsp = run_plan_integrity(root)
        assert okp, f"valid MATRIX should pass plan-integrity, got {errsp}"
        # invalid: phantom FEAT-id + cycle + dangling depends_on
        (root / "harness" / "SERVICE-BOUNDARY-MATRIX.json").write_text(_json.dumps({"boundaries": [
            {"boundary_id": "a", "kind": "backend", "features": ["FEAT-X-PHANTOM"], "depends_on": ["b"]},
            {"boundary_id": "b", "kind": "backend", "features": [], "depends_on": ["a", "ghost"]},
        ]}), encoding="utf-8")
        okp2, errsp2 = run_plan_integrity(root)
        blobp = " ".join(errsp2)
        assert not okp2, "invalid MATRIX should fail plan-integrity"
        assert "FEAT-X-PHANTOM" in blobp, errsp2
        assert "chu trình" in blobp, errsp2
        assert "ghost" in blobp, errsp2
        # no MATRIX → vacuously ok
        (root / "harness" / "SERVICE-BOUNDARY-MATRIX.json").unlink()
        assert run_plan_integrity(root) == (True, []), "no MATRIX → ok"

    # journey/persona ref-integrity
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ARCH / "journeys").mkdir(parents=True)
        (root / ARCH / "personas").mkdir(parents=True)
        (root / ARCH / "feat").mkdir(parents=True)
        (root / ARCH / "epics").mkdir(parents=True)
        (root / "docs" / "discovery").mkdir(parents=True)
        (root / "docs" / "discovery" / "persona-pool.md").write_text("# pool\n## P1 — x\n", encoding="utf-8")
        (root / ARCH / "personas" / "PERSONA-Z-001.md").write_text(
            '---\nid: "PERSONA-Z-001"\npersona_pool_ref: "docs/discovery/persona-pool.md#p1-x"\n---\n# P\n', encoding="utf-8")
        (root / ARCH / "journeys" / "JOURNEY-Z-001.md").write_text(
            '---\nid: "JOURNEY-Z-001"\npersona_refs: ["PERSONA-Z-001"]\n---\n# J\n', encoding="utf-8")
        assert run_lint(root)[0], f"valid journey/persona should pass: {run_lint(root)[1]}"
        # dangling: journey->missing persona; FEAT.journey_refs->missing journey; persona_pool_ref->missing file
        (root / ARCH / "epics" / "EP-Z-001.md").write_text(
            '---\nid: "EP-Z-001"\nfeature_refs: ["FEAT-Z-001", "FEAT-Z-002"]\n---\n', encoding="utf-8")
        (root / ARCH / "feat" / "FEAT-Z-001.md").write_text(
            '---\nid: "FEAT-Z-001"\nepic_ref: "EP-Z-001"\nfeat_type: "user_facing"\n'
            'journey_refs: ["JOURNEY-Z-404"]\npersona_refs: ["PERSONA-Z-405"]\noutcome_persona: "PERSONA-Z-406"\n---\n',
            encoding="utf-8")
        (root / ARCH / "feat" / "FEAT-Z-002.md").write_text(
            '---\nid: "FEAT-Z-002"\nepic_ref: "EP-Z-001"\nfeat_type: "user_facing"\n---\n', encoding="utf-8")
        (root / ARCH / "journeys" / "JOURNEY-Z-002.md").write_text(
            '---\nid: "JOURNEY-Z-002"\npersona_refs: ["PERSONA-Z-404"]\n---\n', encoding="utf-8")
        (root / ARCH / "personas" / "PERSONA-Z-002.md").write_text(
            '---\nid: "PERSONA-Z-002"\npersona_pool_ref: "docs/discovery/MISSING.md#x"\n---\n', encoding="utf-8")
        okj, errsj = run_lint(root)
        blobj = " ".join(errsj)
        assert not okj, "dangling journey/persona refs should fail"
        assert "JOURNEY-Z-404" in blobj and "PERSONA-Z-404" in blobj and "MISSING.md" in blobj, errsj
        # persona file-id refs (FEAT.persona_refs / outcome_persona) cũng phải resolve
        assert "PERSONA-Z-405" in blobj and "PERSONA-Z-406" in blobj, errsj

    # restore REPO_ROOT (run_lint mutated global khi truyền root)
    global REPO_ROOT
    REPO_ROOT = Path(__file__).resolve().parent.parent

    print("OK: planning_lint.py selftest passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
