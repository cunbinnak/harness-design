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

### Lần đầu (dự án / wave 1)

Intake 4 bước, spawn agent, artifact, CR: **[SETUP-GUIDE.md](SETUP-GUIDE.md)**.

```bash
py scripts/harness.py intake-requirement complete
py scripts/harness.py review-document complete '{"approved": true}'
py scripts/harness.py start-wave complete '{"wave_id": "1", "wave_title": "Wave 1"}'
py scripts/harness.py start-dev complete '{"features_in_flight":["FEAT-001"],"boundaries_in_flight":["order"]}'
py scripts/harness.py review-dev complete
py scripts/harness.py dev-handoff complete '{"coverage_pct": 85, "handoff_ready": true}'
py scripts/harness.py test-plan complete
py scripts/harness.py test-execute complete '{"test_result": "pass"}'
py scripts/harness.py release complete '{"release_ok": true}'
py scripts/harness.py end-wave complete '{"end_wave_ok": true}'
py scripts/harness.py state
```

### Wave tiếp theo (lần 2+, plan đã có — không intake lại)

Sau `end-wave`, đổi `wave_id` / evidence cho wave mới. Đổi scope → xem SETUP-GUIDE (`apply-cr`).

```bash
py scripts/harness.py start-wave complete '{"wave_id": "2", "wave_title": "Wave 2"}'
py scripts/harness.py start-dev complete '{"features_in_flight":["FEAT-001"],"boundaries_in_flight":["order"]}'
py scripts/harness.py review-dev complete
py scripts/harness.py dev-handoff complete '{"coverage_pct": 85, "handoff_ready": true}'
py scripts/harness.py test-plan complete
py scripts/harness.py test-execute complete '{"test_result": "pass"}'
py scripts/harness.py release complete '{"release_ok": true}'
py scripts/harness.py end-wave complete '{"end_wave_ok": true}'
py scripts/harness.py state
```

Gates: [`harness/COMMAND-GATES.json`](harness/COMMAND-GATES.json) · **Không** sửa `STATE.json` tay.

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
