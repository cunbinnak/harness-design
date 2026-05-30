---
name: ref-backend-conventions
description: Quy Æ°á»›c cáº¥u trÃºc backend â€” layered hoáº·c DDD, package, naming.
---

# Backend Conventions Skill

## Khi dÃ¹ng

Triá»ƒn khai boundary `kind: backend` (`start-dev`, `fix-bugs`). ADR-001/002 quyáº¿t Ä‘á»‹nh stack vÃ  kiáº¿n trÃºc.

## Chá»n mÃ´ hÃ¬nh (ghi trong ADR-002)

| MÃ´ hÃ¬nh | Khi dÃ¹ng | Cáº¥u trÃºc gá»£i Ã½ |
|---------|----------|----------------|
| **Layered** | CRUD, Ã­t domain phá»©c táº¡p | `api/` â†’ `application/` â†’ `domain/` â†’ `infrastructure/` |
| **DDD tactical** | Nghiá»‡p vá»¥ phá»©c táº¡p, aggregate rÃµ | `domain/` (entity, vo, repository port) + `application/` (use case) + `infrastructure/` (adapter) |

Má»™t repo boundary = má»™t module Maven/Gradle root dÆ°á»›i `services/{boundary_id}/`.

## Package (Java vÃ­ dá»¥)

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

## Quy Æ°á»›c báº¯t buá»™c

1. **API** â€” contract theo `docs/architecture/api/api-{boundary}.md`; khÃ´ng Ä‘á»•i breaking khÃ´ng qua ADR.
2. **DB** â€” schema theo `data-model-{boundary}.md`; migration versioned.
3. **Boundary** â€” khÃ´ng import code trá»±c tiáº¿p tá»« `services/other/`; gá»i qua HTTP/event theo `integrations-matrix.md`.
4. **Config** â€” secrets qua env; khÃ´ng commit credentials.
5. **Test** â€” unit (domain/application) + integration (api + DB testcontainer khi cÃ³).

## Done

- Cáº¥u trÃºc thÆ° má»¥c khá»›p ADR-002 vÃ  HLD boundary.
- Build cháº¡y Ä‘Æ°á»£c (`./mvnw` / `./gradlew`).

