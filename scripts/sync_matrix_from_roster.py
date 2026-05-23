#!/usr/bin/env python3
"""Đồng bộ harness/SERVICE-BOUNDARY-MATRIX.json từ docs/plans/project/agent-roster.md.

Sau intake + review-document — matrix là nguồn sự thật cho owned_paths, KG, agent paths.

Usage:
  py scripts/sync_matrix_from_roster.py
  py scripts/sync_matrix_from_roster.py --dry-run
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from harness_lib import get_boundary, repo_root
from materialize_boundary_agents import FE_BOUNDARY_IDS, parse_roster
from state_engine import register_boundary


def find_production_roster() -> Path:
    p = repo_root() / "docs/plans/project/agent-roster.md"
    if not p.is_file():
        raise FileNotFoundError(
            "docs/plans/project/agent-roster.md missing — run intake step 4 first"
        )
    return p


def _layer_for(boundary_id: str, layer_col: str | None) -> str:
    if layer_col and layer_col.strip().lower() in ("fe", "frontend"):
        return "fe"
    if boundary_id in FE_BOUNDARY_IDS:
        return "fe"
    return "backend"


def default_owned_paths(boundary_id: str, layer: str) -> list[str]:
    if layer == "fe":
        return [
            "apps/**",
            "packages/**",
            f"services/{boundary_id}/**",
            f"docs/architecture/ux/ux-{boundary_id}.md",
        ]
    return [
        f"services/{boundary_id}/**",
        f"docs/architecture/hld/hld-{boundary_id}.md",
        f"docs/architecture/api/api-{boundary_id}.md",
        f"docs/architecture/data-model/data-model-{boundary_id}.md",
    ]


def parse_roster_with_layer(path: Path) -> list[tuple[str, str]]:
    text = path.read_text(encoding="utf-8")
    rows: list[tuple[str, str]] = []
    for line in text.splitlines():
        if "|" not in line or "---" in line or "boundary_id" in line:
            continue
        cols = [c.strip() for c in line.split("|") if c.strip()]
        if not cols or not re.match(r"^[a-z][a-z0-9_-]*$", cols[0]):
            continue
        bid = cols[0]
        layer_col = cols[1] if len(cols) > 1 else ""
        rows.append((bid, _layer_for(bid, layer_col)))
    return rows


def sync_from_roster(*, dry_run: bool = False) -> dict:
    roster_path = find_production_roster()

    rows = parse_roster_with_layer(roster_path)
    if not rows:
        _, ids = parse_roster(roster_path)
        rows = [(b, "fe" if b in FE_BOUNDARY_IDS else "backend") for b in ids]

    added: list[str] = []
    skipped: list[str] = []
    for bid, layer in rows:
        if get_boundary(bid):
            skipped.append(bid)
            continue
        kind = "fe" if layer == "fe" else "backend"
        row = {
            "boundary_id": bid,
            "display_name": bid.replace("-", " ").title(),
            "kind": kind,
            "agent": f"agents/{bid}-agent.md",
            "knowledge_graph": f"knowledge-base/{bid}.knowledge-graph.yaml",
            "materialized_path": f"services/{bid}/" if kind == "backend" else f"services/{bid}/",
            "owned_paths": default_owned_paths(bid, layer),
        }
        if dry_run:
            added.append(bid)
            continue
        register_boundary(row)
        added.append(bid)

    return {"added": added, "skipped": skipped, "roster": str(roster_path)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    result = sync_from_roster(dry_run=args.dry_run)
    import json

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
