# Local dev & deploy tối thiểu

> Architect điền khi intake; dev-handoff xác nhận chạy được.

## Prerequisites

- Docker Desktop / Compose v2
- JDK / Node theo `docs/architecture/adr/ADR-001-tech-stack.md`

## Chạy stack local

```bash
cd docs/architecture/infra
docker compose up -d --build
```

## Service URLs

| Service | URL | Ghi chú |
|---------|-----|---------|
| {boundary}-api | http://localhost:808x | … |
| Postgres | localhost:5432 | … |

## Deploy tối thiểu (wave-001)

| Môi trường | Cách deploy | Ghi chú |
|------------|-------------|---------|
| dev | docker compose | Chỉ wave hiện tại |
| staging | TBD | Sau release |

## Health check

```bash
curl -f http://localhost:808x/actuator/health
```

## Troubleshooting

- Port conflict: đổi mapping trong `docker-compose.yml`
- Migration: chạy Flyway trong từng `services/{boundary}/`
