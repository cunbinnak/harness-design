# INTEG-EXT-{provider}

> Tích hợp với hệ thống bên ngoài.
> **File này chỉ là khung tóm tắt** — chi tiết kỹ thuật phải đọc tài liệu chính thức của provider.

---

## 1. Provider documentation (BẮT BUỘC đọc trước khi implement)

### 1.1 Local docs folder

Nếu provider cung cấp PDF, sample code, hoặc có notes nội bộ → lưu vào folder cùng tên:

```
docs/architecture/integrations/
├── INTEG-EXT-{provider}.md        ← file summary này
└── INTEG-EXT-{provider}/          ← folder docs provider
    ├── api-reference.pdf
    ├── sandbox-credentials.md     (gitignored nếu chứa secret)
    ├── sample-code/
    │   ├── auth-flow.{lang}
    │   └── webhook-verify.{lang}
    └── notes-internal.md          (insights team đã học được)
```

### 1.2 Online docs (links)

Liệt kê tài liệu chính thức online:

| Tài liệu | Link | Note |
|----------|------|------|
| Official API docs | {URL} | Main reference |
| Quick start / Getting started | {URL} | Setup steps |
| Authentication guide | {URL} | Cách auth (HMAC/OAuth/API key) |
| Webhook / Callback guide | {URL} | (nếu có) |
| Sandbox / Test environment | {URL} | Cách test |
| SDK / Client library | {URL/repo} | Official lib (nếu có) |
| Rate limit & SLA | {URL} | |
| Compliance / Security | {URL} | PCI-DSS, GDPR, NAPAS, ... |
| Pricing | {URL} | |
| Changelog | {URL} | Track API version changes |

> Agent implement integration **PHẢI Read các tài liệu trên** (local folder ở § 1.1 hoặc online docs ở § 1.2 qua WebFetch) trước khi code. KHÔNG được đoán API behavior.

## 2. Provider info (overview)

| Field | Value |
|-------|-------|
| Provider name | {Stripe / OnePay / VNPay / Twilio / ...} |
| Provider type | {payment / SMS / OAuth / email / ...} |
| API version | {date hoặc semver} |
| Region | {US / VN / EU / ...} |
| Compliance | {PCI-DSS / GDPR / NAPAS / ...} |

## 3. Use case (tóm tắt — detail ở FEAT)

Boundary nào dùng provider này và tại sao (1-2 dòng):

```
Vd: boundary `payment-mgmt` dùng OnePay để xử lý thanh toán cho user VN.
    Lý do chọn (vs Stripe): hỗ trợ NAPAS, ATM nội địa, QR code.
```

Detail use case → xem [FEAT-*.md](../feat/).

## 4. Decisions cần chốt (theo provider docs)

Liệt kê quyết định kiến trúc dựa trên docs provider:

| Decision | Lựa chọn | Lý do | Reference |
|----------|----------|-------|-----------|
| Auth method | {HMAC / OAuth / API key} | {lý do} | {link provider docs} |
| Flow type | {sync / redirect / async callback / hybrid} | {lý do} | {link} |
| Callback handling | {webhook / IPN / polling} | {lý do} | {link} |
| Idempotency strategy | {provider event_id / boundary-side dedupe} | {lý do} | {link} |
| Error retry | {provider recommend backoff} | | {link} |
| Sandbox vs prod toggle | {env var / config file} | | |

## 5. Credentials

| Credential | Storage | Rotation |
|-----------|---------|----------|
| `{PROVIDER_API_KEY}` | env var / secret manager | {N tháng} |
| `{PROVIDER_HMAC_SECRET}` | secret manager | {N tháng} |
| `{PROVIDER_WEBHOOK_SECRET}` | secret manager | {N tháng} |

## 6. Endpoints + actions (tóm tắt)

Liệt kê endpoint chính boundary sẽ gọi. Chi tiết payload, response, error codes → đọc provider docs.

| Endpoint | Action boundary | Reference |
|----------|-----------------|-----------|
| {endpoint 1} | {what for} | {link} |
| {endpoint 2} | {what for} | {link} |

## 7. Callback (nếu provider gọi về)

- Endpoint nhận: `{boundary}/webhooks/{provider}` hoặc `{boundary}/ipn/{provider}`
- Verify method: {signature / IP whitelist / timestamp}
- Events nhận: liệt kê (chi tiết payload đọc provider docs)
- Idempotency: dedupe bằng `{provider}_event_id`

## 8. Architecture concerns (boundary-side)

- Circuit breaker: open khi error rate > N% trong T phút
- Timeout: connect {N}s, read {N}s
- Retry policy: {N retries, backoff strategy}
- Fallback khi provider down: {queue / cache / fail-fast}
- Logging: log request_id, correlation_id, KHÔNG log credentials

## 9. Test strategy

- Sandbox / test environment: {URL + credentials}
- Test data provider cung cấp: {test cards / phones / tokens}
- E2E test scenarios: {liệt kê}
- Mock provider khi nào (unit test): {có/không}

## 10. Liên quan

- **Provider docs (bắt buộc đọc)**: xem § 1
- **Use case detail**: [FEAT-*.md](../feat/)
- **HLD role**: [hld-{boundary}.md](../hld/) 
- **API wrap internal**: [api-{boundary}.md](../api/) (boundary expose facade)
- **KG**: `integrations[]` trong `knowledge-base/{prefix}-{boundary}.knowledge-graph.yaml`
