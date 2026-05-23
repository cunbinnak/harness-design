"""
Load, validate, and mutate harness/STATE.json per STATE-MACHINE.json.

Usage:
  python scripts/state_engine.py show
  python scripts/state_engine.py validate
  python scripts/state_engine.py transition <trigger>
  python scripts/state_engine.py set <dot.path> <json-value>
  python scripts/state_engine.py register-boundary <json-boundary-row>
  python scripts/state_engine.py materialize-boundary <boundary_id>
  python scripts/state_engine.py spawn-begin <boundary> <kind> <agent_file>
  python scripts/state_engine.py spawn-end
  python scripts/state_engine.py can-command <command_id>
  python scripts/state_engine.py complete-command <command_id> [evidence-json]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from harness_lib import (
    FEAT_RE,
    KINDS,
    WAVE_ID_RE,
    boundary_ids,
    copy_handoff_template,
    get_boundary,
    kg_template,
    load_json,
    load_matrix,
    repo_root,
    save_json,
    save_matrix,
    save_yaml,
    utc_now_iso,
)

SUPPORTED_VERSION = 2
STAGES = frozenset({
    "BOOTSTRAP",
    "REQUIREMENT_INTAKE",
    "BUSINESS_ANALYSIS",
    "TECHNICAL_DESIGN",
    "IMPLEMENTATION_PLAN",
    "IMPLEMENTATION",
    "SELF_REVIEW",
    "SPECIALIST_TESTING",
    "BUG_LOGGING",
    "FIX_MANUAL_BUGS",
    "RELEASE_CANDIDATE",
    "DONE",
})


def state_path() -> Path:
    return repo_root() / "harness" / "STATE.json"


def machine_path() -> Path:
    return repo_root() / "harness" / "STATE-MACHINE.json"


def load_state() -> dict[str, Any]:
    path = state_path()
    if not path.is_file():
        raise FileNotFoundError(f"STATE.json missing: {path}")
    return load_json(path)


def load_machine() -> dict[str, Any]:
    return load_json(machine_path())


def save_state(state: dict[str, Any], *, updated_by: str = "script") -> None:
    state["meta"]["revision"] = int(state["meta"].get("revision", 0)) + 1
    state["meta"]["updated_at"] = utc_now_iso()
    state["meta"]["updated_by"] = updated_by
    save_json(state_path(), state)


def validate_state(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    allowed_b = boundary_ids()

    def err(m: str) -> None:
        errors.append(m)

    if state.get("version") != SUPPORTED_VERSION:
        err(f"version must be {SUPPORTED_VERSION}")

    proj = state.get("project")
    if not isinstance(proj, dict) or not proj.get("id"):
        err("project.id required")

    stage = state.get("stage")

    wave = state.get("wave")
    if not isinstance(wave, dict):
        err("wave object required")
    else:
        wid = wave.get("id")
        num = wave.get("number")
        if stage != "BOOTSTRAP":
            if not wid or not WAVE_ID_RE.match(str(wid)):
                err("wave.id must match wave-NNN when not BOOTSTRAP")
            if not isinstance(num, int) or num < 1:
                err("wave.number must be int >= 1 when not BOOTSTRAP")
            if wid and isinstance(num, int):
                suffix = str(wid).split("-", 1)[-1]
                try:
                    if int(suffix) != num:
                        err("wave.id suffix must match wave.number")
                except ValueError:
                    err("wave.id suffix not numeric")

    if stage not in STAGES:
        err(f"stage must be one of {sorted(STAGES)}")

    prev = state.get("previous_stage")
    if prev is not None and prev not in STAGES:
        err("previous_stage invalid")

    for key in ("features_in_flight", "boundaries_in_flight", "non_negotiables"):
        if not isinstance(state.get(key), list):
            err(f"{key} must be array")

    for feat in state.get("features_in_flight") or []:
        if not FEAT_RE.match(feat):
            err(f"invalid feature id: {feat}")

    for b in state.get("boundaries_in_flight") or []:
        if b not in allowed_b:
            err(f"invalid boundary (not in matrix): {b}")

    if not isinstance(state.get("owned_paths"), list):
        err("owned_paths must be array")
    ctx = state.get("context")
    if ctx is not None and not isinstance(ctx, dict):
        err("context must be object")
    ab = state.get("active_boundary")
    if ab is not None and ab not in allowed_b:
        err(f"invalid active_boundary: {ab}")

    spawn = state.get("spawn") or {}
    active = spawn.get("active")
    if active is not None:
        if active.get("kind") not in KINDS:
            err("spawn.active.kind invalid")
        if not active.get("boundary"):
            err("spawn.active.boundary required when active")

    meta = state.get("meta")
    if not isinstance(meta, dict):
        err("meta required")
    elif meta.get("revision") is None:
        err("meta.revision required")

    wf = state.get("workflow")
    if wf is not None and not isinstance(wf, dict):
        err("workflow must be object")
    elif isinstance(wf, dict):
        if not isinstance(wf.get("allowed_next"), list):
            err("workflow.allowed_next must be array")
        if not isinstance(wf.get("completed"), list):
            err("workflow.completed must be array")

    return errors


def apply_transition(trigger: str, *, updated_by: str = "script") -> dict[str, Any]:
    state = load_state()
    errors = validate_state(state)
    if errors:
        raise ValueError("STATE invalid:\n  - " + "\n  - ".join(errors))

    machine = load_machine()
    stage = state["stage"]
    found = None
    for t in machine.get("transitions", []):
        if t.get("from") == stage and t.get("trigger") == trigger:
            found = t
            break
    if not found:
        raise ValueError(
            f"No transition for stage={stage!r} trigger={trigger!r}"
        )

    new_stage = found["to"]
    state["previous_stage"] = stage
    state["stage"] = new_stage

    if trigger == "start_wave":
        if state["wave"].get("started_at") is None:
            state["wave"]["started_at"] = utc_now_iso()
        if not state["wave"].get("id"):
            state["wave"]["id"] = "wave-001"
            state["wave"]["number"] = 1
        wid = state["wave"]["id"]
        hf = copy_handoff_template(wid)
        state["handoff"] = {"file": str(hf.relative_to(repo_root())).replace("\\", "/"), "last_sync_at": None}

    if trigger == "release_ok":
        state["wave"]["completed_at"] = utc_now_iso()
        state.setdefault("spawn", {})["active"] = None

    if trigger == "reset_wave":
        state["wave"] = {
            "id": None,
            "number": None,
            "title": None,
            "started_at": None,
            "completed_at": None,
        }
        state["boundaries_in_flight"] = []
        state["features_in_flight"] = []
        state["owned_paths"] = []
        state["active_boundary"] = None
        state.setdefault("spawn", {})["active"] = None
        state["handoff"] = {"file": None, "last_sync_at": None}

    save_state(state, updated_by=updated_by)
    return state


def set_by_path(state: dict[str, Any], dot_path: str, value: Any) -> None:
    parts = dot_path.split(".")
    cur: Any = state
    for p in parts[:-1]:
        if p not in cur:
            cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = value


def register_boundary(row: dict[str, Any]) -> dict[str, Any]:
    bid = row.get("boundary_id")
    if not bid:
        raise ValueError("boundary_id required")
    matrix = load_matrix()
    boundaries = matrix.setdefault("boundaries", [])
    if any(b.get("boundary_id") == bid for b in boundaries):
        raise ValueError(f"boundary already registered: {bid}")

    root = repo_root()
    kg_path = row.get("knowledge_graph") or f"knowledge-base/{bid}.knowledge-graph.yaml"
    agent_path = row.get("agent") or f"agents/{bid}-agent.md"
    materialized = row.get("materialized_path") or f"services/{bid}/"
    owned = row.get("owned_paths") or [f"services/{bid}/**"]

    entry = {
        "boundary_id": bid,
        "display_name": row.get("display_name", bid),
        "kind": row.get("kind", "backend"),
        "agent": agent_path,
        "knowledge_graph": kg_path,
        "materialized_path": materialized,
        "owned_paths": owned,
    }
    boundaries.append(entry)
    save_matrix(matrix)

    kg_file = root / kg_path
    if not kg_file.exists():
        data = kg_template()
        data["boundary_id"] = bid
        save_yaml(kg_file, data)

    agent_file = root / agent_path
    if not agent_file.exists():
        tpl = root / "agents" / "_template.agent.md"
        if tpl.is_file():
            text = tpl.read_text(encoding="utf-8")
            text = text.replace("{boundary_id}", bid)
            agent_file.write_text(text, encoding="utf-8")

    return entry


def materialize_boundary(boundary_id: str) -> Path:
    row = get_boundary(boundary_id)
    if not row:
        raise ValueError(f"boundary not in matrix: {boundary_id}")
    root = repo_root()
    rel = row.get("materialized_path", f"services/{boundary_id}/")
    path = root / rel
    path.mkdir(parents=True, exist_ok=True)
    readme = path / "README.md"
    if not readme.exists():
        readme.write_text(
            f"# {boundary_id}\n\nMaterialized by harness. Boundary: `{boundary_id}`.\n",
            encoding="utf-8",
        )
    return path


def spawn_begin(
    boundary: str,
    kind: str,
    agent_file: str,
    *,
    updated_by: str = "script",
) -> dict[str, Any]:
    state = load_state()
    errors = validate_state(state)
    if errors:
        raise ValueError("STATE invalid:\n  - " + "\n  - ".join(errors))

    allowed = (state.get("spawn") or {}).get("allowed_stages") or []
    if state["stage"] not in allowed:
        raise ValueError(
            f"spawn not allowed in stage={state['stage']!r}; allowed={allowed}"
        )
    if state["wave"].get("completed_at"):
        raise ValueError("wave already completed")
    if (state.get("spawn") or {}).get("active"):
        raise ValueError("spawn.active already set; call spawn-end first")
    if boundary not in boundary_ids():
        raise ValueError(f"unknown boundary (register in matrix first): {boundary}")
    if kind not in KINDS:
        raise ValueError(f"unknown kind: {kind}")

    row = get_boundary(boundary)
    state["active_boundary"] = boundary
    state["owned_paths"] = list(row.get("owned_paths", [])) if row else []

    state.setdefault("spawn", {})["active"] = {
        "boundary": boundary,
        "kind": kind,
        "agent_file": agent_file,
        "frozen_at": utc_now_iso(),
        "prompt_hash": None,
    }
    if boundary not in state["boundaries_in_flight"]:
        state["boundaries_in_flight"] = list(state["boundaries_in_flight"]) + [
            boundary
        ]

    save_state(state, updated_by=updated_by)
    return state


def spawn_end(*, updated_by: str = "script") -> dict[str, Any]:
    state = load_state()
    state.setdefault("spawn", {})["active"] = None
    save_state(state, updated_by=updated_by)
    return state


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(__doc__)
        return 64

    cmd = argv[0]
    try:
        if cmd == "show":
            print(json.dumps(load_state(), indent=2, ensure_ascii=False))
            return 0
        if cmd == "validate":
            errors = validate_state(load_state())
            if errors:
                print("INVALID:", file=sys.stderr)
                for e in errors:
                    print(f"  - {e}", file=sys.stderr)
                return 1
            print("OK: STATE.json valid (version 2)")
            return 0
        if cmd == "transition" and len(argv) >= 2:
            state = apply_transition(argv[1])
            print(f"stage -> {state['stage']}")
            return 0
        if cmd == "set" and len(argv) >= 3:
            state = load_state()
            value = json.loads(argv[2])
            set_by_path(state, argv[1], value)
            errs = validate_state(state)
            if errs:
                raise ValueError("\n  - ".join(errs))
            save_state(state)
            print(f"set {argv[1]}")
            return 0
        if cmd == "register-boundary" and len(argv) >= 2:
            row = json.loads(argv[1])
            entry = register_boundary(row)
            print(f"registered: {entry['boundary_id']}")
            return 0
        if cmd == "materialize-boundary" and len(argv) >= 2:
            path = materialize_boundary(argv[1])
            print(f"materialized: {path}")
            return 0
        if cmd == "spawn-begin" and len(argv) >= 4:
            state = spawn_begin(argv[1], argv[2], argv[3])
            print(f"spawn active: {state['spawn']['active']['boundary']}")
            return 0
        if cmd == "spawn-end":
            spawn_end()
            print("spawn cleared")
            return 0
        if cmd == "can-command" and len(argv) >= 2:
            from workflow_engine import can_command

            print(json.dumps(can_command(argv[1]), indent=2, ensure_ascii=False))
            return 0
        if cmd == "complete-command" and len(argv) >= 2:
            from workflow_engine import complete_command

            evidence = json.loads(argv[2]) if len(argv) >= 3 else {}
            state = complete_command(argv[1], evidence)
            print(
                json.dumps(
                    {
                        "command": argv[1],
                        "stage": state["stage"],
                        "allowed_next": state["workflow"]["allowed_next"],
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 0
    except (ValueError, FileNotFoundError, json.JSONDecodeError, RuntimeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(__doc__)
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
