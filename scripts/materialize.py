"""
Materialize per-boundary artifacts from harness/SERVICE-BOUNDARY-MATRIX.json.

For each boundary in MATRIX, generate:
  agents/dev-{prefix}-{boundary}-agent.md
  agents/fix-{prefix}-{boundary}-agent.md
  knowledge-base/{prefix}-{boundary}.knowledge-graph.yaml

Templates:
  agents/_template-dev-agent.md
  agents/_template-fix-agent.md
  knowledge-base/TEMPLATE.boundary-kg.yaml

Usage:
  py scripts/materialize.py                  # materialize ALL boundaries
  py scripts/materialize.py --wave 1         # filter by wave (when MATRIX has wave field)
  py scripts/materialize.py --boundary X     # only one boundary
  py scripts/materialize.py --force          # overwrite existing files
  py scripts/materialize.py --dry-run        # show what would be done
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

sys.path.insert(0, str(HERE))
from build_prompt import SCAFFOLD_REF_SKILLS_PER_KIND, PRIMARY_SKILLS_PER_KIND  # single source: scaffold + primary map

MATRIX_FILE = REPO / "harness" / "SERVICE-BOUNDARY-MATRIX.json"
TEMPLATE_DEV = REPO / "agents" / "_template-dev-agent.md"
TEMPLATE_FIX = REPO / "agents" / "_template-fix-agent.md"
TEMPLATE_KG = REPO / "knowledge-base" / "TEMPLATE.boundary-kg.yaml"

AGENTS_DIR = REPO / "agents"
KB_DIR = REPO / "knowledge-base"

REQUIRED_BOUNDARY_FIELDS = ["boundary_id", "kind", "prefix"]
VALID_KINDS = {"backend", "bff", "web", "mobile"}


def validate_boundary(b: dict, idx: int) -> list[str]:
    errs = []
    for f in REQUIRED_BOUNDARY_FIELDS:
        if not b.get(f):
            errs.append(f"boundary[{idx}] missing required field: {f}")
    kind = b.get("kind")
    if kind and kind not in VALID_KINDS:
        errs.append(f"boundary[{idx}].kind={kind!r} không hợp lệ (cần ∈ {sorted(VALID_KINDS)})")
    return errs


def load_matrix() -> tuple[list[dict], int]:
    if not MATRIX_FILE.exists():
        raise FileNotFoundError(f"MATRIX không tồn tại: {MATRIX_FILE}")
    data = json.loads(MATRIX_FILE.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data, 0
    if isinstance(data, dict):
        return data.get("boundaries", []), data.get("revision", 0)
    raise ValueError("MATRIX format không đúng (cần list hoặc {boundaries: [...]})")


def filter_boundaries(boundaries: list[dict], wave: int | None, only: str | None) -> list[dict]:
    if only:
        return [b for b in boundaries if b.get("boundary_id") == only]
    if wave is not None:
        return [
            b for b in boundaries
            if b.get("wave") == wave or wave in (b.get("waves") or [])
        ]
    return boundaries


def render(template_text: str, vars: dict[str, str]) -> str:
    out = template_text
    for k, v in vars.items():
        out = out.replace(f"{{{{{k}}}}}", str(v))
    return out


def _skill_bullets(skills: list[str], empty: str) -> str:
    if not skills:
        return f"  - _{empty}_"
    return "\n".join(f"  - `{s}`" for s in skills)


def boundary_vars(b: dict, matrix_revision: int) -> dict[str, str]:
    boundary_id = b["boundary_id"]
    prefix = b["prefix"]
    kind = b["kind"]
    owned_paths = b.get("owned_paths") or _default_owned_paths(prefix, boundary_id)
    tech = b.get("tech") or {}
    scaffold_refs = SCAFFOLD_REF_SKILLS_PER_KIND.get(kind, [])
    ref_skills = list(b.get("ref_skills") or [])  # situational, do intake quyết per-boundary
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "boundary": boundary_id,
        "prefix": prefix,
        "kind": kind,
        "repo_url": b.get("repo_url") or f"<set later: git@gitlab.com:org/{prefix}-{boundary_id}.git>",
        "purpose": b.get("purpose") or f"Boundary {boundary_id} ({kind})",
        "tech_language": tech.get("language") or _default_lang(kind),
        "tech_framework": tech.get("framework") or _default_framework(kind),
        "tech_data_store": tech.get("data_store") or _default_data_store(kind),
        "owned_paths_yaml": "\n".join(f"  - {p}" for p in owned_paths),
        "owned_paths_md": "\n".join(f"- `{p}`" for p in owned_paths),
        "primary_skill": (PRIMARY_SKILLS_PER_KIND.get(kind) or ["rules-?"])[0],
        "scaffold_refs_md": _skill_bullets(scaffold_refs, f"kind {kind} dùng convention trong rules-{kind}, không có ref structure riêng"),
        "ref_skills_md": _skill_bullets(ref_skills, "chưa gắn — boundary không dùng cache/event/extra (intake để trống)"),
        "created_at": now,
        "matrix_revision": str(matrix_revision),
    }


def _default_owned_paths(prefix: str, boundary: str) -> list[str]:
    return [
        f"services/{prefix}-{boundary}/**",
        f"docs/architecture/hld/hld-{boundary}.md",
        f"docs/architecture/api/api-{boundary}.md",
        f"docs/architecture/data-model/data-model-{boundary}.md",
        f"docs/architecture/events/{boundary}-events.md",
        f"docs/architecture/ux/ux-{boundary}.md",
        f"knowledge-base/{prefix}-{boundary}.knowledge-graph.yaml",
    ]


def _default_lang(kind: str) -> str:
    return {
        "backend": "Java 21",
        "bff": "Node.js 22 + TS 5",
        "web": "TS 5 + React 19",
        "mobile": "Dart 3 / Flutter 3",
    }.get(kind, "?")


def _default_framework(kind: str) -> str:
    return {
        "backend": "Spring Boot 3.4",
        "bff": "Apollo Server 4",
        "web": "Vite or Next.js 15",
        "mobile": "Flutter 3",
    }.get(kind, "?")


def _default_data_store(kind: str) -> str:
    return {
        "backend": "PostgreSQL 16",
        "bff": "Redis (cache)",
        "web": "none",
        "mobile": "local SQLite",
    }.get(kind, "none")


def target_paths(b: dict) -> dict[str, Path]:
    prefix = b["prefix"]
    boundary = b["boundary_id"]
    return {
        "dev_agent": AGENTS_DIR / f"dev-{prefix}-{boundary}-agent.md",
        "fix_agent": AGENTS_DIR / f"fix-{prefix}-{boundary}-agent.md",
        "kg":        KB_DIR / f"{prefix}-{boundary}.knowledge-graph.yaml",
    }


def materialize_one(b: dict, matrix_revision: int, force: bool, dry_run: bool) -> dict:
    vars = boundary_vars(b, matrix_revision)
    targets = target_paths(b)
    actions: list[tuple[str, str]] = []

    specs = [
        ("dev_agent", TEMPLATE_DEV),
        ("fix_agent", TEMPLATE_FIX),
        ("kg",        TEMPLATE_KG),
    ]
    for key, tpl_path in specs:
        target = targets[key]
        if target.exists() and not force:
            actions.append((key, "SKIP (exists)"))
            continue
        if dry_run:
            actions.append((key, f"WOULD WRITE -> {target.relative_to(REPO)}"))
            continue
        tpl_text = tpl_path.read_text(encoding="utf-8")
        rendered = render(tpl_text, vars)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
        actions.append((key, f"WROTE -> {target.relative_to(REPO)}"))

    return {"boundary": b["boundary_id"], "actions": actions}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser()
    ap.add_argument("--wave", type=int, help="Only materialize boundaries with this wave number")
    ap.add_argument("--boundary", help="Only this boundary_id")
    ap.add_argument("--force", action="store_true", help="Overwrite existing files")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be done")
    args = ap.parse_args()

    for tpl in (TEMPLATE_DEV, TEMPLATE_FIX, TEMPLATE_KG):
        if not tpl.exists():
            print(f"ERROR: Template missing: {tpl}", file=sys.stderr)
            return 2

    try:
        boundaries, revision = load_matrix()
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if not boundaries:
        print("MATRIX empty - no boundaries to materialize.")
        return 0

    all_errs = []
    for i, b in enumerate(boundaries):
        all_errs.extend(validate_boundary(b, i))
    if all_errs:
        print("VALIDATION FAIL:", file=sys.stderr)
        for e in all_errs:
            print(f"  - {e}", file=sys.stderr)
        return 2

    selected = filter_boundaries(boundaries, args.wave, args.boundary)
    if not selected:
        print(f"No boundaries match filter (wave={args.wave}, boundary={args.boundary})")
        return 0

    mode = " (DRY-RUN)" if args.dry_run else (" (FORCE overwrite)" if args.force else "")
    print(f"Materializing {len(selected)} boundary{mode}\n")

    summary = []
    for b in selected:
        result = materialize_one(b, revision, args.force, args.dry_run)
        summary.append(result)
        print(f"  [{result['boundary']}]")
        for key, action in result["actions"]:
            print(f"    {key:12s} {action}")
        print()

    wrote = sum(1 for r in summary for _, a in r["actions"] if a.startswith("WROTE"))
    skipped = sum(1 for r in summary for _, a in r["actions"] if a.startswith("SKIP"))
    would = sum(1 for r in summary for _, a in r["actions"] if a.startswith("WOULD"))
    print(f"Total: wrote={wrote}, skipped={skipped}, would_write={would}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
