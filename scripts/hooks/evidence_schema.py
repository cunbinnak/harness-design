"""Hook: validate evidence fields per HOOK-RULES command_evidence_schema."""

from __future__ import annotations

from typing import Any


def check(command: str, evidence: dict[str, Any], schema_cfg: dict[str, Any]) -> tuple[bool, str]:
    spec = (schema_cfg or {}).get(command)
    if not spec:
        return True, "OK"
    for field in spec.get("required") or []:
        if field not in evidence:
            return False, f"evidence.{field} required for {command}"
    list_min = spec.get("list_min")
    if list_min:
        for field in spec.get("required") or []:
            val = evidence.get(field)
            if not isinstance(val, list) or len(val) < list_min:
                return False, f"evidence.{field} must have >={list_min} items"
    allowed_in = spec.get("in") or {}
    for field, choices in allowed_in.items():
        if evidence.get(field) not in choices:
            return False, f"evidence.{field} must be one of {choices}"
    types = spec.get("types") or {}
    for field, typ in types.items():
        if field in evidence and typ == "boolean" and not isinstance(evidence[field], bool):
            return False, f"evidence.{field} must be boolean"
    return True, "OK"
