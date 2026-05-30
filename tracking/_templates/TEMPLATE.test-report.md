# Test Report — wave-{N}

> Wave: wave-{N} ({wave-title})
> Executed by: test-execute-agent
> Date: {date}
> Cases registry: `tracking/wave-{N}/test-case-registry.md`
> Per-TC logs: `tracking/wave-{N}/test-logs/`
> Screenshots: `tracking/wave-{N}/test-logs/screenshots/`
> E2E framework: playwright | cypress | none

---

## Summary

| Metric | Value |
|--------|-------|
| Total TCs in registry | {N} |
| Auto TCs | {N_auto} |
| Manual TCs | {N_manual} |
| Auto logs produced | {N_logs} (MUST == auto TCs) |
| Passed | {N_pass} |
| Failed | {N_fail} |
| Skipped (N/A) | {N_skip} |
| Bugs logged | {N_bugs} |
| Fix loops triggered | {N_fixes} |
| Screenshots captured | {N_screenshots} |
| Overall | **PASS** (all P0 pass) / **FAIL** (any P0 fail) |

---

## Per-TC Results (cross-ref logs)

### Smoke Tests

| TC | Log file | Result | Duration | Notes |
|----|----------|--------|----------|-------|
| TC-S01 | `test-logs/TC-S01.log` | PASS | 120ms | Health 200 OK |
| TC-S02 | `test-logs/TC-S02.log` | PASS | 340ms | Token received |

### Integration Tests

| TC | Log file | Result | Duration | Notes |
|----|----------|--------|----------|-------|
| TC-I01 | `test-logs/TC-I01.log` | PASS | 580ms | Created id=42 |
| TC-I02 | `test-logs/TC-I02.log` | FAIL | 320ms | Expected 400, got 500 → BUG-001 |
| TC-I03 | `test-logs/TC-I03.log` | PASS | 110ms | 401 as expected |

### E2E Tests

| TC | Log file | Screenshot | Result | Duration | Notes |
|----|----------|------------|--------|----------|-------|
| TC-E01 | `test-logs/TC-E01.log` | `screenshots/TC-E01.png` | PASS | 4.2s | Playwright |
| TC-E02 | `test-logs/TC-E02.log` | `screenshots/TC-E02.png` | SKIP (manual) | - | - |

### Manual Tests

> Manual TCs sẽ được verify ở stage MANUAL_TEST sau end-wave. Test-execute KHÔNG chạy manual TCs.

| TC | Status |
|----|--------|
| TC-M01 | Pending (manual UAT) |
| TC-M02 | Pending (manual UAT) |

### Regression Tests

| TC | Log file | Result | Notes |
|----|----------|--------|-------|
| TC-R01 | `test-logs/TC-R01.log` | PASS | BUG-{NNN} regression check OK |

---

## Failed TCs detail (with bug references)

### TC-I02: FAIL → BUG-001

```
Log: test-logs/TC-I02.log

Command: curl -s -w "\n%{http_code}" -X POST http://localhost:8080/v1/orders -d '{}'
Expected: HTTP 400 (validation error)
Actual: HTTP 500 (internal server error)
Body (500 chars): {"error":"NullPointerException at OrderService.validate"...}

Bug logged: BUG-001 (tracking/wave-{N}/bugs.md#BUG-001)
Origin: auto
Severity: high (validation should not 500)
Boundary: order-mgmt
Status: open → fixed (after fix loop)
```

---

## Fix loops triggered

| Iteration | Bug | Fix agent | Duration | Result |
|-----------|-----|-----------|----------|--------|
| 1 | BUG-001 | fix-{prefix}-order-mgmt-agent | 3m12s | Fixed, re-run TC-I02 PASS |

---

## Infrastructure status (during test run)

```
docker-compose ps (start):
NAME                COMMAND      SERVICE   STATUS         PORTS
auth                ...          auth      Up (healthy)   8081->8081
order-mgmt          ...          order     Up (healthy)   8080->8080
postgres            ...          db        Up (healthy)   5432->5432
redis               ...          cache     Up (healthy)   6379->6379

Teardown (end):
- docker-compose down: SUCCESS
- Volumes cleaned: YES
```

---

## Recommendations for MANUAL_TEST (end-wave)

- All P0 auto pass. Safe to proceed to UAT.
- Manual TCs (M01, M02) pending stakeholder verification.
- BUG-001 fixed and regression covered by TC-R01.
- No flaky test observed.
