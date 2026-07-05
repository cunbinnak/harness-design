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
  - knowledge-base/TEMPLATE.knowledge-graph.yaml
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

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness_lib import load_json, repo_root, save_json, utc_now_iso  # noqa: E402

CORE_AGENTS = frozenset({
    # templates + readme
    "_template-dev-agent.md",
    "_template-fix-agent.md",
    "README.md",
    # discovery (D0-D3)
    "discovery-hypothesis-agent.md",
    "capability-mapper-agent.md",
    "event-stormer-agent.md",
    "charter-author-agent.md",
    # domain
    "domain-po-agent.md",
    "domain-ba-agent.md",
    # design + plan
    "solution-architect-agent.md",
    "program-planner-agent.md",
    # review singletons (per kind + document)
    "review-document-agent.md",
    "review-backend-agent.md",
    "review-bff-agent.md",
    "review-web-agent.md",
    "review-mobile-agent.md",
    # ops
    "start-wave-agent.md",
    "dev-handoff-agent.md",
    "test-plan-agent.md",
    "test-execute-agent.md",
    "log-bug-agent.md",
    "end-wave-agent.md",
    "done-wave-agent.md",
    # side
    "apply-cr-agent.md",
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
        for name in ("PROJECT.md",):
            f = arch / name
            if f.is_file():
                targets["remove"].append(f)
        for sub, prefix in [
            # DOMAIN eng artifacts (bản dịch từ docs/domain qua /domain-translate)
            ("epics", "EP-"),
            ("feat", "FEAT-"),
            ("journeys", "JOURNEY-"),
            ("personas", "PERSONA-"),
            ("business-rules", "BR-"),
            # DESIGN artifacts
            ("adr", "ADR-"),
            ("hld", "hld-"),
            ("api", "api-"),
            ("api", "bff-aggregation-"),
            ("data-model", "data-model-"),
            ("ux", "ux-"),
            ("integrations", "INTEG-"),
        ]:
            d = arch / sub
            if d.is_dir():
                for f in d.glob(f"{prefix}*.md"):
                    if not f.name.startswith("TEMPLATE"):
                        targets["remove"].append(f)
        events = arch / "events"
        if events.is_dir():
            for f in events.glob("*-events.md"):
                if not f.name.startswith("TEMPLATE"):
                    targets["remove"].append(f)
        # design tokens dùng chung (sinh ở DESIGN theo TEMPLATE.design-tokens.css — project-specific)
        tokens = arch / "ux" / "design-tokens.css"
        if tokens.is_file():
            targets["remove"].append(tokens)
        # mockup HTML per boundary (ux/mockups/{boundary}/ — giữ README.md luật mockup)
        mockups = arch / "ux" / "mockups"
        if mockups.is_dir():
            for child in mockups.iterdir():
                if child.is_dir():
                    targets["remove"].append(child)
        infra = arch / "infra"
        if infra.is_dir():
            for name in ("docker-compose.yml", "local-dev.md"):
                f = infra / name
                if f.is_file():
                    targets["remove"].append(f)

    # docs/domain (lớp BUSINESS plain VN — /domain-po·/domain-ba author + ký; giữ TEMPLATE.*)
    dom = root / "docs/domain"
    if dom.is_dir():
        for sub, prefix in [
            ("epics", "EP-"),
            ("feat", "FEAT-"),
            ("journeys", "JOURNEY-"),
            ("personas", "PERSONA-"),
            ("business-rules", "BR-"),
        ]:
            d = dom / sub
            if d.is_dir():
                for f in d.glob(f"{prefix}*.md"):
                    if not f.name.startswith("TEMPLATE"):
                        targets["remove"].append(f)

    # docs/plans (flat layout: WAVE-SEQUENCE.md + wave-{NNN}.md)
    plans = root / "docs/plans"
    if plans.is_dir():
        wseq = plans / "WAVE-SEQUENCE.md"
        if wseq.is_file():
            targets["remove"].append(wseq)
        for f in plans.glob("wave-*.md"):
            if not f.name.startswith("TEMPLATE"):
                targets["remove"].append(f)

    # docs/discovery (D0-D3 artifacts — sinh ở runtime, giữ TEMPLATE.*)
    disc = root / "docs/discovery"
    if disc.is_dir():
        for name in ("hypothesis-log.md", "persona-pool.md", "capability-map.md", "BOUNDARY-MAP.md"):
            f = disc / name
            if f.is_file():
                targets["remove"].append(f)
        es = disc / "event-storming"
        if es.is_dir():
            for f in es.glob("ES-*.md"):
                targets["remove"].append(f)
        bnd = disc / "boundaries"
        if bnd.is_dir():
            for child in bnd.iterdir():  # per-boundary {b}/CHARTER.md dirs; giữ TEMPLATE.CHARTER.md (file)
                if child.is_dir():
                    targets["remove"].append(child)

    # tracking
    tracking = root / "tracking"
    if tracking.is_dir():
        # Per-wave folders: tracking/wave-{N}/ (wave artifacts)
        for child in sorted(tracking.glob("wave-*")):
            if child.is_dir():
                targets["remove"].append(child)
        # Cross-wave: change-requests (keep TEMPLATE)
        cr_dir = tracking / "change-requests"
        if cr_dir.is_dir():
            for f in cr_dir.glob("*.md"):
                if not f.name.startswith("TEMPLATE"):
                    targets["remove"].append(f)
        # Cross-wave files sinh ở runtime: translation-log (domain-translate) +
        # doc-review-findings (sanity-check) + decisions (audit force-bypass)
        for name in ("translation-log.md", "doc-review-findings.md", "decisions.md"):
            f = tracking / name
            if f.is_file():
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
            # KG per-boundary dọn ở vòng glob bên dưới (mọi *.knowledge-graph.yaml trừ TEMPLATE)
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

    # Also: any knowledge-base/*.knowledge-graph.yaml that's not the TEMPLATE
    kg_dir = root / "knowledge-base"
    if kg_dir.is_dir():
        for f in kg_dir.glob("*.knowledge-graph.yaml"):
            if f.name == "TEMPLATE.knowledge-graph.yaml":
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

    # Schema v4 — khớp harness/STATE.json hiện tại (BOOTSTRAP, allowed_next compute động
    # từ STATE-MACHINE.json[BOOTSTRAP].allowed_commands — KHÔNG hardcode trong STATE).
    fresh = {
        "version": 4,
        "project": {
            "id": proj["id"],
            "display_name": proj["display_name"],
            "service_prefix": None,
        },
        "wave": {"id": None, "number": None},
        "stage": "BOOTSTRAP",
        "previous_stage": None,
        "active_boundary": None,
        "wave_boundaries": [],
        "wave_features": [],
        "spawn": {"active": None},
        "workflow": {"last_completed": None},
        "handoff": {"file": None},
        "meta": {
            "revision": 1,
            "updated_at": utc_now_iso(),
            "updated_by": "reset_for_new_project",
            "notes": f"Fresh starter for project={proj['id']}. Run /discovery-start D0 to begin.",
        },
    }
    save_json(state_path, fresh)
    print(f"RESET {state_path.relative_to(root)} (project.id={proj['id']})")


def reset_matrix() -> None:
    root = repo_root()
    p = root / "harness/SERVICE-BOUNDARY-MATRIX.json"
    save_json(p, {"version": 1, "boundaries": []})
    print(f"RESET {p.relative_to(root)}")


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

    print()
    print("=== DONE ===")
    print("Next steps:")
    print("  1. py scripts/harness.py state                       # verify BOOTSTRAP")
    print("  2. py scripts/build_prompt.py discovery-start --disc-wave D0 --input \"<project description>\"")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
