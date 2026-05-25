"""Task checklist — 12 câu trước/sau mỗi việc (session, task, write, transition, change).

Triggers: session_start | pre_task_check | post_task_log | pre_state_transition
          | post_state_transition | pre_write_check | on_change_detected
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from gate_runner import path_allowed_for_edit
from harness_lib import get_boundary, load_json, load_kg, repo_root

CheckStatus = Literal["pass", "warn", "fail", "skip", "info"]


def _norm_path(p: str) -> str:
    """Normalize absolute or relative path to repo-relative form."""
    import re as _re
    n = p.replace("\\", "/")
    try:
        _root = str(repo_root().resolve()).replace("\\", "/").rstrip("/") + "/"
        if n.replace("\\", "/").startswith(_root):
            return n[len(_root):]
    except Exception:
        pass
    n = n.lstrip("/")
    n = _re.sub(r"^[a-zA-Z]:[/\\\\]?", "", n)
    for prefix in ("adlc-design/", "Java/adlc-design/"):
        if n.startswith(prefix):
            n = n[len(prefix):]
            break
    return n

FEAT_ID_RE = re.compile(r"FEAT-\d{3,}", re.I)
AC_RE = re.compile(r"FEAT-\d{3,}:AC-\d+", re.I)
CR_RE = re.compile(r"CR-\d{3,}", re.I)
BUG_RE = re.compile(r"BUG-\d{3,}", re.I)

BLOCKING_CHECKS = frozenset({
    "owned_paths",
    "boundary_resolve",
    "agent_assigned",
    "blockers",
    "task_in_stage",
    "kg_completed",
})

TRIGGER_CHECKS: dict[str, list[str]] = {
    "session_start": [
        "feature",
        "feature_stage",
        "blockers",
        "kg_in_progress",
        "decisions",
        "why_linked",
    ],
    "pre_task_check": [
        "feature",
        "feature_stage",
        "agent_assigned",
        "boundary_resolve",
        "task_in_stage",
        "kg_completed",
        "kg_in_progress",
        "blockers",
        "decisions",
        "do_not_repeat",
        "why_linked",
    ],
    "pre_write_check": [
        "feature",
        "boundary_resolve",
        "owned_paths",
        "task_in_stage",
        "blockers",
        "do_not_repeat",
        "why_linked",
    ],
    "pre_state_transition": [
        "feature",
        "task_in_stage",
        "blockers",
        "kg_in_progress",
        "why_linked",
    ],
    "post_state_transition": ["feature", "feature_stage", "why_linked"],
    "post_task_log": ["kg_completed", "kg_in_progress", "why_linked"],
    "on_change_detected": [
        "owned_paths",
        "feature",
        "boundary_resolve",
        "why_linked",
    ],
}

INTAKE_STEP_AGENTS = {
    "requirement-analyst": "agents/requirement-analyst-agent.md",
    "business-analyst": "agents/business-analyst-agent.md",
    "solution-architect": "agents/solution-architect-agent.md",
    "program-planner": "agents/program-planner-agent.md",
}


@dataclass
class TaskHint:
    task_id: str | None = None
    feature_id: str | None = None
    boundary_id: str | None = None
    agent_file: str | None = None
    paths: list[str] = field(default_factory=list)
    command: str | None = None
    why: str | None = None
    linked_cr: str | None = None
    linked_bug: str | None = None
    trigger: str | None = None
    transition: str | None = None
    return_body: dict[str, Any] | None = None


@dataclass
class CheckItem:
    id: str
    question: str
    status: CheckStatus
    detail: str


@dataclass
class TaskCheckReport:
    trigger: str
    hint: TaskHint
    items: list[CheckItem] = field(default_factory=list)
    blocked: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "trigger": self.trigger,
            "blocked": self.blocked,
            "task": {
                "task_id": self.hint.task_id,
                "feature_id": self.hint.feature_id,
                "boundary_id": self.hint.boundary_id,
                "command": self.hint.command,
            },
            "checks": [
                {"id": i.id, "status": i.status, "question": i.question, "detail": i.detail}
                for i in self.items
            ],
        }


def _shared_kg() -> dict[str, Any]:
    path = repo_root() / "knowledge-base" / "shared.knowledge-graph.yaml"
    if not path.is_file():
        return {}
    rel = str(path.relative_to(repo_root())).replace("\\", "/")
    return load_kg(rel)


def _feat_path(feature_id: str) -> Path | None:
    root = repo_root()
    direct = root / "docs/architecture/feat" / f"{feature_id.upper()}.md"
    if direct.is_file():
        return direct
    feat_dir = root / "docs/architecture/feat"
    if not feat_dir.is_dir():
        return None
    for p in feat_dir.glob("FEAT-*.md"):
        if p.stem.upper() == feature_id.upper():
            return p
    return None


def _feat_stage(feature_id: str) -> str | None:
    p = _feat_path(feature_id)
    if not p:
        return None
    text = p.read_text(encoding="utf-8")
    m = re.search(r"^status:\s*(\S+)", text, re.M | re.I)
    if m:
        return m.group(1).lower()
    m = re.search(r"##\s*Status\s*\n+\s*(\S+)", text, re.I)
    return m.group(1).lower() if m else "unknown"


def _infer_feature(text: str | None, state: dict[str, Any]) -> str | None:
    if text:
        m = FEAT_ID_RE.search(text)
        if m:
            return m.group(0).upper()
    for f in state.get("features_in_flight") or []:
        m = FEAT_ID_RE.search(str(f))
        if m:
            return m.group(0).upper()
    return None


def _infer_task_id(text: str | None, body: dict | None) -> str | None:
    if text and AC_RE.search(text):
        return AC_RE.search(text).group(0).upper()
    if body:
        for key in ("completed", "task_id"):
            val = body.get(key)
            if isinstance(val, list) and val:
                first = str(val[0])
                if AC_RE.search(first) or FEAT_ID_RE.search(first):
                    return first
            if isinstance(val, str) and val.strip():
                return val.strip()
    return None


def _tokens(s: str) -> set[str]:
    return {t.lower() for t in re.findall(r"[a-zA-Z0-9_-]{4,}", s)}


def _match_do_not_repeat(task_text: str, entries: list[str]) -> list[str]:
    if not task_text or not entries:
        return []
    tt = _tokens(task_text)
    return [entry for entry in entries if tt & _tokens(entry)]


def _boundary_from_blob(blob: str) -> str | None:
    if not blob:
        return None
    m = re.search(r"--boundary\s+([a-z][a-z0-9_-]*)", blob, re.I)
    return m.group(1).lower() if m else None


def task_hint_from_context(
    state: dict[str, Any],
    payload: dict[str, Any] | None = None,
    *,
    trigger: str = "pre_task_check",
) -> TaskHint:
    payload = payload or {}
    ti = payload.get("tool_input") or payload.get("toolInput") or {}
    if not isinstance(ti, dict):
        ti = {}

    spawn = (state.get("spawn") or {}).get("active") or {}
    wf = state.get("workflow") or {}
    pipe = wf.get("pipeline") or {}

    paths: list[str] = list(payload.get("paths") or [])
    for key in ("path", "file_path", "filePath", "target_file"):
        for src in (payload, ti):
            if src.get(key):
                paths.append(str(src[key]).replace("\\", "/"))

    blob = str(payload.get("command") or payload.get("shell_command") or ti.get("command") or "")
    boundary = (
        payload.get("boundary_id")
        or _boundary_from_blob(blob)
        or spawn.get("boundary")
        or state.get("active_boundary")
    )
    agent = payload.get("agent_file") or spawn.get("agent_file")
    if not agent and pipe.get("active_step_id"):
        agent = INTAKE_STEP_AGENTS.get(pipe["active_step_id"])

    body = payload.get("return_body") or payload.get("body")
    task_blob = " ".join(
        filter(
            None,
            [payload.get("task_id"), payload.get("why"), blob, str(body) if body else None],
        )
    )
    task_id = _infer_task_id(task_blob, body if isinstance(body, dict) else None)
    feature_id = payload.get("feature_id") or _infer_feature(task_id or task_blob, state)

    why = payload.get("why")
    linked_cr = payload.get("cr_id")
    linked_bug = payload.get("bug_id")
    if not linked_cr:
        m = CR_RE.search(task_blob)
        if m:
            linked_cr = m.group(0).upper()
    if not linked_bug:
        m = BUG_RE.search(task_blob)
        if m:
            linked_bug = m.group(0).upper()
    if not linked_cr:
        cr_ev = (wf.get("evidence") or {}).get("apply-cr") or {}
        linked_cr = cr_ev.get("cr_id")
    if not why and linked_cr:
        why = f"CR {linked_cr}"
    if not why and linked_bug:
        why = f"Bug {linked_bug}"

    command = payload.get("command")
    if not command:
        m = re.search(r"(?:harness\.py|build_command_prompt\.py)\s+([\w-]+)", blob, re.I)
        if m:
            command = m.group(1)

    return TaskHint(
        task_id=task_id,
        feature_id=feature_id,
        boundary_id=str(boundary).lower() if boundary else None,
        agent_file=agent,
        paths=list(dict.fromkeys(_norm_path(p) for p in paths if p)),
        command=command,
        why=why,
        linked_cr=linked_cr,
        linked_bug=linked_bug,
        trigger=trigger,
        transition=payload.get("transition"),
        return_body=body if isinstance(body, dict) else None,
    )


def _check_feature(hint: TaskHint, state: dict[str, Any]) -> CheckItem:
    q = "Task này thuộc feature nào?"
    fid = hint.feature_id
    if not fid:
        inflight = state.get("features_in_flight") or []
        if inflight:
            return CheckItem("feature", q, "warn", f"Chưa xác định feature; features_in_flight={inflight}")
        stage = state.get("stage")
        if stage in ("IMPLEMENTATION", "SELF_REVIEW", "FIX_MANUAL_BUGS"):
            return CheckItem(
                "feature",
                q,
                "warn",
                "Dev stage nhưng chưa gắn FEAT — cần features_in_flight hoặc task_id FEAT-xxx:AC-n",
            )
        return CheckItem("feature", q, "skip", "Chưa có feature (intake/plan — OK)")
    if _feat_path(fid):
        return CheckItem("feature", q, "pass", fid)
    return CheckItem("feature", q, "warn", f"{fid} chưa có file docs/architecture/feat/{fid}.md")


def _check_feature_stage(hint: TaskHint, state: dict[str, Any]) -> CheckItem:
    q = "Feature đó đang ở stage nào?"
    fid = hint.feature_id
    if not fid:
        return CheckItem("feature_stage", q, "skip", "Không có feature_id")
    feat_st = _feat_stage(fid)
    return CheckItem(
        "feature_stage",
        q,
        "info",
        f"FEAT status={feat_st!r}; harness stage={state.get('stage')!r}",
    )


def _check_agent_assigned(hint: TaskHint, state: dict[str, Any]) -> CheckItem:
    q = "Agent hiện tại có đúng agent được assign không?"
    if not hint.boundary_id:
        pipe = (state.get("workflow") or {}).get("pipeline") or {}
        step_id = pipe.get("active_step_id")
        if step_id and hint.agent_file:
            exp = INTAKE_STEP_AGENTS.get(step_id)
            if exp and hint.agent_file.replace("\\", "/").endswith(exp.split("/")[-1]):
                return CheckItem("agent_assigned", q, "pass", f"Intake step agent khớp {exp}")
        return CheckItem("agent_assigned", q, "skip", "Không có boundary — intake/orchestrator")
    row = get_boundary(hint.boundary_id)
    if not row:
        return CheckItem("agent_assigned", q, "fail", f"Boundary {hint.boundary_id!r} không có trong matrix")
    expected = (row.get("agent") or "").replace("\\", "/")
    hint_agent = hint.agent_file
    if not hint_agent:
        spawn_active = (state.get("spawn") or {}).get("active") or {}
        hint_agent = spawn_active.get("agent_file")
    hint_agent = str(hint_agent or "").replace("\\", "/")
    if not hint_agent:
        return CheckItem("agent_assigned", q, "warn", f"Matrix agent={expected}; chưa biết agent đang spawn")
    if hint_agent.endswith(expected.split("/")[-1]) or hint_agent == expected:
        return CheckItem("agent_assigned", q, "pass", f"Agent khớp matrix: {expected}")
    return CheckItem(
        "agent_assigned",
        q,
        "fail",
        f"Agent {hint_agent!r} ≠ matrix {expected!r} cho boundary {hint.boundary_id!r}",
    )


def _check_boundary_resolve(hint: TaskHint, _state: dict[str, Any]) -> CheckItem:
    q = "Boundary có resolve được không?"
    if not hint.boundary_id:
        for p in hint.paths:
            m = re.search(r"services/([a-z][a-z0-9_-]+)/", p)
            if m and get_boundary(m.group(1)):
                return CheckItem("boundary_resolve", q, "pass", f"Suy ra từ path: {m.group(1)}")
        return CheckItem("boundary_resolve", q, "skip", "Không yêu cầu boundary")
    row = get_boundary(hint.boundary_id)
    if row:
        return CheckItem(
            "boundary_resolve",
            q,
            "pass",
            f"{hint.boundary_id} → {row.get('display_name', hint.boundary_id)}",
        )
    return CheckItem(
        "boundary_resolve",
        q,
        "fail",
        f"{hint.boundary_id!r} không trong SERVICE-BOUNDARY-MATRIX",
    )


def _check_owned_paths(hint: TaskHint, state: dict[str, Any], hook_cfg: dict[str, Any]) -> CheckItem:
    q = "File/tài liệu/code định sửa có nằm trong owned_paths không?"
    if not hint.paths:
        return CheckItem("owned_paths", q, "skip", "Không có path trong payload")
    bad = [
        p.replace("\\", "/").lstrip("/")
        for p in hint.paths
        if not path_allowed_for_edit(p.replace("\\", "/").lstrip("/"), state, hook_cfg)
    ]
    if bad:
        return CheckItem(
            "owned_paths",
            q,
            "fail",
            f"Ngoài owned_paths/allowlist: {bad}; owned_paths={state.get('owned_paths') or []}",
        )
    return CheckItem("owned_paths", q, "pass", f"OK: {hint.paths}")


def _check_task_in_stage(hint: TaskHint, state: dict[str, Any]) -> CheckItem:
    q = "Task này có nằm trong stage hiện tại không?"
    stage = state.get("stage")
    spawn_allowed = (state.get("spawn") or {}).get("allowed_stages") or []
    wf = state.get("workflow") or {}
    pipe = wf.get("pipeline") or {}

    if hint.command:
        allowed = wf.get("allowed_next") or []
        if hint.command not in allowed:
            return CheckItem(
                "task_in_stage",
                q,
                "fail",
                f"Command {hint.command!r} ∉ allowed_next={allowed!r}",
            )

    if pipe.get("active_step") and pipe.get("adlc_stage"):
        if stage == pipe["adlc_stage"]:
            return CheckItem(
                "task_in_stage",
                q,
                "pass",
                f"Intake step {pipe['active_step']} @ {stage}",
            )
        return CheckItem(
            "task_in_stage",
            q,
            "warn",
            f"stage={stage!r} ≠ pipeline.adlc_stage={pipe['adlc_stage']!r}",
        )

    if spawn_allowed and stage not in spawn_allowed:
        if (state.get("spawn") or {}).get("active"):
            return CheckItem("task_in_stage", q, "skip", "Orchestrator — không spawn dev")
        return CheckItem(
            "task_in_stage",
            q,
            "fail",
            f"stage={stage!r} không thuộc spawn.allowed_stages={spawn_allowed!r}",
        )

    return CheckItem("task_in_stage", q, "pass", f"stage={stage!r}")


def _check_kg_completed(hint: TaskHint, _state: dict[str, Any]) -> CheckItem:
    q = "KG có task này trong completed chưa?"
    if not hint.task_id:
        return CheckItem("kg_completed", q, "skip", "Không có task_id")
    completed = (_shared_kg().get("implementation") or {}).get("completed") or []
    for item in completed:
        if hint.task_id in str(item) or str(item) in hint.task_id:
            return CheckItem(
                "kg_completed",
                q,
                "fail",
                f"Đã completed trong KG: {item!r} — rule 1 no_redo",
            )
    return CheckItem("kg_completed", q, "pass", "Chưa có trong completed")


def _check_kg_in_progress(hint: TaskHint, _state: dict[str, Any]) -> CheckItem:
    q = "KG có task này đang in_progress chưa?"
    in_prog = (_shared_kg().get("implementation") or {}).get("in_progress") or []
    if not in_prog:
        return CheckItem("kg_in_progress", q, "info", "in_progress rỗng")
    if hint.task_id:
        for item in in_prog:
            if hint.task_id in str(item) or str(item) in hint.task_id:
                return CheckItem("kg_in_progress", q, "pass", f"Đang in_progress: {item!r}")
        return CheckItem(
            "kg_in_progress",
            q,
            "warn",
            f"Task {hint.task_id!r} chưa in_progress; KG có {in_prog!r} — rule 2",
        )
    return CheckItem("kg_in_progress", q, "info", f"in_progress={in_prog}")


def _check_blockers(hint: TaskHint, _state: dict[str, Any]) -> CheckItem:
    q = "Có blocker/open question nào đang chặn không?"
    blockers = list((_shared_kg().get("discipline") or {}).get("blockers") or [])
    if blockers:
        detail = "\n".join(f"  - {b}" for b in blockers)
        kind: CheckStatus = "warn" if hint.linked_cr else "fail"
        return CheckItem("blockers", q, kind, f"discipline.blockers:\n{detail}")
    return CheckItem("blockers", q, "pass", "Không có blocker")


def _check_decisions(hint: TaskHint, _state: dict[str, Any]) -> CheckItem:
    q = "Có accepted decision nào liên quan không?"
    decisions = _shared_kg().get("decisions") or []
    active = [d for d in decisions if isinstance(d, dict) and d.get("status", "active") == "active"]
    if not active:
        return CheckItem("decisions", q, "info", "Không có decision active")
    related: list[str] = []
    needle = " ".join(filter(None, [hint.feature_id, hint.task_id, hint.boundary_id])).lower()
    for d in active:
        blob = f"{d.get('id', '')} {d.get('context', '')} {d.get('decision', '')}".lower()
        if hint.feature_id and hint.feature_id.lower() in blob:
            related.append(str(d.get("id")))
        elif needle and any(part.lower() in blob for part in needle.split() if len(part) > 3):
            related.append(str(d.get("id")))
    if related:
        return CheckItem("decisions", q, "info", f"Decision liên quan: {related} — rule 4")
    return CheckItem("decisions", q, "info", f"{len(active)} decision active; không match task")


def _check_do_not_repeat(hint: TaskHint, _state: dict[str, Any]) -> CheckItem:
    q = "Có do_not_repeat rule nào match không?"
    kg = _shared_kg()
    entries = list((kg.get("discipline") or {}).get("do_not_repeat") or []) + list(
        (kg.get("learnings") or {}).get("gotchas") or []
    )
    task_text = " ".join(filter(None, [hint.task_id, hint.why, hint.command]))
    hits = _match_do_not_repeat(task_text, entries)
    if hits:
        return CheckItem(
            "do_not_repeat",
            q,
            "warn",
            "Match do_not_repeat/gotcha:\n" + "\n".join(f"  - {h}" for h in hits[:5]),
        )
    return CheckItem("do_not_repeat", q, "pass", "Không match do_not_repeat")


def _check_why_linked(hint: TaskHint, state: dict[str, Any]) -> CheckItem:
    q = "Tại sao / link requirement-feature-bug-CR?"
    parts = []
    if hint.why:
        parts.append(f"why={hint.why}")
    if hint.feature_id:
        parts.append(f"feature={hint.feature_id}")
    if hint.linked_cr:
        parts.append(f"CR={hint.linked_cr}")
    if hint.linked_bug:
        parts.append(f"bug={hint.linked_bug}")
    if hint.task_id:
        parts.append(f"task={hint.task_id}")
    wf = state.get("workflow") or {}
    if wf.get("active_command"):
        parts.append(f"command={wf['active_command']}")
    if parts:
        return CheckItem("why_linked", q, "pass", "; ".join(parts))
    stage = state.get("stage")
    if stage in (
        "BOOTSTRAP",
        "REQUIREMENT_INTAKE",
        "BUSINESS_ANALYSIS",
        "TECHNICAL_DESIGN",
        "IMPLEMENTATION_PLAN",
    ):
        return CheckItem("why_linked", q, "info", f"Intake/plan @ {stage}")
    return CheckItem(
        "why_linked",
        q,
        "warn",
        "Thiếu why / FEAT / CR / bug — ghi rõ trước khi dev",
    )


CHECK_FNS = {
    "feature": _check_feature,
    "feature_stage": _check_feature_stage,
    "agent_assigned": _check_agent_assigned,
    "boundary_resolve": _check_boundary_resolve,
    "owned_paths": _check_owned_paths,
    "task_in_stage": _check_task_in_stage,
    "kg_completed": _check_kg_completed,
    "kg_in_progress": _check_kg_in_progress,
    "blockers": _check_blockers,
    "decisions": _check_decisions,
    "do_not_repeat": _check_do_not_repeat,
    "why_linked": _check_why_linked,
}


def run_checklist(
    trigger: str,
    state: dict[str, Any],
    payload: dict[str, Any] | None = None,
    *,
    hook_rules: dict[str, Any] | None = None,
    block: bool | None = None,
) -> TaskCheckReport:
    hook_rules = hook_rules or load_json(repo_root() / "harness" / "HOOK-RULES.json")
    owned_cfg = hook_rules.get("hooks", {}).get("owned_paths", {})
    cfg = hook_rules.get("hooks", {}).get("task_checklist", {})
    check_ids = TRIGGER_CHECKS.get(trigger, cfg.get("checks") or list(CHECK_FNS.keys()))
    hint = task_hint_from_context(state, payload, trigger=trigger)
    report = TaskCheckReport(trigger=trigger, hint=hint)

    for cid in check_ids:
        fn = CHECK_FNS.get(cid)
        if not fn:
            continue
        if cid == "owned_paths":
            item = fn(hint, state, owned_cfg)
        else:
            item = fn(hint, state)
        report.items.append(item)

    should_block = block
    if should_block is None:
        should_block = trigger not in (
            "session_start",
            "post_state_transition",
        )
    if should_block:
        for item in report.items:
            if item.id in BLOCKING_CHECKS and item.status == "fail":
                report.blocked = True
                break
            if item.id in (cfg.get("block_on_warn") or []) and item.status in ("fail", "warn"):
                report.blocked = True
                break

    return report


def format_report(report: TaskCheckReport, *, verbose: bool = True) -> str:
    lines = [f"HARNESS TASK CHECK — {report.trigger}"]
    if report.blocked:
        lines[0] += " [BLOCKED]"
    for item in report.items:
        if not verbose and item.status in ("pass", "skip", "info"):
            continue
        lines.append(f"  [{item.status.upper():4}] {item.question}")
        lines.append(f"         {item.detail}")
    if report.blocked:
        lines.append("HARNESS — KHÔNG ĐƯỢC PHÉP. Sửa checklist trên trước khi tiếp tục.")
    return "\n".join(lines)


def run_trigger(
    trigger: str,
    state: dict[str, Any],
    payload: dict[str, Any] | None = None,
    *,
    block: bool | None = None,
) -> TaskCheckReport:
    return run_checklist(trigger, state, payload, block=block)


def session_brief(state: dict[str, Any], report: TaskCheckReport) -> str:
    wf = state.get("workflow") or {}
    lines = [
        "Harness session — đọc trước khi làm:",
        f"- stage: {state.get('stage')}",
        f"- allowed_next: {wf.get('allowed_next')}",
        f"- pipeline: {wf.get('pipeline')}",
        f"- features_in_flight: {state.get('features_in_flight')}",
    ]
    for item in report.items:
        if item.status in ("fail", "warn"):
            lines.append(f"- [{item.status}] {item.id}: {item.detail}")
    return "\n".join(lines)


def validate_post_task_log(body: dict[str, Any]) -> CheckItem | None:
    changed = body.get("files_changed") or []
    completed = body.get("completed") or []
    if not changed and not completed:
        return None
    kg = body.get("kg_appended") or []
    deferred = body.get("deferred") or []
    if kg:
        return CheckItem("post_task_log", "Ghi KG sau task", "pass", f"kg_appended={kg}")
    if deferred and all(isinstance(d, dict) and d.get("tracked_in") for d in deferred):
        return CheckItem("post_task_log", "Ghi KG sau task", "pass", "deferred tracked")
    return CheckItem(
        "post_task_log",
        "Ghi KG sau task",
        "fail",
        "files_changed/completed có dữ liệu nhưng thiếu kg_appended hoặc deferred.tracked_in",
    )
