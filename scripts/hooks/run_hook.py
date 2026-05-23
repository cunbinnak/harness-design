#!/usr/bin/env python3
"""Run a harness hook by id. Usage: python scripts/hooks/run_hook.py <hook_id> [--payload json]"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPTS))

from harness_lib import load_json, repo_root  # noqa: E402
from state_engine import load_state  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("hook_id")
    parser.add_argument("--payload", default="{}")
    args = parser.parse_args()

    rules = load_json(repo_root() / "harness" / "HOOK-RULES.json")
    hook = rules.get("hooks", {}).get(args.hook_id)
    if not hook:
        print(f"unknown hook: {args.hook_id}", file=sys.stderr)
        return 64

    payload = json.loads(args.payload)
    state = load_state()

    if args.hook_id == "owned_paths":
        from hooks.owned_paths import check  # noqa: WPS433

        path = payload.get("path", "")
        ok, msg = check(path, state, hook)
        if not ok:
            print(msg, file=sys.stderr)
            return 1
        print("OK")
        return 0

    if args.hook_id == "return_schema":
        from hooks.return_schema import check  # noqa: WPS433

        ok, msg = check(payload.get("body"), hook)
        if not ok:
            print(msg, file=sys.stderr)
            return 1
        print("OK")
        return 0

    if args.hook_id == "transition_gate":
        from gate_runner import check_command  # noqa: WPS433

        cmd = payload.get("command")
        evidence = payload.get("evidence", {})
        if not cmd:
            print("payload.command required", file=sys.stderr)
            return 64
        result = check_command(cmd, state, evidence)
        if not result["ok"]:
            for e in result["errors"]:
                print(e, file=sys.stderr)
            return 1
        print("OK")
        return 0

    if args.hook_id == "spawn_active":
        if (state.get("spawn") or {}).get("active"):
            print("spawn.active must be null", file=sys.stderr)
            return 1
        print("OK")
        return 0

    if args.hook_id == "wave_open":
        cmd = payload.get("command", "")
        if cmd in hook.get("except_commands", []):
            print("OK")
            return 0
        if state.get("wave", {}).get("completed_at"):
            print("wave already completed", file=sys.stderr)
            return 1
        print("OK")
        return 0

    if args.hook_id == "workflow_allowed_next":
        from hooks.workflow_allowed import check  # noqa: WPS433

        cmd = payload.get("command")
        if not cmd:
            print("payload.command required", file=sys.stderr)
            return 64
        ok, msg = check(cmd, state)
        if not ok:
            print(msg, file=sys.stderr)
            return 1
        print("OK")
        return 0

    if args.hook_id == "evidence_schema":
        from hooks.evidence_schema import check as ev_check  # noqa: WPS433

        cmd = payload.get("command")
        evidence = payload.get("evidence", {})
        schemas = rules.get("command_evidence_schema", {})
        ok, msg = ev_check(cmd or "", evidence, schemas)
        if not ok:
            print(msg, file=sys.stderr)
            return 1
        print("OK")
        return 0

    if args.hook_id == "dev_agent_spawn":
        from hooks.dev_agent_spawn import check as dev_check  # noqa: WPS433

        ok, msg = dev_check(
            payload.get("command", ""),
            payload.get("boundary_id", ""),
            hook,
        )
        if not ok:
            print(msg, file=sys.stderr)
            return 1
        print("OK")
        return 0

    print(f"hook {args.hook_id} not wired in run_hook.py", file=sys.stderr)
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
