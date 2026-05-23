# Hướng dẫn setup & sử dụng Harness

## 1. Cài đặt

```bash
pip install -r requirements-harness.txt
python scripts/harness.py state
```

Kết quả mong đợi: `workflow.allowed_next: ["start-wave"]`.

### Bắt đầu wave

```bash
python scripts/harness.py start-wave complete '{"wave_title": "Wave 1"}'
```

### Intake & start wave

**Plan trước** (intake 4 bước) → tạo `order-agent.md`, `fix-order-agent.md`, `review-order-agent.md`, …

```bash
python scripts/build_command_prompt.py intake-requirement --step 1 --input "..."
python scripts/materialize_boundary_agents.py --boundaries order,product --wave wave-001
python scripts/harness.py intake-requirement complete
```

**Mở wave** — nạp FEAT + boundaries vào STATE:

```bash
python scripts/build_command_prompt.py start-wave
python scripts/harness.py start-wave complete '{"wave_title": "Wave 1"}'
python scripts/build_command_prompt.py start-dev --boundary order
```

---

## 2. Luồng command (người dùng)

Mỗi bước: orchestrator chạy agent (sau này) → tạo artifact → **`complete`** với evidence JSON.

```text
start-wave → intake-requirement → review-document → register-boundary
  → prepare-dev → start-dev → review-dev → dev-handoff → test-plan → test-execute
  → (fail) fix-bugs → retest → …
  → (pass) release → end-wave
```

Chi tiết gate: [`harness/COMMAND-GATES.json`](harness/COMMAND-GATES.json).

---

## 3. Lệnh CLI

### Kiểm tra trước khi complete

```bash
python scripts/harness.py can intake-requirement
python scripts/harness.py intake-requirement can
```

### Hoàn thành bước (evidence JSON trên CLI)

Evidence = object JSON truyền khi `complete` (không cần thư mục riêng trong repo).

```bash
py scripts/harness.py intake-requirement complete

py scripts/harness.py review-document complete '{"approved": true}'

py scripts/harness.py dev-handoff complete '{"coverage_pct": 85, "handoff_ready": true}'

py scripts/harness.py test-execute complete '{"test_result": "pass"}'

py scripts/harness.py release complete '{"release_ok": true}'

py scripts/harness.py end-wave complete '{"end_wave_ok": true}'
```

### Xem state

```bash
python scripts/harness.py state
```

---

## 4. Artifact tối thiểu (gate)

| Command | File / điều kiện |
|---------|------------------|
| `intake-requirement` | `project/*`, FEAT, architecture, `waves/*/wave.md` §1, agents (chưa handoff) |
| `review-document` | `approved: true` |
| `start-wave` | plan đã có + `handoff/wave-*.md`, `STATE.wave.id` |
| `sync-boundaries` | `SERVICE-BOUNDARY-MATRIX.json` khớp roster |
| `prepare-dev` | cùng `waves/*/wave.md` §2 Assignment, evidence lists → STATE |
| `review-document` | `evidence.approved = true` |
| `register-boundary` | ≥1 row trong `SERVICE-BOUNDARY-MATRIX.json` |
| `dev-handoff` | `coverage_pct ≥ 80`, `handoff_ready = true` |
| `test-plan` | ≥1 file `tracking/test-case-registry/**` |
| `test-execute` | registry + `test_result` pass/fail |
| `fix-bugs` | ≥1 file `tracking/bugs/**` |
| `release` | test pass trước đó + `release_ok = true` |

---

## 5. Hooks

Rule: [`harness/HOOK-RULES.json`](harness/HOOK-RULES.json).

```bash
python scripts/hooks/run_hook.py transition_gate --payload '{"command":"dev-handoff","evidence":{"coverage_pct":85,"handoff_ready":true}}'
python scripts/hooks/run_hook.py owned_paths --payload '{"path":"docs/product/x.md"}'
python scripts/hooks/run_hook.py return_schema --payload '{"body":"{\"completed\":[],\"deferred\":[],\"needs_review\":[],\"files_changed\":[],\"build\":\"pass\",\"lint\":\"pass\",\"test\":\"pass\"}"}'
```

---

## 6. Trong chat (Cursor / Claude)

1. **Read** `commands/COMMAND-FRAMEWORK.md` + command cụ thể.
2. Chạy agent theo stage (triển khai sau).
3. Orchestrator gọi `harness.py … complete` với evidence.
4. Gate fail → sửa artifact, không chuyển bước.

Slash: file trong `commands/*.md` — đã sync sang `.cursor/commands/` và `.claude/commands/` (chạy lại `python scripts/sync_commands.py` khi sửa command).

---

## 7. Thư mục quan trọng

| Path | Vai trò |
|------|---------|
| `harness/STATE.json` | State + `workflow.allowed_next` |
| `harness/COMMAND-GATES.json` | Điều kiện chuyển bước |
| `harness/HOOK-RULES.json` | Rule hook |
| `commands/manifest.yaml` | Danh sách command |
| `scripts/harness.py` | CLI chính |

Xem thêm: [`README.md`](README.md), [`harness/PROTOCOL.md`](harness/PROTOCOL.md).
