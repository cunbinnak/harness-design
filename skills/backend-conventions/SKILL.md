---
name: backend-conventions
description: Quy ước cấu trúc backend — layered hoặc DDD, package, naming.
---

# Backend Conventions Skill

## Khi dùng

Triển khai boundary `kind: backend` (`start-dev`, `fix-bugs`). ADR-001/002 quyết định stack và kiến trúc.

## Chọn mô hình (ghi trong ADR-002)

| Mô hình | Khi dùng | Cấu trúc gợi ý |
|---------|----------|----------------|
| **Layered** | CRUD, ít domain phức tạp | `api/` → `application/` → `domain/` → `infrastructure/` |
| **DDD tactical** | Nghiệp vụ phức tạp, aggregate rõ | `domain/` (entity, vo, repository port) + `application/` (use case) + `infrastructure/` (adapter) |

Một repo boundary = một module Maven/Gradle root dưới `services/{boundary_id}/`.

## Package (Java ví dụ)

```text
services/{boundary}/
  src/main/java/.../{boundary}/
    api/              # REST controllers, DTO request/response
    application/      # services / use cases
    domain/           # entities, domain services (DDD)
    infrastructure/ # JPA, messaging, clients
  src/main/resources/
    application.yml
    db/migration/     # Flyway/Liquibase
  src/test/java/...
```

## Quy ước bắt buộc

1. **API** — contract theo `docs/architecture/api/api-{boundary}.md`; không đổi breaking không qua ADR.
2. **DB** — schema theo `data-model-{boundary}.md`; migration versioned.
3. **Boundary** — không import code trực tiếp từ `services/other/`; gọi qua HTTP/event theo `integrations-matrix.md`.
4. **Config** — secrets qua env; không commit credentials.
5. **Test** — unit (domain/application) + integration (api + DB testcontainer khi có).

## Done

- Cấu trúc thư mục khớp ADR-002 và HLD boundary.
- Build chạy được (`./mvnw` / `./gradlew`).
