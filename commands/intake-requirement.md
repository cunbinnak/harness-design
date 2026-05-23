# intake-requirement

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
2. `start-wave` (cần plan đã có)
3. `sync-boundaries` → `prepare-dev` → dev → release

[docs/LUONG-PHAT-TRIEN-SAN-PHAM.md](../docs/LUONG-PHAT-TRIEN-SAN-PHAM.md)
