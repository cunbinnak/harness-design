---
description: "Harness: register-boundary"
argument-hint: "<boundary_id>"
---

# /register-boundary <boundary_id>

Đăng ký service: matrix + agent + knowledge graph (+ `services/` nếu materialize).

**Input:** `boundary_id` (vd. `catalog-api`)

```bash
python scripts/harness.py register-boundary catalog-api --materialize
```

