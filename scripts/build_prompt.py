"""
Build self-contained spawn prompt for harness commands.

Pattern: pointer-heavy (Tier-C). Inline only STATE bundle, non-negotiables,
owned_paths, skills list, tasks, return schema. Doc files are linked by path —
sub-agent uses Read tool to fetch when needed.

Usage:
  py scripts/build_prompt.py <command> [options]

Options:
  --boundary X        # for start-dev, review-dev, dev-handoff, fix-bugs
  --step N            # for intake-requirement (1-4)
  --wave N            # for start-wave
  --bug-id BUG-NNN    # for fix-bugs
  --cr-id CR-NNN      # for apply-cr
  --stats             # print size breakdown instead of full prompt
  --save PATH         # write to file (and to stdout)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))

import state as state_mod  # noqa: E402

MATRIX_FILE = REPO / "harness" / "SERVICE-BOUNDARY-MATRIX.json"


# ========================================================================
# Loaders
# ========================================================================

def load_matrix() -> list[dict]:
    if not MATRIX_FILE.exists():
        return []
    try:
        data = json.loads(MATRIX_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("boundaries", [])
    except json.JSONDecodeError:
        pass
    return []


def find_boundary(matrix: list[dict], boundary_id: str) -> dict | None:
    for b in matrix:
        if b.get("boundary_id") == boundary_id or b.get("id") == boundary_id:
            return b
    return None


# ========================================================================
# Static blocks
# ========================================================================

NON_NEGOTIABLES = """## NON-NEGOTIABLES

1. Đọc `harness/STATE.json` trước mọi tool call (xem header `[HARNESS ...]` injected).
2. Edit chỉ trong `owned_paths` của `active_boundary` — hook block ngoài.
3. Stage transition CHỈ qua slash command, KHÔNG sửa `stage` trong STATE.json bằng tay.
4. Quyết định non-trivial → artifact ngay (ADR / FEAT / CR / KG).
5. Cross-boundary change → `/apply-cr` + `/review-document` (chỉ từ DONE state).
6. Không bypass test (`--no-verify`, skip), không hardcode secrets."""


RETURN_SCHEMA_TEMPLATE = """## RETURN SCHEMA

Dòng cuối message PHẢI là JSON object đúng schema dưới:

```json
{
  "completed": ["FEAT-XXX:AC-1"],
  "deferred": [{"item":"...", "reason":"...", "tracked_in":"BUG-NNN"}],
  "needs_review": [{"file":"path", "concern":"..."}],
  "files_changed": ["path1"],
  "kg_appended": ["entity:Order", "decision:DEC-001"],
  "build": "pass|fail",
  "lint": "pass|fail",
  "test": "pass|fail",
  "coverage_pct": 82
}
```

Hook SubagentStop validate. Thiếu field → warn. `files_changed` non-empty mà `kg_appended` rỗng → warn."""


PRE_EDIT_CHECKLIST = """## PRE-EDIT CHECKLIST (FM-017)

Trước mỗi Edit/Write/MultiEdit, tự classify intent:

**Additive (proceed):** file mới, method/field mới, comment, import mới.
**Non-additive (STOP, return early `needs_review`):** modify existing method body, rename, delete, signature change, refactor.
**Forbidden:** modify applied migration, force-push, --no-verify."""


# ========================================================================
# Skill mapping
# ========================================================================

PRIMARY_SKILLS_PER_KIND = {
    "backend": ["rules-backend"],
    "bff": ["rules-bff"],
    "web": ["rules-web"],
    "mobile": ["rules-mobile"],
}

REVIEW_SKILLS_PER_KIND = {
    "backend": ["review-backend"],
    "bff": ["review-bff"],
    "web": ["review-web"],
    "mobile": ["review-mobile"],
}

REF_SKILLS_PER_KIND = {
    "backend": ["ref-backend-config", "ref-backend-pattern", "ref-backend-redis", "ref-backend-kafka", "ref-backend-logging"],
    "bff": [],
    "web": ["ref-frontend-config", "ref-frontend-pattern"],
    "mobile": [],
}


# ========================================================================
# Prompt sections
# ========================================================================

def state_bundle(state: dict, extras: dict | None = None) -> str:
    bundle = {
        "stage": state.get("stage"),
        "wave": (state.get("wave") or {}).get("id"),
        "service_prefix": (state.get("project") or {}).get("service_prefix"),
        "active_boundary": state.get("active_boundary"),
        "wave_boundaries": state.get("wave_boundaries"),
    }
    if extras:
        bundle.update(extras)
    lines = ["## STATE BUNDLE (frozen at spawn)\n"]
    for k, v in bundle.items():
        lines.append(f"- {k}: {v}")
    return "\n".join(lines)


def owned_paths_block(boundary_info: dict | None) -> str:
    if not boundary_info:
        return "## OWNED_PATHS\n\n(no active boundary)"
    paths = boundary_info.get("owned_paths", [])
    lines = ["## OWNED_PATHS (Edit chỉ trong các pattern này)\n"]
    for p in paths:
        lines.append(f"- {p}")
    return "\n".join(lines)


def skills_block(skills: list[str], available: list[str] | None = None, note: str = "") -> str:
    """Primary skills = load ngay khi start. Available = on-demand qua Skill tool khi cần."""
    head = "## SKILLS\n"
    if note:
        head += f"\n_{note}_\n"
    parts = []
    if skills:
        parts.append("**Primary (invoke ngay):**\n" + "\n".join(f"- `{s}`" for s in skills))
    else:
        parts.append("**Primary:** (none — command này không cần skill primary)")
    if available:
        parts.append(
            "\n**Available on-demand** (chỉ invoke khi gặp tình huống cụ thể):\n"
            + "\n".join(f"- `{s}`" for s in available)
        )
    return head + "\n" + "\n".join(parts)


def docs_to_read(items: list[tuple[str, str]]) -> str:
    """items = [(label, relative_path), ...] — agent uses Read tool to fetch."""
    head = "## DOCS TO READ (use Read tool when needed)\n"
    if not items:
        return head + "\n(none)"
    body = "\n".join(f"- **{label}**: `{path}`" for label, path in items)
    return head + "\n" + body


def tasks_block(items: list[str]) -> str:
    head = "## TASKS\n"
    body = "\n".join(f"{i+1}. {t}" for i, t in enumerate(items))
    return head + "\n" + body


# ========================================================================
# Per-command builders
# ========================================================================

def build_intake_requirement(state: dict, matrix: list[dict], opts: dict) -> str:
    step = int(opts.get("step") or 1)
    step_specs = {
        1: {
            "agent": "requirement-analyst-agent",
            "skill": "requirement-analysis",
            "output": "docs/architecture/PROJECT.md + FEAT-*.md draft + chốt project.service_prefix",
        },
        2: {
            "agent": "business-analyst-agent",
            "skill": "business-analysis",
            "output": "FEAT-*.md refine (AC testable + BR + boundaries_suggested)",
        },
        3: {
            "agent": "solution-architect-agent",
            "skill": "technical-design",
            "output": "ADR + HLD + API + data-model + UX + events + integrations per boundary",
        },
        4: {
            "agent": "program-planner-agent",
            "skill": "implementation-plan",
            "output": "docs/plans/WAVE-SEQUENCE.md + wave-{N}.md cho MỌI wave + harness/SERVICE-BOUNDARY-MATRIX.json + KG skeleton per boundary",
        },
    }
    spec = step_specs.get(step, step_specs[1])

    parts = [
        f"# SPAWN PROMPT — /intake-requirement step {step}",
        f"\nAgent: **{spec['agent']}** · Skill: `{spec['skill']}` · Output: {spec['output']}",
        state_bundle(state, {"step": step, "input": opts.get("input")}),
        NON_NEGOTIABLES,
        skills_block([spec["skill"]]),
        docs_to_read([
            ("PROJECT (if exists)", "docs/architecture/PROJECT.md"),
            ("FEAT (if exists)", "docs/architecture/feat/FEAT-*.md"),
            ("ADR existing", "docs/architecture/adr/ADR-*.md"),
        ]),
        tasks_block([
            f"Invoke skill `{spec['skill']}` để load checklist + format.",
            f"Produce artifact: {spec['output']}",
            "Hỏi user: 'OK với output này chưa? Cần chỉnh gì?'",
            "Iterate cho tới khi user confirm (không giới hạn số vòng).",
            "Sau user confirm: return RETURN SCHEMA với `user_confirmed: true`, `step: " + str(step) + "`",
        ]),
        RETURN_SCHEMA_TEMPLATE,
    ]
    return "\n\n".join(parts)


def build_review_document(state: dict, matrix: list[dict], opts: dict) -> str:
    feedback = opts.get("feedback") or ""
    has_feedback = bool(feedback.strip())
    mode = "revision" if has_feedback else "sanity-check"
    target_file = opts.get("target_file")

    if mode == "revision":
        tasks = [
            f"Parse feedback từ user: \"{feedback}\"",
            f"Nếu có --file target ({target_file or 'N/A'}): focus revise file đó.",
            "Else: identify file relevant nhất từ feedback → revise file đó.",
            "Read file target (Read tool) → understand current content.",
            "Edit file theo feedback (Edit tool) — preserve format, chỉ sửa intent.",
            "Re-read sau Edit để verify đã sửa đúng.",
            "Return summary các thay đổi cụ thể.",
        ]
        section_label = f"## REVISION TASK\n\nFeedback từ user: **\"{feedback}\"**" + (f"\nTarget file: `{target_file}`" if target_file else "")
    else:
        tasks = [
            "Sanity check toàn bộ intake artifacts (KHÔNG sửa file).",
            "Read PROJECT.md → check scope, NFR, glossary đủ?",
            "Read FEAT-*.md → check AC testable, có BR rules?",
            "Read ADR-*.md → ≥ 3 file, có rationale?",
            "Read HLD/API/data-model/UX per boundary → đủ per boundary?",
            "Read WAVE-SEQUENCE + wave-001 + MATRIX → consistent?",
            "Return issues[] với cụ thể file + concern.",
            "User dùng kết quả để quyết định feedback cho call tiếp.",
        ]
        section_label = "## SANITY CHECK TASK\n\nNo feedback provided. Mode: sanity check — output issues list, KHÔNG sửa file."

    parts = [
        f"# SPAWN PROMPT — /review-document ({mode})",
        f"\nAgent: **review-document-agent** · Mode: `{mode}`",
        state_bundle(state, {"mode": mode, "has_feedback": has_feedback}),
        NON_NEGOTIABLES,
        section_label,
        skills_block(["business-analysis"], note="Skill check business rules + AC testability."),
        docs_to_read([
            ("PROJECT", "docs/architecture/PROJECT.md"),
            ("FEAT all", "docs/architecture/feat/FEAT-*.md"),
            ("ADR all", "docs/architecture/adr/ADR-*.md"),
            ("HLD per boundary", "docs/architecture/hld/hld-*.md"),
            ("API per boundary", "docs/architecture/api/api-*.md"),
            ("data-model per boundary", "docs/architecture/data-model/data-model-*.md"),
            ("UX per boundary", "docs/architecture/ux/ux-*.md"),
            ("Events per boundary", "docs/architecture/events/*-events.md"),
            ("Integrations", "docs/architecture/integrations/INTEG-*.md"),
            ("WAVE-SEQUENCE", "docs/plans/WAVE-SEQUENCE.md"),
            ("Wave plans", "docs/plans/wave-*.md"),
            ("MATRIX", "harness/SERVICE-BOUNDARY-MATRIX.json"),
        ]),
        tasks_block(tasks),
        RETURN_SCHEMA_TEMPLATE + "\n\nExtra fields:\n- `mode`: `revision` | `sanity-check`\n- `issues`: `[{file, concern}]` (sanity-check)\n- `revisions`: `[{file, summary}]` (revision)\n- `feedback_processed`: `true` (set khi mode=revision đã apply)",
    ]
    return "\n\n".join(parts)


def build_approve_document(state: dict, matrix: list[dict], opts: dict) -> str:
    parts = [
        "# SPAWN PROMPT — /approve-document",
        "\n**Instant action** — KHÔNG spawn sub-agent. Pure CLI complete.",
        state_bundle(state),
        NON_NEGOTIABLES,
        "## TASK\n\n1. Ask user explicit confirm.\n2. User reply 'yes' → run `py scripts/harness.py approve-document complete '{\"approved\":true}'`.\n3. User reply 'no' → cancel, suggest /review-document.\n4. Sau approve: report 'Approved. Run /start-wave 1 để mở wave đầu tiên.'",
    ]
    return "\n\n".join(parts)


def build_start_wave(state: dict, matrix: list[dict], opts: dict) -> str:
    wave_n = int(opts.get("wave") or 1)
    parts = [
        f"# SPAWN PROMPT — /start-wave {wave_n}",
        f"\nAgent: **start-wave-agent** · Materialize per-boundary agents + KG + scaffold cho wave-{wave_n:03d}.",
        state_bundle(state, {"wave_n": wave_n}),
        NON_NEGOTIABLES,
        skills_block([]),
        docs_to_read([
            (f"Wave plan", f"docs/plans/wave-{wave_n:03d}.md"),
            ("MATRIX", "harness/SERVICE-BOUNDARY-MATRIX.json"),
            ("WAVE-SEQUENCE", "docs/plans/WAVE-SEQUENCE.md"),
        ]),
        tasks_block([
            f"Read wave-{wave_n:03d}.md để biết boundaries + features tham gia wave.",
            "Read MATRIX để có metadata (kind, prefix, tech, owned_paths) per boundary.",
            f"Run `py scripts/materialize.py --wave {wave_n}` (materialize sẽ gen agents/{{prefix-boundary}}-agent.md + knowledge-base/{{prefix-boundary}}.kg.yaml per boundary).",
            "Verify file đã tồn tại sau materialize.",
            f"Return RETURN SCHEMA với `approved: true`, `wave_n: {wave_n}`.",
        ]),
        RETURN_SCHEMA_TEMPLATE,
    ]
    return "\n\n".join(parts)


def build_boundary_command(
    state: dict, matrix: list[dict], opts: dict, command: str
) -> str:
    """Generic builder for boundary-scoped commands: start-dev, review-dev, fix-bugs."""
    boundary_id = opts.get("boundary") or state.get("active_boundary") or "<unknown>"
    boundary = find_boundary(matrix, boundary_id) or {}
    kind = boundary.get("kind", "backend")
    prefix = boundary.get("prefix") or (state.get("project") or {}).get("service_prefix") or "<prefix>"
    service_folder = boundary.get("service_folder") or f"services/{prefix}-{boundary_id}"
    wave_id = (state.get("wave") or {}).get("id") or "<unknown-wave>"

    if command == "start-dev":
        agent_name = f"dev-{prefix}-{boundary_id}-agent"
        skills = PRIMARY_SKILLS_PER_KIND.get(kind, [])
        ref_skills = REF_SKILLS_PER_KIND.get(kind, [])
        task_list = [
            f"Invoke primary skill `{PRIMARY_SKILLS_PER_KIND.get(kind, ['rules-?'])[0]}` để load convention.",
            "Read HLD + API + data-model + KG của boundary.",
            f"If `{service_folder}/` chưa có code: scaffold theo skill (pom.xml/package.json/pubspec.yaml + folder structure).",
            f"Đọc `docs/plans/{wave_id}.md` §'Features in scope' → lọc dòng có `Boundary == {boundary_id}` = tập FEAT của boundary này; đọc AC trong từng `FEAT-*.md` tương ứng rồi implement.",
            "Run scoped build/test (mvn -pl ./ test cho backend; npm test cho bff/web; flutter test cho mobile).",
            "Append KG: entities, business_rules, events_published khi code.",
            "Return RETURN SCHEMA.",
        ]
    elif command == "review-dev":
        agent_name = f"review-{kind}-agent (singleton)"
        skills = REVIEW_SKILLS_PER_KIND.get(kind, [])
        ref_skills = PRIMARY_SKILLS_PER_KIND.get(kind, [])  # review: chỉ rules-{kind} (WHAT), KHÔNG nạp ref how-to
        task_list = [
            f"Invoke skill `{(REVIEW_SKILLS_PER_KIND.get(kind) or ['review-?'])[0]}`.",
            f"Review code trong `{service_folder}/` theo checklist skill.",
            "Phát hiện issue (coverage<80, lint, convention) → spawn fix sub-agent.",
            "Loop review + fix tới pass.",
            "Append learnings.gotchas vào KG nếu phát hiện pattern xấu.",
            "Return RETURN SCHEMA với `review_result: pass|fail` + `coverage_pct`.",
        ]
    elif command == "fix-bugs":
        bug_id = opts.get("bug_id") or "<BUG-NNN>"
        agent_name = f"fix-{prefix}-{boundary_id}-agent (then chain review-{kind}-agent)"
        skills = PRIMARY_SKILLS_PER_KIND.get(kind, []) + ["bug-logging"]
        ref_skills = REF_SKILLS_PER_KIND.get(kind, []) + REVIEW_SKILLS_PER_KIND.get(kind, [])
        task_list = [
            f"Read `tracking/wave-{{N}}/bugs.md` → tìm heading `## {bug_id}`.",
            "Đọc reproduction steps + expected vs actual.",
            f"Fix code trong `{service_folder}/` theo rules-{kind}.",
            "Verify fix: run scoped test pass.",
            f"Auto chain: spawn `review-{kind}-agent` verify regression.",
            f"If review pass: mark `## {bug_id}` `status: closed` in bugs.md.",
            "Append FM (failure mode) vào KG.",
            "Return RETURN SCHEMA với `bug_id`, `fix_verified: true`.",
        ]
    else:
        agent_name = "<unknown>"
        skills = []
        ref_skills = []
        task_list = ["<unknown command>"]

    parts = [
        f"# SPAWN PROMPT — /{command} --boundary {boundary_id}",
        f"\nAgent: **{agent_name}** · kind: `{kind}` · service folder: `{service_folder}`",
        state_bundle(state, {"command_boundary": boundary_id, "kind": kind}),
        NON_NEGOTIABLES,
        owned_paths_block(boundary),
        skills_block(skills, available=ref_skills, note="Invoke primary trước khi code. Ref-* CHỈ khi gặp tình huống cụ thể (vd: setup security, config kafka)."),
        docs_to_read([
            ("HLD", f"docs/architecture/hld/hld-{boundary_id}.md"),
            ("API", f"docs/architecture/api/api-{boundary_id}.md"),
            ("Data model", f"docs/architecture/data-model/data-model-{boundary_id}.md"),
            ("UX", f"docs/architecture/ux/ux-{boundary_id}.md"),
            ("Events", f"docs/architecture/events/{boundary_id}-events.md"),
            ("Integrations", f"docs/architecture/integrations/INTEG-*{boundary_id}*.md"),
            ("KG", f"knowledge-base/{prefix}-{boundary_id}.knowledge-graph.yaml"),
            ("Wave plan", f"docs/plans/{wave_id}.md"),
            ("Features", "docs/architecture/feat/FEAT-*.md (filter theo wave)"),
        ]),
        tasks_block(task_list),
        PRE_EDIT_CHECKLIST,
        RETURN_SCHEMA_TEMPLATE,
    ]
    return "\n\n".join(parts)


def build_dev_handoff(state: dict, matrix: list[dict], opts: dict) -> str:
    boundary_id = opts.get("boundary") or state.get("active_boundary") or "<unknown>"
    wave_id = (state.get("wave") or {}).get("id") or "<unknown-wave>"
    parts = [
        f"# SPAWN PROMPT — /dev-handoff",
        f"\nAgent: **dev-handoff-agent** · Verify infra + handoff ready.",
        state_bundle(state, {"command_boundary": boundary_id}),
        NON_NEGOTIABLES,
        skills_block(["infra-local-dev"]),
        docs_to_read([
            ("docker-compose", "docs/architecture/infra/docker-compose.yml"),
            ("Wave plan", f"docs/plans/{wave_id}.md"),
        ]),
        tasks_block([
            "Invoke skill `infra-local-dev`.",
            "Update docs/architecture/infra/docker-compose.yml thêm service mới (nếu chưa có).",
            "Verify `docker-compose up -d` thành công, services healthy.",
            f"Verify build local của boundary `{boundary_id}` pass.",
            "Return RETURN SCHEMA với `coverage_pct`, `review_result: pass`, `docker_compose_ok: true`.",
        ]),
        RETURN_SCHEMA_TEMPLATE,
    ]
    return "\n\n".join(parts)


def build_test_plan(state: dict, matrix: list[dict], opts: dict) -> str:
    wave_id = (state.get("wave") or {}).get("id") or "<unknown-wave>"
    parts = [
        "# SPAWN PROMPT — /test-plan",
        "\nAgent: **test-plan-agent** · Sinh test-case-registry cho wave.",
        state_bundle(state),
        NON_NEGOTIABLES,
        skills_block(["test-plan"]),
        docs_to_read([
            ("FEAT all", "docs/architecture/feat/FEAT-*.md"),
            ("API contracts", "docs/architecture/api/api-*.md"),
            ("UX", "docs/architecture/ux/ux-*.md"),
            ("Wave plan", f"docs/plans/{wave_id}.md"),
            ("Existing tests", f"tracking/{wave_id}/test-case-registry.md (if exists)"),
        ]),
        tasks_block([
            "Invoke skill `test-plan`.",
            "Foreach FEAT in wave: foreach AC: tạo TC-* entry.",
            f"Write to `tracking/{wave_id}/test-case-registry.md` (per skill format).",
            "Cover P0 (blocker), P1 (must-have), P2 (nice-to-have).",
            "Return RETURN SCHEMA với `test_cases_count: N`, `docker_compose_ok: true`.",
        ]),
        RETURN_SCHEMA_TEMPLATE,
    ]
    return "\n\n".join(parts)


def build_test_execute(state: dict, matrix: list[dict], opts: dict) -> str:
    wave_id = (state.get("wave") or {}).get("id") or "<unknown-wave>"
    parts = [
        "# SPAWN PROMPT — /test-execute",
        "\nAgent: **test-execute-agent** · Build local + run + internal fix loop.",
        state_bundle(state),
        NON_NEGOTIABLES,
        skills_block(["test-execute", "specialist-testing", "bug-logging", "infra-local-dev"]),
        docs_to_read([
            ("Test registry", f"tracking/{wave_id}/test-case-registry.md"),
            ("docker-compose", "docs/architecture/infra/docker-compose.yml"),
            ("Wave plan", f"docs/plans/{wave_id}.md"),
            ("API contracts", "docs/architecture/api/api-*.md"),
        ]),
        tasks_block([
            "docker-compose up -d, đợi healthy.",
            "Foreach TC in registry (P0 trước): run theo type (api/e2e/ui/...).",
            f"Append result vào `tracking/{wave_id}/test-report.md`.",
            f"Fail → log bug vào `tracking/{wave_id}/bugs.md` (origin: auto) + spawn fix sub-agent → re-test.",
            "Loop tới all P0 pass.",
            "Return RETURN SCHEMA với `test_result: pass`, `test_cases_count`, `bugs_logged: [...]`.",
            "Harness auto-transition TEST_EXECUTE → MANUAL_TEST khi test_result=pass.",
        ]),
        RETURN_SCHEMA_TEMPLATE,
    ]
    return "\n\n".join(parts)


def build_end_wave(state: dict, matrix: list[dict], opts: dict) -> str:
    wave_id = (state.get("wave") or {}).get("id") or "<unknown-wave>"
    parts = [
        "# SPAWN PROMPT — /end-wave",
        "\nAgent: **end-wave-agent** · Soft close wave sau UAT signed.",
        state_bundle(state),
        NON_NEGOTIABLES,
        skills_block([]),
        docs_to_read([
            ("Bugs", f"tracking/{wave_id}/bugs.md"),
            ("Test report", f"tracking/{wave_id}/test-report.md"),
            ("QC signoff", f"tracking/{wave_id}/qc-signoff.md"),
        ]),
        tasks_block([
            f"Verify `tracking/{wave_id}/bugs.md` không còn bug status != closed.",
            f"Write `tracking/{wave_id}/qc-signoff.md` với checklist + UAT signoff.",
            "Update KG execution_history per boundary: status=COMPLETED + end_date + deliverables.",
            "Return RETURN SCHEMA với `uat_signed: true`.",
        ]),
        RETURN_SCHEMA_TEMPLATE,
    ]
    return "\n\n".join(parts)


def build_done_wave(state: dict, matrix: list[dict], opts: dict) -> str:
    wave_id = (state.get("wave") or {}).get("id") or "<unknown-wave>"
    parts = [
        "# SPAWN PROMPT — /done-wave",
        "\nAgent: **done-wave-agent** · Hard close, teardown infra.",
        state_bundle(state),
        NON_NEGOTIABLES,
        skills_block(["infra-local-dev"]),
        docs_to_read([
            ("QC signoff", f"tracking/{wave_id}/qc-signoff.md"),
            ("docker-compose", "docs/architecture/infra/docker-compose.yml"),
        ]),
        tasks_block([
            "Verify QC signoff exists + signed.",
            "Run `docker-compose -f docs/architecture/infra/docker-compose.yml down --volumes` để teardown.",
            f"Archive wave artifacts: copy `tracking/{wave_id}/*.md` → `handoff/{wave_id}.md` (summary).",
            "Reset STATE.json sẽ do harness handle sau khi command complete.",
            "Return RETURN SCHEMA với `teardown_ok: true`.",
        ]),
        RETURN_SCHEMA_TEMPLATE,
    ]
    return "\n\n".join(parts)


def build_apply_cr(state: dict, matrix: list[dict], opts: dict) -> str:
    cr_id = opts.get("cr_id") or "<CR-NNN>"
    parts = [
        f"# SPAWN PROMPT — /apply-cr {cr_id}",
        f"\nAgent: **apply-cr-agent** · Analyze CR impact + transition INTAKE for amendment.",
        state_bundle(state, {"cr_id": cr_id}),
        NON_NEGOTIABLES,
        skills_block([]),
        docs_to_read([
            ("CR file", f"tracking/change-requests/{cr_id}-*.md"),
            ("PROJECT", "docs/architecture/PROJECT.md"),
            ("WAVE-SEQUENCE", "docs/plans/WAVE-SEQUENCE.md"),
            ("MATRIX", "harness/SERVICE-BOUNDARY-MATRIX.json"),
        ]),
        tasks_block([
            f"Read CR file để hiểu scope change.",
            "Identify affected boundaries (cross-reference MATRIX).",
            "Update CR file § 'Kế hoạch cập nhật' với impact analysis.",
            f"Return RETURN SCHEMA với `cr_id: {cr_id}`.",
            "After complete: STATE chuyển INTAKE, gọi /intake-requirement với intake_mode=amendment.",
        ]),
        RETURN_SCHEMA_TEMPLATE,
    ]
    return "\n\n".join(parts)


# ========================================================================
# Dispatch
# ========================================================================

BUILDERS = {
    "intake-requirement": build_intake_requirement,
    "review-document": build_review_document,
    "approve-document": build_approve_document,
    "start-wave": build_start_wave,
    "start-dev": lambda s, m, o: build_boundary_command(s, m, o, "start-dev"),
    "review-dev": lambda s, m, o: build_boundary_command(s, m, o, "review-dev"),
    "dev-handoff": build_dev_handoff,
    "test-plan": build_test_plan,
    "test-execute": build_test_execute,
    "fix-bugs": lambda s, m, o: build_boundary_command(s, m, o, "fix-bugs"),
    "end-wave": build_end_wave,
    "done-wave": build_done_wave,
    "apply-cr": build_apply_cr,
}


def build(command: str, opts: dict) -> str:
    state = state_mod.load_state()
    matrix = load_matrix()
    fn = BUILDERS.get(command)
    if fn is None:
        return f"Unknown command: {command}"
    return fn(state, matrix, opts)


# ========================================================================
# Stats
# ========================================================================

def size_stats(prompt: str) -> dict:
    # Section markers (## headers)
    sections: dict[str, int] = {}
    current = "HEADER"
    sections[current] = 0
    for line in prompt.split("\n"):
        if line.startswith("## "):
            current = line[3:].split(" (")[0].strip()
            sections[current] = 0
        sections[current] += len(line) + 1
    total = sum(sections.values())
    return {"sections": sections, "total_bytes": total, "total_kb": round(total / 1024, 2)}


# ========================================================================
# CLI
# ========================================================================

def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=sorted(BUILDERS.keys()))
    ap.add_argument("--boundary")
    ap.add_argument("--step", type=int)
    ap.add_argument("--wave", type=int)
    ap.add_argument("--bug-id", dest="bug_id")
    ap.add_argument("--cr-id", dest="cr_id")
    ap.add_argument("--input")
    ap.add_argument("--feedback", help="for /review-document revision mode")
    ap.add_argument("--target-file", dest="target_file", help="for /review-document --file")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--save")
    args = ap.parse_args()

    opts = {
        "boundary": args.boundary,
        "step": args.step,
        "wave": args.wave,
        "bug_id": args.bug_id,
        "cr_id": args.cr_id,
        "input": args.input,
        "feedback": args.feedback,
        "target_file": args.target_file,
    }

    prompt = build(args.command, opts)

    if args.stats:
        stats = size_stats(prompt)
        print(f"Prompt size breakdown — /{args.command}:\n")
        for sec, size in stats["sections"].items():
            print(f"  {sec:30s} {size:>8d} B")
        print(f"  {'─' * 40}")
        print(f"  {'TOTAL':30s} {stats['total_bytes']:>8d} B  ({stats['total_kb']} KB)")
        return 0

    if args.save:
        Path(args.save).write_text(prompt, encoding="utf-8")
        sys.stderr.write(f"Saved to {args.save}\n")

    print(prompt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
