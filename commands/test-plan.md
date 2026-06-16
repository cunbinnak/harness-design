---
name: test-plan
description: "Sinh test-case-registry.md cho wave."
when_state: ['DEV_HANDOFF']
sets_stage: TEST_PLAN
spawn:
  agent: "test-plan-agent"
  skills: [test-plan]
gates: [{type: flag, field: docker_compose_ok, expected: true}, {type: flag, field: connectivity_ok, expected: true}, {type: infra_proof}, {type: health_proof}, {type: contract_test_present}]
---

# /test-plan

## Mục đích

Phân tích FEAT + AC -> sinh test cases. Output `tracking/wave-{N}/test-case-registry.md` **format BẢNG** (mỗi TC = 1 hàng: TC/group/type/boundary/feature/AC/pri/pre-condition/steps/expected/note) + Coverage matrix.

**Deferred-scope:** đọc `## Deferred to later waves` của `docs/plans/wave-{N}.md` (+ review-findings wontfix) → TC cho AC/feature deferred tag `@deferred` + `note: deferred wave-N`. test-execute sẽ skip(deferred) → end-wave close sạch tự nhiên (không ép test_result).

## Build prompt + spawn

```bash
py scripts/build_prompt.py test-plan
py scripts/harness.py test-plan complete '{"docker_compose_ok": true, "connectivity_ok": true, "test_cases_count": 15}'
# Gate test-plan: docker_compose_ok + connectivity_ok + infra_proof + health_proof + contract_test_present.
# infra_proof  = parse tracking/{wave}/docker-ps.json → mọi wave_boundaries container State=running.
# health_proof = parse tracking/{wave}/health-proof.json → mọi wave service trả 2xx ở /health/ready
#                (re-verify stack vẫn UP từ dev-handoff sang test). Env-block → force.
# contract_test_present = mỗi consumer (boundary có depends_on trong wave) phải có ≥1 auto-TC
#                group=contract|integration|e2e nối tới nó → chống "thiếu liên kết BE-FE" lọt test. force-able.
```

