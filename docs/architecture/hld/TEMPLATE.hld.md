# HLD — {boundary_id}

> **Purpose:** Mô tả cấu trúc nội bộ + flow chính của boundary `{boundary_id}`.
> **Owner:** `intake:solution-architect` (intake bước 3).
> **Audience:** `dev:backend` / `dev:frontend` / `review:*` của boundary này, `fix:*` khi sửa bug.
> **Out of scope:**
> - Endpoints chi tiết → [`../api/api-{boundary_id}.md`](../api/)
> - DB schema + state machine → [`../data-model/data-model-{boundary_id}.md`](../data-model/)
> - UI wireframes → [`../ux/ux-{boundary_id}.md`](../ux/) (nếu FE)
> - Cross-boundary calls → [`../integrations/`](../integrations/) (`INTEG-INT-*.md` / `INTEG-EXT-*.md`)
> - NFR cấp dự án → [`../PROJECT.md`](../PROJECT.md) (HLD chỉ ghi REFINEMENT nếu boundary stricter)
> - Deployment commands → [`../infra/local-dev.md`](../infra/) + `docker-compose.yml`

---

**Boundary:** `{boundary_id}` · **Layer:** `{layer}` (backend | bff | fe | mobile)
**Wave first introduced:** `{wave_id}` · **FEAT phục vụ:** (list FEAT-xxx)

---

## 1. System Context (C4 L1)

> Vị trí của `{boundary_id}` trong hệ thống — actor nào dùng, gọi/được gọi từ đâu.

```
[Actor] ───► [FE/Client] ───► [{boundary_id}] ───► [Downstream boundaries / DB]
```

- **Upstream caller:** (boundary nào gọi vào — link `integrations/INTEG-*.md` để biết kind: HTTP/event)
- **Downstream calls:** (boundary nào được gọi — link `integrations/INTEG-*.md`)
- **Storage:** (DB type — chi tiết schema ở [`data-model-{boundary_id}.md`](../data-model/))

## 2. Internal Components (C4 L2)

> Phân rã `{boundary_id}` thành các module/layer nội bộ — KHÔNG vẽ hệ thống ngoài.

```
services/{prefix}-{boundary_id}/      # cấu trúc chi tiết theo kind → ref-{kind}-pattern
├── api/                # Controller/handler + DTO (parse, validate, map error→HTTP)
├── application/        # Use case / orchestration (Layered) — gộp vào domain nếu DDD nhẹ
├── domain/             # Business logic (entity, VO) + ports/
├── infrastructure/     # Adapter (DB repo, messaging, HTTP client outbound, cache)
├── config/             # Env, DI wiring
└── tests/              # unit + integration
```

| Layer | Trách nhiệm | Pattern |
|-------|-------------|---------|
| api | Parse request, validate DTO, map errors | Controller |
| domain | Execute business rule, orchestrate repo | Service / Use-case |
| infra | DB query, HTTP outbound | Adapter / Repository impl |
| dto | Input/output schema | Pydantic / Zod / Bean |

## 3. Key Flows (Sequence)

> Mỗi FEAT `Must` → ít nhất 1 flow. Ghi rõ BR-x tại bước thực thi (không lặp BR detail — link FEAT).

### Flow 1 — {FEAT-XXX}: {tên luồng}

```
Client          {boundary} API     Domain Service     DB
  │── POST ───►│                    │                  │
  │            │── validate ───────►│                  │
  │            │                    │── check BR-1 ───►│
  │            │                    │── INSERT ───────►│
  │◄── 201 ────│◄── response ───────│                  │
```

**Business rules thực thi:** BR-1, BR-2 (chi tiết: [`FEAT-XXX`](../feat/))
**Error paths:** xem error codes trong [`api-{boundary_id}.md`](../api/)

### Flow 2 — {FEAT-YYY}: (thêm nếu cần)

## 4. Internal Data Flow (nếu phức tạp)

> Mô tả dữ liệu biến đổi qua các lớp NỘI BỘ. Bỏ qua nếu CRUD đơn giản.

```
[HTTP JSON] → (validate) → [Request DTO] → (map) → [Domain Entity] → (persist) → [DB row]
                                                                                   │
[HTTP JSON] ← (serialize) ← [Response DTO] ← (map) ← [Domain Entity] ◄─────────────┘
```

## 5. Resilience patterns (outbound calls)

> Áp dụng cho mỗi downstream call. Inbound resilience là việc của caller.

| Downstream | Timeout | Retry | Circuit breaker | Fallback |
|------------|---------|-------|----------------|----------|
| {boundary_b} | (ms) | (strategy) | (threshold) | (behavior) |

## 6. NFR refinements (boundary-specific only)

> Chỉ ghi nếu **stricter hơn** [`PROJECT.md`](../PROJECT.md) NFR hoặc boundary-specific. Mặc định kế thừa từ PROJECT.

| Attribute | Project target | Boundary target (stricter) | Cơ chế |
|-----------|---------------|---------------------------|--------|
| (vd Performance) | p95 < 200ms | p95 < 100ms | DB index, connection pool max=20 |

## 7. ADR references

| ADR | Áp dụng vào boundary này thế nào |
|-----|----------------------------------|
| ADR-001 (tech stack) | Dùng {framework}, {ORM} |
| ADR-002 (architecture) | Layered: `api → application → domain → infrastructure` (hoặc DDD theo ADR) |
| ADR-003 (auth) | Middleware JWT validate mọi endpoint trừ `/health` |

**Quyết định cục bộ (không lên ADR):** ghi vào KG `decisions` thay vì HLD.

## 8. Risks & Open questions

| # | Risk / Question | Severity | Owner | Status |
|---|----------------|---------|-------|--------|
| R1 | | High/Med/Low | | Open/Resolved |

Blockers thực sự → ghi vào KG `discipline.blockers` (chặn `complete`).
