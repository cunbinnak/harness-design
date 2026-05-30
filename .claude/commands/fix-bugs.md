---
name: fix-bugs
description: "Fix manual UAT bug. Chain spawn fix sub-agent + review sub-agent verify."
when_state: ['MANUAL_TEST']
sets_stage: MANUAL_TEST
spawn:
  agent: "fix-{prefix-boundary}-agent (materialized) + review-{kind}-agent (singleton)"
  skills: rules-{kind} + review-{kind} + bug-logging
gates: [{type: non_empty, field: bug_id}]
---

# /fix-bugs

## Mục đích

Fix bug từ manual UAT. Chain fix + review trong cùng MANUAL_TEST state.

## Build prompt + spawn

```bash
py scripts/build_prompt.py fix-bugs --bug-id BUG-007
py scripts/harness.py fix-bugs complete '{"bug_id": "BUG-007"}'
```

## Agent chain

```
1. fix-{prefix-boundary}-agent đọc bugs.md > BUG-007 > sửa code
2. Tự động chain spawn review-{kind}-agent verify fix
3. Review pass -> mark BUG-007 status=closed trong bugs.md
4. Review fail -> loop step 1
5. Stay MANUAL_TEST throughout
```

