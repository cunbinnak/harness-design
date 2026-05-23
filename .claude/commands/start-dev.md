---
description: "Harness: start-dev"
argument-hint: ""
---

# /start-dev

Bắt đầu triển khai code theo boundary trong matrix.

**Input:** `boundary_id` (optional nếu một boundary)

**Pre:** [`prepare-dev`](prepare-dev.md) đã complete.

**Agent:** `{boundary_id}-agent` từ matrix

```bash
python scripts/harness.py start-dev complete
```

