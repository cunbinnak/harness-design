# Bugs — wave-{N}

> Wave: wave-{N} ({wave-title})
> Format: mỗi bug = heading `## BUG-NNN — title` + frontmatter (status, origin, severity, boundary, ...)
> Updated by: test-execute-agent (auto bugs), fix-bugs (manual bugs from MANUAL_TEST)
> Status enum: `open` | `in_progress` | `fixed` | `closed` | `wontfix`
> Origin enum: `auto` (from test-execute) | `manual` (from MANUAL_TEST UAT) | `framework` (tooling)

---

## BUG-001 — Validation 500 instead of 400 on empty payload

```yaml
status: closed
origin: auto
severity: high
boundary: order-mgmt
detected_by: test-execute-agent
detected_at: "{date}"
detected_in: TC-I02
fixed_by: fix-{prefix}-order-mgmt-agent
fixed_at: "{date}"
fix_commit: "abc123"
verified_in: TC-I02 (re-run) + TC-R01 (regression)
```

### Reproduce

```bash
curl -s -w "\n%{http_code}" -X POST http://localhost:8080/v1/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Expected

HTTP 400 với body `{"code":"VALIDATION_ERROR","message":"required fields missing"}`.

### Actual

HTTP 500 với body `{"error":"NullPointerException at OrderService.validate(OrderService.java:42)"}`.

### Root cause

Service không validate request DTO trước khi access fields. `request.getCustomerId()` throw NPE khi payload rỗng.

### Fix

Added `@Valid` annotation trên controller method + `@NotNull` constraint trên `customerId` field trong DTO.

### Regression

TC-R01 added to test-case-registry — verify validation 400 với empty/null fields.

---

## BUG-002 — Order list pagination cursor invalid

```yaml
status: open
origin: manual
severity: medium
boundary: order-mgmt
detected_by: stakeholder (UAT)
detected_at: "{date}"
ac_violated: FEAT-001:AC-5
assigned_to: fix-{prefix}-order-mgmt-agent
```

### Reproduce

1. Login as admin
2. Navigate to /orders
3. Click "Next page" sau khi list > 20 items
4. Cursor parameter invalid → empty list

### Expected

Pagination cursor work, next page hiển thị 20 items kế tiếp.

### Actual

Empty list. Console log shows cursor decode error.

### Notes

UAT bug from MANUAL_TEST. Need fix-bugs chain (fix + review verify).

---

## BUG-003 — FE accessibility violation: color contrast

```yaml
status: in_progress
origin: framework
severity: low
boundary: fe-web
detected_by: axe-core (review-web)
detected_at: "{date}"
detected_in: review-dev (color contrast WCAG AA)
assigned_to: dev-{prefix}-fe-web-agent
```

### Detail

axe-core scan phát hiện:
- Component: `<Button variant="secondary">`
- WCAG criterion: 1.4.3 Contrast (Minimum)
- Foreground: `#999999`, Background: `#FFFFFF`
- Contrast ratio: 2.85 (need >= 4.5 for AA)

### Fix

Update button text color to `#666666` để pass contrast >= 4.5.

---

## Summary

| Status | Count |
|--------|-------|
| Open | 1 (BUG-002) |
| In progress | 1 (BUG-003) |
| Fixed | 0 |
| Closed | 1 (BUG-001) |
| Wontfix | 0 |
| **Total** | **3** |

| Origin | Count |
|--------|-------|
| auto | 1 |
| manual | 1 |
| framework | 1 |

## Notes

- `end-wave` chỉ allow khi status open == 0 (theo gate `no_open_bugs`).
- `fix-bugs` command spawn fix agent + chain review để verify fix không có regression.
- Bug từ MANUAL_TEST có `origin: manual`, từ test-execute có `origin: auto`.
- Bug detect bởi review agent (vd axe-core) có `origin: framework`.
