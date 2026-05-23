"""Evaluate COMMAND-GATES.json for a harness command."""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any

from harness_lib import boundary_ids, expand_globs, load_json, repo_root


def gates_path() -> Path:
    return repo_root() / "harness" / "COMMAND-GATES.json"


def load_gates() -> dict[str, Any]:
    return load_json(gates_path())


def _glob_count(root: Path, pattern: str) -> int:
    return len(expand_globs(root, [pattern]))


def _check_gate(
    gate: dict[str, Any],
    *,
    root: Path,
    state: dict[str, Any],
    evidence: dict[str, Any],
    thresholds: dict[str, Any],
) -> str | None:
    gtype = gate.get("type")
    if gtype == "artifact_glob":
        n = _glob_count(root, gate["pattern"])
        if n < int(gate.get("min", 1)):
            return f"artifact_glob: need >={gate.get('min', 1)} for {gate['pattern']}, got {n}"
        return None
    if gtype == "registry_has_cases":
        pat = gate.get("pattern", "tracking/test-case-registry/**")
        n = _glob_count(root, pat)
        if n < int(gate.get("min", 1)):
            return f"registry_has_cases: need files under {pat}"
        return None
    if gtype == "matrix_non_empty":
        if not boundary_ids():
            return "matrix_non_empty: no boundaries in SERVICE-BOUNDARY-MATRIX.json"
        return None
    if gtype == "matrix_covers_roster":
        from load_wave_roster import find_roster  # noqa: WPS433
        from sync_matrix_from_roster import parse_roster_with_layer  # noqa: WPS433

        roster_path = find_roster()
        if not roster_path:
            return "matrix_covers_roster: agent-roster.md not found"
        roster_ids = {b for b, _ in parse_roster_with_layer(roster_path)}
        matrix_ids = boundary_ids() - frozenset({"reviewer"})
        missing = sorted(roster_ids - matrix_ids)
        if missing:
            return (
                f"matrix_covers_roster: SERVICE-BOUNDARY-MATRIX missing {missing} "
                f"(run: py scripts/harness.py sync-boundaries)"
            )
        return None
    if gtype == "evidence_field":
        field = gate["field"]
        val = evidence.get(field)
        if "equals" in gate and val != gate["equals"]:
            return f"evidence.{field} must equal {gate['equals']!r}, got {val!r}"
        if "in" in gate and val not in gate["in"]:
            return f"evidence.{field} must be one of {gate['in']}, got {val!r}"
        if val is None:
            return f"evidence.{field} required"
        return None
    if gtype == "coverage_min":
        field = gate.get("field", "coverage_pct")
        val = evidence.get(field)
        if val is None:
            return f"evidence.{field} required for coverage gate"
        try:
            pct = float(val)
        except (TypeError, ValueError):
            return f"evidence.{field} must be numeric"
        min_pct = float(thresholds.get("coverage_backend_pct", 80))
        if pct < min_pct:
            return f"coverage {pct}% < threshold {min_pct}%"
        return None
    if gtype == "wave_open":
        return None
    if gtype == "wave_active":
        wave = state.get("wave") or {}
        if not wave.get("id"):
            return "wave_active: wave.id required — run start-wave first"
        if wave.get("completed_at"):
            return "wave_active: wave already completed"
        return None
    if gtype == "boundary_agents_created":
        sets = _complete_dev_sets(root)
        if len(sets) < int(gate.get("min", 1)):
            return (
                f"boundary_agents_created: need >={gate.get('min', 1)} complete dev sets "
                f"({{b}}-agent, fix-{{b}}-agent, review-{{b}}-agent), got {len(sets)}"
            )
        return None
    if gtype == "dev_agent_sets_complete":
        sets = _complete_dev_sets(root)
        min_b = int(gate.get("min_boundaries", 1))
        if len(sets) < min_b:
            return (
                f"dev_agent_sets_complete: need >={min_b} boundaries with 3 agents each, got {len(sets)}: {sets}"
            )
        return None
    if gtype == "fe_agent_set_complete":
        fe_id = gate.get("boundary_id", "fe")
        if not _dev_set_complete(root, fe_id):
            return (
                f"fe_agent_set_complete: need agents/{fe_id}-agent.md, "
                f"fix-{fe_id}-agent.md, review-{fe_id}-agent.md (materialize --include-fe)"
            )
        return None
    if gtype == "wave_roster_synced":
        wf = state.get("workflow") or {}
        if not wf.get("wave_roster_loaded"):
            return "wave_roster_synced: workflow.wave_roster_loaded is false — run load_wave_roster on start-wave"
        feats = state.get("features_in_flight") or []
        bounds = state.get("boundaries_in_flight") or []
        if not bounds:
            return "wave_roster_synced: boundaries_in_flight empty after start-wave"
        return None
    if gtype == "evidence_list_min":
        field = gate["field"]
        val = evidence.get(field)
        if not isinstance(val, list) or len(val) < int(gate.get("min", 1)):
            return f"evidence.{field} must be list with >={gate.get('min', 1)} items"
        return None
    return f"unknown gate type: {gtype!r}"


def check_command(
    command_id: str,
    state: dict[str, Any],
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return {ok, errors, warnings, branch}."""
    cfg_all = load_gates()
    cmd_cfg = cfg_all.get("commands", {}).get(command_id)
    if not cmd_cfg:
        return {"ok": False, "errors": [f"unknown command: {command_id}"], "warnings": []}

    evidence = evidence or {}
    root = repo_root()
    thresholds = cfg_all.get("thresholds", {})
    errors: list[str] = []
    warnings: list[str] = []

    wf = state.get("workflow") or {}
    completed = set(wf.get("completed") or [])
    for req in cmd_cfg.get("requires_previous") or []:
        if req not in completed:
            errors.append(f"requires_previous: {req!r} not completed")

    prev_any = cmd_cfg.get("requires_previous_any")
    if prev_any and not any(p in completed for p in prev_any):
        errors.append(f"requires_previous_any: need one of {prev_any}")

    if cmd_cfg.get("requires_test_pass"):
        ev = wf.get("evidence") or {}
        passed = any(
            ev.get(c, {}).get("test_result") == "pass" for c in ("test-execute", "retest")
        ) or any(
            c.get("command") in ("test-execute", "retest")
            and c.get("status") == "pass"
            and (c.get("evidence") or {}).get("test_result") == "pass"
            for c in (state.get("checkpoints") or [])
        )
        if not passed:
            errors.append("requires_test_pass: test-execute or retest must have test_result=pass")

    wave = state.get("wave") or {}
    if wave.get("completed_at") and command_id != "intake-requirement":
        errors.append("wave already completed")

    for gate in cmd_cfg.get("gates") or []:
        msg = _check_gate(gate, root=root, state=state, evidence=evidence, thresholds=thresholds)
        if msg:
            errors.append(msg)

    branch = None
    branches = cmd_cfg.get("branches")
    if branches:
        tr = evidence.get("test_result")
        if tr in branches:
            branch = tr
            sub = branches[tr]
            for gate in sub.get("gates") or []:
                msg = _check_gate(gate, root=root, state=state, evidence=evidence, thresholds=thresholds)
                if msg:
                    errors.append(msg)
        else:
            errors.append("evidence.test_result must be 'pass' or 'fail' for branching commands")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "branch": branch,
        "config": cmd_cfg,
    }


def allowed_next(state: dict[str, Any]) -> list[str]:
    wf = state.get("workflow") or {}
    return list(wf.get("allowed_next") or ["start-wave"])


def can_run(command_id: str, state: dict[str, Any]) -> dict[str, Any]:
    nxt = allowed_next(state)
    if command_id not in nxt:
        return {
            "ok": False,
            "errors": [f"command {command_id!r} not in allowed_next: {nxt}"],
        }
    return check_command(command_id, state, (state.get("workflow") or {}).get("evidence", {}).get(command_id))


INTAKE_SPECIALIST_SUFFIXES = frozenset({
    "requirement-analyst-agent.md",
    "business-analyst-agent.md",
    "solution-architect-agent.md",
    "program-planner-agent.md",
    "intake-orchestrator-agent.md",
    "reviewer-agent.md",
    "_template.agent.md",
})

HARNESS_COMMAND_AGENT_SUFFIXES = frozenset({
    "start-wave-agent.md",
    "review-document-agent.md",
    "prepare-dev-agent.md",
    "dev-handoff-agent.md",
    "test-plan-agent.md",
    "test-execute-agent.md",
    "release-agent.md",
    "end-wave-agent.md",
})

DEV_AGENT_PREFIXES = ("", "fix-", "review-")


def _is_harness_or_intake_agent(name: str) -> bool:
    return name in INTAKE_SPECIALIST_SUFFIXES or name in HARNESS_COMMAND_AGENT_SUFFIXES


def _dev_boundary_ids(root: Path) -> list[str]:
    agents_dir = root / "agents"
    if not agents_dir.is_dir():
        return []
    out: list[str] = []
    for p in agents_dir.glob("*-agent.md"):
        if _is_harness_or_intake_agent(p.name) or p.name.startswith("fix-") or p.name.startswith("review-"):
            continue
        out.append(p.stem.replace("-agent", ""))
    return sorted(set(out))


def _dev_set_complete(root: Path, boundary_id: str) -> bool:
    agents_dir = root / "agents"
    return all(
        (agents_dir / f"{prefix}{boundary_id}-agent.md").is_file()
        for prefix in DEV_AGENT_PREFIXES
    )


def _complete_dev_sets(root: Path) -> list[str]:
    return [b for b in _dev_boundary_ids(root) if _dev_set_complete(root, b)]


def _boundary_agent_files(root: Path) -> list[Path]:
    agents_dir = root / "agents"
    if not agents_dir.is_dir():
        return []
    return [
        agents_dir / f"{prefix}{bid}-agent.md"
        for bid in _dev_boundary_ids(root)
        for prefix in DEV_AGENT_PREFIXES
        if (agents_dir / f"{prefix}{bid}-agent.md").is_file()
    ]


def path_allowed_for_edit(path: str, state: dict[str, Any], hook_cfg: dict[str, Any]) -> bool:
    norm = path.replace("\\", "/")
    prefixes = hook_cfg.get("allowlist_prefixes") or []
    if any(norm.startswith(p) for p in prefixes):
        return True
    owned = state.get("owned_paths") or []
    for op in owned:
        opn = op.replace("\\", "/")
        if opn.endswith("/**"):
            if norm.startswith(opn[:-3]):
                return True
        elif fnmatch.fnmatch(norm, opn):
            return True
    return False
