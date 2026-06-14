# Commands

Source of truth: 19 command file ở `commands/*.md`. Sync sang `.claude/commands/` qua `py scripts/sync_commands.py`.

State machine: [harness/STATE-MACHINE.json](../harness/STATE-MACHINE.json) (17 states, 19 commands).

## Front-half (intake tách nhỏ — clone ADLC)

| # | Command | From state | To state | Note |
|---|---------|-----------|----------|------|
| 1 | [discovery-start](discovery-start.md) | BOOTSTRAP / DISC_D{N} | DISC_D{N} | Vào/ở wave D0-D3 + spawn agent (self-loop) |
| 2 | [discovery-end](discovery-end.md) | DISC_D{N} | DISC_D{N+1} / DOMAIN_AUTHORING | Verify gate (discovery_gate) → wave kế; D3 → DOMAIN |
| 3 | [domain-start](domain-start.md) | DOMAIN_AUTHORING | DOMAIN_AUTHORING | Author EPIC/FEATURE/JOURNEY/BR/PERSONA (self-loop) |
| 4 | [domain-end](domain-end.md) | DOMAIN_AUTHORING | DESIGN | Gate: ≥1 epic+feat+BR |
| 5 | [design](design.md) | DESIGN | PLAN | ADR/HLD/API/data-model/UX/events/integrations. Gate design_gate |
| 6 | [plan](plan.md) | PLAN | REVIEW | WAVE-SEQUENCE + wave-*.md + MATRIX + KG. Gate plan_gate |
| 7 | [review-document](review-document.md) | REVIEW | REVIEW | Revision loop (feedback) |
| 8 | [approve-document](approve-document.md) | REVIEW | REVIEW | Mark approved=true (no transition) |

## Wave flow (back-half)

| # | Command | From state | To state | Note |
|---|---------|-----------|----------|------|
| 9 | [start-wave](start-wave.md) | REVIEW | WAVE_OPEN | Materialize agents+KG per boundary (gate approved=true) |
| 10 | [start-dev](start-dev.md) | WAVE_OPEN | DEV | Spawn dev sub-agent (kind-aware) |
| 11 | [review-dev](review-dev.md) | DEV | REVIEW_DEV | Review ghi findings; MAIN spawn fix → re-review till open_findings==0 |
| 12 | [dev-handoff](dev-handoff.md) | REVIEW_DEV | DEV_HANDOFF | Gate: coverage>=80, infra ready |
| 13 | [test-plan](test-plan.md) | DEV_HANDOFF | TEST_PLAN | Sinh test-case-registry |
| 14 | [test-execute](test-execute.md) | TEST_PLAN / MANUAL_TEST | TEST_EXECUTE | Build local + run + log bug auto. KHÔNG fix. Auto MANUAL_TEST (pass/fail) |
| 15 | [log-bug](log-bug.md) | MANUAL_TEST | MANUAL_TEST | Ghi 1 bug manual (UAT) vào bugs.md (origin=manual) |
| 16 | [fix-bugs](fix-bugs.md) | MANUAL_TEST | MANUAL_TEST | Sweep mọi bug open (no-arg) hoặc 1 bug-id → re-run test verify → close |
| 17 | [end-wave](end-wave.md) | MANUAL_TEST | DONE | Gate: uat_signed + test_result=pass + no_open_bugs |
| 18 | [done-wave](done-wave.md) | DONE | BOOTSTRAP | Teardown infra, reset |
| 19 | [apply-cr](apply-cr.md) | DONE | DESIGN | CR amendment (→ /design → /plan → REVIEW) |

## Removed

- `intake-requirement.md` — tách thành Discovery (D0-D3) → Domain → Design → Plan → Review (clone ADLC, không còn 4-step monolithic).
- `release.md` — auto-transition TEST_EXECUTE -> MANUAL_TEST khi test_result=pass (không cần command).
- `retest.md` — internal loop trong test-execute/fix-bugs (không cần command).
- `register-boundary.md` — gộp vào start-wave materialize.
- `show-state.md` — đã có `py scripts/harness.py state`.

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
  - {type: all_boundaries_reviewed}
---
```

> **Lưu ý**: frontmatter `gates:` là **documentation** — enforce thật do `scripts/gates.py GATE_RULES` (đọc bởi `gates.check_for_command`), KHÔNG parse frontmatter. Giữ `gates:` mirror GATE_RULES để khỏi lệch.

Field meaning:
- `when_state`: command chỉ allowed khi STATE.stage ∈ list này
- `sets_stage`: stage sau khi transition thành công
- `spawn.agent`: sub-agent file cần spawn
- `spawn.skills`: skills cần load (per kind nếu materialized)
- `gates`: list rule check evidence trước khi transition

## Workflow

1. **Sửa command**: edit `commands/<name>.md` ở repo root
2. **Sync**: `py scripts/sync_commands.py` (propagate to `.claude/commands/`)
3. **Verify**: `py scripts/harness.py validate` (STATE khớp STATE-MACHINE) + `py scripts/smoke_test.py`

## Liên quan

- [harness/STATE-MACHINE.json](../harness/STATE-MACHINE.json) — state + transitions
- [harness/PROTOCOL.md](../harness/PROTOCOL.md) — chi tiết protocol orchestrator↔sub-agent
- [agents/README.md](../agents/README.md) — agent inventory + materialize
- Root [CLAUDE.md](../CLAUDE.md) — router file, SLASH COMMANDS section
