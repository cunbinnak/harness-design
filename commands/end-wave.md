---
name: end-wave
description: "UAT đã signed off. Soft close wave -> DONE."
when_state: ['MANUAL_TEST']
sets_stage: DONE
spawn:
  agent: "end-wave-agent"
  skills: []
gates: [{type: flag, field: uat_signed, expected: true}, {type: test_passed}, {type: no_open_bugs}, {type: features_complete}]
---

# /end-wave

## Mục đích

UAT đã signed off, không còn open bug, **test-execute cuối xanh**. Soft close: wave kết thúc logic + **tắt service** (`docker compose stop` — giữ image+volume cho wave kế reuse nhanh). KHÔNG `down --volumes` (đó là `/done-wave` hard-close).

## Build prompt + spawn

```bash
py scripts/build_prompt.py end-wave
py scripts/harness.py end-wave complete '{"uat_signed": true}'
# gates: uat_signed + test_passed (STATE.test_result=pass) + no_open_bugs (bugs.md) + features_complete
```

> Sau `/fix-bugs`, `STATE.test_result` còn `fail` của lần test trước → `/end-wave` **bị chặn** tới khi re-run `/test-execute` cho full suite xanh. Ép vòng fix ↔ test-execute tới khi sạch.

> **`features_complete` (WIP=1 ship-gate, L07):** derive `feature-state.md` — KHÔNG in-scope feat nào được `active` (làm dở: một phần AC verified, phần khác chưa). Đây là "xong hẳn 1 feat mới sang feat kế" biến từ lời-dặn thành enforcement máy tại điểm ship (VCR=1.0). CHỈ chặn `active`; `not_started` (vd AC chỉ-manual chưa ghi report) do test_passed/uat lo — không chặn oan. Refresh state: `py scripts/capture_feature_state.py`. force-bypass+audit.

