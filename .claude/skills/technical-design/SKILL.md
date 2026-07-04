---
name: technical-design
description: Stage DESIGN (/design, solution-architect) — boundary decomposition + kind/stack, ADR, HLD (theo TEMPLATE.hld ZIP)/API/data-model/events per boundary, integrations, docker-compose skeleton. UX/UI KHÔNG thuộc skill này (bước riêng /design-ux, ux-designer-agent). Sau DOMAIN, trước PLAN. Enterprise cross-cutting concerns.
---

# Technical Design Skill

## Khi load
Command **`/design`** (stage **DESIGN** → PLAN) — agent `solution-architect-agent`, sau `/domain-end`.
Input: `docs/architecture/PROJECT.md` + product DOMAIN (`feat/` AC+BR, `epics/`, `business-rules/`, `journeys/`, `personas/`) + charter boundaries (`docs/discovery/boundaries/*/CHARTER.md`).

> **Step 3 chỉ DESIGN (docs).** Scaffold code (`services/{prefix}-{boundary}/`) xảy ra ở `/start-dev` (dev agent), KHÔNG ở đây.

## Deliverable của /design (đúng cái gate design verify)
1. **ADR** `docs/architecture/adr/ADR-NNN-*.md` — **≥ 3**, theo chủ đề (tech-stack, backend-architecture [Layered/Hexagonal], auth, **api-error-convention [envelope + generic codes chung]**, ui-kit, event/messaging…). Theo `TEMPLATE.adr`: context · decision · **Alternatives considered ≥2 (lý do reject)** · consequences (ZIP planning-rules: ADR thiếu ≥2 alternative → reject).
2. **Boundary decomposition** — chốt từ `boundaries_suggested`: mỗi boundary + **kind** (`backend`/`bff`/`web`/`mobile`) + **stack** (set tại đây, vd Java 21 + Spring Boot 3.4). Ghi nhận **tech situational per-boundary** (phát/nhận event, dùng cache/lock, external đặc thù) — input để step 4 gắn `ref_skills` vào MATRIX.
3. **Per boundary**:
   - `hld/hld-{boundary}.md` — **theo `TEMPLATE.hld.md`**: design goals + responsibilities/non-responsibilities · data ownership (no FK) · C4 (context/container/component) + **CHỐT kiến trúc boundary (Layered/Hexagonal) + layer/package** (HLD là source cho dev) · integration summary · key flows (happy + critical error) · auth & permission · consistency & transaction *(nếu multi-write/event)* · failure & resilience *(nếu outbound)* · deployment & scaling · observability · NFR refine. Chi tiết layout file/folder → `ref-{kind}-pattern`.
   - `api/api-{boundary}.md` — **theo `TEMPLATE.api.md`**: contract (REST/OpenAPI 3.1 / GraphQL) + **Domain error code catalog** (→ `{Domain}ErrorEnum`; map mỗi BR / invalid-state transition → 1 code). Common error envelope + generic codes (400/401/403/404/409/429/500) **GIỐNG NHAU mọi boundary** (chuẩn chung, không mỗi boundary 1 kiểu); per-endpoint Errors chỉ **ref** code trong catalog.
   - **`kind=bff` có aggregation ≥2 backend** → thêm `api/bff-aggregation-{boundary}.md` **theo `TEMPLATE.bff-aggregation.md`** (fan-out composition: DataLoader/N+1, timeout cascade, graceful degrade, circuit breaker, caching, resolver). Bổ trợ `api-{boundary}.md` (full schema).
   - `data-model/data-model-{boundary}.md` — **theo `TEMPLATE.data-model.md`**: ownership · entities + **mục đích từng bảng** (lưu gì / phục vụ FEAT nào) · schema (**no FK** — liên kết qua id, app-layer) · state machine (entity có status) · migration approach.
   - `ux/ux-{boundary}.md` + `ux/design-tokens.css` — **KHÔNG làm ở skill này**: UX/UI là bước riêng **`/design-ux`** (agent chuyên môn `ux-designer-agent`, skill `ux-design`) chạy sau khi api-{be}.md sẵn. Architect chỉ đảm bảo FE boundary có HLD + BE contract đủ cho UX consume.
   - `events/{boundary}-events.md` — **theo `TEMPLATE.events.md`**: event phát/nhận (topic, payload schema, consumers, idempotency key).
4. **Integrations** **theo `TEMPLATE.integration-internal.md` / `TEMPLATE.integration-external.md`**: `integrations/INTEG-INT-*.md` (cross-boundary) + `INTEG-EXT-*.md` (external) — **≥ 1**.
5. **`infra/docker-compose.yml`** skeleton local dev (service + DB/cache/broker cho boundary trong scope).

## Enterprise cross-cutting concerns (PHẢI address trong design)
Mỗi concern ghi rõ ở ADR / HLD / API (không để hở):
- **Auth**: JWT/OAuth2 flow + điểm tích hợp RBAC/PBAC.
- **Observability**: structured log schema + metrics endpoint + trace propagation header.
- **Resilience**: circuit breaker / retry boundary / timeout hierarchy cho external call.
- **Caching**: chiến lược L1/L2 + TTL + invalidation.
- **Rate limiting**: per-tenant / per-user.
- **Idempotency**: idempotency key cho mutation/callback endpoint.
- **Pagination**: cursor-based cho list data lớn (không offset).
- **Versioning**: API version (URL `/v1/` hoặc header).
- **Health checks**: `/health/live`, `/health/ready`.

## Phương pháp
1. **Research** — nếu domain phức tạp + có WebSearch: pattern từ production system (CQRS / Saga / Outbox / Event-Sourcing), API design convention, data consistency ở scale, service decomposition. KHÔNG bịa nguồn.
2. Đọc FEAT → chốt boundary list + kind + quan hệ (depends_on, ai gọi ai).
3. ADR nền trước (stack, kiến trúc backend, auth, event) → design sau tuân ADR.
4. Per boundary: HLD (theo `TEMPLATE.hld`) → API (contract + error) → data-model (backend) → events. (FE boundary: HLD ở đây; UX = `/design-ux` sau khi api sẵn.)
5. Integrations: cross-boundary (sync HTTP / async event) + external.
6. docker-compose skeleton.

## Flow (/design)
- Iterate với user: trình bày ADR + design per boundary → "OK chưa? chỉnh gì?" → sửa. Lặp tới khi user confirm (không giới hạn số vòng).
- **Self-loop refine**: chưa vừa ý → user chạy lại `/design` (re-spawn DESIGN→DESIGN, KHÔNG advance, idempotent update). Khi confirm toàn bộ → return `user_confirmed: true` → main chạy `/design-end` (`py scripts/harness.py design-end complete '{}'`, gate design_gate: ADR≥3 + INTEG + per-boundary completeness) → DESIGN → PLAN.

## Quality checklist
- [ ] ADR/HLD nhất quán với `docs/architecture/ARCHITECTURE-PRINCIPLES.md` (layering hexagonal BE / FE layers, contract-first, no-business-logic-in-FE, decision-traceability DECISION-REF, anti-patterns); deviation phải có ADR override.
- [ ] ≥ 3 ADR (theo chủ đề, có decision + **alternatives ≥2** + consequences).
- [ ] Mỗi boundary chốt kind + stack; HLD theo `TEMPLATE.hld` (goals/responsibilities, data ownership, C4, flows happy+error, auth, deployment; consistency/failure khi áp dụng) + API.
- [ ] API theo `TEMPLATE.api`: có **Domain error catalog** (→ `{Domain}ErrorEnum`, map mọi BR/invalid-state → code); common envelope + generic codes **giống nhau mọi boundary**; per-endpoint chỉ ref code (không đẻ code mới); đủ error responses; pagination cursor; versioning.
- [ ] Backend boundary có data-model **theo TEMPLATE.data-model** (mỗi bảng có mục đích; no FK — liên kết qua id; state machine cho entity có status). (UX cho FE boundary do `/design-ux` — gate `/design-end` vẫn đòi đủ.)
- [ ] Boundary phát/nhận event có `{boundary}-events.md`.
- [ ] Ref FEAT/EP/BR/persona bằng id canonical ĐẦY ĐỦ (`FEAT-{prefix}-NNN`, `PERSONA-{prefix}-NNN`…), KHÔNG rút gọn (`FEAT-NNN`) — tránh ID drift, giữ traceability resolve được.
- [ ] **Trả nợ TODO-engineer (gate `todo_resolved` @/design-end):** mọi `TODO engineer` / `TBD (DESIGN)` translator để lại trong eng feat/BR đã ĐIỀN — BR `enforcement_location` chỉ đúng nơi enforce (api/data-model/event handler), FEAT `consumes_contracts` trỏ contract thật. Chưa chốt → Open question có chủ, KHÔNG để TBD.
- [ ] **Contract frontmatter khớp topology (gate `contract_graph_parity` @/plan):** api-*.md `producer`/`consumers[]`, INTEG-INT `consumer`/`producer`, events subscriber dùng đúng `boundary_id` — sẽ bị đối chiếu MATRIX depends_on 2 chiều.
- [ ] ≥ 1 integration thật (INTEG-INT / INTEG-EXT).
- [ ] Enterprise concerns đều addressed: auth · observability · resilience · caching · rate limit · idempotency · health check.
- [ ] `infra/docker-compose.yml` skeleton có service cho boundary trong scope.
- [ ] (Nếu research) ≥ 1 nguồn thật, ghi link.

## Done
- ADR (≥3) + per-boundary HLD/API/data-model/UX/events + integrations (≥1) + docker-compose skeleton + enterprise concerns addressed (khớp gate design_gate); user đã confirm → DESIGN → PLAN.
