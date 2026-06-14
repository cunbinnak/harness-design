---
name: start-dev
description: "Vào DEV cho 1 boundary. Spawn dev sub-agent (kind tự detect từ MATRIX). Gọi lặp được cho từng boundary trong wave. Lần đầu tự tạo services/{prefix-boundary}/ scaffold."
when_state: ['WAVE_OPEN', 'DEV']
sets_stage: DEV
spawn:
  agent: "dev-{prefix-boundary}-agent (materialized)"
  skills: rules-{kind} per matrix entry
gates: [{type: in_state_list, field: boundary, state_field: wave_boundaries}]
---

# /start-dev

## Mục đích

Bắt đầu code 1 boundary trong wave. Build self-contained prompt cho dev sub-agent (kind-aware: backend/bff/web/mobile). Lần đầu cho boundary: agent scaffold service folder + push lên repo riêng (polyrepo).

## Flow (thứ tự QUAN TRỌNG)

> **`complete` chạy TRƯỚC khi spawn** — để vào DEV + set `active_boundary` NGAY. Nhờ đó **Stop hook gate build/test trong lúc** dev scaffold/code, và **reminder boundary lúc spawn trỏ đúng** `active_boundary` (Stop hook chỉ chạy khi stage ∈ {DEV, REVIEW_DEV, TEST_EXECUTE} VÀ `active_boundary` có code — xem `dispatcher.handle_stop`). Nếu complete SAU spawn: dev code khi stage còn WAVE_OPEN + `active_boundary`=None → Stop hook **bỏ qua** (không gate), reminder rỗng.

```bash
# 1. Vào DEV + set active_boundary (gate: boundary ∈ wave_boundaries)
py scripts/harness.py start-dev complete '{"boundary": "order-management"}'
# 2. Build self-contained prompt (STATE giờ = DEV, active_boundary đã set)
py scripts/build_prompt.py start-dev --boundary order-management
# 3. Spawn dev sub-agent với prompt (Agent tool) — agent scaffold + code TRONG stage DEV
```

## Agent behavior

- Đọc DOCS IN SCOPE inline trong prompt
- Lần đầu: tạo `services/{project.service_prefix}-{boundary}/` skeleton (pom.xml / package.json / pubspec.yaml theo kind)
- Lần đầu: emit guardrail repo con — `CLAUDE.md` + `.claude/settings.json` + `.gitignore` từ `docs/architecture/infra/TEMPLATE.service-repo-*` (create-if-missing, substitute placeholder từ MATRIX + STATE.project)
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

