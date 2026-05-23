from __future__ import annotations

import json
from typing import Any


def check(body: Any, hook_cfg: dict[str, Any]) -> tuple[bool, str]:
    if body is None:
        return False, "empty return body"
    if isinstance(body, str):
        try:
            data = json.loads(body.strip())
        except json.JSONDecodeError as e:
            return False, f"not JSON: {e}"
    elif isinstance(body, dict):
        data = body
    else:
        return False, "return must be JSON object"

    for field in hook_cfg.get("required_fields") or []:
        if field not in data:
            return False, f"missing field: {field}"
    return True, "OK"
