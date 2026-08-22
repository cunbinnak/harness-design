---
type: design
artifact_kind: bff-aggregation
contract_id: "bff-aggregation/{{name}}"
status: "DRAFT | ACTIVE | DEPRECATED"
version: 1
bff: "{{bff-boundary-name}}"   # boundary_id kind=bff sở hữu surface
fe_consumers: []         # boundary_id kind=web/mobile consume (MATRIX consumed_by)
backend_dependencies: [] # boundary_id backend BFF gọi (MATRIX depends_on)
last_reviewed: "{{DATE}}"
---

> Điền NGẮN GỌN: ưu tiên bảng/bullet, không văn xuôi thừa, không lặp. Doc này agent downstream đọc nhiều lần — tiết kiệm context.

# BFF Aggregation — `bff-aggregation/{{name}}`

> BFF compose N backend boundary serve MỘT operation FE-facing (GraphQL field / REST aggregation). Bổ trợ `api/api-{{bff}}.md` (full schema BFF); file này document fan-out composition (parallelism, timeout budget, graceful degrade, error mapping). Author ở DESIGN khi aggregation ≥ 2 backend call. Backend dep = boundary cùng repo (MATRIX `depends_on`).

---

## 1. Purpose

{{1-2 câu: operation FE-facing nào aggregation phục vụ. Vd: GraphQL `customer(id)` = profile + orders + payment methods, fan-out 3 backend, FE thấy 1 object.}}

---

## 2. FE-facing surface

| Aspect | Value |
|---|---|
| Surface kind | {{GraphQL field / REST endpoint / subscription}} |
| Full BFF schema | `api/api-{{bff}}.md` (aggregation này là 1 operation trong đó) |
| Operation | {{Query.customer / GET /customers/:id/summary}} |
| Auth context | {{Bearer JWT role X / scoped}} |
| Persisted query | Production: persisted-query ID thay full query string (chống injection + giảm payload); mapping chốt ở deploy |
| Caching | {{per-viewer TTL 60s / no-cache mutation}} (§9) |

---

## 3. Backend boundaries fan-out

> Mỗi backend = `boundary_id` (MATRIX `depends_on`); contract = `api/api-{{boundary}}.md`.

| # | Backend boundary | Contract | Call shape | Required? |
|---|---|---|---|---|
| 1 | `{{boundary-1}}` | `api/api-{{boundary-1}}.md` | GET `/customers/:id` | Required |
| 2 | `{{boundary-2}}` | `api/api-{{boundary-2}}.md` | GET `/orders?customer_id=:id` | Required |
| 3 | `{{boundary-3}}` | `api/api-{{boundary-3}}.md` | GET `/payment-methods?customer_id=:id` | Optional (graceful degrade) |

---

## 4. Composition strategy

```
FE → BFF resolver
       ├─→ load({{boundary-1}})   ┐
       ├─→ load({{boundary-2}})   ├── parallel (Promise.all / Future.wait)
       └─→ load({{boundary-3}})   ┘ → Compose → FE-shaped response
```

**Parallelism**: call độc lập chạy song song; call phụ thuộc serialize (vd cần `customer.tenant_id` trước khi query orders). Ghi dependency edge:

| Edge | Reason |
|---|---|
| `{{boundary-1}} → {{boundary-2}}` | Cần `customer.tenant_id` cho tenant-scoped query |
| `{{boundary-2}} ↔ {{boundary-3}}` (no edge) | Độc lập → parallel |

**DataLoader (N+1 prevention)**: list field PHẢI batch per backend (1 batch thay N call). Backend thiếu batch endpoint → amend contract (CR MODERATE).

---

## 5. Identity propagation

| Concern | Mechanism |
|---|---|
| Viewer JWT | Extract ở BFF entry → resolver context |
| Forward to backend | Service-to-service (mTLS/service JWT) + `X-On-Behalf-Of: <viewer-sub>` |
| Always | `X-Tenant-ID`, `X-Correlation-ID`, `X-Request-ID` per call |
| Forbidden | Forge identity / system token bypass user authz |

---

## 6. Timeout budget (cascade)

| Layer | Timeout | Notes |
|---|---|---|
| FE → BFF total | 30s | FE chờ |
| BFF resolver total | 20s | reserve compose+serialize |
| Required call | 5s | block resolver |
| Optional call | 2s | null/fallback nếu quá |

**Invariant**: per-call < resolver total < BFF total < FE timeout.

---

## 7. Failure modes + graceful degradation

| Mode | BFF response |
|---|---|
| Required backend (`{{boundary-1}}`) down | Error union typed `customer_unavailable`; FE show error UI |
| Required backend (`{{boundary-2}}`) down | Error union `orders_unavailable`; partial info vẫn trả |
| Optional backend (`{{boundary-3}}`) down/timeout | Trả phần còn lại; `paymentMethods: null` + warning |
| Auth fail mid-call | GraphQL error `unauthorized` field-level |
| 5xx transient | Retry per circuit (§8) → rồi error |

**Pattern**: typed error union — KHÔNG throw nếu partial result hữu ích.

### 7.1 Backend error → FE error mapping

> BFF KHÔNG leak raw backend error envelope ra FE. Map `error.code` backend (`api/api-{{boundary}}.md` §4) → field-level FE error.

| Backend code | FE-facing error | Field |
|---|---|---|
| `FORBIDDEN` (backend-1) | `unauthorized` | `customer` |
| `NOT_FOUND` (backend-1) | `customer: null` | — |
| `DEPENDENCY_UNAVAILABLE` (backend-2) | `orders_unavailable` (typed union) | `recentOrders` |
| `RATE_LIMITED` (bất kỳ) | propagate `429` + `Retry-After` | toàn op |

---

## 8. Circuit breaker (per-backend)

| Setting | Value |
|---|---|
| Open trigger | 5 fail liên tục HOẶC 50% fail rate / 1 phút |
| Open duration | 30s → half-open probe (1 request; close nếu OK, mở lại nếu fail) |
| Fallback when open | Fast-fail → degrade (optional=null; required=typed error) |
| Metric | `bff_circuit_state{backend, state}` |

Convention resilience chốt ở ADR.

---

## 9. Caching

| Field | Cache key | TTL |
|---|---|---|
| `Customer.profile` | viewer + customer_id | 60s |
| `Customer.recentOrders` | viewer + customer_id + limit | 30s |
| `Customer.paymentMethods` | viewer + customer_id | 5min |

- Store: per-request (in-memory dedupe) + cross-request (Redis, per-viewer TTL).
- Invalidation: subscribe backend event (`customer.updated.v1` → invalidate key) — xem `events/{{boundary}}-events.md`.
- KHÔNG cache mutation result. Cache key LUÔN gồm viewer (tránh leak cross-user).

---

## 10. Authorization at BFF

- Field-level authz: check viewer role (UX — ẩn field không quyền).
- Result filtering: filter response theo viewer claims.
- **Defense in depth**: backend VẪN enforce business rule (BFF check chỉ UX). KHÔNG re-enforce business rule ở BFF.

---

## 11. Schema + resolver (FE-facing)

```graphql
type Customer {
  id: ID!
  profile: CustomerProfile!                 # {{boundary-1}}
  recentOrders(limit: Int = 10): [Order!]!  # {{boundary-2}}
  paymentMethods: [PaymentMethod!]          # {{boundary-3}}, null on degrade
}
type Query { customer(id: ID!): Customer }
```

```ts
customer: async (_, { id }, ctx) => {
  const profile = await ctx.loaders.customerProfile.load(id);  // required, cần trước (tenant)
  if (!profile) return null;
  const [orders, pm] = await Promise.allSettled([              // parallel
    ctx.loaders.orders.load({ customerId: id, limit: 10 }),
    ctx.loaders.paymentMethods.load(id),
  ]);
  return { id, profile,
    recentOrders: orders.status === "fulfilled" ? orders.value : [],
    paymentMethods: pm.status === "fulfilled" ? pm.value : null };
}
```

Type codegen từ mỗi backend `api/api-{{boundary}}.md` — KHÔNG hand-roll type.

---

## 12. Observability

| Signal | Specifics |
|---|---|
| Trace | Parent `bff.{{operation}}`; child span per backend call |
| Metric | `bff_aggregation_{{operation}}_duration_seconds`, `bff_backend_call_{{boundary}}_total{result,status}`, `bff_circuit_state{backend,state}` |
| Log | Per call: operation, backend, status, duration, viewer_id (no PII) |
| Audit | Mutation: full action log per security policy |

---

## 13. Testing

- **Component**: resolver + mock backend client (fixture per `api/api-{{boundary}}.md`) — happy + mỗi backend fail + circuit-open + partial degrade + error mapping (§7.1).
- **Integration**: real backend trong `docker-compose` test env — full fan-out ≥1 aggregation critical.
- **Contract**: outbound call khớp mỗi backend contract (verify ở `test-execute`).

---

## 14. Versioning + backward compatibility

- **Additive (MINOR — dev trong wave)**: thêm field aggregating backend mới; thêm optional dependency; bỏ dependency redundant.
- **Breaking → WAVE SAU** (không sửa tại chỗ): lùi `/domain` sửa hợp đồng, `/approve-document` khoá lại, wave kế giao bản mới. Consumer đang chạy phải còn chạy được suốt lúc đó — luật cộng-trước-xoá-sau ở `tracking/BC-LEDGER.md §2`: đổi resolver signature; remove field; đổi degradation semantics.

---

## 15. Anti-patterns (forbidden)

- (cấm) Sequential khi parallel được · N+1 (list field không DataLoader) · backend call không timeout
- (cấm) Throw uncaught khi optional fail (dùng typed error union) · forge viewer identity / system token bypass authz
- (cấm) Re-enforce business rule ở BFF · cache mutation result · cache key thiếu viewer (leak cross-user)
- (cấm) Hand-roll type backend contract · hardcode backend URL · leak raw backend error envelope ra FE · bỏ persisted-query ở production

---

## 16. Consumers + dependencies

> Đồng bộ MATRIX (`consumed_by` / `depends_on`).

**FE consumers** (web/mobile): `{{web-boundary}}` (Apollo Client), `{{mobile-boundary}}` (generated SDK).
**Backend dependencies**: `{{boundary-1}}`, `{{boundary-2}}`, `{{boundary-3}}` — pattern cross-boundary ở `integrations/INTEG-INT-*.md`.

---

## 17. Change log

| Date | Version | Change | Author |
|---|---|---|---|
| {{DATE}} | 1 | Initial | solution-architect |
