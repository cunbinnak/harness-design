"""
Shared helper functions cho harness scripts (JSON/YAML I/O + repo root + timestamp).

Các script kernel (state.py/gates.py/build_prompt.py) tự inline I/O của riêng chúng;
module này phục vụ tooling phụ trợ (reset_for_new_project.py, …) cần helper chung.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def repo_root() -> Path:
    """Repo root (parent của scripts/)."""
    return REPO_ROOT


def load_json(path) -> dict:
    """Đọc + parse JSON file (utf-8)."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path, data) -> None:
    """Ghi JSON (indent 2, giữ unicode, trailing newline) — khớp format các kernel file."""
    Path(path).write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def utc_now_iso() -> str:
    """Timestamp ISO-8601 UTC (cho meta.updated_at)."""
    return datetime.now(timezone.utc).isoformat()


def load_yaml(path):
    """Đọc + parse YAML (cần pyyaml). Dùng cho KG yaml nếu cần."""
    try:
        import yaml  # type: ignore
    except ImportError as e:  # pragma: no cover
        raise RuntimeError("pyyaml chưa cài — `pip install pyyaml` để dùng load_yaml") from e
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def save_yaml(path, data) -> None:
    """Ghi YAML (giữ unicode, không sort key)."""
    try:
        import yaml  # type: ignore
    except ImportError as e:  # pragma: no cover
        raise RuntimeError("pyyaml chưa cài — `pip install pyyaml` để dùng save_yaml") from e
    Path(path).write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
