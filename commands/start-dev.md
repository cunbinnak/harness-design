---
name: start-dev
description: "Vào DEV mode cho 1 boundary. Spawn dev sub-agent (kind tự detect từ MATRIX). Lần đầu tự tạo services/{prefix-boundary}/ scaffold."
when_state: ['WAVE_OPEN']
sets_stage: DEV
spawn:
  agent: "dev-{prefix-boundary}-agent (materialized)"
  skills: rules-{kind} per matrix entry
gates: [{type: in_state_list, field: boundary, state_field: wave_boundaries}]
---

# /start-dev

## Mục đích

Bắt đầu code 1 boundary trong wave. Build self-contained prompt cho dev sub-agent (kind-aware: backend/bff/web/mobile). Lần đầu cho boundary: agent scaffold service folder + push lên repo riêng (polyrepo).

## Build prompt + spawn

```bash
py scripts/build_prompt.py start-dev --boundary order-management
# stdout self-contained prompt: STATE bundle + skill rules-backend + HLD + API + data-model + KG + FEAT
# (spawn via Agent tool with output)
py scripts/harness.py start-dev complete '{"boundary": "order-management"}'
```

## Agent behavior

- Đọc DOCS IN SCOPE inline trong prompt
- Lần đầu: tạo `services/{project.service_prefix}-{boundary}/` skeleton (pom.xml / package.json / pubspec.yaml theo kind)
- Implement AC trong FEAT
- Append KG, return RETURN SCHEMA

