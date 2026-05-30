---
name: dev-handoff
description: "Verify docker-compose + infra ready cho test agent chạy local."
when_state: ['REVIEW_DEV']
sets_stage: DEV_HANDOFF
spawn:
  agent: "dev-handoff-agent"
  skills: [infra-local-dev]
gates: [{type: coverage, field: coverage_pct, min: 80}, {type: flag, field: review_result, expected: pass}]
---

# /dev-handoff

## Mục đích

Chuẩn bị infra để test agent chạy được local. Update `docs/architecture/infra/docker-compose.yml` thêm service mới cho boundary. Verify build local OK.

## Build prompt + spawn

```bash
py scripts/build_prompt.py dev-handoff --boundary order-management
py scripts/harness.py dev-handoff complete '{"coverage_pct": 85, "review_result": "pass", "docker_compose_ok": true}'
```

