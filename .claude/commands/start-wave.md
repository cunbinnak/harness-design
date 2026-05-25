---
description: "Harness command: start-wave"
argument-hint: "[wave-id]"
---

# /start-wave [wave-id]

Mở **một** wave — sau `review-document` (lần đầu) hoặc sau `end-wave` (wave tiếp, không đổi scope).

**Agent:** [start-wave-agent.md](../agents/start-wave-agent.md)

## `wave_id` (linh hoạt)

| Bạn nhập | Chuẩn hóa thành |
|----------|-----------------|
| `2`, `02` | `wave-002` |
| `wave-2` | `wave-002` |
| `wave-002` | `wave-002` |

```bash
py scripts/build_command_prompt.py start-wave --wave 2
py scripts/harness.py start-wave complete '{"wave_id": "2", "wave_title": "Phase 2"}'
```

Roster chỉ nạp boundaries có `waves_participating` chứa wave này.

Guide: [SETUP-GUIDE.md](../SETUP-GUIDE.md)