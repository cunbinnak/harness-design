# dev-handoff

Bàn giao dev → QA: build infra, verify coverage, điền handoff doc.

**Agent:** [dev-handoff-agent.md](../agents/dev-handoff-agent.md)

## Điều kiện

- `review-dev complete` đã xong
- Coverage BE ≥ 80%, FE ≥ 60% (gate kiểm tra)
- `docker-compose up --build` chạy được

## Luồng

```
1. Chạy pytest/jest --coverage  →  kiểm tra BE ≥ 80%, FE ≥ 60%
2. docker-compose up --build -d
3. Smoke test: GET /health → 200
4. Điền handoff/{wave-id}.md đầy đủ (service inventory, endpoints, deploy steps)
5. Ghi KG
6. harness complete
```

## Handoff document

Template: `handoff/TEMPLATE.wave.md`
File thực: `handoff/{wave-id}.md` (tạo bởi start-wave, điền bởi dev-handoff-agent)

**Phải điền đủ:**
- Service inventory (port, health endpoint)
- Lệnh khởi động local
- Endpoints cần test
- Coverage numbers
- Vấn đề đã biết

## Chạy

```bash
py scripts/build_command_prompt.py dev-handoff

py scripts/harness.py dev-handoff complete '{
  "coverage_pct": 85,
  "coverage_fe_pct": 65,
  "handoff_ready": true
}'
```

Gate: coverage_pct ≥ 80%, coverage_fe_pct ≥ 60%, handoff_ready: true, docker-compose ≥ 1 service.
