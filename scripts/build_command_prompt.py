#!/usr/bin/env python3
"""Build spawn prompt for a harness command.

Dev commands (start-dev, fix-bugs, review-dev) → agents/{prefix}{boundary}-agent.md (tạo lúc plan).
Các command khác → agents/{command}-agent.md cố định trong repo.

Usage:
  python scripts/build_command_prompt.py intake-requirement --step 1 --input "..."
  python scripts/build_command_prompt.py start-wave
  python scripts/build_command_prompt.py start-dev --boundary order
  python scripts/build_command_prompt.py fix-bugs --boundary order
  python scripts/build_command_prompt.py review-dev --boundary order
  python scripts/build_command_prompt.py test-execute
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from harness_lib import get_boundary, load_json, repo_root
from state_engine import load_state

INTAKE_SPECIALISTS = frozenset({
    "requirement-analyst",
    "business-analyst",
    "solution-architect",
    "program-planner",
    "intake-orchestrator",
})

COMMAND_AGENTS: dict[str, str] = {
    "start-wave": "agents/start-wave-agent.md",
    "review-document": "agents/review-document-agent.md",
    "prepare-dev": "agents/prepare-dev-agent.md",
    "dev-handoff": "agents/dev-handoff-agent.md",
    "test-plan": "agents/test-plan-agent.md",
    "test-execute": "agents/test-execute-agent.md",
    "release": "agents/release-agent.md",
    "end-wave": "agents/end-wave-agent.md",
}

DEV_COMMAND_PREFIX: dict[str, str] = {
    "start-dev": "",
    "fix-bugs": "fix-",
    "review-dev": "review-",
}

SKILL_BY_COMMAND: dict[str, str | None] = {
    "prepare-dev": "implementation-plan",
    "dev-handoff": "implementation",
    "test-plan": "specialist-testing",
    "test-execute": "specialist-testing",
    "release": "release-candidate",
    "review-document": "business-analysis",
}


def _read(path: Path, limit: int = 12000) -> str:
    if not path.is_file():
        return f"(missing: {path})"
    text = path.read_text(encoding="utf-8")
    return text[:limit] + ("…" if len(text) > limit else "")


def _state_block() -> str:
    state = load_state()
    return json.dumps(
        {
            "stage": state.get("stage"),
            "wave": state.get("wave"),
            "handoff": state.get("handoff"),
            "features_in_flight": state.get("features_in_flight"),
            "boundaries_in_flight": state.get("boundaries_in_flight"),
            "workflow": state.get("workflow"),
        },
        indent=2,
        ensure_ascii=False,
    )


def _inline_header(title: str) -> str:
    return f"\n## {title}\n\n"


def dev_agent_rel(command: str, boundary_id: str) -> str:
    prefix = DEV_COMMAND_PREFIX.get(command, "")
    return f"agents/{prefix}{boundary_id}-agent.md"


def list_dev_boundaries() -> list[str]:
    root = repo_root() / "agents"
    out: list[str] = []
    for p in sorted(root.glob("*-agent.md")):
        name = p.name
        if name.startswith("fix-") or name.startswith("review-"):
            continue
        stem = p.stem.replace("-agent", "")
        if stem in INTAKE_SPECIALISTS or stem in ("reviewer",):
            continue
        if name.startswith("_"):
            continue
        out.append(stem)
    return out


def build_intake_step(step: int, user_input: str | None) -> str:
    pipeline = load_json(repo_root() / "harness" / "INTAKE-PIPELINE.json")
    steps = {s["order"]: s for s in pipeline["steps"]}
    if step not in steps:
        raise ValueError(f"step must be 1-{len(steps)}")
    s = steps[step]
    root = repo_root()
    agent_path = root / s["agent"]
    skill_path = root / "skills" / f"{s['skill']}.skill.md"

    parts = [
        f"# INTAKE PIPELINE — step {step}/4: {s['id']}",
        "",
        "You are a fresh subagent. Complete ONLY this step.",
        "",
        _inline_header("STATE"),
        _state_block(),
    ]
    if user_input and step == 1:
        parts.extend([_inline_header("USER INPUT"), user_input, ""])
    if step > 1:
        parts.extend([
            _inline_header("PRIOR ARTIFACTS"),
            "- docs/product/PROJECT.md",
            "- docs/product/FEAT-*.md",
            "- handoff/wave-*.md",
            "- docs/architecture/hld/, api/, data-model/, ux/ (sau bước 3)",
            "",
        ])
    parts.extend([
        _inline_header("AGENT SPEC"),
        _read(agent_path),
        _inline_header("SKILL"),
        _read(skill_path),
    ])
    if step == 4:
        parts.extend([
            _inline_header("PLANS (đề xuất A — file wave gộp)"),
            "- `docs/plans/project/waves-roadmap.md`",
            "- `docs/plans/project/agent-roster.md`",
            "- `docs/plans/waves/{wave-id}/wave.md` — §1 Plan (intake); §2 Assignment để trống cho prepare-dev",
            "Template: `docs/plans/_templates/`",
            "",
            _inline_header("DEV BOUNDARY AGENTS (bắt buộc)"),
            "Với mỗi boundary_id backend từ architect, tạo **3 file** từ `agents/_template.agent.md`:",
            "- `agents/{boundary_id}-agent.md` — start-dev",
            "- `agents/fix-{boundary_id}-agent.md` — fix-bugs",
            "- `agents/review-{boundary_id}-agent.md` — review-dev",
            "",
            _inline_header("FE AGENTS (bắt buộc)"),
            "Luôn materialize boundary FE (mặc định `fe`) — thêm 3 file:",
            "- `agents/fe-agent.md`, `fix-fe-agent.md`, `review-fe-agent.md` (layer frontend)",
            "",
            "Chạy một lệnh (tự thêm FE nếu chưa có trong list):",
            "`py scripts/materialize_boundary_agents.py --boundaries order,product --wave wave-001`",
            "",
            "Ghi roster (backend + fe). RETURN: `boundaries_created` gồm cả `fe`.",
            "",
        ])
    parts.extend([_inline_header("RETURN"), "JSON only per harness/PROTOCOL.md."])
    return "\n".join(parts)


def build_command_agent(command: str) -> str:
    root = repo_root()
    agent_rel = COMMAND_AGENTS.get(command)
    if not agent_rel:
        raise ValueError(f"no fixed agent for command {command!r}")
    parts = [
        f"# COMMAND: {command}",
        "",
        _inline_header("STATE"),
        _state_block(),
        _inline_header("AGENT SPEC"),
        _read(root / agent_rel),
    ]
    skill = SKILL_BY_COMMAND.get(command)
    if skill:
        parts.extend([_inline_header("SKILL"), _read(root / "skills" / f"{skill}.skill.md")])
    if command == "start-wave":
        parts.extend([
            _inline_header("WAVE ROSTER (sẽ nạp khi complete)"),
            "Sau complete, harness gọi load_wave_roster — đọc:",
            "- docs/plans/project/agent-roster.md",
            "- docs/plans/waves/{wave-id}/wave.md → features_in_flight",
            "",
        ])
    if command == "review-document":
        parts.extend([
            _inline_header("PIPELINE TRACE"),
            "Handoff Intake pipeline + kiểm tra bộ 3 dev agents/boundary (backend + FE `fe`).",
            "",
        ])
    parts.extend([_inline_header("RETURN"), "JSON only per harness/PROTOCOL.md."])
    return "\n".join(parts)


def build_dev_command(command: str, boundary_id: str) -> str:
    root = repo_root()
    agent_rel = dev_agent_rel(command, boundary_id)
    agent_path = root / agent_rel
    if not agent_path.is_file():
        raise ValueError(
            f"missing {agent_rel}. Run intake step 4 or "
            f"materialize_boundary_agents.py --boundaries {boundary_id}"
        )
    row = get_boundary(boundary_id)
    kg = (row or {}).get("knowledge_graph", f"knowledge-base/{boundary_id}.knowledge-graph.yaml")

    parts = [
        f"# COMMAND: {command} — boundary {boundary_id}",
        "",
        _inline_header("STATE"),
        _state_block(),
        _inline_header("BOUNDARY DEV AGENT"),
        _read(agent_path),
        _inline_header("KNOWLEDGE GRAPH"),
        _read(root / kg, limit=8000),
        _inline_header("CONTEXT"),
        "Wave plan, FEAT in flight, architecture — chỉ sửa owned_paths từ matrix.",
        _inline_header("RETURN"),
        "JSON only per PROTOCOL.md.",
    ]
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build command prompt to stdout")
    parser.add_argument("command")
    parser.add_argument("--step", type=int, help="Intake step 1-4")
    parser.add_argument("--input", help="User input for intake step 1")
    parser.add_argument("--boundary", help="boundary_id for dev commands")
    parser.add_argument("--list-boundaries", action="store_true")
    args = parser.parse_args()

    if args.list_boundaries:
        for b in list_dev_boundaries():
            print(b)
        return 0

    cmd = args.command
    try:
        if cmd == "intake-requirement":
            if not args.step:
                print("intake-requirement requires --step 1|2|3|4", file=sys.stderr)
                return 64
            sys.stdout.write(build_intake_step(args.step, args.input))
            return 0
        if cmd in DEV_COMMAND_PREFIX:
            if not args.boundary:
                avail = ", ".join(list_dev_boundaries()) or "(none)"
                print(f"Available boundaries: {avail}", file=sys.stderr)
                print(f"Usage: ... {cmd} --boundary <id>", file=sys.stderr)
                return 64
            sys.stdout.write(build_dev_command(cmd, args.boundary))
            return 0
        if cmd in COMMAND_AGENTS:
            sys.stdout.write(build_command_agent(cmd))
            return 0
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(f"Unknown command: {cmd}", file=sys.stderr)
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
