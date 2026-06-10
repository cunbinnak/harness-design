---
name: fix-bugs
description: "Fix bug (Mode A). KHÔNG arg = sweep MỌI bug open; có <bug-id> = fix 1 cái. MAIN spawn fix → re-run TC verify → close."
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

## Hai chế độ

- **Sweep (không arg)** — fix MỌI bug open, tự động (không cần báo từng ID):
  ```bash
  py scripts/build_prompt.py fix-bugs        # orchestrator: liệt kê bug open → MAIN loop per bug
  ```
  MAIN đọc `bugs.md` → mỗi bug `status ∈ {open, in_progress}`: spawn `fix-{prefix}-{boundary}-agent` (boundary lấy từ row) → close → bug kế.

- **Đơn lẻ (`--bug-id`)** — fix 1 bug:
  ```bash
  py scripts/build_prompt.py fix-bugs --bug-id BUG-007 --boundary <b>
  py scripts/harness.py fix-bugs complete '{"bug_id": "BUG-007"}'
  ```

## Flow mỗi bug (MAIN spawn fix, KHÔNG chain review)

```
1. MAIN spawn fix-{prefix-boundary}-agent với bug_id
2. fix đọc row BUG-007 trong bugs.md > reproduce TC fail > sửa code
3. fix re-run CHÍNH TC fail + scoped test pass (regression) — KHÔNG gọi review-agent
4. Pass -> fix set BUG-007 status=closed + regression TC-R* trong bugs.md > return
5. Fail -> fix loop step 2-3
6. Stay MANUAL_TEST throughout
```

> Test bug verify bằng test. Code review là việc của `/review-dev` (REVIEW_DEV), không phải ở đây.

