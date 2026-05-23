"""Chuẩn hóa wave id — chấp nhận 2, 02, wave-2, wave-002 → wave-002."""

from __future__ import annotations

import re

WAVE_CANONICAL_RE = re.compile(r"^wave-(\d{1,3})$", re.I)


def normalize_wave_id(raw: str | int | None, *, default: str = "wave-001") -> str:
    if raw is None or (isinstance(raw, str) and not str(raw).strip()):
        return default
    s = str(raw).strip().replace("_", "-").lower()
    m = WAVE_CANONICAL_RE.match(s)
    if m:
        return f"wave-{int(m.group(1)):03d}"
    if re.fullmatch(r"\d{1,3}", s):
        return f"wave-{int(s):03d}"
    if s.startswith("wave") and not s.startswith("wave-"):
        suffix = s[4:].lstrip("-")
        if suffix.isdigit():
            return f"wave-{int(suffix):03d}"
    return s


def wave_number(wave_id: str) -> int:
    wid = normalize_wave_id(wave_id)
    m = WAVE_CANONICAL_RE.match(wid)
    if m:
        return int(m.group(1))
    return 1
