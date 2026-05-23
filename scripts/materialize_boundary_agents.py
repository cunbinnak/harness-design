#!/usr/bin/env python3
"""Materialize dev boundary agents (dev + fix + review) from roster.

Backend boundaries: order, product, ...
FE boundary (mặc định `fe`): fe-agent, fix-fe-agent, review-fe-agent

Usage:
  py scripts/materialize_boundary_agents.py --wave wave-001 --boundaries order,product
  py scripts/materialize_boundary_agents.py --wave wave-001 --boundaries order --include-fe
  py scripts/materialize_boundary_agents.py --from-roster docs/plans/project/agent-roster.md
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from harness_lib import repo_root

FE_BOUNDARY_IDS = frozenset({"fe", "frontend"})

ROLE_META = {
    "dev": {
        "prefix": "",
        "role_label": "Development",
        "primary_command": "start-dev",
        "spawn_stage": "IMPLEMENTATION",
        "skill_primary": "implementation",
        "identity": "kỹ sư triển khai boundary `{bid}`",
        "display": "{bid} Development Agent",
        "mission": "Triển khai code đúng FEAT và wave-plan trong owned_paths.",
        "forbidden": (
            "- Self-review thay `review-{bid}-agent`.\n"
            "- Sửa bug thay `fix-{bid}-agent`.\n"
            "- Test/release hoặc đăng ký matrix."
        ),
    },
    "fix": {
        "prefix": "fix-",
        "role_label": "Bug fix",
        "primary_command": "fix-bugs",
        "spawn_stage": "FIX_MANUAL_BUGS",
        "skill_primary": "implementation",
        "identity": "kỹ sư sửa bug boundary `{bid}`",
        "display": "fix-{bid} Bug Fix Agent",
        "mission": "Sửa lỗi trong owned_paths; ghi `tracking/bugs/`.",
        "forbidden": "- Feature mới ngoài bug scope.\n- test-execute / release.",
    },
    "review": {
        "prefix": "review-",
        "role_label": "Self-review",
        "primary_command": "review-dev",
        "spawn_stage": "SELF_REVIEW",
        "skill_primary": "self-review",
        "identity": "reviewer code boundary `{bid}`",
        "display": "review-{bid} Self-Review Agent",
        "mission": "Rà soát chất lượng code trước handoff QA.",
        "forbidden": "- Triển khai feature mới.\n- Chạy test-plan/execute.",
    },
}

LAYER_META = {
    "backend": {
        "layer": "backend",
        "layer_label": "Backend / service",
        "owned_paths_hint": "`services/{bid}/` và paths trong SERVICE-BOUNDARY-MATRIX",
        "role_meta": ROLE_META,
    },
    "fe": {
        "layer": "fe",
        "layer_label": "Frontend",
        "owned_paths_hint": "`apps/`, `packages/`, `services/fe/` (theo matrix)",
        "role_meta": {
            **ROLE_META,
            "dev": {
                **ROLE_META["dev"],
                "skill_primary": "frontend-implementation",
                "identity": "kỹ sư frontend boundary `{bid}`",
                "display": "{bid} Frontend Development Agent",
                "mission": "Triển khai UI/FE đúng FEAT, HLD và contract API backend.",
            },
            "fix": {
                **ROLE_META["fix"],
                "skill_primary": "frontend-implementation",
                "identity": "kỹ sư sửa bug frontend boundary `{bid}`",
                "display": "fix-{bid} Frontend Bug Fix Agent",
                "mission": "Sửa lỗi UI/FE trong owned_paths; ghi `tracking/bugs/`.",
            },
            "review": {
                **ROLE_META["review"],
                "skill_primary": "self-review",
                "identity": "reviewer frontend boundary `{bid}`",
                "display": "review-{bid} Frontend Self-Review Agent",
                "mission": "Rà soát chất lượng FE trước handoff QA.",
            },
        },
    },
}


def layer_for_boundary(boundary_id: str) -> str:
    if boundary_id in FE_BOUNDARY_IDS:
        return "fe"
    return "backend"


def _template() -> str:
    return (repo_root() / "agents" / "_template.agent.md").read_text(encoding="utf-8")


def _fill(
    template: str,
    *,
    bid: str,
    role_key: str,
    wave: str,
    wave_scope: str,
    layer_key: str,
) -> str:
    layer = LAYER_META[layer_key]
    meta = layer["role_meta"][role_key]
    owned = layer["owned_paths_hint"].format(bid=bid)
    return (
        template.replace("{{boundary_id}}", bid)
        .replace("{{layer}}", layer["layer"])
        .replace("{{layer_label}}", layer["layer_label"])
        .replace("{{owned_paths_hint}}", owned)
        .replace("{{prefix}}", meta["prefix"])
        .replace("{{role}}", role_key)
        .replace("{{role_label}}", meta["role_label"])
        .replace("{{primary_command}}", meta["primary_command"])
        .replace("{{spawn_stage}}", meta["spawn_stage"])
        .replace("{{wave}}", wave)
        .replace("{{wave_scope}}", wave_scope)
        .replace("{{role_mission}}", meta["mission"])
        .replace("{{identity_one_liner}}", meta["identity"].format(bid=bid))
        .replace("{{agent_display_name}}", meta["display"].format(bid=bid))
        .replace("{{role_forbidden}}", meta["forbidden"].format(bid=bid))
        .replace("{{skill_primary}}", meta["skill_primary"])
    )


def materialize(
    boundaries: list[str],
    wave: str,
    *,
    wave_scope: str = "Theo wave-plan",
    include_fe: bool = True,
    fe_boundary_id: str = "fe",
    dry_run: bool = False,
    force: bool = False,
) -> list[str]:
    root = repo_root()
    template = _template()
    created: list[str] = []

    bids = [b.strip() for b in boundaries if b.strip()]
    fe_id = fe_boundary_id.strip() or "fe"
    if include_fe and fe_id not in bids:
        bids.append(fe_id)

    for bid in bids:
        layer_key = layer_for_boundary(bid)
        for role_key in ("dev", "fix", "review"):
            layer = LAYER_META[layer_key]
            meta = layer["role_meta"][role_key]
            name = f"{meta['prefix']}{bid}-agent.md"
            path = root / "agents" / name
            content = _fill(
                template,
                bid=bid,
                role_key=role_key,
                wave=wave,
                wave_scope=wave_scope,
                layer_key=layer_key,
            )
            rel = str(path.relative_to(root))
            if dry_run:
                created.append(rel)
                continue
            if path.is_file() and not force:
                continue
            path.write_text(content, encoding="utf-8")
            created.append(rel)
    return created


def parse_roster(path: Path) -> tuple[str, list[str]]:
    text = path.read_text(encoding="utf-8")
    wave = "wave-001"
    m = re.search(r"wave-\d{3}", text, re.I)
    if m:
        wave = m.group(0).lower()
    boundaries: list[str] = []
    for line in text.splitlines():
        if "|" not in line or "---" in line or "boundary_id" in line:
            continue
        cols = [c.strip() for c in line.split("|") if c.strip()]
        if cols and re.match(r"^[a-z][a-z0-9_-]*$", cols[0]):
            boundaries.append(cols[0])
    return wave, sorted(set(boundaries))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wave", default="wave-001")
    ap.add_argument("--wave-scope", default="Theo wave-plan")
    ap.add_argument("--boundaries", help="comma-separated boundary ids (backend + optional fe)")
    ap.add_argument("--from-roster", type=Path)
    ap.add_argument("--fe-boundary", default="fe", help="FE boundary id when --include-fe")
    ap.add_argument("--no-fe", action="store_true", help="skip auto materialize FE agent set")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if args.from_roster:
        p = args.from_roster if args.from_roster.is_absolute() else repo_root() / args.from_roster
        wave, boundaries = parse_roster(p)
    elif args.boundaries:
        wave = args.wave.replace("_", "-")
        boundaries = [b.strip() for b in args.boundaries.split(",") if b.strip()]
    else:
        ap.error("need --boundaries or --from-roster")

    created = materialize(
        boundaries,
        wave,
        wave_scope=args.wave_scope,
        include_fe=not args.no_fe,
        fe_boundary_id=args.fe_boundary,
        dry_run=args.dry_run,
        force=args.force,
    )
    for p in created:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
