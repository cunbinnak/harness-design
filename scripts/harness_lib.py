"""Shared helpers for ADLC harness scripts."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

WAVE_ID_RE = re.compile(r"^wave-[0-9]{3}$")
FEAT_RE = re.compile(r"^FEAT-[A-Z0-9-]+$")
ORCHESTRATOR_BOUNDARIES = frozenset({"reviewer"})
KINDS = frozenset({"backend", "bff", "web", "mobile", "reviewer"})

STAGE_DOC_GLOBS: dict[str, list[str]] = {
    "REQUIREMENT_INTAKE": ["docs/product/**"],
    "BUSINESS_ANALYSIS": ["docs/product/**"],
    "TECHNICAL_DESIGN": ["docs/architecture/**"],
    "IMPLEMENTATION_PLAN": ["docs/plans/**", "docs/architecture/**"],
    "IMPLEMENTATION": ["docs/architecture/**", "docs/plans/**"],
    "SELF_REVIEW": [],
    "SPECIALIST_TESTING": ["tracking/test-case-registry/**"],
    "BUG_LOGGING": ["tracking/bugs/**"],
    "FIX_MANUAL_BUGS": ["tracking/bugs/**"],
    "RELEASE_CANDIDATE": ["docs/plans/**"],
}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML required: pip install pyyaml")
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def save_yaml(path: Path, data: dict[str, Any]) -> None:
    if yaml is None:
        raise RuntimeError("PyYAML required: pip install pyyaml")
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def matrix_path() -> Path:
    return repo_root() / "harness" / "SERVICE-BOUNDARY-MATRIX.json"


def load_matrix() -> dict[str, Any]:
    return load_json(matrix_path())


def save_matrix(matrix: dict[str, Any]) -> None:
    save_json(matrix_path(), matrix)


def boundary_ids(matrix: dict[str, Any] | None = None) -> frozenset[str]:
    matrix = matrix or load_matrix()
    ids = {b["boundary_id"] for b in matrix.get("boundaries", []) if b.get("boundary_id")}
    return frozenset(ids) | ORCHESTRATOR_BOUNDARIES


def get_boundary(boundary_id: str, matrix: dict[str, Any] | None = None) -> dict[str, Any] | None:
    matrix = matrix or load_matrix()
    for b in matrix.get("boundaries", []):
        if b.get("boundary_id") == boundary_id:
            return b
    return None


def load_kg(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.is_absolute():
        p = repo_root() / p
    return load_yaml(p)


def save_kg(path: str | Path, data: dict[str, Any]) -> None:
    p = Path(path)
    if not p.is_absolute():
        p = repo_root() / p
    data.setdefault("meta", {})["updated_at"] = utc_now_iso()
    save_yaml(p, data)


def kg_template() -> dict[str, Any]:
    tpl = repo_root() / "knowledge-base" / "TEMPLATE.knowledge-graph.yaml"
    return load_yaml(tpl)


def expand_globs(root: Path, patterns: list[str]) -> list[str]:
    out: list[str] = []
    for pat in patterns:
        clean = pat.replace("\\", "/")
        if clean.endswith("/**"):
            base = clean[:-3]
            d = root / base
            if d.is_dir():
                for f in sorted(d.rglob("*")):
                    if f.is_file() and not f.name.startswith("."):
                        out.append(str(f.relative_to(root)).replace("\\", "/"))
        else:
            for f in sorted(root.glob(clean)):
                if f.is_file():
                    out.append(str(f.relative_to(root)).replace("\\", "/"))
    return sorted(set(out))


def load_machine() -> dict[str, Any]:
    return load_json(repo_root() / "harness" / "STATE-MACHINE.json")


def skill_for_stage(stage: str, machine: dict[str, Any]) -> str | None:
    st = machine.get("states", {}).get(stage, {})
    return st.get("skill")


def copy_handoff_template(wave_id: str) -> Path:
    root = repo_root()
    dest = root / "handoff" / f"{wave_id}.md"
    tpl = root / "handoff" / "TEMPLATE.wave.md"
    if not dest.exists() and tpl.is_file():
        text = tpl.read_text(encoding="utf-8")
        text = text.replace("{wave-id}", wave_id)
        dest.write_text(text, encoding="utf-8")
    return dest
