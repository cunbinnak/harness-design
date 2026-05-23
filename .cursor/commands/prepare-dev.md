---
description: "Harness: prepare-dev"
argument-hint: ""
---

# /prepare-dev

Tru?c `start-dev`: g?n FEAT?boundary?agent, n?p context, sync `STATE`.

**Agent:** [`agents/prepare-dev-agent.md`](../agents/prepare-dev-agent.md)

**Evidence:** `features_in_flight`, `boundaries_in_flight` — xem `'{"features_in_flight": ["FEAT-001"], "boundaries_in_flight": ["order"]}'`

```bash
python scripts/harness.py prepare-dev complete '{"features_in_flight": ["FEAT-001"], "boundaries_in_flight": ["order"]}'
```

Pre: `review-document` + `register-boundary` (matrix d?).

