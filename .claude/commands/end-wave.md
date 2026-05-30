---
name: end-wave
description: "UAT đã signed off. Soft close wave -> DONE."
when_state: ['MANUAL_TEST']
sets_stage: DONE
spawn:
  agent: "end-wave-agent"
  skills: []
gates: [{type: flag, field: uat_signed, expected: true}, {type: no_open_bugs}]
---

# /end-wave

## Mục đích

UAT đã signed off, không còn open bug. Soft close: wave kết thúc logic, infra vẫn UP cho post-mortem.

## Build prompt + spawn

```bash
py scripts/build_prompt.py end-wave
py scripts/harness.py end-wave complete '{"uat_signed": true}'
# gates also check no_open_bugs trong tracking/wave-N/bugs.md
```

