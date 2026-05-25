# Harness Setup Guide

## Prerequisites

```bash
pip install -r requirements-harness.txt
py scripts/harness.py state
```

Mới fork repo: chạy `reset_for_new_project.py` để clear artifacts project cũ (xem [README.md](README.md)).

Ở BOOTSTRAP, `workflow.allowed_next = ["intake-requirement"]`.

---

## How commands work

Mỗi command có 2 lệnh:

```bash
py scripts/build_command_prompt.py <command> [--step N] [--input "..."] [--boundary X]
py scripts/harness.py <command> complete '<json evidence>'
```

Check `allowed_next` trước: `py scripts/harness.py state`. **KHÔNG** sửa `STATE.json` tay — hook chặn.

Evidence schema: xem `harness/COMMAND-GATES.json` + `harness/HOOK-RULES.json`.

---

## Workflow sequence

```text
intake-requirement (x4) -> review-document -> start-wave [-> register-boundary?]
  -> start-dev -> review-dev -> dev-handoff
  -> test-plan -> test-execute
       |
       +-- fail -> fix-bugs -> retest (smart: pass_auto -> SPECIALIST_TESTING)
       |
       +-- pass -> release -> end-wave [SOFT: stage = MANUAL_TEST, infra UP]
                                 |
                                 +-- bug manual -> fix-bugs -> retest (smart: pass_manual -> MANUAL_TEST)
                                 |
                                 +-- clean -> done-wave [HARD: teardown + reset -> BOOTSTRAP]

apply-cr -> intake-requirement (amendment) -> review-document -> start-wave (next wave)
```

---

## Intake (4-step pipeline)

Phân tích **toàn bộ dự án** → multi-wave plan + materialize agents/KGs.

| Step | Agent | Role | Output |
|------|-------|------|--------|
| 1 | requirement-analyst | `intake:requirement-analyst` | PROJECT.md + FEAT/* draft + open questions |
| 2 | business-analyst | `intake:business-analyst` | AC testable + BR + boundaries_suggested |
| 3 | solution-architect | `intake:solution-architect` | ADR + HLD + API + data-model + UX + integrations |
| 4 | program-planner | `intake:program-planner` | waves-roadmap, agent-roster, materialize (agents, KGs, matrix) |

```bash
py scripts/build_command_prompt.py intake-requirement --step 1 --input "<project description>"
# ... step 2, 3, 4 ...
py scripts/harness.py intake-requirement complete '{}'
```

Sau intake: `/review-document` (gate) → `/start-wave`.

Amendment: re-intake với `{"intake_mode": "amendment", "cr_id": "CR-XXX"}` — gates nhẹ hơn (`gates_amendment`).

---

## After end-wave (wave kế tiếp)

`end-wave` là **soft close** — stage chuyển `MANUAL_TEST`, infra vẫn UP. Hai đường:

| Tình huống | Lệnh |
|-----------|------|
| UAT pass, clean | `/done-wave` -> BOOTSTRAP -> `/start-wave` wave kế tiếp |
| Bug manual UAT | `/fix-bugs --boundary X` -> `/retest` -> (loop) -> `/done-wave` |
| Wave kế tiếp đã plan, không đổi scope | sau `/done-wave`: `/start-wave` với `wave_id` mới |
| Đổi scope (CR) | `/apply-cr` -> `/intake-requirement (amendment)` -> `/review-document` -> `/start-wave` |

---

## Change requests (CR)

File CR trong repo = đã duyệt. Flow:

```text
apply-cr -> intake-requirement (amendment + cr_id) -> review-document -> start-wave | start-dev
```

1. Tạo `tracking/change-requests/CR-NNN-*.md` từ [TEMPLATE.cr.md](tracking/change-requests/TEMPLATE.cr.md)
2. `py scripts/build_command_prompt.py apply-cr --cr CR-001` → agent điền § "Kế hoạch cập nhật"
3. `py scripts/harness.py apply-cr complete '{"cr_id":"CR-001"}'`
4. Intake 4 step với `intake_mode: amendment` + `cr_id`

Chi tiết: [commands/apply-cr.md](commands/apply-cr.md).

---

## Gate checklist (summary)

| Command | Main artifacts / evidence |
|---------|---------------------------|
| `intake-requirement` | PROJECT, FEAT, ADR≥3, HLD/API/data-model/UX per boundary, plans, roster, agents, KGs, integrations matrix |
| `review-document` | `approved: true` |
| `start-wave` | `wave.md` §1 ready, matrix synced from roster |
| `start-dev` | `wave.md` §2, `features_in_flight`, `boundaries_in_flight` |
| `review-dev` | `wave_active`, `dev_boundary_resolved` |
| `dev-handoff` | `coverage_pct >= 80`, `coverage_fe_pct >= 60`, `handoff_ready`, `docker-compose.yml` |
| `test-plan` | `tracking/waves/*/test-cases.md` >= 1 |
| `test-execute` | cases registry + `test_result` (auto only) |
| `fix-bugs` | `tracking/waves/*/bugs/**` >= 1, boundary resolved |
| `retest` | `test_result` (smart routing: pass_auto vs pass_manual) |
| `release` | prior test pass (checkpoint) + `release_ok: true` + wave active |
| `end-wave` | `end_wave_ok: true` + handoff doc exists |
| `done-wave` | `done_wave_ok: true` + no bugs Open in `tracking/waves/{wave-id}/bugs/` |
| `apply-cr` | CR file + § "Kế hoạch cập nhật" filled |

---

## Tracking (per-wave folder)

```
tracking/
+-- change-requests/             # cross-wave
|   +-- TEMPLATE.cr.md
|   +-- CR-NNN-*.md
+-- waves/{wave-id}/
    +-- test-cases.md            # test-plan output
    +-- test-results.md          # test-execute output (auto)
    +-- manual-test-log.md       # MANUAL_TEST stage (stakeholder)
    +-- release-notes.md         # release output
    +-- bugs/
        +-- BUG-{n}-*.md         # frontmatter: origin: auto | manual
```

Format bug ticket: xem [tracking/_templates/TEMPLATE.bug.md](tracking/_templates/TEMPLATE.bug.md). Field `origin` quyết định smart routing của `retest`.

---

## Hooks

- Logic: `harness/HOOK-RULES.json` + `scripts/hooks/`
- Cursor: `.cursor/hooks.json`
- Claude Code: `.claude/settings.local.json`

| Trigger | Khi nào |
|---------|---------|
| `session_start` | Mở session |
| `pre_write_check` | Sửa file (kiểm tra owned_paths) |
| `pre_state_transition` | `harness complete` (kiểm tra allowed_next + gate + KG blockers) |
| `pre_task_check` | Spawn sub-agent (kiểm tra stage + spawn_allowed) |
| `post_task_log` | Sub-agent kết thúc (kiểm tra RETURN + kg_appended) |

Vi phạm → "HARNESS — KHÔNG ĐƯỢC PHÉP." Không lách bằng sửa STATE.

---

## Doc scope per agent (agent_roles registry)

Mỗi agent có `role:` trong frontmatter -> `harness/AGENT-DISCIPLINE.json[agent_roles]` định nghĩa file/glob được đọc. `build_command_prompt.py` auto-inject section **DOCS IN SCOPE** vào prompt.

Ví dụ:
- `dev:backend` -> chỉ HLD/API/data-model của boundary mình + wave + KG
- `dev:frontend` -> UX + API contracts (không HLD/data-model BE internals)
- `test-execute` -> test-cases + handoff + infra (không source code)

Chi tiết: [agents/README.md](agents/README.md).

---

## Key paths

| Path | Role |
|------|------|
| `harness/STATE.json` | Current stage + `workflow.allowed_next` |
| `harness/STATE-MACHINE.json` | 13 states + transitions |
| `harness/COMMAND-GATES.json` | Gate per command + branches |
| `harness/AGENT-DISCIPLINE.json` | Rules + `agent_roles` registry |
| `harness/SERVICE-BOUNDARY-MATRIX.json` | Boundaries, owned paths (auto-sync from roster) |
| `commands/manifest.yaml` | Command registry |
| `scripts/harness.py` | CLI entry |

See: [README.md](README.md), [agents/README.md](agents/README.md), [commands/README.md](commands/README.md), [harness/PROTOCOL.md](harness/PROTOCOL.md).
