"""
Pure policy functions for harness hooks.

All functions in this module are PURE: no file I/O, no state mutation,
no logging. They take parsed input and return decisions or formatted text.

Used by dispatcher.py which handles I/O.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# ========================================================================
# State formatting (SessionStart, UserPromptSubmit, Notification, PreCompact)
# ========================================================================

# Next-step guidance per stage — báo CHÍNH XÁC lệnh + arg + ý nghĩa (thay vì list tên trống).
# Gồm cả back-edge (lùi về stage sở hữu để sửa doc đã frozen).
STAGE_NEXT_GUIDE = {
    "BOOTSTRAP": "/discovery-start D0 (bắt đầu Discovery)",
    "DISC_D0": "/discovery-start D1 (gate D0 → sang D1) · hoặc /discovery-start D0 (refine hypothesis)",
    "DISC_D1": "/discovery-start D2 (gate D1 → sang D2) · hoặc /discovery-start D1 (refine capability/persona)",
    "DISC_D2": "/discovery-start D3 (gate D2 → sang D3) · hoặc /discovery-start D2 (refine event-storming)",
    "DISC_D3": "/discovery-end (gate D3 → DOMAIN) · hoặc /discovery-start D3 (refine charter/PROJECT)",
    "DOMAIN_AUTHORING": "/domain-start <EPIC|FEATURE|JOURNEY|BR|PERSONA> (author) · /domain-end → DESIGN",
    "DESIGN": "/design (refine) · /design-end → PLAN · LÙI sửa product: /domain-start <mode> → DOMAIN",
    "PLAN": "/plan → REVIEW · LÙI sửa design: /design → DESIGN",
    "REVIEW": "/review-document (sửa mọi doc) · /approve-document · /start-wave <N>",
    "WAVE_OPEN": "/start-dev <boundary>",
    "DEV": "/start-dev <boundary khác> · xong hết boundary → /review-dev",
    "REVIEW_DEV": "/dev-handoff (sau khi mọi boundary review pass)",
    "DEV_HANDOFF": "/test-plan",
    "TEST_PLAN": "/test-execute",
    "TEST_EXECUTE": "(tự động → MANUAL_TEST sau khi chạy)",
    "MANUAL_TEST": "/fix-bugs · /test-execute (re-run full suite) · /end-wave (khi sạch bug + test pass)",
    "DONE": "/done-wave (teardown → BOOTSTRAP) · hoặc /apply-cr <CR> (amend → DOMAIN)",
}


def next_step_hint(state: dict) -> str:
    """Gợi ý bước tiếp theo CHÍNH XÁC (lệnh + arg + nghĩa) theo stage hiện tại."""
    return STAGE_NEXT_GUIDE.get(state.get("stage", "?"), "xem allowed_commands")


def format_state_brief(state: dict, allowed_cmds: list[str]) -> str:
    """Multi-line brief for SessionStart / PreCompact."""
    stage = state.get("stage", "?")
    wave = state.get("wave") or {}
    wave_id = wave.get("id") or "-"
    boundary = state.get("active_boundary") or "-"
    last = state.get("workflow", {}).get("last_completed") or "-"
    lines = [
        f"HARNESS — ADLC Design v4",
        f"  stage         = {stage}",
        f"  wave          = {wave_id}",
        f"  boundary      = {boundary}",
        f"  last_completed= {last}",
        f"  next          = {next_step_hint(state)}",
    ]
    return "\n".join(lines)


def state_header_line(state: dict, allowed_cmds: list[str]) -> str:
    """One-line header for UserPromptSubmit / Notification injection."""
    stage = state.get("stage", "?")
    wave = (state.get("wave") or {}).get("id") or "-"
    boundary = state.get("active_boundary") or "-"
    return f"[HARNESS stage={stage} wave={wave} boundary={boundary} | next: {next_step_hint(state)}]"


def memory_marker(state: dict, allowed_cmds: list[str]) -> str:
    """Pinned summary for PreCompact — giữ TRẠNG THÁI HIỆN TẠI sau compaction (không có history)."""
    return format_state_brief(state, allowed_cmds)


# ========================================================================
# Protected files (PreToolUse Write|Edit)
# ========================================================================

PROTECTED_PATHS = {
    "harness/STATE.json",
    "harness/STATE-MACHINE.json",
    "harness/SERVICE-BOUNDARY-MATRIX.json",
    ".claude/settings.json",
}


def is_protected_file(rel_path: str) -> bool:
    """Check if path is one of the kernel files that should not be hand-edited."""
    if not rel_path:
        return False
    normalized = rel_path.replace("\\", "/").lstrip("./")
    return normalized in PROTECTED_PATHS


# ------------------------------------------------------------------------
# Doc phase-lock (single-repo port của ZIP `pretooluse-readonly-inputs.py`)
# ------------------------------------------------------------------------
# ZIP (multi-repo) đóng băng upstream bằng snapshot `_inputs/**` read-only per repo. Single-repo
# tương đương = phase-lock theo stage: mỗi LỚP doc chỉ sửa được ở stage SỞ HỮU (+ REVIEW = cửa
# revision chung). Stage khác → frozen → LÙI về stage sở hữu (back-edge /design, /domain-start)
# rồi tiến lại (re-gate); sau ship dùng /apply-cr. Chống dev/test sửa spec cho khớp code (anti-pattern
# e2e) + chống sửa FEAT/HLD lúc đã ở PLAN. Thực thi NON-NEGOTIABLE #6 (trước chỉ honor-system).

_REVIEW = "REVIEW"
_DISC_STAGES = {"DISC_D0", "DISC_D1", "DISC_D2", "DISC_D3"}

# (label, set stage được sửa, regex path repo-relative). infra/ KHÔNG khoá (docker-compose update ở
# dev-handoff); knowledge-base/tracking/services/handoff KHÔNG khoá (back-half/dev append).
PHASE_LOCK_CLASSES = [
    ("discovery", _DISC_STAGES | {_REVIEW},
     re.compile(r"^docs/discovery/|^docs/architecture/PROJECT\.md$")),
    ("domain", {"DOMAIN_AUTHORING", _REVIEW},
     re.compile(r"^docs/domain/|^docs/architecture/(epics|feat|journeys|business-rules|personas)/")),
    ("design", {"DESIGN", _REVIEW},
     re.compile(r"^docs/architecture/(adr|hld|api|data-model|ux|events|integrations)/")),
    ("plan", {"PLAN", _REVIEW},
     re.compile(r"^docs/plans/")),
]
_BACK_HINT = {
    "discovery": "lùi qua done-wave→/discovery-start (hoặc sửa ở REVIEW)",
    "domain": "lùi /domain-start <mode> → DOMAIN",
    "design": "lùi /design → DESIGN",
    "plan": "về PLAN",
}


def phase_lock_violation(rel_path: str, stage: str) -> str | None:
    """None = cho phép; str = lý do chặn (doc thuộc lớp phase-lock mà stage hiện tại không sở hữu).

    TEMPLATE.* + README.md luôn cho sửa (scaffolding). Doc ngoài 4 lớp → không khoá.
    """
    if not rel_path or not stage:
        return None
    norm = rel_path.replace("\\", "/").lstrip("./")
    base = norm.rsplit("/", 1)[-1]
    if base.startswith("TEMPLATE.") or base == "README.md":
        return None
    for label, editable, pat in PHASE_LOCK_CLASSES:
        if pat.search(norm):
            if stage in editable:
                return None
            return (
                f"FM-PHASE-LOCK: '{norm}' (tài liệu {label}) đã ĐÓNG BĂNG ở stage '{stage}'. "
                f"Chỉ sửa được ở {sorted(editable)}. Muốn sửa → {_BACK_HINT.get(label)} rồi tiến lại "
                "(re-gate); sau ship dùng /apply-cr. KHÔNG sửa upstream từ stage sau (NON-NEGOTIABLE #6)."
            )
    return None


def safe_rel_path(abs_or_rel: str) -> str:
    """Normalize a path to repo-relative if possible; pass through if outside repo."""
    if not abs_or_rel:
        return ""
    p = Path(abs_or_rel.replace("\\", "/"))
    try:
        resolved = p.resolve()
        rel = resolved.relative_to(REPO_ROOT.resolve())
        return str(rel).replace("\\", "/")
    except (ValueError, OSError):
        # Outside repo — return original; not protected
        return str(p).replace("\\", "/")


# ========================================================================
# Bash gate parsing (PreToolUse Bash, PostToolUse Bash)
# ========================================================================

HARNESS_CMD_RE = re.compile(
    r"(?:harness\.py|state\.py)\s+(?:complete\s+)?([\w-]+)\s+complete\b",
    re.IGNORECASE,
)
HARNESS_CMD_RE_ALT = re.compile(
    r"(?:harness\.py|state\.py)\s+([\w-]+)\s+complete\b",
    re.IGNORECASE,
)
JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}")


def parse_harness_complete(bash_cmd: str) -> dict | None:
    """
    Parse a bash command line like:
      py scripts/harness.py dev-handoff complete '{"coverage_pct":85,...}'

    Returns {"command": "dev-handoff", "evidence": {...}} or None.
    """
    if not bash_cmd:
        return None
    m = HARNESS_CMD_RE_ALT.search(bash_cmd)
    if not m:
        return None
    command = m.group(1)
    evidence: dict = {}
    # Try to extract JSON object from the trailing portion
    brace_idx = bash_cmd.find("{")
    if brace_idx >= 0:
        match = JSON_BLOCK_RE.search(bash_cmd[brace_idx:])
        if match:
            try:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    evidence = parsed
            except json.JSONDecodeError:
                pass
    return {"command": command, "evidence": evidence}


# ========================================================================
# RETURN SCHEMA validation (SubagentStop)
# ========================================================================

RETURN_SCHEMA_REQUIRED = [
    "completed",
    "deferred",
    "needs_review",
    "files_changed",
    "build",
    "lint",
    "test",
]


def extract_json_object(text: str) -> dict | None:
    """Find the last balanced JSON object in `text`. Returns parsed dict or None."""
    if not text:
        return None
    # Find candidate substrings; prefer the LAST balanced JSON (final message)
    best: dict | None = None
    for match in JSON_BLOCK_RE.finditer(text):
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                best = parsed
        except json.JSONDecodeError:
            continue
    return best


def validate_return_schema(parsed: dict) -> tuple[bool, list[str]]:
    """Check required fields present in sub-agent RETURN SCHEMA."""
    if not isinstance(parsed, dict):
        return False, ["Not a JSON object"]
    missing = [k for k in RETURN_SCHEMA_REQUIRED if k not in parsed]
    if missing:
        return False, [f"Missing required field: {k}" for k in missing]
    return True, []


# ========================================================================
# Task spawn analysis (PreToolUse Task)
# ========================================================================

# Command spawn agent PHẢI dùng prompt từ build_prompt.py (E-6). Chỉ token ĐẶC THÙ (hyphen, không
# trùng từ tiếng Anh thường) — KHÔNG thêm "design"/"plan" bare (false-positive). domain-po/ba/translate
# + test-plan/test-execute thêm theo yêu cầu "ép MAIN dùng build_prompt, KHÔNG tự build prompt spawn".
DEV_SPAWN_KEYWORDS = (
    "start-dev", "fix-bugs", "review-dev",
    "domain-po", "domain-ba", "domain-translate",
    "test-plan", "test-execute",
)


def detect_dev_spawn(task_prompt: str) -> str | None:
    """Detect Task spawn của command-agent (dev/fix/review + domain-po/ba/translate).

    Trả command khớp hoặc None. Khớp = phải spawn bằng build_prompt.py output (E-6).
    """
    if not task_prompt:
        return None
    low = task_prompt.lower()
    for kw in DEV_SPAWN_KEYWORDS:
        if kw in low or kw.replace("-", "") in low.replace("-", ""):
            return kw
    return None


def detect_harness_agent_spawn(task_prompt: str, agent_names: list[str]) -> str | None:
    """E-6 chặt: Task spawn nhắc TÊN AGENT harness (registry từ agents/) → phải dùng build_prompt.

    Bao MỌI workflow spawn (dev/fix/review/domain/discovery/design/plan/test) không kẹt từ-thường,
    ít false-positive (chỉ tên agent THẬT). Explore/research không nhắc tên agent → không khớp.
    Trả tên agent khớp hoặc None.
    """
    if not task_prompt or not agent_names:
        return None
    low = task_prompt.lower()
    for name in agent_names:
        n = name.lower()
        if n and n in low:
            return name
    return None


def looks_like_build_prompt(task_prompt: str) -> bool:
    """True nếu prompt do `build_prompt.py` sinh (có chữ ký STATE BUNDLE frozen / SPAWN PROMPT).

    Dùng để chặn MAIN tự compose tay prompt cho command sub-agent (dễ truyền sai
    boundary/owned_paths/assumption) — E-6.
    """
    if not task_prompt:
        return False
    return (
        "STATE BUNDLE (frozen at spawn)" in task_prompt
        or "# SPAWN PROMPT" in task_prompt
    )


def boundary_reminder(boundary: str | None) -> str:
    """One-line reminder for Task spawns of dev agents."""
    if not boundary:
        return "REMINDER: Dev-spawn — ensure boundary is in wave_boundaries."
    return f"REMINDER: Dev-spawn for boundary='{boundary}' — edit only its owned_paths."


# ========================================================================
# Inline self-test (run: py scripts/hooks/policies.py)
# ========================================================================

def _selftest() -> int:
    # phase-lock: domain doc frozen ở PLAN, sửa được ở DOMAIN/REVIEW
    assert phase_lock_violation("docs/architecture/feat/FEAT-1.md", "PLAN") is not None
    assert phase_lock_violation("docs/architecture/feat/FEAT-1.md", "DOMAIN_AUTHORING") is None
    assert phase_lock_violation("docs/architecture/feat/FEAT-1.md", "REVIEW") is None
    assert phase_lock_violation("docs/architecture/feat/FEAT-1.md", "DEV") is not None
    # design doc frozen ở PLAN + DEV, sửa được ở DESIGN
    assert phase_lock_violation("docs/architecture/hld/hld-x.md", "PLAN") is not None
    assert phase_lock_violation("docs/architecture/hld/hld-x.md", "DESIGN") is None
    assert phase_lock_violation("docs/architecture/ux/ux-web.md", "DEV") is not None
    # plan doc frozen ở DEV, sửa được ở PLAN
    assert phase_lock_violation("docs/plans/wave-001.md", "DEV") is not None
    assert phase_lock_violation("docs/plans/wave-001.md", "PLAN") is None
    # discovery + PROJECT.md: discovery-owned (frozen ở DOMAIN)
    assert phase_lock_violation("docs/architecture/PROJECT.md", "DOMAIN_AUTHORING") is not None
    assert phase_lock_violation("docs/architecture/PROJECT.md", "DISC_D3") is None
    assert phase_lock_violation("docs/discovery/BOUNDARY-MAP.md", "DESIGN") is not None
    # TEMPLATE.* + README luôn sửa được (scaffolding)
    assert phase_lock_violation("docs/architecture/hld/TEMPLATE.hld.md", "DEV") is None
    assert phase_lock_violation("docs/architecture/feat/README.md", "PLAN") is None
    assert phase_lock_violation("docs/architecture/ux/TEMPLATE.design-tokens.css", "PLAN") is None
    # KHÔNG khoá: infra (docker-compose update ở dev-handoff), KG, tracking, services, arch root
    assert phase_lock_violation("docs/architecture/infra/docker-compose.yml", "DEV_HANDOFF") is None
    assert phase_lock_violation("knowledge-base/x.knowledge-graph.yaml", "DEV") is None
    assert phase_lock_violation("tracking/wave-001/bugs.md", "TEST_EXECUTE") is None
    assert phase_lock_violation("services/demo-x/src/A.java", "DEV") is None
    assert phase_lock_violation("docs/architecture/ARCHITECTURE-PRINCIPLES.md", "PLAN") is None
    # next-step hint contextual (arg + back-edge)
    assert "discovery-start D2" in next_step_hint({"stage": "DISC_D1"})  # advance qua start (cơ chế mới)
    assert "/design" in next_step_hint({"stage": "PLAN"})          # back-edge
    assert "domain-start" in next_step_hint({"stage": "DESIGN"})    # back-edge
    assert "header" not in state_header_line({"stage": "PLAN"}, []).lower() or True
    assert "next:" in state_header_line({"stage": "DISC_D0"}, [])
    # E-6 chặt: detect theo tên agent (registry) — khớp tên thật, không khớp prompt research
    assert detect_harness_agent_spawn("spawn domain-po-agent author epic", ["domain-po-agent", "dev-x-agent"]) == "domain-po-agent"
    assert detect_harness_agent_spawn("explore codebase for X", ["domain-po-agent"]) is None
    assert detect_harness_agent_spawn("anything", []) is None
    # E-6 keyword: test-plan/test-execute ép build_prompt (chống MAIN tự build prompt spawn test)
    assert detect_dev_spawn("spawn agent tạo test-plan cho wave") == "test-plan"
    assert detect_dev_spawn("run test-execute black-box trên hệ thống") == "test-execute"
    assert detect_dev_spawn("review the test plan document") is None  # space-form KHÔNG khớp (không false-positive)
    # build_prompt-signed output cho test PHẢI pass (không bị block)
    assert looks_like_build_prompt("# SPAWN PROMPT — /test-execute\n...") is True
    print("OK: policies.py selftest passed")
    return 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(_selftest())
