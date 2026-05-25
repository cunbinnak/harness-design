---
description: "Harness command: end-wave"
argument-hint: ""
---

# /end-wave

Ship wave → **MANUAL_TEST** stage. **KHÔNG** teardown, **KHÔNG** reset.

**Agent:** [end-wave-agent.md](../agents/end-wave-agent.md) · **Role:** `end-wave`

## Hành vi

| | Trước | Sau |
|---|------|-----|
| Stage | DONE | **MANUAL_TEST** |
| Infra | Up | **Vẫn Up** (cho UAT) |
| `wave.id` | Active | **Vẫn active** |
| `allowed_next` | — | `["fix-bugs", "done-wave"]` |

## Output

1. Finalize `handoff/{wave-id}.md` — thêm section "Wave Shipped" + UAT guide
2. Tạo `tracking/waves/{wave-id}/manual-test-log.md` (skeleton cho stakeholder điền)
3. KG: `wave-{wave-id}-shipped` decision

## Chạy

```bash
py scripts/build_command_prompt.py end-wave
py scripts/harness.py end-wave complete '{"end_wave_ok": true}'
```

Gate: `release complete`, `end_wave_ok: true`, `handoff/wave-*.md` tồn tại.

## Sau end-wave: 2 đường

| Tình huống | Lệnh |
|-----------|------|
| UAT pass — không bug | `/done-wave` |
| UAT fail — có bug manual | `/fix-bugs --boundary X` → `/retest` (smart route về MANUAL_TEST) |