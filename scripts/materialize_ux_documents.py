#!/usr/bin/env python3
"""Tạo docs/architecture/ux/ux-{boundary_id}.md từ template (mọi FE boundary).

Usage:
  py scripts/materialize_ux_documents.py --boundaries fe-web,fe-admin
  py scripts/materialize_ux_documents.py --from-roster docs/plans/project/agent-roster.md
  py scripts/materialize_ux_documents.py --from-roster docs/plans/project/agent-roster.md --force
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from harness_lib import repo_root
from materialize_boundary_agents import parse_roster_row

TEMPLATE_REL = Path("docs/architecture/ux/TEMPLATE.ux.md")


def _template_text() -> str:
    p = repo_root() / TEMPLATE_REL
    if not p.is_file():
        raise FileNotFoundError(f"missing {TEMPLATE_REL}")
    return p.read_text(encoding="utf-8")


def _render_ux(boundary_id: str, template: str) -> str:
    text = template.replace("{boundary_id}", boundary_id)
    # Đảm bảo tiêu đề khớp file
    if text.startswith("# UX —"):
        text = re.sub(
            r"^# UX —.*$",
            f"# UX — {boundary_id}",
            text,
            count=1,
            flags=re.M,
        )
    return text


def fe_boundary_ids_from_roster(roster_path: Path) -> list[str]:
    rows = parse_roster_row(roster_path)
    return [r.boundary_id for r in rows if r.layer == "fe"]


def materialize_ux(
    boundary_ids: list[str],
    *,
    dry_run: bool = False,
    force: bool = False,
) -> list[str]:
    root = repo_root()
    ux_dir = root / "docs/architecture/ux"
    ux_dir.mkdir(parents=True, exist_ok=True)
    template = _template_text()
    created: list[str] = []

    for bid in boundary_ids:
        bid = bid.strip()
        if not bid:
            continue
        out = ux_dir / f"ux-{bid}.md"
        rel = str(out.relative_to(root)).replace("\\", "/")
        if out.is_file() and not force:
            continue
        if dry_run:
            created.append(rel)
            continue
        out.write_text(_render_ux(bid, template), encoding="utf-8")
        created.append(rel)
    return created


def main() -> int:
    ap = argparse.ArgumentParser(description="Materialize ux-{boundary_id}.md for FE boundaries")
    ap.add_argument("--boundaries", help="comma-separated FE boundary ids (e.g. fe-web,fe-admin)")
    ap.add_argument("--from-roster", type=Path, help="agent-roster.md — chỉ row layer fe")
    ap.add_argument("--force", action="store_true", help="overwrite existing ux files")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ids: list[str] = []
    if args.boundaries:
        ids = [b.strip() for b in args.boundaries.split(",") if b.strip()]
    if args.from_roster:
        path = args.from_roster
        if not path.is_file():
            path = repo_root() / path
        if not path.is_file():
            print(f"ERROR: roster not found: {args.from_roster}", file=sys.stderr)
            return 1
        ids = fe_boundary_ids_from_roster(path)
        if not ids:
            print(
                "WARN: no FE rows in roster (cột layer = fe). "
                "Thêm fe-web, fe-admin, … vào agent-roster.md",
                file=sys.stderr,
            )

    if not ids:
        print(
            "ERROR: specify --boundaries or --from-roster with FE boundaries",
            file=sys.stderr,
        )
        return 64

    created = materialize_ux(ids, dry_run=args.dry_run, force=args.force)
    if not created:
        print("No new ux files (already exist; use --force to overwrite)")
        return 0
    for p in created:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
