---
description: "Harness command: apply-cr"
argument-hint: "--cr CR-001"
---

# /apply-cr --cr CR-001

**Phân tích Change Request** và chuẩn bị **intake amendment**. File CR tồn tại = coi như **đã duyệt** (không bước approve riêng).

Orchestrator: [apply-cr-agent.md](../agents/apply-cr-agent.md) · Pipeline: [CR-INTAKE-PIPELINE.json](../harness/CR-INTAKE-PIPELINE.json)

## Khi nào

- Thay đổi scope / nghiệp vụ / boundary sau khi đã có plan (`review-document` trở đi)
- Giữa dev (`start-dev`, `review-dev`) hoặc sau `end-wave`

## Chạy

1. Tạo `tracking/change-requests/CR-NNN-*.md` từ [TEMPLATE.cr.md](../tracking/change-requests/TEMPLATE.cr.md)
2. Phân tích CR:

```bash
py scripts/build_command_prompt.py apply-cr --cr CR-001
py scripts/harness.py apply-cr complete '{"cr_id":"CR-001","cr_path":"tracking/change-requests/CR-001-....md"}'
```

3. Intake amendment (bắt buộc sau `apply-cr` nếu có `cr_id`):

```bash
py scripts/build_command_prompt.py intake-requirement --step 1 --input "CR-001: ..."
# ... step 2–4 ...
py scripts/harness.py intake-requirement complete '{"intake_mode":"amendment","cr_id":"CR-001","change_summary":"..."}'
py scripts/harness.py review-document complete '{"approved": true}'
```

Wave đang mở: tiếp `start-dev` (không cần `start-wave` lại). Wave mới / sau `end-wave`: `start-wave`.

Discipline: rule `.cursor/rules/harness-agent-discipline.mdc` + shared KG