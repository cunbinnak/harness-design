"""Discipline hooks — KG blockers, kg_appended on RETURN, spawn stage."""

from __future__ import annotations

from typing import Any

from harness_lib import load_kg, repo_root


def _shared_kg_path() -> str:
    return "knowledge-base/shared.knowledge-graph.yaml"


def discipline_snapshot() -> dict[str, Any]:
    root = repo_root()
    rel = _shared_kg_path()
    if not (root / rel).is_file():
        return {"blockers": [], "in_progress": [], "do_not_repeat": []}
    data = load_kg(rel)
    disc = data.get("discipline") or {}
    learn = data.get("learnings") or {}
    impl = data.get("implementation") or {}
    return {
        "blockers": list(disc.get("blockers") or []),
        "in_progress": list(impl.get("in_progress") or []),
        "do_not_repeat": list(disc.get("do_not_repeat") or [])
        + list(learn.get("gotchas") or []),
    }


def check_blockers(
    state: dict[str, Any],
    hook_cfg: dict[str, Any],
    *,
    context: str = "tiếp tục",
) -> tuple[bool, str]:
    except_cmds = hook_cfg.get("except_commands") or []
    wf = state.get("workflow") or {}
    if wf.get("last_completed") in except_cmds:
        return True, "OK"
    snap = discipline_snapshot()
    blockers = snap["blockers"]
    if blockers:
        return (
            False,
            "HARNESS — KG discipline.blockers đang chặn:\n"
            + "\n".join(f"  - {b}" for b in blockers)
            + f"\nGỡ blocker (knowledge_writer.py blocker) hoặc CR trước khi {context}.",
        )
    return True, "OK"


def check_kg_return(body: dict[str, Any], hook_cfg: dict[str, Any]) -> tuple[bool, str]:
    triggers = hook_cfg.get("requires_kg_when") or ["files_changed", "completed"]
    fired = False
    for key in triggers:
        val = body.get(key)
        if isinstance(val, list) and len(val) > 0:
            fired = True
            break
    if not fired:
        return True, "OK"

    kg = body.get("kg_appended")
    if isinstance(kg, list) and len(kg) > 0:
        return True, "OK"

    deferred = body.get("deferred") or []
    if deferred and all(
        isinstance(d, dict) and d.get("tracked_in") for d in deferred
    ):
        return True, "OK"

    return (
        False,
        "RETURN SCHEMA: khi files_changed hoặc completed không rỗng, "
        "bắt buộc kg_appended (vd. decision:DEC-001) hoặc deferred[].tracked_in. "
        "Ghi KG: py scripts/knowledge_writer.py decision|do-not-repeat ...",
    )


def check_spawn_stage(state: dict[str, Any], hook_cfg: dict[str, Any]) -> tuple[bool, str]:
    allowed = (state.get("spawn") or {}).get("allowed_stages") or []
    stage = state.get("stage")
    if not allowed:
        return True, "OK"
    if stage not in allowed:
        return (
            False,
            f"spawn không được phép ở stage={stage!r}; "
            f"allowed_stages={allowed!r} (xem STATE-MACHINE / command hiện tại).",
        )
    return True, "OK"
