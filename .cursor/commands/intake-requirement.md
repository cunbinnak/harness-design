---
description: "Harness: intake-requirement — bắt đầu luồng (trước start-wave)"
argument-hint: "<input>"
---

# /intake-requirement <input>

**Bước đầu tiên:** nhận yêu cầu → phân tích → lập kế hoạch. **Chưa** `start-wave`.

```bash
py scripts/build_command_prompt.py intake-requirement --step 1 --input "YOUR INPUT"
py scripts/build_command_prompt.py intake-requirement --step 2
py scripts/build_command_prompt.py intake-requirement --step 3
py scripts/build_command_prompt.py intake-requirement --step 4
py scripts/materialize_boundary_agents.py --boundaries order,product --wave wave-001
py scripts/harness.py intake-requirement complete
```

Tiếp theo: `review-document` → `start-wave` → …

Gates: [`harness/COMMAND-GATES.json`](../harness/COMMAND-GATES.json)
