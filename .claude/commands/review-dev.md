---
name: review-dev
description: "Self-review code. Internal loop: review-{kind} agent spawn fix sub-agents tới pass."
when_state: ['DEV']
sets_stage: REVIEW_DEV
spawn:
  agent: "review-{kind}-agent (singleton per kind)"
  skills: review-{kind}
gates: []
---

# /review-dev

## Mục đích

Review code dev vừa làm. Check coverage, convention, KG. Phát hiện issue -> spawn fix sub-agent fix -> re-review. Loop tới pass.

## Build prompt + spawn

```bash
py scripts/build_prompt.py review-dev --boundary order-management
# agent review-backend (cho kind=backend) tự loop fix + review
py scripts/harness.py review-dev complete '{}'
```

## Agent internal loop

```
1. Review code trong services/{prefix-boundary}/ theo skill review-{kind}
2. Phát hiện issue (coverage < 80, lint fail, convention violate) -> spawn fix-{prefix-boundary}-agent
3. Fix agent sửa -> trở lại step 1
4. Loop tới pass tất cả
5. Return {review_result: pass, coverage_pct: 85, ...}
```

