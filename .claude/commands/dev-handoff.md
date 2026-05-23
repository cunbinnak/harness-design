---
description: "Harness command: dev-handoff"
argument-hint: ""
---

# /dev-handoff

**Agent:** [dev-handoff-agent.md](../agents/dev-handoff-agent.md)

```bash
python scripts/build_command_prompt.py dev-handoff
python scripts/harness.py dev-handoff complete '{"coverage_pct": 85, "handoff_ready": true}'
```

Gate: coverage ≥ 80%, `handoff_ready: true`