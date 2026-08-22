---
type: contract
artifact_kind: api-contract
contract_id: "api/{{name}}"
contract_style: "REST | gRPC | GraphQL"
status: "DRAFT | ACTIVE | DEPRECATED"
version: 1
producer: "{{boundary-or-bff-name}}"   # boundary_id (kind backend/bff) sở hữu API, theo MATRIX
consumers: []   # boundary_id consume — đồng bộ MATRIX consumed_by
domain_error_enum: "{{Domain}}ErrorEnum"   # enum domain-error riêng boundary (vd RefundErrorEnum)
last_reviewed: "{{DATE}}"
supersedes: "{{contract-id hoặc 'none'}}"
---

> Điền NGẮN GỌN: ưu tiên bảng/bullet, không văn xuôi thừa, không lặp. Doc này agent downstream đọc nhiều lần — tiết kiệm context.

# API Contract — `api/{{name}}`

> 1 contract / boundary backend (hoặc bff). Shape đầy đủ request/response + error catalog mọi operation. Author ở DESIGN. Sửa additive=MINOR (trong wave); breaking=MAJOR (wave sau, §7). Consumer = boundary khác cùng repo (MATRIX `consumed_by`); pattern cross-boundary → `integrations/INTEG-INT-*.md`.

---

## 1. Purpose

{{1-2 câu: API cho capability/user gì; boundary nào produce/consume.}}

---

## 2. Style + transport

| Aspect | Value |
|---|---|
| Style | {{REST / gRPC / GraphQL}} |
| Transport | {{HTTPS / HTTP/2+TLS / WebSocket}} |
| Base path | `/api/v1` (version trong path; host per-env ở config, KHÔNG hardcode) |
| Content-Type | `application/json; charset=utf-8` |
| Auth | {{Bearer JWT / mTLS / API key}} — verify ở `application/` layer |
| Tenant scope | Mọi request mang `X-Tenant-ID` (hoặc JWT claim); BE filter theo tenant (bắt buộc) |
| Idempotency | Mutation BẮT BUỘC header `Idempotency-Key` (UUID); cache 24h; replay key+payload → cùng response (§5) |
| Rate limit | {{1000 req/phút/tenant}}; vượt → `429` + `Retry-After` (§6) |
| Pagination | Cursor-based: `cursor` (opaque) + `limit` (max 100, default 20) (§3.x list) |
| Versioning | Version trong base path; breaking → `/api/v2`, v1 giữ qua deprecation window (§7) |
| Correlation | `X-Correlation-ID` mỗi request; echo về `request_id` trong error envelope |

---

## 3. Operations

> Lặp §3.x cho MỖI operation. Request+response shape đầy đủ (JSON Schema draft-07 hoặc proto). Error per-op ref `{{Domain}}ErrorEnum` (§4.2) + generic (§4.1).

### 3.1 {{Operation-1 — vd POST /refunds}}

| Aspect | Value |
|---|---|
| Method · Path | `POST /api/v1/refunds` |
| Mô tả | {{1 câu}} |
| Auth | Bearer JWT, role `{{refund-issuer}}` |
| Idempotency | Bắt buộc (`Idempotency-Key`) |
| Rate-limit bucket | {{per-tenant mutation}} |

**Request body** (JSON Schema draft-07):

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["payment_id", "amount", "reason"],
  "properties": {
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
    "reason": { "type": "string", "minLength": 5, "maxLength": 500 }
  },
  "additionalProperties": false
}
```

**Response `201 Created`**:

```json
{ "id": "{{uuid}}", "payment_id": "{{uuid}}", "amount": { "value": "12.50", "currency": "USD" }, "status": "PENDING", "created_at": "{{ISO8601}}" }
```

**Error responses** (envelope §4.1; `error.code` từ generic §4.1 HOẶC `{{Domain}}ErrorEnum` §4.2):

| HTTP | error.code | Nguồn | Nghĩa | Recoverable |
|---|---|---|---|---|
| 400 | `VALIDATION_FAILED` | generic | Body fail schema | Yes — sửa input |
| 401 | `UNAUTHENTICATED` | generic | Token thiếu/sai | Yes — re-auth |
| 403 | `FORBIDDEN` | generic | Thiếu role | No |
| 409 | `IDEMPOTENCY_CONFLICT` | generic | Cùng key, payload khác | No |
| 422 | `REFUND_TOO_LARGE` | `{{Domain}}ErrorEnum` | Amount > số dư hoàn (BR-xxx) | Yes |
| 429 | `RATE_LIMITED` | generic | Vượt quota (§6) | Yes — backoff |
| 500 | `INTERNAL_ERROR` | generic | Lỗi server | Yes — retry |
| 503 | `DEPENDENCY_UNAVAILABLE` | generic | Downstream down | Yes |

### 3.2 {{Operation-2 — vd GET /refunds/:id}}

| Aspect | Value |
|---|---|
| Method · Path | `GET /api/v1/refunds/{id}` |
| Auth | Bearer JWT, role `{{refund-viewer}}` |
| Idempotency | N/A (read) |

**Response `200 OK`**: {{schema như §3.1 response, đầy đủ field}}. **Error**: `401`, `403`, `404 NOT_FOUND`, `429`, `500`.

### 3.3 {{List op — vd GET /refunds (paginated)}}

| Aspect | Value |
|---|---|
| Method · Path | `GET /api/v1/refunds?status=&cursor=&limit=` |
| Query params | `status` (optional), `cursor` (opaque, optional), `limit` (1–100, default 20) |

**Response `200 OK`** (envelope pagination chuẩn — GIỐNG mọi list op trong repo):

```json
{ "items": [ { /* object như §3.1 response */ } ], "page": { "next_cursor": "{{opaque-or-null}}", "limit": 20, "has_more": true } }
```

`next_cursor=null` ⇒ hết trang; client KHÔNG decode cursor (opaque). Cursor encode vị trí ổn định (vd `created_at+id`), KHÔNG offset.

---

## 4. Error model (envelope + codes)

### 4.1 Common error envelope (IDENTICAL mọi boundary)

```json
{ "error": { "code": "{{UPPER_SNAKE}}", "message": "{{human-readable}}", "details": [ { "field": "{{path}}", "issue": "{{field-level code}}" } ] }, "request_id": "{{correlation-id echo}}", "timestamp": "{{ISO8601}}" }
```

Client map `error.code` → i18n; KHÔNG parse `message`. `details[]` optional cho field-level validation.

**Generic codes — GIỐNG mọi boundary** (định nghĩa 1 lần ở convention; mỗi op chỉ ref):

| HTTP | code | Khi nào |
|---|---|---|
| 400 | `VALIDATION_FAILED` | Body/param fail schema; chi tiết `details[]` |
| 401 | `UNAUTHENTICATED` | Token thiếu/hết hạn/sai |
| 403 | `FORBIDDEN` | Auth rồi nhưng thiếu role/scope |
| 404 | `NOT_FOUND` | Resource không tồn tại (hoặc khác tenant — KHÔNG leak) |
| 409 | `CONFLICT` | State conflict chung (optimistic lock) |
| 409 | `IDEMPOTENCY_CONFLICT` | Cùng key, payload khác |
| 429 | `RATE_LIMITED` | Vượt quota; kèm `Retry-After` |
| 500 | `INTERNAL_ERROR` | Lỗi server không lường |
| 503 | `DEPENDENCY_UNAVAILABLE` | Downstream tạm down |

### 4.2 Domain error catalog — `{{Domain}}ErrorEnum`

> Lỗi NGHIỆP VỤ riêng boundary (thường 422). Mỗi value map 1 BR. Single source: BE define enum, FE/consumer map i18n theo enum, KHÔNG hardcode chuỗi.

| Enum value | HTTP | Map BR | Nghĩa | Recoverable |
|---|---|---|---|---|
| `REFUND_TOO_LARGE` | 422 | `BR-xxx` | Amount vượt số dư hoàn | Yes |
| `REFUND_WINDOW_EXPIRED` | 422 | `BR-xxx` | Quá hạn hoàn | No |
| {{...}} | | | | |

---

## 5. Idempotency

- Áp dụng MỌI mutation có side-effect.
- Client gửi `Idempotency-Key: <uuid-v4>` per logical attempt (retry dùng LẠI cùng key).
- Server lần đầu → lưu `(key, tenant_id) → response snapshot` TTL 24h. Replay cùng key+payload → trả cached (cùng `id`, cùng status). Cùng key+payload KHÁC → `409 IDEMPOTENCY_CONFLICT`.
- Key scope theo tenant.

---

## 6. Rate limiting

| Aspect | Value |
|---|---|
| Scope | Per-tenant (+ per-route bucket cho endpoint nhạy) |
| Limit | {{1000 req/phút/tenant}}; mutation bucket chặt hơn read |
| Vượt | `429 RATE_LIMITED` + `Retry-After: <giây>` |
| Header info | `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` |
| Unauthenticated | Bucket riêng chặt hơn (chống abuse) |

---

## 7. Versioning + backward compatibility

**Additive (MINOR — dev trong wave)**: thêm field response/request optional (default an toàn); thêm endpoint; thêm error code (consumer ignore code lạ).

**Breaking → WAVE SAU** (không sửa tại chỗ): lùi `/domain` sửa hợp đồng, `/approve-document` khoá lại, wave kế giao bản mới. Consumer đang chạy phải còn chạy được suốt lúc đó — luật cộng-trước-xoá-sau ở `tracking/BC-LEDGER.md §2`. (bỏ) qua thẳng → DESIGN sửa contract)**: xoá field / đổi type / đổi semantics / optional→required / đổi nghĩa HTTP status / rename.

Breaking → `/api/v2`; v1 giữ ACTIVE qua deprecation window (default 2 wave) → `status: DEPRECATED` → xoá.

---

## 8. Examples

Happy: `POST /refunds` + headers (`Authorization`, `X-Tenant-ID`, `Idempotency-Key`, `Content-Type`) + body → `201 {"id":...,"status":"PENDING"}`. Validation: thiếu `reason` → `400 VALIDATION_FAILED` (`details[].field=reason`). Domain: amount > số dư → `422 REFUND_TOO_LARGE` (map BR-xxx). Idempotency replay: cùng key+payload → cached `201`; key cùng+payload khác → `409`.

---

## 9. Security

- AuthN: JWT verify per `rules-backend` (OAuth2 RS); mTLS service-to-service.
- AuthZ: role/scope ở `application/` layer (KHÔNG ở controller/FE — FE chỉ ẩn UI).
- Tenant isolation: mọi query filter `tenant_id`; `404` (không `403`) khi resource khác tenant (tránh leak).
- PII: mask field nhạy trong log (`ref-backend-logging`). Replay protection: idempotency 24h (§5). Input: validate schema trước domain; size limit body.

---

## 10. Performance

| Aspect | Value |
|---|---|
| p50 / p99 latency | < {{100ms}} / < {{500ms}} |
| Throughput | ≥ {{500 req/s}} / instance |
| Timeout (consumer-side) | {{30s}} (xem INTEG-INT cross-boundary) |
| Retry (consumer-side) | Backoff + jitter, max 3, CHỈ trên 5xx+429 (KHÔNG retry 4xx khác) |

---

## 11. Observability

- Metric: `api_{{name}}_request_total{operation,result,code}` + `..._duration_seconds`.
- Trace span `api.{{name}}.{operation}`; propagate `X-Correlation-ID`.
- Log JSON: `correlation_id`, `tenant_id`, `operation`, `status`, `duration_ms` — mask PII.

---

## 12. Consumers

> Consumer = `boundary_id` (MATRIX `consumed_by`); pattern cross-boundary → `integrations/INTEG-INT-*.md`.

| Consumer (boundary_id) | Kind | Cách gọi | Notes |
|---|---|---|---|
| `{{web-boundary}}` | web | Via BFF | |
| `{{other-boundary}}` | backend | Cross-boundary | `INTEG-INT-{{name}}.md` |

---

## 13. References

- HLD: `hld/hld-{{producer}}.md` · Data: `data-model/data-model-{{producer}}.md` · Domain error→BR: `business-rules/BR-*.md`
- KG: `knowledge-base/{{producer}}.knowledge-graph.yaml` · Integration: `integrations/INTEG-INT-*.md` · Convention: `rules-backend` / `ref-backend-restclient`

---

## 14. Change log

| Date | Version | Change | Severity | Author |
|---|---|---|---|---|
| {{DATE}} | 1 | Initial draft | — | solution-architect |
