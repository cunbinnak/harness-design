---
description: "Harness command: intake-requirement"
argument-hint: "<input>"
---

# /intake-requirement <input>

**Command đầu tiên** — phân tích yêu cầu & lập kế hoạch (**trước** `start-wave`).

Orchestrator: [intake-orchestrator-agent.md](../agents/intake-orchestrator-agent.md)

## Chạy

```bash
py scripts/build_command_prompt.py intake-requirement --step 1 --input "..."
py scripts/build_command_prompt.py intake-requirement --step 2
py scripts/build_command_prompt.py intake-requirement --step 3
py scripts/build_command_prompt.py intake-requirement --step 4
py scripts/materialize_boundary_agents.py --boundaries order,product --wave wave-001
py scripts/harness.py intake-requirement complete
```

## Sau intake

1. `review-document`
2. `start-wave` (sync matrix từ roster — không cần lệnh riêng)
3. `start-dev` → … → `release` → `end-wave`

Đổi scope sau này: [`apply-cr`](apply-cr.md) → intake `amendment` → `review-document`.

[SETUP-GUIDE.md](../SETUP-GUIDE.md)