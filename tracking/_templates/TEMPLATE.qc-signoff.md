# QC Signoff — wave-{N}

> Wave: wave-{N} ({wave-title})
> Stage: MANUAL_TEST
> Started: {start-date}
> UAT verifiers: {stakeholder-name}, QA team
> Updated by: end-wave-agent (finalize)

---

## UAT Test Sessions

### Session 1 — {tester-name} — {date}

| TC | Title | Type | Result | Notes |
|----|-------|------|--------|-------|
| TC-M01 | Business flow create order | manual | PASS | Stakeholder confirm OK |
| TC-M02 | Edge case max quantity | manual | PASS | Handle gracefully |
| TC-M03 | Multi-tenant isolation | manual | PASS | Tenant A không thấy data tenant B |
| TC-M04 | Print preview PDF | manual | FAIL | PDF render sai font → BUG-002 |

### Session 2 — {tester-name} — {date}

> Sau khi BUG-002 fixed, re-test.

| TC | Title | Type | Result | Notes |
|----|-------|------|--------|-------|
| TC-M04 | Print preview PDF | manual | PASS | Font đã fix, render OK |

---

## Bugs Found During UAT

| Bug | TC ref | Severity | Status | Fixed in |
|-----|--------|----------|--------|----------|
| BUG-002 | TC-M04 | medium | closed | fix-bugs iteration |

---

## Acceptance Criteria Coverage

| FEAT | AC | TCs verifying | Status |
|------|-----|---------------|--------|
| FEAT-001 | AC-1, AC-2, AC-3 | TC-S02, TC-I01, TC-I02, TC-I03 | PASS |
| FEAT-002 | AC-1, AC-2 | TC-E01, TC-M01 | PASS |
| FEAT-003 | AC-1 | TC-M03 | PASS |

**Coverage**: 100% AC of FEAT 'Must' priority.

---

## NFR Verification

| NFR | Target | Measured | Status |
|-----|--------|----------|--------|
| Response time p99 | <= 200ms | 180ms | PASS |
| Concurrent users | 100 | 100 stable | PASS |
| Multi-tenant isolation | strict | verified TC-M03 | PASS |
| Auth security | JWT + RBAC | verified TC-I03 | PASS |

---

## Sign-off

### Stakeholder approval

```yaml
stakeholder: "{name}"
role: "Product Owner"
signoff_date: "{date}"
decision: "APPROVED"
notes: "All P0/P1 manual TCs pass. Acceptable for production deployment."
```

### QA approval

```yaml
qa_lead: "{name}"
signoff_date: "{date}"
decision: "APPROVED"
notes: "Auto + manual test coverage adequate. No critical issue."
```

### Dev approval

```yaml
dev_lead: "{name}"
signoff_date: "{date}"
decision: "APPROVED"
notes: "All bugs fixed and regression verified."
```

---

## Checklist before end-wave complete

- [x] All P0 auto TCs pass (test-execute)
- [x] All P0 manual TCs pass (UAT)
- [x] No open bug (status != open trong bugs.md)
- [x] Stakeholder sign-off
- [x] NFR verified vs PROJECT.md targets
- [x] handoff/wave-{N}.md updated với release summary

## Next steps

- end-wave complete → state DONE
- done-wave để teardown infra + reset
- Wave kế tiếp: wave-{N+1} (nếu plan có) hoặc /apply-cr (nếu có CR)
