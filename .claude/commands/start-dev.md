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

> Nguồn chuẩn (single source): `scripts/build_prompt.py` — `PRIMARY_SKILLS_PER_KIND` / `REVIEW_SKILLS_PER_KIND` / `SCAFFOLD_REF_SKILLS_PER_KIND`. **Situational ref = per-boundary, lấy từ MATRIX field `ref_skills`** (không có map tĩnh ở kernel). Bảng dưới chỉ mirror.

| kind | primary (invoke ngay) | review | scaffold ref (bắt buộc khi scaffold) | situational ref | build file |
|---|---|---|---|---|---|
| `backend` | `rules-backend` | `review-backend` | `ref-backend-pattern`, `ref-backend-config`, `ref-backend-logging` | từ MATRIX `ref_skills` | `pom.xml` / `build.gradle` |
| `bff` | `rules-bff` | `review-bff` | — (convention trong `rules-bff`) | từ MATRIX `ref_skills` | `package.json` (Apollo) |
| `web` | `rules-web` | `review-web` | `ref-frontend-pattern`, `ref-frontend-config` | từ MATRIX `ref_skills` | `package.json` (Vite) |
| `mobile` | `rules-mobile` | `review-mobile` | — (convention trong `rules-mobile`) | từ MATRIX `ref_skills` | `pubspec.yaml` (Flutter) |

- **Primary** = `rules-{kind}` (hub) → invoke ngay.
- **Scaffold ref** = structure/config/logging, **invoke BẮT BUỘC khi scaffold** (folder layout theo kiến trúc HLD §4). Universal theo kind.
- **Situational ref** (cache/event/extra…) = **KHÔNG hardcode ở kernel**. Intake (step 3/4) gắn per-boundary vào MATRIX `ref_skills` → materialize vào `dev-{boundary}-agent.md` + build_prompt truyền qua. **Thêm ref mới sau này = sửa MATRIX, không đụng kernel.**
- Skills wave-level (không theo kind): `test-plan`, `test-execute`, `specialist-testing`, `bug-logging`, `infra-local-dev`.

