#!/usr/bin/env python3
"""Intake pipeline — track progress in harness/STATE.json per step.

Usage:
  python scripts/intake_pipeline.py list
  python scripts/intake_pipeline.py show
  python scripts/intake_pipeline.py begin <1-4>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from harness_lib import load_json, repo_root, utc_now_iso


def pipeline_path() -> Path:
    return repo_root() / "harness" / "PIPELINES.json"


def load_pipeline(name: str = "intake-requirement") -> dict[str, Any]:
    data = load_json(pipeline_path())
    pipelines = data.get("pipelines") or {}
    if name not in pipelines:
        raise ValueError(f"pipeline {name!r} not in {pipeline_path().name}")
    return pipelines[name]


def _steps_by_order(pipeline: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {s["order"]: s for s in pipeline["steps"]}


def begin_step(order: int, *, updated_by: str = "intake_pipeline") -> dict[str, Any]:
    """Mark intake step *order* in STATE (stage + workflow.pipeline)."""
    from state_engine import load_state, save_state, validate_state  # noqa: WPS433
    from workflow_engine import ensure_workflow  # noqa: WPS433

    pipeline = load_pipeline()
    command = pipeline["command"]
    steps = _steps_by_order(pipeline)
    if order not in steps:
        raise ValueError(f"step must be 1-{len(steps)}")

    state = ensure_workflow(load_state())
    wf = state["workflow"]
    if command not in wf.get("allowed_next", []):
        raise ValueError(
            f"{command!r} not in workflow.allowed_next={wf.get('allowed_next')!r}"
        )

    step_cfg = steps[order]
    pipe = dict(wf.get("pipeline") or {})

    if order == 1:
        pipe = {
            "command": command,
            "total_steps": len(steps),
            "completed_steps": [],
            "active_step": None,
            "active_step_id": None,
            "adlc_stage": None,
            "started_at": utc_now_iso(),
            "updated_at": None,
        }
    elif pipe.get("command") != command:
        raise ValueError("intake pipeline chưa bắt đầu — chạy step 1 trước")

    completed = list(pipe.get("completed_steps") or [])
    prev = order - 1
    if order > 1:
        if prev not in completed and pipe.get("active_step") != prev:
            raise ValueError(
                f"phải hoàn thành step {prev} trước "
                f"(completed_steps={completed}, active_step={pipe.get('active_step')})"
            )
        if prev not in completed:
            completed.append(prev)
            completed.sort()

    pipe["completed_steps"] = completed
    pipe["active_step"] = order
    pipe["active_step_id"] = step_cfg["id"]
    pipe["adlc_stage"] = step_cfg["adlc_stage"]
    pipe["updated_at"] = utc_now_iso()
    wf["pipeline"] = pipe
    wf["active_command"] = command

    target_stage = step_cfg["adlc_stage"]
    if state.get("stage") != target_stage:
        state["previous_stage"] = state.get("stage")
        state["stage"] = target_stage

    errors = validate_state(state)
    if errors:
        raise ValueError("STATE invalid after intake step:\n  - " + "\n  - ".join(errors))

    try:
        from hooks.task_check import run_trigger  # noqa: WPS433

        run_trigger(
            "pre_task_check",
            state,
            {"command": "intake-requirement", "step": order, "agent_file": step_cfg["agent"]},
            block=False,
        )
    except Exception:
        pass

    save_state(state, updated_by=updated_by)
    return step_cfg


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


def cmd_show() -> int:
    from state_engine import load_state  # noqa: WPS433

    state = load_state()
    wf = state.get("workflow") or {}
    print(
        json.dumps(
            {
                "stage": state.get("stage"),
                "workflow": {
                    "active_command": wf.get("active_command"),
                    "allowed_next": wf.get("allowed_next"),
                    "pipeline": wf.get("pipeline"),
                },
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_begin(n: int) -> int:
    step = begin_step(n)
    print(
        json.dumps(
            {
                "step": step["id"],
                "order": step["order"],
                "adlc_stage": step["adlc_stage"],
                "agent": step["agent"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 64
    if sys.argv[1] == "list":
        return cmd_list()
    if sys.argv[1] == "show":
        return cmd_show()
    if sys.argv[1] == "begin" and len(sys.argv) >= 3:
        return cmd_begin(int(sys.argv[2]))
    if sys.argv[1] == "step" and len(sys.argv) >= 3:
        return cmd_begin(int(sys.argv[2]))
    print(__doc__)
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
