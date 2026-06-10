---
name: log-bug
description: "Log 1 bug manual (UAT) vào bugs.md từ mô tả. Spawn log-bug-agent (origin=manual). Rồi /fix-bugs."
when_state: ['MANUAL_TEST']
sets_stage: MANUAL_TEST
spawn:
  agent: "log-bug-agent"
  skills: [bug-logging]
gates: [{type: non_empty, field: bug_id}]
---

# /log-bug

## Mục đích

UAT/stakeholder phát hiện bug → ghi vào `tracking/wave-{N}/bugs.md` (`origin=manual`) để `/fix-bugs` xử lý. **Chỉ cần MÔ TẢ** — `log-bug-agent` tự parse + suy boundary.

## Vị trí trong flow

```
MANUAL_TEST
  /log-bug "<mô tả>"   → log-bug-agent append row (origin=manual, status=open)
  /fix-bugs            → sweep fix mọi bug open (hoặc /fix-bugs BUG-NNN cho 1 cái)
  /end-wave            → gate no_open_bugs
```

## Build prompt + spawn

```bash
py scripts/build_prompt.py log-bug --description "lỗi validate SĐT khách hàng chưa đúng định dạng VN (10 số)"
# → spawn log-bug-agent
py scripts/harness.py log-bug complete '{"bug_id": "BUG-005"}'
```

## Flow

```
1. MAIN spawn log-bug-agent với mô tả (kèm màn/context nếu user nêu)
2. agent invoke bug-logging → đọc bugs.md (next BUG-NNN) → parse mô tả
3. agent suy boundary từ nội dung + màn (FEAT/UX/MATRIX); mơ hồ → hỏi user 1 câu
4. agent append 1 row (origin=manual, status=open) → return bug_id
5. Stay MANUAL_TEST. Tiếp tục /log-bug bug khác, hoặc /fix-bugs để xử.
```

## Quy tắc

- **Chỉ ghi, KHÔNG fix** — fix là `/fix-bugs`.
- Mô tả **càng rõ màn/bước càng tốt** → agent suy boundary chính xác, đỡ phải hỏi.
- `sev` mặc định `medium`; muốn khác thì nêu trong mô tả.
- Bug `auto` (test-execute) đã tự log — `/log-bug` chỉ cho bug **manual** (UAT).
