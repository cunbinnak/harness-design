---
type: design
artifact_kind: data-model
target_boundary: "{{boundary}}"
# Chỉ kind=backend có data-model. FE (web/mobile) KHÔNG — consume contract (P1).
kind: backend
status: ACTIVE
version: 1
tier: T2
owner_authority: Architecture Authority
created_at: "{{DATE}}"
last_reviewed: "{{DATE}}"
db_engine: "{{Postgres 16 / MySQL 8 / ...}}"
schema_name: "{{boundary}}"
related_brs: []                          # BR mà model enforce
adr_refs: []                             # ADR chốt identity/concurrency/partitioning
---

# Data Model — `{{boundary}}`

> Điền NGẮN GỌN: ưu tiên bảng/bullet, không văn xuôi thừa, không lặp. Doc này agent downstream đọc nhiều lần — tiết kiệm context.
> Hai mặt trong một file: (1) Domain model (aggregate/entity/VO/event/state machine); (2) Physical schema (table/index/constraint/migration). Private cho boundary; ngoài chỉ thấy contract.
> **KHÔNG cross-boundary FK** (P1): tham chiếu boundary khác bằng id (UUID), resolve app-layer — KHÔNG `REFERENCES other_schema.table`.

---

## 1. Aggregates (domain)

> Aggregate = root + child + VO, chung consistency boundary. Invariant enforce TRONG aggregate (không phó mặc DB).

### 1.1 `{{AggregateName-1}}` (root: `{{Entity}}`)

**Identity:** `{{EntityId}}` — type {{UUID v7 / monotonic}}, sinh ở {{application / DB default}} (ADR: `ADR-{{boundary}}-{{NNN}}`).

| Field | Type (domain) | Required | Notes / invariant |
|---|---|---|---|
| {{id}} | {{UUID}} | yes | identity |
| {{tenant_id}} | {{UUID}} | yes | multi-tenant — mọi query filter field này |
| {{status}} | {{StatusEnum}} | yes | state machine §4 |
| {{amount}} | `Money` (VO §3) | yes | ≥ 0 |
| {{version}} | int | yes | optimistic concurrency |
| {{created_at/updated_at}} | Timestamp UTC | yes | created immutable; updated set mỗi save |

**Child entities:**

| Child | Quan hệ | Lifecycle |
|---|---|---|
| {{LineItem}} | 1 `{{Aggregate}}` có N | cascade-delete theo root; không độc lập |

**Invariants (enforce TRONG aggregate):**
- {{vd. "total = sum(line_items.subtotal) — BR-{{boundary}}-002"}}
- {{vd. "status theo state machine §4 — không set tuỳ ý"}}
- {{vd. "Once SHIPPED, modification reject — BR-{{boundary}}-001"}}

**Operations (command trên aggregate):**

| Command | Pre-condition | Post-condition | Emits event | BR |
|---|---|---|---|---|
| `{{place}}(...)` | {{...}} | status={{CONFIRMED}} | `{{EventName-1}}` | `BR-{{boundary}}-001` |
| `{{cancel}}(reason)` | status<{{TERMINAL}} | status=CANCELLED | `{{EventName-3}}` | `BR-{{boundary}}-003` |

### 1.2 (Aggregate khác)
{{Same structure}}

**Aggregate relationship:** {{vd. "Order tham chiếu Customer bằng customer_id — KHÔNG ôm Customer trong Order aggregate (khác consistency boundary)."}}

---

## 2. Entity-relationship (logical)

```mermaid
erDiagram
  {{AGGREGATE_1}} ||--o{ {{CHILD_1}} : contains
  {{AGGREGATE_1}} }o--|| {{AGGREGATE_2}} : "refs by id"
  {{AGGREGATE_1}} {
    uuid id PK
    uuid tenant_id
    string status
    int version
  }
  {{CHILD_1}} {
    uuid id PK
    uuid {{aggregate_1}}_id FK
  }
```

> FK trong sơ đồ chỉ là FK nội bộ boundary. Cross-boundary ref vẽ "refs by id", KHÔNG FK vật lý.

---

## 3. Value objects

Immutable, equality theo value (no identity):

| VO | Fields | Validation |
|---|---|---|
| `Money` | `amount: Decimal`, `currency: ISO4217` | amount ≥ 0; currency allowed list |
| `{{LineItem}}` | `{{item_id, quantity, unit_price}}` | quantity > 0; subtotal = qty × price |
| `IdempotencyKey` | `value: String` | format `^[a-zA-Z0-9-]{8,64}$` |
| `TenantId` | `value: UUID` | required everywhere |

---

## 4. State machines

### 4.1 `{{Aggregate}}.status`

```
{{INITIAL}} ──▶ {{CONFIRMED}} ──▶ {{IN_PROGRESS}} ──▶ {{TERMINAL}}
   └──▶ CANCELLED   (nếu status < {{IN_PROGRESS}})
```

**Transition table (nguồn chân lý — code/test generate từ đây):**

| From | Event / command | Guard | To | Side effect |
|---|---|---|---|---|
| {{INITIAL}} | `{{confirm}}` | {{payment ok}} | {{CONFIRMED}} | emit `{{Confirmed}}` |
| {{CONFIRMED}} | `{{cancel}}` | — | CANCELLED | emit `{{Cancelled}}`, release hold |
| {{IN_PROGRESS}} | `{{complete}}` | {{all done}} | {{TERMINAL}} | emit `{{Completed}}` |

**Terminal:** {{TERMINAL}}, CANCELLED. **Illegal transition** → reject domain error (không silently ignore). Test ở `test-execute`.

---

## 5. Physical schema (DDL)

> DDL cho `db_engine` ở frontmatter. Migration forward-only (`db/migrations/V{n}__*.sql`), expand→migrate→contract, không sửa migration đã merge.

```sql
-- schema: {{boundary}}
CREATE TABLE {{boundary}}.{{aggregate_1}} (
    id              UUID          PRIMARY KEY,
    tenant_id       UUID          NOT NULL,
    status          VARCHAR(32)   NOT NULL,
    amount          NUMERIC(19,4) NOT NULL CHECK (amount >= 0),
    currency        CHAR(3)       NOT NULL,
    version         INTEGER       NOT NULL DEFAULT 0,   -- optimistic concurrency
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE TABLE {{boundary}}.{{child_1}} (
    id              UUID          PRIMARY KEY,
    {{aggregate_1}}_id UUID       NOT NULL REFERENCES {{boundary}}.{{aggregate_1}}(id) ON DELETE CASCADE,
    -- ^ FK chỉ trong cùng schema/boundary. KHÔNG REFERENCES schema khác.
    quantity        INTEGER       NOT NULL CHECK (quantity > 0),
    unit_price      NUMERIC(19,4) NOT NULL
);

-- Cross-boundary ref: customer_id KHÔNG FK, chỉ UUID + index. Resolve app-layer.
ALTER TABLE {{boundary}}.{{aggregate_1}} ADD COLUMN customer_id UUID NOT NULL;
```

### 5.1 Indexes

| Index | Columns | Type | Lý do |
|---|---|---|---|
| `pk_{{aggregate_1}}` | `(id)` | PK | identity |
| `ix_{{aggregate_1}}_tenant` | `(tenant_id, status)` | btree | mọi query filter tenant_id |
| `ix_{{aggregate_1}}_customer` | `(customer_id)` | btree | lookup cross-boundary ref |
| `uq_{{aggregate_1}}_idem` | `(tenant_id, idempotency_key)` | unique | backstop chống double-process |

### 5.2 Constraints (DB-level — backstop, KHÔNG thay invariant aggregate)

| Constraint | Rule | Tương ứng invariant |
|---|---|---|
| `chk_amount_nonneg` | `amount >= 0` | §1 Money ≥ 0 |
| `uq_idem` | unique idempotency-key per tenant | §6 idempotency |

> DB constraint là lưới an toàn cuối, không phải nơi enforce business rule chính (rule ở domain).

---

## 6. Idempotency + concurrency

| Cơ chế | Cách làm | Field / store |
|---|---|---|
| Optimistic concurrency | so version khi save, conflict → retry/refuse | `version` column |
| Idempotency (write API) | Idempotency-Key → store kết quả 24h | Redis `{{boundary}}:idem:{key}` + unique DB |
| Dedupe consumer (event) | track event-id đã xử lý | `processed_events(event_id)` hoặc Redis set |

---

## 7. Domain events (internal)

> Internal — chỉ handler trong boundary subscribe. Cross-boundary → `events/{{boundary}}-events.md` (artifact khác, có contract).

| Event | Emitted by | Payload (essence) | Internal handler | Effect |
|---|---|---|---|---|
| `{{InternalEvent-1}}` | `{{Aggregate}}.{{op}}()` | {{aggregate-id, ts}} | `{{Handler}}` | {{update read-model}} |

Promote internal → integration event cần CR + author contract ở `events/`.

---

## 8. Domain services

Logic không thuộc riêng một aggregate:

| Service | Purpose | Uses | BR |
|---|---|---|---|
| `{{PricingService}}` | tính giá theo rule | `{{Order, Discount, PricingRule}}` | `BR-{{boundary}}-{{NNN}}` |
| `{{EligibilityService}}` | quyết định {{op}} có cho phép | `{{Aggregate, Policy}}` | `BR-{{boundary}}-{{NNN}}` |

---

## 9. Repository contracts (internal)

> Port khai báo ở `domain`, impl ở `outbound-db`. KHÔNG phải cross-boundary contract.

```
{{Aggregate}}Repository:
  findById({{id}})                       -> Option<{{Aggregate}}>
  save({{aggregate}})                    -> void   (optimistic concurrency qua version)
  findBy{{Filter}}({{params}}, paging)   -> Page<{{Aggregate}}>
```

**Forbidden:** `findAll()` thiếu paging; SQL thô leak ra interface; leak ORM type (Entity/Row) — trả domain object.

---

## 10. Anti-corruption layer (ACL)

> External map về domain ở `outbound-{{provider}}/`, KHÔNG leak vào `domain/`.

| External (contract / provider) | Internal model |
|---|---|
| `{{Stripe amount}}` (integer cents) | `Money` VO (Decimal + currency) |
| `INTEG-EXT-{{name}}` `PaymentEvent` | `PaymentRef` ({{id, amount}}) |

Consume → translate → cache snapshot nếu cần (đừng gọi external trong vòng lặp).

---

## 11. Data lifecycle + retention

| Data | Retention | Archival / delete | Lý do (compliance) |
|---|---|---|---|
| {{Refund record}} | {{7 năm}} | archive cold sau {{1 năm}} | {{tax/audit}} |
| {{Idempotency key}} | {{24h}} | TTL tự hết | — |
| {{PII field}} | {{theo policy}} | mask/erase khi {{xoá tài khoản}} | {{GDPR-like}} |

**PII inventory:** {{field PII trong model}} → mask log, cân nhắc encrypt at-rest.

---

## 12. Migration approach

| Loại thay đổi | Severity | Cách làm |
|---|---|---|
| Thêm column nullable / table mới | additive | 1 migration forward |
| Thêm column NOT NULL | cần backfill | expand (nullable) → backfill → set NOT NULL (nhiều wave) |
| Đổi type / rename | breaking | dual-write + backfill + cutover + drop (strangler) |
| Drop column / table | breaking | deprecate → ngừng đọc → drop wave sau |

Không DROP cùng wave với lần cuối còn đọc. Migration test rollback-safe ở `test-execute`.

---

## 13. Business rule references

Mỗi `BR-*` phải enforce ở đâu đó trong file này (hoặc note deferred):

| BR-ID | Where enforced |
|---|---|
| `BR-{{boundary}}-001` | `{{Aggregate}}.{{op}}()` pre-condition (§1) |
| `BR-{{boundary}}-002` | `{{DomainService}}.evaluate()` (§8) |
| `BR-{{boundary}}-003` | invariant state machine §4 |

---

## 14. Ubiquitous language

Dùng chính xác trong code/docs/comment — tránh đồng nghĩa:

| Term | Definition |
|---|---|
| {{Refund}} | Trả tiền lại cho người trả; KHÁC "chargeback" (external khởi tạo). |
| {{Capture}} | Chuyển tiền đã authorize từ hold sang settled. |
| {{Reconciled}} | Settled + khớp sổ nội bộ. |

Term khác nghĩa ở aggregate khác → namespace (`Refund.Status` vs `Payment.Status`).

---

## 15. Change log

| Date | Version | Author | CR/ADR | Description |
|---|---|---|---|---|
| {{DATE}} | 1 | {{Author}} | — | Initial data model |
