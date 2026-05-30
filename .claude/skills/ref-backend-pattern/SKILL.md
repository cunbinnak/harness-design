---
name: ref-backend-pattern
description: Mẫu cấu trúc thư mục + layered architecture cho backend boundary. Tuning theo stack project.
---

# Reference: Backend Project Structure

> **Purpose:** Mô tả cấu trúc thư mục chuẩn của 1 backend boundary trong project. Agent BE load skill này để biết build code theo layout nào.
> **Audience:** `dev:backend`, `fix:backend`, `review:backend`.
> **Tuning:** Mỗi project có thể điều chỉnh tùy stack (Python/Java/Node/Go). Edit file này sau khi chốt ADR tech stack.

## Cấu trúc thư mục chuẩn

```
services/{boundary_id}/
├── api/                # Tầng vào — HTTP handler / Router / Controller
│   ├── routes.{ext}
│   └── {entity}-handler.{ext}
├── domain/             # Business logic
│   ├── {entity}-service.{ext}
│   └── ports/          # Interface repo (Hexagonal)
│       └── {entity}-repository.{ext}
├── infra/              # Adapter — DB, cache, HTTP client outbound
│   ├── {entity}-repo-pg.{ext}
│   └── http-client-{ext_svc}.{ext}
├── dto/                # Request/Response schema + validation
│   ├── {entity}-request.{ext}
│   └── {entity}-response.{ext}
├── config/             # Env, DI wiring
└── tests/
    ├── unit/           # Test domain pure (mock infra)
    └── integration/    # Test với DB/cache thật (testcontainers / compose)
```

## Trách nhiệm từng layer

| Layer | Trách nhiệm | Pattern | Phụ thuộc |
|-------|-------------|---------|-----------|
| `api/` | Parse request, validate DTO, map error → HTTP code | Controller | dto, domain |
| `domain/` | Business rule, orchestrate repo qua port | Service / Use-case | ports (interface) |
| `domain/ports/` | Interface abstraction | Port | (none) |
| `infra/` | DB query, HTTP outbound, cache | Adapter / Repository impl | domain/ports |
| `dto/` | Input/output schema, validation | Pydantic / Zod / Bean | (none) |
| `config/` | Env, DI, app startup | (framework-specific) | (all) |
| `tests/unit/` | Test domain pure, mock infra | (framework test) | domain |
| `tests/integration/` | Test với DB/cache thật | Testcontainers | infra |

## Naming conventions

- **File:** `kebab-case.{ext}` (vd `order-service.py`, `customer-handler.ts`)
- **Class:** `PascalCase` (vd `OrderService`, `CustomerHandler`)
- **Function/Method:** `snake_case` (Python/Ruby) hoặc `camelCase` (Node/Java)
- **Constant:** `UPPER_SNAKE_CASE`
- **Test file:** `{entity}-{layer}-test.{ext}` hoặc `test_{module}.py`

## Forbidden patterns

- `api/` import trực tiếp từ `infra/` — phải qua `domain/`
- `domain/` import từ `infra/` — chỉ qua `domain/ports/` (DIP)
- Logic nghiệp vụ trong `api/` handler — chỉ parse + delegate
- SQL/ORM call trong `domain/` — chỉ trong `infra/`

## Khi nào tuning skill này

- Project dùng framework khác layered (vd: clean architecture, hexagonal đầy đủ) → cập nhật folder names
- Stack đặc biệt (vd: Spring có `repository/`, `entity/`, `mapper/`) → bổ sung
- Microservice với BFF/CQRS → thêm layer riêng

Edit trực tiếp file này khi project có decision khác chuẩn — đồng bộ với `docs/architecture/adr/ADR-002-backend-architecture.md`.

