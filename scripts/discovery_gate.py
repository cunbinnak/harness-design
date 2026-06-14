"""
discovery_gate.py — Exit gate cho mỗi DISCOVERY sub-wave D0-D3 (cloned từ ZIP discovery-gate.py).

Scope harness: clone tối giản D0-D2 + charter (D3). Bỏ D3.5/D4/D5/D6/D7 (plumbing multi-repo).

Usage:
  py scripts/discovery_gate.py <D-wave>   # D0 | D1 | D2 | D3
  py scripts/discovery_gate.py --all

Exit codes:
  0 — gate pass (đủ artifact để transition sang D{N+1})
  1 — gate fail (artifact missing / dưới minimum count)
  2 — usage error (D-wave invalid)

Strictness: file-exists + minimum-count check (regex), KHÔNG parse YAML sâu (tránh false-positive).
Path harness: docs/discovery/* (ZIP dùng _discovery/*). Root = repo root (parent của scripts/).

Dùng bởi gates.py (kind=discovery_wave): khi /discovery-end <D>, gọi check_gate(D); fail → block transition.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parent.parent
DISC = "docs/discovery"


# ---------- Helpers (port verbatim từ ZIP) ----------

def file_exists(rel: str) -> bool:
    return (REPO_ROOT / rel).exists()


def file_nonempty(rel: str) -> bool:
    p = REPO_ROOT / rel
    return p.exists() and p.stat().st_size > 0


def read(rel: str) -> str:
    p = REPO_ROOT / rel
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="ignore")


def count_lines_matching(rel: str, pattern: str) -> int:
    text = read(rel)
    if not text:
        return 0
    rx = re.compile(pattern, re.MULTILINE)
    return len(rx.findall(text))


def section_nonempty(rel: str, header_pattern: str) -> bool:
    """Section dưới markdown header có content thật (không chỉ placeholder)."""
    text = read(rel)
    if not text:
        return False
    rx = re.compile(rf"^{header_pattern}.*?$(.*?)(?=^##\s|\Z)", re.MULTILINE | re.DOTALL)
    m = rx.search(text)
    if not m:
        return False
    body = m.group(1).strip()
    body = re.sub(r"_[A-Z]+_", "", body)        # _TBD_, _PENDING_, ...
    body = re.sub(r"\{\{[^}]+\}\}", "", body)    # {{placeholder}}
    return len(body.strip()) > 20               # ≥20 chars content thật


def subdirs_with_file(parent: str, filename: str) -> list[str]:
    """Subdir dưới parent/ có chứa filename. Loại _TEMPLATE."""
    p = REPO_ROOT / parent
    if not p.exists():
        return []
    return sorted(
        d.name for d in p.iterdir()
        if d.is_dir() and d.name != "_TEMPLATE" and (d / filename).exists()
    )


def _count_non_placeholder_table_rows(rel: str, section_header_regex: str) -> int:
    """Đếm row table dưới section, loại header/separator/_TBD_."""
    text = read(rel)
    if not text:
        return 0
    m = re.search(rf"^{section_header_regex}.*?$(.*?)(?=^##\s|\Z)", text, re.MULTILINE | re.DOTALL)
    if not m:
        return 0
    count = 0
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:|]+\|?\s*$", line):  # separator
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        non_empty = [c for c in cells if c and c != "_TBD_" and not c.startswith("_") and "{{" not in c]
        if non_empty:
            count += 1
    return count


# ---------- Per-wave gate (port từ ZIP gate_d0/d1/d2; d3 adapt single-repo) ----------

def gate_d0() -> tuple[bool, list[str]]:
    """D0: hypothesis-log.md — vision + problem + ≥3 hypothesis + ≥2 anti-hypothesis."""
    errors: list[str] = []
    rel = f"{DISC}/hypothesis-log.md"
    if not file_nonempty(rel):
        errors.append(f"MISSING: {rel} (cần file + non-empty)")
        return False, errors

    if not section_nonempty(rel, "## 1\\. Vision narrative"):
        errors.append(f"{rel} §1 Vision narrative trống hoặc chỉ placeholder")
    if not section_nonempty(rel, "## 2\\. Problem statement"):
        errors.append(f"{rel} §2 Problem statement trống hoặc chỉ placeholder")

    hypo_count = count_lines_matching(rel, r"^\|\s*H\d+\s*\|")
    if hypo_count < 3:
        errors.append(f"{rel} §3 Hypotheses chỉ có {hypo_count} row (yêu cầu ≥3)")

    text = read(rel)
    m4 = re.search(r"^## 4\..*?$(.*?)(?=^##\s|\Z)", text, re.MULTILINE | re.DOTALL)
    anti_count = 0
    if m4:
        body = m4.group(1)
        anti_count = len([
            l for l in body.splitlines()
            if re.match(r"^\s*[-*]\s+\S", l) or re.match(r"^\s*\d+\.\s+\S", l)
        ])
    if anti_count < 2:
        errors.append(f"{rel} §4 Anti-hypotheses chỉ có {anti_count} item (yêu cầu ≥2)")

    return len(errors) == 0, errors


def gate_d1() -> tuple[bool, list[str]]:
    """D1: persona-pool ≥1 persona + ≥2 anti-persona; capability-map ≥5 capability + ≥1 candidate domain."""
    errors: list[str] = []

    persona = f"{DISC}/persona-pool.md"
    if not file_nonempty(persona):
        errors.append(f"MISSING: {persona}")
    else:
        persona_count = count_lines_matching(persona, r"^##\s+P\d+\s*[—-]")
        if persona_count < 1:
            errors.append(f"{persona} không có persona nào (yêu cầu ≥1 dạng '## P1 — Name')")

        ptext = read(persona)
        m_anti = re.search(r"^##\s+Anti-personas.*?$(.*?)(?=^##\s|\Z)", ptext, re.MULTILINE | re.DOTALL)
        anti_p_count = 0
        if m_anti:
            body = m_anti.group(1)
            anti_p_count = len([
                l for l in body.splitlines()
                if re.match(r"^\s*[-*]\s+\S", l) or re.match(r"^\s*\d+\.\s+\S", l)
            ])
        if anti_p_count < 2:
            errors.append(f"{persona} §Anti-personas chỉ có {anti_p_count} item (yêu cầu ≥2)")

    cap = f"{DISC}/capability-map.md"
    if not file_nonempty(cap):
        errors.append(f"MISSING: {cap}")
    else:
        text = read(cap)
        m = re.search(r"^## 1\..*?$(.*?)^## 2\.", text, re.MULTILINE | re.DOTALL)
        cap_rows = 0
        if m:
            for line in m.group(1).splitlines():
                line = line.strip()
                if line.startswith("|") and not re.match(r"^\|[\s\-:]+\|", line) and "Capability" not in line and "_TBD_" not in line:
                    cap_rows += 1
        if cap_rows < 5:
            errors.append(f"{cap} §1 Persona × Capability chỉ có {cap_rows} capability row (yêu cầu ≥5, không tính header/_TBD_)")

        m3 = re.search(r"^## 3\..*?$(.*?)(?=^##\s|\Z)", text, re.MULTILINE | re.DOTALL)
        domain_rows = 0
        if m3:
            for line in m3.group(1).splitlines():
                line = line.strip()
                if line.startswith("|") and not re.match(r"^\|[\s\-:]+\|", line) and "Domain" not in line and "_TBD_" not in line:
                    domain_rows += 1
        if domain_rows < 1:
            errors.append(f"{cap} §3 Candidate domains chưa có domain nào (yêu cầu ≥1, không tính header/_TBD_)")

    return len(errors) == 0, errors


def gate_d2() -> tuple[bool, list[str]]:
    """D2: ≥1 ES file per candidate domain (D1 §3), mỗi file §1 Events ≥10."""
    errors: list[str] = []

    cap = f"{DISC}/capability-map.md"
    if not file_nonempty(cap):
        errors.append(f"MISSING: {cap} (D1 chưa xong)")
        return False, errors

    text = read(cap)
    m3 = re.search(r"^## 3\..*?$(.*?)(?=^##\s|\Z)", text, re.MULTILINE | re.DOTALL)
    domains: list[str] = []
    if m3:
        for line in m3.group(1).splitlines():
            line = line.strip()
            if line.startswith("|") and not re.match(r"^\|[\s\-:]+\|", line) and "Domain" not in line:
                parts = [p.strip() for p in line.strip("|").split("|")]
                if parts and parts[0] and parts[0] != "_TBD_":
                    name = re.sub(r"[^a-z0-9-]", "-", parts[0].lower()).strip("-")
                    if name:
                        domains.append(name)

    if not domains:
        errors.append(f"{cap} §3 không list candidate domain nào — không xác định được expected ES files")
        return False, errors

    es_dir = REPO_ROOT / DISC / "event-storming"
    es_files = list(es_dir.glob("ES-*.md")) if es_dir.exists() else []
    es_names = {f.stem for f in es_files}

    for domain in domains:
        expected = f"ES-{domain}"
        if expected not in es_names:
            errors.append(f"MISSING: {DISC}/event-storming/{expected}.md (cho domain '{domain}' từ capability-map §3)")
            continue
        es_text = read(f"{DISC}/event-storming/{expected}.md")
        m_ev = re.search(r"^##?\s*1\.\s*Events.*?$(.*?)(?=^##\s|\Z)", es_text, re.MULTILINE | re.DOTALL)
        if m_ev:
            event_count = len([l for l in m_ev.group(1).splitlines() if re.match(r"^\s*[-*\d]+\.?\s+\w", l)])
        else:
            event_count = 0
        if event_count < 10:
            errors.append(f"{DISC}/event-storming/{expected}.md §1 Events chỉ có {event_count} event (yêu cầu ≥10)")

    return len(errors) == 0, errors


def gate_d3() -> tuple[bool, list[str]]:
    """D3 (adapt single-repo): BOUNDARY-MAP ≥1 row + ≥1 CHARTER Mission + derive PROJECT.md.

    Bỏ check ADR-D3/SYSTEM-TOPOLOGY (stack decision thuộc technical-design/DESIGN sau).
    D3 derive PROJECT.md (PRD) → DOMAIN_AUTHORING. **KHÔNG sinh FEAT** ở đây: DOMAIN sở hữu
    product, author THẲNG vào docs/architecture/{epics,feat,business-rules}/ (single-repo, KHÔNG translate).
    """
    errors: list[str] = []

    bmap = f"{DISC}/BOUNDARY-MAP.md"
    if not file_nonempty(bmap):
        errors.append(f"MISSING: {bmap}")
    else:
        total_real_rows = 0
        for section in (r"## 1\.", r"## 2\.", r"## 3\."):
            total_real_rows += _count_non_placeholder_table_rows(bmap, section)
        if total_real_rows < 1:
            errors.append(f"{bmap} không có row non-placeholder nào (yêu cầu ≥1 boundary). Hiện chỉ _TBD_.")

    # ≥1 target có CHARTER.md (non-_TEMPLATE) + §1 Mission có content
    boundaries = subdirs_with_file(f"{DISC}/boundaries", "CHARTER.md")
    if not boundaries:
        errors.append(f"Chưa có target nào với CHARTER.md trong {DISC}/boundaries/<x>/ (yêu cầu ≥1 non-_TEMPLATE)")
    else:
        for b in boundaries:
            charter = f"{DISC}/boundaries/{b}/CHARTER.md"
            if not section_nonempty(charter, "## 1\\. Mission"):
                errors.append(f"{charter} §1 Mission trống hoặc chỉ placeholder")

    # D3 derive PROJECT.md (PRD) → bridge sang DOMAIN authoring
    if not file_nonempty("docs/architecture/PROJECT.md"):
        errors.append("MISSING: docs/architecture/PROJECT.md (D3 charter-author derive PRD từ hypothesis+capability+ES)")

    return len(errors) == 0, errors


# ---------- Dispatch ----------

GATES: dict[str, Callable[[], tuple[bool, list[str]]]] = {
    "D0": gate_d0,
    "D1": gate_d1,
    "D2": gate_d2,
    "D3": gate_d3,
}

# Map stage harness → gate của stage đang rời (outgoing).
STAGE_TO_GATE = {
    "DISC_D0": "D0",
    "DISC_D1": "D1",
    "DISC_D2": "D2",
    "DISC_D3": "D3",
}


def check_gate(wave: str) -> tuple[bool, list[str]]:
    """Run gate cho wave. Trả (passed, errors). Dùng bởi gates.py."""
    wave = wave.upper()
    if wave not in GATES:
        return False, [f"unknown wave {wave!r}. Valid: {sorted(GATES.keys())}"]
    return GATES[wave]()


def _print_result(wave: str, passed: bool, errors: list[str]) -> int:
    if passed:
        print(f"OK: {wave} exit gate PASS")
        return 0
    print(f"FAIL: {wave} exit gate:", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    print(
        f"\nResolution: produce artifact thiếu (xem plan §Flow). "
        f"Hoặc override: state.py complete discovery-end với --force (ghi tracking/decisions.md).",
        file=sys.stderr,
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(prog="discovery_gate.py", description="DISCOVERY exit gate D0-D3")
    ap.add_argument("wave", nargs="?", help="D0 | D1 | D2 | D3")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args(argv)

    if args.all:
        rc = 0
        for w in ("D0", "D1", "D2", "D3"):
            passed, errors = check_gate(w)
            if _print_result(w, passed, errors) != 0:
                rc = 1
        return rc
    if not args.wave:
        ap.print_help(sys.stderr)
        return 2
    passed, errors = check_gate(args.wave)
    if args.wave.upper() not in GATES:
        print(f"ERROR: unknown wave {args.wave!r}", file=sys.stderr)
        return 2
    return _print_result(args.wave.upper(), passed, errors)


if __name__ == "__main__":
    sys.exit(main())
