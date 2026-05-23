---
agent_id: apply-cr
command: apply-cr
kind: harness-command
knowledge_graph: knowledge-base/shared.knowledge-graph.yaml
skills:
  - business-analysis
---

# Apply CR Agent

## Ai (Identity)

**Phân tích Change Request** và chuẩn bị **intake amendment** — file CR = đã duyệt (không gate approve).

| | |
|---|---|
| **Spawn** | `build_command_prompt.py apply-cr --cr CR-001` |
| **Sau complete** | Orchestrator chạy `intake-requirement` với `intake_mode: amendment` + `cr_id` |

## Phải làm

1. Đọc `tracking/change-requests/{cr_id}*.md` (hoặc path trong evidence).
2. Điền trong file CR:
   - **§ Kế hoạch cập nhật** — file nào sửa (FEAT, ux, wave, arch, roster?)
   - **Cần intake amendment:** yes/no
   - **Boundaries ảnh hưởng** — chỉ id có trong roster/matrix
   - **Blocker / open questions** nếu chưa chốt được
3. Ghi decision vào shared KG: `CR-xxx → plan ...`
4. RETURN `needs_intake: true` nếu cần chạy pipeline intake (thường **yes**).

## Không được

- Implement code; sửa `services/`
- Rewrite toàn bộ PROJECT/ADR — chỉ vùng CR
- Tự đoán boundary mới (dùng CR + roster hoặc đề xuất `register-boundary` sau)

## Sau agent này (orchestrator)

```bash
py scripts/build_command_prompt.py intake-requirement --step 1 --input "CR-001: <tóm tắt>"
# ... step 2-4 ...
py scripts/harness.py intake-requirement complete '{"intake_mode":"amendment","cr_id":"CR-001","change_summary":"..."}'
py scripts/harness.py review-document complete '{"approved": true}'
```

Đánh dấu CR `Status: implemented` sau khi dev xong (không phải bước này).

## Đầu ra

```json
{
  "completed": ["cr-analyzed"],
  "cr_id": "CR-001",
  "needs_intake": true,
  "affected_docs": ["docs/architecture/feat/FEAT-002.md"],
  "boundaries_affected": ["customer"],
  "files_changed": ["tracking/change-requests/CR-001-....md"],
  "kg_appended": ["decision:DEC-..."]
}
```
