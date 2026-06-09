---
name: test-execute
description: "Build service local + run auto test + log bug (origin=auto). KHÔNG fix (fix qua /fix-bugs). Auto-transition MANUAL_TEST sau khi chạy."
when_state: ['TEST_PLAN']
sets_stage: TEST_EXECUTE
spawn:
  agent: "test-execute-agent"
  skills: [test-execute, specialist-testing, bug-logging, infra-local-dev]
gates: [{type: int_min, field: test_cases_count, min: 1}]
---

# /test-execute

## Mục đích

Build & run service local theo docker-compose. Execute test cases theo registry. Fail -> log bug (origin=auto) vào bugs.md. **KHÔNG fix ở đây** — fix qua `/fix-bugs` ở MANUAL_TEST. Auto-transition MANUAL_TEST sau khi chạy (pass HAY fail).

## Build prompt + spawn

```bash
py scripts/build_prompt.py test-execute
py scripts/harness.py test-execute complete '{"test_cases_count": 15, "test_result": "pass"}'
# auto-transition: STATE.stage -> MANUAL_TEST
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

