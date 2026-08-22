---
type: contract
artifact_kind: integration-internal
contract_id: "INTEG-INT-{{name}}"
status: "DRAFT | ACTIVE | DEPRECATED"
version: 1
consumer: "{{boundary-A}}"      # boundary_id GỌI (MATRIX depends_on chứa producer)
producer: "{{boundary-B}}"      # boundary_id ĐƯỢC GỌI
mode: "sync | async | saga | outbox-relay"
last_reviewed: "{{DATE}}"
---

> Điền NGẮN GỌN: ưu tiên bảng/bullet, không văn xuôi thừa, không lặp. Doc này agent downstream đọc nhiều lần — tiết kiệm context.

# Integration (internal) — `INTEG-INT-{{name}}`

> Tích hợp có hướng giữa HAI boundary backend CÙNG repo: consumer A gọi/subscribe/phụ thuộc producer B. Document calling pattern: identity propagation, retry/timeout, circuit breaker, saga/outbox, ACL mapping. Author ở DESIGN. Khác: `api/api-{{B}}.md` (shape endpoint B) · `events/{{B}}-events.md` (event schema B) · `INTEG-EXT-*.md` (third-party). File này BIND cách gọi A→B tới api/event contract đã có. Single-repo: A,B cùng do mình thiết kế — KHÔNG cần bilateral sign-off, chỉ cần consistency với contract.

---

## 1. Purpose

{{1-2 câu: integration enable capability gì. Vd: "`order-svc` confirm đơn → yêu cầu `payment-svc` capture + chờ xác nhận; saga + timeout + compensating khi fail."}}

---

## 2. Integration mode

| Mode | Khi nào dùng |
|---|---|
| **sync** | A chờ response B trước khi hoàn tất; result cần ngay + latency chấp nhận được |
| **async** (fire-and-forget) | A publish event; B subscribe; không vòng ack. Notification, projection |
| **saga** | Distributed transaction nhiều bước; mỗi bước A trigger B; compensating khi fail |
| **outbox-relay** | A persist intent vào DB; worker forward sang B. Đảm bảo delivery dù A fail |

Integration này = **{{mode}}**.

---

## 3. Underlying contracts consumed

> Integration xây trên ≥1 api/event contract đã có; phải KHỚP shape ở contract đó.

| Underlying contract | Type | Operation |
|---|---|---|
| `api/api-{{B}}.md` | api (REST/gRPC) | `POST /capture` |
| `events/{{B}}-events.md` | event | subscribe `payment.captured.v1` |
| `events/{{B}}-events.md` | event | subscribe `payment.capture-failed.v1` |

---

## 4. Flow

### 4.1 Happy path

```mermaid
sequenceDiagram
  participant A as {{boundary-A}} (consumer)
  participant B as {{boundary-B}} (producer)
  participant Bus as Event Bus
  A->>A: persist saga state = STARTED
  A->>B: POST /capture (Idempotency-Key, X-Correlation-ID, X-On-Behalf-Of)
  B-->>A: 201 Accepted (capture_id, status=PENDING)
  A->>A: saga state = IN_PROGRESS
  B-->>Bus: publish payment.captured.v1 (after settle)
  Bus-->>A: deliver event (dedupe by event_id)
  A->>A: saga state = COMPLETED; emit own event downstream
```

### 4.2 Failure path (compensation)

```mermaid
sequenceDiagram
  participant A
  participant B
  participant Bus
  A->>B: POST /capture
  B-->>A: 5xx OR timeout
  A->>A: retry per §8
  alt retries exhausted
    A->>A: saga = FAILED; compensating action (vd cancel order); publish compensation event
  end
  alt B accept nhưng fail sau
    B-->>Bus: payment.capture-failed.v1
    Bus-->>A: A: saga = FAILED → compensate
  end
```

---

## 5. Identity propagation

| Field | Source | Purpose |
|---|---|---|
| `Authorization` | mTLS HOẶC signed service JWT | Auth A → B |
| `X-On-Behalf-Of` | viewer ID của A (nếu user-initiated) | B dùng cho authz + audit |
| `X-Tenant-ID` | session A | Multi-tenant scope |
| `X-Correlation-ID` | correlation_id A | Trace chain |
| `X-Causation-ID` | command/event ID hiện tại A | Lineage |
| `Idempotency-Key` | A-gen deterministic (hash saga_id) | Replay safety |

**Forbidden**: A act "as system" không lý do + audit. Luôn mang user context khi user-initiated.

---

## 6. Anti-corruption layer (ACL)

A coi B là **external** dù cùng repo. Type B KHÔNG leak vào domain A.

| B's type (từ `api/api-{{B}}.md`) | A's domain type | Mapper location |
|---|---|---|
| `B.PaymentCaptureRequest` | A `PaymentInstruction` (command) | `services/{{prefix-A}}/outbound/{{B}}/mapper.{{ext}}` |
| `B.CaptureResponse` | A `PaymentReceipt` VO | Same |
| `B.CaptureFailedReason` enum | A `PaymentFailureReason` enum (subset) | Same; value lạ → `UNKNOWN` |

Rules: mapper ở outbound adapter A (`outbound/{{B}}-client/`); `domain/` A KHÔNG import type B (`application/` chỉ làm với VO của A); B thêm field A ignore → MINOR.

---

## 7. Saga state (nếu mode=saga)

```sql
CREATE TABLE saga_payment_capture (
  saga_id           UUID PRIMARY KEY,
  order_id          UUID NOT NULL,              -- aggregate A trigger saga
  state             TEXT NOT NULL,              -- STARTED|IN_PROGRESS|COMPLETED|FAILED|COMPENSATING|COMPENSATED
  capture_id        UUID,
  attempt_count     INT  NOT NULL DEFAULT 0,
  last_error        TEXT,
  tenant_id         UUID NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL,
  updated_at        TIMESTAMPTZ NOT NULL,
  UNIQUE (order_id, tenant_id)                  -- 1 saga / order
);
```

**State transitions**:
```
STARTED → IN_PROGRESS → COMPLETED
   │            └─→ FAILED → COMPENSATING → COMPENSATED
   └─→ FAILED (retry exhausted trước khi B accept)
```

**Compensating action** (saga FAILED): update aggregate (vd order PAYMENT_FAILED) · emit compensation event · notify user qua FE (nếu có) · mark COMPENSATED.

---

## 8. Retry policy (sync)

| Aspect | Value |
|---|---|
| Retry on | 5xx, 429, network timeout |
| KHÔNG retry | 4xx khác (except 429) — caller bug, không transient |
| Strategy | Exponential backoff + jitter; initial 100ms / max 30s; max retries 3 |
| Total budget | Saga timeout {{5 phút}} → FAILED → compensate |

`Idempotency-Key` PHẢI giống qua mọi retry — `= hash(saga_id)` (KHÔNG gồm attempt_count).

---

## 9. Circuit breaker (per-producer)

| Setting | Value |
|---|---|
| Open trigger | 5 fail liên tục HOẶC 50% fail rate / 1 phút |
| Open duration | 30s → half-open probe (1 request; close nếu OK, mở lại nếu fail) |
| Fallback when open | Fast-fail → domain A quyết: queue / fail / degrade |
| Metric | `integration_circuit_state{producer=B, state}` |

---

## 10. Outbox pattern (nếu mode=outbox-relay)

A persist outbound call trong DB, worker drain → commit A + outbound call atomic (commit ⇒ row outbox; worker drain riêng → đảm bảo gửi dù A crash).

```sql
CREATE TABLE outbox_to_{{B}} (
  outbox_id       UUID PRIMARY KEY,
  target          TEXT NOT NULL,         -- "{{B}}:/capture"
  payload_json    JSONB NOT NULL,
  state           TEXT NOT NULL,         -- PENDING|IN_FLIGHT|SENT|FAILED
  attempt_count   INT  NOT NULL DEFAULT 0,
  last_error      TEXT,
  tenant_id       UUID NOT NULL,
  enqueued_at     TIMESTAMPTZ NOT NULL
);
```

```pseudo
loop:
  rows = SELECT * FROM outbox_to_B WHERE state=PENDING LIMIT 100
  for row: mark IN_FLIGHT; try: call B → SENT; except: attempts++; if > max → FAILED + alert; else retry
```

---

## 11. Versioning + backward compatibility

**Additive (MINOR — dev trong wave)**: B thêm field optional / error code (A coi unknown = transient); A dùng field optional mới của B.

**Breaking → WAVE SAU** (không sửa tại chỗ): lùi `/domain` sửa hợp đồng, `/approve-document` khoá lại, wave kế giao bản mới. Consumer đang chạy phải còn chạy được suốt lúc đó — luật cộng-trước-xoá-sau ở `tracking/BC-LEDGER.md §2`: B xoá field A dùng / đổi semantics / status code; đổi mode. Breaking → re-design CẢ A và B cùng amendment (single-repo: 1 mình sửa cả hai); deprecation window chốt khi CR.

---

## 12. Performance characteristics

| Aspect | Value |
|---|---|
| p99 round-trip (A↔B) | < {{500ms}} |
| Saga completion p99 | < {{5s}} |
| Outbox drain lag | < {{30s}} enqueue → sent |
| Throughput | ≥ {{100 sagas/s}} |

---

## 13. Failure mode matrix

| Scenario | A's behavior |
|---|---|
| B sync 5xx / timeout | Retry §8 |
| B sync 4xx | No retry; FAILED; compensate nếu saga |
| B accept nhưng event missing (sau T) | Polling fallback HOẶC FAILED → compensate |
| B event A subscribe không tới | Subscriber timeout (saga timeout) → FAILED |
| A crash giữa saga | Restart: scan IN_PROGRESS saga > T → resume / compensate |
| B gửi compensating event | A handle + reverse local state |

---

## 14. Observability

| Signal | Specifics |
|---|---|
| Trace | Saga span A propagate sang B; child span per outbound call |
| Metric | `integration_{{name}}_call_total{producer,status}`, `..._saga_state_total{state}`, `..._outbox_lag_seconds`, `..._circuit_state{producer,state}` |
| Log | Per call: `correlation_id`, `saga_id`, `idempotency_key`, `attempt_count`, result |
| Audit | User-initiated: log on-behalf-of viewer |

---

## 15. Testing

- **Component (A's side)**: mock B client; happy + mỗi failure (5xx, 4xx, timeout, no-event); saga transitions; compensating action.
- **Integration**: real B trong `docker-compose` test env; full saga happy + ≥1 failure-path có compensation; idempotency replay.
- **Contract**: outbound call A khớp `api/api-{{B}}.md`; event handler khớp `events/{{B}}-events.md` (`test-execute`). **Chaos**: inject B fail/latency staging.

---

## 16. Anti-patterns (forbidden)

- (cấm) Distributed transaction 2PC (dùng saga/outbox) · A đọc DB của B trực tiếp (phải qua contract) · domain A import type B (skip ACL)
- (cấm) Synchronous call trong DB transaction (deadlock) · retry không idempotency key (duplicate) · retry vô hạn (phải max + circuit breaker)
- (cấm) Saga không persist state (mất khi restart) · event subscribe không dedupe (double-effect) · forge identity service-to-service không audit · saga step không định nghĩa compensating action

---

## 17. References

- Underlying: `api/api-{{B}}.md`, `events/{{B}}-events.md` · HLD: `hld/hld-{{A}}.md`, `hld/hld-{{B}}.md`
- MATRIX: `harness/SERVICE-BOUNDARY-MATRIX.json` (`depends_on`) · Convention: `ref-backend-restclient` / `ref-backend-kafka` · KG: `integrations[]` trong `knowledge-base/{{A}}.knowledge-graph.yaml`

---

## 18. Change log

| Date | Version | Change | Severity | Author |
|---|---|---|---|---|
| {{DATE}} | 1 | Initial draft | — | solution-architect |
