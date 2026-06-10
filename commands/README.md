# Commands

Source of truth: 12 command file ở `commands/*.md`. Sync sang `.claude/commands/` qua `py scripts/sync_commands.py`.

State machine: [harness/STATE-MACHINE.json](../harness/STATE-MACHINE.json) (10 states, 14 transitions).

## Wave flow

| # | Command | From state | To state | Note |
|---|---------|-----------|----------|------|
| 1 | [intake-requirement](intake-requirement.md) | BOOTSTRAP / INTAKE | INTAKE | 4-step pipeline, iterative user confirm |
| 2 | [review-document](review-document.md) | INTAKE | INTAKE | Gate: approved=true |
| 3 | [start-wave](start-wave.md) | INTAKE | WAVE_OPEN | Materialize agents+KG per boundary |
| 4 | [start-dev](start-dev.md) | WAVE_OPEN | DEV | Spawn dev sub-agent (kind-aware) |
| 5 | [review-dev](review-dev.md) | DEV | REVIEW_DEV | Review ghi findings; MAIN spawn fix → re-review till open_findings==0 |
| 6 | [dev-handoff](dev-handoff.md) | REVIEW_DEV | DEV_HANDOFF | Gate: coverage>=80, infra ready |
| 7 | [test-plan](test-plan.md) | DEV_HANDOFF | TEST_PLAN | Sinh test-case-registry |
| 8 | [test-execute](test-execute.md) | TEST_PLAN / MANUAL_TEST | TEST_EXECUTE | Build local + run + log bug auto. KHÔNG fix. Auto MANUAL_TEST (pass/fail). Re-run được từ MANUAL_TEST |
| 9 | [log-bug](log-bug.md) | MANUAL_TEST | MANUAL_TEST | Ghi 1 bug manual (UAT) vào bugs.md (spawn log-bug-agent, origin=manual) |
| 10 | [fix-bugs](fix-bugs.md) | MANUAL_TEST | MANUAL_TEST | Sweep mọi bug open (no-arg) hoặc 1 bug-id. MAIN spawn fix (Mode A) → re-run test verify → close |
| 11 | [end-wave](end-wave.md) | MANUAL_TEST | DONE | Gate: uat_signed + no_open_bugs |
| 12 | [done-wave](done-wave.md) | DONE | BOOTSTRAP | Teardown infra, reset |
| 13 | [apply-cr](apply-cr.md) | DONE | INTAKE | CR amendment |

## Removed in v4

- `release.md` — auto-transition TEST_EXECUTE -> MANUAL_TEST khi test_result=pass (không cần command)
- `retest.md` — internal loop trong test-execute/fix-bugs (không cần command)
- `register-boundary.md` — gộp vào start-wave materialize
- `show-state.md` — đã có `py scripts/harness.py state`

## Command file frontmatter

```yaml
---
name: dev-handoff
description: ...
when_state: [REVIEW_DEV]
sets_stage: DEV_HANDOFF
spawn:
  agent: dev-handoff-agent
  skills: [infra-local-dev]
gates:
  - {type: coverage, field: coverage_pct, min: 80}
  - {type: flag, field: review_result, expected: pass}
---
```

Field meaning:
- `when_state`: command chỉ allowed khi STATE.stage ∈ list này
- `sets_stage`: stage sau khi transition thành công
- `spawn.agent`: sub-agent file cần spawn
- `spawn.skills`: skills cần load (per kind nếu materialized)
- `gates`: list rule check evidence trước khi transition

## Workflow

1. **Sửa command**: edit `commands/<name>.md` ở repo root
2. **Sync**: `py scripts/sync_commands.py` (propagate to `.claude/commands/`)
3. **Re-generate hàng loạt**: `py scripts/gen_commands.py` (dữ liệu spec ở trong script)

## Liên quan

- [harness/STATE-MACHINE.json](../harness/STATE-MACHINE.json) — state + transitions
- [harness/PROTOCOL.md](../harness/PROTOCOL.md) — chi tiết protocol orchestrator↔sub-agent
- [agents/README.md](../agents/README.md) — agent inventory + materialize
- Root [CLAUDE.md](../CLAUDE.md) — router file, SLASH COMMANDS section
