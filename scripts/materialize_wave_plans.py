#!/usr/bin/env python3
"""Tạo docs/plans/waves/{wave-id}/wave.md cho mọi wave trong waves-roadmap.

Usage:
  py scripts/materialize_wave_plans.py --from-roadmap docs/plans/project/waves-roadmap.md
  py scripts/materialize_wave_plans.py --waves wave-001,wave-002
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from harness_lib import repo_root

WAVE_ID_RE = re.compile(r"wave-\d{3}", re.I)


def parse_wave_ids_from_roadmap(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    found: list[str] = []
    in_table = False
    for line in text.splitlines():
        if "Wave list" in line or line.strip().lower().startswith("## wave"):
            in_table = True
            continue
        if in_table and line.startswith("## ") and "Wave list" not in line:
            in_table = False
        m = WAVE_ID_RE.search(line)
        if m and "|" in line and "---" not in line:
            found.append(m.group(0).lower())
        elif m and not found and "wave-" in line.lower():
            found.append(m.group(0).lower())
    if not found:
        for m in WAVE_ID_RE.finditer(text):
            found.append(m.group(0).lower())
    return sorted(set(found))


def _template_wave(wave_id: str) -> str:
    tpl = (repo_root() / "docs/plans/_templates/wave.md").read_text(encoding="utf-8")
    return tpl.replace("{wave-id}", wave_id).replace("{wave-id}", wave_id)


def materialize(wave_ids: list[str], *, dry_run: bool = False, force: bool = False) -> list[str]:
    root = repo_root()
    created: list[str] = []
    for wid in wave_ids:
        wid = wid.strip().replace("_", "-")
        if not WAVE_ID_RE.fullmatch(wid):
            continue
        dest_dir = root / "docs/plans/waves" / wid
        dest = dest_dir / "wave.md"
        rel = str(dest.relative_to(root))
        if dest.is_file() and not force:
            continue
        if dry_run:
            created.append(rel)
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest.write_text(_template_wave(wid), encoding="utf-8")
        created.append(rel)
    return created


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-roadmap", type=Path)
    ap.add_argument("--waves", help="comma-separated wave-001,wave-002")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if args.from_roadmap:
        p = args.from_roadmap if args.from_roadmap.is_absolute() else repo_root() / args.from_roadmap
        ids = parse_wave_ids_from_roadmap(p)
    elif args.waves:
        ids = [w.strip() for w in args.waves.split(",") if w.strip()]
    else:
        ap.error("need --from-roadmap or --waves")

    for rel in materialize(ids, dry_run=args.dry_run, force=args.force):
        print(rel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
