---
description: "Harness command: review-dev"
argument-hint: ""
---

# /review-dev

Self-review theo boundary — spawn `review-{boundary}-agent.md`.

```bash
python scripts/build_command_prompt.py review-dev --boundary order
python scripts/harness.py review-dev complete
```