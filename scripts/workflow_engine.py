"""Command workflow: complete-command, can-command, STATE.workflow."""

from __future__ import annotations

from typing import Any

from build_context import build_context
from gate_runner import allowed_next, check_command, load_gates
from harness_lib import utc_now_iso, load_json, repo_root
from state_engine import (
    apply_transition,
    load_state,
    save_state,
    validate_state,
)


def _enforce_pre_complete_hooks(
    command_id: str, evidence: dict[str, Any], state: dict[str, Any]
) -> None:
    rules_path = repo_root() / "harness" / "HOOK-RULES.json"
    rules = load_json(rules_path) if rules_path.is_file() else {}

    from hooks.workflow_allowed import check as wf_check  # noqa: WPS433

    ok, msg = wf_check(command_id, state)
    if not ok:
        raise ValueError(msg)

    from hooks.evidence_schema import check as ev_check  # noqa: WPS433

    ok, msg = ev_check(command_id, evidence, rules.get("command_evidence_schema", {}))
    if not ok:
        raise ValueError(msg)


def ensure_workflow(state: dict[str, Any]) -> dict[str, Any]:
    if "workflow" not in state or not isinstance(state["workflow"], dict):
        state["workflow"] = {
            "last_completed": None,
            "completed": [],
            "allowed_next": ["intake-requirement"],
            "evidence": {},
        }
    wf = state["workflow"]
    wf.setdefault("completed", [])
    wf.setdefault("allowed_next", ["intake-requirement"])
    wf.setdefault("evidence", {})
    return state


def _checkpoint_append(
    state: dict[str, Any], command_id: str, status: str, evidence: dict[str, Any]
) -> None:
    state.setdefault("checkpoints", []).append(
        {
            "command": command_id,
            "at": utc_now_iso(),
            "status": status,
            "evidence": evidence,
        }
    )


def _apply_sets_stage(state: dict[str, Any], stage: str | None) -> None:
    if stage:
        state["previous_stage"] = state.get("stage")
        state["stage"] = stage


def _wave_bootstrap(command_id: str, evidence: dict[str, Any]) -> None:
    state = load_state()
    if state["stage"] == "BOOTSTRAP" or not state["wave"].get("id"):
        apply_transition("start_wave", updated_by=command_id)
        state = load_state()
        title = evidence.get("wave_title")
        if title:
            state["wave"]["title"] = title
            save_state(state, updated_by=command_id)


def _sync_state_fields(state: dict[str, Any], evidence: dict[str, Any], sync_cfg: dict[str, str]) -> None:
    for state_key, evidence_key in sync_cfg.items():
        if evidence_key in evidence:
            state[state_key] = list(evidence[evidence_key]) if isinstance(evidence[evidence_key], list) else evidence[evidence_key]


def complete_command(
    command_id: str,
    evidence: dict[str, Any] | None = None,
    *,
    updated_by: str = "script",
) -> dict[str, Any]:
    evidence = evidence or {}
    state = ensure_workflow(load_state())
    wf = state["workflow"]
    if command_id not in wf.get("allowed_next", []):
        raise ValueError(
            f"command {command_id!r} not allowed; allowed_next={wf.get('allowed_next')}"
        )

    _enforce_pre_complete_hooks(command_id, evidence, state)

    cfg_all = load_gates()
    cmd_cfg = cfg_all["commands"][command_id]

    if cmd_cfg.get("wave_bootstrap"):
        _wave_bootstrap(command_id, evidence)
        state = ensure_workflow(load_state())

    if cmd_cfg.get("load_wave_roster"):
        wave_id = (state.get("wave") or {}).get("id") or "wave-001"
        import load_wave_roster as lwr  # noqa: WPS433

        lwr.load_for_wave(wave_id)
        state = ensure_workflow(load_state())

    if cmd_cfg.get("run_sync_matrix"):
        import sync_matrix_from_roster as sm  # noqa: WPS433

        sm.sync_from_roster()
        state = ensure_workflow(load_state())

    errors = validate_state(load_state())
    if errors:
        raise ValueError("STATE invalid:\n  - " + "\n  - ".join(errors))
    state = ensure_workflow(load_state())

    result = check_command(command_id, state, evidence)
    if not result["ok"]:
        _checkpoint_append(state, command_id, "fail", evidence)
        wf["evidence"][command_id] = evidence
        save_state(state, updated_by=updated_by)
        raise ValueError("Gates failed:\n  - " + "\n  - ".join(result["errors"]))

    branch = result.get("branch")
    branch_cfg = None
    if branch and cmd_cfg.get("branches"):
        branch_cfg = cmd_cfg["branches"].get(branch)

    sets_stage = cmd_cfg.get("sets_stage")
    next_allowed = list(cmd_cfg.get("next_allowed") or [])
    trigger = cmd_cfg.get("transition_trigger")

    if branch_cfg:
        if branch_cfg.get("sets_stage"):
            sets_stage = branch_cfg["sets_stage"]
        if branch_cfg.get("transition_trigger"):
            trigger = branch_cfg["transition_trigger"]
        if branch_cfg.get("next_allowed"):
            next_allowed = list(branch_cfg["next_allowed"])

    wf["evidence"][command_id] = evidence
    _checkpoint_append(state, command_id, "pass", evidence)

    completed = list(wf.get("completed") or [])
    if command_id not in completed:
        completed.append(command_id)
    wf["completed"] = completed
    wf["last_completed"] = command_id
    wf["allowed_next"] = next_allowed

    if sets_stage and trigger:
        try:
            state = apply_transition(trigger, updated_by=updated_by)
            state = ensure_workflow(load_state())
            if state["stage"] != sets_stage:
                _apply_sets_stage(state, sets_stage)
        except ValueError:
            _apply_sets_stage(state, sets_stage)
    elif sets_stage:
        _apply_sets_stage(state, sets_stage)
    elif trigger:
        state = apply_transition(trigger, updated_by=updated_by)
        state = ensure_workflow(load_state())

    state = ensure_workflow(load_state())
    wf = state["workflow"]
    wf["evidence"][command_id] = evidence
    wf["completed"] = completed
    wf["last_completed"] = command_id
    wf["allowed_next"] = next_allowed

    sync_cfg = cmd_cfg.get("sync_state")
    if sync_cfg:
        _sync_state_fields(state, evidence, sync_cfg)

    if sync_cfg:
        _sync_state_fields(state, evidence, sync_cfg)

    if cmd_cfg.get("post_reset_wave"):
        state = apply_transition("reset_wave", updated_by=updated_by)
        state = ensure_workflow(load_state())
        state["workflow"]["allowed_next"] = ["intake-requirement"]
        state["workflow"]["completed"] = []
        state["workflow"]["last_completed"] = None

    save_state(state, updated_by=updated_by)

    if cmd_cfg.get("run_build_context"):
        try:
            build_context()
        except Exception:
            pass

    return load_state()


def can_command(command_id: str) -> dict[str, Any]:
    state = ensure_workflow(load_state())
    in_list = command_id in allowed_next(state)
    gate = check_command(command_id, state, (state.get("workflow") or {}).get("evidence", {}).get(command_id))
    return {
        "command": command_id,
        "allowed_next": allowed_next(state),
        "in_allowed_next": in_list,
        "gates_ok": gate["ok"] if in_list else False,
        "errors": [] if in_list else ["not in allowed_next"] + gate.get("errors", []),
    }
