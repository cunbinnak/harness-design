---
name: ref-back-end-config
description: Mẫu cấu hình YAML/env cho backend boundary. Sample compose, app config, secrets management.
---

# Reference: Backend Config Patterns

> **Purpose:** Mẫu cấu hình chuẩn cho backend — docker-compose service entry, app YAML, env vars, secrets.
> **Audience:** `dev:backend`, `review:backend`.
> **Tuning:** Theo stack/framework + cloud target.

## docker-compose service entry (mẫu)

```yaml
services:
  {boundary_id}:
    build:
      context: ../../services/{boundary_id}
      dockerfile: Dockerfile
    image: {project_name}/{boundary_id}:latest
    ports:
      - "${BOUNDARY_PORT:-8080}:8080"
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      JWT_SECRET: ${JWT_SECRET}
      LOG_LEVEL: ${LOG_LEVEL:-info}
      PORT: 8080
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 20s
    restart: unless-stopped
```

## .env.example (mẫu)

```env
# Database
DB_USER=postgres
DB_PASSWORD=changeme-in-prod
DB_NAME={boundary_id}_db
DATABASE_URL=postgresql://postgres:changeme-in-prod@localhost:5432/{boundary_id}_db

# Auth
JWT_SECRET=dev-secret-min-32-chars-change-in-prod
JWT_EXPIRY=3600

# App
PORT=8080
LOG_LEVEL=info

# Outbound (nếu có)
# UPSTREAM_SERVICE_URL=http://other-boundary:8080
```

## app.yaml / config.yaml (Python/Spring)

```yaml
# Python (FastAPI / Pydantic Settings)
app:
  name: {boundary_id}
  version: 1.0.0
  port: ${PORT:8080}

database:
  url: ${DATABASE_URL}
  pool_size: 20
  pool_timeout: 30

auth:
  jwt_secret: ${JWT_SECRET}
  jwt_expiry_seconds: ${JWT_EXPIRY:3600}

logging:
  level: ${LOG_LEVEL:info}
  format: json
```

## Secrets management

- **Dev:** `.env` file (gitignore!) + `.env.example` (commit)
- **Prod:** Vault / AWS Secrets Manager / Azure Key Vault — **KHÔNG** commit
- **CI:** Inject qua env vars (GitHub Actions secrets, GitLab CI variables)

## Forbidden config patterns

- Hardcode `DATABASE_URL`, `JWT_SECRET` trong code — luôn qua env
- Commit `.env` thực — chỉ `.env.example`
- Default secret production (`SECRET_KEY=dev`) — fail fast nếu thiếu env
- Log password / token / sensitive data

## Khi nào tuning

- Stack khác (Node `.env` → `config/default.json`)
- Cloud-native (k8s ConfigMap + Secret) → thay docker-compose entry bằng manifest
- Multi-env (dev/staging/prod) → bổ sung `config.{env}.yaml` overrides

Đồng bộ với `docs/architecture/adr/ADR-001-tech-stack.md` + `docs/architecture/infra/docker-compose.yml`.
