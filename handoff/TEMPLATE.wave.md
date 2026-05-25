# Dev Handoff — {wave-id}

> **Purpose:** Bàn giao wave từ dev → QA → stakeholder UAT. Chứa thông tin **runtime/operational** để vận hành + test.
> **Owner:** §1-§4 `dev-handoff` agent; §5 `end-wave` agent (UAT guide); §6 `done-wave` agent (final sign-off).
> **Audience:** `test-execute`, stakeholder UAT, `done-wave`.
> **Out of scope:**
> - Architecture → `docs/architecture/hld/`
> - API spec → `docs/architecture/api/`
> - Test cases → `tracking/waves/{wave-id}/test-cases.md`
> - Test results → `tracking/waves/{wave-id}/test-results.md`
> - Bugs → `tracking/waves/{wave-id}/bugs/`

---

## 1. Summary

| | |
|---|---|
| **Wave** | {wave-id} ({wave-title}) |
| **Stage hiện tại** | (cập nhật theo từng giai đoạn) |
| **Features hoàn thành** | FEAT-XXX, FEAT-YYY (link [`docs/architecture/feat/`](../docs/architecture/feat/)) |
| **Boundaries** | (list boundary_id) |
| **Coverage BE / FE** | {pct}% / {pct}% (ngưỡng 80 / 60) |
| **Build status** | ✅ / ❌ |

## 2. Service inventory (runtime)

> QA cần spin up trước khi test. Stakeholder UAT dùng để truy cập app.

| Service | Boundary | Port | Health endpoint | Tech stack |
|---------|----------|------|----------------|------------|
| {boundary-api} | {boundary} | {HOST_PORT} | `GET /health` | {lang}/{framework} |
| postgres | db | 5432 | — | PostgreSQL {ver} |
| redis (nếu có) | cache | 6379 | — | Redis {ver} |

## 3. Start local

> Chi tiết command + env: [`docs/architecture/infra/local-dev.md`](../docs/architecture/infra/local-dev.md) (không lặp ở đây).

```bash
cd docs/architecture/infra
cp .env.example .env       # chỉnh DATABASE_URL, JWT_SECRET nếu cần
docker-compose up --build -d
docker-compose ps          # tất cả services Up (healthy)
curl http://localhost:{PORT}/health   # expect 200
```

## 4. Endpoints (count + reference)

| Boundary | Số endpoints | Spec |
|----------|-------------|------|
| {boundary-A} | 6 | [`api-{boundary-A}.md`](../docs/architecture/api/) |
| {boundary-B} | 4 | [`api-{boundary-B}.md`](../docs/architecture/api/) |

Test token (dev only): `Authorization: Bearer {dev_jwt_token}` (xem `.env`).

## 5. UAT Instructions (sau `end-wave`)

> Stakeholder/QA verify ở stage MANUAL_TEST. Bug log → `tracking/waves/{wave-id}/bugs/` với `origin: manual`.

1. App URL: `http://localhost:{PORT}` (xem §2 service inventory)
2. Test credentials: (lấy từ `.env` dev account)
3. Manual test cases: `tracking/waves/{wave-id}/test-cases.md` — filter cột `Type: manual`
4. Ghi kết quả: `tracking/waves/{wave-id}/manual-test-log.md`
5. Nếu phát hiện bug:
   ```
   tracking/waves/{wave-id}/bugs/BUG-{n}-{short}.md
     frontmatter:
       origin: manual
       severity: medium
       status: open
   ```
   Báo dev → `/fix-bugs --boundary X` → `/retest` (smart route về MANUAL_TEST).
6. Clean → `/done-wave` (teardown + reset).

## 6. Known issues & deferred

| # | Type | Mô tả | Plan |
|---|------|-------|------|
| | bug-known | (low-severity, không block release) | wave kế |
| | tech-debt | (refactor sau) | wave kế |
| | deferred | (FEAT defer) | wave-XXX |

## 7. Decisions in wave (link KG)

| ID | Decision | KG |
|----|----------|-----|
| DEC-XXX | (1 dòng tóm tắt) | `knowledge-base/shared.knowledge-graph.yaml` |

## 8. Sign-off (cập nhật khi `end-wave` / `done-wave`)

### Wave Shipped (sau `end-wave`)

- **Date:** {date}
- **Released by:** dev team
- **Manual test ready:** ✅
- **Infra status:** Running (do NOT stop until done-wave)

### Wave Done (sau `done-wave`)

- **Date:** {date}
- **UAT result:** ✅ Approved by {stakeholder}
- **Bugs fixed during UAT:** BUG-XXX (hoặc "None")
- **Infra:** Stopped (`docker-compose down`)
- **Next wave:** wave-{N+1} (nếu có plan) / TBD
