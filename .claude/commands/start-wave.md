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

## Sau khi complete (harness tự set qua `apply_effects`, KHÔNG sửa tay)

- `STATE.wave` = `{id: "wave-001", number: 1}` ← từ `wave_n`
- `STATE.wave_boundaries` = boundaries có field `wave == N` trong MATRIX (derive trực tiếp từ MATRIX = single source of truth, không tin evidence agent)
- `STATE.wave_features` = union (dedup) `features[]` của các boundary thuộc wave N trong MATRIX
- `STATE.active_boundary` reset về `null` (set lại khi `/start-dev`)
- Arg wave chuẩn hoá: `/start-wave 1` ≡ `/start-wave 01` → `wave-001`; wave phải tồn tại trong MATRIX (gate `wave_in_matrix`) nếu không reject
- File `agents/{dev,fix}-{prefix-boundary}-agent.md` đã tồn tại (qua `materialize.py`)

