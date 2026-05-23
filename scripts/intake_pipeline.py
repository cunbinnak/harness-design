#!/usr/bin/env python3
"""Intake pipeline — one command, multiple specialist agents.

Usage:
  python scripts/intake_pipeline.py list
  python scripts/intake_pipeline.py step <1-4>
  python scripts/intake_pipeline.py show
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from harness_lib import load_json, repo_root


def pipeline_path() -> Path:
    return repo_root() / "harness" / "INTAKE-PIPELINE.json"


def load_pipeline() -> dict:
    return load_json(pipeline_path())


def cmd_list() -> int:
    p = load_pipeline()
    print(f"Command: {p['command']}")
    print(f"Orchestrator: {p['orchestrator_agent']}\n")
    for s in sorted(p["steps"], key=lambda x: x["order"]):
        print(f"  {s['order']}. {s['id']}")
        print(f"     agent: {s['agent']}")
        print(f"     skill: {s['skill']} · stage: {s['adlc_stage']}")
        print(f"     {s['summary']}\n")
    return 0


def cmd_step(n: int) -> int:
    p = load_pipeline()
    steps = {s["order"]: s for s in p["steps"]}
    if n not in steps:
        print(f"Step must be 1-{len(steps)}", file=sys.stderr)
        return 64
    s = steps[n]
    root = repo_root()
    agent = root / s["agent"]
    print(json.dumps(
        {
            "step": s["id"],
            "order": s["order"],
            "agent_file": str(agent.relative_to(root)).replace("\\", "/"),
            "skill": s["skill"],
            "adlc_stage": s["adlc_stage"],
            "summary": s["summary"],
            "agent_exists": agent.is_file(),
        },
        indent=2,
        ensure_ascii=False,
    ))
    return 0


def cmd_show() -> int:
    from state_engine import load_state

    state = load_state()
    print(json.dumps(
        {
            "wave": state.get("wave"),
            "stage": state.get("stage"),
            "handoff": state.get("handoff"),
            "workflow_allowed_next": (state.get("workflow") or {}).get("allowed_next"),
        },
        indent=2,
        ensure_ascii=False,
    ))
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 64
    if sys.argv[1] == "list":
        return cmd_list()
    if sys.argv[1] == "show":
        return cmd_show()
    if sys.argv[1] == "step" and len(sys.argv) >= 3:
        return cmd_step(int(sys.argv[2]))
    print(__doc__)
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
