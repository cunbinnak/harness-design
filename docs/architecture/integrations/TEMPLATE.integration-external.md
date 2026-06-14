---
type: contract
artifact_kind: integration-external
contract_id: "INTEG-EXT-{{provider}}"
status: "DRAFT | ACTIVE | DEPRECATED"
version: 1
consumer: "{{boundary-name}}"        # boundary_id GỌI provider (MATRIX)
provider: "{{Stripe | OnePay | VNPay | Twilio | ...}}"
provider_type: "{{payment | SMS | OAuth | email | KYC | ...}}"
mode: "sync | redirect | async-callback | hybrid"
last_reviewed: "{{DATE}}"
---

> Điền NGẮN GỌN: ưu tiên bảng/bullet, không văn xuôi thừa, không lặp. Doc này agent downstream đọc nhiều lần — tiết kiệm context.

# Integration (external) — `INTEG-EXT-{{provider}}`

> Tích hợp boundary backend với third-party NGOÀI repo: calling pattern + auth + retry/timeout + circuit breaker + fallback + ACL mapping + callback. File này là khung hợp đồng — payload/error chính xác PHẢI đọc docs provider (§1), KHÔNG đoán API. Author ở DESIGN. Khác INTEG-INT (cùng repo): B là third-party, mình KHÔNG control schema/SLA → ACL + fallback + circuit breaker BẮT BUỘC.

---

## 1. Provider documentation (BẮT BUỘC đọc trước khi implement)

### 1.1 Local docs folder

```
docs/architecture/integrations/
├── INTEG-EXT-{{provider}}.md        ← file này
└── INTEG-EXT-{{provider}}/          ← folder docs provider
    ├── api-reference.pdf
    ├── sandbox-credentials.md        (gitignored nếu chứa secret)
    ├── sample-code/{auth-flow,webhook-verify}.{{lang}}
    └── notes-internal.md
```

### 1.2 Online docs (links)

| Tài liệu | Link | Note |
|---|---|---|
| Official API docs | {{URL}} | Main reference |
| Authentication guide | {{URL}} | HMAC/OAuth/API key |
| Webhook / Callback guide | {{URL}} | nếu có |
| Sandbox / Test env | {{URL}} | Cách test |
| SDK / Client library | {{URL/repo}} | nếu có |
| Rate limit & SLA | {{URL}} | |
| Compliance / Security | {{URL}} | PCI-DSS / GDPR / NAPAS |
| Pricing · Changelog | {{URL}} | Track API version |

> Agent implement PHẢI Read tài liệu trên (local §1.1 hoặc online §1.2 qua WebFetch) trước khi code.

---

## 2. Provider info (overview)

| Field | Value |
|---|---|
| Provider · Type | {{Stripe / OnePay}} · {{payment / SMS}} |
| API version | {{date / semver}} |
| Region · Compliance | {{US/VN/EU}} · {{PCI-DSS / GDPR / NAPAS}} |
| SLA (provider-stated) | {{uptime % / response time}} |

---

## 3. Use case (detail ở FEAT)

{{Boundary nào dùng provider + tại sao (1-2 dòng). Vd: "`payment-mgmt` dùng OnePay cho user VN — hỗ trợ NAPAS, ATM nội địa, QR." Detail → `feat/FEAT-*.md`.}}

---

## 4. Architecture decisions (theo provider docs)

| Decision | Lựa chọn | Lý do | Reference |
|---|---|---|---|
| Auth method | {{HMAC / OAuth / API key}} | {{lý do}} | {{link}} |
| Flow type | {{sync / redirect / async callback / hybrid}} | {{lý do}} | {{link}} |
| Callback handling | {{webhook / IPN / polling}} | {{lý do}} | {{link}} |
| Idempotency | {{provider event_id / boundary-side dedupe}} | {{lý do}} | {{link}} |
| Error retry | {{theo provider backoff}} | | {{link}} |
| Sandbox/prod toggle | {{env var / config}} | | |

---

## 5. Credentials + secrets

| Credential | Storage | Rotation |
|---|---|---|
| `{{PROVIDER_API_KEY}}` | secret manager (Azure Key Vault) — KHÔNG hardcode | {{N tháng}} |
| `{{PROVIDER_HMAC_SECRET}}` / `{{PROVIDER_WEBHOOK_SECRET}}` | secret manager | {{N tháng}} |

KHÔNG commit secret; KHÔNG log credential. Sandbox vs prod toggle qua env/config (§4).

---

## 6. Operations boundary gọi

> Endpoint chính. Payload/response/error chính xác → đọc provider docs (§1).

| Operation | Endpoint provider | Action | HTTP | Idempotency | Reference |
|---|---|---|---|---|---|
| {{Create charge}} | `POST {{/v1/charges}}` | {{khởi tạo thanh toán}} | sync | header `Idempotency-Key` (provider hỗ trợ?) | {{link}} |
| {{Get status}} | `GET {{/v1/charges/:id}}` | {{poll trạng thái}} | sync | N/A | {{link}} |

---

## 7. Callback (provider gọi về — nếu có)

| Aspect | Value |
|---|---|
| Endpoint nhận | `{{boundary}}/webhooks/{{provider}}` hoặc `/ipn/{{provider}}` |
| Verify | {{signature HMAC / IP whitelist / timestamp tolerance}} — REJECT nếu fail |
| Events nhận | {{liệt kê — payload đọc provider docs}} |
| Idempotency | Dedupe theo `{{provider}}_event_id` (provider có thể redeliver) |
| Response | Ack nhanh (2xx) SAU khi persist; xử lý nặng → async queue |
| Replay/order | Webhook out-of-order / replay → handler idempotent + check state hiện tại |

---

## 8. Identity + tenant propagation

| Field | Mục đích |
|---|---|
| `Idempotency-Key` (nếu provider hỗ trợ) | Replay safety phía provider |
| `X-Correlation-ID` (nội bộ) | Trace request user → call provider → callback |
| tenant context | Map provider account/sub-merchant ↔ `tenant_id` nội bộ |

KHÔNG forward JWT user nội bộ ra provider. Boundary auth tới provider bằng credential riêng (§5).

---

## 9. Anti-corruption layer (ACL)

Provider type KHÔNG leak vào domain boundary.

| Provider type | Domain type (boundary) | Mapper location |
|---|---|---|
| `{{provider}}.ChargeRequest` | `{{PaymentInstruction}}` (internal command) | `services/{{prefix-boundary}}/outbound/{{provider}}/mapper.{{ext}}` |
| `{{provider}}.ChargeResponse` | `{{PaymentReceipt}}` VO | Same |
| `{{provider}}.error_code` (mở) | `{{PaymentFailureReason}}` enum nội bộ | Same; code lạ → `UNKNOWN` (log) |

Rules: mapper ở outbound adapter; `domain/` KHÔNG import type/SDK provider; provider thêm field → MINOR, mapper ignore.

---

## 10. Resilience (timeout · retry · circuit breaker · fallback)

| Aspect | Value |
|---|---|
| Timeout | connect {{3s}}, read {{10s}} (theo SLA provider) |
| Retry on | 5xx, 429, network timeout — backoff + jitter, max {{3}} |
| KHÔNG retry | 4xx khác (input sai) · operation non-idempotent mà provider chưa hỗ trợ idempotency-key (tránh double-charge) |
| Circuit breaker | Open khi error rate > {{50%}} / {{1 phút}} HOẶC {{5}} fail liên tục; open {{30s}} → half-open probe |
| Fallback khi provider down | {{queue + retry later / cache last-known / fail-fast + báo user}} |
| Degraded UX | {{vd "tạm thời không thanh toán được, thử lại sau" — KHÔNG mất đơn}} |

Metric `integration_circuit_state{provider, state}`; alert khi circuit open kéo dài.

---

## 11. Failure mode matrix

| Scenario | Boundary behavior |
|---|---|
| Provider 5xx / timeout | Retry §10 → circuit nếu lặp → fallback |
| Provider 4xx (input) | No retry; map error → user; KHÔNG double-submit |
| Accept nhưng callback không tới (sau T) | Polling fallback (`GET status`) hoặc mark UNKNOWN → reconcile |
| Callback signature sai | Reject + log security event; KHÔNG xử lý |
| Callback duplicate | Dedupe `{{provider}}_event_id` → ignore |
| Provider đổi API version | Contract test fail → alert; pin version §2 |
| Double-charge risk | Idempotency-key (§6) + check state trước khi gọi |

---

## 12. Observability

| Signal | Specifics |
|---|---|
| Metric | `integration_{{provider}}_call_total{operation,status}`, `..._duration_seconds`, `..._circuit_state{state}`, `..._callback_total{result}` |
| Log | Per call: `correlation_id`, operation, provider status, duration — KHÔNG log credential/PII |
| Trace | Span `ext.{{provider}}.{operation}` |
| Alert | Circuit open kéo dài · callback verify fail spike · error rate > ngưỡng |

---

## 13. Test strategy

- **Sandbox**: {{URL + test credential}} (§1). Test data: {{test cards/phones/tokens}}.
- **Mock** (unit/component): mock provider client — happy + 5xx + 4xx + timeout + callback (valid/invalid signature/duplicate).
- **Integration**: chạy thật trên sandbox ≥1 flow critical (happy + 1 failure + 1 callback).
- **Resilience**: verify circuit breaker open/fallback khi provider down. **Contract**: pin API version; fail → alert.

---

## 14. Versioning + backward compatibility

- Provider thêm field → boundary ignore (ACL §9 bền với additive).
- Provider breaking (đổi semantics / xoá field mình dùng / đổi API version) → re-design boundary (`/apply-cr` từ DONE nếu đã ship). Pin version (§2) + monitor changelog (§1.2).

---

## 15. Anti-patterns (forbidden)

- (cấm) Hardcode credential / log secret · đoán API behavior không đọc provider docs
- (cấm) Retry operation non-idempotent không idempotency-key (double-charge) · retry vô hạn (phải max + circuit breaker)
- (cấm) Xử lý callback không verify signature · callback không dedupe (`{{provider}}_event_id`)
- (cấm) domain import type/SDK provider (skip ACL) · forward JWT user nội bộ ra provider · không định nghĩa fallback khi provider down

---

## 16. References

- Provider docs (BẮT BUỘC): §1 · Use case: `feat/FEAT-*.md` · HLD: `hld/hld-{{boundary}}.md`
- API facade nội bộ: `api/api-{{boundary}}.md` · Convention: `ref-backend-restclient` · KG: `integrations[]` trong `knowledge-base/{{boundary}}.knowledge-graph.yaml`

---

## 17. Change log

| Date | Version | Change | Severity | Author |
|---|---|---|---|---|
| {{DATE}} | 1 | Initial draft | — | solution-architect |
