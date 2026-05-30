# Events — {boundary}

> File này mô tả **async events** mà boundary `{boundary}` publish (phát ra) và consume (nhận về).
> Use case chi tiết "tại sao cần event này" đã ghi ở FEAT-*.md.
> Broker (Kafka/RabbitMQ/...) chốt ở ADR.

---

## 1. Events boundary này phát ra (Published)

Mỗi event có 1 section dưới đây. Ví dụ: order-mgmt phát ra `OrderConfirmed` khi đơn hàng được xác nhận.

### `{boundary}.{tên-event}.v1`

**Khi nào phát**: Mô tả trigger — vd "Khi order chuyển từ PENDING sang CONFIRMED sau khi payment thành công."

**Schema payload** (JSON):

```json
{
  "event_id": "evt_xxx",            // unique id, dùng để consumer dedupe
  "event_type": "order.confirmed",
  "event_version": "1.0.0",
  "occurred_at": "2026-05-29T10:15:30Z",
  "tenant_id": 42,
  "data": {
    "order_id": "ord_xxx",
    "customer_id": "cus_xxx",
    "total_amount": "199.99"
  }
}
```

**Ai consume**: List các boundary subscribe event này.
- `billing-mgmt` — generate invoice
- `notification` — send email

**Idempotency**: Consumer dedupe bằng `event_id` (tránh xử lý 2 lần khi retry).

**Ordering**: 
- `none` (events có thể đến không đúng thứ tự), HOẶC
- `partitioned by {key}` (events cùng key đảm bảo thứ tự, vd cùng tenant_id)

**Khi lỗi**:
- Retry 3 lần với exponential backoff (1s, 2s, 4s).
- Vẫn fail → ghi vào outbox table, background job retry.
- Stuck > 1h → alert oncall.

---

## 2. Events boundary này nhận về (Consumed)

### `{source-boundary}.{tên-event}.v1` (từ {source-boundary})

**Producer**: Boundary nào phát ra (vd `payment-mgmt`).

**Handler**: Class xử lý event (vd `PaymentSucceededHandler`).

**Boundary làm gì khi nhận**:
1. Lookup entity liên quan (vd order theo payment_id).
2. Update state (vd order PENDING → CONFIRMED).
3. (Optional) Publish event downstream.

**Idempotency**: Dedupe bằng `event_id` lưu trong table `consumed_events`.

**Khi lỗi**:
- Transient error → retry N lần.
- Persistent error → đẩy vào DLQ topic `{boundary}.dlq.{source-event}`.

---

## 3. Versioning

Khi schema thay đổi không backward-compatible:
- Bump version: `v1` → `v2`.
- Producer publish CẢ HAI version trong 1 wave để consumer có thời gian migrate.
- Sau khi tất cả consumer đã migrate xong → drop v1.

## 4. Liên quan

- **Tại sao cần event này** → xem [FEAT-*.md](../feat/) (use case + business rule).
- **Architecture role** → xem [hld-{boundary}.md](../hld/hld-{boundary}.md).
- **Broker choice** → xem [ADR](../adr/) (Kafka vs RabbitMQ vs ...).
- **Sync API** (REST/GraphQL khác async event) → xem [api-{boundary}.md](../api/api-{boundary}.md).
- **Cross-boundary sync contracts** → xem [integrations/](../integrations/).
