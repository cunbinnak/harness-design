---
description: "Harness command: register-boundary"
argument-hint: ""
---

# /register-boundary

Đăng ký service: matrix + agent + knowledge graph (+ `services/` nếu materialize).

**Input:** `boundary_id` (vd. `catalog-api`)

```bash
python scripts/harness.py register-boundary catalog-api --materialize
```