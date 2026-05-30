#!/usr/bin/env python3
"""Reset harness for a new project (v4 — TODO: full rewrite).

⚠️ STATUS: STUB — script này chưa được update cho v4 structure.
File paths + agent inventory + KG locations đã thay đổi nhiều ở rebuild v4.

KEEP (v4 structure, never touched):
  - scripts/**
  - .claude/skills/**
  - harness/{STATE-MACHINE.json, PROTOCOL.md}
  - .claude/settings.json, .gitignore, README.md, SETUP-GUIDE.md, AGENTS.md, CLAUDE.md
  - agents/{_template-*.md, README.md, ALL singleton command agents (16 files)}
  - knowledge-base/TEMPLATE.boundary-kg.yaml
  - docs/architecture/{TEMPLATE.*.md, README.md} + folder structure
  - docs/plans/{TEMPLATE.*.md, README.md}
  - tracking/{_templates/*, README.md}
  - handoff/TEMPLATE.wave.md
  - commands/**, .claude/commands/**

REMOVE (project-specific artifacts):
  - docs/architecture/PROJECT.md
  - docs/architecture/{feat,adr,hld,api,data-model,ux,events,integrations}/[non-TEMPLATE files]
  - docs/architecture/infra/docker-compose.yml (preserve TEMPLATE if exists)
  - docs/plans/WAVE-SEQUENCE.md + wave-*.md
  - tracking/wave-*/  (entire folders)
  - handoff/wave-*.md
  - agents/{dev-,fix-}*-agent.md (materialized per boundary)
  - knowledge-base/*.knowledge-graph.yaml (except TEMPLATE)
  - services/** (if exists — should be gitignored)

RESET:
  - harness/STATE.json -> BOOTSTRAP initial state (preserves project.id)
  - harness/SERVICE-BOUNDARY-MATRIX.json -> empty boundaries

Usage (when stub replaced with real impl):
  py scripts/reset_for_new_project.py --dry-run
  py scripts/reset_for_new_project.py --confirm
  py scripts/reset_for_new_project.py --confirm --project-id my-new-app --display-name "My New App"

TODO Step 21+: Rewrite full v4 implementation.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from harness_lib import load_json, load_yaml, repo_root, save_json, save_yaml, utc_now_iso

CORE_AGENTS = frozenset({
    "_template.agent.md",
    "README.md",
    "intake-orchestrator-agent.md",
    "requirement-analyst-agent.md",
    "business-analyst-agent.md",
    "solution-architect-agent.md",
    "program-planner-agent.md",
    "apply-cr-agent.md",
    "start-wave-agent.md",
    "review-document-agent.md",
    "dev-handoff-agent.md",
    "test-plan-agent.md",
    "test-execute-agent.md",
    "release-agent.md",
    "end-wave-agent.md",
    "done-wave-agent.md",
    "reviewer-agent.md",
})


def _boundary_agent_files(boundary: str) -> list[str]:
    return [
        f"{boundary}-agent.md",
        f"fix-{boundary}-agent.md",
        f"review-{boundary}-agent.md",
    ]


def collect_targets() -> dict[str, list[Path]]:
    root = repo_root()
    targets: dict[str, list[Path]] = {"remove": [], "reset": []}

    # docs/architecture project-specific files
    arch = root / "docs/architecture"
    if arch.is_dir():
        for name in ("PROJECT.md", "integrations-matrix.md"):
            f = arch / name
            if f.is_file():
                targets["remove"].append(f)
        for sub, prefix in [
            ("feat", "FEAT-"),
            ("adr", "ADR-"),
            ("hld", "hld-"),
            ("api", "api-"),
            ("data-model", "data-model-"),
            ("ux", "ux-"),
        ]:
            d = arch / sub
            if d.is_dir():
                for f in d.glob(f"{prefix}*.md"):
                    if not f.name.startswith("TEMPLATE"):
                        targets["remove"].append(f)
        infra = arch / "infra"
        if infra.is_dir():
            for name in ("docker-compose.yml", "local-dev.md"):
                f = infra / name
                if f.is_file():
                    targets["remove"].append(f)

    # docs/plans
    plans = root / "docs/plans"
    if plans.is_dir():
        for sub in ("project", "waves"):
            d = plans / sub
            if d.is_dir():
                for f in d.rglob("*"):
                    if f.is_file() and not f.name.startswith("TEMPLATE") and f.name != ".gitkeep":
                        targets["remove"].append(f)

    # tracking
    tracking = root / "tracking"
    if tracking.is_dir():
        # Per-wave folder structure: remove entire tracking/waves/* (wave artifacts)
        waves_dir = tracking / "waves"
        if waves_dir.is_dir():
            for child in waves_dir.iterdir():
                if child.name == ".gitkeep":
                    continue
                targets["remove"].append(child)
        # Cross-wave: change-requests (keep TEMPLATE)
        cr_dir = tracking / "change-requests"
        if cr_dir.is_dir():
            for f in cr_dir.glob("*.md"):
                if not f.name.startswith("TEMPLATE"):
                    targets["remove"].append(f)

    # handoff
    handoff = root / "handoff"
    if handoff.is_dir():
        for f in handoff.glob("wave-*.md"):
            targets["remove"].append(f)

    # Boundary agents + KGs (derive from current matrix)
    try:
        matrix = load_json(root / "harness/SERVICE-BOUNDARY-MATRIX.json")
        for b in matrix.get("boundaries", []):
            bid = b.get("boundary_id")
            if not bid:
                continue
            for name in _boundary_agent_files(bid):
                f = root / "agents" / name
                if f.is_file() and name not in CORE_AGENTS:
                    targets["remove"].append(f)
            kg = root / "knowledge-base" / f"{bid}.knowledge-graph.yaml"
            if kg.is_file():
                targets["remove"].append(kg)
    except Exception:
        pass

    # Also: any agents/*.md not in CORE_AGENTS (stale boundary agents)
    agents_dir = root / "agents"
    if agents_dir.is_dir():
        for f in agents_dir.glob("*-agent.md"):
            if f.name in CORE_AGENTS:
                continue
            if f not in targets["remove"]:
                targets["remove"].append(f)

    # Also: any knowledge-base/*.yaml that's not shared or TEMPLATE
    kg_dir = root / "knowledge-base"
    if kg_dir.is_dir():
        for f in kg_dir.glob("*.knowledge-graph.yaml"):
            if f.name in ("shared.knowledge-graph.yaml", "TEMPLATE.knowledge-graph.yaml"):
                continue
            if f not in targets["remove"]:
                targets["remove"].append(f)

    # services/ directory — keep framework files (README, .gitkeep), remove project code
    services = root / "services"
    if services.is_dir():
        FRAMEWORK_KEEP = {".gitkeep", "README.md"}
        for child in services.iterdir():
            if child.name in FRAMEWORK_KEEP:
                continue
            targets["remove"].append(child)

    # Files to reset
    targets["reset"].append(root / "harness/STATE.json")
    targets["reset"].append(root / "harness/SERVICE-BOUNDARY-MATRIX.json")
    if (root / "knowledge-base/shared.knowledge-graph.yaml").is_file():
        targets["reset"].append(root / "knowledge-base/shared.knowledge-graph.yaml")

    return targets


def reset_state(project_id: str | None, display_name: str | None) -> None:
    root = repo_root()
    state_path = root / "harness/STATE.json"
    current = load_json(state_path) if state_path.is_file() else {}
    proj = current.get("project") or {}
    if project_id:
        proj["id"] = project_id
    if display_name:
        proj["display_name"] = display_name
    if not proj.get("id"):
        proj["id"] = "new-project"
    if not proj.get("display_name"):
        proj["display_name"] = proj["id"].replace("-", " ").title()

    fresh = {
        "version": 2,
        "project": proj,
        "wave": {"id": None, "number": None},
        "stage": "BOOTSTRAP",
        "previous_stage": None,
        "features_in_flight": [],
        "boundaries_in_flight": [],
        "active_boundary": None,
        "owned_paths": [],
        "non_negotiables": [],
        "context": {
            "docs": [],
            "skills": [],
            "agents": [],
            "knowledge_graphs": ["knowledge-base/shared.knowledge-graph.yaml"],
            "kg_discipline": {
                "in_progress": [], "do_not_repeat": [], "blockers": [], "active_decisions": []
            },
            "rules": [".cursor/rules/harness-agent-discipline.mdc"]
        },
        "spawn": {"allowed_stages": ["IMPLEMENTATION", "FIX_MANUAL_BUGS"], "active": None},
        "workflow": {
            "last_completed": None,
            "completed": [],
            "allowed_next": ["intake-requirement"],
            "evidence": {},
            "pipeline": None,
            "active_command": None
        },
        "checkpoints": [],
        "handoff": {"file": None, "last_sync_at": None},
        "tracking": {"bugs": [], "change_requests": [], "deferred_items": []},
        "meta": {
            "revision": 1,
            "updated_at": utc_now_iso(),
            "updated_by": "reset_for_new_project",
            "notes": f"Fresh starter for project={proj['id']}. Run /intake-requirement to begin."
        }
    }
    save_json(state_path, fresh)
    print(f"RESET {state_path.relative_to(root)} (project.id={proj['id']})")


def reset_matrix() -> None:
    root = repo_root()
    p = root / "harness/SERVICE-BOUNDARY-MATRIX.json"
    save_json(p, {"version": 1, "boundaries": []})
    print(f"RESET {p.relative_to(root)}")


def reset_shared_kg() -> None:
    root = repo_root()
    p = root / "knowledge-base/shared.knowledge-graph.yaml"
    tpl = root / "knowledge-base/TEMPLATE.knowledge-graph.yaml"
    if not p.is_file():
        return
    if tpl.is_file():
        try:
            data = load_yaml(tpl)
            data.setdefault("meta", {})["updated_at"] = utc_now_iso()
            save_yaml(p, data)
            print(f"RESET {p.relative_to(root)} (from TEMPLATE)")
            return
        except Exception:
            pass
    # Fallback: minimal skeleton
    skeleton = {
        "meta": {"updated_at": utc_now_iso(), "scope": "shared"},
        "domain": {"entities": []},
        "decisions": [],
        "implementation": {"in_progress": [], "completed": []},
        "discipline": {"do_not_repeat": [], "blockers": []},
        "learnings": {"gotchas": []}
    }
    save_yaml(p, skeleton)
    print(f"RESET {p.relative_to(root)} (skeleton)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="show targets, do nothing")
    ap.add_argument("--confirm", action="store_true", help="actually delete/reset")
    ap.add_argument("--project-id", help="new project.id (kebab-case)")
    ap.add_argument("--display-name", help="new project.display_name")
    args = ap.parse_args()

    if not args.dry_run and not args.confirm:
        ap.error("Use --dry-run to preview or --confirm to execute. This is destructive.")

    targets = collect_targets()
    root = repo_root()

    print("=== Files to REMOVE ===")
    for f in targets["remove"]:
        try:
            rel = f.relative_to(root)
        except Exception:
            rel = f
        marker = "(dir)" if f.is_dir() else ""
        print(f"  - {rel} {marker}")
    print(f"Total: {len(targets['remove'])}")
    print()
    print("=== Files to RESET ===")
    for f in targets["reset"]:
        print(f"  - {f.relative_to(root)}")
    print()

    if args.dry_run:
        print("DRY RUN — no changes made.")
        return 0

    # Execute
    for f in targets["remove"]:
        try:
            if f.is_dir():
                shutil.rmtree(f)
            else:
                f.unlink()
            print(f"REMOVED {f.relative_to(root)}")
        except Exception as e:
            print(f"FAIL remove {f}: {e}", file=sys.stderr)

    reset_state(args.project_id, args.display_name)
    reset_matrix()
    reset_shared_kg()

    print()
    print("=== DONE ===")
    print("Next steps:")
    print("  1. py scripts/harness.py state                       # verify BOOTSTRAP")
    print("  2. py scripts/build_command_prompt.py intake-requirement --step 1 --input \"<project description>\"")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
