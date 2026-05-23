# ADLC Design — Harness Engineering

Khung repo áp dụng **Harness** (lớp điều phối **ngoài model**) cho phát triển sản phẩm theo wave, state ADLC, và boundary/service **materialize khi chạy**.

## Cấu trúc (cố định)

```
AGENTS.md
docs/product/          # PROJECT.md + FEAT-*
docs/architecture/     # hld/, api/, data-model/, ux/ per boundary
docs/plans/            # project/ + waves/{id}/wave.md
harness/
  STATE.json
  STATE-MACHINE.json
  PROTOCOL.md
  CONTEXT-RULES.json
  SERVICE-BOUNDARY-MATRIX.json
  FAILURE-MODES.md
  hooks/
agents/
skills/
commands/              # lệnh (manifest + .md)
handoff/
tracking/
knowledge-base/
scripts/
services/
```

## Harness làm gì?

| Trách nhiệm | Nơi lưu |
|-------------|---------|
| Agent nào, chạy khi nào | `STATE-MACHINE.json`, `agents/`, `STATE.json` |
| Input/output | `PROTOCOL.md` (RETURN SCHEMA) |
| State hiện tại | `STATE.json` |
| **Shared memory** | **`knowledge-base/*.knowledge-graph.yaml`** (domain, backlog, **decisions**, learnings) |
| Boundary / quyền sửa | `SERVICE-BOUNDARY-MATRIX.json`, `hooks/` |
| Spec sản phẩm | `docs/` |
| Handoff / bug / test | `handoff/`, `tracking/` |

**Làm ở đâu** = `boundary_id` trong **SERVICE-BOUNDARY-MATRIX.json**, **không** suy từ folder `services/` có sẵn lúc BOOTSTRAP.

---

## Hướng dẫn sử dụng (quy trình)

### 0. BOOTSTRAP (ban đầu)

- Mở `harness/STATE.json`: `stage` = `BOOTSTRAP`, wave/features/context **trống**.
- `SERVICE-BOUNDARY-MATRIX.json`: `boundaries: []`.
- Chỉ có `knowledge-base/shared.knowledge-graph.yaml` (shared memory trống).

```bash
python scripts/state_engine.py validate
python scripts/state_engine.py show
```

### Quy trình command

Xem [`HUONG-DAN-SETUP.md`](HUONG-DAN-SETUP.md). Tóm tắt:

```bash
python scripts/harness.py intake-requirement complete
python scripts/harness.py review-document complete '{"approved": true}'
python scripts/harness.py start-wave complete '{"wave_title": "Wave 1"}'
python scripts/harness.py start-dev complete '{"features_in_flight":["FEAT-001"],"boundaries_in_flight":["order"]}'
python scripts/harness.py dev-handoff complete '{"coverage_pct": 85, "handoff_ready": true}'
python scripts/harness.py test-execute complete '{"test_result": "pass"}'
python scripts/harness.py release complete '{"release_ok": true}'
python scripts/harness.py end-wave complete '{"end_wave_ok": true}'
python scripts/harness.py state
```

Gates: [`harness/COMMAND-GATES.json`](harness/COMMAND-GATES.json).

---

## Tài liệu tham chiếu

| File | Mục đích |
|------|----------|
| [`AGENTS.md`](AGENTS.md) | Map command ↔ agent |
| [`agents/README.md`](agents/README.md) | Danh sách agent |
| [`harness/PROTOCOL.md`](harness/PROTOCOL.md) | Spawn, RETURN SCHEMA, pass/fail |
| [`knowledge-base/README.md`](knowledge-base/README.md) | Shared memory + decisions |
| [`HUONG-DAN-SETUP.md`](HUONG-DAN-SETUP.md) | Setup + command workflow |
| [`harness/COMMAND-GATES.json`](harness/COMMAND-GATES.json) | Điều kiện chuyển bước |
| [`commands/`](commands/) | Khung command + manifest |
| [`requirements-harness.txt`](requirements-harness.txt) | `pip install -r requirements-harness.txt` (PyYAML) |

### Đăng ký boundary (runtime)

```bash
python scripts/harness.py register-boundary catalog-api --materialize
```
