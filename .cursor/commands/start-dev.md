---
description: "Harness: start-dev — triển khai theo boundary"
argument-hint: "<boundary_id>"
---

# /start-dev [boundary_id]

Bắt đầu code boundary — agent `agents/{boundary}-agent.md`.

**Gồm:** điền `docs/plans/waves/{wave-id}/wave.md` §2 Assignment (trước đây là `prepare-dev`).

```bash
py scripts/build_command_prompt.py start-dev --boundary customer
py scripts/harness.py start-dev complete '{"features_in_flight":["FEAT-001-..."],"boundaries_in_flight":["customer","sales","fe"]}'
```

Tiếp theo: `/review-dev`.

Gates: [`harness/COMMAND-GATES.json`](../harness/COMMAND-GATES.json)
