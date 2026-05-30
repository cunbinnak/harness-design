---
name: rules-web
description: Convention bắt buộc khi code web frontend (React/Vite/Next…). Hub — ref pattern + config.
---

# Rules Web Skill

> **Primary skill** cho `kind=web` (invoke ngay khi spawn dev/fix/review).
> On-demand refs:
> - Cấu trúc thư mục + tổ chức component → `ref-frontend-pattern`.
> - File cấu hình (package.json, env, build, Dockerfile FE) → `ref-frontend-config`.

## Khi load
Sub-agent `kind=web` ở `/start-dev`, `/fix-bugs`, `/review-dev`.

## Data layer — theo thiết kế dự án (xem integrations design)
- **Default — REST trực tiếp backend**: client (Axios/fetch) gọi contract `docs/architecture/api/api-{backend}.md`; interceptor gắn auth + map error. Types khớp DTO trong API spec.
- **Optional — qua BFF/GraphQL**: CHỈ khi design có boundary `bff`. `npm run codegen` refresh types từ BFF schema TRƯỚC khi code; wire ops theo `integrations/INTEG-INT-{web}-to-{bff}.md`; KHÔNG invent op name.

> Boundary serve REST hay BFF ghi trong `hld-{boundary}.md` / integration design — không tự ý đổi.

## Quy ước bắt buộc
1. **Component**: implement theo `docs/architecture/ux/ux-{boundary}.md` (Figma/wireframe), đúng design fidelity.
2. **Wire actions**: mọi element actionable map đúng endpoint/op trong integration design; handle **loading / error / success** đủ trạng thái.
3. **Auth**: theo auth flow đã chốt (token/refresh/route guard); KHÔNG embed credential.
4. **Role gate**: dùng `roles[]` claim từ JWT.
5. **a11y**: WCAG 2.1 AA; axe-core scan 0 critical.
6. **NO business logic** trong FE — price/score/eligibility validate ở backend (hoặc BFF).
7. **Test**: Vitest + RTL + mock layer (MSW cho REST / Apollo MockedProvider cho GraphQL); coverage ≥ **60%**.

## Naming & structure
- **Component file**: `PascalCase.tsx`. **Hook**: `useXxx.ts` (camelCase). **Service/client**: `kebab-case.ts`. **Test**: `*.test.tsx` / `*.spec.ts`.
- **Folder layout**: `pages` / `components` / `hooks` / `api(services)` / `stores` / `router` — xem `ref-frontend-pattern`.

## Done
- Build pass, typecheck pass, a11y scan clean, test ≥ 60%.
- Design fidelity match UX spec; chỉ sửa file trong `owned_paths`.
