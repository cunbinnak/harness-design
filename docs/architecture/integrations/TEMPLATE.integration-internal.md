# INTEG-INT-{caller}-to-{callee}

> Tích hợp sync giữa 2 boundary nội bộ. Vd: `bff-order` gọi `order-mgmt` lookup order.
> Async (event) sống ở [events/](../events/), KHÔNG ở đây.
> Use case "tại sao cần" ở FEAT-*.md.

---

## 1. Tổng quan

| Field | Value |
|-------|-------|
| Caller boundary | {caller-boundary} |
| Callee boundary | {callee-boundary} |
| Direction | caller → callee (sync request/response) |
| Protocol | {HTTP/REST | gRPC | GraphQL | tRPC} |
| Auth | {mTLS | JWT bearer | service mesh | API key} |

## 2. Endpoints sử dụng

Caller gọi những endpoint nào của callee. Endpoint detail (request/response schema) ở `api-{callee}.md`.

| Endpoint | Method | Purpose | Reference |
|----------|--------|---------|-----------|
| `/api/v1/orders/{id}` | GET | Lookup order detail | [api-{callee}.md](../api/api-{callee}.md) |
| `/api/v1/orders` | POST | Tạo order | ... |

## 3. Auth model

Cách caller authenticate với callee:

| Method | Khi dùng | Vd |
|--------|----------|-----|
| mTLS | Banking, gov, high security | NAPAS integration |
| JWT bearer (service token) | Standard service-to-service | Most internal calls |
| Service mesh (Istio mTLS) | Có service mesh trong cluster | K8s với Istio |
| API key (service-scoped) | Đơn giản, low security | Internal admin tools |

**Method dùng**: {chọn 1}

**Token propagation**:
- Caller forward user JWT (nếu request từ user-context)? {yes/no}
- Service-to-service token cho non-user calls? {yes/no}
- Header carrying: `Authorization: Bearer ...` + `X-User-Context: ...`

## 4. Resilience

| Concern | Strategy |
|---------|----------|
| Timeout | connect {N}s, read {N}s |
| Retry | {N retries, backoff {linear/exponential}} |
| Circuit breaker | Open khi error rate > N% trong T phút, half-open sau T2s |
| Bulkhead | Connection pool size: {N} |
| Fallback | {cache / default value / fail-fast} khi callee down |

## 5. Idempotency

- Caller có gửi idempotency key không? {yes/no}
- Header: `Idempotency-Key: {uuid}`
- Callee dedupe trong window: {N} hours

## 6. Cache strategy

- Caller có cache response không? {yes/no}
- Cache key: {pattern}
- TTL: {N} seconds
- Invalidation: {time-based / event-driven}

## 7. Observability

Metrics expose ở caller:
- `external_calls_total{callee, status}` — counter
- `external_calls_duration_seconds{callee}` — histogram
- `circuit_breaker_state{callee}` — gauge

Alert thresholds:
- p99 > {N}ms
- Error rate > {N}%
- Circuit breaker open

## 8. Tracing

- Caller propagate trace headers (W3C Trace Context hoặc B3) {yes/no}
- Header: `traceparent`, `tracestate`
- Span name: `{caller} → {callee} {endpoint}`

## 9. Test strategy

- Unit test: mock callee (vd WireMock, MSW).
- Integration test: docker-compose có cả caller + callee.
- Contract test: Pact (nếu áp dụng).
- E2E test: full stack với tất cả boundaries up.

## 10. Liên quan

- **Use case** → [FEAT-*.md](../feat/) (which feature drives this call)
- **Caller HLD** → [hld-{caller}.md](../hld/) (caller uses callee)
- **Callee API** → [api-{callee}.md](../api/) (endpoint spec)
- **KG**:
  - Caller side: `dependencies.outbound[]` trong `knowledge-base/{prefix}-{caller}.knowledge-graph.yaml`
  - Callee side: `dependencies.inbound[]` trong `knowledge-base/{prefix}-{callee}.knowledge-graph.yaml`
