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

## Bổ sung rule bắt buộc

### TypeScript & code quality
8. **TypeScript strict**: bật `strict: true`; KHÔNG dùng `any` trừ khi có comment giải thích rõ lý do.
9. **Không magic string / magic number**: route path, storage key, query key, role, status code, error code phải đưa vào constants.
10. **Không `// @ts-ignore`**. Nếu bắt buộc, dùng `// @ts-expect-error` kèm lý do.
11. **Không dead code / console debug** trong production code. Chỉ dùng logger/monitoring wrapper nếu project có chuẩn.
12. **Không duplicate logic format**: date, currency, phone, status label, badge mapping phải gom về helper/shared util.

### Component boundary
13. **Component nhỏ, rõ trách nhiệm**:
    - UI component chỉ render + emit event.
    - Container/page xử lý fetch data, state orchestration, navigation.
    - Không nhồi API call trực tiếp vào component thuần UI.
14. **Props rõ kiểu dữ liệu**: không truyền object quá lớn nếu component chỉ cần vài field; ưu tiên `Pick<>` hoặc type riêng.
15. **Không mutate props/state**. Luôn update immutable.
16. **Không lạm dụng global state**: chỉ dùng global khi cần share cross-page/cross-feature; còn lại giữ local hoặc server-state cache.

### Data fetching & API contract
17. **API client tách riêng theo boundary**: không gọi `fetch/axios` rải rác trong UI component.
18. **Request/Response type bám API spec** trong `docs/architecture/api/api-{backend}.md` hoặc generated types.
19. **Server state dùng chuẩn thống nhất**: React Query / SWR / Apollo theo config dự án; không tự chế cache thủ công.
20. **Query key khai báo tập trung** để tránh lệch cache/invalidation.
21. **Mutation handle đủ flow**:
    - optimistic update nếu design cho phép;
    - invalidate/refetch đúng query liên quan;
    - rollback khi lỗi nếu có optimistic update.
22. **Pagination/filter/sort/search phản ánh đúng contract backend**; không tự filter client-side nếu backend đã định nghĩa server-side.
23. **Không invent field/status/error code** ngoài API spec. Thiếu contract → tạo blocker/CR thay vì tự đoán.

### Form & validation
24. **Form dùng schema validation thống nhất**: Zod/Yup/Valibot theo config dự án.
25. **FE validation chỉ để UX**, backend/BFF vẫn là source of truth.
26. **Error field mapping đúng contract**: lỗi field-level, form-level, global-level tách rõ.
27. **Submit form chống double submit** bằng disabled/loading/idempotency key nếu contract yêu cầu.
28. **Dirty state phải xử lý** với form chỉnh sửa dữ liệu quan trọng: cảnh báo khi rời trang nếu chưa lưu.

### UX state
29. Mỗi màn hình có data fetching phải xử lý đủ: **loading · empty · error · success · partial/disabled** (nếu permission hoặc dependency chưa đủ).
30. **Không để button/action "im lặng"**: click phải có phản hồi rõ — spinner, toast, inline message hoặc navigation.
31. **Toast không thay thế field error**. Lỗi nhập liệu phải hiển thị gần field liên quan.
32. **Confirm destructive action**: delete/cancel/revoke/reset phải có confirm dialog nếu UX spec yêu cầu hoặc có nguy cơ mất dữ liệu.

### Routing & navigation
33. **Route khai báo tập trung**; không hardcode path trong nhiều component.
34. **Protected route bắt buộc dùng route guard** theo auth flow.
35. **Deep link phải hoạt động**: reload trực tiếp URL vẫn render đúng nếu user có quyền.
36. **Navigation sau mutation** theo UX spec; không tự redirect nếu chưa được thiết kế.

### Auth, permission & security
37. **Role gate ở FE chỉ phục vụ UX**, KHÔNG phải security boundary. Backend/BFF vẫn enforce quyền.
38. **Không lưu token tùy tiện**. Cách lưu token/refresh token theo auth design đã chốt.
39. **Không log token, credential, PII, response nhạy cảm**.
40. **Không `dangerouslySetInnerHTML`** trừ khi có sanitize rõ ràng và được review.
41. **Không expose secret qua env FE**. Biến `VITE_*` / `NEXT_PUBLIC_*` được xem là public.
42. **Upload file validate client-side** theo UX/contract: size, type, extension, preview, progress, error.

### Styling & responsive
43. **Responsive theo breakpoint chuẩn của project**; không hardcode media query rải rác nếu design system đã có token.
44. **Dùng design token/theme** cho spacing, color, typography; không dùng màu/spacing tùy tiện.
45. **Không inline style phức tạp** trừ case rất nhỏ hoặc dynamic style có lý do.
46. **Không phá layout khi text dài**: handle overflow, ellipsis, wrap, empty label.
47. **Dark mode/theme**: nếu project hỗ trợ thì component mới không được hardcode màu làm vỡ theme.

### Accessibility
48. Element tương tác phải dùng semantic HTML trước: `button`, `a`, `label`, `input`.
49. Icon button phải có accessible name: `aria-label` hoặc text ẩn.
50. Modal/dropdown/menu phải xử lý keyboard navigation, focus trap, Escape close nếu component tự build.
51. Form input phải có label hoặc accessible label.
52. Không dùng màu là tín hiệu duy nhất để truyền trạng thái lỗi/thành công.

### Performance
53. **Không fetch lặp vô hạn** do dependency array sai.
54. **Debounce search/filter** nếu gọi API theo input.
55. **Lazy load route/page lớn** theo chuẩn project.
56. **Không memo hóa bừa bãi**. Chỉ dùng `useMemo/useCallback/memo` khi có lý do render/performance rõ.
57. **Image tối ưu**: lazy load, size rõ ràng, alt text phù hợp; Next dùng `next/image` nếu project dùng Next.
58. **Bundle size để ý**: không thêm lib nặng nếu native/simple util đã đủ.

### Internationalization, date/time & format
59. **Không hardcode text nếu project có i18n**. Text UI phải đi qua translation resource.
60. **Date/time xử lý timezone rõ ràng** theo product spec; không tự format bằng string thủ công.
61. **Currency/number/percent dùng formatter chung** để đồng nhất locale.
62. **Status label/badge mapping lấy từ constant/mapper**, không viết rải rác nhiều nơi.

### Testing
63. Test component assert theo hành vi người dùng, ưu tiên query bằng role/label/text thay vì className/testId.
64. API test mock ở network boundary: REST dùng MSW; GraphQL dùng Apollo MockedProvider / MSW GraphQL theo config.
65. Test tối thiểu cho mỗi màn/action chính: render success · loading · error · submit success · submit validation error · permission denied/hidden action (nếu có role gate).
66. Không snapshot test lớn trừ component rất ổn định; ưu tiên assertion rõ ràng.
67. Bug fix phải có regression test nếu lỗi có thể tái hiện tự động.

### Review checklist
68. Trước khi Done, reviewer/dev kiểm tra: UI đúng UX spec · action map đúng API/integration · không hardcode secret/config · không business logic quan trọng ở FE · đủ loading/error/empty/success · route guard/role gate đúng · typecheck/build/test pass · không sửa ngoài `owned_paths`.

## Naming & structure
- **Component file**: `PascalCase.tsx`. **Hook**: `useXxx.ts` (camelCase). **Service/client**: `kebab-case.ts`. **Test**: `*.test.tsx` / `*.spec.ts`.
- **Folder layout**: `pages` / `components` / `hooks` / `api(services)` / `stores` / `router` — xem `ref-frontend-pattern`.

## Done
- `npm run typecheck` / build / `npm run lint` pass; test pass, coverage ≥ **60%** (ngưỡng web); a11y scan clean.
- Không còn `console.log` / `debugger` / dead code; không có `any` / `@ts-ignore` / hardcoded route/status/role không kiểm soát.
- Mọi màn data-fetching đủ **loading / empty / error / success**; action quan trọng có confirm hoặc feedback rõ ràng.
- API types khớp contract; không invent field/op/error code.
- Role gate đúng UX nhưng KHÔNG thay backend authorization; không hardcode secret/config; không business logic quan trọng ở FE.
- Responsive + a11y đạt yêu cầu tối thiểu.
- Design fidelity match UX spec; chỉ sửa file trong `owned_paths`.
