---
description: "Harness: test-execute"
argument-hint: ""
---

# /test-execute

Agent test **ch?y** theo plan + registry t? `test-plan`.

**Agent:** [`agents/test-execute-agent.md`](../agents/test-execute-agent.md)

**Evidence:** `{"test_result": "pass"}` ho?c `"fail"` — `'{"test_result": "pass"}'`

```bash
python scripts/harness.py test-execute complete '{"test_result": "pass"}'
```

- `pass` ? cho phép `release`
- `fail` ? `fix-bugs`

