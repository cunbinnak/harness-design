---
name: fix-bugs
description: "Fix manual UAT bug (Mode A). MAIN spawn fix → fix re-run TC + scoped test verify → close bug."
when_state: ['MANUAL_TEST']
sets_stage: MANUAL_TEST
spawn:
  agent: "fix-{prefix-boundary}-agent (materialized)"
  skills: rules-{kind} + bug-logging
gates: [{type: non_empty, field: bug_id}]
---

# /fix-bugs

## Mục đích

Fix bug từ manual UAT (Mode A). Fix + verify bằng re-run test trong cùng MANUAL_TEST state. KHÔNG gọi review-agent (sub-agent không spawn được sub-agent; review-agent là của REVIEW_DEV).

## Build prompt + spawn

```bash
py scripts/build_prompt.py fix-bugs --bug-id BUG-007
py scripts/harness.py fix-bugs complete '{"bug_id": "BUG-007"}'
```

## Flow (MAIN spawn fix, KHÔNG chain review)

```
1. MAIN spawn fix-{prefix-boundary}-agent với bug_id
2. fix đọc row BUG-007 trong bugs.md > reproduce TC fail > sửa code
3. fix re-run CHÍNH TC fail + scoped test pass (regression) — KHÔNG gọi review-agent
4. Pass -> fix set BUG-007 status=closed + regression TC-R* trong bugs.md > return
5. Fail -> fix loop step 2-3
6. Stay MANUAL_TEST throughout
```

> Test bug verify bằng test. Code review là việc của `/review-dev` (REVIEW_DEV), không phải ở đây.

