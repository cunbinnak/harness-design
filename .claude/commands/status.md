---
name: status
description: "Đang ở đâu, gate còn thiếu gì, chốt kế là gì. Chạy được ở mọi stage — không đổi stage, không gate."
argument-hint: "(không arg)"
when_state: "*"
allowed-tools: Bash, Read
---

# /status

Chạy được ở **mọi stage**. Không đổi gì, không tiêu gate.

```bash
py scripts/harness.py state
```

In ra: `stage` · `wave` · `active_boundary` · `wave_boundaries` · `allowed_commands` · `last_completed`.

Đọc thêm khi cần trả lời *"còn thiếu gì để đi tiếp"*:

| Câu hỏi | Ở đâu |
|---|---|
| Gate D-wave còn thiếu gì | `py scripts/discovery_gate.py <D0..D3>` |
| FEAT nào xong / đang dở | `tracking/{wave}/feature-state.md` (refresh: `py scripts/capture_feature_state.py`) |
| Bug đang mở | `tracking/{wave}/bugs.md` |
| Wave trước đã giao gì | `archive/wave-*/DELIVERED.md` |
| Năng lực nào chưa giao | `docs/discovery/capability-map.md` §1 cột `Trạng thái` |
| Quyết định đã ghi khi mơ hồ | `tracking/decisions.md` |
| Ai được / KHÔNG được làm gì | `docs/discovery/persona-pool.md` §Ma trận vai × hành động |

## Báo cáo thế nào

Ba dòng, không đổ nguyên JSON:

```
Đang ở : <stage> · <wave> · <boundary>
Chốt kế: <lệnh cụ thể + arg>
Thiếu  : <gate nào đỏ, thiếu gì — hoặc "không thiếu gì, chạy được ngay">
```

Không đọc được STATE → nói thẳng là không đọc được, đừng đoán.
