---
name: test-execute
description: Run auto test theo registry, ghi test-report.md, log bug nếu fail.
---

# Test Execute Skill

## Khi load
`test-execute-agent` ở `/test-execute` và `/retest`.

## Hoạt động
1. Đọc `tracking/wave-{N}/test-case-registry.md`.
2. Foreach TC (P0 trước, P1, P2):
   - Run cmd theo type (api → curl/postman, e2e → playwright, ui → playwright, …).
   - Append result vào `tracking/wave-{N}/test-report.md`: `TC-ID: pass|fail|skip + timestamp + duration + log tail`.
3. Foreach fail: log bug vào `tracking/wave-{N}/bugs.md` (skill `bug-logging`).

## Exit
- Tất cả P0 pass → `test_result: pass` → command transition RELEASE.
- Bất kỳ P0 fail → `test_result: fail` → command transition BUG_LOGGING.
