# PROTOCOL

Giao thức orchestrator (Harness) ↔ sub-agent (model). **Harness = lớp ngoài model** quyết định agent, stage, I/O, memory, boundary.

## Nguồn sự thật (không mâu thuẫn)

| Khái niệm | File |
|----------|------|
| State hiện tại | `harness/STATE.json` |
| Stage / trigger | `harness/STATE-MACHINE.json` |
| Boundary & ownership | `harness/SERVICE-BOUNDARY-MATRIX.json` |
| Shared memory | `knowledge-base/*.knowledge-graph.yaml` |
| Context rules | `harness/CONTEXT-RULES.json` |
| Spec sản phẩm | `docs/` |

## Sub-agent (triển khai sau)

Khi `start-dev` / `fix-bugs`: orchestrator spawn agent theo boundary (`agents/{boundary_id}-agent.md`).

1. Pre: `STATE.stage` phù hợp, boundary trong matrix, `spawn.active == null`.
2. Agent đọc KG + `STATE.context`.
3. Trả **RETURN SCHEMA** (JSON only).
4. `log-knowledge` + cập nhật handoff/tracking; `spawn-end` nếu dùng spawn.

Command workflow: `harness.py complete <command>` — xem `HUONG-DAN-SETUP.md`.

## RETURN SCHEMA

```json
{
  "completed": ["FEAT-XXX:AC-1"],
  "deferred": [{"item": "...", "reason": "...", "tracked_in": "CR-001"}],
  "needs_review": [{"file": "path", "concern": "..."}],
  "files_changed": ["path1"],
  "kg_appended": ["decision:DEC-001", "learning:..."],
  "failure_modes_logged": ["FM-001"],
  "build": "pass",
  "lint": "pass",
  "test": "pass",
  "coverage_pct": null
}
```

## Pass / fail (gate trước chuyển bước)

Điều kiện chi tiết: **`harness/COMMAND-GATES.json`**. Orchestrator gọi:

```bash
python scripts/harness.py complete <command> [evidence.json]
```

| Command | Gate chính |
|---------|--------------|
| `dev-handoff` | `coverage_pct` ≥ ngưỡng, `handoff_ready` |
| `review-document` | `approved: true` |
| `test-execute` | `test_result`: pass/fail |
| `release` | test pass + `release_ok` |

Hook: `scripts/hooks/run_hook.py transition_gate`.

## Pass / fail (trigger STATE-MACHINE — tham chiếu)

## Retry / loop

- `SELF_REVIEW` → `IMPLEMENTATION` (`review_fail`)
- `SPECIALIST_TESTING` → `BUG_LOGGING` → `FIX_MANUAL_BUGS` → `SPECIALIST_TESTING` (`retest`)

## Handoff & audit

- File: `STATE.handoff.file` (vd. `handoff/wave-001.md`)
- Checkpoint: `STATE.checkpoints[]`
- Decisions bền: `knowledge-base` → `decisions[]`
