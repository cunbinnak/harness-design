"""
approve_document.py — stamp trạng thái duyệt vào frontmatter doc DESIGN/PLAN khi /approve-document.

Trước đây /approve-document chỉ set `approved: true` vào STATE.json — frontmatter `status:` của
từng doc là field trang trí không ai flip (doc duyệt rồi vẫn hiện DRAFT). Script này máy-hóa:

  - docs/architecture/{adr,hld,data-model,ux,integrations}/*.md  → status: APPROVED
  - docs/architecture/{api,events}/*.md (contract)               → status: ACTIVE
    (lifecycle contract DRAFT|ACTIVE|DEPRECATED — ACTIVE = đã duyệt để build theo; DEPRECATED giữ nguyên)

KHÔNG đụng: docs/domain (ký qua domain_approve.py) · eng product epics/feat/BR/journeys/personas
(lifecycle TRANSLATED→ENRICHED riêng + opt-out deferred/dropped của plan_integrity) · docs/plans
(PLANNED|IN_PROGRESS|COMPLETED là lifecycle wave, PLANNED sau approve là đúng nghĩa) · TEMPLATE.*.

Idempotent — re-run sau mỗi vòng revision đều được. Gate `doc_stamped` @approve-document verify
stamp đã xảy ra (mirror domain_stamped — chặn approve chay).

Usage:
  py scripts/approve_document.py            # stamp toàn bộ
  py scripts/approve_document.py --selftest
Exit: 0 = ok (kể cả không có doc nào) · 1 = lỗi IO.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# (glob tương đối repo-root, status đích, status giữ nguyên nếu đang là)
#
# Dùng GLOB chứ không dùng thư mục: lớp discovery có file lồng (`boundaries/<b>/CHARTER.md`) và
# file lẻ ngoài thư mục của nó (`docs/architecture/PROJECT.md` — discovery sở hữu theo phase-lock).
STAMP_PLANS: dict[str, list[tuple[str, str, tuple[str, ...]]]] = {
    # Ký ở CHỐT D3 của `/discover`, trước khi sang DOMAIN. Vì sao ký tại đây chứ không đợi REVIEW:
    # discovery là lớp THƯỢNG NGUỒN nhất — domain/design/plan đều xây trên nó. Đợi tới REVIEW mới
    # ký nghĩa là phát hiện lỗ ở hypothesis-log sau khi đã dựng ba tầng lên trên, phải tháo ngược.
    # Cùng lý do challenge đặt TRƯỚC khi code chứ không dựa vào review sau khi code.
    "discovery": [
        ("docs/discovery/*.md", "APPROVED", ()),
        ("docs/discovery/event-storming/ES-*.md", "APPROVED", ()),
        ("docs/discovery/boundaries/*/CHARTER.md", "APPROVED", ()),
        ("docs/architecture/PROJECT.md", "APPROVED", ()),
    ],
    # Ký ở `/approve-document` (REVIEW) — cổng mở wave.
    "design": [
        ("docs/architecture/adr/*.md", "APPROVED", ()),
        ("docs/architecture/hld/*.md", "APPROVED", ()),
        ("docs/architecture/data-model/*.md", "APPROVED", ()),
        ("docs/architecture/ux/*.md", "APPROVED", ()),
        ("docs/architecture/integrations/*.md", "APPROVED", ()),
        ("docs/architecture/api/*.md", "ACTIVE", ("DEPRECATED",)),
        ("docs/architecture/events/*.md", "ACTIVE", ("DEPRECATED",)),
    ],
}

_STATUS_RE = re.compile(r"^(\s*status\s*:).*$", re.MULTILINE)


def _stamp(path: Path, status: str, keep: tuple[str, ...]) -> bool:
    """Set `status: <status>` trong frontmatter (giữ nguyên nếu đang ∈ keep). True nếu file đổi."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not text.startswith("---"):
        return False  # không có frontmatter → không stamp (doc tự do)
    end = text.find("\n---", 3)
    if end <= 0:
        return False
    fm, rest = text[: end], text[end:]
    m = _STATUS_RE.search(fm)
    if m:
        current = m.group(0).split(":", 1)[1].strip().strip("\"'").upper()
        if current in keep:
            return False
        new_fm = _STATUS_RE.sub(rf"\1 {status}", fm, count=1)
    else:
        new_fm = fm.rstrip("\n") + f"\nstatus: {status}"
    new = new_fm + rest
    if new != text:
        path.write_text(new, encoding="utf-8")
        return True
    return False


def run(layer: str = "design", root: Path | None = None) -> tuple[int, int]:
    """Stamp một LỚP doc theo STAMP_PLANS. Trả (số file quét, số file đổi)."""
    root = root or REPO_ROOT
    scanned = changed = 0
    for pattern, status, keep in STAMP_PLANS[layer]:
        for p in sorted(root.glob(pattern)):
            if not p.is_file():
                continue
            if p.name.startswith("TEMPLATE") or p.name.startswith("_TEMPLATE") or p.name == "README.md":
                continue
            scanned += 1
            if _stamp(p, status, keep):
                changed += 1
    return scanned, changed


def _selftest() -> int:
    import shutil
    import tempfile

    d = Path(tempfile.mkdtemp(prefix="approve_doc_"))
    try:
        (d / "docs/architecture/hld").mkdir(parents=True)
        (d / "docs/architecture/api").mkdir(parents=True)
        (d / "docs/architecture/hld/hld-x.md").write_text(
            '---\ntype: design\nstatus: "DRAFT | REVIEW | APPROVED"\n---\n# H\n', encoding="utf-8")
        (d / "docs/architecture/api/api-x.md").write_text(
            '---\nstatus: DRAFT\nversion: 1\n---\n# A\n', encoding="utf-8")
        (d / "docs/architecture/api/api-old.md").write_text(
            '---\nstatus: DEPRECATED\n---\n# old\n', encoding="utf-8")
        (d / "docs/architecture/api/TEMPLATE.api.md").write_text(
            '---\nstatus: DRAFT\n---\n', encoding="utf-8")
        scanned, changed = run("design", d)
        assert scanned == 3 and changed == 2, (scanned, changed)
        assert "status: APPROVED" in (d / "docs/architecture/hld/hld-x.md").read_text(encoding="utf-8")
        assert "status: ACTIVE" in (d / "docs/architecture/api/api-x.md").read_text(encoding="utf-8")
        assert "status: DEPRECATED" in (d / "docs/architecture/api/api-old.md").read_text(encoding="utf-8")
        assert "status: DRAFT" in (d / "docs/architecture/api/TEMPLATE.api.md").read_text(encoding="utf-8")
        # idempotent
        assert run("design", d) == (3, 0)

        # lớp discovery: file phẳng + file LỒNG (boundaries/<b>/CHARTER.md) + file LẺ ngoài
        # docs/discovery (PROJECT.md — discovery sở hữu theo phase-lock). Đây là lý do dùng
        # glob thay vì duyệt thư mục.
        (d / "docs/discovery/event-storming").mkdir(parents=True)
        (d / "docs/discovery/boundaries/payment").mkdir(parents=True)
        for rel in ("docs/discovery/hypothesis-log.md", "docs/discovery/persona-pool.md",
                    "docs/discovery/event-storming/ES-payment.md",
                    "docs/discovery/boundaries/payment/CHARTER.md",
                    "docs/architecture/PROJECT.md"):
            (d / rel).write_text("---\nstatus: DRAFT\n---\n# x\n", encoding="utf-8")
        (d / "docs/discovery/TEMPLATE.hypothesis-log.md").write_text(
            "---\nstatus: DRAFT\n---\n", encoding="utf-8")
        sc, ch = run("discovery", d)
        assert (sc, ch) == (5, 5), (sc, ch)
        assert "status: APPROVED" in (d / "docs/discovery/boundaries/payment/CHARTER.md").read_text(encoding="utf-8")
        assert "status: APPROVED" in (d / "docs/architecture/PROJECT.md").read_text(encoding="utf-8")
        assert "status: DRAFT" in (d / "docs/discovery/TEMPLATE.hypothesis-log.md").read_text(encoding="utf-8")
        assert run("discovery", d) == (5, 0)          # idempotent
        # ký discovery KHÔNG đụng lớp design và ngược lại
        assert run("design", d) == (3, 0)
        print("OK: approve_document.py selftest passed")
        return 0
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        return _selftest()
    layer = "design"
    for i, a in enumerate(argv):
        if a == "--layer" and i + 1 < len(argv):
            layer = argv[i + 1]
        elif a.startswith("--layer="):
            layer = a.split("=", 1)[1]
    if layer not in STAMP_PLANS:
        print(f"ERROR: --layer phải ∈ {sorted(STAMP_PLANS)} (nhận {layer!r})", file=sys.stderr)
        return 2
    scanned, changed = run(layer)
    what = ("discovery (hypothesis/persona/capability/BOUNDARY-MAP/ES/CHARTER/PROJECT) → APPROVED"
            if layer == "discovery" else
            "design/contract (adr/hld/data-model/ux/integrations → APPROVED; api/events → ACTIVE; "
            "DEPRECATED giữ nguyên)")
    print(f"OK: lớp {layer} — quét {scanned} doc, stamp {changed} file. {what}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
