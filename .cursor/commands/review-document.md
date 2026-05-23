---
description: "Harness command: review-document"
argument-hint: ""
---

# /review-document

**Agent:** [review-document-agent.md](../agents/review-document-agent.md)

```bash
python scripts/build_command_prompt.py review-document
python scripts/harness.py review-document complete '{"approved": true}'
```

Kiểm tra bộ 3 dev agents/boundary + pipeline intake trong handoff.