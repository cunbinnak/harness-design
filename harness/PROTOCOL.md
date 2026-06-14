# PROTOCOL

Giao thức orchestrator (Harness v4) ↔ sub-agent. Harness = lớp ngoài model quyết định agent, state, I/O, memory, boundary.

## Nguồn sự thật

| Khái niệm | File |
|----------|------|
| State hiện tại | `harness/STATE.json` |
| State machine (17 states + 29 transitions) | `harness/STATE-MACHINE.json` |
| Boundary metadata + ownership | `harness/SERVICE-BOUNDARY-MATRIX.json` |
| Gate logic (per command) | `scripts/gates.py` (inline, không separate file) |
| Hook policies (9 events) | `scripts/hooks/policies.py` + `dispatcher.py` |
| Hook config (Claude Code) | `.claude/settings.json` |
| Per-boundary memory | `knowledge-base/{boundary}.knowledge-graph.yaml` |
| Spec sản phẩm | `docs/architecture/`, `docs/plans/` |
| Tracking artifacts per wave | `tracking/wave-{N}/` |

## State machine (17 states)

**Front-half** (intake tách nhỏ — clone ADLC DISCOVERY/DOMAIN/ARCHITECT):
```
BOOTSTRAP → DISC_D0 → DISC_D1 → DISC_D2 → DISC_D3 → DOMAIN_AUTHORING → DESIGN → PLAN → REVIEW
   discovery-start/end (self-loop re-spawn; gate disk per wave)   │            │       │
   D3 → DOMAIN_AUTHORING                domain-start (self-loop) ──┘   /design   /plan  review/approve
```
**Back-half** (wave execution):
```
REVIEW → WAVE_OPEN → DEV → REVIEW_DEV → DEV_HANDOFF → TEST_PLAN → TEST_EXECUTE → (auto) MANUAL_TEST → DONE → BOOTSTRAP
 start-wave  start-dev↻      ↑ fix Mode B loop                                    ↑ fix-bugs/log-bug↻      │
                                                                                          DONE → DESIGN (apply-cr amendment)
```

Chi tiết transitions + evidence required: xem `harness/STATE-MACHINE.json`.

## Sub-agent spawn

```
1. User gọi /command [args]
2. Slash command body → Claude main đọc playbook
3. Main run: py scripts/build_prompt.py <cmd> [opts] → stdout self-contained prompt
4. Main spawn sub-agent qua Agent tool với prompt
5. Sub-agent invoke skill (primary) → load checklist/convention
6. Sub-agent làm việc, edit file trong owned_paths
7. Sub-agent return RETURN SCHEMA JSON ở dòng cuối
8. Hook SubagentStop validate RETURN SCHEMA
9. Main run: py scripts/harness.py <cmd> complete '<evidence>'
10. Hook PreToolUse(Bash) check gate (gates.py)
11. Pass → state.py apply transition (cập nhật stage + last_completed; KHÔNG ghi history)
12. Auto-transition nếu state có auto_transition_on match (vd test pass → MANUAL_TEST)
```

## RETURN SCHEMA

Mỗi sub-agent PHẢI return JSON ở dòng cuối message:

```json
{
  "completed": ["FEAT-NNN:AC-M"],
  "deferred": [{"item": "...", "reason": "...", "tracked_in": "BUG-NNN | CR-NNN"}],
  "needs_review": [{"file": "path", "concern": "..."}],
  "files_changed": ["services/{prefix-boundary}/..."],
  "kg_appended": ["entity:OrderAggregate", "br:BR-ORDER-001", "decision:DEC-NNN"],
  "build": "pass | fail",
  "lint": "pass | fail",
  "test": "pass | fail",
  "coverage_pct": 85
}
```

Extra fields theo loại agent (xem agent file RETURN SCHEMA section):
- Discovery (D0-D3): `wave`, `user_confirmed`, `service_prefix` (D3)
- Domain (po/ba): `mode`, `user_confirmed`
- Design: `user_confirmed`, `boundaries_proposed`, `adrs_created`, `nfr_addressed`
- Plan: `user_confirmed`, `waves_planned`, `boundaries_materialized`
- Review: `review_result`, `open_findings`, `coverage_pct`
- Test execute: `test_result`, `test_cases_count`, `bugs_logged`
- Dev handoff: `coverage_pct`, `docker_compose_ok`, `connectivity_ok`
- End wave: `uat_signed`; Done wave: `teardown_ok`

> RETURN SCHEMA canonical (7 field bắt buộc) inject bởi `build_prompt.py RETURN_SCHEMA_TEMPLATE`. `kg_appended` là soft-guidance trong prompt (warn ở text), **KHÔNG** enforce ở hook SubagentStop (`RETURN_SCHEMA_REQUIRED` chỉ gồm completed/deferred/needs_review/files_changed/build/lint/test).

## Gate evidence

Sub-agent return JSON → user/orchestrator chạy:

```bash
py scripts/harness.py <command> complete '<evidence-json>'
```

Evidence là input cho gates.py check tại moment complete. Pass → state transition (cập nhật stage + last_completed).

| Command | Gate chính (gates.py) |
|---------|----------------------|
| `discovery-start` | `wave` non-empty (D0..D3) |
| `discovery-end` | `discovery_wave` — `discovery_gate.py <wave>` check artifact disk (force-bypass + reason) |
| `domain-start` | `mode` non-empty (EPIC/FEATURE/JOURNEY/BR/PERSONA) |
| `domain-end` | `domain_gate` — ≥1 epic + ≥1 feat + ≥1 BR ở docs/architecture/ |
| `design` | `design_gate` — ADR≥3 + HLD + API + INTEG |
| `plan` | `plan_gate` — WAVE-SEQUENCE + MATRIX + wave-*.md + KG skeleton |
| `review-document` | `feedback_processed: true` |
| `approve-document` | `approved: true` |
| `start-wave` | `approved: true` + `wave_n >= 1` + MATRIX file tồn tại |
| `start-dev` | `boundary` ∈ `wave_boundaries` |
| `review-dev` | `no_open_findings` — reject complete nếu review-findings.md còn row BLOCKER/MAJOR status=open (review_results vẫn ghi vào STATE cho gate dev-handoff) |
| `dev-handoff` | `all_boundaries_reviewed` — mọi `wave_boundaries` review pass + coverage theo kind (BE80/BFF70/web60/mobile60) đọc từ STATE.review_results (KHÔNG check infra — infra-proof là gate test-plan) |
| `test-plan` | `docker_compose_ok: true` + `connectivity_ok` + infra proof |
| `test-execute` | `test_cases_count >= 1` |
| `_auto` (TEST_EXECUTE → MANUAL_TEST) | `test_result` (any — pass HAY fail) |
| `log-bug` | `bug_id` non-empty (log-bug-agent trả về sau khi append row) |
| `fix-bugs` | `bug_id` non-empty (đơn lẻ); sweep no-arg = MAIN orchestrate, complete per-bug |
| `end-wave` | `uat_signed: true` + `test_result: pass` (STATE — lần test-execute cuối xanh, ép re-run sau fix) + `no_open_bugs` (parse `tracking/wave-{N}/bugs.md`) |
| `done-wave` | `teardown_ok: true` |
| `apply-cr` | `cr_id` non-empty |

## Internal loops (no command needed)

Một số state có internal agent behavior, không cần command từ user:

| State | Internal behavior |
|-------|-------------------|
| REVIEW_DEV | review-{kind}-agent ghi review-findings.md + trả open_findings; MAIN (orchestrator) đọc → spawn fix Mode B → re-review tới open_findings==0 (gate no_open_findings chặn complete) |
| TEST_EXECUTE | test-execute-agent run + log bug (origin=auto) vào bugs.md. KHÔNG fix → transition MANUAL_TEST (pass HAY fail); bug auto fix qua /fix-bugs |
| MANUAL_TEST | **/log-bug "<mô tả>"**: spawn log-bug-agent → append row `origin=manual` vào bugs.md (suy boundary từ FEAT/UX/màn). **/fix-bugs** (sweep no-arg = fix mọi bug open; hoặc <bug-id>): MAIN spawn fix-{boundary}-agent (Mode A) → re-run TC + scoped test verify → close (KHÔNG gọi review-agent). **/test-execute re-run được** từ đây → chạy lại full auto suite; TC fail lại = reopen bug, regression mới = bug mới. Lặp tới sạch → /end-wave (no_open_bugs) |

## Hooks (9 events)

Tất cả route qua `scripts/hooks/dispatcher.py --event <name>`:

| Event | Matcher | Behavior |
|-------|---------|----------|
| SessionStart | startup\|resume | Inject brief STATE |
| UserPromptSubmit | * | Inject `[HARNESS stage=X ...]` header mỗi turn |
| Notification | * | Inject state header |
| PreCompact | * | Pin STATE summary hiện tại (stage + wave + boundary) |
| PreToolUse | Bash | Check `harness <X> complete` gate; deny nếu sai |
| PreToolUse | Write\|Edit\|MultiEdit\|NotebookEdit | Block 4 kernel files (STATE.json, STATE-MACHINE.json, SERVICE-BOUNDARY-MATRIX.json, settings.json) |
| PreToolUse | Task | KHÔNG block theo stage (Explore free); inject boundary reminder + block dev/fix/review spawn bằng prompt tự viết tay (E-6) |
| PostToolUse | Bash | no-op (STATE.json chỉ giữ trạng thái hiện tại) |
| SubagentStop | * | Parse RETURN SCHEMA, validate 7 field bắt buộc |
| Stop | * | Build/lint/test **wave-scoped** per kind khi stage ∈ {DEV, REVIEW_DEV, TEST_EXECUTE} + có sửa services/; đỏ→block 40 dòng cuối; cache git-hash |
| SessionEnd | * | Cleanup spawn.active nếu stale |

Hook policies pure functions in `scripts/hooks/policies.py`. Dispatcher routes events to handlers. Fail-open: hook crash → allow tool call.

## Handoff & audit

| Loại | Nơi |
|------|-----|
| Per-wave handoff doc | `handoff/wave-{N}.md` (dev-handoff + end-wave + done-wave append) |
| Audit trail | `git log` (commit per change) — STATE.json KHÔNG lưu history |
| Per-boundary memory | `knowledge-base/{boundary}.knowledge-graph.yaml` |
| Per-wave artifacts | `tracking/wave-{N}/` (test cases, report, bugs, signoff) |
| Per-wave CRs | `tracking/wave-{N}/change-requests/` |

## Failure modes

| ID | Mô tả | Mitigation |
|----|-------|------------|
| FM-001 | Agent edit ngoài owned_paths | Hook PreToolUse block |
| FM-002 | Sub-agent return không phải JSON RETURN SCHEMA | Hook SubagentStop warn |
| FM-003 | Gate fail (vd coverage < 80) | Reject `harness complete`, user fix |
| FM-004 | Spawn double sub-agent | Hook check `spawn.active != null` deny |
| FM-005 | State.json corrupt | `state.py validate` detect; manual fix |
| FM-006 | Sub-agent crash giữa wave | Re-run command; resume theo artifact đã tạo (PROJECT.md/MATRIX/code tồn tại) + `last_completed` |
| FM-016 | FE/Mobile thiếu INTEG mapping | Spawn pre-check warn, agent return early needs_review |
| FM-017 | Non-additive edit không user confirm | Pre-edit checklist in agent prompt, return needs_review |
