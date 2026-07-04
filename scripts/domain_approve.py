"""
domain_approve.py — KÝ business doc ở docs/domain/: jargon-check + stamp `status: APPROVED` vào frontmatter.

Ký TRƯỚC, dịch SAU. Ký lẻ 1 doc hoặc toàn bộ (không arg = all). Doc còn jargon kỹ thuật → REFUSE
(không stamp) để chủ-nghiệp-vụ sửa cho plain rồi ký lại. Stamp ghi thẳng frontmatter (không qua Edit
tool → phase-lock không chặn; DOMAIN_AUTHORING vẫn sở hữu docs/domain).

Usage:
  py scripts/domain_approve.py            # ký TẤT CẢ business doc
  py scripts/domain_approve.py EP-clinic-001   # ký 1 doc (theo stem/prefix)
  py scripts/domain_approve.py all
Exit: 0 = đã ký (hoặc đã ký sẵn) · 1 = còn jargon, refuse · 2 = không tìm thấy target.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import gates  # noqa: E402  (reuse _domain_business_files + _JARGON_RES + _frontmatter_approved)

REPO_ROOT = SCRIPTS.parent


def _has_jargon(body: str) -> list[str]:
    return [rx.pattern for rx in gates._JARGON_RES if rx.search(body)]


def _stamp_approved(path: Path) -> bool:
    """KÝ = set `status: APPROVED` trong frontmatter (ZIP-faithful sign-off). True nếu đổi."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end > 0:
            fm, rest = text[4:end], text[end:]
            if re.search(r"^\s*status\s*:", fm, re.MULTILINE):
                fm = re.sub(r"^\s*status\s*:.*$", "status: APPROVED", fm, count=1, flags=re.MULTILINE)
            else:
                fm = fm.rstrip("\n") + "\nstatus: APPROVED"
            new = "---\n" + fm + rest
        else:
            new = "---\nstatus: APPROVED\n---\n" + text
    else:
        new = "---\nstatus: APPROVED\n---\n" + text
    if new != text:
        path.write_text(new, encoding="utf-8")
        return True
    return False


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass
    argv = argv if argv is not None else sys.argv[1:]
    target = (argv[0] if argv else "all").strip()

    files = gates._domain_business_files(REPO_ROOT)
    if target.lower() != "all":
        files = [p for p in files if p.stem == target or p.stem.startswith(target)]
        if not files:
            print(f"FAIL: không thấy business doc '{target}' ở docs/domain/", file=sys.stderr)
            return 2
    if not files:
        print("FAIL: chưa có business doc nào ở docs/domain/ — /domain-po · /domain-ba author trước.", file=sys.stderr)
        return 2

    jargon_docs: list[str] = []
    for p in files:
        txt = p.read_text(encoding="utf-8", errors="ignore")
        body = txt.split("\n---", 1)[1] if txt.startswith("---") and "\n---" in txt else txt
        if _has_jargon(body):
            jargon_docs.append(str(p.relative_to(REPO_ROOT)).replace("\\", "/"))

    if jargon_docs:
        print("REFUSE — business doc còn JARGON kỹ thuật (sửa cho plain nghiệp vụ rồi ký lại):", file=sys.stderr)
        for d in jargon_docs:
            print(f"  - {d}", file=sys.stderr)
        print("  (bỏ code/SQL/API-path/class-name/HTTP-status — chi tiết kỹ thuật để /domain-translate sinh ở eng layer.)", file=sys.stderr)
        return 1

    stamped = [str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in files if _stamp_approved(p)]
    already = len(files) - len(stamped)
    print(f"OK: đã ký {len(files)} business doc ({len(stamped)} stamp mới, {already} đã ký sẵn). "
          f"→ khi MỌI doc ký → /domain-translate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
