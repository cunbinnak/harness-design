---
name: ref-backend-config
description: >
  Reference patterns cho backend service configuration và scaffold — application.yml (Spring Boot 3.4),
  profiles (local/dev/staging/prod), env var binding, secrets management (Azure Key Vault),
  Spring Security OAuth2 Resource Server (JWT), database connection pooling (HikariCP),
  Kafka consumer/producer config, Redis cache config, Temporal workflow client config,
  observability config, Gradle setup, Dockerfile (multi-stage), .gitignore.
  Consult khi scaffold boundary mới hoặc khi cần config pattern cụ thể.
---

# Reference — Backend Config Patterns

> Config patterns cho backend service. Consult khi scaffold boundary mới hoặc cần config cụ thể.

---

## 1. Config File Structure

### Spring Boot 3.4 (e.g. Spring Boot)

```yaml
# application.yml — base config
spring:
  application:
    name: ${SPRING_APPLICATION_NAME:{{service-name}}}
  profiles:
    active: ${SPRING_PROFILES_ACTIVE:local}

server:
  port: ${SERVER_PORT:{{default-port}}}
  servlet:
    context-path: ${CONTEXT_PATH:/{{boundary}}}

# Profile-specific overrides
---
spring:
  config:
    activate:
      on-profile: local
  datasource:
    url: jdbc:postgresql://${DB_HOST:localhost}:${DB_PORT:5432}/${DB_NAME:{{boundary}}_service}
    username: ${DB_USER:{{project_code}}}
    password: ${DB_PASSWORD:dev_password}
```

### Node.js 22 (e.g. Node.js + TypeScript)

```typescript
// src/config/index.ts
import { z } from 'zod';

const schema = z.object({
  NODE_ENV: z.enum(['local', 'dev', 'staging', 'prod']).default('local'),
  PORT: z.coerce.number().default({{default-port}}),
  UPSTREAM_{{SERVICE}}_URL: z.string().url(),
  REDIS_URL: z.string().url().default('redis://localhost:6379'),
});

export const config = schema.parse(process.env);
```

## 2. Profile Strategy

| Profile | Purpose |
|---|---|
| `local` | Developer machine — Compose stack per `ref-local-dev-contract` skill |
| `dev` | Shared dev environment — cloud-hosted, ephemeral data |
| `sit` | System Integration Test — production-like, managed services |
| `prod` | Production — hardened, managed services |

**Profile files bắt buộc** — mỗi service PHẢI có đủ:

```
src/main/resources/
├── application.yml          ← base (shared defaults)
├── application-dev.yml      ← dev env overrides
├── application-sit.yml      ← SIT env overrides
└── application-prod.yml     ← prod env overrides
```

Mỗi profile file override env-specific values: DB URL, secrets ref, log level, feature flags, Kafka bootstrap, cache TTL. KHÔNG để tất cả config trong `application.yml` base rồi chỉ dùng env var — mỗi môi trường phải có file riêng để dễ review và audit.

Default profile resolution:
- Local developer: fallback to `local` (base `application.yml` đủ cho local dev)
- CI/dev: env var `SPRING_PROFILES_ACTIVE=dev`
- SIT: env var `SPRING_PROFILES_ACTIVE=sit`
- Production: env var `SPRING_PROFILES_ACTIVE=prod`

## 3. Environment Variable Conventions

```bash
# Service identity
SPRING_APPLICATION_NAME={{boundary}}-service
SPRING_PROFILES_ACTIVE=local
CONTEXT_PATH=/{{boundary}}          # API gateway route prefix — mỗi boundary có path riêng

# Database
DB_HOST=postgres               # hostname trong compose network
DB_PORT=5432
DB_NAME={{project_code}}_{{boundary}}_service
DB_USER={{project_code}}
DB_PASSWORD={{secret_ref_or_env_value}}

# Cache (if applicable)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD={{secret_ref}}

# Message broker (if applicable)
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_CONSUMER_GROUP_ID={{boundary}}-service-consumer

# OIDC (if applicable)
OIDC_ISSUER_URI=http://keycloak:8080/realms/{{REALM}}
OIDC_CLIENT_ID={{boundary}}-service
OIDC_CLIENT_SECRET={{secret_ref}}
```

## 4. Secrets Manager Integration

### Pattern: Config refs → resolver

```yaml
# Config declares refs, not values
datasource:
  password: ${DB_PASSWORD_REF:secret://{{secrets_manager_path}}/db-password}

oidc:
  client-secret: ${OIDC_SECRET_REF:secret://{{secrets_manager_path}}/oidc-client-secret}
```

### Secrets Manager options

| Manager | When to use |
|---|---|
| Azure Key Vault (e.g. AWS Secrets Manager) | Production AWS deployment |
| HashiCorp Vault | Multi-cloud or on-prem |
| Kubernetes Secrets | Standalone K8s với sealed-secrets |
| `.env` files (dev only) | Local development (Compose stack) |

## 5. Connection Pooling

### Database (e.g. HikariCP for Java)

```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: ${DB_POOL_MAX_SIZE:10}
      minimum-idle: ${DB_POOL_MIN_IDLE:2}
      connection-timeout: ${DB_CONN_TIMEOUT_MS:30000}
      idle-timeout: ${DB_IDLE_TIMEOUT_MS:600000}
      max-lifetime: ${DB_MAX_LIFETIME_MS:1800000}
```

Size based on: `(max concurrent requests) / (services per DB)` + buffer.

### JPA / Hibernate batch write (bắt buộc khi dùng `saveAll()`)

```yaml
spring:
  jpa:
    open-in-view: false
    hibernate:
      ddl-auto: validate
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect
        jdbc:
          batch_size: 50        # thiếu config này saveAll() vẫn gửi N INSERT riêng lẻ
        order_inserts: true     # group INSERT by entity type để batch hiệu quả
        order_updates: true
        default_schema: ${DB_SCHEMA:{{boundary}}}
```

### HTTP Client

```yaml
http-client:
  connect-timeout-ms: 5000
  read-timeout-ms: 10000
  max-connections: 50
  max-connections-per-host: 10
```

## 6. Kafka Config

```yaml
spring:
  kafka:
    bootstrap-servers: ${KAFKA_BOOTSTRAP_SERVERS:kafka:9092}
    producer:
      key-serializer: org.apache.kafka.common.serialization.StringSerializer
      value-serializer: org.apache.kafka.common.serialization.StringSerializer
      acks: all               # wait for all in-sync replicas — at-least-once guarantee
      retries: 3
      properties:
        enable.idempotence: true
    consumer:
      group-id: ${KAFKA_CONSUMER_GROUP_ID:{{boundary}}-consumer}
      auto-offset-reset: earliest
      enable-auto-commit: false
      key-deserializer: org.apache.kafka.common.serialization.StringDeserializer
      value-deserializer: org.apache.kafka.common.serialization.StringDeserializer
    listener:
      ack-mode: manual        # manual ack — consumer controls offset commit
```

```bash
# Env vars
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_CONSUMER_GROUP_ID={{boundary}}-consumer
```

## 7. Observability Config

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,metrics,info,prometheus
  metrics:
    tags:
      application: ${spring.application.name}
      env: ${spring.profiles.active}

logging:
  pattern:
    console: '%d{ISO8601} [%thread] %-5level %logger{36} [traceId=%X{traceId}] - %msg%n'
```

## 10. Forbidden Actions

- KHÔNG hardcode secrets trong config files
- KHÔNG commit `.env` với real production values (use `.env.example` template)
- KHÔNG check credentials vào git (use `.gitignore`)
- KHÔNG set production defaults without env var override path
- KHÔNG ignore profile activation logic

## 11. Gradle Setup

```groovy
// build.gradle — Groovy DSL (KHÔNG build.gradle.kts)
plugins {
    id 'org.springframework.boot' version '3.4.0'
    id 'io.spring.dependency-management' version '1.1.4'
    id 'java'
    id 'jacoco'
}

group = 'com.{{project_code}}'
sourceCompatibility = '21'

dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    implementation 'org.springframework.boot:spring-boot-starter-security'
    implementation 'org.springframework.boot:spring-boot-starter-oauth2-resource-server'
    implementation 'org.springframework.boot:spring-boot-starter-actuator'
    implementation 'org.springframework.boot:spring-boot-starter-data-redis'
    implementation 'org.springframework.kafka:spring-kafka'
    implementation 'org.flywaydb:flyway-core'
    implementation 'org.flywaydb:flyway-database-postgresql'
    implementation 'org.postgresql:postgresql'
    implementation 'org.mapstruct:mapstruct:1.5.5.Final'
    compileOnly 'org.projectlombok:lombok'
    annotationProcessor 'org.projectlombok:lombok'
    annotationProcessor 'org.mapstruct:mapstruct-processor:1.5.5.Final'
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.testcontainers:junit-jupiter'
    testImplementation 'org.testcontainers:postgresql'
    testImplementation 'org.testcontainers:kafka'
    // BẮT BUỘC cho JUnit 5 Platform
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
}

jacocoTestCoverageVerification {
    violationRules {
        rule { limit { minimum = 0.80 } }
    }
}
check.dependsOn jacocoTestCoverageVerification
```

> Gradle wrapper PHẢI commit: `gradle wrapper --gradle-version 8.7`

## 12. Spring Security — OAuth2 Resource Server

> SecurityConfig đầy đủ (filterChain, JWT converter, TenantContextFilter, HMAC, SpEL sandbox) → load skill `ref-backend-security`

Config `application.yml`:
```yaml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          jwk-set-uri: ${JWKS_URI}
```

## 13. Dockerfile

```dockerfile
FROM eclipse-temurin:21-jdk-alpine AS builder
WORKDIR /app
COPY gradlew settings.gradle build.gradle ./
COPY gradle ./gradle
RUN ./gradlew dependencies --no-daemon -q
COPY src ./src
RUN ./gradlew bootJar --no-daemon -x test && \
    find build/libs -name '*.jar' ! -name '*plain*' -exec cp {} build/libs/app.jar \;

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
COPY --from=builder /app/build/libs/app.jar app.jar
USER appuser
EXPOSE ${SERVER_PORT:-8080}
ENTRYPOINT ["java", "-jar", "app.jar"]
```

> Hoặc tắt plain jar trong `build.gradle` (`jar { enabled = false }`) thay vì rename.

## 13.1 RSA Key Generation (optional — chỉ khi service cần load key từ file)

```bash
# infra/scripts/generate-keys.sh — chạy một lần trước docker compose up
#!/bin/sh
set -e
DIR="$(dirname "$0")/../keys"
mkdir -p "$DIR"
[ -f "$DIR/jwt-private.pem" ] && echo "Keys exist." && exit 0
openssl genrsa -out "$DIR/jwt-private.pem" 2048
openssl rsa -in "$DIR/jwt-private.pem" -pubout -out "$DIR/jwt-public.pem"
```

docker-compose mount:
```yaml
volumes:
  - ./keys/jwt-private.pem:/app/keys/jwt-private.pem:ro
  - ./keys/jwt-public.pem:/app/keys/jwt-public.pem:ro
```

`.gitignore`: thêm `infra/keys/` và `*.pem`.

## 14. .gitignore

```gitignore
build/
.gradle/
*.class
!gradle/wrapper/gradle-wrapper.jar
.idea/
*.iml
.vscode/
.env
.env.local
application-local.yml
application-secrets.yml
*.log
logs/
```

## Change Log

| Date | Summary |
|---|---|
| 2026-05-02 | Initial backend-config reference skill |
| 2026-05-07 | Add §11 Gradle, §12 Spring Security OAuth2, §13 Dockerfile, §14 .gitignore |
