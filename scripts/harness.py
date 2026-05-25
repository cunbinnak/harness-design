"""Harness CLI — command workflow theo COMMAND-GATES.json.

Usage:
  python scripts/harness.py can intake-requirement
  python scripts/harness.py complete dev-handoff evidence.json
  python scripts/harness.py intake-requirement complete evidence.json
  python scripts/harness.py register-boundary catalog-api --materialize
  python scripts/harness.py state
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

CORE = [
    "intake-requirement",
    "review-document",
    "start-wave",
    "start-dev",
    "review-dev",
    "dev-handoff",
    "test-plan",
    "test-execute",
]
EXTENDED = ["apply-cr", "register-boundary", "fix-bugs", "retest", "release", "end-wave", "done-wave"]
ALL = CORE + EXTENDED


def _scripts() -> Path:
    return Path(__file__).resolve().parent


def _py() -> str:
    return sys.executable


def _run(args: list[str]) -> int:
    return subprocess.call([_py(), *args], cwd=str(_scripts().parent))


def cmd_state() -> int:
    r = _run([str(_scripts() / "state_engine.py"), "validate"])
    if r != 0:
        return r
    return _run([str(_scripts() / "state_engine.py"), "show"])


def cmd_can(command: str) -> int:
    return _run([str(_scripts() / "state_engine.py"), "can-command", command])


def cmd_complete(command: str, evidence_path: str | None) -> int:
    evidence = "{}"
    if evidence_path and Path(evidence_path).is_file():
        evidence = Path(evidence_path).read_text(encoding="utf-8")
    return _run(
        [str(_scripts() / "state_engine.py"), "complete-command", command, evidence]
    )


def cmd_register(boundary_id: str, materialize: bool) -> int:
    payload = json.dumps(
        {
            "boundary_id": boundary_id,
            "display_name": boundary_id.replace("-", " ").title(),
            "kind": "backend",
        },
        ensure_ascii=False,
    )
    r = _run([str(_scripts() / "state_engine.py"), "register-boundary", payload])
    if r != 0:
        return r
    if materialize:
        r = _run(
            [str(_scripts() / "state_engine.py"), "materialize-boundary", boundary_id]
        )
        if r != 0:
            return r
    return cmd_complete("register-boundary", None)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nCommands:", ", ".join(ALL))
        return 64

    verb = sys.argv[1]
    rest = sys.argv[2:]

    if verb in ("state", "show-state"):
        return cmd_state()
    if verb == "can" and rest:
        return cmd_can(rest[0])
    if verb == "complete" and rest:
        ev = rest[1] if len(rest) > 1 else None
        return cmd_complete(rest[0], ev)
    if verb == "register-boundary" and rest:
        mat = "--materialize" in rest
        bid = rest[0]
        return cmd_register(bid, mat)
    if verb in ALL:
        if rest and rest[0] == "complete":
            ev = rest[1] if len(rest) > 1 else None
            return cmd_complete(verb, ev)
        if rest and rest[0] == "can":
            return cmd_can(verb)
        print(f"Usage: harness.py {verb} complete [evidence.json]", file=sys.stderr)
        return 64

    print(f"Unknown: {verb}", file=sys.stderr)
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
