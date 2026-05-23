# ADLC Design Harness

Khung **Harness** — lớp điều phối **ngoài model** — cho phát triển sản phẩm theo wave, state machine ADLC, boundary/service materialize lúc chạy, và shared memory (Knowledge Graph).

Orchestrator (bạn / IDE) chỉ được chạy command nằm trong `workflow.allowed_next`. Agent con tuân **rule discipline** + **KG**; hooks chặn sửa sai phạm vi và `harness complete` khi còn blocker.

---

## Bắt đầu nhanh

```bash
pip install -r requirements-harness.txt
py scripts/harness.py state          # xem stage + allowed_next
```

Ở **BOOTSTRAP**, `allowed_next` thường là `["intake-requirement"]`.

```bash
# Intake bước 1 (ví dụ)
py scripts/build_command_prompt.py intake-requirement --step 1 --input "Mô tả sản phẩm..."
# ... bước 2–4, materialize agents ...
py scripts/harness.py intake-requirement complete

py scripts/harness.py review-document complete '{"approved": true}'
py scripts/harness.py start-wave complete '{"wave_id": "1", "wave_title": "Wave 1"}'
```

**Không** sửa `harness/STATE.json` tay để nhảy bước.

Hướng dẫn đầy đủ: **[SETUP-GUIDE.md](SETUP-GUIDE.md)**

---

## Luồng workflow

```text
intake-requirement → review-document → start-wave [→ register-boundary?]
  → start-dev → review-dev → dev-handoff
  → test-plan → test-execute
  → (fail) fix-bugs → retest
  → (pass) release → end-wave

Đổi scope: apply-cr → intake-requirement (amendment) → review-document → start-dev | start-wave
```

Nguồn sự thật runtime: [`harness/COMMAND-GATES.json`](harness/COMMAND-GATES.json)  
Danh sách command: [`commands/README.md`](commands/README.md)

---

## Cấu trúc repo

```text
harness/                 STATE, gates, protocol, matrix, hook rules
agents/                  Spec agent (intake specialists + boundary dev + command agents)
commands/                Mô tả từng bước + manifest.yaml (sync slash IDE)
scripts/                 harness.py, gates, hooks, materialize, build_context
docs/                    Spec sản phẩm (product, architecture, plans)
knowledge-base/          Shared memory (decisions, discipline, implementation)
handoff/                 Bàn giao theo wave
tracking/                Bugs, test cases, change requests (CR)
services/                Code materialize theo boundary (sau start-dev)
.cursor/rules/           Agent discipline (alwaysApply)
```

Boundary và `owned_paths` lấy từ **`SERVICE-BOUNDARY-MATRIX.json`**, không đoán từ cây thư mục lúc BOOTSTRAP.

---

## CLI thường dùng

| Mục đích | Lệnh |
|----------|------|
| Trạng thái | `py scripts/harness.py state` |
| Có được chạy command? | `py scripts/harness.py can <command>` |
| Hoàn thành bước | `py scripts/harness.py <command> complete` |
| Evidence (JSON) | `py scripts/harness.py start-dev complete '{"features_in_flight":["FEAT-001"],"boundaries_in_flight":["order"]}'` |
| Prompt agent | `py scripts/build_command_prompt.py <command> [--step N] [--boundary id] [--wave 2]` |
| Sync slash commands | `py scripts/sync_commands.py` |
| Ghi KG | `py scripts/knowledge_writer.py decision …` / `do-not-repeat` / `blocker` |

Đăng ký boundary thêm (tùy chọn):

```bash
py scripts/harness.py register-boundary <boundary-id> --materialize
```

---

## Discipline, KG và hooks

| Thành phần | Vai trò |
|------------|---------|
| [`.cursor/rules/harness-agent-discipline.mdc`](.cursor/rules/harness-agent-discipline.mdc) | Rule chung — đọc/ghi KG mỗi lượt |
| [`knowledge-base/shared.knowledge-graph.yaml`](knowledge-base/shared.knowledge-graph.yaml) | `discipline.blockers`, `do_not_repeat`, `decisions`, `implementation.*` |
| [`harness/HOOK-RULES.json`](harness/HOOK-RULES.json) | Cấu hình hook |
| [`scripts/hooks/`](scripts/hooks/) | `owned_paths`, gates trên shell, `discipline_blockers`, `discipline_kg_return` |

Vi phạm → **HARNESS — KHÔNG ĐƯỢC PHÉP** (IDE `failClosed: true`).

---

## Tài liệu theo vai

| Đọc khi | File |
|---------|------|
| Setup & gate checklist | [SETUP-GUIDE.md](SETUP-GUIDE.md) |
| Spawn / RETURN JSON | [harness/PROTOCOL.md](harness/PROTOCOL.md) |
| Map command ↔ agent | [AGENTS.md](AGENTS.md) · [agents/README.md](agents/README.md) |
| Shared memory | [knowledge-base/README.md](knowledge-base/README.md) |
| Change request | [commands/apply-cr.md](commands/apply-cr.md) · [tracking/change-requests/TEMPLATE.cr.md](tracking/change-requests/TEMPLATE.cr.md) |
| Hooks (chi tiết) | [scripts/hooks/README.md](scripts/hooks/README.md) |

---

## Yêu cầu

- Python 3.10+ (`py` trên Windows)
- PyYAML: `pip install -r requirements-harness.txt`
- Cursor / Claude: bật project hooks (`.cursor/hooks.json`)
