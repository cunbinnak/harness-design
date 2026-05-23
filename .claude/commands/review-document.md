---
description: "Harness: review-document"
argument-hint: ""
---

# /review-document

Ðánh giá tài li?u — không gap / mâu thu?n gi?a product, plan, architecture.

**Input:** scope (optional)

**Agent:** [`agents/review-document-agent.md`](../agents/review-document-agent.md)

**Evidence:** `{"approved": true}` — xem `'{"approved": true}'`

```bash
python scripts/harness.py review-document complete '{"approved": true}'
```

