# HLD — {boundary_id}

> **Purpose:** Thiết kế **cấp cao** (HLD) của boundary `{boundary_id}` — view kiến trúc/logic + ranh giới trách nhiệm, KHÔNG phải code chi tiết.
> **Owner:** `intake:solution-architect` (intake bước 3) · **Audience:** `dev:*` / `review:*` / `fix:*` / QA / stakeholder kỹ thuật.
> **Out of scope (link chi tiết):** cấu trúc code/folder → `ref-{kind}-pattern` · endpoints → [`../api/`](../api/) · schema → [`../data-model/`](../data-model/) · UI → [`../ux/`](../ux/) · cross-boundary → [`../integrations/`](../integrations/) · NFR dự án → [`../PROJECT.md`](../PROJECT.md) · infra → [`../infra/`](../infra/).
> **Quy ước:** section gắn **(tùy chọn)** → bỏ nếu boundary không áp dụng (vd CRUD đơn giản, không outbound/event).

---

**Boundary:** `{boundary_id}` · **Kind:** `{kind}` (backend|bff|web|mobile) · **Stack:** `{language + framework}` · **Wave(s):** `{waves}` · **FEAT:** (FEAT-xxx)

---

## 1. Design goals & responsibilities
- **Goals:** boundary sinh ra để giải quyết gì (1–3 mục, gắn FEAT/business value).
- **Responsibilities:** … (boundary CHỊU trách nhiệm gì)
- **Non-responsibilities:** … (KHÔNG làm — vd: không xử lý thanh toán = `payment`; không lưu profile = `auth`)

## 2. Data ownership
- **Sở hữu (source of truth):** {Entity-A}, {Entity-B} — nơi duy nhất ghi.
- **Đọc-only (không own):** {Entity-X} lấy qua API/event của {boundary}.
- Cross-boundary liên kết qua **id** (no FK — `rules-backend`). Schema → [`data-model-{boundary_id}.md`](../data-model/).

## 3. Context (C4 L1) + integration summary
```
 [Actor: {role}] ──► [ {boundary_id} ({kind}) ] ──sync/async──► [ {downstream/ext} ]
                            ▲ event/HTTP
                     [ {upstream boundary} ]
```
| Hướng | Đối tác | Kiểu | Đồng bộ? | Mục đích |
|---|---|---|---|---|
| Inbound (ai gọi mình) | {upstream} | HTTP/event | sync/async | … |
| Outbound (mình gọi ai) | {downstream/ext} | HTTP/event | sync/async | … |

Detail: [`integrations/INTEG-*.md`](../integrations/).

## 4. Architecture (C4 container + component)
> Container = đơn vị runtime; Component = nhóm trách nhiệm **logic** (KHÔNG phải folder — code structure → `ref-{kind}-pattern`).

| Container (runtime) | Tech | Trách nhiệm |
|---|---|---|
| App service | {framework} | xử lý request/nghiệp vụ |
| Datastore / Cache / Broker | {PostgreSQL / Redis / Kafka} | state / cache-lock / event (bỏ dòng không dùng) |

| Component (logic) | Trách nhiệm |
|---|---|
| Inbound (API/controller) | validate, map error → response |
| Use case / application | orchestrate nghiệp vụ, transaction boundary |
| Domain | business rule + invariant |
| Adapter (persistence/integration) | đọc-ghi DB / gọi external / event |

## 5. Key flows (sequence)
> Mỗi FEAT `Must` ≥ 1 flow: **happy + ≥ 1 nhánh lỗi quan trọng**. Ghi BR-x tại bước thực thi (detail → FEAT).
```
Actor   Inbound    Use case   Domain   DB
 │─req──►│─validate►│─apply BR-1►│─persist►│
 │◄─2xx──│◄─────────│◄───────────│         │
 │─(invalid)►│ 400 VALIDATION (error codes → api-*.md)
```
**BR:** BR-1, BR-2 ([`FEAT-XXX`](../feat/)) · **Error paths:** [`api-{boundary_id}.md`](../api/)

## 6. Auth & permission
- **Ai được gọi:** role/permission theo nhóm endpoint (vd `manager` → quản lý; `staff` → đọc).
- **Tenant isolation:** mọi query filter `tenant_id` từ token. **Public vs internal:** endpoint nào public (login/health) vs internal.
- Identity lấy từ security context, KHÔNG tin client.

## 7. Consistency & transaction strategy *(tùy chọn — khi multi-write / cross-boundary / event)*
- **Tx boundary:** ở service/use-case; multi-write trong 1 boundary = 1 ACID tx.
- **Cross-boundary:** KHÔNG distributed tx → **eventual consistency** qua event; publish **sau commit** (after-commit / outbox).
- **Idempotency:** consumer/callback/retry dedup theo event/idempotency key.
- **Saga/compensation:** nếu luồng trải nhiều boundary — mô tả bước + bước bù.

## 8. Failure behavior & resilience *(tùy chọn — khi có outbound call)*
- **Downstream lỗi:** fail-fast hay degrade; fallback/cache stale; lỗi propagate ra client thế nào.
- **Partial failure:** DB commit nhưng event/cache fail → bù (outbox retry / reconcile).

| Downstream | Timeout | Retry | Circuit breaker | Fallback |
|---|---|---|---|---|
| {boundary_b / ext} | (ms) | (strategy) | (threshold) | (behavior) |

## 9. Deployment & scaling topology
- **Đơn vị deploy:** 1 container/image; stateless (state ở DB/cache).
- **Scaling:** scale ngang N replica (vd HPA theo CPU/req); điểm nghẽn dự kiến (DB pool, lock…).
- **Sticky/affinity:** có cần không (mặc định KHÔNG — stateless). **Startup deps:** DB/broker phải sẵn (health-gated).
- Infra/compose local → [`../infra/`](../infra/).

## 10. Observability *(chỉ ghi điểm đặc thù — mặc định kế thừa PROJECT/ADR)*
Log structured + `traceId` (không log nhạy cảm) · metrics rate/latency/error + business metric · tracing propagate qua downstream/event · health `/health/live|ready`.

## 11. API surface (tóm tắt)
| Nhóm | Method/Op | Mục đích |
|---|---|---|
| {Resource} | GET/POST/PUT/DELETE `/v1/{resource}` | … |

Contract + error format → [`api-{boundary_id}.md`](../api/).

## 12. NFR refinements *(tùy chọn — chỉ khi stricter hơn PROJECT)*
| Attribute | Project | Boundary (stricter) | Cơ chế |
|---|---|---|---|
| (vd Performance) | p95 < 200ms | p95 < 100ms | index, pool max=20 |

## 13. ADR references *(theo chủ đề, không hardcode số)*
| ADR (chủ đề) | Áp dụng vào boundary |
|---|---|
| tech-stack | {framework}, {ORM} |
| backend-architecture | Layered (`api→application→domain→infrastructure`) hoặc Hexagonal — theo ADR |
| auth | JWT validate mọi endpoint trừ public |

> Quyết định cục bộ (không lên ADR) → KG `decisions`.

## 14. Risks & open questions
| # | Risk / Question | Severity | Owner | Status |
|---|---|---|---|---|
| R1 | | High/Med/Low | | Open/Resolved |

> Blocker thực sự → KG `discipline.blockers` (chặn `complete`).
