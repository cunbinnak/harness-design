---
name: ref-frontend-pattern
description: Cấu trúc thư mục + tổ chức component frontend boundary. Data layer REST-default, BFF optional.
---

# Reference: Frontend Structure

> **Purpose:** Layout chuẩn 1 frontend boundary. Agent FE load để build UI theo cấu trúc nào.
> **Audience:** `dev:web`, `fix:web`, `review:web` — load on-demand từ `rules-web`.
> **Tách bạch:** cấu trúc = file này · config (package.json, build) = `ref-frontend-config` · convention bắt buộc + naming = `rules-web`.
> **Tuning:** theo framework (React/Vue/Next/Svelte) + bundler.

## 1. Layout chuẩn (React/Vite ví dụ)

```
services/{prefix}-{boundary}/
├── src/
│   ├── pages/            # Route page ~ map 1-1 SCR-XXX trong ux-{boundary}.md
│   ├── components/
│   │   ├── ui/           # Atomic (Button, Input, Modal) — no business logic
│   │   ├── layout/       # Header, Sidebar, PageWrapper
│   │   └── domain/       # Domain widget (OrderCard, CustomerList)
│   ├── hooks/            # Data fetching, state, side effect (useXxx)
│   ├── api/              # API client layer  ← xem §2
│   ├── stores/           # Cross-component state (Zustand/Redux/Pinia)
│   ├── router/           # index + guards (auth/role guard)
│   ├── types/            # TS interface — khớp DTO (REST) hoặc generated (GraphQL)
│   ├── utils/            # Pure helper (formatter, validator)
│   └── styles/           # Theme token, global style
├── tests/{unit,integration,e2e}
└── package.json
```

## 2. Data layer — REST default | BFF optional
- **REST (default)**: `api/api-client.ts` (Axios/fetch wrapper + auth interceptor) + `api/{resource}-service.ts` gọi contract `api-{backend}.md`. `types/` viết tay khớp DTO.
- **BFF/GraphQL (optional, khi design có bff)**: `api/` chứa generated hooks/ops từ codegen; `types/` là generated. Cấu hình codegen ở `ref-frontend-config`.

## 3. Trách nhiệm từng folder
| Folder | Trách nhiệm | Phụ thuộc |
|---|---|---|
| `pages/` | Route entry, compose components | components, hooks, api |
| `components/ui/` | Atomic, no business logic | styles |
| `components/domain/` | Domain widget | hooks, types |
| `hooks/` | Data fetch, state, side effect | api, stores |
| `api/` | API call layer (REST client / GraphQL ops) | types |
| `stores/` | Cross-component state | api |
| `router/` | Navigation map + guard | hooks, stores |

## 4. Forbidden patterns
- `components/` gọi API trực tiếp — phải qua `hooks/` → `api/`.
- `pages/` chứa business logic phức tạp — chuyển vào `hooks/`.
- `api/` chứa UI logic — chỉ data call.
- Business logic (price/eligibility) tính ở FE — chỉ render kết quả từ backend/BFF.
- Prop drilling 3+ level — dùng store/context.

## 5. Done
- Cấu trúc khớp `ux-{boundary}.md` (page ~ screen) + data layer đúng design (REST/BFF).
- Build/typecheck pass trước `review-dev`.
