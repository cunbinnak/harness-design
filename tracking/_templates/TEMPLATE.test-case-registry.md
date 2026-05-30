# Test Case Registry — wave-{N}

> Wave: wave-{N} ({wave-title})
> Features: FEAT-001, FEAT-002, ...
> Created: {date}
> Created by: test-plan-agent
> Boundaries: {boundary-list}

---

## Smoke Tests (must pass before other tests)

### TC-S01: Health check

```yaml
type: auto
boundary: all
feature: infrastructure
ac: N/A
priority: P0
```

**Pre-condition**: `docker-compose up -d` completed, all services healthy.

**Steps**:
1. `curl http://localhost:8080/health`

**Expected**: HTTP 200, body `{"status":"ok"}`.

**Data setup**: none.

**Cleanup**: none.

---

### TC-S02: Auth token valid

```yaml
type: auto
boundary: auth
feature: FEAT-001
ac: FEAT-001:AC-1
priority: P0
```

**Pre-condition**: auth service up + seed user trong DB.

**Steps**:
1. POST `/v1/auth/login` với `{"email":"admin@dev.local","password":"dev-password"}`

**Expected**: HTTP 200 + body chứa `access_token`.

---

## Integration Tests — FEAT-{NNN}

> AC liên quan: FEAT-{NNN}:AC-{M}

### TC-I01: Create entity success

```yaml
type: auto
boundary: {boundary}
feature: FEAT-{NNN}
ac: FEAT-{NNN}:AC-1
priority: P1
```

**Pre-condition**: auth token (TC-S02), tenant `demo-tenant` trong DB.

**Steps**:
1. POST `/v1/{resource}` với valid payload
2. Verify HTTP 201
3. GET `/v1/{resource}/{id}` verify response

**Expected**: 201 + id returned, GET returns same entity.

### TC-I02: Validation 400

```yaml
type: auto
boundary: {boundary}
feature: FEAT-{NNN}
ac: FEAT-{NNN}:AC-2
priority: P1
```

**Steps**:
1. POST `/v1/{resource}` với payload thiếu required field

**Expected**: HTTP 400, body chứa `code: VALIDATION_ERROR`.

### TC-I03: Auth required

```yaml
type: auto
boundary: {boundary}
feature: FEAT-{NNN}
ac: FEAT-{NNN}:AC-3
priority: P0
```

**Steps**:
1. POST `/v1/{resource}` KHÔNG có Authorization header

**Expected**: HTTP 401, body chứa `code: UNAUTHORIZED`.

---

## E2E Tests (FE flows) — FEAT-{NNN}

### TC-E01: Create + view {entity}

```yaml
type: auto
boundary: fe-{name}
feature: FEAT-{NNN}
ac: FEAT-{NNN}:AC-{M}
priority: P1
framework: playwright
```

**Steps**:
1. Login với credential test
2. Navigate to /resource
3. Click "Create new"
4. Fill form + submit
5. Verify item xuất hiện trong list

**Expected**: Item visible với name vừa tạo, screenshot saved.

### TC-E02: PDF print preview

```yaml
type: manual
boundary: fe-{name}
feature: FEAT-{NNN}
ac: FEAT-{NNN}:AC-{M}
priority: P2
```

**Steps**:
1. Open entity detail
2. Click "Print" button
3. Verify PDF preview opens

**Expected**: PDF render đúng layout + data.

---

## Manual UAT Tests (stakeholder)

### TC-M01: Business flow {X}

```yaml
type: manual
boundary: cross-cutting
feature: FEAT-{NNN}
ac: FEAT-{NNN}:AC-{M}
priority: P1
verifier: stakeholder
```

**Steps**:
1. Login as stakeholder role
2. Execute business flow steps (per UAT script)
3. Verify final state đúng nghiệp vụ

**Expected**: Stakeholder confirm OK.

### TC-M02: Edge case A

```yaml
type: manual
boundary: {boundary}
feature: FEAT-{NNN}
ac: FEAT-{NNN}:AC-{M}
priority: P2
verifier: QA
```

**Steps**:
1. Input boundary value (max/min)

**Expected**: Handle gracefully, no crash.

---

## Regression Tests

> Test bug fix từ wave trước (nếu có).

### TC-R01: BUG-{NNN} fix

```yaml
type: auto
boundary: {boundary}
feature: regression
ref_bug: BUG-{NNN}
priority: P0
```

**Verify**: Regression không xuất hiện lại sau fix.

---

## Coverage matrix

| FEAT:AC | TCs covering | Auto count | Manual count |
|---------|--------------|------------|--------------|
| FEAT-001:AC-1 | TC-S02, TC-I01 | 2 | 0 |
| FEAT-001:AC-2 | TC-I02 | 1 | 0 |
| FEAT-001:AC-3 | TC-I03 | 1 | 0 |
| FEAT-002:AC-1 | TC-E01, TC-M01 | 1 | 1 |
| ... | ... | ... | ... |

**Total**: {N} TCs ({auto} auto, {manual} manual). AC coverage: 100%.
