---
name: start-wave
description: "Mở wave N. Materialize per-boundary agents + KG + folder structure từ MATRIX."
when_state: ['INTAKE']
sets_stage: WAVE_OPEN
spawn:
  agent: "start-wave-agent"
  skills: []
gates: [{type: flag, field: approved, expected: true}, {type: int_min, field: wave_n, min: 1}, {type: file_exists, path: harness/SERVICE-BOUNDARY-MATRIX.json}]
---

# /start-wave

## Mục đích

Mở wave N. Đọc MATRIX, sinh `agents/dev-{prefix-boundary}-agent.md`, `agents/fix-{prefix-boundary}-agent.md`, `knowledge-base/{prefix-boundary}.knowledge-graph.yaml` cho mỗi boundary trong wave.

## Build prompt + spawn

```bash
py scripts/build_prompt.py start-wave --wave 1
py scripts/materialize.py --wave 1  # script đọc MATRIX + materialize
py scripts/harness.py start-wave complete '{"approved": true, "wave_n": 1}'
```

## Sau khi complete

- STATE.wave = {id: "wave-001", number: 1}
- STATE.wave_boundaries = [list từ wave-001.md]
- File agents/{dev,fix}-{prefix-boundary}-agent.md đã tồn tại

