---
name: end-wave
description: "UAT đã signed off. Soft close wave -> DONE."
when_state: ['MANUAL_TEST']
sets_stage: DONE
spawn:
  agent: "end-wave-agent"
  skills: []
gates: [{type: flag, field: uat_signed, expected: true}, {type: test_passed}, {type: no_open_bugs}]
---

# /end-wave

## Mục đích

UAT đã signed off, không còn open bug, **test-execute cuối xanh**. Soft close: wave kết thúc logic + **tắt service** (`docker compose stop` — giữ image+volume cho wave kế reuse nhanh). KHÔNG `down --volumes` (đó là `/done-wave` hard-close).

## Build prompt + spawn

```bash
py scripts/build_prompt.py end-wave
py scripts/harness.py end-wave complete '{"uat_signed": true}'
# gates: uat_signed + test_passed (STATE.test_result=pass) + no_open_bugs (bugs.md)
```

> Sau `/fix-bugs`, `STATE.test_result` còn `fail` của lần test trước → `/end-wave` **bị chặn** tới khi re-run `/test-execute` cho full suite xanh. Ép vòng fix ↔ test-execute tới khi sạch.

