---
name: tech-stack
description: Tham chiếu stack BE/FE — chi tiết nằm trong ADR, không hard-code trong agent.
---

# Tech Stack Skill

## Nguồn sự thật

| ADR | Chủ đề |
|-----|--------|
| `docs/architecture/adr/ADR-001-tech-stack.md` | BE + FE framework, runtime, monorepo |
| `docs/architecture/adr/ADR-002-backend-architecture.md` | Layered vs DDD, module layout |
| `docs/architecture/adr/ADR-003-auth-security.md` | AuthN/Z, JWT/session, CORS |
| `docs/architecture/adr/ADR-004-ui-kit.md` | Design system, i18n, a11y |
| `docs/architecture/adr/ADR-005-pdf-integrations.md` | PDF/export, file storage, email (nếu có) |

Intake bước 3 (architect) **tạo 3–5 ADR** từ template; dev agents **đọc ADR** trước khi code.

## Mặc định gợi ý (chỉ khi ADR chưa chốt)

- **BE:** Java 21 + Spring Boot 3, PostgreSQL, Flyway.
- **FE:** TypeScript + React 18 + Vite, gọi REST OpenAPI.
- **Infra local:** `docs/architecture/infra/docker-compose.yml` (Postgres, Redis tùy ADR).

## Không được

- Đổi stack trong code mà không cập nhật ADR + PROJECT.
- Trộn stack khác nhau giữa hai boundary cùng wave không có lý do trong ADR.

## Done

- Mọi boundary dev/FE agent liệt kê ADR liên quan trong handoff wave.
