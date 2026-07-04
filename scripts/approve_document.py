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

# (thư mục tương đối, status đích, status giữ nguyên nếu đang là)
STAMP_PLAN = [
    ("docs/architecture/adr", "APPROVED", ()),
    ("docs/architecture/hld", "APPROVED", ()),
    ("docs/architecture/data-model", "APPROVED", ()),
    ("docs/architecture/ux", "APPROVED", ()),
    ("docs/architecture/integrations", "APPROVED", ()),
    ("docs/architecture/api", "ACTIVE", ("DEPRECATED",)),
    ("docs/architecture/events", "ACTIVE", ("DEPRECATED",)),
]

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


def run(root: Path | None = None) -> tuple[int, int]:
    """Stamp toàn bộ theo STAMP_PLAN. Trả (số file quét, số file đổi)."""
    root = root or REPO_ROOT
    scanned = changed = 0
    for rel, status, keep in STAMP_PLAN:
        d = root / rel
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.md")):
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
        scanned, changed = run(d)
        assert scanned == 3 and changed == 2, (scanned, changed)
        assert "status: APPROVED" in (d / "docs/architecture/hld/hld-x.md").read_text(encoding="utf-8")
        assert "status: ACTIVE" in (d / "docs/architecture/api/api-x.md").read_text(encoding="utf-8")
        assert "status: DEPRECATED" in (d / "docs/architecture/api/api-old.md").read_text(encoding="utf-8")
        assert "status: DRAFT" in (d / "docs/architecture/api/TEMPLATE.api.md").read_text(encoding="utf-8")
        # idempotent
        assert run(d) == (3, 0)
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
    scanned, changed = run()
    print(f"OK: quét {scanned} doc design/contract — stamp {changed} file "
          f"(adr/hld/data-model/ux/integrations → APPROVED; api/events → ACTIVE; DEPRECATED giữ nguyên).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
