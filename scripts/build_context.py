"""Build STATE.context (skills, docs, agents, knowledge_graphs) for current stage."""

from __future__ import annotations

import sys

from harness_lib import (
    STAGE_DOC_GLOBS,
    expand_globs,
    get_boundary,
    load_machine,
    repo_root,
    skill_for_stage,
)
from state_engine import load_state, save_state, validate_state


def build_context() -> dict:
    state = load_state()
    stage = state.get("stage", "BOOTSTRAP")
    machine = load_machine()
    root = repo_root()

    ctx = state.setdefault("context", {})
    skills: list[str] = []
    sk = skill_for_stage(stage, machine)
    if sk:
        skills.append(sk)
    ctx["skills"] = skills

    docs: list[str] = []
    for pat in STAGE_DOC_GLOBS.get(stage, []):
        docs.extend(expand_globs(root, [pat]))
    ctx["docs"] = sorted(set(docs))

    kgs = ["knowledge-base/shared.knowledge-graph.yaml"]
    ab = state.get("active_boundary")
    if ab:
        row = get_boundary(ab)
        if row and row.get("knowledge_graph"):
            kgs.append(row["knowledge_graph"])
    else:
        for bid in state.get("boundaries_in_flight") or []:
            row = get_boundary(bid)
            if row and row.get("knowledge_graph"):
                kgs.append(row["knowledge_graph"])
    ctx["knowledge_graphs"] = sorted(set(kgs))

    agents: list[str] = []
    if ab:
        row = get_boundary(ab)
        if row and row.get("agent"):
            agents.append(row["agent"])
    ctx["agents"] = agents

    hf = (state.get("handoff") or {}).get("file")
    if hf:
        p = root / hf
        if p.is_file() and hf not in ctx["docs"]:
            ctx["docs"] = sorted(set(ctx["docs"]) + [hf.replace("\\", "/")])

    errs = validate_state(state)
    if errs:
        raise ValueError("STATE invalid after build_context:\n  - " + "\n  - ".join(errs))
    save_state(state)
    return ctx


def main() -> None:
    try:
        ctx = build_context()
        print(f"stage={load_state()['stage']}")
        print(f"skills={ctx.get('skills')}")
        print(f"docs={len(ctx.get('docs', []))} paths")
        print(f"knowledge_graphs={ctx.get('knowledge_graphs')}")
    except (ValueError, RuntimeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
