---
name: ref-front-end-pattern
description: Mẫu cấu trúc thư mục cho frontend boundary. Component organization, state management layout.
---

# Reference: Frontend Project Structure

> **Purpose:** Mô tả cấu trúc thư mục chuẩn của 1 frontend boundary. Agent FE load skill này để build UI theo layout chuẩn.
> **Audience:** `dev:frontend`, `fix:frontend`, `review:frontend`.
> **Tuning:** Theo framework (React/Vue/Angular/Svelte) — đồng bộ với ADR-004 UI kit.

## Cấu trúc thư mục chuẩn

```
services/{boundary_id}/
├── src/
│   ├── pages/                  # Route pages — map 1-1 với SCR-XXX trong ux-*.md
│   │   ├── {Resource}List.tsx
│   │   ├── {Resource}Detail.tsx
│   │   └── {Resource}Form.tsx
│   ├── components/             # Reusable UI components
│   │   ├── ui/                 # Base components (Button, Input, Modal...)
│   │   ├── layout/             # Layout (Header, Sidebar, PageWrapper)
│   │   └── domain/             # Domain-specific (OrderCard, CustomerList)
│   ├── hooks/                  # Custom hooks (React) / Composables (Vue)
│   │   └── use{Resource}.ts
│   ├── services/               # API client — gọi BE qua api-*.md contracts
│   │   ├── api-client.ts       # Axios/fetch wrapper + auth interceptor
│   │   └── {resource}-service.ts
│   ├── stores/                 # State management (Redux/Zustand/Pinia/Vuex)
│   │   └── {resource}-store.ts
│   ├── router/                 # Routing + guards
│   │   ├── index.ts
│   │   └── guards.ts           # Auth guard, role guard
│   ├── utils/                  # Helpers (formatter, validator, date)
│   ├── types/                  # TypeScript interfaces (match API DTOs)
│   └── styles/                 # Global styles, theme tokens
├── tests/
│   ├── unit/                   # Component + hook tests
│   ├── integration/            # Page-level (multiple components)
│   └── e2e/                    # Cypress / Playwright
├── public/                     # Static assets
└── package.json
```

## Trách nhiệm từng folder

| Folder | Trách nhiệm | Phụ thuộc |
|--------|-------------|-----------|
| `pages/` | Route entry, compose components | components, hooks, services |
| `components/ui/` | Atomic — Button, Input, Modal (no business logic) | styles |
| `components/layout/` | Page chrome (Header, Sidebar) | hooks (auth) |
| `components/domain/` | Domain widget (OrderCard) | hooks, types |
| `hooks/` | Data fetching, state, side effects | services, stores |
| `services/` | API call layer, fetch wrappers | types |
| `stores/` | Cross-component state | services |
| `router/` | Navigation map, guards | hooks, stores |
| `utils/` | Pure helpers | (none) |
| `types/` | TypeScript interfaces | (none — match API DTOs) |

## Naming conventions

- **Component file:** `PascalCase.tsx` (vd `OrderList.tsx`, `Button.tsx`)
- **Hook file:** `camelCase.ts` starting with `use` (vd `useOrders.ts`)
- **Service file:** `kebab-case-service.ts` (vd `order-service.ts`)
- **Test file:** `{Component}.test.tsx` hoặc `*.spec.ts`
- **Style:** CSS Modules `Component.module.css` hoặc styled-components

## Forbidden patterns

- `pages/` chứa business logic phức tạp — chuyển vào hook
- `components/` gọi API trực tiếp — phải qua `hooks/` → `services/`
- `services/` chứa UI logic — chỉ API call
- Inline style chaos — dùng design tokens / CSS Modules
- Prop drilling 3+ levels — dùng store hoặc context

## Khi nào tuning

- Framework khác (Vue): `pages/` → `views/`, `hooks/` → `composables/`
- Architecture khác (feature-sliced design): tổ chức theo feature thay vì type
- Monorepo: shared `packages/` cho UI kit
- SSR (Next.js/Nuxt): bổ sung `app/`, `api/` routes

Đồng bộ với `docs/architecture/adr/ADR-004-ui-kit.md`.
