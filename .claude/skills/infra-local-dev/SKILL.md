---
name: infra-local-dev
description: Setup infra cục bộ để test handoff: docker-compose + env + seed.
---

# Infra Local Dev Skill

## Khi load
`dev-handoff-agent` để verify infra cho test agent chạy local.

## Output: `docs/architecture/infra/docker-compose.yml`

Yêu cầu:
1. **Service per boundary** (chỉ những boundary trong wave hiện tại).
2. **Network internal**: container giao tiếp qua service name.
3. **DB seed**: volume `./seed/{boundary}/*.sql` mount vào DB container.
4. **Health check**: mỗi service có `healthcheck` block, max 30s.
5. **Env**: `.env.example` checked-in (template), `.env` gitignored.

## Verify
- `docker-compose up -d` thành công, all services healthy.
- Test agent run `docker-compose exec {service} <test-cmd>` work.

## Done
- `docker-compose.yml` valid, services healthy.
- `.env.example` đủ vars cần thiết.
- README ngắn `docs/architecture/infra/README.md` ghi cách chạy.
