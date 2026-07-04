# Harness Setup Guide

ADLC Design Harness v4 — bộ khung orchestrator cho workflow ADLC.

## Prerequisites

- Python 3.14+
- Docker (cho dev/test infra)
- Git
- IDE: VSCode (recommend) hoặc Cursor

```bash
pip install -r requirements-harness.txt
py scripts/harness.py state    # show current STATE (default: BOOTSTRAP)
```

## First-time setup (fork repo)

Khi fork repo cho project mới:

```bash
# 1. Clone
git clone <fork-url>
cd <project>

# 2. (Optional) Reset state nếu có artifacts cũ
py scripts/reset_for_new_project.py

# 3. Verify state
py scripts/harness.py state
# stage: BOOTSTRAP
# allowed_commands: [discovery-start]
```

## Daily workflow

Mỗi command có 2 lệnh:

```bash
# 1. Build self-contained prompt cho sub-agent
py scripts/build_prompt.py <command> [options]

# 2. Apply gate + transition state (sau khi sub-agent done)
py scripts/harness.py <command> complete '<json-evidence>'
```

Check state trước mỗi command:

```bash
py scripts/harness.py state
py scripts/harness.py can <command>    # YES/NO command có được allowed
```

KHÔNG sửa `harness/STATE.json` tay — hook chặn.

## Workflow sequence (24 commands)

```
BOOTSTRAP
   ↓ /discovery-start D0 "<project description>"
DISC_D0..D3   (D0 hypothesis · D1 persona+capability · D2 event-storming · D3 charter+PROJECT.md)
   ↺ /discovery-start <D> (cùng wave = refine; D kế = tiến wave, gate wave đang rời)
   ↓ /discovery-end (chốt ở D3 → DOMAIN_AUTHORING)
DOMAIN_AUTHORING   (2 lớp business↔eng)
   ↺ /domain-po <EPIC|FEATURE|JOURNEY> · /domain-ba <BR|PERSONA> (author BUSINESS plain VN → docs/domain/)
   ↓ /domain-approve (KÝ status: APPROVED — jargon-check)
   ↓ /domain-translate (DỊCH sang eng → docs/architecture/, giữ id + source)
   ↓ /domain-end (gate domain_gate + planning_lint + translation_parity)
DESIGN
   ↺ /design (hệ thống/contract: ADR/HLD/API/data-model/events/INTEG + docker-compose — solution-architect)
   ↺ /design-ux (UX/UI cho FE boundary: ux-*.md + design-tokens.css — ux-designer, chạy SAU /design)
   ↓ /design-end (gate design_gate + todo_resolved)
PLAN
   ↓ /plan (WAVE-SEQUENCE + wave-*.md + MATRIX + KG skeleton)
REVIEW
   ↺ /review-document  (no-arg = sanity-check bắt buộc · "<feedback>" = revision loop)
   ↓ /approve-document (gate doc_review + approved=true)
   ↓ /start-wave <N>
WAVE_OPEN
   ↓ /start-dev <boundary>
DEV
   ↓ /review-dev (gate no_open_findings — review ghi findings → MAIN spawn fix → re-review)
REVIEW_DEV
   ↓ /dev-handoff (gate all_boundaries_reviewed: review pass + coverage theo kind)
DEV_HANDOFF
   ↓ /test-plan
TEST_PLAN
   ↓ /test-execute (run + log bug auto, KHÔNG fix)
TEST_EXECUTE
   ↓ (auto) sau khi chạy (pass HAY fail)
MANUAL_TEST
   ↺ /log-bug "<mô tả>" (UAT phát hiện bug → log-bug-agent ghi row origin=manual)
   ↺ /fix-bugs (sweep mọi bug open: auto+manual) hoặc /fix-bugs <bug-id>
   ↺ /test-execute (re-run full auto suite sau fix → bug mới/regression → fix tiếp)
   ↓ /end-wave (UAT signed + test_result=pass + no_open_bugs)
DONE
   ├ /done-wave → BOOTSTRAP (hard close; boundary mới → /discovery-start D3)
   └ /apply-cr <CR-ID> → DOMAIN_AUTHORING (CR feature: po/ba → ký → translate → /domain-end; kiến trúc-only: /domain-end thẳng → /design...)
```

> Phủ ĐỦ D0-D7 của ADLC dạng gộp (D4-D7 → DESIGN/PLAN, D6 → D3 PROJECT.md). Xem `CLAUDE.md §ADLC MAPPING`.

## Front-half (Discovery → Domain → Design → Plan)

Mỗi stage spawn agent bởi Claude main (flat orchestration, no orchestrator agent):

| Stage | Command | Agent / skill | Output |
|------|---------|---------------|--------|
| Discovery D0 | `/discovery-start D0` | discovery-hypothesis-agent / `discovery-hypothesis` | `docs/discovery/hypothesis-log.md` |
| Discovery D1 | `/discovery-start D1` | capability-mapper-agent / `capability-mapping` | `persona-pool.md` + `capability-map.md` |
| Discovery D2 | `/discovery-start D2` | event-stormer-agent / `event-storming` | `event-storming/ES-*.md` |
| Discovery D3 | `/discovery-start D3` | charter-author-agent / `boundary-charter` | `BOUNDARY-MAP` + `boundaries/*/CHARTER.md` + `PROJECT.md` + service_prefix |
| Domain (business) | `/domain-po <mode>` · `/domain-ba <mode>` | domain-po/ba-agent / `domain-po`,`domain-ba` | `docs/domain/{epics,feat,journeys,personas,business-rules}/` (plain VN, DRAFT) |
| Domain (ký) | `/domain-approve [<id>]` | instant (domain_approve.py — jargon-check + stamp) | business doc `status: APPROVED` |
| Domain (dịch) | `/domain-translate` | domain-translator-agent / `domain-translator` | `docs/architecture/{epics,feat,journeys,personas,business-rules}/` (eng + `source`) |
| Design | `/design` | solution-architect-agent / `technical-design` | ADR + HLD + API + data-model + events + integrations + docker-compose (KHÔNG UX) |
| Design UX | `/design-ux` | ux-designer-agent / `ux-design` | `ux/ux-{boundary}.md` + `ux/design-tokens.css` (FE boundary, sau /design) |
| Plan | `/plan` | program-planner-agent / `implementation-plan` | WAVE-SEQUENCE + wave-*.md + MATRIX + KG skeleton |

```bash
/discovery-start D0 "CRM cho công ty bán nhựa HDPE multi-tenant"
/discovery-start D1        # gate D0 (≥3 hypothesis) → sang D1; ... D2, D3 tương tự
/discovery-end             # chốt D3 → DOMAIN_AUTHORING
/domain-po FEATURE         # author FEAT business (self-loop; EPIC/JOURNEY tương tự)
/domain-ba BR              # author business-rule (PERSONA tương tự)
/domain-approve            # KÝ toàn bộ (jargon-check)
/domain-translate          # dịch sang eng docs/architecture/
/domain-end                # gate parity → DESIGN
/design                    # self-loop refine (hệ thống/contract)
/design-ux                 # UX/UI cho FE boundary (sau khi api-{be}.md sẵn)
/design-end                # → PLAN
/plan                      # → REVIEW
/review-document           # sanity-check (bắt buộc trước approve)
/review-document "PROJECT.md thiếu NFR security"   # revise nếu có gap
/approve-document
/start-wave 1              # materialize per-boundary, → WAVE_OPEN
```

## Dev cycle

```bash
/start-dev order-mgmt
# → spawn dev-{prefix}-order-mgmt-agent, scaffold services/, code

/review-dev
# → spawn review-backend-agent (kind detected from MATRIX)
# → review ghi review-findings.md + trả open_findings; MAIN spawn fix Mode B → re-review tới open_findings==0

/dev-handoff
# → verify infra docker-compose + coverage + smoke functional
```

## Test cycle

```bash
/test-plan
# → spawn test-plan-agent → write tracking/wave-{N}/test-case-registry.md

/test-execute
# → build local, run auto test với proof
# → fail → log bug (origin=auto) vào bugs.md. KHÔNG fix ở đây
# → auto-transition MANUAL_TEST (pass HAY fail); bug auto fix qua /fix-bugs
```

## UAT + Close

```bash
# Stakeholder UAT manually, log results vào tracking/wave-{N}/qc-signoff.md
# Phát hiện bug? → ghi vào bugs.md
/log-bug "lỗi validate SĐT khách hàng chưa đúng định dạng VN 10 số"
# → log-bug-agent suy boundary + append row (origin=manual, status=open) → BUG-NNN

/fix-bugs
# → sweep: MAIN đọc bugs.md → fix MỌI bug open (auto+manual) → re-run TC verify → close
# (hoặc /fix-bugs BUG-001 cho 1 cái)

/end-wave
# → mark UAT signed, transition DONE

/done-wave
# → teardown infra, archive, reset BOOTSTRAP
```

## Change Request flow

```bash
# 1. Tạo CR file
cp tracking/_templates/TEMPLATE.cr.md tracking/wave-002/change-requests/CR-001-add-payment.md
# Edit CR file: scope, rationale, ...

# 2. State phải = DONE (sau done-wave hoặc end-wave)
/apply-cr CR-001
# → analyze impact, transition DOMAIN_AUTHORING (re-enter đầu pipeline authoring)

# 3. Re-flow amendment (STATE → DOMAIN_AUTHORING)
# CR đổi product → author business vùng CR rồi ký + dịch:
/domain-po FEATURE   # (hoặc /domain-ba BR) → /domain-approve → /domain-translate
/domain-end          # CR kiến trúc-only thì chạy thẳng lệnh này
/design              # amendment ADR/HLD/API/... vùng CR
/design-end
/plan                # re-scope wave plan + MATRIX nếu cần
/review-document "..."
/approve-document
/start-wave 2        # next wave với scope updated
```

## Gate checklist (summary)

| Command | Main gate (gates.py — SoT `GATE_RULES`; bảng đầy đủ ở PROTOCOL.md §Gate evidence) |
|---------|--------------|
| `discovery-start` | `wave` non-empty + `discovery_advance` (tiến wave → gate wave đang rời) |
| `discovery-end` | `discovery_wave` — gate disk D3 (force-bypass + reason) |
| `domain-po` / `domain-ba` | `mode` non-empty |
| `domain-approve` | `domain_no_jargon` (business plain, ký được) |
| `domain-translate` | `domain_signed` (mọi business doc đã APPROVED) |
| `domain-end` | `domain_gate` + `planning_lint` + `translation_parity` (business ký ↔ eng 1-1) |
| `design` / `design-ux` | (self-loop refine — không gate; UX = ux-designer-agent riêng) |
| `design-end` | `design_gate` (ADR≥3 + INTEG + per-boundary + design-tokens khi có web) + `todo_resolved` |
| `plan` | `plan_gate` + lint + `plan_integrity` (FEAT mồ côi) + `matrix_coherence` + `api_transport` + `wave_sequence_lint` + `contract_graph_parity` |
| `review-document` | `feedback_processed: true` (no-arg = sanity-check ghi findings) |
| `approve-document` | `doc_review` (sanity-check chạy + hết gap BLOCKER/MAJOR) + `approved: true` |
| `start-wave` | `approved: true` + `wave_n >= 1` + MATRIX + `wave_in_matrix` |
| `start-dev` | `boundary` ∈ wave_boundaries |
| `review-dev` | `review_results` non-empty + `no_open_findings` (BLOCKER/MAJOR sạch) |
| `dev-handoff` | `all_boundaries_reviewed` (coverage derive từ report) + `infra_proof` + `health_proof` + `code_compliance` + `web_styling` + `api_contract_proof` |
| `test-plan` | flags + `infra_proof` + `health_proof` + `contract_test_present` + `ui_test_present` + `registry_scope` + `ac_coverage` |
| `test-execute` | `test_cases_count >= 1` + `test_evidence`; auto-transition; `test_result` harness derive |
| `log-bug` / `fix-bugs` | `bug_id` non-empty |
| `end-wave` | `uat_signed: true` + `test_result=pass` + `no_open_bugs` |
| `done-wave` | `teardown_ok: true` |
| `apply-cr` | `cr_id` non-empty (chỉ từ DONE → DOMAIN_AUTHORING) |

Chi tiết: xem [harness/PROTOCOL.md](harness/PROTOCOL.md).

## Hooks

Hook config: `.claude/settings.json` (9 events, đã wire ở Step 9 rebuild).

| Event | Behavior |
|-------|----------|
| SessionStart | Brief STATE đầu session |
| UserPromptSubmit | Inject `[HARNESS stage=X ...]` mỗi turn |
| PreToolUse(Bash) | Check gate khi `harness <X> complete` |
| PreToolUse(Write\|Edit\|NotebookEdit) | Block 4 kernel files (STATE.json, STATE-MACHINE.json, SERVICE-BOUNDARY-MATRIX.json, settings.json) |
| PreToolUse(Task) | KHÔNG block theo stage; inject boundary reminder + block dev/fix/review spawn tự viết tay (E-6) |
| PostToolUse(Bash) | no-op (STATE chỉ giữ trạng thái hiện tại) |
| SubagentStop | Validate RETURN SCHEMA JSON (7 field) |
| PreCompact | Pin STATE summary trước compact |
| SessionEnd | Cleanup spawn.active stale |

Vi phạm → hook print error rõ và refuse.

## Key paths

| Path | Role |
|------|------|
| `harness/STATE.json` | Current stage (chỉ trạng thái hiện tại, no history) |
| `harness/STATE-MACHINE.json` | 17 states + 29 transitions |
| `harness/SERVICE-BOUNDARY-MATRIX.json` | Boundary metadata + owned_paths |
| `harness/PROTOCOL.md` | Orchestrator ↔ sub-agent protocol |
| `scripts/harness.py` | CLI entry |
| `scripts/state.py` | STATE manager |
| `scripts/gates.py` | Pure gate functions |
| `scripts/build_prompt.py` | Build self-contained spawn prompt |
| `scripts/materialize.py` | Per-boundary artifact generator |
| `scripts/hooks/dispatcher.py` | Hook event router |
| `agents/` | Agent inventory (singleton + materialized) |
| `commands/` | Slash command source (synced to `.claude/commands/`) |
| `.claude/skills/` | On-demand skills (project-customizable) |
| `docs/discovery/` | hypothesis-log + persona-pool + capability-map + event-storming + BOUNDARY-MAP + CHARTER (D0-D3) |
| `docs/architecture/` | PROJECT + epics + feat + journeys + personas + business-rules (DOMAIN) + ADR + HLD + API + data-model + UX + events + integrations (DESIGN) |
| `docs/plans/` | WAVE-SEQUENCE + wave-{N} |
| `tracking/wave-{N}/` | Per-wave test/bugs/signoff + CR |
| `knowledge-base/` | Per-boundary KG yaml |

## Troubleshooting

### `state.py validate` fail

- Check `harness/STATE.json` schema matches `STATE-MACHINE.json[version]`.
- Compare with `git show pre-rebuild-{date}:harness/STATE.json` để biết baseline.

### Hook block command

- Read error message — hook print lý do cụ thể.
- KHÔNG bypass bằng sửa STATE.json — fix underlying issue (vd add evidence missing).

### Sub-agent return không phải JSON

- Check agent file RETURN SCHEMA section — sub-agent failed to follow.
- Hook SubagentStop warn (không block) — user manually verify return text.

### Skill không load

- Verify path: `.claude/skills/<skill-name>/SKILL.md` (không root `skills/`).
- Reload Claude Code session.
- Check skill frontmatter `name:` match.

## More

- Router file (Claude Code): [CLAUDE.md](CLAUDE.md)
- Cross-IDE entry: [AGENTS.md](AGENTS.md)
- Protocol detail: [harness/PROTOCOL.md](harness/PROTOCOL.md)
- Agent inventory: [agents/README.md](agents/README.md)
- Commands flow: [commands/README.md](commands/README.md)
