"""
Build self-contained spawn prompt for harness commands.

Pattern: pointer-heavy (Tier-C). Inline only STATE bundle, non-negotiables,
owned_paths, skills list, tasks, return schema. Doc files are linked by path —
sub-agent uses Read tool to fetch when needed.

Usage:
  py scripts/build_prompt.py <command> [options]

Options:
  --boundary X        # for start-dev, review-dev, dev-handoff, fix-bugs
  --disc-wave D       # for discovery-start|end (D0|D1|D2|D3)
  --mode M            # for domain-po (EPIC|FEATURE|JOURNEY) | domain-ba (BR|PERSONA)
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
6. Không bypass test (`--no-verify`, skip), không hardcode secrets.
7. **TUÂN THỦ skill được giao**: convention `rules-{kind}` + cấu trúc/layout `ref-{kind}-pattern` (đúng kiến trúc HLD §4) + template tương ứng. KHÔNG tự bịa cấu trúc/đặt tên/đổi build tool ngoài skill+ADR. Review/gate sẽ reject nếu lệch."""


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

# Ref structure/config/logging — universal theo kind, cần MỖI lần scaffold. Invoke BẮT BUỘC ở task_list.
# Situational ref (tuỳ tech của boundary) KHÔNG liệt kê ở kernel: do intake quyết per-boundary và ghi field
# `ref_skills` trong MATRIX (single source). build_prompt chỉ đọc boundary["ref_skills"] → truyền qua.
SCAFFOLD_REF_SKILLS_PER_KIND = {
    "backend": ["ref-backend-pattern", "ref-backend-config", "ref-backend-logging"],
    "bff": [],
    "web": ["ref-frontend-pattern", "ref-frontend-config"],
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


def skills_block(skills: list[str], available: list[str] | None = None, note: str = "", scaffold: list[str] | None = None) -> str:
    """Primary skills = load ngay khi start. Scaffold = BẮT BUỘC khi tạo skeleton. Available = on-demand khi cần."""
    head = "## SKILLS\n"
    if note:
        head += f"\n_{note}_\n"
    parts = []
    if skills:
        parts.append("**Primary (invoke ngay):**\n" + "\n".join(f"- `{s}`" for s in skills))
    else:
        parts.append("**Primary:** (none — command này không cần skill primary)")
    if scaffold:
        parts.append(
            "\n**Scaffold (invoke BẮT BUỘC khi tạo skeleton — cây thư mục + config + logging):**\n"
            + "\n".join(f"- `{s}`" for s in scaffold)
        )
    if available:
        parts.append(
            "\n**Available** (invoke NGAY khi điều kiện/ngữ cảnh đúng — không bỏ qua nếu cần):\n"
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


def boundary_doc_refs(
    boundary_id: str, kind: str, features: list[str] | None,
    depends_on: list[str] | None = None,
) -> list[tuple[str, str]]:
    """Tài liệu BẮT BUỘC đọc cho 1 boundary — GẮN CỨNG deterministic theo boundary_id + kind.

    Single source dùng chung bởi build_prompt (spawn-time) + materialize.py (bake vào agent .md),
    nên cả hai KHÔNG bao giờ lệch. FEAT lấy explicit từ MATRIX `features` — KHÔNG bắt agent tự
    discovery từ wave plan (nguồn miss). MATRIX.features rỗng → fallback wave-plan filter.
    """
    b = boundary_id
    # LUÔN có (technical-design: HLD + API mọi boundary; KG materialize mọi boundary).
    refs: list[tuple[str, str]] = [
        ("PROJECT.md (CHỈ đọc §NFR + §Glossary — ràng buộc phi chức năng + thuật ngữ; BỎ QUA scope/roadmap)", "docs/architecture/PROJECT.md"),
        ("HLD (kiến trúc — §4 chốt Layered/Hexagonal)", f"docs/architecture/hld/hld-{b}.md"),
    ]
    # API contract: backend/bff đọc của CHÍNH MÌNH; FE (web/mobile) đọc của backend/bff nó gọi (MATRIX.depends_on).
    if kind in ("web", "mobile"):
        deps = list(depends_on or [])
        if deps:
            for dep in deps:
                refs.append((f"API contract của backend/bff `{dep}` (FE gọi — bám đúng shape)",
                             f"docs/architecture/api/api-{dep}.md"))
        else:
            refs.append(("API contract của backend FE gọi (MATRIX.depends_on RỖNG — xem integration design)",
                         "docs/architecture/api/api-*.md"))
    else:
        refs.append(("API contract", f"docs/architecture/api/api-{b}.md"))
    # data-model: technical-design "Backend boundary có data-model" → chỉ backend.
    if kind == "backend":
        refs.append(("Data model", f"docs/architecture/data-model/data-model-{b}.md"))
    # UX: technical-design "FE boundary có UX" → chỉ web/mobile.
    if kind in ("web", "mobile"):
        refs.append(("UX / wireframe", f"docs/architecture/ux/ux-{b}.md"))
    refs.append(("Knowledge graph (domain/BR/events/permissions)", f"knowledge-base/{b}.knowledge-graph.yaml"))
    # CÓ ĐIỀU KIỆN — chỉ tồn tại nếu boundary thực sự có (technical-design dòng 55 + integrations).
    # Đọc NẾU file tồn tại; KHÔNG giả định mọi boundary đều có.
    refs.append(("Events phát/nhận (CHỈ nếu boundary phát/nhận event)", f"docs/architecture/events/{b}-events.md"))
    refs.append(("Integrations (CHỈ nếu boundary tham gia tích hợp)", f"docs/architecture/integrations/INTEG-*{b}*.md"))
    feats = list(features or [])
    if feats:
        for fid in feats:
            refs.append((f"FEAT {fid} — AC + BR PHẢI implement", f"docs/architecture/feat/{fid}-*.md"))
    else:
        refs.append((
            "FEAT (MATRIX.features RỖNG — fallback: lọc wave plan §Features in scope theo Boundary)",
            "docs/architecture/feat/FEAT-*.md",
        ))
    return refs


def tasks_block(items: list[str]) -> str:
    head = "## TASKS\n"
    body = "\n".join(f"{i+1}. {t}" for i, t in enumerate(items))
    return head + "\n" + body


# ========================================================================
# Per-command builders
# ========================================================================

# ------------------------------------------------------------------------
# DISCOVERY (D0-D3 ideation — clone tối giản từ ZIP DISCOVERY phase)
# ------------------------------------------------------------------------

DISCOVERY_WAVES = {
    "D0": {
        "agent": "discovery-hypothesis-agent",
        "skill": "discovery-hypothesis",
        "role": "Business Authority",
        "output": "docs/discovery/hypothesis-log.md",
        "template": "docs/discovery/TEMPLATE.hypothesis-log.md",
        "gate": "§1 Vision + §2 Problem non-empty; ≥3 row `| H\\d |`; ≥2 anti-hypothesis §4",
        "reads": [("Project mô tả (nếu user truyền)", "$ARGUMENTS")],
    },
    "D1": {
        "agent": "capability-mapper-agent",
        "skill": "capability-mapping",
        "role": "Business + Architecture",
        "output": "docs/discovery/persona-pool.md + docs/discovery/capability-map.md",
        "template": "docs/discovery/TEMPLATE.persona-pool.md + docs/discovery/TEMPLATE.capability-map.md",
        "gate": "≥1 `## P\\d —`; ≥2 anti-persona; ≥5 capability row §1; ≥1 candidate domain §3",
        "reads": [("Hypothesis-log (D0)", "docs/discovery/hypothesis-log.md")],
    },
    "D2": {
        "agent": "event-stormer-agent",
        "skill": "event-storming",
        "role": "Architecture + Business",
        "output": "docs/discovery/event-storming/ES-{domain}.md (1 file / candidate domain)",
        "template": "docs/discovery/event-storming/TEMPLATE.ES.md",
        "gate": "mỗi candidate domain (capability-map §3) có ES file; §1 Events ≥10",
        "reads": [
            ("Capability-map §3 (candidate domains)", "docs/discovery/capability-map.md"),
            ("Persona-pool (actors)", "docs/discovery/persona-pool.md"),
        ],
    },
    "D3": {
        "agent": "charter-author-agent",
        "skill": "boundary-charter",
        "role": "Architecture Authority",
        "output": "docs/discovery/BOUNDARY-MAP.md + docs/discovery/boundaries/{b}/CHARTER.md "
                   "+ docs/architecture/PROJECT.md (PRD)",
        "template": "docs/discovery/boundaries/TEMPLATE.CHARTER.md + docs/discovery/TEMPLATE.BOUNDARY-MAP.md",
        "gate": "BOUNDARY-MAP ≥1 row; ≥1 CHARTER §1 Mission; PROJECT.md tồn tại; chốt service_prefix",
        "reads": [
            ("Hypothesis-log", "docs/discovery/hypothesis-log.md"),
            ("Capability-map", "docs/discovery/capability-map.md"),
            ("Persona-pool", "docs/discovery/persona-pool.md"),
            ("Event-storming", "docs/discovery/event-storming/ES-*.md"),
        ],
    },
}


def build_discovery_start(state: dict, matrix: list[dict], opts: dict) -> str:
    wave = (opts.get("disc_wave") or "D0").upper()
    spec = DISCOVERY_WAVES.get(wave, DISCOVERY_WAVES["D0"])
    extra_tasks: list[str] = []
    if wave == "D3":
        extra_tasks = [
            "**Sau charter**: derive `docs/architecture/PROJECT.md` (PRD: scope in/out + NFR số + "
            "security/compliance + success metrics + glossary) từ hypothesis + capability + event-storming.",
            "**KHÔNG sinh FEAT/Epic/BR ở D3** — DOMAIN (stage sau) sở hữu product: author BUSINESS vào "
            "`docs/domain/` qua `/domain-po`/`/domain-ba`. D3 chỉ charter + BOUNDARY-MAP + PROJECT.md.",
            "**Chốt `service_prefix`** (kebab ngắn) → trả trong RETURN SCHEMA `service_prefix`.",
        ]
    parts = [
        f"# SPAWN PROMPT — /discovery-start {wave}",
        f"\nAgent: **{spec['agent']}** ({spec['role']}) · Skill: `{spec['skill']}` · Output: {spec['output']}",
        state_bundle(state, {"discovery_wave": wave, "input": opts.get("input")}),
        NON_NEGOTIABLES,
        skills_block([spec["skill"]]),
        docs_to_read(spec["reads"] + [("Template (cấu trúc PHẢI giữ để gate khớp)", spec["template"])]),
        tasks_block([
            f"Invoke skill `{spec['skill']}` để load phương pháp + cấu trúc artifact.",
            f"Đọc template `{spec['template']}` — **giữ NGUYÊN heading/section** (gate `discovery_gate.py {wave}` "
            "match bằng regex; lệch heading → gate false-fail).",
            f"Produce: {spec['output']}.",
            *extra_tasks,
            "Interactive với user (AskUserQuestion ≤5): hỏi info còn thiếu, KHÔNG bịa.",
            f"Exit gate {wave}: {spec['gate']}.",
            "Iterate tới khi user confirm. Idempotent: re-run thì update file đã có, KHÔNG blind-append.",
            f"Return RETURN SCHEMA với `wave: \"{wave}\"`, `user_confirmed: true`"
            + (", `service_prefix: \"<prefix>\"`" if wave == "D3" else "") + ".",
            (f"Sau khi xong + user OK → main chạy `/discovery-start {'D' + str(int(wave[1:]) + 1)}` "
             f"(gate {wave} → vào wave kế)." if wave != "D3"
             else "Sau khi xong + user OK → main chạy `/discovery-end` (gate D3 → DOMAIN_AUTHORING)."),
        ]),
        RETURN_SCHEMA_TEMPLATE + f"\n\nExtra fields:\n- `wave`: `{wave}`\n- `user_confirmed`: `true`"
        + ("\n- `service_prefix`: `<kebab>` (D3 chốt)" if wave == "D3" else ""),
    ]
    return "\n\n".join(parts)


def build_discovery_end(state: dict, matrix: list[dict], opts: dict) -> str:
    """Chốt Discovery (chỉ ở DISC_D3): gate D3 → DOMAIN_AUTHORING."""
    parts = [
        "# SPAWN PROMPT — /discovery-end (chốt Discovery)",
        "\n**Instant action (no sub-agent)** — verify gate D3 + transition → DOMAIN_AUTHORING.",
        state_bundle(state, {"discovery_wave": "D3"}),
        NON_NEGOTIABLES,
        "## TASK — chốt Discovery (D3)\n\n"
        "1. Chạy `py scripts/discovery_gate.py D3` để xem gate pass/fail (charter + BOUNDARY-MAP + PROJECT.md + service_prefix).\n"
        "2. Gate PASS → `py scripts/harness.py discovery-end complete '{\"service_prefix\":\"<kebab>\"}'` "
        "→ transition → DOMAIN_AUTHORING.\n"
        "3. Gate FAIL → KHÔNG complete. Báo user artifact D3 còn thiếu; quay lại `/discovery-start D3` bổ sung.\n"
        "4. **Override (chỉ khi user đồng ý bỏ qua)**: "
        "`'{\"service_prefix\":\"<kebab>\",\"force\":true,\"reason\":\"<lý do>\"}'` → skip gate + ghi audit `tracking/decisions.md`.",
        "## Sau khi vào DOMAIN_AUTHORING\n\nBáo user: chạy `/domain-po <EPIC|FEATURE|JOURNEY>` + `/domain-ba <BR|PERSONA>` "
        "author BUSINESS plain VN vào `docs/domain/` (loop tới khi OK) → `/domain-approve <id|all>` (ký) → `/domain-translate` (dịch sang eng docs/architecture/) → `/domain-end` → DESIGN.",
    ]
    return "\n\n".join(parts)


# ------------------------------------------------------------------------
# DOMAIN 2 lớp (clone ZIP A1): po/ba author BUSINESS plain VN vào docs/domain/ → /domain-approve KÝ
# → /domain-translate DỊCH sang eng docs/architecture/ (gate translation_parity giữ 1-1).
# ------------------------------------------------------------------------

DOMAIN_MODES = {
    "EPIC": {"skill": "domain-po", "agent": "domain-po-agent", "role": "po-author",
             "out": "docs/domain/epics/EP-<PREFIX>-NNN.md",
             "tmpl": "docs/domain/epics/TEMPLATE.epic.md",
             "boot": [("Hypothesis (D0)", "docs/discovery/hypothesis-log.md"),
                      ("Capability-map (D1)", "docs/discovery/capability-map.md"),
                      ("Persona-pool (D1)", "docs/discovery/persona-pool.md"),
                      ("Feature con (business, nếu có)", "docs/domain/feat/FEAT-*.md")]},
    "FEATURE": {"skill": "domain-po", "agent": "domain-po-agent", "role": "po-author",
                "out": "docs/domain/feat/FEAT-<PREFIX>-NNN.md",
                "tmpl": "docs/domain/feat/TEMPLATE.feat.md",
                "boot": [("Epic cha (business)", "docs/domain/epics/EP-*.md"),
                         ("Journey liên quan (flow → AC đúng)", "docs/domain/journeys/JOURNEY-*.md"),
                         ("BR liên quan (business)", "docs/domain/business-rules/BR-*.md"),
                         ("Persona-pool", "docs/discovery/persona-pool.md")]},
    "JOURNEY": {"skill": "domain-po", "agent": "domain-po-agent", "role": "po-author",
                "out": "docs/domain/journeys/JOURNEY-<PREFIX>-NNN.md",
                "tmpl": "docs/domain/journeys/TEMPLATE.journey.md",
                "boot": [("Persona-pool (D1) — actor + goal cho journey", "docs/discovery/persona-pool.md"),
                         ("Persona chi tiết (business)", "docs/domain/personas/PERSONA-*.md"),
                         ("Event-storming D2 (OPTIONAL ref — CHỈ khi cần truy flow/event làm chuỗi step)", "docs/discovery/event-storming/ES-*.md")]},
    "BR": {"skill": "domain-ba", "agent": "domain-ba-agent", "role": "ba-author",
           "out": "docs/domain/business-rules/BR-<PREFIX>-NNN.md",
           "tmpl": "docs/domain/business-rules/TEMPLATE.business-rule.md",
           "boot": [("Feature dùng rule (nguồn chính của BR, business)", "docs/domain/feat/FEAT-*.md"),
                    ("Journey liên quan (trigger nghiệp vụ)", "docs/domain/journeys/JOURNEY-*.md"),
                    ("Event-storming hot-spot D2 (OPTIONAL ref — CHỈ khi cần seed rule từ hot-spot)", "docs/discovery/event-storming/ES-*.md")]},
    "PERSONA": {"skill": "domain-ba", "agent": "domain-ba-agent", "role": "ba-author",
                "out": "docs/domain/personas/PERSONA-<PREFIX>-NNN.md",
                "tmpl": "docs/domain/personas/TEMPLATE.persona.md",
                "boot": [("Persona-pool (D1) — adapt chi tiết", "docs/discovery/persona-pool.md"),
                         ("Journey persona tham gia", "docs/domain/journeys/JOURNEY-*.md")]},
    # WIREFRAME bỏ: wireframe = UX = ux/ (DESIGN phase technical-design lo, không phải DOMAIN artifact riêng).
}
# po viết EPIC/FEATURE/JOURNEY · ba viết BR/PERSONA (tách lệnh /domain-po, /domain-ba).
DOMAIN_PO_MODES = ("EPIC", "FEATURE", "JOURNEY")
DOMAIN_BA_MODES = ("BR", "PERSONA")


def build_domain_author(state: dict, matrix: list[dict], opts: dict) -> str:
    """DOMAIN author BUSINESS doc (plain VN) vào docs/domain/ (A1). po=EPIC/FEATURE/JOURNEY, ba=BR/PERSONA.

    KÝ (approve) + DỊCH (translate) là bước RIÊNG sau — KHÔNG approve/dịch ở đây.
    """
    cmd = opts.get("command") or "domain-po"
    default_mode = "FEATURE" if cmd == "domain-po" else "BR"
    mode = (opts.get("mode") or default_mode).upper()
    spec = DOMAIN_MODES.get(mode, DOMAIN_MODES[default_mode])
    boot = list(spec["boot"]) + [(f"Template {mode} (giữ NGUYÊN cấu trúc + mục 'Câu hỏi cho Author')", spec["tmpl"])]
    mode_task = {
        "EPIC": "Epic gom feature theo capability + outcome cho persona. §Vision + §Success metrics nghiệp vụ "
                "(KHÔNG metric kỹ thuật) + §MVP scope (link FEAT) + §Ngoài phạm vi. "
                "**`feature_refs` PHẢI link ≥2 FEAT** (ZIP planning-rules: <2 → granularity sai, merge). `target_capability` + `priority`.",
        "FEATURE": "**≥4 AC** BDD (Cho/Khi/Thì) + `epic_ref` + `feat_type` (user_facing|platform) "
                   "+ `business_rule_refs` (link BR; thiếu → /domain-ba BR trước) + `has_ui_touchpoint`. "
                   "§Ngoài phạm vi (QC dựa vào). AC mô tả HÀNH VI NGHIỆP VỤ thuần.",
        "BR": "§Phát biểu quy tắc + §Lý do (reference nguồn: luật/policy/contract/decision) + §Khi nào áp dụng "
              "+ **≥2 ví dụ cụ thể** (1 happy + 1 vi phạm — QC seed test). `severity` CORNERSTONE/NORMAL + `related_features`.",
        "JOURNEY": "3-7 step hành trình người dùng, mỗi step (hành động + kỳ vọng + cảm xúc). `persona_refs` + touchpoints "
                   "nhất quán device persona. Nguồn: persona-pool + event-storming.",
        "PERSONA": "Adapt persona-pool (D1) thành narrative chi tiết: role/goals/pains/workflow hàng ngày. "
                   "**Anti-persona BẮT BUỘC** (ai KHÔNG phải target). `persona_pool_ref`.",
    }[mode]
    parts = [
        f"# SPAWN PROMPT — /{cmd} {mode}",
        f"\nAgent: **{spec['agent']}** ({spec['role']}) · Skill: `{spec['skill']}` · Output: `{spec['out']}` (BUSINESS plain VN)",
        state_bundle(state, {"domain_mode": mode}),
        NON_NEGOTIABLES,
        skills_block([spec["skill"]]),
        "## BOOT SEQUENCE (đọc theo thứ tự, targeted — đừng đọc sweeping)\n"
        + "\n".join(f"{i+1}. **{label}**: `{path}`" for i, (label, path) in enumerate(boot)),
        tasks_block([
            f"Invoke skill `{spec['skill']}`; đọc agent spec `agents/{spec['agent']}.md` (owned_paths + boot + forbidden).",
            f"Đọc boot sequence trên (targeted). Author `{spec['out']}` theo template — giữ cấu trúc + frontmatter.",
            mode_task,
            "**Ngôn ngữ NGHIỆP VỤ THUẦN** (no jargon): KHÔNG tên class/SQL/API-path/HTTP-status/schema — "
            "chi tiết kỹ thuật để `/domain-translate` sinh ở eng layer (docs/architecture/). Gate `domain_no_jargon` (lúc ký) chặn jargon.",
            "**Hỏi NGAY sau khi viết (bổ sung):** đọc mục **'Câu hỏi cho Author'** trong template → dùng AskUserQuestion hỏi user "
            "TỪNG câu mở đó NGAY → fold câu trả lời vào doc. KHÔNG để câu hỏi treo.",
            "**Lặp tới khi OK (bổ sung):** vòng draft → trình user → user góp ý → sửa → lặp; CHỈ dừng khi user xác nhận OK. KHÔNG one-shot.",
            "`status: DRAFT` (KHÔNG tự approve — ký là bước riêng `/domain-approve`). Idempotent re-run.",
            f"Author thêm artifact → gọi lại `/domain-po`/`/domain-ba <mode>`. Xong cả bộ → `/domain-approve <id|all>` (ký) → `/domain-translate` (dịch eng). "
            f"Return RETURN SCHEMA `wave: \"authoring\"`, `mode: \"{mode}\"`, `files_changed`.",
        ]),
        RETURN_SCHEMA_TEMPLATE,
    ]
    return "\n\n".join(parts)


def build_domain_end(state: dict, matrix: list[dict], opts: dict) -> str:
    parts = [
        "# SPAWN PROMPT — /domain-end (gate DOMAIN_AUTHORING → DESIGN)",
        "\n**Instant action** — verify gate + transition.",
        state_bundle(state),
        NON_NEGOTIABLES,
        "## TASK — đóng DOMAIN authoring\n\n"
        "1. Gate (kind `domain_gate`): ≥1 `docs/architecture/epics/EP-*.md` + ≥1 `docs/architecture/feat/FEAT-*.md` "
        "+ ≥1 `docs/architecture/business-rules/BR-*.md` (= ĐẦU RA eng do `/domain-translate` đã sinh).\n"
        "2. PASS → `py scripts/harness.py domain-end complete '{}'` → transition DOMAIN_AUTHORING → DESIGN.\n"
        "3. FAIL (chưa có eng output) → KHÔNG complete; kiểm đã `/domain-approve` + `/domain-translate` chưa (eng layer sinh từ đó), hoặc author thêm rồi ký+dịch lại.\n"
        "4. Override (user đồng ý): `py scripts/harness.py domain-end complete '{\"force\":true,\"reason\":\"<lý do>\"}'` → ghi audit tracking/decisions.md.",
        "## Sau DOMAIN (vào DESIGN)\n\nProduct (epic/feat/BR) đã có ở docs/architecture/. Stage → DESIGN. "
        "Chạy `/design` (technical-design: ADR/HLD/API/data-model/UX/events/integrations) → `/plan` "
        "(implementation-plan: WAVE-SEQUENCE+MATRIX+KG) → REVIEW → /approve-document → /start-wave 1.",
    ]
    return "\n\n".join(parts)


def build_domain_approve(state: dict, matrix: list[dict], opts: dict) -> str:
    """KÝ business doc (target rỗng = all). Instant action: jargon-check + stamp `status: APPROVED`."""
    target = opts.get("target") or "all"
    parts = [
        f"# SPAWN PROMPT — /domain-approve {target}",
        "\n**Instant action** — business-owner KÝ business doc (ký TRƯỚC, dịch SAU).",
        state_bundle(state, {"approve_target": target}),
        NON_NEGOTIABLES,
        "## TASK — ký business doc\n\n"
        f"1. `py scripts/domain_approve.py {target}` — jargon-check `docs/domain/` ({'mọi doc' if target=='all' else target}); "
        "sạch → stamp **`status: APPROVED`** vào frontmatter; còn jargon → refuse + báo doc/đoạn (sửa cho plain rồi ký lại). BẮT BUỘC chạy script — KHÔNG stamp tay, KHÔNG bỏ qua.\n"
        f"2. PASS → `py scripts/harness.py domain-approve complete '{{\"target\":\"{target}\"}}'` (gate `domain_no_jargon` + `domain_stamped` — complete mà file chưa stamp sẽ bị CHẶN) → ở lại DOMAIN_AUTHORING.\n"
        "3. Ký lẻ: `/domain-approve EP-<...>` · ký hết: `/domain-approve` (không arg = all).\n"
        "4. Override (user đồng ý): thêm `\"force\":true,\"reason\":\"...\"` → ghi audit.\n"
        "→ Khi MỌI business doc đã ký → `/domain-translate` (gate `domain_signed`).",
    ]
    return "\n\n".join(parts)


def build_domain_translate(state: dict, matrix: list[dict], opts: dict) -> str:
    """DỊCH business (docs/domain/, đã ký) → eng (docs/architecture/) — spawn domain-translator."""
    parts = [
        "# SPAWN PROMPT — /domain-translate",
        "\nAgent: **domain-translator-agent** · Skill: `domain-translator` · business → engineering spec.",
        state_bundle(state),
        NON_NEGOTIABLES,
        skills_block(["domain-translator"]),
        docs_to_read([
            ("Business epics (đã ký)", "docs/domain/epics/EP-*.md"),
            ("Business features (đã ký)", "docs/domain/feat/FEAT-*.md"),
            ("Business rules (đã ký)", "docs/domain/business-rules/BR-*.md"),
            ("Business journeys/personas (đã ký)", "docs/domain/{journeys/JOURNEY-*,personas/PERSONA-*}.md"),
            ("Eng templates (giữ cấu trúc)", "docs/architecture/{epics,feat,business-rules,journeys,personas}/TEMPLATE.*.md"),
        ]),
        tasks_block([
            "Invoke skill `domain-translator`. CHỈ dịch khi gate `domain_signed` pass (mọi business doc `status: APPROVED`).",
            "Foreach business doc ở `docs/domain/` → DỊCH sang eng artifact tương ứng `docs/architecture/{epics,feat,business-rules,journeys,personas}/` "
            "theo eng template: GIỮ NGUYÊN Ý nghiệp vụ, THÊM độ chính xác kỹ thuật (BDD AC chuẩn, field/enum/error code, ref-id). KHÔNG bịa scope mới.",
            "Truy vết: eng doc frontmatter `source: docs/domain/<file>` + `domain_source_id: <id>` — BẮT BUỘC (gate `translation_parity` @/domain-end đối chiếu 1-1: business đã ký thiếu eng doc = bỏ sót; eng doc không source = mồ côi). Giữ id (FEAT-x business → FEAT-x eng). DỊCH ĐỦ 100% doc đã ký, không bỏ sót cái nào.",
            "Interactive nếu business doc mơ hồ (≤5 câu); KHÔNG tự quyết scope nghiệp vụ — hỏi user.",
            "Xong → `py scripts/harness.py domain-translate complete '{}'`. Return RETURN SCHEMA `files_changed` (eng docs sinh ra).",
            "Sau dịch: `/domain-end` (gate `domain_gate`: eng epic+feat+BR tồn tại) → DESIGN.",
        ]),
        RETURN_SCHEMA_TEMPLATE,
    ]
    return "\n\n".join(parts)


def build_design(state: dict, matrix: list[dict], opts: dict) -> str:
    """Technical design (stage DESIGN) — solution-architect: hệ thống/contract (UX = /design-ux riêng)."""
    parts = [
        "# SPAWN PROMPT — /design",
        "\nAgent: **solution-architect-agent** · Skill: `technical-design` · Stage DESIGN → PLAN. **KHÔNG design UX/UI** — đó là `/design-ux` (ux-designer-agent).",
        state_bundle(state),
        NON_NEGOTIABLES,
        skills_block(["technical-design"]),
        docs_to_read([
            ("PROJECT (PRD: scope/NFR/stack/glossary — D3)", "docs/architecture/PROJECT.md"),
            ("Boundary map (topology + quan hệ — D3)", "docs/discovery/BOUNDARY-MAP.md"),
            ("Charter từng boundary (mission/owned-data/capabilities/deps — D3)", "docs/discovery/boundaries/*/CHARTER.md"),
            ("Epic (capability grouping — DOMAIN)", "docs/architecture/epics/EP-*.md"),
            ("FEAT (AC + business_rule_refs — eng, dịch từ business qua /domain-translate)", "docs/architecture/feat/FEAT-*.md"),
            ("Business rules (domain invariant → API error catalog + data-model — DOMAIN)", "docs/architecture/business-rules/BR-*.md"),
            ("Journey + Persona (UX context cho FE boundary — DOMAIN)", "docs/architecture/journeys/JOURNEY-*.md + docs/architecture/personas/PERSONA-*.md"),
            ("Event-storming D2 raw (OPTIONAL ref — đã fold vào FEAT/BR/domain; CHỈ đọc khi cần truy nguồn domain event/hot-spot, KHÔNG bắt buộc)", "docs/discovery/event-storming/ES-*.md"),
            ("Templates artifact (PHẢI đọc + giữ cấu trúc)", "docs/architecture/{adr,hld,api,data-model,ux,events,integrations}/TEMPLATE.*.md"),
        ]),
        tasks_block([
            "Invoke skill `technical-design`.",
            "Đọc boot sequence trên (targeted) + template từng artifact TRƯỚC khi author.",
            "Produce per boundary: ADR (≥3), HLD, API, data-model (backend), events (nếu phát/nhận); + integrations (≥1) + infra/docker-compose skeleton. **UX (ux-{boundary}.md + design-tokens.css) KHÔNG làm ở đây** — user chạy `/design-ux` (ux-designer-agent) sau khi api-{be}.md sẵn; FE boundary ở /design chỉ cần HLD.",
            "Boundary decomposition + kind/stack lấy từ Charter + BOUNDARY-MAP (D3); FEAT/BR (DOMAIN) → API error catalog + data-model invariant.",
            "**TRẢ NỢ TODO-engineer (gate `todo_resolved` @/design-end):** mọi marker `TODO engineer`/`TBD (DESIGN)` translator để lại trong eng feat/BR (nhất là BR `enforcement_location`, FEAT `consumes_contracts`) phải được ĐIỀN ở stage này; chưa chốt thật → ghi Open question có chủ, KHÔNG để TBD.",
            "**Contract graph khớp MATRIX (gate `contract_graph_parity` @/plan):** api-*.md frontmatter `producer`/`consumers[]`, INTEG-INT `consumer`/`producer`, events subscriber phải dùng đúng boundary_id — 3 nguồn này sẽ bị đối chiếu với MATRIX depends_on, khai lệch = chặn ở /plan.",
            "Iterate với user tới khi confirm. **Chưa vừa ý → user chạy lại `/design`** = re-spawn refine (self-loop DESIGN→DESIGN, KHÔNG advance). Idempotent: update artifact đã có, KHÔNG blind-append.",
            "Khi user OK TOÀN BỘ: return RETURN SCHEMA `user_confirmed: true` → nhắc user chạy `/design-ux` (nếu có FE boundary + chưa làm UX) rồi **`/design-end`** (gate per-boundary completeness) → DESIGN→PLAN. KHÔNG tự advance bằng `/design`.",
        ]),
        RETURN_SCHEMA_TEMPLATE,
    ]
    return "\n\n".join(parts)


def build_design_ux(state: dict, matrix: list[dict], opts: dict) -> str:
    """UX/UI design (stage DESIGN, self-loop) — ux-designer-agent chuyên môn, tách khỏi solution-architect."""
    parts = [
        "# SPAWN PROMPT — /design-ux",
        "\nAgent: **ux-designer-agent** · Skill: `ux-design` · Stage DESIGN (self-loop) — UX/UI cho FE boundary. "
        "KHÔNG đụng ADR/HLD/API/data-model/events/INTEG (đó là `/design`).",
        state_bundle(state),
        NON_NEGOTIABLES,
        skills_block(["ux-design"]),
        docs_to_read([
            ("PROJECT (persona/platform/design system/ADR ui-kit)", "docs/architecture/PROJECT.md"),
            ("Boundary map (FE boundary nào: kind web/mobile)", "docs/discovery/BOUNDARY-MAP.md"),
            ("FEAT (user story + AC — nguồn user flow)", "docs/architecture/feat/FEAT-*.md"),
            ("Journey + Persona (UX context)", "docs/architecture/journeys/JOURNEY-*.md + docs/architecture/personas/PERSONA-*.md"),
            ("API contract BE phục vụ (UX consume, KHÔNG bịa endpoint)", "docs/architecture/api/api-*.md"),
            ("Templates (PHẢI giữ cấu trúc)", "docs/architecture/ux/TEMPLATE.ux.md + docs/architecture/ux/TEMPLATE.design-tokens.css"),
            ("UX hiện có (refine idempotent)", "docs/architecture/ux/ux-*.md (nếu đã có)"),
        ]),
        tasks_block([
            "Invoke skill `ux-design`.",
            "**design-tokens.css TRƯỚC** (SoT `--color-*`/`--font-*`/`--space-*` + dark/hc theme, theo TEMPLATE — 1 file dùng chung MỌI web boundary; gate `design_gate` đòi khi có web boundary).",
            "Foreach FE boundary (kind web/mobile): `ux-{boundary}.md` theo TEMPLATE.ux — user flow per FEAT Must · wireframe per screen · component states đầy đủ (default/hover/disabled/loading/error/empty) · API calls khớp `api-{be}.md` · validation FE · permission UI · responsive · a11y WCAG 2.1 AA · **§Visual polish** (app shell/spacing rhythm/type scale/primitives/interaction states/elevation — cụ thể đối chiếu được).",
            "Thiếu endpoint/contract để vẽ flow → ghi Open question cho architect (user chạy `/design` bổ sung), KHÔNG tự bịa.",
            "Iterate với user tới khi confirm. **Chưa vừa ý → user chạy lại `/design-ux`** (self-loop, KHÔNG advance). Idempotent: update file đã có.",
            "Khi user OK: return RETURN SCHEMA `user_confirmed: true` → cả /design lẫn /design-ux xong → user chạy `/design-end`.",
        ]),
        RETURN_SCHEMA_TEMPLATE,
    ]
    return "\n\n".join(parts)


def build_design_end(state: dict, matrix: list[dict], opts: dict) -> str:
    """Advance DESIGN→PLAN: verify design_gate (per-boundary completeness) rồi transition. KHÔNG spawn author mới."""
    parts = [
        "# SPAWN PROMPT — /design-end",
        "\nĐóng stage DESIGN → PLAN sau khi user đã vừa ý technical design. Verify gate rồi transition — KHÔNG spawn agent author mới.",
        state_bundle(state),
        tasks_block([
            "Xác nhận user đã OK toàn bộ design (ADR/HLD/API/data-model/UX/events/integrations). Chưa OK → quay lại `/design` (refine), ĐỪNG chạy design-end.",
            "Gate design_gate: ADR≥3 + INTEG≥1 + **MỖI boundary trong BOUNDARY-MAP đủ artifact đúng kind** (backend→hld+api; web/mobile→hld+ux) + design-tokens.css khi có web boundary. Kèm gate `todo_resolved`: marker TODO-engineer/TBD(DESIGN) trong eng feat/BR phải đã điền hết. Thiếu → gate đỏ, quay lại `/design` bổ sung.",
            "Gate pass → main chạy `py scripts/harness.py design-end complete '{}'` → DESIGN→PLAN, rồi `/plan`.",
            "Gate FAIL → KHÔNG complete. Báo boundary/artifact còn thiếu.",
        ]),
    ]
    return "\n\n".join(parts)


def build_plan(state: dict, matrix: list[dict], opts: dict) -> str:
    """Implementation plan (stage PLAN) — tái dùng skill implementation-plan + program-planner-agent."""
    parts = [
        "# SPAWN PROMPT — /plan",
        "\nAgent: **program-planner-agent** · Skill: `implementation-plan` · Stage PLAN → REVIEW.",
        state_bundle(state),
        NON_NEGOTIABLES,
        skills_block(["implementation-plan"]),
        docs_to_read([
            ("PROJECT (CHỈ §scope + §duration/timeline → chia wave; bỏ qua phần khác)", "docs/architecture/PROJECT.md"),
            ("Boundary map (TOPOLOGY: phủ 100% boundary + quan hệ — D3)", "docs/discovery/BOUNDARY-MAP.md"),
            ("Charter boundaries (CHỈ §capability + §depends_on → thứ tự wave; KHÔNG cần chi tiết khác)", "docs/discovery/boundaries/*/CHARTER.md"),
            ("Epic (theme → wave grouping — DOMAIN)", "docs/architecture/epics/EP-*.md"),
            ("FEAT (CHỈ frontmatter epic_ref/persona + §AC count → map FEAT→boundary→wave; KHÔNG cần đọc kỹ từng AC)", "docs/architecture/feat/FEAT-*.md"),
            ("Business rules (cross-FEAT invariant per wave)", "docs/architecture/business-rules/BR-*.md"),
            ("Integrations (cross-boundary deps → thứ tự + dependency giữa wave)", "docs/architecture/integrations/INTEG-*.md"),
            ("Design HLD/API/data-model/UX/events (CHỈ kiểm SỰ TỒN TẠI = contract đã có cho boundary; KHÔNG đọc full nội dung — đọc on-demand khi cần suy `ref_skills`)", "docs/architecture/{hld,api,data-model,ux,events}/*.md"),
            ("Template WAVE-SEQUENCE + wave (giữ field wave_class/strategy/targets)", "docs/plans/TEMPLATE.WAVE-SEQUENCE.md + docs/plans/TEMPLATE.wave.md"),
        ]),
        tasks_block([
            "Invoke skill `implementation-plan`; đọc boot sequence trên + 2 template plan TRƯỚC khi author.",
            "Planner = TOPOLOGY + sequencing: dùng BOUNDARY-MAP + CHARTER.depends_on + INTEG để xếp thứ tự wave; map FEAT→boundary→wave qua epic_ref. KHÔNG cần full nội dung HLD/API/data-model/ux/events — chỉ cần biết contract đã TỒN TẠI (design đã chốt) cho boundary; đọc full on-demand khi thật sự cần.",
            "Produce: docs/plans/WAVE-SEQUENCE.md + wave-{N}.md cho MỌI wave + materialize MATRIX (`py scripts/materialize_matrix.py`) + KG skeleton per boundary.",
            "MATRIX materialize chạy ở stage PLAN (ALLOW_STAGES có PLAN).",
            "Iterate với user tới khi confirm.",
            "**Phủ 100% FEAT (gate `plan_integrity`):** mọi FEAT-*.md phải vào `features[]` của đúng 1 boundary trong MATRIX — FEAT bỏ sót = mồ côi = gate chặn (chủ động hoãn/bỏ → frontmatter `status: deferred|dropped`).",
            "**Contract graph (gate `contract_graph_parity`):** MATRIX `depends_on`/`consumed_by` phải khớp 2 chiều với api-*.md `consumers[]` + INTEG-INT + events subscribers — cạnh gọi nhau không có contract doc / contract khai cạnh không có trong MATRIX = chặn.",
            "Sau confirm: return RETURN SCHEMA `user_confirmed: true`. Gate /plan: WAVE-SEQUENCE + MATRIX + wave files + KG + lint (integrity/coherence/contract-graph) → transition PLAN→REVIEW. Rồi /approve-document → /start-wave 1.",
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
            "Sanity-check toàn bộ doc đã author (discovery + domain + design + plan) — READ-ONLY, KHÔNG sửa doc.",
            "**Độ phủ năng lực (quan trọng nhất):** đối chiếu `capability-map.md` (D1) + nhu cầu mỗi persona "
            "(`persona-pool.md`) + mỗi journey → MỌI năng lực phải có ≥1 FEAT phủ. Năng lực NỀN mà loại sản "
            "phẩm này đương nhiên cần (xác thực/đăng nhập/cấp token, phân quyền, multi-tenant nếu SaaS, xử lý "
            "lỗi/empty-state) mà KHÔNG có FEAT/AC → gap BLOCKER (đây chính là lỗi 'thiếu luồng login' lọt tới handoff).",
            "**Mâu thuẫn cross-doc:** FEAT vs BR, AC vs api/data-model, HLD vs PROJECT scope, MATRIX vs BOUNDARY-MAP "
            "— phát biểu trái nhau ở 2 doc → gap.",
            "**AC testable:** mỗi FEAT.AC `Must` đo được (Cho/Khi/Thì), gồm non-happy-path; không testable → gap.",
            "**Cross-ref integrity:** epic↔feat↔BR↔journey↔persona id tham chiếu phải tồn tại (không dangling).",
            "**Câu hỏi cho Author chưa chốt:** còn `## Câu hỏi cho Author` / TODO chưa trả lời trong doc → gap.",
            "Ghi MỌI gap vào `tracking/doc-review-findings.md` (template `tracking/_templates/TEMPLATE.doc-review-findings.md`): "
            "mỗi gap 1 row `DR-NNN | severity | concern | file | status` (severity BLOCKER/MAJOR/MINOR; status=open). "
            "**Luôn ghi file kể cả KHÔNG có gap** (bảng rỗng) — gate /approve-document đọc file này; thiếu file = review chưa chạy = chặn approve.",
            "Return issues[] (file + concern + severity). KHÔNG sửa doc nguồn — user feed `/review-document \"<feedback>\"` "
            "(revision mode) hoặc lùi `/domain-po`·`/domain-ba` author bổ sung (→ /domain-approve → /domain-translate) để vá gap BLOCKER/MAJOR.",
        ]
        section_label = (
            "## SANITY-CHECK TASK (gap / mâu thuẫn / thiếu độ phủ)\n\n"
            "No feedback → mode sanity-check: quét gap toàn bộ doc, ghi `tracking/doc-review-findings.md`, "
            "KHÔNG sửa doc nguồn.\n\n"
            "> Gate `/approve-document` chặn nếu file còn gap **BLOCKER/MAJOR** status=open → ép vá trước khi start-wave "
            "(mirror review-dev cho code, nhưng cho TÀI LIỆU). Mục tiêu chính: bắt **thiếu năng lực nền (vd auth/login)** "
            "trước khi vào build."
        )

    parts = [
        f"# SPAWN PROMPT — /review-document ({mode})",
        f"\nAgent: **review-document-agent** · Mode: `{mode}`",
        state_bundle(state, {"mode": mode, "has_feedback": has_feedback}),
        NON_NEGOTIABLES,
        section_label,
        skills_block(["business-analysis"], note="Skill check business rules + AC testability (lens AC/BR). GAP/độ-phủ năng lực: theo SANITY-CHECK TASK dưới."),
        docs_to_read([
            ("PROJECT", "docs/architecture/PROJECT.md"),
            ("Capability map (độ phủ)", "docs/discovery/capability-map.md"),
            ("Persona pool (nhu cầu)", "docs/discovery/persona-pool.md"),
            ("Epics", "docs/architecture/epics/EP-*.md"),
            ("FEAT all", "docs/architecture/feat/FEAT-*.md"),
            ("Business rules", "docs/architecture/business-rules/BR-*.md"),
            ("Journeys", "docs/architecture/journeys/JOURNEY-*.md"),
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
            ("Findings (ghi vào)", "tracking/doc-review-findings.md"),
            ("Findings template", "tracking/_templates/TEMPLATE.doc-review-findings.md"),
        ]),
        tasks_block(tasks),
        RETURN_SCHEMA_TEMPLATE + "\n\nExtra fields:\n- `mode`: `revision` | `sanity-check`\n- `issues`: `[{file, concern, severity}]` (sanity-check — mirror các row DR-NNN đã ghi)\n- `findings_file`: `tracking/doc-review-findings.md` (sanity-check — LUÔN ghi, kể cả 0 gap)\n- `revisions`: `[{file, summary}]` (revision)\n- `feedback_processed`: `true` (set khi mode=revision đã apply)",
    ]
    return "\n\n".join(parts)


def build_approve_document(state: dict, matrix: list[dict], opts: dict) -> str:
    parts = [
        "# SPAWN PROMPT — /approve-document",
        "\n**Instant action** — KHÔNG spawn sub-agent. Pure CLI complete.",
        state_bundle(state),
        NON_NEGOTIABLES,
        "## TASK\n\n1. Ask user explicit confirm.\n2. User reply 'yes' → run `py scripts/harness.py approve-document complete '{\"approved\":true}'`.\n3. User reply 'no' → cancel, suggest /review-document.\n4. Sau approve: report 'Approved. Run /start-wave 1 để mở wave đầu tiên.'\n\n"
        "> **Gate `doc_review`:** lệnh này bị CHẶN nếu `/review-document` (no-arg, sanity-check) chưa chạy "
        "(thiếu `tracking/doc-review-findings.md`) hoặc còn gap **BLOCKER/MAJOR** open. Vá gap (revision loop "
        "hoặc lùi `/domain-po`·`/domain-ba` → ký → translate) tới sạch. Edge thật → `'{\"approved\":true,\"force\":true,\"reason\":\"<lý do>\"}'` "
        "(bypass + audit `tracking/decisions.md`).",
    ]
    return "\n\n".join(parts)


def build_start_wave(state: dict, matrix: list[dict], opts: dict) -> str:
    wave_n = int(opts.get("wave") or 1)
    parts = [
        f"# SPAWN PROMPT — /start-wave {wave_n}",
        f"\nAgent: **start-wave-agent** · Materialize per-boundary agents + KG skeleton, rồi seed phần design vào KG từ docs đã chốt — wave-{wave_n:03d}.",
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
            f"Run `py scripts/materialize.py --wave {wave_n}` (gen agents/dev-{{prefix}}-{{boundary}}-agent.md + knowledge-base/{{boundary}}.knowledge-graph.yaml skeleton per boundary).",
            "Verify file đã tồn tại sau materialize.",
            "Seed phần DESIGN vào KG cho MỖI boundary (docs đã chốt sau approve): đọc data-model→`entities`, FEAT→`business_rules`, events doc→`events_*`, HLD §7→`permissions`, INTEG→`dependencies`/`integrations`. **Edit ĐÚNG file vừa materialize `knowledge-base/{{boundary}}.knowledge-graph.yaml` (tên KHÔNG prefix — khớp materialize.py) — TUYỆT ĐỐI KHÔNG tạo file KG mới / đổi tên.** GIỮ RỖNG `learnings`/`decisions`/`discipline`/`failure_modes`/`execution_history`. Chỉ seed cái docs CÓ, KHÔNG bịa.",
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
    scaffold_block: list[str] = []  # scaffold refs hiển thị riêng ở SKILLS block (start-dev)

    if command == "start-dev":
        agent_name = f"dev-{prefix}-{boundary_id}-agent"
        skills = PRIMARY_SKILLS_PER_KIND.get(kind, [])
        scaffold_refs = SCAFFOLD_REF_SKILLS_PER_KIND.get(kind, [])
        scaffold_block = scaffold_refs
        # Situational ref = do intake quyết per-boundary, lưu MATRIX field `ref_skills`. Kernel chỉ đọc + truyền qua.
        ref_skills = list(boundary.get("ref_skills") or [])
        scaffold_invoke = " + ".join(f"`{s}`" for s in scaffold_refs) if scaffold_refs else "(kind này không có ref structure riêng)"
        # Skill mô tả cây thư mục chuẩn: ref-{kind}-pattern nếu có, else rules-{kind}.
        pattern_ref = next((s for s in scaffold_refs if s.endswith("-pattern")), PRIMARY_SKILLS_PER_KIND.get(kind, ['rules-?'])[0])
        task_list = [
            f"Invoke primary skill `{PRIMARY_SKILLS_PER_KIND.get(kind, ['rules-?'])[0]}` để load convention.",
            "Read HLD + API + data-model + KG của boundary; lấy **kiến trúc (Layered/Hexagonal) đã CHỐT ở HLD §4** (HLD §4 chỉ CHỌN kiến trúc — KHÔNG phải nguồn cây thư mục).",
            f"**Scaffold (BẮT BUỘC invoke {scaffold_invoke} trước khi tạo file)** — nếu `{service_folder}/` chưa có code: tạo build file (**theo ADR tech-stack** — backend: Gradle `build.gradle` default / Maven `pom.xml`; bff/web: `package.json`; mobile: `pubspec.yaml`) + **folder/file layout BÁM ĐÚNG cây thư mục trong `{pattern_ref}`** — **chọn đúng layout Layered HAY Hexagonal/DDD theo kiến trúc chốt ở HLD §4, KHÔNG mặc định Layered**. KHÔNG tự bịa cấu trúc; KHÔNG dùng bảng layer HLD làm cây thư mục; KHÔNG tự đổi build tool khác ADR.",
        ]
        if ref_skills:
            task_list.append(
                "Boundary này được intake gắn ref skill (MATRIX `ref_skills`): "
                + ", ".join(f"`{s}`" for s in ref_skills)
                + " — **invoke khi code phần tương ứng** (vd cache/event)."
            )
        _feats = list(boundary.get("features") or [])
        if _feats:
            _feat_task = (
                "Đọc AC + BR trong các FEAT đã GẮN CỨNG cho boundary này (MATRIX `features`): "
                + ", ".join(f"`{f}`" for f in _feats)
                + " (path ở §DOCS TO READ) → implement MỌI AC, enforce MỌI BR. KHÔNG tự suy FEAT từ wave plan."
            )
        else:
            _feat_task = (
                f"(MATRIX `features` RỖNG — intake chưa gắn) Fallback: đọc `docs/plans/{wave_id}.md` "
                f"§'Features in scope' → lọc dòng `Boundary == {boundary_id}` = tập FEAT; đọc AC từng `FEAT-*.md` rồi implement."
            )
        task_list += [
            _feat_task,
            "Run scoped build/test (mvn -pl ./ test cho backend; npm test cho bff/web; flutter test cho mobile) — **phải XANH mới được return**: compile error / test fail → sửa tới khi pass. KHÔNG return khi build/lint/test=fail (SubagentStop + Stop hook sẽ block).",
            "KG: phần design (entities/business_rules/events/permissions) đã seed ở /start-wave — chỉ UPDATE nếu implement khác design (kèm sửa data-model); APPEND phần kinh nghiệm (learnings/gotchas/failure_modes/decisions) khi phát sinh.",
            "Return RETURN SCHEMA.",
        ]
    elif command == "review-dev":
        agent_name = f"review-{kind}-agent (singleton)"
        skills = REVIEW_SKILLS_PER_KIND.get(kind, [])
        ref_skills = PRIMARY_SKILLS_PER_KIND.get(kind, [])  # review: chỉ rules-{kind} (WHAT), KHÔNG nạp ref how-to
        task_list = [
            f"Invoke skill `{(REVIEW_SKILLS_PER_KIND.get(kind) or ['review-?'])[0]}`.",
            f"Read `FEAT-*` boundary đảm nhận → review code trong `{service_folder}/` theo checklist skill (gồm **AC/BR compliance**: mọi AC implement + BR enforce).",
            f"**GHI findings ra `tracking/{wave_id}/review-findings.md`** (theo `tracking/_templates/TEMPLATE.review-findings.md`): mỗi issue = 1 row `RF-NNN` với `severity/status=open/boundary={boundary_id}/file(path:line)/type/description/suggested_fix`. Row đã fix ở vòng trước (status=resolved) → re-review xác nhận, KHÔNG xoá.",
            "**KHÔNG spawn fix, KHÔNG tự loop** — đó là việc của MAIN orchestrator. Review chỉ đánh giá + ghi findings + trả số liệu.",
            "Append learnings.gotchas vào KG nếu phát hiện pattern xấu (KHÔNG đụng phần design).",
            "Return RETURN SCHEMA với `review_result: pass|fail`, **`open_findings: <số row BLOCKER/MAJOR status=open>`**, `coverage_pct`.",
        ]
    elif command == "fix-bugs":
        bug_id = opts.get("bug_id") or "<BUG-NNN>"
        agent_name = f"fix-{prefix}-{boundary_id}-agent (Mode A — bug-id)"
        skills = PRIMARY_SKILLS_PER_KIND.get(kind, []) + ["bug-logging"]
        # Refs cho fix = scaffold (structure/config/logging) + ref_skills boundary (MATRIX). KHÔNG review (fix không gọi review-agent).
        ref_skills = (
            SCAFFOLD_REF_SKILLS_PER_KIND.get(kind, [])
            + list(boundary.get("ref_skills") or [])
        )
        task_list = [
            f"Read `tracking/wave-{{N}}/bugs.md` (bảng) → tìm **row `{bug_id}`**.",
            "Đọc cột reproduce + expected + actual + error log + TC + AC.",
            "**Reproduce đúng TC fail** (xác nhận thấy bug) TRƯỚC khi sửa.",
            f"Fix code trong `{service_folder}/` theo rules-{kind} — tối thiểu, đúng root cause.",
            "Verify: **build XANH (no compile error)** + **re-run CHÍNH TC fail** → pass + scoped test pass (regression). **KHÔNG gọi review-agent** (sub-agent không spawn được sub-agent; review-agent là của REVIEW_DEV).",
            f"Test pass → set ô `status` của row `{bug_id}` = `closed` + thêm regression `TC-R*` trong bảng bugs.md.",
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
        skills_block(skills, available=ref_skills, scaffold=scaffold_block, note="Primary = invoke ngay. Scaffold = BẮT BUỘC khi tạo skeleton (cây thư mục theo ref-pattern). Ref situational = invoke NGAY khi boundary có điều kiện tương ứng (cache/event/log)."),
        docs_to_read(
            boundary_doc_refs(boundary_id, kind, boundary.get("features"), boundary.get("depends_on"))
            + [("Wave plan (scope wave hiện tại)", f"docs/plans/{wave_id}.md")]
        ),
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
            ("Handoff template (BẮT BUỘC điền §1-§4)", "handoff/TEMPLATE.wave.md"),
        ]),
        tasks_block([
            "Invoke skill `infra-local-dev`.",
            "**dev-handoff = INFRA-ONLY:** CHỈ sửa `docs/architecture/infra/docker-compose.yml`. **TUYỆT ĐỐI KHÔNG sửa `services/{boundary}/**`** (Dockerfile/src/config/migration) — hook chặn. Dockerfile do dev scaffold (gate code_compliance); thiếu/sai → STOP + fix-agent.",
            "Update docs/architecture/infra/docker-compose.yml thêm service mới (nếu chưa có) + env khớp app đọc.",
            f"`docker-compose up -d --build` → services healthy + **verify cross-boundary connectivity** (caller→callee qua service name theo INTEG-INT/depends_on). **Tận dụng lại service wave trước:** `up -d` idempotent — service đã có (wave trước `end-wave` chỉ `stop`, GIỮ image+volume) → khởi động lại NHANH từ image+volume cũ; chỉ boundary MỚI/đổi mới build+tạo. KHÔNG `down` trước (giữ data wave trước).",
            f"**MAIN/orchestrator chạy `py scripts/capture_infra_proof.py`** (HARNESS đo) → `tracking/{wave_id}/docker-ps.json` (infra_proof) + `health-proof.json` (health_proof: curl /health/ready 2xx) + `api-proof.json` (fetch OpenAPI `/v3/api-docs` mỗi backend — gate api_contract_proof so endpoint runtime vs `api-{{boundary}}.md`; fetch fail = backend thiếu springdoc → fix-agent bổ sung theo ref-backend-config). Service chưa UP → exit !=0.",
            "**Service chưa healthy → `docker compose logs <svc>` chẩn ROOT-CAUSE:** (a) lỗi compose/env → sửa docker-compose.yml + up lại; (b) **lỗi code/migration/config/Dockerfile trong `services/{boundary}/`** (tên/kiểu cột migration sai, thiếu HealthController, healthcheck curl trên image không có curl…) → **STOP, báo MAIN spawn `fix-{boundary}-agent` (Mode B)** kèm root-cause → fix → re-run /dev-handoff. KHÔNG tự sửa code.",
            f"Verify build local boundary `{boundary_id}` pass (đọc kết quả, KHÔNG sửa source).",
            f"**Ghi `handoff/{wave_id}.md` §1-§4** (Summary · Service inventory: service/port/health · Start local · Endpoints) theo `handoff/TEMPLATE.wave.md`. (§5 end-wave, §6 done-wave.)",
            "Return RETURN SCHEMA với `coverage_pct`, `review_result: pass`, `docker_compose_ok: true`, `connectivity_ok: true`.",
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
            ("Template registry (BẮT BUỘC — copy cấu trúc cột; KHÔNG tự chế format)", "tracking/_templates/TEMPLATE.test-case-registry.md"),
            ("FEAT all", "docs/architecture/feat/FEAT-*.md"),
            ("API contracts", "docs/architecture/api/api-*.md"),
            ("UX", "docs/architecture/ux/ux-*.md"),
            ("Wave plan", f"docs/plans/{wave_id}.md"),
            ("Existing tests", f"tracking/{wave_id}/test-case-registry.md (nếu đã có)"),
        ]),
        tasks_block([
            "Invoke skill `test-plan`. **Đọc template `tracking/_templates/TEMPLATE.test-case-registry.md`** (đúng đường dẫn này) → copy cấu trúc cột, KHÔNG tự tạo format mới.",
            "Foreach FEAT in wave: foreach AC: tạo TC-* entry.",
            f"**Deferred-scope:** đọc mục `## Deferred to later waves` trong `docs/plans/{wave_id}.md` + review-findings wontfix → TC cho AC/feature deferred đánh tag `@deferred` + `note: deferred wave-N`. Các TC này test-execute sẽ skip(deferred), KHÔNG tính bug/fail (đạt test_result=pass tự nhiên). Defer phải khai báo ở wave plan mới có hiệu lực (tag đơn lẻ vô tác dụng).",
            "**Scope (gate `registry_scope`):** auto-TC CHỈ trace FEAT thuộc wave plan ≤ wave hiện tại (registry tích luỹ — FEAT wave trước hợp lệ để regression). FEAT chỉ ở wave TƯƠNG LAI → KHÔNG sinh TC (over-scope = test feature chưa build = bug rác). FEAT/AC deferred mà row thiếu tag @deferred → gate chặn.",
            "**UI coverage (gate `ui_test_present`):** mỗi WEB boundary trong wave phải có ≥1 auto-TC UI in-scope (type=auto, group=e2e, boundary=<web>) — Playwright load màn hình chính + assert style token áp dụng (computed style ≠ browser default) + screenshot. KHÔNG được để UI toàn manual/deferred.",
            "**AC coverage (gate `ac_coverage`):** MỌI `### AC-n` của FEAT in-scope wave phải có ≥1 TC trace `FEAT-N:AC-M` (cột feature+AC; auto hoặc manual; token deferred bỏ qua) — AC thiếu TC = mồ côi, gate chặn. Ngược lại KHÔNG trace AC không tồn tại (stale).",
            f"Write to `tracking/{wave_id}/test-case-registry.md` (per skill format).",
            "Cover P0 (blocker), P1 (must-have), P2 (nice-to-have).",
            "Return RETURN SCHEMA với `test_cases_count: N`, `docker_compose_ok: true`, `connectivity_ok: true` (infra status kế thừa từ /dev-handoff — verify stack còn UP; gate test-plan: 2 flag + infra_proof + health_proof + contract_test_present + ui_test_present + registry_scope).",
        ]),
        RETURN_SCHEMA_TEMPLATE,
    ]
    return "\n\n".join(parts)


def build_test_execute(state: dict, matrix: list[dict], opts: dict) -> str:
    wave_id = (state.get("wave") or {}).get("id") or "<unknown-wave>"
    parts = [
        "# SPAWN PROMPT — /test-execute",
        "\nAgent: **test-execute-agent** · Chạy auto TC **BLACK-BOX trên hệ thống ĐANG CHẠY** (API/UI/e2e) + log bug (origin=auto). **KHÔNG build source · KHÔNG mvn/npm/gradle/vitest · KHÔNG đo coverage** (đó là việc DEV ở /start-dev). KHÔNG fix (fix qua /fix-bugs).",
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
            "Infra + service đã UP từ `/dev-handoff` (giữ UP) — **KHÔNG tự dựng**; sanity reachable, down → STOP báo chạy lại `/dev-handoff`.",
            "**SEED data tiền-đề — BẮT BUỘC trước khi chạy TC cần data:** đọc cột `pre-condition`/`test-data` của TC → tạo prerequisite (token/tenant/entity) **qua API thật** (POST tạo theo `api-{boundary}.md`) — black-box, KHÔNG insert DB tay nếu có endpoint. Reference/sample data (lookup, slot…) đã seed ở `docs/architecture/infra/init/*.sql` lúc dev-handoff. Sau TC → **cleanup** record vừa tạo (isolation, deterministic). TC cần data mà không seed = KHÔNG được `skip`/`pass` khống (phải seed rồi chạy thật).",
            "Foreach TC `type=auto` (P0 trước) — **black-box trên hệ thống đang chạy**: **API smoke** (gọi endpoint thật → assert status/shape/field) + **UI/e2e** (Playwright/integration_test). KHÔNG build source, KHÔNG đo coverage (việc DEV). Service/UI chưa up → `skip` (ghi lý do service-down vào log) — nhưng skip bị ĐỐI CHIẾU health-proof.json: proof nói UP mà skip = gate chặn; service chết thật → re-run `py scripts/capture_infra_proof.py` cập nhật proof trước khi skip.",
            f"**TC trên WEB boundary (UI/e2e):** Playwright mở trang thật (log `GET <url> -> status` từ page.goto) + **screenshot MỖI TC (pass hay fail)** vào `tracking/{wave_id}/screenshots/{{TC}}.png` (gate test_evidence check PNG thật) + **assert style token áp dụng** (computed style element chính khớp design-tokens, KHÔNG phải browser default — trang trắng/unstyled = FAIL + bug layer=frontend đính screenshot).",
            "TC tag `@deferred` (AC/feature đã khai báo deferred ở wave plan) → `skip(deferred)`, **KHÔNG log bug, KHÔNG tính fail** (out-of-scope wave này).",
            f"Append result vào `tracking/{wave_id}/test-report.md` (mỗi TC: result + network-call `METHOD path -> status`). **Bằng chứng bắt buộc (gate test_evidence):** mỗi auto-TC in-scope phải có log thật ở `tracking/{wave_id}/test-logs/{{TC}}.log`; group integration/e2e/perf/security phải có dòng `METHOD path -> status` trong log; skip phải nêu lý do service-down (không mâu thuẫn health-proof); TC web boundary phải có screenshot. Thiếu = gate chặn (nghi test ảo).",
            f"Fail → append row vào bảng `tracking/{wave_id}/bugs.md` (origin: auto, đủ TC/AC/error-log). **KHÔNG spawn fix, KHÔNG loop** — bug auto fix qua `/fix-bugs` ở MANUAL_TEST.",
            "**KHÔNG teardown infra** — giữ UP cho MANUAL_TEST; teardown ở `/done-wave`.",
            "Return RETURN SCHEMA với `test_result: pass|fail`, `test_cases_count`, `bugs_logged: [...]`. `build`/`lint` = `pass` (n/a — black-box KHÔNG build); BỎ QUA `coverage_pct` (KHÔNG đo ở đây). **Harness DERIVE `test_result` từ test-report.md** (auto-TC in-scope all-pass → pass; còn lại → fail) — tự-khai pass mà report có fail sẽ bị end-wave chặn.",
            "Harness auto-transition TEST_EXECUTE → MANUAL_TEST sau khi chạy (pass HAY fail).",
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
        skills_block(["infra-local-dev"]),
        docs_to_read([
            ("Bugs", f"tracking/{wave_id}/bugs.md"),
            ("Test report", f"tracking/{wave_id}/test-report.md"),
            ("QC signoff", f"tracking/{wave_id}/qc-signoff.md"),
            ("docker-compose", "docs/architecture/infra/docker-compose.yml"),
        ]),
        tasks_block([
            f"Verify `tracking/{wave_id}/bugs.md` không còn bug status != closed.",
            f"Write `tracking/{wave_id}/qc-signoff.md` với checklist + UAT signoff.",
            "Update KG execution_history per boundary: status=COMPLETED + end_date + deliverables.",
            "**Tắt service (UAT đã xong ở MANUAL_TEST):** `docker compose -f docs/architecture/infra/docker-compose.yml stop` "
            "— dừng container nhưng **GIỮ image + volume** (data) để wave kế `dev-handoff` `up -d` khởi động lại NHANH (reuse). "
            "KHÔNG `down --volumes` (đó là `/done-wave` hard-close). Infra-dep (postgres/redis/kafka) cũng stop cùng.",
            "Return RETURN SCHEMA với `uat_signed: true` + `infra_stopped: true`.",
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
        f"\nAgent: **apply-cr-agent** · Analyze CR impact + transition DOMAIN_AUTHORING for amendment.",
        state_bundle(state, {"cr_id": cr_id}),
        NON_NEGOTIABLES,
        skills_block(["business-analysis"], available=["implementation-plan"], note="Skill check CR impact lên scope/AC/BR."),
        docs_to_read([
            ("CR file", f"tracking/change-requests/{cr_id}-*.md"),
            ("PROJECT", "docs/architecture/PROJECT.md"),
            ("Epic/FEAT/BR hiện có (xác định CR thêm mới hay sửa)", "docs/architecture/{epics/EP-*,feat/FEAT-*,business-rules/BR-*}.md"),
            ("BOUNDARY-MAP (CR có cần boundary mới? → nếu có, dùng done-wave→discovery thay vì apply-cr)", "docs/discovery/BOUNDARY-MAP.md"),
            ("WAVE-SEQUENCE", "docs/plans/WAVE-SEQUENCE.md"),
            ("MATRIX", "harness/SERVICE-BOUNDARY-MATRIX.json"),
        ]),
        tasks_block([
            "Invoke skill `business-analysis` để analyze CR impact (+ `implementation-plan` on-demand cho wave-plan impact).",
            f"Read CR file để hiểu scope change. Phân loại: (a) thêm/đổi FEATURE (product) hay (b) chỉ đổi kiến trúc/contract.",
            "Identify affected boundaries (cross-reference MATRIX). Nếu CR cần BOUNDARY MỚI (chưa trong BOUNDARY-MAP) → KHÔNG dùng apply-cr; báo user dùng `done-wave` → `/discovery-start D3` (charter boundary mới).",
            "Update CR file § 'Kế hoạch cập nhật' với impact analysis.",
            f"Return RETURN SCHEMA với `cr_id: {cr_id}`.",
            "After complete: STATE → **DOMAIN_AUTHORING**. CR feature → `/domain-po`/`/domain-ba` author business mới → `/domain-approve` → `/domain-translate` → `/domain-end`. CR kiến trúc-only → `/domain-end` qua thẳng. Rồi `/design` → `/design-end` → `/plan` → REVIEW → `/start-wave`.",
        ]),
        RETURN_SCHEMA_TEMPLATE,
    ]
    return "\n\n".join(parts)


# ========================================================================
# Dispatch
# ========================================================================

def build_review_dev_wave(state: dict, matrix: list[dict], opts: dict) -> str:
    """Wave-scoped /review-dev (không --boundary): orchestrator cho main loop review TUẦN TỰ mọi boundary trong wave."""
    wave_boundaries = state.get("wave_boundaries") or []
    wave_id = (state.get("wave") or {}).get("id") or "<wave>"
    rows = []
    for bid in wave_boundaries:
        b = find_boundary(matrix, bid) or {}
        k = b.get("kind", "?")
        rows.append((bid, k))
    if rows:
        table = "| boundary | kind | review agent |\n|---|---|---|\n" + "\n".join(
            f"| `{bid}` | `{k}` | `review-{k}-agent` (skill `{(REVIEW_SKILLS_PER_KIND.get(k) or ['review-?'])[0]}`) |"
            for bid, k in rows
        )
        steps = "\n".join(f"py scripts/build_prompt.py review-dev --boundary {bid}   # → spawn review-{k}-agent" for bid, k in rows)
    else:
        table = "_(wave_boundaries rỗng — chạy /start-wave trước)_"
        steps = "# (không có boundary)"

    parts = [
        f"# SPAWN PROMPT — /review-dev (WAVE-SCOPED: {wave_id})",
        state_bundle(state, {"mode": "wave-review"}),
        NON_NEGOTIABLES,
        "## MỤC TIÊU\n"
        "Review **TOÀN BỘ** boundary trong wave này, mỗi boundary theo **kind** của nó. "
        "Pass chỉ khi **MỌI** boundary pass (review_result + coverage theo kind).",
        "## BOUNDARIES TRONG WAVE\n\n" + table,
        "## CÁCH CHẠY — BẠN (MAIN) ORCHESTRATE VÒNG REVIEW→FIX\n"
        "> review-agent là sub-agent **KHÔNG tự spawn fix được** (không nest spawn). Vì vậy **BẠN — MAIN loop — điều phối**: "
        "review trả findings → BẠN đọc → BẠN spawn fix → BẠN re-review. Không có 'agent tự loop'.\n\n"
        "Lệnh lấy prompt review từng boundary:\n```\n" + steps + "\n```\n\n"
        "Với MỖI boundary theo thứ tự (TUẦN TỰ, không song song), lặp tới sạch:\n"
        "1. **Spawn `review-{kind}-agent`** với prompt trên. Review-agent: kiểm theo checklist → "
        f"GHI/cập nhật `tracking/{wave_id}/review-findings.md` (mỗi finding 1 row: severity/status/boundary/file/type/suggested_fix) → "
        "return RETURN SCHEMA `{review_result, open_findings, coverage_pct}`. Review **KHÔNG** spawn fix.\n"
        "2. Đọc `open_findings` trong return:\n"
        "   - `== 0` → boundary sạch, sang bước 4.\n"
        f"   - `> 0` → đọc các row `status=open` của boundary trong `tracking/{wave_id}/review-findings.md` → "
        "**BẠN spawn `fix-{prefix}-{boundary}-agent` (Mode B)**, compose prompt = FEAT/AC boundary + danh sách finding (file/type/suggested_fix). "
        "Fix sửa code → set row `status=resolved` → return.\n"
        "3. **Quay lại bước 1** (re-review) — review xác nhận row resolved, phát hiện thêm nếu có. Lặp tới `open_findings==0` (cap ~5 vòng; quá → STOP báo user).\n"
        "4. Ghi `{boundary, kind, review_result:pass, coverage_pct}`. Sang boundary kế.",
        "## KẾT THÚC\n"
        "- Khi MỌI boundary `open_findings==0` + `review_result=pass`:\n"
        "```\npy scripts/harness.py review-dev complete '{\"review_results\":[{\"boundary\":\"<b>\",\"kind\":\"<k>\",\"review_result\":\"pass\",\"coverage_pct\":NN}]}'\n```\n"
        f"- **Gate `no_open_findings` chặn complete** nếu `tracking/{wave_id}/review-findings.md` còn row BLOCKER/MAJOR `status=open` → buộc fix sạch trước, không lách được.\n"
        "- Boundary nào fix mãi không sạch → **STOP**, báo user, KHÔNG complete.\n"
        "- Gate `/dev-handoff` verify thêm: mọi `wave_boundaries` có trong `review_results` pass + coverage đạt ngưỡng kind.",
    ]
    return "\n\n".join(parts)


def build_fix_bugs_sweep(state: dict, matrix: list[dict], opts: dict) -> str:
    """/fix-bugs KHÔNG có --bug-id: sweep MỌI bug open. MAIN đọc bugs.md → loop spawn fix per bug."""
    wave_id = (state.get("wave") or {}).get("id") or "<wave>"
    parts = [
        f"# SPAWN PROMPT — /fix-bugs (SWEEP — mọi bug open trong {wave_id})",
        state_bundle(state, {"mode": "fix-sweep"}),
        NON_NEGOTIABLES,
        "## MỤC TIÊU\n"
        "Fix **MỌI bug đang mở** trong `bugs.md` (`status ∈ {open, in_progress}`). Tự động — KHÔNG cần user báo từng ID.",
        docs_to_read([("Bugs", f"tracking/{wave_id}/bugs.md")]),
        "## CÁCH CHẠY — BẠN (MAIN) ĐIỀU PHỐI (fix-agent làm việc nặng)\n"
        f"1. Đọc `tracking/{wave_id}/bugs.md` → lấy MỌI row `status ∈ {{open, in_progress}}` (cột `BUG` + `boundary`).\n"
        "2. Với MỖI bug (tuần tự):\n"
        "```\npy scripts/build_prompt.py fix-bugs --bug-id <BUG-NNN> --boundary <boundary trong row>\n```\n"
        "   → spawn `fix-{prefix}-{boundary}-agent` (Mode A) với prompt đó → fix re-run TC verify → set row `status=closed`.\n"
        "3. Xong bug này mới sang bug kế. Hết bug open → done.\n"
        "4. MAIN CHỈ điều phối (đọc bugs.md + spawn tuần tự); KHÔNG tự fix code.",
        "## KẾT THÚC\n"
        "- Mọi bug open → closed: báo user.\n"
        "- Bug nào fix mãi không được → STOP, báo user (KHÔNG để loop vô hạn).",
    ]
    return "\n\n".join(parts)


def build_log_bug(state: dict, matrix: list[dict], opts: dict) -> str:
    """/log-bug "<mô tả>": spawn log-bug-agent ghi 1 bug manual vào bugs.md (UAT)."""
    wave_id = (state.get("wave") or {}).get("id") or "<wave>"
    desc = opts.get("description") or opts.get("input") or "<mô tả bug — user truyền qua /log-bug>"
    parts = [
        "# SPAWN PROMPT — /log-bug",
        "\nAgent: **log-bug-agent** · Ghi 1 bug `manual` vào bugs.md từ mô tả UAT (KHÔNG fix).",
        state_bundle(state, {"mode": "log-bug"}),
        NON_NEGOTIABLES,
        f"## MÔ TẢ BUG (từ user)\n\n> {desc}",
        skills_block(["bug-logging"]),
        docs_to_read([
            ("Bugs (lấy BUG-NNN kế tiếp)", f"tracking/{wave_id}/bugs.md"),
            ("FEAT (suy AC + boundary)", "docs/architecture/feat/FEAT-*.md"),
            ("UX (suy màn → boundary FE)", "docs/architecture/ux/ux-*.md"),
            ("MATRIX (danh sách boundary)", "harness/SERVICE-BOUNDARY-MATRIX.json"),
        ]),
        tasks_block([
            "Invoke skill `bug-logging` (format bảng + ID increment).",
            f"Đọc `tracking/{wave_id}/bugs.md` → `BUG-NNN` kế tiếp (max id + 1).",
            "Parse mô tả → `title` / `reproduce` / `expected` / `actual`. `sev=medium` nếu mô tả không nêu.",
            "**Suy `boundary`** từ nội dung + màn/context trong mô tả (đối chiếu FEAT/UX/MATRIX). KHÔNG rõ → hỏi user đúng 1 câu 'bug thuộc boundary nào'.",
            "Map `AC` (`FEAT-N:AC-M`) nếu xác định được FEAT liên quan; else để rỗng.",
            f"**Append 1 row** vào bảng `tracking/{wave_id}/bugs.md`: `origin=manual`, `status=open`, đủ title/boundary/reproduce/expected/actual/sev.",
            "Return RETURN SCHEMA với `bug_id: BUG-NNN`.",
        ]),
        RETURN_SCHEMA_TEMPLATE,
    ]
    return "\n\n".join(parts)


BUILDERS = {
    "discovery-start": build_discovery_start,
    "discovery-end": build_discovery_end,
    "domain-po": lambda s, m, o: build_domain_author(s, m, {**o, "command": "domain-po"}),
    "domain-ba": lambda s, m, o: build_domain_author(s, m, {**o, "command": "domain-ba"}),
    "domain-approve": build_domain_approve,
    "domain-translate": build_domain_translate,
    "domain-end": build_domain_end,
    "design": build_design,
    "design-ux": build_design_ux,
    "design-end": build_design_end,
    "plan": build_plan,
    "review-document": build_review_document,
    "approve-document": build_approve_document,
    "start-wave": build_start_wave,
    "start-dev": lambda s, m, o: build_boundary_command(s, m, o, "start-dev"),
    "review-dev": lambda s, m, o: (
        build_boundary_command(s, m, o, "review-dev") if o.get("boundary")
        else build_review_dev_wave(s, m, o)
    ),
    "dev-handoff": build_dev_handoff,
    "test-plan": build_test_plan,
    "test-execute": build_test_execute,
    "fix-bugs": lambda s, m, o: (
        build_boundary_command(s, m, o, "fix-bugs") if o.get("bug_id")
        else build_fix_bugs_sweep(s, m, o)
    ),
    "log-bug": build_log_bug,
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
    ap.add_argument("--wave", type=int)
    ap.add_argument("--disc-wave", dest="disc_wave", help="for /discovery-start|end (D0|D1|D2|D3)")
    ap.add_argument("--mode", help="for /domain-po (EPIC|FEATURE|JOURNEY) | /domain-ba (BR|PERSONA)")
    ap.add_argument("--target", help="for /domain-approve (EP-/FEAT-/BR-... id, hoặc bỏ trống = all)")
    ap.add_argument("--bug-id", dest="bug_id")
    ap.add_argument("--cr-id", dest="cr_id")
    ap.add_argument("--input")
    ap.add_argument("--feedback", help="for /review-document revision mode")
    ap.add_argument("--description", dest="description", help="for /log-bug — mô tả bug manual")
    ap.add_argument("--target-file", dest="target_file", help="for /review-document --file")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--save")
    args = ap.parse_args()

    opts = {
        "boundary": args.boundary,
        "wave": args.wave,
        "bug_id": args.bug_id,
        "cr_id": args.cr_id,
        "input": args.input,
        "disc_wave": args.disc_wave,
        "mode": args.mode,
        "target": args.target,
        "feedback": args.feedback,
        "description": args.description,
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
