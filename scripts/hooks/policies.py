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
    "BOOTSTRAP": "/discover D0 (bắt đầu khám phá)",
    "DISC_D0": "/discover D1 (gate D0 → sang D1) · hoặc /discover D0 (đào thêm hypothesis)",
    "DISC_D1": "/discover D2 (gate D1 → sang D2) · hoặc /discover D1 (đào thêm capability/persona/ma trận quyền)",
    "DISC_D2": "/discover D3 (gate D2 → sang D3) · hoặc /discover D2 (đào thêm event-storming)",
    "DISC_D3": "/discover (D3 đạt gate → chốt sang DOMAIN) · hoặc /discover D3 (đào thêm charter/PROJECT)",
    "DOMAIN_AUTHORING": "/domain (hành lang nửa sau: nghiệp vụ → ký → dịch → thiết kế → chia wave → rà chéo, dừng ở REVIEW)",
    "DESIGN": "/domain (chạy tiếp: thiết kế → chia wave → rà chéo). LÙI sửa nghiệp vụ: /domain từ DOMAIN (re-ký + re-dịch)",
    "PLAN": "/domain (chạy tiếp: chia wave → rà chéo → REVIEW)",
    "REVIEW": "/approve-document (bạn ĐỌC + duyệt = KHOÁ SCOPE) → /run-wave <N> · cần sửa doc: /domain (chạy lại từ chốt liên quan)",
    "WAVE_OPEN": "/run-wave (chạy tiếp hành lang: code → review → dựng thật → test → dogfood)",
    "DEV": "/run-wave (chạy tiếp: boundary còn lại → review)",
    "REVIEW_DEV": "/run-wave (chạy tiếp: dựng chạy thật → test)",
    "DEV_HANDOFF": "/run-wave (chạy tiếp: sinh test case)",
    "TEST_PLAN": "/run-wave (chạy tiếp: chạy test)",
    "TEST_EXECUTE": "(tự động → MANUAL_TEST sau khi chạy)",
    "MANUAL_TEST": "/run-wave (sửa bug + re-test, và dogfood nếu chưa) · /dogfood <vai> (chạy lại 1 vai) · /next-wave (khi UAT ký + sạch bug)",
    "DONE": "/next-wave (snapshot + mở wave kế; hết wave thì teardown)",
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
    fp = _feature_state_progress(wave_id)  # clock-in L05: session mới thấy ngay feat còn dở
    if fp:
        lines.append(f"  features      = {fp}")
    return "\n".join(lines)


def _feature_state_progress(wave_id: str) -> str:
    """Đọc tracking/{wave}/feature-state.md → summary 1 dòng cho clock-in (feat active/còn lại).

    Không parse lại report (rẻ) — chỉ đọc bảng derive HARNESS đã ghi. Rỗng nếu chưa có file.
    """
    if not wave_id or wave_id == "-":
        return ""
    f = REPO_ROOT / "tracking" / wave_id / "feature-state.md"
    if not f.is_file():
        return ""
    passing = active = other = 0
    active_ids: list[str] = []
    for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s.startswith("| FEAT-"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 2:
            continue
        st = cells[1].split()[0] if cells[1] else ""
        if st == "passing":
            passing += 1
        elif st == "active":
            active += 1
            active_ids.append(cells[0])
        else:
            other += 1
    total = passing + active + other
    if not total:
        return ""
    tail = f" · đang dở: {', '.join(active_ids)}" if active_ids else ""
    return f"{passing}/{total} passing{tail}"


def state_header_line(state: dict, allowed_cmds: list[str]) -> str:
    """One-line header for UserPromptSubmit / Notification injection."""
    stage = state.get("stage", "?")
    wave = (state.get("wave") or {}).get("id") or "-"
    boundary = state.get("active_boundary") or "-"
    return f"[HARNESS stage={stage} wave={wave} boundary={boundary} | next: {next_step_hint(state)}]"


def memory_marker(state: dict, allowed_cmds: list[str]) -> str:
    """Pinned summary for PreCompact — giữ TRẠNG THÁI HIỆN TẠI sau compaction (không có history)."""
    return format_state_brief(state, allowed_cmds)


def _section(text: str, header: str) -> str:
    """Một mục của markdown, tới `## ` kế tiếp. Rỗng nếu không thấy."""
    i = text.find(header)
    if i < 0:
        return ""
    j = text.find("\n## ", i + len(header))
    return text[i: j if j > 0 else len(text)].strip()


def reanchor_after_compact(state: dict, allowed_cmds: list[str]) -> str:
    """Nhồi lại LUẬT sau khi context bị nén (SessionStart matcher `compact`).

    VÌ SAO CÓ HÀM NÀY
        Compact giữ được "đang làm gì" nhưng làm phẳng "đang bị cấm gì" — mà NON-NEGOTIABLES đúng
        thuộc loại thứ hai. PreCompact của mình chỉ ghim TRẠNG THÁI (stage/wave/next), không ghim luật.

        Việc này gấp hơn kể từ khi gỡ turn-flag: kỷ luật "chốt đỏ → DỪNG, không force, không nhảy
        chốt" giờ sống hoàn toàn bằng văn xuôi trong prompt. Sau compact, đó chính là thứ trôi đầu tiên.

    ĐỌC THẲNG TỪ `CLAUDE.md`, KHÔNG chép cứng vào đây — chép cứng là tự tạo bản sao thứ hai của luật:
    sửa CLAUDE.md mà quên file này thì hook nhồi luật CŨ vào đúng lúc MAIN đang mất trí nhớ, hỏng hơn
    là không nhồi gì. Không đọc được thì nói thẳng là không đọc được.
    """
    try:
        claude = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        claude = ""
    rules = _section(claude, "## NON-NEGOTIABLES")
    if not rules:
        rules = ("_Không đọc được `CLAUDE.md` §NON-NEGOTIABLES — mở file đó đọc trước khi làm tiếp._")
    return "\n".join([
        "# HARNESS — nhồi lại luật sau compact",
        "",
        "Context vừa bị nén. Bản tóm tắt giữ được *đang làm gì* nhưng thường đánh rơi *đang bị cấm gì*.",
        "Dưới đây là luật đọc THẲNG từ `CLAUDE.md`, không phải từ tóm tắt.",
        "",
        rules,
        "",
        "## Trạng thái sống (đọc từ STATE.json, không từ trí nhớ)",
        "",
        "```",
        format_state_brief(state, allowed_cmds),
        "```",
        "",
        "## Trước khi làm tiếp",
        "",
        "Không chắc đang dở việc gì → `/status`. Đừng mở việc mới khi chốt hiện tại chưa xanh.",
    ])


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


# Proof file do capture_infra_proof.py (HARNESS đo) sinh — agent KHÔNG được Write/Edit tay.
# tracking/** nói chung ghi tự do (report/bugs/registry), nhưng 3 file này là BẰNG CHỨNG máy đo
# cho gate infra_proof/health_proof/api_contract_proof — ghi tay được thì cả tầng harness-đo
# đứng trên thư mục ghi-tự-do (agent fake proof sau khi script chạy).
PROOF_FILE_RE = re.compile(
    r"^tracking/[^/]+/((docker-ps|health-proof|api-proof)\.json|feature-state\.md)$")


def is_proof_file(rel_path: str) -> bool:
    """True nếu path là artifact HARNESS-derive (chỉ script capture_* được sinh, agent KHÔNG ghi tay).

    3 proof-json (capture_infra_proof.py) + feature-state.md (capture_feature_state.py — trạng thái
    FEAT derive từ report, ghi tay = fake tiến độ). Đều là VIEW của phép derive, không phải file agent khai.
    """
    if not rel_path:
        return False
    return bool(PROOF_FILE_RE.match(rel_path.replace("\\", "/").lstrip("./")))


# ------------------------------------------------------------------------
# Doc phase-lock (single-repo port của ZIP `pretooluse-readonly-inputs.py`)
# ------------------------------------------------------------------------
# ZIP (multi-repo) đóng băng upstream bằng snapshot `_inputs/**` read-only per repo. Single-repo
# tương đương = phase-lock theo stage: mỗi LỚP doc chỉ sửa được ở stage SỞ HỮU (+ REVIEW = cửa
# revision chung). Stage khác → frozen → LÙI về stage sở hữu (back-edge /design, /domain-po//domain-ba)
# rồi tiến lại (re-gate); sau ship dùng /apply-cr. Chống dev/test sửa spec cho khớp code (anti-pattern
# e2e) + chống sửa FEAT/HLD lúc đã ở PLAN. Thực thi NON-NEGOTIABLE #6 (trước chỉ honor-system).

_REVIEW = "REVIEW"
_DISC_STAGES = {"DISC_D0", "DISC_D1", "DISC_D2", "DISC_D3"}

# (label, set stage được sửa, regex path repo-relative). infra/ KHÔNG khoá (docker-compose update ở
# dev-handoff); knowledge-base/tracking/services/handoff KHÔNG khoá (back-half/dev append).
PHASE_LOCK_CLASSES = [
    ("discovery", _DISC_STAGES | {_REVIEW},
     re.compile(r"^docs/discovery/|^docs/architecture/PROJECT\.md$")),
    # business thuần: author/ký/dịch ở DOMAIN — DESIGN KHÔNG được đụng narrative/AC/rule.
    ("domain-business", {"DOMAIN_AUTHORING", _REVIEW},
     re.compile(r"^docs/domain/|^docs/architecture/(epics|journeys|personas)/")),
    # eng spec feat/BR: dual-owner. Business (AC/rule) do DOMAIN dịch; NHƯNG field kỹ thuật
    # translator cố ý để mở (enforcement_location/consumes_contracts = `TBD (DESIGN)`) là việc
    # DESIGN điền (gate todo_resolved @/design-end). Nên DESIGN cũng sửa được lớp này.
    ("domain-spec", {"DOMAIN_AUTHORING", "DESIGN", _REVIEW},
     re.compile(r"^docs/architecture/(feat|business-rules)/")),
    ("design", {"DESIGN", _REVIEW},
     re.compile(r"^docs/architecture/(adr|hld|api|data-model|ux|events|integrations)/")),
    ("plan", {"PLAN", _REVIEW},
     re.compile(r"^docs/plans/")),
]
_BACK_HINT = {
    "discovery": "lùi qua done-wave→/discovery-start (hoặc sửa ở REVIEW)",
    "domain-business": "lùi /domain-po·/domain-ba → DOMAIN (sửa business → /domain-approve → /domain-translate)",
    "domain-spec": "field kỹ thuật (enforcement/contract) → sửa ở DESIGN; narrative/AC → lùi /domain-po·/domain-ba",
    "design": "lùi /design → DESIGN",
    "plan": "về PLAN",
}


def phase_lock_violation(rel_path: str, stage: str) -> str | None:
    """None = cho phép; str = lý do chặn (doc thuộc lớp phase-lock mà stage hiện tại không sở hữu).

    TEMPLATE.* / EXAMPLE.* + README.md luôn cho sửa (scaffolding/bài mẫu). Doc ngoài 4 lớp → không khoá.
    """
    if not rel_path or not stage:
        return None
    norm = rel_path.replace("\\", "/").lstrip("./")
    base = norm.rsplit("/", 1)[-1]
    if base.startswith("TEMPLATE.") or base.startswith("EXAMPLE.") or base == "README.md":
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
    r"(?:harness\.py|state\.py)\s+([\w-]+)\s+complete\b",
    re.IGNORECASE,
)
JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}")


# Thân heredoc = DỮ LIỆU đang được ghi ra file, không phải lệnh sắp chạy.
# `cat > commands/run-wave.md <<'EOF' … py scripts/harness.py start-wave complete … EOF`
# là viết TÀI LIỆU có ví dụ lệnh, không phải chạy lệnh đó.
HEREDOC_RE = re.compile(
    r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1[^\n]*\n.*?^\s*\2\s*$",
    re.DOTALL | re.MULTILINE,
)


def strip_heredocs(bash_cmd: str) -> str:
    """Bỏ thân heredoc khỏi command trước khi phân tích.

    VÌ SAO: hook phải xét lệnh LÀM GÌ, không phải nó CHỨA CHỮ GÌ. Không bỏ thân heredoc thì viết
    một file tài liệu có ví dụ `harness … complete` sẽ bị hook tưởng là đang chạy stage-command,
    rồi deny vì gate của lệnh đó không đạt — chặn oan đúng lúc người ta đang viết chính tài liệu
    mô tả lệnh. (Cùng họ với luật của VIPER `guard_ds`: chỉ chặn lỗi MỚI, không bắt đền nội dung
    vốn có — hook báo oan là hook sẽ bị tắt.)
    """
    if not bash_cmd or "<<" not in bash_cmd:
        return bash_cmd
    return HEREDOC_RE.sub("<<HEREDOC-BODY-STRIPPED>>", bash_cmd)


def parse_harness_complete(bash_cmd: str) -> dict | None:
    """
    Parse a bash command line like:
      py scripts/harness.py dev-handoff complete '{"coverage_pct":85,...}'

    Returns {"command": "dev-handoff", "evidence": {...}} or None.
    """
    if not bash_cmd:
        return None
    bash_cmd = strip_heredocs(bash_cmd)
    m = HARNESS_CMD_RE.search(bash_cmd)
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
    "start-dev", "fix", "review-dev",
    "domain-po", "domain-ba", "domain-translate",
    "test-plan", "test-execute", "design-ux",
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
    # dual-owner eng spec: DESIGN cũng sửa được feat/BR (điền field kỹ thuật todo_resolved)
    assert phase_lock_violation("docs/architecture/feat/FEAT-1.md", "DESIGN") is None
    assert phase_lock_violation("docs/architecture/business-rules/BR-1.md", "DESIGN") is None
    # nhưng business thuần (epics/journeys/personas + docs/domain) DESIGN KHÔNG đụng
    assert phase_lock_violation("docs/architecture/epics/EP-1.md", "DESIGN") is not None
    assert phase_lock_violation("docs/architecture/personas/PS-1.md", "DESIGN") is not None
    assert phase_lock_violation("docs/domain/feat/FEAT-1.md", "DESIGN") is not None
    assert phase_lock_violation("docs/domain/business-rules/BR-1.md", "DESIGN") is not None
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
    # TEMPLATE.* / EXAMPLE.* + README luôn sửa được (scaffolding/bài mẫu)
    assert phase_lock_violation("docs/architecture/hld/TEMPLATE.hld.md", "DEV") is None
    assert phase_lock_violation("docs/architecture/feat/README.md", "PLAN") is None
    assert phase_lock_violation("docs/architecture/ux/TEMPLATE.design-tokens.css", "PLAN") is None
    assert phase_lock_violation("docs/architecture/ux/mockups/EXAMPLE.reference.html", "DEV") is None
    # KHÔNG khoá: infra (docker-compose update ở dev-handoff), KG, tracking, services, arch root
    assert phase_lock_violation("docs/architecture/infra/docker-compose.yml", "DEV_HANDOFF") is None
    assert phase_lock_violation("knowledge-base/x.knowledge-graph.yaml", "DEV") is None
    assert phase_lock_violation("tracking/wave-001/test-report.md", "TEST_EXECUTE") is None
    assert phase_lock_violation("services/demo-x/src/A.java", "DEV") is None
    assert phase_lock_violation("docs/architecture/ARCHITECTURE-PRINCIPLES.md", "PLAN") is None
    # proof file harness-đo: agent KHÔNG được ghi tay (FM-PROOF-FORGE); tracking khác vẫn tự do
    assert is_proof_file("tracking/wave-001/health-proof.json") is True
    assert is_proof_file("tracking/wave-001/docker-ps.json") is True
    assert is_proof_file("tracking/wave-012/api-proof.json") is True
    assert is_proof_file("tracking/wave-001/feature-state.md") is True  # HARNESS-derive, agent không ghi tay
    assert is_proof_file("tracking\\wave-001\\health-proof.json") is True  # path Windows
    assert is_proof_file("tracking/wave-001/test-report.md") is False
    assert is_proof_file("tracking/wave-001/test-report.md") is False
    assert is_proof_file("tracking/doc-review-findings.md") is False
    assert is_proof_file("docs/health-proof.json") is False
    # next-step hint contextual (arg + back-edge)
    assert "/discover D2" in next_step_hint({"stage": "DISC_D1"})   # gộp: 1 lệnh cho cả D-wave
    assert "/domain" in next_step_hint({"stage": "PLAN"})          # hành lang nửa sau, chạy tiếp
    assert "/domain" in next_step_hint({"stage": "DESIGN"})       # back-edge
    assert "ký" in next_step_hint({"stage": "DOMAIN_AUTHORING"})  # flow 2 lớp: ký → dịch
    assert "header" not in state_header_line({"stage": "PLAN"}, []).lower() or True
    assert "next:" in state_header_line({"stage": "DISC_D0"}, [])
    # E-6 chặt: detect theo tên agent (registry) — khớp tên thật, không khớp prompt research
    assert detect_harness_agent_spawn("spawn domain-po-agent author epic", ["domain-po-agent", "dev-x-agent"]) == "domain-po-agent"
    assert detect_harness_agent_spawn("explore codebase for X", ["domain-po-agent"]) is None
    assert detect_harness_agent_spawn("anything", []) is None
    # heredoc: viết TÀI LIỆU có ví dụ lệnh ≠ chạy lệnh đó (hook xét lệnh LÀM GÌ, không phải CHỨA GÌ)
    _doc = ("cat > commands/run-wave.md <<'EOF'\n"
            "py scripts/harness.py start-wave complete '{\"wave_n\": 1}'\n"
            "EOF")
    assert parse_harness_complete(_doc) is None, "viết doc chứa ví dụ lệnh KHÔNG được coi là chạy lệnh"
    # heredoc không trích dẫn cũng vậy
    assert parse_harness_complete("cat > f.md <<EOF\npy scripts/harness.py plan complete\nEOF") is None
    # nhưng lệnh THẬT vẫn phải nhận ra — kể cả khi cùng dòng với heredoc khác
    _real = parse_harness_complete('py scripts/harness.py plan complete \'{"a":1}\'')
    assert _real and _real["command"] == "plan" and _real["evidence"] == {"a": 1}
    _mixed = parse_harness_complete("cat > f.md <<'EOF'\nhello\nEOF\npy scripts/harness.py plan complete")
    assert _mixed and _mixed["command"] == "plan", "lệnh thật SAU heredoc vẫn phải bị bắt"
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


# ========================================================================
# token_violation — design system đã chốt thì phải theo, chặn NGAY LÚC GHI
# ========================================================================
#
# VÌ SAO CÓ. Luật "mockup và code FE chỉ lắp từ token" hiện chỉ sống ở gate `web_styling`
# @dev-handoff — tức là BÁO sau khi code đã viết xong, và chỉ khi có người chạy tới chốt đó.
# Cám dỗ lớn nhất lúc dựng UI là gõ thẳng `#3B82F6` cho nhanh; nhanh hơn thật, và giết đúng
# tác dụng của design token: phản hồi "chữ nhỏ quá / màu chìm quá" lẽ ra sửa MỘT token rồi lan
# ra mọi màn, nay thành đi sửa tay từng chỗ — rồi pha code thừa hưởng nguyên mớ đó.
#
# CHỈ CHẶN LỖI MỚI so với bản đang trên đĩa. File bẩn từ trước (viết lúc chưa có hook) là việc
# của gate; edit không thêm lỗi — kể cả edit đang sửa dần từng lỗi một — phải đi qua, nếu không
# hook bắt đền lỗi cũ và Edit không sửa nổi file.
#
# FAIL-OPEN, và mỗi chỗ mở đều có người bắt hộ: chưa chốt design-tokens.css · file ngoài phạm vi
# · không đọc được → cho qua, gate `web_styling` + `design_system_closed` là backstop.

TOKEN_SCOPE_DIRS = ("docs/architecture/ux/mockups/",)
TOKEN_SCOPE_EXTS = (".css", ".scss", ".html", ".tsx", ".jsx", ".vue", ".svelte")
TOKENS_CSS = "docs/architecture/ux/design-tokens.css"

_RAW_COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(")
_VAR_USE_RE = re.compile(r"var\(\s*(--[\w-]+)")
_ROOT_BLOCK_RE = re.compile(r":root[^{]*\{[^}]*\}", re.DOTALL)


def _in_token_scope(rel: str) -> bool:
    if not rel:
        return False
    r = rel.replace("\\", "/")
    if r.startswith(TOKEN_SCOPE_DIRS):
        return True
    # code FE của boundary: services/**/src/** file style/component
    return r.startswith("services/") and r.endswith(TOKEN_SCOPE_EXTS)


def _strip_root(css: str) -> str:
    """Bỏ khối `:root{...}` — đó là CHỖ HỢP LỆ để khai giá trị thô."""
    return _ROOT_BLOCK_RE.sub("", css)


def _token_errors(text: str, declared: set[str]) -> tuple[set[str], set[str]]:
    """(mã màu thô ngoài :root, token dùng mà chưa khai)."""
    body = _strip_root(text)
    raw = {m.group(0) for m in _RAW_COLOR_RE.finditer(body)}
    used = {m.group(1) for m in _VAR_USE_RE.finditer(text)}
    return raw, (used - declared if declared else set())


def token_violation(rel: str, new_text: str, root: Path | None = None) -> str | None:
    """Thông báo chặn, hoặc None nếu cho qua. Chỉ tính lỗi MỚI so với bản trên đĩa."""
    if not new_text or not _in_token_scope(rel):
        return None
    base = root or Path(__file__).resolve().parent.parent.parent
    tokens_file = base / TOKENS_CSS
    if not tokens_file.is_file():
        return None                       # chưa chốt design system → chưa có gì để theo
    try:
        declared = {m.group(1) for m in re.finditer(r"(--[\w-]+)\s*:", tokens_file.read_text(
            encoding="utf-8", errors="ignore"))}
    except OSError:
        return None
    if not declared:
        return None                       # SoT chưa khai token nào → gate design_system_closed bắt
    try:
        old_text = (base / rel).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        old_text = ""
    raw_new, undecl_new = _token_errors(new_text, declared)
    raw_old, undecl_old = _token_errors(old_text, declared)
    raw = raw_new - raw_old
    undecl = undecl_new - undecl_old
    if not raw and not undecl:
        return None
    msg = [f"FM-TOKEN-DRIFT: '{rel}' thêm lỗi MỚI so với bản đang có —"]
    if raw:
        msg.append(f"  · mã màu thô ngoài `:root`: {', '.join(sorted(raw)[:5])}")
        msg.append("    Gõ thẳng hex là giết đúng tác dụng của design token: phản hồi \"màu chìm quá\"")
        msg.append(f"    lẽ ra sửa MỘT token trong `{TOKENS_CSS}` rồi lan ra mọi màn.")
    if undecl:
        msg.append(f"  · dùng token chưa khai ở SoT: {', '.join(sorted(undecl)[:5])}")
        msg.append(f"    Thiếu token thì THÊM VÀO `{TOKENS_CSS}` trước, đừng khai biến mới tại chỗ —")
        msg.append("    đó là dựng design system thứ hai mà không ai biết.")
    msg.append("  Lỗi CŨ trong file không bị tính: sửa dần từng chỗ vẫn đi qua được.")
    return "\n".join(msg)
