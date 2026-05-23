---
agent_id: start-wave
command: start-wave
kind: harness-command
knowledge_graph: knowledge-base/shared.knowledge-graph.yaml
skills:
  - implementation
---

# Start Wave Agent

## Ai (Identity)

**Mở một wave** — sau intake + review; không viết lại toàn bộ plan dự án.

| | |
|---|---|
| **Command** | `start-wave` |
| **Spawn** | `build_command_prompt.py start-wave --wave <wave-id>` |

## Đầu vào (evidence khi complete)

```json
{
  "wave_id": "wave-001",
  "wave_title": "MVP"
}
```

| Field | Ý nghĩa |
|-------|---------|
| `wave_id` | Wave cần mở (`wave-001`, `wave-002`, …) — phải có `docs/plans/waves/{wave_id}/wave.md` từ intake |
| `wave_title` | Tên hiển thị trong `STATE.wave.title` |

Mặc định nếu thiếu: `wave_id` = `wave-001`.

## Phải làm

1. Xác nhận `docs/plans/waves/{wave_id}/wave.md` khớp wave đang mở.
2. Tạo/cập nhật `handoff/wave-{suffix}.md`.
3. Orchestrator `complete` với evidence trên → harness nạp roster + sync matrix.

## Không được

- Mở wave chưa có plan file
- `start-wave` trước `review-document` approved
