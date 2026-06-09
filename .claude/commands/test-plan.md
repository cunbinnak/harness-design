---
name: test-plan
description: "Sinh test-case-registry.md cho wave."
when_state: ['DEV_HANDOFF']
sets_stage: TEST_PLAN
spawn:
  agent: "test-plan-agent"
  skills: [test-plan]
gates: [{type: flag, field: docker_compose_ok, expected: true}]
---

# /test-plan

## Mục đích

Phân tích FEAT + AC -> sinh test cases. Output `tracking/wave-{N}/test-case-registry.md` **format BẢNG** (mỗi TC = 1 hàng: TC/group/type/boundary/feature/AC/pri/pre-condition/steps/expected/note) + Coverage matrix.

## Build prompt + spawn

```bash
py scripts/build_prompt.py test-plan
py scripts/harness.py test-plan complete '{"docker_compose_ok": true, "test_cases_count": 15}'
```

