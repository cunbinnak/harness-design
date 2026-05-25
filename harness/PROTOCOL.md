# PROTOCOL

Giao thức orchestrator (Harness) <-> sub-agent. **Harness = lớp ngoài model** quyết định agent, stage, I/O, memory, boundary.

## Nguồn sự thật

| Khái niệm | File |
|----------|------|
| State hiện tại | `harness/STATE.json` (audit trail: `checkpoints[]`) |
| Stage / transitions | `harness/STATE-MACHINE.json` (13 states) |
| Command gates + sequence | `harness/COMMAND-GATES.json` |
| Hooks + evidence schemas | `harness/HOOK-RULES.json` |
| **Agent doc-scope registry** | `harness/AGENT-DISCIPLINE.json` (`agent_roles` + `memory_layers`) |
| Pipeline multi-step | `harness/PIPELINES.json` |
| Boundary & ownership | `harness/SERVICE-BOUNDARY-MATRIX.json` |
| Shared memory (KG) | `knowledge-base/*.knowledge-graph.yaml` |
| Spec sản phẩm | `docs/` |
| Discipline rule | `.cursor/rules/harness-agent-discipline.mdc` + `knowledge-base` (`discipline.*`) |

## Sub-agent spawn

1. **Pre-spawn:** `STATE.stage` thuộc `spawn.allowed_stages`, boundary trong matrix, `spawn.active == null`.
2. **Spawn:** `build_command_prompt.py <cmd> [--boundary X]` -> inject vào prompt: STATE block, agent spec, KG, DOCS IN SCOPE (auto-resolve từ `agent_roles[<role>]`).
3. **Agent làm việc** -> trả RETURN SCHEMA (JSON only).
4. **Post-agent hooks:** `return_schema` + `discipline_kg_return` check `kg_appended` -> orchestrator lưu `checkpoints[]`.

## RETURN SCHEMA

```json
{
  "completed": ["FEAT-XXX:AC-1"],
  "deferred": [{"item": "...", "reason": "...", "tracked_in": "CR-001"}],
  "needs_review": [{"file": "path", "concern": "..."}],
  "files_changed": ["path1"],
  "kg_appended": ["decision:DEC-001", "learning:..."],
  "build": "pass",
  "lint": "pass",
  "test": "pass",
  "coverage_pct": null
}
```

`kg_appended` BẮT BUỘC khi có `files_changed` hoặc `completed` (hook `discipline_kg_return` chặn nếu thiếu).

## Gate evidence (transient)

```bash
py scripts/harness.py <command> complete '<json evidence>'
```

Evidence là input cho gate check tại moment complete -> ghi vào `checkpoints[]` (audit trail). Không có dict riêng `wf.evidence` — agent kế tiếp đọc context qua KG + STATE + DOCS IN SCOPE.

| Command | Gate chính |
|---------|--------------|
| `review-document` | `approved: true` |
| `dev-handoff` | `coverage_pct >= 80`, `coverage_fe_pct >= 60`, `handoff_ready: true` |
| `test-execute` | `test_result: pass | fail` |
| `retest` | `test_result: pass | fail` (smart routing dựa bug origin) |
| `release` | prior test pass + `release_ok: true` |
| `end-wave` | `end_wave_ok: true` |
| `done-wave` | `done_wave_ok: true` |

Hooks chi tiết: `scripts/hooks/README.md` · `run_hook.py` · `ide_bridge.py`.

## Retry / loop

```
SELF_REVIEW -> IMPLEMENTATION (review_fail)

SPECIALIST_TESTING -> BUG_LOGGING -> FIX_MANUAL_BUGS -> SPECIALIST_TESTING (retest)
                                                          ^
                                                          | retest_manual
MANUAL_TEST -> BUG_LOGGING -> FIX_MANUAL_BUGS ------------+
```

## Handoff & audit

| Loại | Nơi |
|------|-----|
| Wave handoff doc | `STATE.handoff.file` (vd `handoff/wave-001.md`) |
| Audit trail | `STATE.checkpoints[]` (mỗi command complete) |
| Decisions bền | `knowledge-base/*.yaml` -> `decisions[]` |
| Per-wave artifacts | `tracking/waves/{wave-id}/` |
