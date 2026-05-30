"""
STATE manager for ADLC Design Harness.

Reads/writes harness/STATE.json, validates against harness/STATE-MACHINE.json,
applies transitions, and appends audit history.

This module CONTAINS side effects (file I/O). Pure gate logic lives in gates.py.

CLI:
  py scripts/state.py show
  py scripts/state.py validate
  py scripts/state.py can <command>
  py scripts/state.py complete <command> '<evidence-json>'
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import gates

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = REPO_ROOT / "harness" / "STATE.json"
MACHINE_FILE = REPO_ROOT / "harness" / "STATE-MACHINE.json"
MATRIX_FILE = REPO_ROOT / "harness" / "SERVICE-BOUNDARY-MATRIX.json"


# ========================================================================
# I/O
# ========================================================================

def load_state() -> dict:
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def load_machine() -> dict:
    return json.loads(MACHINE_FILE.read_text(encoding="utf-8"))


def save_state(state: dict, updated_by: str = "state.py") -> None:
    meta = state.setdefault("meta", {})
    meta["revision"] = int(meta.get("revision", 0)) + 1
    meta["updated_at"] = datetime.now(timezone.utc).isoformat()
    meta["updated_by"] = updated_by
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# ========================================================================
# Validation
# ========================================================================

def validate(state: dict | None = None, machine: dict | None = None) -> list[str]:
    state = state if state is not None else load_state()
    machine = machine if machine is not None else load_machine()
    errors: list[str] = []
    if state.get("stage") not in machine.get("states", {}):
        errors.append(f"stage={state.get('stage')!r} không có trong STATE-MACHINE.states")
    if state.get("version") != machine.get("version"):
        errors.append(
            f"version mismatch: STATE.version={state.get('version')} "
            f"MACHINE.version={machine.get('version')}"
        )
    return errors


# ========================================================================
# Query
# ========================================================================

def allowed_commands(state: dict | None = None, machine: dict | None = None) -> list[str]:
    state = state if state is not None else load_state()
    machine = machine if machine is not None else load_machine()
    stage = state.get("stage")
    return machine.get("states", {}).get(stage, {}).get("allowed_commands", [])


def can_run(command: str, state: dict | None = None, machine: dict | None = None) -> bool:
    return command in allowed_commands(state, machine)


def find_transition(
    command: str, state: dict | None = None, machine: dict | None = None
) -> dict | None:
    state = state if state is not None else load_state()
    machine = machine if machine is not None else load_machine()
    stage = state.get("stage")
    for t in machine.get("transitions", []):
        if t.get("from") == stage and t.get("trigger") == command:
            return t
    return None


# ========================================================================
# Complete (transition)
# ========================================================================

def complete(command: str, evidence_str: str | dict) -> dict:
    """
    Main entry: try to apply transition for `command` with given evidence.
    Returns {ok: bool, message: str, ...}.
    """
    state = load_state()
    machine = load_machine()

    # Parse evidence
    if isinstance(evidence_str, str):
        try:
            evidence = json.loads(evidence_str)
        except json.JSONDecodeError as e:
            return _err(f"Evidence JSON invalid: {e}")
    else:
        evidence = evidence_str

    if not isinstance(evidence, dict):
        return _err(f"Evidence phải là JSON object, nhận: {type(evidence).__name__}")

    # 1. Command allowed at current stage?
    if not can_run(command, state, machine):
        return _err(
            f"Command '{command}' không allowed ở stage '{state['stage']}'. "
            f"Allowed: {allowed_commands(state, machine)}"
        )

    # 2. Transition exists?
    transition = find_transition(command, state, machine)
    if transition is None:
        return _err(
            f"Không tìm thấy transition cho '{command}' từ stage '{state['stage']}'"
        )

    # 3. Gate check (pure)
    ok, errors = gates.check_for_command(command, state, evidence)
    if not ok:
        return _err("Gate failed:\n  - " + "\n  - ".join(errors))

    # 4. Apply transition
    old_stage = state["stage"]
    new_stage = transition["to"]
    state["previous_stage"] = old_stage
    state["stage"] = new_stage

    # 5. Append history
    state.setdefault("workflow", {}).setdefault("history", []).append(
        {
            "command": command,
            "at": datetime.now(timezone.utc).isoformat(),
            "from_stage": old_stage,
            "to_stage": new_stage,
            "evidence": evidence,
        }
    )
    state["workflow"]["last_completed"] = command

    # 6. Chain auto-transitions (e.g., TEST_EXECUTE -> MANUAL_TEST when test_result=pass)
    chain = _try_auto_transition(state, machine, evidence)
    transitions_msg = f"{command}: {old_stage} -> {new_stage}"
    if chain:
        transitions_msg += f" -> {chain}"

    save_state(state, updated_by=f"complete:{command}")
    return _ok(transitions_msg)


def _try_auto_transition(state: dict, machine: dict, evidence: dict) -> str | None:
    """
    After a regular transition, check if current stage has an _auto transition
    whose evidence_required is satisfied. If so, apply it. Returns the new stage
    or None if no auto-transition happened.
    """
    current = state["stage"]
    for t in machine.get("transitions", []):
        if t.get("from") != current or t.get("trigger") != "_auto":
            continue
        required = t.get("evidence_required", {})
        if _evidence_matches(evidence, required):
            old = state["stage"]
            state["previous_stage"] = old
            state["stage"] = t["to"]
            state.setdefault("workflow", {}).setdefault("history", []).append(
                {
                    "command": "_auto",
                    "at": datetime.now(timezone.utc).isoformat(),
                    "from_stage": old,
                    "to_stage": t["to"],
                    "evidence": evidence,
                }
            )
            return t["to"]
    return None


def _evidence_matches(evidence: dict, required: dict) -> bool:
    """Check evidence satisfies required dict (each key=value must match)."""
    for k, v in required.items():
        if v == "any":
            if k not in evidence or evidence[k] in (None, ""):
                return False
        elif evidence.get(k) != v:
            return False
    return True


# ========================================================================
# Helpers
# ========================================================================

def _ok(msg: str, **extra) -> dict:
    return {"ok": True, "message": msg, **extra}


def _err(msg: str, **extra) -> dict:
    return {"ok": False, "error": msg, **extra}


def summary(state: dict | None = None, machine: dict | None = None) -> dict:
    state = state if state is not None else load_state()
    machine = machine if machine is not None else load_machine()
    return {
        "stage": state.get("stage"),
        "previous_stage": state.get("previous_stage"),
        "wave": state.get("wave"),
        "active_boundary": state.get("active_boundary"),
        "wave_boundaries": state.get("wave_boundaries"),
        "allowed_commands": allowed_commands(state, machine),
        "spawn_active": state.get("spawn", {}).get("active"),
        "last_completed": state.get("workflow", {}).get("last_completed"),
        "history_count": len(state.get("workflow", {}).get("history", [])),
        "revision": state.get("meta", {}).get("revision"),
    }


# ========================================================================
# CLI
# ========================================================================

USAGE = """Usage:
  py scripts/state.py show
  py scripts/state.py validate
  py scripts/state.py can <command>
  py scripts/state.py complete <command> '<evidence-json>'
"""


def main(argv: list[str] | None = None) -> int:
    # Force UTF-8 stdout on Windows (cp1252 default breaks Unicode messages)
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(USAGE)
        return 64

    cmd = argv[0]

    if cmd == "show":
        print(json.dumps(summary(), indent=2, ensure_ascii=False))
        return 0

    if cmd == "validate":
        errors = validate()
        if errors:
            for e in errors:
                print(f"FAIL: {e}", file=sys.stderr)
            return 1
        print("OK: STATE.json valid against STATE-MACHINE.json")
        return 0

    if cmd == "can":
        if len(argv) < 2:
            print("Usage: state.py can <command>", file=sys.stderr)
            return 64
        target = argv[1]
        st = load_state()
        if can_run(target, st):
            print(f"YES: '{target}' allowed at stage={st['stage']}")
            return 0
        print(
            f"NO: '{target}' not allowed at stage={st['stage']}. "
            f"Allowed: {allowed_commands(st)}",
            file=sys.stderr,
        )
        return 1

    if cmd == "complete":
        if len(argv) < 3:
            print("Usage: state.py complete <command> '<evidence-json>'", file=sys.stderr)
            return 64
        result = complete(argv[1], argv[2])
        if result["ok"]:
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0
        print(json.dumps(result, indent=2, ensure_ascii=False), file=sys.stderr)
        return 1

    print(f"Unknown subcommand: {cmd}", file=sys.stderr)
    print(USAGE, file=sys.stderr)
    return 64


if __name__ == "__main__":
    sys.exit(main())
