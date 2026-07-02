---
name: test-execute
description: "Chạy auto TC BLACK-BOX trên hệ thống đang chạy + log bug (origin=auto). KHÔNG build source, KHÔNG fix (fix qua /fix-bugs). Auto-transition MANUAL_TEST sau khi chạy. Re-run được từ MANUAL_TEST sau fix."
when_state: ['TEST_PLAN', 'MANUAL_TEST']
sets_stage: TEST_EXECUTE
spawn:
  agent: "test-execute-agent"
  skills: [test-execute, specialist-testing, bug-logging, infra-local-dev]
gates: [{type: int_min, field: test_cases_count, min: 1}, {type: test_evidence}]
---

# /test-execute

## Mục đích

Chạy auto test cases theo registry **black-box trên hệ thống ĐANG CHẠY** (KHÔNG build source). Fail -> log bug (origin=auto) vào bugs.md. **KHÔNG fix ở đây** — fix qua `/fix-bugs` ở MANUAL_TEST. Auto-transition MANUAL_TEST sau khi chạy (pass HAY fail).

## Gate `test_evidence` (chống test ảo)

`scripts/gates.py check_test_evidence` parse registry + `tracking/wave-{N}/test-report.md` + `test-logs/` + `bugs.md` + `screenshots/` + `health-proof.json`. Mỗi auto-TC **in-scope** (bỏ `@deferred` đã khai báo wave plan): (a) phải có result trong report; (b) group integration/e2e/perf/security khi pass|fail phải có network-call `METHOD path -> status` trong log; (c) skip phải nêu lý do service-down (marker cụm-từ cụ thể, "dropdown"/"unavailable" chung chung KHÔNG tính) **và không mâu thuẫn health-proof** (proof nói service UP → skip service-down bị chặn; service chết thật → re-run `capture_infra_proof.py` cập nhật proof); (d) result=FAIL phải có ≥1 bug reference (cột `TC` bugs.md) — chống "fail quên log = miss bug" (mirror ZIP `lint_execution`); (e) **TC trên WEB boundary khi pass|fail phải có screenshot thật** `screenshots/{TC}*.png` (PNG/JPEG magic-bytes ≥1KB — chống UI-test khống). **KHÔNG fail chỉ vì TC=fail** (bug hợp lệ ĐÃ log) — chỉ chặn khi thiếu bằng chứng đã chạy / fail không log bug. `test_result` do harness **DERIVE từ report** (in-scope all-pass → pass), không verbatim từ agent. Env-block → `force:true,reason` (audit).

## Build prompt + spawn

```bash
py scripts/build_prompt.py test-execute
py scripts/harness.py test-execute complete '{"test_cases_count": 15, "test_result": "pass"}'
# auto-transition: STATE.stage -> MANUAL_TEST ; harness DERIVE lại test_result từ test-report.md
```

## Flow (test-only, KHÔNG fix)

```
1. docker-compose up -d
2. Run test cases (Postman/Playwright/...) per skill test-execute, capture proof per TC
3. Fail -> log BUG-NNN vào tracking/wave-N/bugs.md (origin: auto). KHÔNG spawn fix, KHÔNG loop.
4. Aggregate test-report.md. KHÔNG teardown (infra giữ UP cho MANUAL_TEST)
5. return {test_result: pass|fail, test_cases_count, bugs_logged: [...]}
6. Harness auto-transition TEST_EXECUTE -> MANUAL_TEST (pass HAY fail)
7. Bug auto + UAT manual đều fix qua /fix-bugs ở MANUAL_TEST; gate no_open_bugs (end-wave) chặn ship
```

## Vòng loop re-run (MANUAL_TEST)

`/test-execute` chạy được **lại từ MANUAL_TEST** (sau khi /fix-bugs) để chạy **full auto suite**, bắt regression cross-boundary/E2E mà scoped test per-bug không thấy:

```
MANUAL_TEST
  /fix-bugs <BUG-NNN>     → fix từng bug (re-run TC đó + scoped test)
  /test-execute           → chạy LẠI full suite → TEST_EXECUTE → _auto → MANUAL_TEST
     · TC fail lại        → UPDATE row cũ = status open (reopen regression)
     · TC pass            → row giữ closed (không log lại)
     · regression mới     → log BUG mới (open)
  (lặp fix ↔ re-run tới khi re-run sạch)
  /end-wave               → gate no_open_bugs: còn bug open thì chặn
```

