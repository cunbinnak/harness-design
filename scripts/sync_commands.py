#!/usr/bin/env python3
"""Sync commands/manifest.yaml → .cursor/commands and .claude/commands."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    raise SystemExit(1) from None


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def frontmatter(cmd_id: str, args: str = "") -> str:
    hint = f" {args}" if args else ""
    return (
        f"---\n"
        f"description: \"Harness command: {cmd_id}\"\n"
        f"argument-hint: \"{hint.strip()}\"\n"
        f"---\n\n"
        f"# /{cmd_id}{hint}\n\n"
    )


def body_for(cmd_id: str, extra: str = "") -> str:
    complete_line = f"python scripts/harness.py {cmd_id} complete"
    if extra:
        complete_line += f" {extra}"
    return "\n".join(
        [
            "Orchestrator: chạy agent (sau này) → artifact → complete.",
            "",
            "```bash",
            complete_line,
            f"python scripts/harness.py can {cmd_id}",
            "```",
            "",
            "Gates: `harness/COMMAND-GATES.json`. Huong dan: `SETUP-GUIDE.md`.",
        ]
    )


def collect_commands(manifest: dict) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for section in ("core", "extended", "meta"):
        for item in manifest.get(section) or []:
            if isinstance(item, str):
                out.append((item, "", ""))
            elif isinstance(item, dict):
                cid = item["id"]
                args = item.get("args", "")
                ev = item.get("evidence")
                extra = "evidence.json" if isinstance(ev, dict) and ev else ""
                out.append((cid, args, extra))
    return out


def sync_target(root: Path, target_dir: Path, manifest: dict) -> int:
    target_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for cmd_id, args, extra in collect_commands(manifest):
        doc_path = root / "commands" / f"{cmd_id}.md"
        if doc_path.is_file():
            content = doc_path.read_text(encoding="utf-8")
            lines = content.splitlines()
            body = "\n".join(lines[1:]).lstrip() if lines and lines[0].startswith("# ") else content
        else:
            body = body_for(cmd_id, extra)
        (target_dir / f"{cmd_id}.md").write_text(frontmatter(cmd_id, args) + body, encoding="utf-8")
        n += 1
    return n


def main() -> int:
    root = repo_root()
    manifest = yaml.safe_load((root / "commands" / "manifest.yaml").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        print("Invalid manifest.yaml", file=sys.stderr)
        return 1
    n1 = sync_target(root, root / ".cursor" / "commands", manifest)
    n2 = sync_target(root, root / ".claude" / "commands", manifest)
    print(f"Synced {n1} -> .cursor/commands, {n2} -> .claude/commands")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
