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

**Front-half** (intake tách nhỏ — clone ADLC DISCOVERY/DOMAIN/ARCHITECT; DOMAIN 2 lớp business↔eng):
```
BOOTSTRAP → DISC_D0 → DISC_D1 → DISC_D2 → DISC_D3 → DOMAIN_AUTHORING → DESIGN → PLAN → REVIEW
   discovery-start tiến wave (gate wave đang rời)      │                  │        │       │
   DISC_D3 → /discovery-end → DOMAIN                   │      /design↻ /design-ux↻  /plan   review/approve
   /domain-po·/domain-ba (author business, self-loop) ─┘            /design-end
   → /domain-approve (ký) → /domain-translate (dịch eng) → /domain-end
```
**Back-half** (wave execution):
```
REVIEW → WAVE_OPEN → DEV → REVIEW_DEV → DEV_HANDOFF → TEST_PLAN → TEST_EXECUTE → (auto) MANUAL_TEST → DONE → BOOTSTRAP
 start-wave  start-dev↻      ↑ fix Mode B loop                                    ↑ fix-bugs/log-bug↻      │
                                                              DONE → DOMAIN_AUTHORING (apply-cr: po/ba → ký → translate)
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

> **SoT = `scripts/gates.py` `GATE_RULES`** — bảng dưới là bản tóm tắt đọc-cho-người; lệch → GATE_RULES thắng. Mọi content-gate force-bypass được (`force:true,reason` → audit `tracking/decisions.md`).

| Command | Gate chính (gates.py) |
|---------|----------------------|
| `discovery-start` | `wave` non-empty (D0..D3) + `discovery_advance` (nhảy tiến → gate wave đang rời; refine/first-entry miễn) |
| `discovery-end` | `discovery_wave` — `discovery_gate.py D3` check artifact disk |
| `domain-po` / `domain-ba` | `mode` non-empty (EPIC/FEATURE/JOURNEY · BR/PERSONA) |
| `domain-approve` | `domain_no_jargon` (business doc plain nghiệp vụ mới ký được) + `domain_stamped` (file target phải ĐÃ `status: APPROVED` trên disk — chứng minh domain_approve.py đã chạy, chặn complete chay) |
| `domain-translate` | `domain_signed` — MỌI business doc docs/domain/ đã `status: APPROVED` (ký TRƯỚC dịch SAU) |
| `domain-end` | `domain_gate` (≥1 eng epic+feat+BR) + `planning_lint` (field bắt buộc + ref-integrity) + `translation_parity` (business đã ký ↔ eng doc 1-1 qua `source`/`domain_source_id`; eng epics/feat/BR không nguồn = mồ côi) |
| `design` | (self-loop refine hệ thống/contract — solution-architect. KHÔNG gate, KHÔNG advance) |
| `design-ux` | (self-loop — ux-designer-agent, skill ux-design; thiết kế theo TỪNG MÀN: **SCREEN-MAP.md** (màn↔boundary↔FEAT↔mockup) + **mockup HTML tĩnh per màn** `ux/mockups/{b}/{screen}.html` + ux-*.md + design-tokens.css. KHÔNG gate, KHÔNG advance) |
| `design-end` | `design_gate` (ADR≥3 + INTEG≥1 + per-boundary completeness: backend/bff→hld+api, web/mobile→hld+ux + design-tokens.css khi có web + **SCREEN-MAP parse từng row: mockup tồn tại + dùng token, web boundary 0 màn = chặn, màn trace FEAT ma = chặn, FEAT has_ui_touchpoint 0 màn = chặn**) + `todo_resolved` (marker `TODO engineer`/`TBD (DESIGN)` trong eng feat/BR đã điền hết) |
| `plan` | `plan_gate` (WAVE-SEQUENCE + MATRIX + wave-*.md + KG) + `planning_lint` + `plan_integrity` (FEAT-id MATRIX có file + **FEAT mồ côi**: FEAT-*.md phải vào features[] boundary nào đó + depends_on no-cycle) + `matrix_coherence` (MATRIX phủ đủ BOUNDARY-MAP đúng kind) + `api_transport` (tenant-id qua header/JWT, không query) + `wave_sequence_lint` (§wave-NNN enum/cap/purity) + `contract_graph_parity` (api consumers[]/INTEG/events subscribers ↔ MATRIX depends_on 2 chiều) |
| `review-document` | `feedback_processed: true` (revision mode; no-arg = sanity-check ghi doc-review-findings.md) |
| `approve-document` | `doc_review` (sanity-check đã chạy + không gap BLOCKER/MAJOR open) + `doc_stamped` (doc design/contract phải ĐÃ stamp APPROVED/ACTIVE bởi `approve_document.py` — chặn approve chay) + `approved: true` |
| `start-wave` | `approved: true` + `wave_n ≥ 1` + MATRIX tồn tại + `wave_in_matrix` (wave có boundary) |
| `start-dev` | `boundary` ∈ `wave_boundaries` |
| `review-dev` | `review_results` non-empty (chống complete `{}` làm STATE rỗng) + `no_open_findings` (review-findings.md hết row BLOCKER/MAJOR open) |
| `dev-handoff` | `all_boundaries_reviewed` (mọi wave boundary pass + coverage BE80/BFF70/web·mobile60 — **harness derive từ coverage report thật** khi service đã scaffold, không tin số tự khai) + `infra_proof` (docker-ps.json: State=running content-validated) + `health_proof` (health-proof.json HARNESS curl /health/ready 2xx) + `code_compliance` (backend: cấm H2/create-drop, bắt Dockerfile + base config + ≥1 profile) + `web_styling` (FE có styling thật; plain-CSS dùng `var(--...)` VÀ token được định nghĩa/import trong bundle) + `api_contract_proof` (endpoint khai api-{b}.md tồn tại trong runtime OpenAPI — api-proof.json) |
| `test-plan` | `docker_compose_ok` + `connectivity_ok` + `infra_proof` + `health_proof` (stack còn UP) + `contract_test_present` (consumer có depends_on → ≥1 TC contract/integration/e2e) + `journey_e2e_present` (chuỗi depends_on ≥3 boundary → ≥1 TC e2e/integration span cả chuỗi; API-driven, không đợi FE) + `ui_test_present` (mỗi web boundary ≥1 auto-TC UI in-scope) + `registry_scope` (TC chỉ trace FEAT ≤ wave hiện tại; deferred phải tag) + `ac_coverage` (FEAT.AC ↔ TC 2 chiều: AC mồ côi + TC stale) |
| `test-execute` | `test_cases_count ≥ 1` + `test_evidence` (report+log+bugs+screenshots+health-proof: network-call thật cho group mạng; skip phải service-down thật + không mâu thuẫn health-proof; TC web boundary phải có screenshot PNG thật; FAIL phải có bug ref; harness DERIVE test_result từ report) |
| `_auto` (TEST_EXECUTE → MANUAL_TEST) | `test_result` (any — pass HAY fail) |
| `log-bug` | `bug_id` non-empty (log-bug-agent trả về sau khi append row) |
| `fix-bugs` | `bug_id` non-empty (đơn lẻ); sweep no-arg = MAIN orchestrate, complete per-bug |
| `end-wave` | `uat_signed: true` + `test_result: pass` (STATE — harness derive từ report, ép re-run sau fix) + `no_open_bugs` (parse `tracking/wave-{N}/bugs.md`) + `features_complete` (derive feature-state: KHÔNG in-scope feat nào `active`/làm-dở — WIP=1 ship-gate L07; chỉ chặn active, không chặn not_started) |
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
| PreToolUse | Write\|Edit\|MultiEdit\|NotebookEdit | Block 4 kernel files (STATE.json, STATE-MACHINE.json, SERVICE-BOUNDARY-MATRIX.json, settings.json) + **3 proof file harness-đo** (`tracking/*/{docker-ps,health-proof,api-proof}.json` — chỉ capture_infra_proof.py được sinh, FM-PROOF-FORGE) + **phase-lock doc upstream** (doc lớp discovery/domain/design/plan chỉ sửa ở stage sở hữu +REVIEW; ngoại lệ dual-owner: eng `feat/business-rules` sửa được ở cả DOMAIN + DESIGN — DESIGN điền field kỹ thuật `todo_resolved`) + block `services/**` khi spawn.active=dev-handoff-agent |
| PreToolUse | Task | KHÔNG block theo stage (Explore free); inject boundary reminder + block spawn MỌI command-agent bằng prompt tự viết tay (E-6: keyword + tên-agent registry; thiếu chữ ký `# SPAWN PROMPT`/`STATE BUNDLE` = block) |
| PreToolUse | Skill\|SlashCommand | Chặn **CHỈ `SlashCommand`** tool chạy harness cmd ∈ GATE_RULES (MAIN tự nối pipeline). **`Skill` tool cho qua LUÔN** (sub-agent load convention skill — kể cả tên trùng command; Skill không transition state) |
| PostToolUse | Bash | no-op (STATE.json chỉ giữ trạng thái hiện tại) |
| SubagentStop | * | Parse RETURN SCHEMA, validate 7 field bắt buộc |
| Stop | * | Build/lint/test **wave-scoped** per kind khi stage ∈ {DEV, REVIEW_DEV, TEST_EXECUTE} + có sửa services/; đỏ→block 40 dòng cuối; cache git-hash |
| SessionEnd | * | Cleanup spawn.active nếu stale |

Hook policies pure functions in `scripts/hooks/policies.py`. Dispatcher routes events to handlers. Fail-open: hook crash → allow tool call.

### Turn-flag (#11) — chống MAIN tự nối lệnh

File cờ `harness/.turn-advance.flag` mở **đúng 1 lượt** cho **1 `harness <cmd> complete`** mỗi user-turn:

- **Reset** ở `UserPromptSubmit` + `SessionStart` (mỗi prompt người dùng mở lại 1 cờ).
- **Tiêu cờ** khi 1 `harness complete` PASS gate → `complete` thứ 2 cùng turn bị `PreToolUse(Bash)` deny (`"MAIN tự nối lệnh"`). Buộc MAIN dừng, báo kết quả, chờ user gõ lệnh kế.
- **Gate-fail KHÔNG tiêu cờ** — cho phép retry cùng lệnh trong turn.
- **Vá lỗ hổng:** `PreToolUse(SlashCommand)` chặn MAIN tự chạy slash-command ∈ `GATE_RULES` (nếu không, invoke sẽ fire lại `UserPromptSubmit` → reset cờ → lệnh kế lọt). User **gõ tay** slash-command = pre-loaded, MAIN không gọi tool → không ảnh hưởng. **`Skill` tool KHÔNG chặn** — sub-agent CẦN load skill convention của chính nó (domain-po/test-plan/ux-design…); Skill không transition state nên không phải vector tự-nối-lệnh.
- **#12 dev-handoff infra-only:** `_pre_task` set `spawn.active=dev-handoff-agent` → `PreToolUse(Write|Edit)` block sửa `services/**` (lỗi code boundary → fix-agent, dev-handoff KHÔNG tự vá).

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
