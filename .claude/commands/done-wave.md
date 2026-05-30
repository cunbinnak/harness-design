---
name: done-wave
description: "Hard close: teardown infra, archive wave artifacts, reset -> BOOTSTRAP."
when_state: ['DONE']
sets_stage: BOOTSTRAP
spawn:
  agent: "done-wave-agent"
  skills: [infra-local-dev]
gates: [{type: flag, field: teardown_ok, expected: true}]
---

# /done-wave

## Mục đích

Teardown infra (docker-compose down --volumes), archive wave artifacts vào handoff/wave-N.md, reset STATE -> BOOTSTRAP cho wave kế tiếp.

## Build prompt + spawn

```bash
py scripts/build_prompt.py done-wave
docker-compose -f docs/architecture/infra/docker-compose.yml down --volumes
py scripts/harness.py done-wave complete '{"teardown_ok": true}'
```

