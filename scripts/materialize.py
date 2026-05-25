#!/usr/bin/env python3
"""Materialize dispatcher — unified entry point for materialization scripts.

Usage:
  py scripts/materialize.py boundary-agents --from-roster docs/plans/project/agent-roster.md
  py scripts/materialize.py knowledge-graphs --from-roster docs/plans/project/agent-roster.md
  py scripts/materialize.py ux --boundaries fe-web,fe-admin
  py scripts/materialize.py wave-plans --from-roadmap docs/plans/project/waves-roadmap.md
"""

from __future__ import annotations

import sys

SUBCOMMANDS = {
    "boundary-agents": "materialize_boundary_agents",
    "knowledge-graphs": "materialize_knowledge_graphs",
    "ux": "materialize_ux_documents",
    "wave-plans": "materialize_wave_plans",
}


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        print("\nSubcommands:", ", ".join(SUBCOMMANDS))
        return 0
    sub = sys.argv[1]
    if sub not in SUBCOMMANDS:
        print(f"Unknown subcommand: {sub}", file=sys.stderr)
        print(f"Available: {', '.join(SUBCOMMANDS)}", file=sys.stderr)
        return 64
    module_name = SUBCOMMANDS[sub]
    mod = __import__(module_name)
    sys.argv = [module_name] + sys.argv[2:]
    return mod.main()


if __name__ == "__main__":
    raise SystemExit(main())
