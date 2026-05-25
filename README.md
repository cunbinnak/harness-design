# ADLC Design — Harness Engineering

Khung repo áp dụng **Harness** (lớp điều phối **ngoài model**) cho phát triển sản phẩm theo wave, state ADLC, và boundary/service **materialize khi chạy**.

→ Framework là **template tái sử dụng** — fork repo, chạy `/intake-requirement`, framework tự sinh agents/docs/plans cho project mới.

## Cấu trúc

```
docs/architecture/         # PROJECT.md, feat/, adr/, hld/, api/, data-model/, ux/, infra/, integrations-matrix.md
docs/plans/                # project/{waves-roadmap, agent-roster}, waves/{id}/wave.md
harness/                   # 7 JSON configs
  STATE.json
  STATE-MACHINE.json       # 13 states (BOOTSTRAP -> ... -> MANUAL_TEST -> BOOTSTRAP)
  COMMAND-GATES.json       # 15 commands + gates
  HOOK-RULES.json          # hooks + evidence schemas
  AGENT-DISCIPLINE.json    # rules + agent_roles (central doc-scope registry)
  PIPELINES.json           # intake (4 steps) + apply-cr pipelines
  SERVICE-BOUNDARY-MATRIX.json
agents/                    # 15 core agents + materialized boundary agents
  _template.agent.md       # template cho boundary materialization
  intake-orchestrator-agent.md
  {requirement,business,solution,program}-*-agent.md
  apply-cr-agent.md, start-wave-agent.md, review-document-agent.md
  dev-handoff-agent.md, test-{plan,execute}-agent.md
  release-agent.md, end-wave-agent.md, done-wave-agent.md, reviewer-agent.md
skills/                    # 13 skills (folder-per-skill structure)
  <name>/SKILL.md
commands/                  # slash commands + manifest.yaml
handoff/                   # TEMPLATE.wave.md + {wave-id}.md
tracking/                  # per-wave structure
  change-requests/         # cross-wave (root)
  waves/{wave-id}/         # test-cases, test-results, manual-test-log, release-notes, bugs/
knowledge-base/            # shared.yaml + {boundary}.knowledge-graph.yaml
scripts/                   # harness.py + materialize.py + reset_for_new_project.py + hooks/
services/                  # code (materialized per boundary)
.cursor/rules/             # agent discipline (alwaysApply)
```

## Harness làm gì?

| Trách nhiệm | Nơi lưu |
|-------------|---------|
| State hiện tại | `harness/STATE.json` (audit trail trong `checkpoints[]`) |
| Stage / transitions | `harness/STATE-MACHINE.json` |
| Command gates + sequence | `harness/COMMAND-GATES.json` |
| Hooks (pre/post checks) | `harness/HOOK-RULES.json` + `scripts/hooks/` |
| **Agent doc-scope** | `harness/AGENT-DISCIPLINE.json[agent_roles]` (central registry) |
| Pipeline multi-step | `harness/PIPELINES.json` |
| Boundary / ownership | `harness/SERVICE-BOUNDARY-MATRIX.json` (auto-sync từ roster) |
| Shared memory (KG) | `knowledge-base/*.knowledge-graph.yaml` |
| Spec sản phẩm | `docs/architecture/`, `docs/plans/` |
| Wave artifacts | `tracking/waves/{wave-id}/` + `handoff/{wave-id}.md` |

**Doc scope mỗi agent** = role trong frontmatter → lookup registry → `build_command_prompt.py` auto-inject **DOCS IN SCOPE**. BE chỉ đọc HLD/API/data-model của boundary mình, FE chỉ đọc UX + API contracts, test không đọc source code.

---

## Setup cho project mới

```bash
pip install -r requirements-harness.txt

# Preview
py scripts/reset_for_new_project.py --dry-run

# Reset starter (xóa artifacts project cũ, đặt tên mới)
py scripts/reset_for_new_project.py --confirm \
    --project-id my-new-app \
    --display-name "My New App"

py scripts/harness.py state   # stage = BOOTSTRAP, allowed_next = [intake-requirement]
```

---

## Quy trình command (16 commands)

Mỗi command: `/build_command_prompt.py <cmd>` (spawn agent) + `/harness.py <cmd> complete` (gate + transition).
Luôn check `py scripts/harness.py state` để xem `workflow.allowed_next`. **KHÔNG** sửa `STATE.json` tay.

### Flow chuẩn (1 wave từ đầu đến cuối)

| # | Slash | Stage sau | Việc | Ví dụ `complete` |
|---|-------|-----------|------|------------------|
| 1 | `/intake-requirement` (x4 step) | IMPLEMENTATION_PLAN | Phân tích -> PROJECT, FEAT, ADR, HLD, API, UX, plans, roster, agents, KGs | `... intake-requirement complete '{}'` |
| 2 | `/review-document` | IMPLEMENTATION_PLAN | Gate review tài liệu | `'{"approved": true}'` |
| 3 | `/start-wave` | IMPLEMENTATION_PLAN | Mở wave + load roster + sync matrix | `'{"wave_id":"1","wave_title":"MVP"}'` |
| 4 | `/start-dev --boundary X` | IMPLEMENTATION | Dev BE / FE từng boundary | `'{"features_in_flight":["FEAT-001"],"boundaries_in_flight":["order"]}'` |
| 5 | `/review-dev --boundary X` | SELF_REVIEW | Self-review code + coverage | `'{}'` |
| 6 | `/dev-handoff` | SPECIALIST_TESTING | Bàn giao dev -> QA (BE>=80%, FE>=60%) | `'{"coverage_pct":85,"coverage_fe_pct":65,"handoff_ready":true}'` |
| 7 | `/test-plan` | SPECIALIST_TESTING | Tạo `tracking/waves/{wave}/test-cases.md` | `'{}'` |
| 8 | `/test-execute` | RELEASE_CANDIDATE (pass) / BUG_LOGGING (fail) | Auto test + smoke + integration + teardown | `'{"test_result":"pass"}'` |
| 9 | `/release` | DONE | Tạo `tracking/waves/{wave}/release-notes.md` | `'{"release_ok": true}'` |
| 10 | `/end-wave` (**soft**) | **MANUAL_TEST** | Ship UAT - giữ infra UP, tạo manual-test-log | `'{"end_wave_ok": true}'` |
| 11 | `/done-wave` (**hard**) | BOOTSTRAP | Teardown + reset STATE cho wave kế tiếp | `'{"done_wave_ok": true}'` |

### Test fail / Manual test fail

```bash
/fix-bugs --boundary X    # Stage: BUG_LOGGING -> FIX_MANUAL_BUGS
/retest                   # Smart routing: pass_auto -> SPECIALIST_TESTING; pass_manual -> MANUAL_TEST
```

Bug ticket format `tracking/waves/{wave-id}/bugs/BUG-{n}-*.md` với frontmatter `origin: auto | manual` — `retest` đọc để route đúng.

### Khác

| Slash | Khi nào |
|-------|---------|
| `/show-state` | Xem stage + `allowed_next` |
| `/apply-cr` | Thay đổi scope giữa chừng -> kéo `/intake-requirement` (amendment) -> `/review-document` |
| `/register-boundary` | Thêm boundary ngoài roster |

---

## State-machine

```
BOOTSTRAP
  | start_wave
REQUIREMENT_INTAKE -> BUSINESS_ANALYSIS -> TECHNICAL_DESIGN -> IMPLEMENTATION_PLAN
  | advance
IMPLEMENTATION -> SELF_REVIEW -> SPECIALIST_TESTING
                                    |
                         tests_pass | tests_fail
                                    v        v
                             RELEASE_CANDIDATE     BUG_LOGGING -> FIX_MANUAL_BUGS
                                    | release_ok                       | retest_auto/retest_manual
                                    v                                  ^
                                  DONE                                 |
                                    | end_wave_ok                      |
                                    v                                  |
                                MANUAL_TEST <----- retest_manual ------+
                                    |                  ^
                         bug_logged | reset_wave       | advance (fix-bugs)
                                    v   (done-wave)    |
                                BUG_LOGGING ---------> FIX_MANUAL_BUGS
                                    v
                                BOOTSTRAP (wave kế tiếp)
```

---

## Wave kế tiếp

| Tình huống | Bắt đầu bằng |
|------------|--------------|
| Wave kế tiếp đã plan, không đổi scope | `/start-wave` với `wave_id` mới (vd `"2"` -> `wave-002`) |
| Có thay đổi nghiệp vụ / CR | `/apply-cr` -> `/intake-requirement` (amendment) -> `/review-document` -> `/start-wave` |

---

## Tài liệu tham chiếu

| File | Mục đích |
|------|----------|
| [`SETUP-GUIDE.md`](SETUP-GUIDE.md) | Setup + workflow đầy đủ |
| [`agents/README.md`](agents/README.md) | Danh sách agent + bảng role->docs |
| [`commands/README.md`](commands/README.md) | Từng command |
| [`harness/PROTOCOL.md`](harness/PROTOCOL.md) | Spawn protocol, RETURN SCHEMA |
| [`harness/AGENT-DISCIPLINE.json`](harness/AGENT-DISCIPLINE.json) | Rules + **agent_roles registry** (doc-scope) |
| [`harness/COMMAND-GATES.json`](harness/COMMAND-GATES.json) | Điều kiện chuyển bước |
| [`harness/STATE-MACHINE.json`](harness/STATE-MACHINE.json) | States + transitions |
| [`knowledge-base/README.md`](knowledge-base/README.md) | Shared memory (KG) |
| [`.cursor/rules/harness-agent-discipline.mdc`](.cursor/rules/harness-agent-discipline.mdc) | Rule + KG discipline |
| [`requirements-harness.txt`](requirements-harness.txt) | `pip install -r requirements-harness.txt` |

### Materialize scripts (dispatcher)

```bash
py scripts/materialize.py boundary-agents --from-roster docs/plans/project/agent-roster.md
py scripts/materialize.py knowledge-graphs --from-roster docs/plans/project/agent-roster.md
py scripts/materialize.py ux               --boundaries fe-web,fe-admin
py scripts/materialize.py wave-plans       --from-roadmap docs/plans/project/waves-roadmap.md
```

### Đăng ký boundary mới (runtime)

```bash
py scripts/harness.py register-boundary catalog-api --materialize
```
