"""
Harness CLI — thin wrapper for state.py.

Usage:
  py scripts/harness.py state                              # show current STATE summary
  py scripts/harness.py validate                           # validate STATE against MACHINE
  py scripts/harness.py can <command>                      # check if command allowed
  py scripts/harness.py <command> complete '<evidence>'    # apply transition
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import json  # noqa: E402

import state as state_mod  # noqa: E402

MACHINE_FILE = SCRIPTS.parent / "harness" / "STATE-MACHINE.json"


def _load_commands() -> list[str]:
    """Command hợp lệ = mọi trigger trong STATE-MACHINE.json — DERIVE, không hardcode.

    Trước đây list hardcode → thêm command mới vào STATE-MACHINE mà quên chỗ này = CLI báo
    'Unknown' dù transition hợp lệ (bug design-ux bắt được khi chạy thử; tệ hơn: hook turn-flag
    đã tiêu lượt trước khi CLI fail → user phí 1 turn). Trigger `_*` (vd `_auto`) là internal,
    không phải CLI command.
    """
    try:
        data = json.loads(MACHINE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    triggers = {t.get("trigger") for t in data.get("transitions", []) if isinstance(t, dict)}
    return sorted(t for t in triggers if isinstance(t, str) and t and not t.startswith("_"))


COMMANDS = _load_commands()


def main() -> int:
    # UTF-8 stdout on Windows
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    if len(sys.argv) < 2:
        print(__doc__)
        print("Commands:", ", ".join(COMMANDS))
        return 64

    verb = sys.argv[1]
    rest = sys.argv[2:]

    if verb in ("state", "show"):
        return state_mod.main(["show"])
    if verb == "validate":
        return state_mod.main(["validate"])
    if verb == "can" and rest:
        return state_mod.main(["can", rest[0]])

    # <command> complete '<evidence>'
    if verb in COMMANDS:
        if rest and rest[0] == "complete":
            ev = rest[1] if len(rest) > 1 else "{}"
            return state_mod.main(["complete", verb, ev])
        if rest and rest[0] == "can":
            return state_mod.main(["can", verb])
        print(f"Usage: harness.py {verb} complete '<evidence-json>'", file=sys.stderr)
        return 64

    print(f"Unknown: {verb}", file=sys.stderr)
    print(__doc__, file=sys.stderr)
    return 64


if __name__ == "__main__":
    sys.exit(main())
