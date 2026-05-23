#!/usr/bin/env python3
"""Tạo knowledge-base/{boundary_id}.knowledge-graph.yaml từ template.

Usage:
  py scripts/materialize_knowledge_graphs.py --boundaries customer,sales,fe-web
  py scripts/materialize_knowledge_graphs.py --from-roster docs/plans/project/agent-roster.md
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from harness_lib import repo_root
from materialize_boundary_agents import parse_roster, parse_roster_row

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


def _template_path() -> Path:
    return repo_root() / "knowledge-base" / "TEMPLATE.knowledge-graph.yaml"


def _load_template() -> dict:
    if yaml is None:
        raise RuntimeError("PyYAML required: pip install pyyaml")
    data = yaml.safe_load(_template_path().read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("invalid KG template")
    return data


def materialize_kg(
    boundaries: list[str],
    *,
    dry_run: bool = False,
    force: bool = False,
) -> list[str]:
    root = repo_root()
    created: list[str] = []
    base = _load_template()
    for bid in boundaries:
        bid = bid.strip()
        if not bid:
            continue
        path = root / "knowledge-base" / f"{bid}.knowledge-graph.yaml"
        rel = str(path.relative_to(root))
        if path.is_file() and not force:
            continue
        data = {**base, "boundary_id": bid}
        data.setdefault("meta", {})["updated_at"] = None
        data["meta"]["updated_by"] = "materialize_knowledge_graphs"
        if dry_run:
            created.append(rel)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
        created.append(rel)
    return created


def boundaries_from_roster(path: Path) -> list[str]:
    rows = parse_roster_row(path)
    if rows:
        return [r[0] for r in rows]
    _, ids = parse_roster(path)
    return ids


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boundaries", help="comma-separated")
    ap.add_argument("--from-roster", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if args.from_roster:
        p = args.from_roster if args.from_roster.is_absolute() else repo_root() / args.from_roster
        bids = boundaries_from_roster(p)
    elif args.boundaries:
        bids = [b.strip() for b in args.boundaries.split(",") if b.strip()]
    else:
        ap.error("need --boundaries or --from-roster")

    for rel in materialize_kg(bids, dry_run=args.dry_run, force=args.force):
        print(rel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
