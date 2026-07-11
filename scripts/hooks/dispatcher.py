"""
Single-entry hook dispatcher for ADLC Design Harness.

Claude Code invokes this script with --event <name> and stdin JSON payload.
Dispatcher routes to handlers in policies.py, formats output per Claude Code spec.

Events handled:
  SessionStart, UserPromptSubmit, Notification, PreCompact, SessionEnd
  PreToolUse (Bash | Write|Edit|MultiEdit | Task | Skill|SlashCommand)
  PostToolUse (Bash)
  SubagentStop, Stop

Error policy: fail-open. If hook code crashes, allow tool call through.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
REPO_ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(HERE))

import policies  # noqa: E402
import state as state_mod  # noqa: E402


# ========================================================================
# Output helpers (Claude Code spec)
# ========================================================================

def _print_json(obj: dict) -> None:
    """Print JSON to stdout (no BOM). Used for Claude Code hook responses."""
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.flush()


def allow_silent() -> int:
    """Default allow: exit 0 with no output."""
    return 0


def pre_tool_deny(reason: str) -> int:
    """PreToolUse hook deny output (Claude Code spec)."""
    _print_json({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    })
    return 0


def stop_block(reason: str) -> int:
    """Stop / SubagentStop block output."""
    _print_json({"decision": "block", "reason": reason})
    return 0


def inject_context(text: str) -> int:
    """SessionStart / UserPromptSubmit / Notification / PreCompact context injection."""
    _print_json({"additionalContext": text})
    return 0


# ========================================================================
# Payload accessors
# ========================================================================

def _read_payload() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw}


def _tool_name(payload: dict) -> str:
    return str(
        payload.get("tool_name")
        or payload.get("toolName")
        or ""
    )


def _tool_input(payload: dict) -> dict:
    ti = payload.get("tool_input") or payload.get("toolInput") or {}
    return ti if isinstance(ti, dict) else {}


def _bash_command(payload: dict) -> str:
    ti = _tool_input(payload)
    return str(ti.get("command") or "")


def _edit_path(payload: dict) -> str:
    ti = _tool_input(payload)
    for key in ("file_path", "filePath", "path"):
        if ti.get(key):
            return policies.safe_rel_path(str(ti[key]))
    return ""


def _task_prompt(payload: dict) -> str:
    ti = _tool_input(payload)
    return str(ti.get("prompt") or ti.get("description") or "")


def _skill_name(payload: dict) -> str:
    """Tên skill/slash-command MAIN gọi qua Skill/SlashCommand tool.

    Skill tool input: `skill`. SlashCommand tool input: `command` (vd '/dev-handoff arg').
    Chuẩn hoá: bỏ '/' đầu, bỏ namespace 'plugin:', lấy token đầu (tên lệnh, bỏ arg)."""
    ti = _tool_input(payload)
    raw = str(ti.get("skill") or ti.get("command") or ti.get("name") or "").strip()
    if not raw:
        return ""
    raw = raw.lstrip("/")
    raw = raw.split()[0] if raw.split() else ""   # bỏ arg sau khoảng trắng
    raw = raw.split(":")[-1]                        # 'plugin:skill' → 'skill'
    return raw


def _last_assistant_text(payload: dict) -> str:
    for key in (
        "last_assistant_message",
        "lastAssistantMessage",
        "text",
        "response",
        "output",
    ):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return str(payload.get("_raw") or "")


# ========================================================================
# Handlers
# ========================================================================

# #11: MAIN KHÔNG tự nối lệnh — chỉ 1 `harness <cmd> complete` mỗi user-turn. Marker reset ở
# UserPromptSubmit/SessionStart (fresh turn); _pre_bash set khi cho qua complete đầu, chặn complete kế.
TURN_ADVANCE_FLAG = REPO_ROOT / "harness" / ".turn-advance.flag"


def _clear_turn_flag() -> None:
    try:
        TURN_ADVANCE_FLAG.unlink()
    except OSError:
        pass


def handle_session_start(payload: dict) -> int:
    _clear_turn_flag()  # fresh session → reset turn-advance
    state = state_mod.load_state()
    allowed = state_mod.allowed_commands(state)
    brief = policies.format_state_brief(state, allowed)
    return inject_context(brief)


def handle_user_prompt_submit(payload: dict) -> int:
    _clear_turn_flag()  # user gõ → mở 1 lượt mới (1 stage-command)
    state = state_mod.load_state()
    allowed = state_mod.allowed_commands(state)
    return inject_context(policies.state_header_line(state, allowed))


def handle_notification(payload: dict) -> int:
    state = state_mod.load_state()
    allowed = state_mod.allowed_commands(state)
    return inject_context(policies.state_header_line(state, allowed))


def handle_pre_compact(payload: dict) -> int:
    state = state_mod.load_state()
    allowed = state_mod.allowed_commands(state)
    return inject_context(policies.memory_marker(state, allowed))


def handle_session_end(payload: dict) -> int:
    """Cleanup: clear stale spawn.active if any."""
    try:
        state = state_mod.load_state()
        spawn = state.get("spawn") or {}
        if spawn.get("active"):
            state["spawn"]["active"] = None
            state_mod.save_state(state, updated_by="session_end_cleanup")
    except Exception:
        pass
    return allow_silent()


# --------- PreToolUse routing ---------

def handle_pre_tool_use(payload: dict) -> int:
    tool = _tool_name(payload)
    if tool == "Bash":
        return _pre_bash(payload)
    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        return _pre_write_edit(payload)
    if tool in ("Task", "Agent", "Subagent"):
        return _pre_task(payload)
    if tool in ("Skill", "SlashCommand"):
        return _pre_skill(payload)
    return allow_silent()


def _pre_skill(payload: dict) -> int:
    """Chặn MAIN TỰ chạy harness slash-command (auto-nối pipeline) — CHỈ tool `SlashCommand`.

    Phân biệt 2 tool khác hẳn nhau (trước đây gộp → chặn oan sub-agent load skill):
    - **`SlashCommand`** tool = CHẠY LỆNH `/test-plan` (như user gõ → fire UserPromptSubmit → reset
      turn-flag → MAIN tự nối pipeline). Vector tự-nối-lệnh THẬT → deny nếu ∈ GATE_RULES.
    - **`Skill`** tool = LOAD convention skill (sub-agent nạp checklist của chính nó: domain-po,
      test-plan, ux-design…). KHÔNG transition state, KHÔNG fire UserPromptSubmit → CHO QUA LUÔN,
      kể cả tên trùng harness command. (Để transition vẫn phải `harness complete` qua Bash →
      _pre_bash + turn-flag đã chặn; Skill không giúp MAIN né gì.)
    Skill ngoài-harness (research/code-review/…) → cho qua như thường.
    """
    if _tool_name(payload) != "SlashCommand":
        return allow_silent()  # Skill tool (load convention) — sub-agent cần, không phải tự-nối-lệnh
    name = _skill_name(payload)
    if not name:
        return allow_silent()
    try:
        import gates
        harness_cmds = set(gates.GATE_RULES)
    except Exception:
        return allow_silent()  # fail-open
    if name in harness_cmds:
        return pre_tool_deny(
            f"MAIN tự chạy slash-command '/{name}' — KHÔNG được (NON-NEGOTIABLE: MAIN KHÔNG TỰ NỐI LỆNH). "
            f"Harness slash-command là hành động USER GÕ (pre-loaded). MAIN chỉ chạy `harness <cmd> complete` "
            f"cho lệnh user đã gõ rồi DỪNG, báo bước kế, CHỜ user gõ lệnh tiếp. Muốn '/{name}' chạy → bảo user gõ."
        )
    return allow_silent()


def _pre_bash(payload: dict) -> int:
    cmd = _bash_command(payload)
    parsed = policies.parse_harness_complete(cmd)
    if parsed is None:
        return allow_silent()  # not a harness complete call

    command_id = parsed["command"]
    evidence = parsed["evidence"]
    state = state_mod.load_state()

    if not state_mod.can_run(command_id, state):
        allowed = state_mod.allowed_commands(state)
        return pre_tool_deny(
            f"Command '{command_id}' không allowed ở stage '{state['stage']}'. "
            f"Allowed: {allowed}"
        )

    # Gate pre-check (best effort; final gate runs inside state.complete)
    import gates
    ok, errors = gates.check_for_command(command_id, state, evidence)
    if not ok:
        return pre_tool_deny("Gate sẽ fail:\n  - " + "\n  - ".join(errors))

    # #11: chống MAIN tự nối lệnh — 1 stage-command/user-turn. Gate-fail KHÔNG tiêu cờ (return ở trên).
    if TURN_ADVANCE_FLAG.exists():
        return pre_tool_deny(
            f"MAIN tự nối lệnh — đã chạy 1 stage-command (harness complete) trong lượt này. "
            f"DỪNG: báo user kết quả + bước kế, CHỜ user gõ lệnh. (Mỗi prompt = 1 stage-command; "
            f"user muốn đi tiếp thì invoke lệnh kế. Lệnh đang chặn: '{command_id}'.)"
        )
    try:
        TURN_ADVANCE_FLAG.write_text("used", encoding="utf-8")
    except OSError:
        pass
    return allow_silent()


def _handoff_no_code_fix(stage: str | None, spawn_active: str | None, norm_path: str) -> bool:
    """True = chặn edit services/** vì đang trong dev-handoff (infra-only, #12).

    Gate theo STAGE: chỉ chặn ở DEV_HANDOFF — lúc duy nhất dev-handoff-agent chạy. Ngoài stage đó
    (REVIEW_DEV/MANUAL_TEST/DEV…) mọi sửa services là fix/dev-agent hợp lệ → KHÔNG chặn oan dù cờ
    spawn.active còn kẹt (SubagentStop có thể không fire với background Agent tool → cờ stale)."""
    return (
        stage == "DEV_HANDOFF"
        and spawn_active == "dev-handoff-agent"
        and norm_path.startswith("services/")
    )


def _pre_write_edit(payload: dict) -> int:
    path = _edit_path(payload)
    if policies.is_protected_file(path):
        return pre_tool_deny(
            f"'{path}' là kernel file. KHÔNG sửa tay — dùng `py scripts/harness.py <cmd> complete '...'` để transition state."
        )
    if policies.is_proof_file(path):
        return pre_tool_deny(
            f"FM-PROOF-FORGE: '{path}' là PROOF FILE harness-đo — CHỈ `py scripts/capture_infra_proof.py` được sinh, "
            "KHÔNG ghi/sửa tay (ghi tay = fake bằng chứng infra/health/api). Service chưa UP → start thật rồi "
            "chạy lại capture; env không Docker → gate force:true,reason (audit decisions.md)."
        )
    # Phase-lock: doc upstream đã qua stage sở hữu → frozen (port ZIP readonly-inputs cho single-repo).
    try:
        st = state_mod.load_state()
    except Exception:
        st = {}
    stage = st.get("stage")
    if stage:
        violation = policies.phase_lock_violation(path, stage)
        if violation:
            return pre_tool_deny(violation)
    # #12: dev-handoff-agent (infra-only) KHÔNG được sửa services/** — lỗi code/migration/Dockerfile
    # của boundary → STOP, báo MAIN spawn fix-{boundary}-agent (Mode B). dev-handoff chỉ sửa docker-compose.yml.
    # Gate theo STAGE (robust): block CHỈ ở DEV_HANDOFF — lúc duy nhất dev-handoff-agent chạy. Ngoài
    # stage đó (REVIEW_DEV/MANUAL_TEST/DEV…) mọi sửa services là fix/dev-agent hợp lệ → KHÔNG chặn oan
    # dù cờ spawn.active còn kẹt (SubagentStop có thể không fire với background Agent tool → cờ stale).
    norm = path.replace("\\", "/").lstrip("./")
    if _handoff_no_code_fix(stage, (st.get("spawn") or {}).get("active"), norm):
        return pre_tool_deny(
            f"FM-HANDOFF-NO-CODE-FIX: dev-handoff INFRA-ONLY — KHÔNG sửa '{norm}' (code/migration/config/Dockerfile "
            "của boundary). Container chết do lỗi này → STOP, đọc `docker compose logs`, báo root-cause + "
            "spawn `fix-{boundary}-agent` (Mode B) để fix → re-run /dev-handoff. dev-handoff chỉ chỉnh docker-compose.yml."
        )
    return allow_silent()


def _harness_agent_names() -> list[str]:
    """Registry tên agent harness từ agents/*.md (trừ _template-*/README) — cho E-6 detect."""
    out: list[str] = []
    agents_dir = REPO_ROOT / "agents"
    if not agents_dir.is_dir():
        return out
    for p in agents_dir.glob("*-agent.md"):
        stem = p.stem
        if stem.startswith("_") or stem.lower().startswith("readme"):
            continue
        out.append(stem)
    return out


def _pre_task(payload: dict) -> int:
    """Inject reminder for dev-spawn; KHÔNG block.

    KHÔNG chặn theo `spawn.active`: model harness cho phép NESTED spawn
    (review-{kind}-agent → fix → re-review). Chặn double-spawn ở đây sẽ
    phá chính luồng review→fix→test→fix. Concurrency-control nếu cần làm
    ở orchestrator, không ở hook này.
    """
    state = state_mod.load_state()
    # Inject reminder via additionalContext (non-blocking)
    prompt = _task_prompt(payload)
    # E-6 chặt: keyword (dev/fix/review/domain) HOẶC tên agent harness (registry agents/).
    matched = policies.detect_dev_spawn(prompt) or policies.detect_harness_agent_spawn(prompt, _harness_agent_names())
    if matched:
        # E-6: dev/fix/review sub-agent PHẢI spawn bằng prompt từ build_prompt.py (chứa STATE
        # BUNDLE frozen + owned_paths + RETURN SCHEMA). MAIN tự viết tay → dễ sai boundary → block.
        if not policies.looks_like_build_prompt(prompt):
            return pre_tool_deny(
                f"Spawn '{matched}' sub-agent bằng prompt tự viết tay — PHẢI chạy "
                f"`py scripts/build_prompt.py {matched} [--mode/--boundary/...]` rồi spawn với output đó "
                "(STATE BUNDLE frozen + owned_paths/boot + RETURN SCHEMA chuẩn). MAIN KHÔNG tự build prompt (E-6)."
            )
        # #12: dev-handoff-agent = infra-only → đánh dấu spawn.active để PreToolUse(Write|Edit) chặn
        # sửa services/** (lỗi code boundary phải để fix-agent, KHÔNG dev-handoff tự vá).
        try:
            if "dev-handoff-agent" in prompt.lower():
                state.setdefault("spawn", {})["active"] = "dev-handoff-agent"
                state_mod.save_state(state, updated_by="pre_task:dev-handoff")
            elif (state.get("spawn") or {}).get("active"):
                # Spawn agent KHÁC dev-handoff = bằng chứng dev-handoff trước đã return (MAIN đã
                # chuyển sang agent kế, vd fix-agent). Clear cờ stale ngay tại ranh giới spawn — không
                # phụ thuộc SubagentStop (có thể không fire với background Agent tool).
                state["spawn"]["active"] = None
                state_mod.save_state(state, updated_by="pre_task:clear-stale-spawn")
        except Exception:
            pass
        boundary = state.get("active_boundary")
        reminder = policies.boundary_reminder(boundary)
        # PreToolUse can also use additionalContext for inject without deny
        _print_json({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "additionalContext": reminder,
            }
        })
        return 0
    return allow_silent()


# --------- PostToolUse (Bash) ---------

def handle_post_tool_use(payload: dict) -> int:
    """PostToolUse(Bash) — no-op. STATE.json chỉ giữ trạng thái hiện tại (không ghi history/checkpoint)."""
    return allow_silent()


# --------- SubagentStop ---------

def handle_subagent_stop(payload: dict) -> int:
    text = _last_assistant_text(payload)
    parsed = policies.extract_json_object(text)
    if parsed is None:
        # Sub-agent didn't return JSON — warn soft (not block per v4 plan)
        return allow_silent()
    ok, errors = policies.validate_return_schema(parsed)
    if not ok:
        # Soft warn — log but don't block (could change to block later)
        sys.stderr.write(
            f"WARN: SubagentStop RETURN SCHEMA invalid: {'; '.join(errors)}\n"
        )
    try:
        state = state_mod.load_state()
    except Exception:
        state = {}
    # A-1: compile/lint error (build/lint=fail) KHÔNG được kết thúc ở BẤT KỲ stage nào;
    #      test=fail chỉ chặn ở DEV/REVIEW_DEV (TEST_EXECUTE/MANUAL_TEST: test fail = log bug, hợp lệ).
    stage = state.get("stage")
    red = [k for k in ("build", "lint") if str(parsed.get(k)).lower() == "fail"]
    if stage in ("DEV", "REVIEW_DEV") and str(parsed.get("test")).lower() == "fail":
        red.append("test")
    if red:
        return stop_block(
            f"Sub-agent tự báo {', '.join(red)}=fail — KHÔNG kết thúc khi còn đỏ. "
            "Sửa tới khi xanh rồi mới return (A-1)."
        )
    # Clear spawn.active
    try:
        state.setdefault("spawn", {})["active"] = None
        state_mod.save_state(state, updated_by="subagent_stop")
    except Exception:
        pass
    return allow_silent()


# --------- Stop (scoped build/test gate) ---------

STOP_RUN_STAGES = {"DEV", "REVIEW_DEV", "TEST_EXECUTE"}
STOP_CACHE_FILE = REPO_ROOT / "harness" / ".stop-cache.json"
STOP_TIMEOUT_SEC = 600
_HASH_SKIP_DIRS = {
    ".git", "node_modules", "target", "build", ".gradle", "dist", "out",
    ".venv", "venv", "__pycache__", ".dart_tool", ".idea", "coverage", ".next",
}


def _matrix_boundary(boundary_id: str) -> dict | None:
    f = REPO_ROOT / "harness" / "SERVICE-BOUNDARY-MATRIX.json"
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    boundaries = data.get("boundaries", []) if isinstance(data, dict) else data
    for b in boundaries:
        if isinstance(b, dict) and b.get("boundary_id") == boundary_id:
            return b
    return None


def _service_hash(folder: Path) -> str:
    """Content hash của folder (bỏ build artifact) — đổi code thì hash đổi."""
    h = hashlib.sha256()
    for root, dirs, files in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if d not in _HASH_SKIP_DIRS)
        for name in sorted(files):
            p = Path(root) / name
            try:
                h.update(str(p.relative_to(folder)).encode("utf-8"))
                h.update(p.read_bytes())
            except OSError:
                continue
    return h.hexdigest()


def _build_test_cmd(kind: str, folder: Path) -> list[str] | None:
    """Lệnh build+test theo kind, detect build tool. None = không nhận diện được."""
    if kind == "backend":
        # Gradle = default harness → ưu tiên; Maven chỉ khi ADR chọn (pom.xml).
        if (folder / "build.gradle").is_file() or (folder / "build.gradle.kts").is_file():
            gradlew = folder / "gradlew"
            return [str(gradlew) if gradlew.is_file() else "gradle", "test"]
        if (folder / "pom.xml").is_file():
            return ["mvn", "-q", "-B", "test"]
    elif kind in ("bff", "web"):
        if (folder / "package.json").is_file():
            return ["npm", "test", "--silent"]
    elif kind == "mobile":
        if (folder / "pubspec.yaml").is_file():
            return ["flutter", "test"]
    return None


def _read_stop_cache() -> dict:
    try:
        return json.loads(STOP_CACHE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _write_stop_cache(cache: dict, boundary: str, entry: dict) -> None:
    cache[boundary] = entry
    try:
        STOP_CACHE_FILE.write_text(
            json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError:
        pass


def _stop_check_boundary(state: dict, boundary: str, cache: dict) -> str | None:
    """Build/test 1 boundary scoped theo kind. None = pass/skip; trả message nếu FAIL."""
    b = _matrix_boundary(boundary)
    if not b:
        return None
    prefix = b.get("prefix") or (state.get("project") or {}).get("service_prefix") or ""
    kind = b.get("kind", "backend")
    folder = REPO_ROOT / "services" / f"{prefix}-{boundary}"
    if not folder.is_dir():
        return None  # code chưa scaffold → không gate

    cmd = _build_test_cmd(kind, folder)
    if not cmd:
        return None  # không nhận diện build tool

    cur_hash = _service_hash(folder)
    cached = cache.get(boundary, {})
    if cached.get("hash") == cur_hash:
        if cached.get("result") == "pass":
            return None  # code không đổi + lần trước xanh → skip rerun
        return cached.get("output") or f"build/test FAIL (cached) — boundary {boundary}"

    try:
        proc = subprocess.run(
            cmd, cwd=str(folder), capture_output=True, text=True, timeout=STOP_TIMEOUT_SEC
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as e:
        sys.stderr.write(f"Stop hook: không chạy được {cmd} ({e}) — fail-open\n")
        return None  # thiếu tool / timeout → không chặn dev

    if proc.returncode != 0:
        tail = "\n".join((proc.stdout + proc.stderr).strip().splitlines()[-40:])
        msg = f"`{' '.join(cmd)}` FAIL (kind={kind}, boundary={boundary}). 40 dòng cuối:\n{tail}"
        _write_stop_cache(cache, boundary, {"hash": cur_hash, "result": "fail", "output": msg})
        return msg

    _write_stop_cache(cache, boundary, {"hash": cur_hash, "result": "pass"})
    return None


def handle_stop(payload: dict) -> int:
    """
    Quality gate cuối turn: stage ∈ {DEV, REVIEW_DEV, TEST_EXECUTE} → build/test scoped theo kind
    cho MỌI boundary trong wave (A-1: không chỉ active_boundary — boundary đỏ bị bỏ lại khi MAIN
    /start-dev boundary kế vẫn bị bắt ở turn stop kế). Fail → block kèm 40 dòng cuối. Cache
    content-hash để skip boundary sạch. Fail-open mọi lỗi hạ tầng (thiếu tool / timeout).
    """
    try:
        state = state_mod.load_state()
    except Exception:
        return allow_silent()

    if state.get("stage") not in STOP_RUN_STAGES:
        return allow_silent()
    boundaries = state.get("wave_boundaries") or []
    if not boundaries:
        b = state.get("active_boundary")
        boundaries = [b] if b else []
    if not boundaries:
        return allow_silent()

    cache = _read_stop_cache()
    fails: list[str] = []
    for bid in boundaries:
        msg = _stop_check_boundary(state, bid, cache)
        if msg:
            fails.append(msg)
    if fails:
        return stop_block("\n\n---\n\n".join(fails))
    return allow_silent()


# ========================================================================
# Main
# ========================================================================

HANDLERS = {
    "SessionStart": handle_session_start,
    "UserPromptSubmit": handle_user_prompt_submit,
    "Notification": handle_notification,
    "PreCompact": handle_pre_compact,
    "SessionEnd": handle_session_end,
    "PreToolUse": handle_pre_tool_use,
    "PostToolUse": handle_post_tool_use,
    "SubagentStop": handle_subagent_stop,
    "Stop": handle_stop,
}


def _selftest() -> int:
    """Hermetic test cho _pre_skill (chặn MAIN tự chạy harness slash-command) + _skill_name."""
    import io, contextlib
    import gates
    # _skill_name parsing
    assert _skill_name({"tool_input": {"skill": "test-plan"}}) == "test-plan"
    assert _skill_name({"tool_input": {"command": "/dev-handoff order-mgmt"}}) == "dev-handoff"
    assert _skill_name({"tool_input": {"skill": "plugin:test-execute"}}) == "test-execute"
    assert _skill_name({"tool_input": {}}) == ""

    def _cap(payload):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            _pre_skill(payload)
        return buf.getvalue()

    # SlashCommand tool = MAIN chạy lệnh harness (tự nối pipeline) → deny
    for cmd in ("/test-plan", "/test-execute", "/dev-handoff", "/start-wave"):
        out = _cap({"tool_name": "SlashCommand", "tool_input": {"command": cmd}})
        assert '"permissionDecision": "deny"' in out and cmd.lstrip("/") in out, f"{cmd}: {out!r}"
    # Skill tool = sub-agent LOAD convention skill (kể cả tên trùng harness command) → ALLOW (vá chặn oan)
    for cmd in ("domain-po", "domain-ba", "test-plan", "test-execute", "ux-design"):
        assert _cap({"tool_name": "Skill", "tool_input": {"skill": cmd}}) == "", f"Skill '{cmd}' phải allow: {cmd}"
    # skill/command ngoài-harness → allow
    for other in ("deep-research", "code-review", "verify"):
        assert _cap({"tool_name": "SlashCommand", "tool_input": {"command": f"/{other}"}}) == "", other
    # empty → allow
    assert _cap({"tool_name": "SlashCommand", "tool_input": {}}) == ""
    # sanity: GATE_RULES chứa harness cmds
    assert {"dev-handoff", "test-plan", "test-execute"} <= set(gates.GATE_RULES)
    # #12 stage-gate: chặn edit services CHỈ ở DEV_HANDOFF + cờ dev-handoff-agent
    assert _handoff_no_code_fix("DEV_HANDOFF", "dev-handoff-agent", "services/x/A.java") is True
    # cờ kẹt nhưng đã sang stage khác (fix Mode B) → KHÔNG chặn oan
    assert _handoff_no_code_fix("REVIEW_DEV", "dev-handoff-agent", "services/x/A.java") is False
    assert _handoff_no_code_fix("MANUAL_TEST", "dev-handoff-agent", "services/x/A.java") is False
    assert _handoff_no_code_fix("DEV", "dev-handoff-agent", "services/x/A.java") is False
    # đúng stage nhưng không phải services/ (vd docker-compose.yml) → cho qua
    assert _handoff_no_code_fix("DEV_HANDOFF", "dev-handoff-agent", "docs/architecture/infra/docker-compose.yml") is False
    # không có cờ → cho qua
    assert _handoff_no_code_fix("DEV_HANDOFF", None, "services/x/A.java") is False
    print("OK: dispatcher.py selftest passed")
    return 0


def main() -> int:
    # UTF-8 console on Windows
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--event", choices=sorted(HANDLERS))
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return _selftest()
    if not args.event:
        ap.error("--event is required (or --selftest)")

    payload = _read_payload()
    handler = HANDLERS[args.event]

    try:
        return handler(payload)
    except Exception as e:
        # Fail-open: log to stderr, exit 0 (allow tool through)
        sys.stderr.write(f"hook dispatcher error [{args.event}]: {e}\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
