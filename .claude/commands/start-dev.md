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

## kind_matrix

> Nguồn chuẩn (single source of truth): `scripts/build_prompt.py` — `PRIMARY_SKILLS_PER_KIND` / `REVIEW_SKILLS_PER_KIND` / `REF_SKILLS_PER_KIND`. Bảng này chỉ mirror để tra cứu; sửa code map khi đổi.

| kind | primary (invoke ngay) | review | ref on-demand | scaffold | data layer |
|---|---|---|---|---|---|
| `backend` | `rules-backend` | `review-backend` | `ref-backend-config`, `ref-backend-pattern`, `ref-backend-{redis,kafka,logging}` | `pom.xml` / `build.gradle` | expose REST/GraphQL contract |
| `bff` | `rules-bff` | `review-bff` | — | `package.json` (Apollo) | GraphQL gateway → backend REST |
| `web` | `rules-web` | `review-web` | `ref-frontend-config`, `ref-frontend-pattern` | `package.json` (Vite) | REST trực tiếp BE (default) \| BFF optional |
| `mobile` | `rules-mobile` | `review-mobile` | — | `pubspec.yaml` (Flutter) | REST trực tiếp BE (default) \| BFF optional |

- **Primary** = `rules-{kind}` (hub) → tự ref tới pattern/config khi cần.
- `ref-{kind}-config` + `ref-{kind}-pattern` chỉ tồn tại cho `backend`/`web`; `bff`/`mobile` dùng convention trong `rules-{kind}`.
- `backend` còn có `ref-backend-redis` / `ref-backend-kafka` / `ref-backend-logging` — load on-demand khi boundary dùng tới.
- Skills wave-level (không theo kind): `test-plan`, `test-execute`, `specialist-testing`, `bug-logging`, `infra-local-dev`.

