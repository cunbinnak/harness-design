# PROTOCOL

Giao thức orchestrator (Harness v4) ↔ sub-agent. Harness = lớp ngoài model quyết định agent, state, I/O, memory, boundary.

## Nguồn sự thật

| Khái niệm | File |
|----------|------|
| State hiện tại | `harness/STATE.json` |
| State machine (10 states + 14 transitions) | `harness/STATE-MACHINE.json` |
| Boundary metadata + ownership | `harness/SERVICE-BOUNDARY-MATRIX.json` |
| Gate logic (per command) | `scripts/gates.py` (inline, không separate file) |
| Hook policies (9 events) | `scripts/hooks/policies.py` + `dispatcher.py` |
| Hook config (Claude Code) | `.claude/settings.json` |
| Per-boundary memory | `knowledge-base/{prefix}-{boundary}.knowledge-graph.yaml` |
| Spec sản phẩm | `docs/architecture/`, `docs/plans/` |
| Tracking artifacts per wave | `tracking/wave-{N}/` |

## State machine (10 states)

```
BOOTSTRAP → INTAKE → WAVE_OPEN → DEV → REVIEW_DEV → DEV_HANDOFF
                                  ↑       ↓
                                  └ fix-bugs (loop)
                                           ↓
                          TEST_PLAN → TEST_EXECUTE → (auto) MANUAL_TEST
                                                      ↑       ↓
                                                      └ fix (loop)
                                                              ↓
                                                            DONE → BOOTSTRAP
                                                              ↓ apply-cr
                                                            INTAKE (amendment)
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
11. Pass → state.py apply transition, append history
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
- Intake step: `user_confirmed`, `step_completed`, `project_prefix`, `features_proposed`, ...
- Review: `review_result`, `checklist_summary`, `fix_loops_triggered`
- Test execute: `test_result`, `test_breakdown`, `bugs_logged`
- Dev handoff: `coverage_pct`, `docker_compose_ok`, `infra_status`
- End wave: `uat_signed`, `no_open_bugs`
- Done wave: `teardown_ok`

`kg_appended` BẮT BUỘC khi `files_changed` không rỗng. Hook SubagentStop warn nếu thiếu.

## Gate evidence

Sub-agent return JSON → user/orchestrator chạy:

```bash
py scripts/harness.py <command> complete '<evidence-json>'
```

Evidence là input cho gates.py check tại moment complete. Pass → state transition + ghi history.

| Command | Gate chính (gates.py) |
|---------|----------------------|
| `intake-requirement` | `step >= 1` |
| `review-document` | `feedback_processed: true` |
| `approve-document` | `approved: true` |
| `start-wave` | `approved: true` + `wave_n >= 1` + MATRIX file tồn tại |
| `start-dev` | `boundary` ∈ `wave_boundaries` |
| `review-dev` | (no evidence) |
| `dev-handoff` | `coverage_pct >= 80` + `review_result: pass` |
| `test-plan` | `docker_compose_ok: true` |
| `test-execute` | `test_cases_count >= 1` |
| `_auto` (TEST_EXECUTE → MANUAL_TEST) | `test_result: pass` |
| `fix-bugs` | `bug_id` non-empty |
| `end-wave` | `uat_signed: true` + `no_open_bugs` (parse `tracking/wave-{N}/bugs.md`) |
| `done-wave` | `teardown_ok: true` |
| `apply-cr` | `cr_id` non-empty |

## Internal loops (no command needed)

Một số state có internal agent behavior, không cần command từ user:

| State | Internal behavior |
|-------|-------------------|
| REVIEW_DEV | review-{kind}-agent spawn fix sub-agent loop tới pass |
| TEST_EXECUTE | test-execute-agent run + fail → log bug → spawn fix sub-agent → re-test loop |
| MANUAL_TEST | /fix-bugs chain spawn fix-{boundary}-agent + review-{kind}-agent verify |

## Hooks (9 events)

Tất cả route qua `scripts/hooks/dispatcher.py --event <name>`:

| Event | Matcher | Behavior |
|-------|---------|----------|
| SessionStart | startup\|resume | Inject brief STATE |
| UserPromptSubmit | * | Inject `[HARNESS stage=X ...]` header mỗi turn |
| Notification | * | Inject state header |
| PreCompact | * | Pin STATE summary + 3 recent transitions |
| PreToolUse | Bash | Check `harness <X> complete` gate; deny nếu sai |
| PreToolUse | Write\|Edit | Block protected files (STATE/STATE-MACHINE/settings.json) |
| PreToolUse | Task | KHÔNG block theo stage (Explore agent free); inject boundary reminder |
| PostToolUse | Bash | Append checkpoint sau harness complete success |
| SubagentStop | * | Parse RETURN SCHEMA, validate fields |
| Stop | * | (stub — sẽ implement build/lint/test runner per kind sau) |
| SessionEnd | * | Cleanup spawn.active nếu stale |

Hook policies pure functions in `scripts/hooks/policies.py`. Dispatcher routes events to handlers. Fail-open: hook crash → allow tool call.

## Handoff & audit

| Loại | Nơi |
|------|-----|
| Per-wave handoff doc | `handoff/wave-{N}.md` (dev-handoff + end-wave + done-wave append) |
| Audit trail | `STATE.workflow.history[]` (mỗi command complete entry) |
| Per-boundary memory | `knowledge-base/{prefix}-{boundary}.knowledge-graph.yaml` |
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
| FM-006 | Sub-agent crash giữa wave | Re-run command, state.history detect resume point |
| FM-016 | FE/Mobile thiếu INTEG mapping | Spawn pre-check warn, agent return early needs_review |
| FM-017 | Non-additive edit không user confirm | Pre-edit checklist in agent prompt, return needs_review |
