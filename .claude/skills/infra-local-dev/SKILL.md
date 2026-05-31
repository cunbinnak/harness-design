---
name: infra-local-dev
description: Setup + verify infra local cho test handoff — docker-compose service per boundary + DB/redis/kafka, network internal, healthcheck, chạy migrations, verify. dev-handoff.
---

# Infra Local Dev Skill

## Khi load
`dev-handoff-agent` ở `/dev-handoff` (state DEV_HANDOFF). **Mục tiêu:** khi DONE, `test-execute` agent chạy được local — app boundary + DB/Redis/Kafka **healthy**, schema **migrated**.
Input: `docs/architecture/infra/docker-compose.yml` (skeleton từ intake step 3) + boundaries trong wave (MATRIX) + `data-model-{boundary}.md` (migrations).

## Output: `docs/architecture/infra/docker-compose.yml` (1 vị trí chuẩn)
Yêu cầu:
1. **Service per boundary** — 1 app container cho mỗi boundary trong **wave hiện tại** (build từ `services/{prefix}-{boundary}/`), + infra (DB/cache/broker) chúng dùng. KHÔNG thêm boundary ngoài wave, không service thừa.
2. **Network internal** — container gọi nhau qua **service name** (vd app → `postgres:5432`, `redis:6379`, `kafka:9092`), KHÔNG `localhost` bên trong container.
3. **Healthcheck** mỗi service (interval/retries); app `depends_on` infra với `condition: service_healthy`.
4. Volume cho DB persist; dev creds **inline** (dev-only, không phải secret — không cần .env riêng).

```yaml
services:
  # --- app service per boundary trong wave (build từ code boundary) ---
  demo-order-management:                 # = {prefix}-{boundary}
    build: ../../../services/demo-order-management   # boundary có Dockerfile (ref-backend-config)
    ports: ["8080:8080"]
    environment:                          # host = service name (network internal)
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/app_dev
      REDIS_URL: redis://redis:6379
      KAFKA_SERVER_HOST: kafka:9092
    depends_on:
      postgres: { condition: service_healthy }
    healthcheck: { test: ["CMD","curl","-f","http://localhost:8080/health/ready"], interval: 10s, retries: 12 }
  # --- infra (chỉ cái boundary trong wave dùng) ---
  postgres:
    image: postgres:16-alpine
    environment: { POSTGRES_DB: app_dev, POSTGRES_USER: postgres, POSTGRES_PASSWORD: postgres }
    ports: ["5432:5432"]
    volumes: ["pg_data:/var/lib/postgresql/data"]
    healthcheck: { test: ["CMD-SHELL","pg_isready -U postgres"], interval: 5s, retries: 10 }
  redis:                                  # bỏ nếu không dùng
    image: redis:7-alpine
    ports: ["6379:6379"]
    healthcheck: { test: ["CMD","redis-cli","ping"], interval: 5s, retries: 10 }
  zookeeper:                              # chỉ khi dùng Kafka
    image: confluentinc/cp-zookeeper:7.6.0
    environment: { ZOOKEEPER_CLIENT_PORT: 2181 }
  kafka:                                  # bỏ nếu không dùng
    image: confluentinc/cp-kafka:7.6.0
    ports: ["9092:9092"]
    depends_on: [zookeeper]
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    healthcheck: { test: ["CMD","kafka-broker-api-versions","--bootstrap-server","localhost:9092"], interval: 10s, retries: 15 }
volumes: { pg_data: {} }
```

## Verify (BẮT BUỘC chạy lệnh + đọc output, không chỉ viết file)
```bash
cd docs/architecture/infra && docker compose up -d --build
# đợi tới khi tất cả healthy (max ~60s)
for i in $(seq 1 12); do
  H=$(docker compose ps --format json 2>/dev/null | grep -c '"Health":"healthy"' || echo 0)
  T=$(docker compose ps -q | wc -l); echo "[$i] healthy $H/$T"; [ "$H" = "$T" ] && break; sleep 5
done
docker compose ps
docker compose exec postgres pg_isready -U postgres   # "accepting connections"
docker compose exec redis redis-cli ping              # "PONG" (nếu có)
curl -f http://localhost:8080/health/ready            # app boundary ready
```
Service fail → `docker compose logs <svc> --tail=50` → diagnose → sửa compose → `docker compose down && up -d --build` → lặp. KHÔNG qua bước migration khi còn service fail.

## Migrations (sau khi infra healthy)
Chạy migration của mỗi backend boundary từ `services/{prefix}-{boundary}/`, theo stack:
```bash
# Java/Flyway
mvn -q flyway:migrate -Dflyway.url="jdbc:postgresql://localhost:5432/app_dev" -Dflyway.user=postgres -Dflyway.password=postgres
# Liquibase / Prisma (npx prisma migrate deploy) / Alembic (alembic upgrade head) / raw: psql ... -f schema.sql
```
Verify schema thật:
```bash
psql "postgresql://postgres:postgres@localhost:5432/app_dev" -c "\dt" \
  -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';"
```
`count = 0` → migration chưa chạy, debug ngay.

## Done (gate `/dev-handoff`: `docker_compose_ok=true`)
- `docker-compose.yml` valid, **mọi service (app boundary + infra) healthy**; migrations applied (schema có tables).
- Test agent chạy được: `docker compose exec {service} <test-cmd>` / `curl localhost:{port}/health`.

> Production deploy (Dockerfile/Helm/CI-CD) KHÔNG thuộc skill này — state machine hiện kết thúc ở DONE (UAT), chưa có stage deploy.
