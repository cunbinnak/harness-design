---
id: BUG-{n}
wave: {wave-id}
origin: auto                    # auto | manual | review | framework
severity: medium                # critical | high | medium | low
status: open                    # open → reproduced → fixed → verified → closed
detected_by: test-execute       # test-execute | stakeholder | reviewer | <agent-id>
related_tc: TC-{n}              # ID test case liên quan
related_log: tracking/waves/{wave-id}/test-logs/TC-{n}.log
boundary: {boundary-id}
detected_at: {ISO date}         # tạo bug
reproduced_at: null             # fix-agent điền sau khi reproduce
fixed_at: null                  # fix-agent điền sau khi fix
verified_at: null               # retest điền sau khi verify
---

# BUG-{n} — {tiêu đề ngắn}

## Mô tả

(Mô tả ngắn vấn đề)

## Steps to reproduce

1. (Bước 1)
2. (Bước 2)
3. Expected: ...
4. Actual: ...

## Evidence

- **Test log**: `tracking/waves/{wave-id}/test-logs/TC-{n}.log` (link đầy đủ)
- **Screenshot**: `tracking/waves/{wave-id}/test-logs/screenshots/TC-{n}.png` (nếu UI)
- **HTTP capture**: response code + body từ log

## Suspected root cause

(Suy đoán từ tester — fix-agent có thể chọn approach khác sau khi đọc source)

## Fix suggestion

(Gợi ý hướng fix — fix-agent quyết cuối)

---

## Fix cycle log (BẮT BUỘC điền đủ — fix-agent + retest)

### Step 1 — Reproduce
- **Reproduced at**: (timestamp)
- **By**: fix-{boundary}-agent
- **Command run**: (curl/pytest command)
- **Actual response**: HTTP {code}, body excerpt
- **Confirmed**: ✓ bug tồn tại / ✗ không reproduce được (giải thích)

### Step 2 — Fix
- **Fixed at**: (timestamp)
- **Files changed**: (list)
- **Root cause identified**: (mô tả ngắn)
- **Lint**: pass | fail
- **Unit test local**: pass | fail

### Step 3 — Verify (fix-agent local)
- **Re-run TC**: (command + actual response)
- **Regression test**: pass | fail (link log)
- **Verification log**: `tracking/waves/{wave-id}/bugs/verification/BUG-{n}-verify.log`

### Step 4 — Verify retest (by retest command)
- **Verified at**: (timestamp by retest)
- **Re-run via test-execute infra**: pass | fail
- **Status**: verified | failed (quay lại fix)

---

> **Lưu ý field `origin`:**
> - `auto` → bug từ `test-execute`. `retest` smart-route về `SPECIALIST_TESTING`.
> - `manual` → bug stakeholder log trong stage `MANUAL_TEST`. `retest` smart-route về `MANUAL_TEST`.
> - `review` → bug `reviewer-agent` flag trong `SELF_REVIEW`. Smart route auto path.
> - `framework` → vấn đề về framework setup (vd: thiếu E2E config) — không phải bug code.
>
> **Status flow bắt buộc:** `open → reproduced → fixed → verified → closed`. KHÔNG được skip step.
> Hook gate check: bug có status `fixed` mà thiếu `reproduced_at` → reject.
