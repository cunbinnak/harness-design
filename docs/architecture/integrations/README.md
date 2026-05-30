# Integrations

Sync contracts giữa các service / boundary. Async (event-based) sống ở [events/](../events/).

## Hai loại integration

| Loại | File pattern | Khi nào dùng |
|------|--------------|--------------|
| **External (EXT)** | `INTEG-EXT-{provider}.md` + (optional) folder `INTEG-EXT-{provider}/` chứa docs provider | Tích hợp với hệ thống bên ngoài (Stripe, OnePay, Twilio, …) |
| **Internal (INT)** | `INTEG-INT-{caller}-to-{callee}.md` | Tích hợp giữa các boundary nội bộ (BFF↔backend, backend↔backend, FE↔BFF, …) |

## Cấu trúc folder

```
docs/architecture/integrations/
├── README.md
├── TEMPLATE.integration-external.md
├── TEMPLATE.integration-internal.md
├── INTEG-EXT-onepay.md              ← summary spec (~150 dòng)
├── INTEG-EXT-onepay/                ← (optional) docs provider
│   ├── api-reference.pdf
│   ├── sandbox-credentials.md
│   ├── sample-code/
│   └── notes-internal.md
├── INTEG-EXT-twilio.md
├── INTEG-EXT-twilio/
└── INTEG-INT-bff-order-to-order-mgmt.md
```

External có folder docs để chứa PDF/sample code/notes nội bộ provider cung cấp.
Internal chỉ file summary (knowledge đã trong repo qua HLD/API).

## Khi nào tạo

Intake step 3 (solution-architect) tạo file integrations cho mọi sync dependency:
- Mỗi external provider → 1 file INTEG-EXT.
- Mỗi cross-boundary sync call → 1 file INTEG-INT.

## File chứa gì

**External (INTEG-EXT-*)**:
- Provider info (URL, version, sandbox vs prod)
- Auth method (API key, OAuth, mTLS)
- Endpoints sử dụng + rate limit + SLA
- Webhook handling (nếu có)
- Cost model (per call, per month, …)
- Error handling + retry strategy

**Internal (INTEG-INT-*)**:
- Caller boundary + Callee boundary
- Direction (caller → callee)
- Protocol (HTTP/REST, gRPC, GraphQL)
- Endpoints + auth (mTLS, JWT)
- Idempotency strategy
- Retry + circuit breaker + timeout
- Cache strategy (nếu có)

## Workflow

- Intake step 3: solution-architect viết integration spec.
- Dev: dev-agent implement client theo spec.
- Review: review agent verify code khớp spec.
- KG: integrations append vào `knowledge-base/{prefix}-{boundary}.knowledge-graph.yaml` section `integrations[]` + `dependencies.outbound[]` + `dependencies.inbound[]`.

## Naming

- External: `INTEG-EXT-stripe.md`, `INTEG-EXT-twilio.md`, `INTEG-EXT-keycloak.md`
- Internal: `INTEG-INT-bff-order-to-order-mgmt.md` (caller-to-callee)

## Versioning

External: theo version provider (vd Stripe API 2024-06-20).
Internal: theo version contract (vd v1, v2 trong path /api/v1/...).

## Liên quan

- [api-{boundary}.md](../api/) — API spec của từng boundary (callee side)
- [events/](../events/) — async event contracts (khác sync)
- [hld-{boundary}.md](../hld/) — high-level design (nơi integration role)
- [knowledge-base/{prefix}-{boundary}.knowledge-graph.yaml](../../../knowledge-base/) — integrations, dependencies sections
