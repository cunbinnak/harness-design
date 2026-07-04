# Commands

Source of truth: 24 command file ở `commands/*.md`. Sync sang `.claude/commands/` qua `py scripts/sync_commands.py`.

State machine: [harness/STATE-MACHINE.json](../harness/STATE-MACHINE.json) (17 states, 24 commands).

## Front-half (intake tách nhỏ — clone ADLC; DOMAIN 2 lớp business↔eng)

| # | Command | From state | To state | Note |
|---|---------|-----------|----------|------|
| 1 | [discovery-start](discovery-start.md) | BOOTSTRAP / DISC_D{N} | DISC_D{N} / DISC_D{N+1} | TIẾN qua wave (gate wave đang rời) hoặc refine cùng wave |
| 2 | [discovery-end](discovery-end.md) | DISC_D3 | DOMAIN_AUTHORING | Chốt Discovery (1 lần, gate D3) |
| 3 | [domain-po](domain-po.md) | DOMAIN_AUTHORING | DOMAIN_AUTHORING | Author BUSINESS Epic/Feature/Journey (plain VN, `docs/domain/`, self-loop) |
| 4 | [domain-ba](domain-ba.md) | DOMAIN_AUTHORING | DOMAIN_AUTHORING | Author BUSINESS BR/Persona (plain VN, `docs/domain/`, self-loop) |
| 5 | [domain-approve](domain-approve.md) | DOMAIN_AUTHORING | DOMAIN_AUTHORING | KÝ business doc (`status: APPROVED`, jargon-check; `<id>` hoặc all) |
| 6 | [domain-translate](domain-translate.md) | DOMAIN_AUTHORING | DOMAIN_AUTHORING | DỊCH business đã ký → eng `docs/architecture/` (gate domain_signed) |
| 7 | [domain-end](domain-end.md) | DOMAIN_AUTHORING | DESIGN | Gate: domain_gate + planning_lint + translation_parity |
| 8 | [design](design.md) | DESIGN / PLAN | DESIGN | Self-loop refine hệ thống/contract — solution-architect (từ PLAN = back-edge). KHÔNG UX, KHÔNG advance |
| 9 | [design-ux](design-ux.md) | DESIGN / PLAN | DESIGN | Self-loop UX/UI cho FE boundary — ux-designer-agent (ux-*.md + design-tokens.css). Chạy SAU /design |
| 10 | [design-end](design-end.md) | DESIGN | PLAN | Gate: design_gate + todo_resolved |
| 11 | [plan](plan.md) | PLAN | REVIEW | Gate: plan_gate + lint + plan_integrity + matrix_coherence + api_transport + wave_sequence_lint + contract_graph_parity |
| 12 | [review-document](review-document.md) | REVIEW | REVIEW | CÓ arg = revision; KHÔNG arg = sanity-check (ghi doc-review-findings.md) |
| 13 | [approve-document](approve-document.md) | REVIEW | REVIEW | Gate doc_review + approved=true (no transition) |

> Back-edge: `PLAN --/design--> DESIGN`; `DESIGN --/domain-po·/domain-ba--> DOMAIN_AUTHORING` (sửa business → re-ký → re-translate → tiến lại re-gate).

## Wave flow (back-half)

| # | Command | From state | To state | Note |
|---|---------|-----------|----------|------|
| 14 | [start-wave](start-wave.md) | REVIEW | WAVE_OPEN | Materialize agents+KG per boundary (gate approved=true + wave_in_matrix) |
| 15 | [start-dev](start-dev.md) | WAVE_OPEN / DEV | DEV | Spawn dev sub-agent (kind-aware, lặp per boundary) |
| 16 | [review-dev](review-dev.md) | DEV | REVIEW_DEV | Review cả wave, ghi findings; MAIN spawn fix → re-review till open_findings==0 |
| 17 | [dev-handoff](dev-handoff.md) | REVIEW_DEV | DEV_HANDOFF | Gate: all_boundaries_reviewed (coverage derive từ report) + infra/health/api proof + code_compliance + web_styling |
| 18 | [test-plan](test-plan.md) | DEV_HANDOFF | TEST_PLAN | Sinh registry. Gate: contract/ui_test_present + registry_scope + ac_coverage |
| 19 | [test-execute](test-execute.md) | TEST_PLAN / MANUAL_TEST | TEST_EXECUTE | Black-box trên hệ thống đang chạy + log bug auto. KHÔNG fix. Auto MANUAL_TEST (gate test_evidence) |
| 20 | [log-bug](log-bug.md) | MANUAL_TEST | MANUAL_TEST | Ghi 1 bug manual (UAT) vào bugs.md (origin=manual) |
| 21 | [fix-bugs](fix-bugs.md) | MANUAL_TEST | MANUAL_TEST | Sweep mọi bug open (no-arg) hoặc 1 bug-id → re-run test verify → close |
| 22 | [end-wave](end-wave.md) | MANUAL_TEST | DONE | Gate: uat_signed + test_result=pass + no_open_bugs. Stop service (giữ image+volume) |
| 23 | [done-wave](done-wave.md) | DONE | BOOTSTRAP | Teardown infra (down --volumes), reset |
| 24 | [apply-cr](apply-cr.md) | DONE | DOMAIN_AUTHORING | CR feature → po/ba → ký → translate; kiến trúc-only → /domain-end thẳng |

## Removed

- `domain-start.md` — tách thành `domain-po` + `domain-ba` (author business 2 lớp) + `domain-approve` (ký) + `domain-translate` (dịch eng); không còn author thẳng vào `docs/architecture/`.
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
