#!/usr/bin/env python3
"""Load wave roster — features + boundaries vào STATE (gọi sau start-wave).

Usage:
  py scripts/load_wave_roster.py --wave wave-001
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from harness_lib import expand_globs, repo_root
from state_engine import load_state, save_state


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def wave_doc_path(wave: str) -> Path:
    """Merged plan + assignment: docs/plans/waves/{wave}/wave.md"""
    return repo_root() / "docs/plans/waves" / wave.replace("_", "-") / "wave.md"


def find_wave_plan(wave: str) -> Path | None:
    root = repo_root()
    merged = wave_doc_path(wave)
    if merged.is_file():
        return merged
    for p in expand_globs(root, [f"docs/plans/{wave}-plan.md", "docs/plans/wave-*-plan.md"]):
        if p.name == f"{wave}-plan.md" or wave in p.name:
            return p
    return None


def find_roster() -> Path | None:
    root = repo_root()
    candidates = (
        "docs/plans/project/agent-roster.md",
        "docs/plans/project-agent-roster.md",
    )
    for name in candidates:
        p = root / name
        if p.is_file():
            return p
    return None


def parse_features_from_plan(plan_path: Path | None, wave: str) -> list[str]:
    if not plan_path:
        return []
    text = _read(plan_path)
    feats: list[str] = []
    for m in re.finditer(r"FEAT-[A-Za-z0-9_-]+", text):
        feats.append(m.group(0))
    return sorted(set(feats))


def parse_boundaries_for_wave(roster_path: Path | None, wave: str) -> list[str]:
    if not roster_path:
        return []
    from materialize_boundary_agents import parse_roster_row  # noqa: WPS433
    from wave_ids import normalize_wave_id  # noqa: WPS433

    wave = normalize_wave_id(wave)
    rows = parse_roster_row(roster_path)
    if rows:
        return sorted(
            {
                r.boundary_id
                for r in rows
                if wave in [normalize_wave_id(w) for w in r.waves]
            }
        )
    text = _read(roster_path)
    in_matrix = False
    boundaries: list[str] = []
    for line in text.splitlines():
        if "Ma trận wave" in line or "wave → boundary" in line.lower():
            in_matrix = True
            continue
        if in_matrix and "|" in line and wave in line:
            cols = [c.strip() for c in line.split("|") if c.strip()]
            if len(cols) >= 2 and cols[0].startswith("wave"):
                continue
            if len(cols) >= 2:
                for part in re.split(r"[,;]", cols[-1]):
                    b = part.strip()
                    if re.match(r"^[a-z][a-z0-9_-]*$", b):
                        boundaries.append(b)
    if boundaries:
        return sorted(set(boundaries))

    for line in text.splitlines():
        if "|" not in line or "---" in line or "boundary_id" in line:
            continue
        cols = [c.strip() for c in line.split("|") if c.strip()]
        if len(cols) >= 3 and cols[0] and re.match(r"^[a-z][a-z0-9_-]*$", cols[0]):
            if wave in cols[2]:
                boundaries.append(cols[0])
    return sorted(set(boundaries))


def list_dev_agent_files(boundaries: list[str]) -> dict[str, list[str]]:
    root = repo_root() / "agents"
    out: dict[str, list[str]] = {}
    for b in boundaries:
        files = []
        for prefix in ("", "fix-", "review-"):
            name = f"{prefix}{b}-agent.md"
            if (root / name).is_file():
                files.append(f"agents/{name}")
        out[b] = files
    return out


def apply_to_state(wave: str, features: list[str], boundaries: list[str]) -> dict:
    state = load_state()
    state["wave"] = {
        **(state.get("wave") or {}),
        "id": wave,
        "number": int(wave.split("-")[-1]) if "-" in wave else 1,
    }
    state["features_in_flight"] = features
    state["boundaries_in_flight"] = boundaries
    wf = state.setdefault("workflow", {})
    wf["wave_roster_loaded"] = True
    wf["wave_boundaries"] = boundaries
    wf["wave_features"] = features
    wf["wave_dev_agents"] = list_dev_agent_files(boundaries)
    wf["wave_doc"] = str(wave_doc_path(wave).relative_to(repo_root())).replace("\\", "/")
    save_state(state)
    return state


def load_for_wave(wave: str) -> dict:
    """Parse plan + roster and apply to STATE. Returns summary dict."""
    from wave_ids import normalize_wave_id  # noqa: WPS433

    wave = normalize_wave_id(wave)
    plan = find_wave_plan(wave)
    roster = find_roster()
    features = parse_features_from_plan(plan, wave)
    boundaries = parse_boundaries_for_wave(roster, wave)
    if not boundaries and roster:
        from materialize_boundary_agents import parse_roster

        _, boundaries = parse_roster(roster)
    state = apply_to_state(wave, features, boundaries)
    return {
        "wave": wave,
        "features": features,
        "boundaries": boundaries,
        "wave_doc": state.get("workflow", {}).get("wave_doc"),
        "state": state,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wave", default="wave-001")
    args = ap.parse_args()
    wave = args.wave.replace("_", "-")
    summary = load_for_wave(wave)
    print(
        json.dumps(
            {
                "ok": True,
                "wave": summary["wave"],
                "wave_doc": summary.get("wave_doc"),
                "features_in_flight": summary["features"],
                "boundaries_in_flight": summary["boundaries"],
                "dev_agents": summary["state"]["workflow"].get("wave_dev_agents"),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
