---
name: rules-web
description: Convention bắt buộc khi code web frontend (React/Vite/Next).
---

# Rules Web Skill

## Khi load
Sub-agent kind=web ở /start-dev, /fix-bugs cho boundary web frontend.

## Quy ước bắt buộc
1. **Codegen**: `npm run codegen` refresh GraphQL types từ BFF schema TRƯỚC khi code.
2. **Component**: implement theo `docs/architecture/ux/ux-{boundary}.md` (Figma hoặc wireframe).
3. **GraphQL ops**: wire mọi actionable element theo INTEG-FE mapping; KHÔNG invent op name.
4. **Loading/error/success**: handler đúng spec INTEG-FE.
5. **Auth flow**: qua bff-auth; KHÔNG embed adapter trực tiếp.
6. **Role gate**: dùng `roles[]` JSONB từ JWT.
7. **a11y**: WCAG 2.1 AA; axe-core scan 0 critical.
8. **NO business logic** trong FE — price/score/eligibility validate ở BFF/backend.
9. **Test**: Vitest + RTL + MSW; coverage ≥ 60%.

## Done
- Build pass, typecheck pass, a11y scan clean.
- Design fidelity match UX spec.
