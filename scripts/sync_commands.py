"""
Sync commands/*.md -> .claude/commands/ (and optionally .cursor/commands/).

Source of truth: commands/<name>.md (with frontmatter name, description, when_state, sets_stage, gates).
Target: copy to .claude/commands/<name>.md so Claude Code picks up slash commands.

Usage:
  py scripts/sync_commands.py            # sync to .claude/ only
  py scripts/sync_commands.py --cursor   # also sync to .cursor/commands/
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "commands"
CLAUDE_DST = REPO / ".claude" / "commands"
CURSOR_DST = REPO / ".cursor" / "commands"

SKIP_NAMES = {"README.md"}


def sync_to(dst: Path) -> int:
    dst.mkdir(parents=True, exist_ok=True)
    src_names = {f.name for f in SRC.glob("*.md") if f.name not in SKIP_NAMES}
    for old in dst.glob("*.md"):
        if old.name not in src_names:
            old.unlink()
            print(f"  removed: {dst.relative_to(REPO)}/{old.name}")
    count = 0
    for f in SRC.glob("*.md"):
        if f.name in SKIP_NAMES:
            continue
        target = dst / f.name
        shutil.copy2(f, target)
        count += 1
        print(f"  synced:  {dst.relative_to(REPO)}/{f.name}")
    return count


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    targets = [CLAUDE_DST]
    if "--cursor" in sys.argv:
        targets.append(CURSOR_DST)

    total = 0
    for dst in targets:
        print(f"\nSyncing to {dst.relative_to(REPO)}/")
        total += sync_to(dst)
    print(f"\nTotal files synced: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
