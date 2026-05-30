---
name: ref-backend-pattern
description: Cấu trúc thư mục + kiến trúc backend boundary — Layered hoặc DDD tactical theo ADR. Layer responsibilities, forbidden patterns.
---

# Reference: Backend Structure (Layered | DDD)

> **Purpose:** Layout chuẩn 1 backend boundary. Agent BE load để biết build theo cấu trúc nào.
> **Audience:** `dev:backend`, `fix:backend`, `review:backend` — load on-demand từ `rules-backend`.
> **Tách bạch:** cấu trúc = file này · config (application.yml, security, kafka…) = `ref-backend-config` · convention bắt buộc = `rules-backend`.
> **Tuning:** chọn mô hình + đặt tên layer theo **ADR backend-architecture**. Edit file này sau khi chốt ADR.

## 1. Chọn mô hình (ghi trong ADR backend-architecture)

| Mô hình | Khi dùng | Đặc trưng |
|---|---|---|
| **Layered** | CRUD, domain ít phức tạp | Luồng thẳng `api → application → domain → infrastructure` |
| **DDD tactical** | Nghiệp vụ phức tạp, aggregate rõ, nhiều invariant | `domain/` là trung tâm (aggregate + VO + port), `application/` orchestrate use case |

Một boundary = một repo polyrepo, root `services/{prefix}-{boundary}/` (prefix = `project.service_prefix`).

## 2. Layout — Layered

```
services/{prefix}-{boundary}/
├── api/              # Controller/handler + DTO request/response + validation; map error → HTTP code
├── application/      # Use case / application service; orchestrate domain qua port
├── domain/           # Entity, value object, domain service
│   └── ports/        # Interface repository / gateway (DIP)
├── infrastructure/   # Adapter: repo impl (JPA/SQL), messaging, HTTP client outbound, cache
├── config/           # Env binding, DI wiring, app startup  (chi tiết → ref-backend-config)
└── tests/
    ├── unit/         # Domain/application thuần, mock infra
    └── integration/  # api + DB/cache thật (testcontainers / docker-compose)
```

## 3. Layout — DDD tactical

```
services/{prefix}-{boundary}/
├── domain/           # Aggregate root, entity, value object, domain event, ports/ (repo interface)
├── application/      # Use case / command handler; transaction boundary
├── infrastructure/   # Adapter impl các port + persistence + messaging
├── api/              # Inbound adapter (REST/GraphQL controller) + DTO
├── config/           # DI wiring  (chi tiết → ref-backend-config)
└── tests/{unit,integration}
```

## 4. Trách nhiệm từng layer

| Layer | Trách nhiệm | Phụ thuộc |
|---|---|---|
| `api/` | Parse request, validate DTO, map error → HTTP status | dto, application |
| `application/` | Orchestrate use case, transaction, gọi domain qua port | domain, ports |
| `domain/` | Business rule, invariant, entity/VO/aggregate | (none — pure) |
| `domain/ports/` | Interface abstraction (repo/gateway) | (none) |
| `infrastructure/` | Repo impl, DB query, messaging, HTTP outbound, cache | domain/ports |
| `config/` | Env, DI, startup | (all) |

## 5. Forbidden patterns
- `api/` import trực tiếp `infrastructure/` — phải qua `application/`/`domain`.
- `domain/` import `infrastructure/` — chỉ qua `domain/ports/` (DIP).
- Business logic trong `api/` handler — chỉ parse + delegate.
- SQL/ORM call trong `domain/` — chỉ trong `infrastructure/`.
- Import code từ `services/{prefix}-{other}/` — cross-boundary chỉ qua HTTP/event theo `docs/architecture/integrations/INTEG-*.md`.

## 7. Done
- Cấu trúc khớp mô hình chốt trong ADR backend-architecture + `hld-{boundary}.md`.
- API khớp `api-{boundary}.md`; schema khớp `data-model-{boundary}.md`.
- Build chạy được (`./mvnw` / `./gradlew` / runner stack).
