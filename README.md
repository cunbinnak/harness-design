# ADLC Design — Harness Engineering

Khung repo áp dụng **Harness** (lớp điều phối **ngoài model**) cho phát triển sản phẩm theo wave, state ADLC, và boundary/service **materialize khi chạy**.

## Cấu trúc (cố định)

```
AGENTS.md
docs/product/          # PROJECT.md + FEAT-*
docs/architecture/     # adr/, hld/, api/, data-model/, ux/, infra/
docs/plans/            # project/ + waves/{id}/wave.md
harness/
  STATE.json
  STATE-MACHINE.json
  PROTOCOL.md
  COMMAND-GATES.json
  SERVICE-BOUNDARY-MATRIX.json
agents/
skills/
commands/              # manifest + .md
handoff/
tracking/
knowledge-base/
scripts/
services/
.cursor/rules/         # agent discipline (alwaysApply)
```

## Harness làm gì?

| Trách nhiệm | Nơi lưu |
|-------------|---------|
| Agent nào, chạy khi nào | `STATE-MACHINE.json`, `agents/`, `STATE.json` |
| Input/output | `PROTOCOL.md` (RETURN SCHEMA) |
| State hiện tại | `STATE.json` |
| Shared memory | `knowledge-base/*.knowledge-graph.yaml` |
| Boundary / quyền sửa | `SERVICE-BOUNDARY-MATRIX.json`, `scripts/hooks/` |
| Spec sản phẩm | `docs/` |
| Handoff / bug / test | `handoff/`, `tracking/` |

**Làm ở đâu** = `boundary_id` trong **SERVICE-BOUNDARY-MATRIX.json**, **không** suy từ folder `services/` lúc BOOTSTRAP.

---

## Hướng dẫn sử dụng (quy trình)

### 0. BOOTSTRAP (ban đầu)

- `harness/STATE.json`: `stage` = `BOOTSTRAP`, wave/features/context trống.
- `SERVICE-BOUNDARY-MATRIX.json`: `boundaries: []`.
- `knowledge-base/shared.knowledge-graph.yaml` — shared memory trống.

```bash
pip install -r requirements-harness.txt
py scripts/state_engine.py validate
py scripts/harness.py state
```

### Quy trình command

Trong **Cursor / Claude**: gọi slash command (mở `commands/<tên>.md`) → chạy agent theo prompt → khi artifact đạt gate thì **complete**:

```bash
py scripts/harness.py <command> complete
py scripts/harness.py <command> complete '<json evidence>'   # nếu gate yêu cầu
```

Luôn xem bước được phép: `/show-state` hoặc `py scripts/harness.py state` (`workflow.allowed_next`). **Không** sửa `harness/STATE.json` tay.

| Thứ tự | Slash | Việc cần làm | Ví dụ `complete` |
|--------|--------|----------------|------------------|
| 1 | `/intake-requirement` | Phân tích dự án, plan mọi wave, roster, agents (4 bước pipeline) | `py scripts/harness.py intake-requirement complete` |
| 2 | `/review-document` | Duyệt bộ tài liệu plan | `… review-document complete '{"approved": true}'` |
| 3 | `/start-wave` | Mở một wave; sync matrix từ roster | `… start-wave complete '{"wave_id":"1","wave_title":"Wave 1"}'` |
| 4 | `/start-dev` | Dev theo boundary (`--boundary` trong prompt) | `… start-dev complete '{"features_in_flight":["FEAT-001"],"boundaries_in_flight":["order"]}'` |
| 5 | `/review-dev` | Self-review code boundary | `… review-dev complete` |
| 6 | `/dev-handoff` | Bàn giao dev → QA (coverage, compose) | `… dev-handoff complete '{"coverage_pct":85,"handoff_ready":true}'` |
| 7 | `/test-plan` | Viết test case registry | `… test-plan complete` |
| 8 | `/test-execute` | Chạy test | `… test-execute complete '{"test_result":"pass"}'` |
| 9 | `/release` | Release candidate | `… release complete '{"release_ok": true}'` |
| 10 | `/end-wave` | Đóng wave | `… end-wave complete '{"end_wave_ok": true}'` |
| — | `/show-state` | Xem stage + `allowed_next` | `py scripts/harness.py state` |

**Ví dụ intake (bước 1):**

```bash
/intake-requirement
py scripts/build_command_prompt.py intake-requirement --step 1 --input "CRM cho SME, 3 wave..."
# --step 2, 3, 4 ...
py scripts/harness.py intake-requirement complete
```

**Wave tiếp theo** (plan đã có, không đổi scope): bỏ `/intake-requirement` và `/review-document`, bắt đầu từ `/start-wave` với `wave_id` mới (vd. `"2"` → `wave-002`).

**Test fail:** `/fix-bugs` → `/retest` (thay vì `/release`).

**Đổi scope:** `/apply-cr` → `/intake-requirement` (amendment) → `/review-document` — chi tiết [commands/apply-cr.md](commands/apply-cr.md).

Chi tiết gate & hooks: [SETUP-GUIDE.md](SETUP-GUIDE.md) · [commands/README.md](commands/README.md).

---

## Tài liệu tham chiếu

| File | Mục đích |
|------|----------|
| [`SETUP-GUIDE.md`](SETUP-GUIDE.md) | Setup + workflow đầy đủ |
| [`AGENTS.md`](AGENTS.md) | Map command ↔ agent |
| [`agents/README.md`](agents/README.md) | Danh sách agent |
| [`commands/README.md`](commands/README.md) | Từng command |
| [`harness/PROTOCOL.md`](harness/PROTOCOL.md) | Spawn, RETURN SCHEMA |
| [`knowledge-base/README.md`](knowledge-base/README.md) | Shared memory |
| [`.cursor/rules/harness-agent-discipline.mdc`](.cursor/rules/harness-agent-discipline.mdc) | Rule + KG discipline |
| [`harness/COMMAND-GATES.json`](harness/COMMAND-GATES.json) | Điều kiện chuyển bước |
| [`requirements-harness.txt`](requirements-harness.txt) | `pip install -r requirements-harness.txt` |

### Đăng ký boundary (runtime)

```bash
py scripts/harness.py register-boundary catalog-api --materialize
```
