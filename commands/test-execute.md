---
name: test-execute
description: "Build service local + run auto test. Internal loop: fail -> spawn fix -> retest -> pass. Auto-transition MANUAL_TEST khi pass."
when_state: ['TEST_PLAN']
sets_stage: TEST_EXECUTE
spawn:
  agent: "test-execute-agent"
  skills: [test-execute, specialist-testing, bug-logging, infra-local-dev]
gates: [{type: int_min, field: test_cases_count, min: 1}]
---

# /test-execute

## Mục đích

Build & run service local theo docker-compose. Execute test cases theo registry. Fail -> log bug + spawn fix sub-agent -> retest. Loop tới pass.

## Build prompt + spawn

```bash
py scripts/build_prompt.py test-execute
py scripts/harness.py test-execute complete '{"test_cases_count": 15, "test_result": "pass"}'
# auto-transition: STATE.stage -> MANUAL_TEST
```

## Agent internal loop

```
1. docker-compose up -d
2. Run test cases (Postman/Playwright/...) per skill test-execute
3. Fail -> log BUG-NNN vào tracking/wave-N/bugs.md (origin: auto)
        -> spawn fix-{prefix-boundary}-agent fix
        -> back to step 2
4. All pass -> return {test_result: pass, ...}
5. Harness auto-transition TEST_EXECUTE -> MANUAL_TEST
```

