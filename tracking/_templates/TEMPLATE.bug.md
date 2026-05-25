---
id: BUG-{n}
wave: {wave-id}
origin: auto                    # auto | manual | review
severity: medium                # critical | high | medium | low
status: open                    # open | fixed | verified | closed
detected_by: test-execute       # test-execute | stakeholder | reviewer | <agent-id>
related_tc: TC-{n}              # ID test case liên quan (nếu có)
boundary: {boundary-id}         # boundary chịu trách nhiệm fix
created_at: {ISO date}
---

# BUG-{n} — {tiêu đề ngắn}

## Mô tả

(Mô tả ngắn vấn đề từ góc người dùng / tester)

## Steps to reproduce

1. (Bước 1)
2. (Bước 2)
3. Expected: ...
4. Actual: ...

## Evidence

- Screenshot / log / request-response (nếu có)
- File: `path/to/log.txt`

## Suspected root cause

(Suy đoán từ tester / reviewer — không bắt buộc)

## Fix suggestion

(Gợi ý fix nếu có — fix agent có thể chọn approach khác)

---

## Fix log

| Date | Agent | Action | Result |
|------|-------|--------|--------|
| {date} | fix-{boundary}-agent | Implemented fix | Status: fixed |
| {date} | retest | Re-tested | Status: verified |

---

> **Lưu ý field `origin`:**
> - `auto` → bug từ `test-execute` (auto test). `retest` smart-route về SPECIALIST_TESTING.
> - `manual` → bug stakeholder/QA log trong stage MANUAL_TEST. `retest` smart-route về MANUAL_TEST.
> - `review` → bug reviewer-agent flag trong stage SELF_REVIEW. Path tương tự auto.
