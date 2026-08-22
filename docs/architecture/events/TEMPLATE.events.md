---
type: contract
artifact_kind: event-contract
boundary: "{{boundary-name}}"   # boundary_id producer (kind backend), theo MATRIX
status: "DRAFT | ACTIVE | DEPRECATED"
version: 1
last_reviewed: "{{DATE}}"
---

> Điền NGẮN GỌN: ưu tiên bảng/bullet, không văn xuôi thừa, không lặp. Doc này agent downstream đọc nhiều lần — tiết kiệm context.

# Events — `{{boundary}}` (produce + subscribe)

> 1 file / boundary backend: gom MỌI domain event boundary **phát** (§3+) và **nhận** (§9). Pub/sub async, at-least-once — subscriber dedupe theo `event_id` (idempotent handler bắt buộc). Author ở DESIGN. Subscriber = boundary cùng repo (MATRIX `consumed_by`); pattern async cross-boundary cũng ghi ở `integrations/INTEG-INT-*.md` (mode=async).

---

## 1. Tổng quan

| Aspect | Value |
|---|---|
| Producer | `{{boundary}}` (kind backend) |
| Bus | {{Kafka / NATS / RabbitMQ}} (chốt ở ADR) |
| Topic convention | `{{domain}}.{{entity}}.{{action}}.v{{N}}` (vd `payment.refund.issued.v1`) |
| Delivery | At-least-once — subscriber dedupe theo `event_id` |
| Serialization | JSON (envelope §2), `snake_case` |
| Events phát / nhận | §3+ / §9 |

---

## 2. Envelope schema (CHUNG mọi event)

Mọi event dùng envelope này (chỉ `payload` khác):

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["event_id","event_type","event_version","aggregate_id","occurred_at","producer","tenant_id","payload"],
  "properties": {
    "event_id":       { "type": "string", "format": "uuid" },
    "event_type":     { "type": "string", "description": "vd payment.refund.issued" },
    "event_version":  { "type": "string", "pattern": "^v\\d+$" },
    "aggregate_id":   { "type": "string", "format": "uuid" },
    "tenant_id":      { "type": "string", "format": "uuid" },
    "occurred_at":    { "type": "string", "format": "date-time" },
    "producer":       { "const": "{{boundary}}" },
    "correlation_id": { "type": "string", "format": "uuid" },
    "causation_id":   { "type": "string", "format": "uuid" },
    "payload":        { "type": "object" }
  },
  "additionalProperties": false
}
```

| Field | Nghĩa |
|---|---|
| `event_id` | Globally unique. **Subscriber dedupe theo field này** (idempotency key). |
| `event_type` | Stable id; = suffix topic. |
| `event_version` | Schema version; bump khi breaking. |
| `aggregate_id` | Ordering + partitioning (§3.x). |
| `tenant_id` | Tenant scope (bắt buộc — subscriber honor để isolate). |
| `occurred_at` | Thời điểm event xảy ra (semantic), KHÔNG phải enqueue time. |
| `producer` | Boundary phát. |
| `correlation_id` | Request gốc khởi đầu chuỗi (trace). |
| `causation_id` | Event/command trực tiếp gây ra event này (§4). |
| `payload` | Domain data riêng event (§3.x). |

---

## 3. Events phát

> Lặp §3.x cho MỖI event phát: topic, trigger, payload schema, ordering, idempotency, consumers.

### 3.1 Event: `{{payment.refund.issued.v1}}`

| Aspect | Value |
|---|---|
| Topic | `payment.refund.issued.v1` |
| Trigger | {{State change phát — vd "refund settle thành công với provider"}} |
| `aggregate_id` | = `{{refund_id}}` |
| Partition key | `aggregate_id` ⇒ ordering per-aggregate |
| Ordering | Per-partition theo `aggregate_id`; KHÔNG global; subscriber tolerate out-of-order cross-aggregate |
| Retention | {{7 ngày}} |
| Idempotency key (consumer) | `event_id` |
| Produce timing | **After-commit** (outbox, §8) |

**Payload schema** (JSON Schema draft-07):

```json
{
  "type": "object",
  "required": ["refund_id", "payment_id", "amount", "settled_at"],
  "properties": {
    "refund_id":  { "type": "string", "format": "uuid" },
    "payment_id": { "type": "string", "format": "uuid" },
    "amount": {
      "type": "object",
      "required": ["value", "currency"],
      "properties": {
        "value":    { "type": "string", "pattern": "^\\d+(\\.\\d{1,2})?$" },
        "currency": { "type": "string", "pattern": "^[A-Z]{3}$" }
      },
      "additionalProperties": false
    },
    "settled_at":  { "type": "string", "format": "date-time" }
  },
  "additionalProperties": false
}
```

**Consumers**:

| Subscriber (boundary_id) | Kind | Handler | Effect |
|---|---|---|---|
| `{{notification-boundary}}` | backend | `RefundIssuedHandler` | Gửi email khách |
| `{{reconciliation-boundary}}` | backend | `LedgerUpdater` | Cập nhật ledger |

**Payload rules**: field `snake_case`; Money = `{ value: string-decimal, currency: ISO-4217 }` (KHÔNG raw float); datetime ISO-8601 UTC; KHÔNG raw input chưa validate; KHÔNG PII chưa redact (§7).

### 3.2 Event: `{{...}}`

{{Lặp block §3.1}}

---

## 4. Causation chain (lineage)

| Caused by | `causation_id` = |
|---|---|
| Command `{{RefundCreate}}` | command id |
| Event cha `{{PaymentCaptured}}` | parent `event_id` |
| External webhook | webhook receipt id |

Subscriber trace lineage = follow `causation_id` ngược qua log/event store.

---

## 5. Consumer expectations (mọi subscriber)

PHẢI: dedupe theo `event_id` (idempotent — re-delivery KHÔNG double-effect) · tolerate replay · honor `tenant_id` · treat envelope immutable · handle out-of-order cross-aggregate (reorder theo `occurred_at` nếu cần).

NÊN: log `event_id`+`correlation_id` · emit metric per kết quả · ack CHỈ sau khi persist state change.

---

## 6. Idempotency + ordering (chi tiết)

- **Dedupe store**: giữ `(event_id, tenant_id)` đã xử lý (table/Redis TTL ≥ retention broker). Đã thấy → ignore + ack.
- **Ordering**: chỉ per-partition (= per `aggregate_id`). Cần thứ tự cross-aggregate → reorder consumer-side theo `occurred_at` hoặc redesign aggregate.

```pseudo
on event:
  if seen(event.event_id, event.tenant_id): ack(); return
  handle(event)                  # idempotent business effect
  mark_seen(event.event_id, event.tenant_id); ack(event)
```

---

## 7. Security

- KHÔNG secrets/token trong payload.
- PII: redact/mask hoặc ref bằng aggregate-id (`ref-backend-logging`).
- Encryption: TLS in-transit; at-rest theo config broker.
- AuthN/AuthZ: producer auth tới bus; subscriber authorized per topic (ACL broker).

---

## 8. Failure modes + retry

| Mode | Handling |
|---|---|
| Producer fail sau DB-commit, trước publish | **Outbox**: persist event row cùng tx; worker drain → publish (after-commit) |
| Subscriber crash giữa handle | Re-delivery → idempotent handler (§6) |
| Broker down | Producer-side outbox/retry |
| Poison message (parse fail) | Retry N → **DLT** + alert |
| Schema drift | Contract test (`test-execute`); breaking → version bump (§10) |

**Retry consumer-side**: backoff + jitter, max N → DLT. KHÔNG retry vô hạn (block partition).

---

## 9. Events nhận (subscribe)

> Event boundary này SUBSCRIBE từ boundary khác; mỗi dòng ref contract event producer.

| Topic subscribe | Producer (boundary_id) | Contract | Handler | Effect |
|---|---|---|---|---|
| `{{order.confirmed.v1}}` | `{{order-boundary}}` | `events/{{order-boundary}}-events.md` §3.x | `{{OrderConfirmedHandler}}` | {{tạo refund eligibility}} |

---

## 10. Versioning + backward compatibility

**Additive (MINOR — dev trong wave)**: thêm field payload/envelope optional; subscriber ignore field lạ.

**Breaking → WAVE SAU** (không sửa tại chỗ): lùi `/domain` sửa hợp đồng, `/approve-document` khoá lại, wave kế giao bản mới. Consumer đang chạy phải còn chạy được suốt lúc đó — luật cộng-trước-xoá-sau ở `tracking/BC-LEDGER.md §2`: xoá field / đổi type / optional→required / rename / đổi `event_type`.

Breaking → bump `event_version` → topic mới `.v2`. Producer dual-publish v1+v2 qua deprecation window (default 2 wave); subscriber migrate xong → ngừng v1.

---

## 11. Performance

| Aspect | Value |
|---|---|
| Producer publish p99 | < {{50ms}} |
| Subscriber processing budget | < {{2s}} / event |
| Throughput peak | ≥ {{1000 events/s}} |
| Lag tolerance | < {{30s}} emit → delivery |

---

## 12. References

- HLD: `hld/hld-{{boundary}}.md` · API: `api/api-{{boundary}}.md` · Data: `data-model/data-model-{{boundary}}.md`
- Async cross-boundary: `integrations/INTEG-INT-*.md` (mode=async) · Convention: `ref-backend-kafka` · KG: `knowledge-base/{{boundary}}.knowledge-graph.yaml`

---

## 13. Change log

| Date | Version | Change | Severity | Author |
|---|---|---|---|---|
| {{DATE}} | 1 | Initial draft | — | solution-architect |
