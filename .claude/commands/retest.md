---
description: "Harness command: retest"
argument-hint: ""
---

# /retest

Chạy lại test sau `fix-bugs` — smart routing.

**Evidence:** `{"test_result": "pass" | "fail"}`

## Smart routing

`workflow_engine.py` đọc `state.checkpoints[]` để xác định origin của bug đã fix:

| Origin bug | Branch | Stage sau (pass) | next_allowed |
|------------|--------|------------------|--------------|
| `auto` (từ test-execute) | `pass_auto` | SPECIALIST_TESTING | `["release"]` |
| `manual` (từ MANUAL_TEST stage) | `pass_manual` | MANUAL_TEST | `["fix-bugs", "done-wave"]` |
| (fail trong cả 2) | `fail` | FIX_MANUAL_BUGS giữ nguyên | `["fix-bugs"]` |

## Chạy

```bash
# Auto retest (sau test-execute fail)
py scripts/harness.py retest complete '{"test_result": "pass"}'
# → quay về SPECIALIST_TESTING, allowed_next=[release]

# Manual retest (sau bug từ MANUAL_TEST stage)
py scripts/harness.py retest complete '{"test_result": "pass"}'
# → quay về MANUAL_TEST, allowed_next=[fix-bugs, done-wave]
```

Không cần truyền `origin` — đọc từ bug ticket gần nhất status=fixed.