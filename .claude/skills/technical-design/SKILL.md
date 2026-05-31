---
name: technical-design
description: Intake step 3 (solution-architect) — boundary decomposition + kind/stack, ADR, HLD (theo TEMPLATE.hld: goals/responsibilities/data-ownership/C4/flows/auth/consistency/failure/deploy)/API/data-model/UX/events per boundary, integrations, docker-compose skeleton. Enterprise cross-cutting concerns.
---

# Technical Design Skill

## Khi load
`/intake-requirement` **step 3** — agent `solution-architect-agent`, sau step 2.
Input: `PROJECT.md` + `FEAT-*.md` (đã có AC + BR + `boundaries_suggested` từ step 2).

> **Step 3 chỉ DESIGN (docs).** Scaffold code (`services/{prefix}-{boundary}/`) xảy ra ở `/start-dev` (dev agent), KHÔNG ở đây.

## Deliverable của step 3 (đúng cái command verify)
1. **ADR** `docs/architecture/adr/ADR-NNN-*.md` — **≥ 3**, theo chủ đề (tech-stack, backend-architecture [Layered/Hexagonal], auth, ui-kit, event/messaging…). Theo `TEMPLATE.adr`: context · decision · consequences.
2. **Boundary decomposition** — chốt từ `boundaries_suggested`: mỗi boundary + **kind** (`backend`/`bff`/`web`/`mobile`) + **stack** (set tại đây, vd Java 21 + Spring Boot 3.4).
3. **Per boundary**:
   - `hld/hld-{boundary}.md` — **theo `TEMPLATE.hld.md`**: design goals + responsibilities/non-responsibilities · data ownership (no FK) · C4 (context/container/component **logic**) + integration summary · key flows (happy + critical error) · auth & permission · consistency & transaction *(nếu multi-write/event)* · failure & resilience *(nếu outbound)* · deployment & scaling · observability · NFR refine. KHÔNG vẽ source-folder (→ `ref-{kind}-pattern`).
   - `api/api-{boundary}.md` — contract (REST/OpenAPI 3.1 hoặc GraphQL schema); document **đủ error responses** (400/401/403/404/409/429/500).
   - `data-model/data-model-{boundary}.md` — schema (backend; no FK theo convention).
   - `ux/ux-{boundary}.md` — flows + screens (mỗi FE boundary 1 file) → **invoke skill `ux-design`** (user flow, wireframe, UI states, a11y, permission UI).
   - `events/{boundary}-events.md` — boundary phát/nhận event.
4. **Integrations** `integrations/INTEG-INT-*.md` (cross-boundary) + `INTEG-EXT-*.md` (external) — **≥ 1**.
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
1. **Research (optional)** — nếu domain phức tạp + có WebSearch: pattern từ production system (CQRS / Saga / Outbox / Event-Sourcing), API design convention, data consistency ở scale, service decomposition. KHÔNG bịa nguồn.
2. Đọc FEAT → chốt boundary list + kind + quan hệ (depends_on, ai gọi ai).
3. ADR nền trước (stack, kiến trúc backend, auth, event) → design sau tuân ADR.
4. Per boundary: HLD (theo `TEMPLATE.hld`) → API (contract + error) → data-model (backend) / UX (FE) → events.
5. Integrations: cross-boundary (sync HTTP / async event) + external.
6. docker-compose skeleton.

## Flow step 3 (theo command)
- Iterate với user: trình bày ADR + design per boundary → "OK chưa? chỉnh gì?" → sửa. Lặp tới khi user confirm (không giới hạn số vòng).
- Sau user confirm: return RETURN SCHEMA với `user_confirmed: true`, `step: 3`.

## Quality checklist
- [ ] ≥ 3 ADR (theo chủ đề, có decision + consequences).
- [ ] Mỗi boundary chốt kind + stack; HLD theo `TEMPLATE.hld` (goals/responsibilities, data ownership, C4, flows happy+error, auth, deployment; consistency/failure khi áp dụng) + API.
- [ ] API document đủ error responses (400/401/403/404/409/429/500); pagination cursor cho list lớn; versioning.
- [ ] Backend boundary có data-model (no FK); FE boundary có UX.
- [ ] Boundary phát/nhận event có `{boundary}-events.md`.
- [ ] ≥ 1 integration thật (INTEG-INT / INTEG-EXT).
- [ ] Enterprise concerns đều addressed: auth · observability · resilience · caching · rate limit · idempotency · health check.
- [ ] `infra/docker-compose.yml` skeleton có service cho boundary trong scope.
- [ ] (Nếu research) ≥ 1 nguồn thật, ghi link.

## Done
- ADR (≥3) + per-boundary HLD/API/data-model/UX/events + integrations (≥1) + docker-compose skeleton + enterprise concerns addressed (khớp verify intake step 3); user đã confirm.
