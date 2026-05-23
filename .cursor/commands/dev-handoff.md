---
description: "Harness: dev-handoff"
argument-hint: ""
---

# /dev-handoff

Bàn giao dev ? test. **B?t bu?c coverage d?t ngu?ng** m?i complete.

**Agent:** [`agents/dev-handoff-agent.md`](../agents/dev-handoff-agent.md)

**Gate:** `coverage_pct` = 80 (xem `COMMAND-GATES.json`), `handoff_ready: true`

**Evidence:** `'{"coverage_pct": 85, "handoff_ready": true}'`

```bash
python scripts/harness.py dev-handoff complete '{"coverage_pct": 85, "handoff_ready": true}'
```

Fail gate ? quay `review-dev` / `start-dev`, không `test-plan`.

