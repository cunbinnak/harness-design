# API — {boundary_id}

> **Purpose:** Contract đầy đủ của endpoints/operations mà `{boundary_id}` expose.
> **Owner:** `intake:solution-architect`.
> **Audience:** `dev:backend` (implement), `dev:frontend` (gọi), `test-plan` / `test-execute` (test contract), `fix:*`.
> **Out of scope:**
> - Implementation chi tiết → [`../hld/hld-{boundary_id}.md`](../hld/)
> - DB schema → [`../data-model/data-model-{boundary_id}.md`](../data-model/)
> - UI usage → [`../ux/ux-{boundary_id}.md`](../ux/) (nếu FE)
> - Cross-boundary call chains → [`../integrations-matrix.md`](../integrations-matrix.md)

---

## Base info

| | |
|---|---|
| **Base URL (dev)** | `http://localhost:{PORT}` |
| **Base URL (prod)** | TBD |
| **Versioning** | URL path (`/v1/...`) |
| **Auth scheme** | Bearer JWT (header `Authorization: Bearer <token>`) — trừ endpoints public |
| **Content-Type** | `application/json` |
| **OpenAPI spec** | (nếu có: `services/{boundary_id}/openapi.yaml`) |

## Common error format

```json
{
  "error": "ERR_CODE",
  "message": "Human-readable description",
  "details": { "field": "extra info" }
}
```

## Common error codes

| Code | HTTP | Khi nào |
|------|------|---------|
| `VALIDATION_ERROR` | 400 | DTO không hợp lệ |
| `UNAUTHORIZED` | 401 | Thiếu/sai token |
| `FORBIDDEN` | 403 | Không có quyền |
| `NOT_FOUND` | 404 | Resource không tồn tại |
| `CONFLICT` | 409 | Trùng dữ liệu / state conflict |
| `INTERNAL_ERROR` | 500 | Lỗi server |

---

## Endpoints

### Summary table

| Method | Path | Mục đích | Auth | Implements |
|--------|------|----------|------|------------|
| GET | `/health` | Health check | none | (smoke test) |
| POST | `/v1/{resource}` | Tạo mới | Bearer | FEAT-XXX:AC-1 |
| GET | `/v1/{resource}` | Danh sách | Bearer | FEAT-XXX:AC-2 |
| GET | `/v1/{resource}/{id}` | Chi tiết | Bearer | FEAT-XXX:AC-3 |
| PUT | `/v1/{resource}/{id}` | Cập nhật | Bearer | FEAT-XXX:AC-4 |
| DELETE | `/v1/{resource}/{id}` | Xóa | Bearer | FEAT-XXX:AC-5 |

### Endpoint detail

#### `POST /v1/{resource}` — Tạo mới

**Auth:** Bearer · **Implements:** FEAT-XXX:AC-1 · **Business rules:** BR-1, BR-2

**Request:**

```http
POST /v1/{resource}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "string (2-100 chars, required)",
  "description": "string (max 500, optional)",
  "status": "PENDING | ACTIVE (default: PENDING)"
}
```

**Response — 201 Created:**

```json
{
  "id": "uuid",
  "name": "string",
  "description": "string | null",
  "status": "PENDING",
  "created_at": "2026-01-15T10:30:00Z",
  "created_by": "user-id"
}
```

**Errors:**

| HTTP | Code | Trigger |
|------|------|---------|
| 400 | `VALIDATION_ERROR` | `name` < 2 ký tự hoặc thiếu |
| 401 | `UNAUTHORIZED` | Token invalid |
| 409 | `CONFLICT` | `name` trùng (BR-1: unique) |

---

#### `GET /v1/{resource}/{id}` — Lấy chi tiết

**Auth:** Bearer · **Implements:** FEAT-XXX:AC-3

**Request:**

```http
GET /v1/{resource}/{id}
Authorization: Bearer <token>
```

**Response — 200 OK:**

```json
{
  "id": "uuid",
  "name": "string",
  ...
}
```

**Errors:**

| HTTP | Code | Trigger |
|------|------|---------|
| 404 | `NOT_FOUND` | id không tồn tại |
| 401 | `UNAUTHORIZED` | Token invalid |

---

(Lặp pattern trên cho mỗi endpoint còn lại: PUT, DELETE, GET list...)

---

## Rate limits / Quotas (nếu có)

| Endpoint | Limit | Window |
|----------|-------|--------|
| (vd) `POST /v1/auth/login` | 5 requests | 1 min/IP |
| Default | 100 requests | 1 min/user |

## Backward compatibility

- **Breaking change** = phải bump version path (`/v2/...`)
- **Non-breaking:** thêm field optional, thêm endpoint mới
- Deprecation: ghi `Deprecation` header + `Sunset` date
