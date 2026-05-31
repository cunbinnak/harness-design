---
name: review-bff
description: Self-review BFF — schema additive, DataLoader (no N+1), cache keys, error mapping, security (auth context/query cost/DoS), owned_paths.
---

# Review BFF Skill

> Checklist source-of-truth cho `review-bff-agent` ở `/review-dev`. Fail → spawn fix → re-review → loop tới pass.

## Lệnh chạy
```bash
npm run -s test -- --coverage     # Vitest + coverage
npm run -s typecheck              # tsc --noEmit
npm run -s schema:check           # validate SDL + so diff vs main (additive)
git diff --name-only main...HEAD
```

## Checklist (PASS/FAIL/NA)
1. **Build + typecheck** xanh; test ≥ **70%**.
2. **Schema additive**: diff SDL vs `main` chỉ thêm field/type hoặc `@deprecated`; KHÔNG remove/rename breaking.
3. **DataLoader**: mọi resolver có quan hệ → field dùng loader batch; KHÔNG gọi backend trong vòng lặp (kiểm N+1 qua log/trace test).
4. **Cache key**: data nhạy cảm có prefix `userId`/`tenantId`. FAIL nếu cache global cho per-user data.
5. **Error mapping**: HTTP backend → `extensions.code` enum đúng (`UNAUTHENTICATED`/`FORBIDDEN`/`BAD_USER_INPUT`/`INTERNAL`), khớp `integrations/INTEG-INT-{bff}-to-*.md`.
6. **No business logic**: resolver chỉ orchestrate + shape; tính toán nghiệp vụ phải ở backend.
7. **Security (GraphQL gateway)**:
   - **Auth context**: verify token ở gateway; forward identity an toàn xuống backend — client KHÔNG override `userId`/`tenantId`/role.
   - **Query cost / DoS**: có depth + complexity limit + pagination; introspection tắt ở prod; schema không expose field nhạy cảm.
   - **Injection passthrough**: arg truyền xuống backend được validate; không nối raw input vào downstream query/URL.
   - **Error**: không leak stack/internal (đã ở mục 5); rate limit per user/tenant.
8. **No secrets**; **Owned paths** ⊆ boundary; **KG** appended (ops + loaders + cache keys).

## Anti-patterns cần flag
- Resolver `Promise.all` map gọi REST từng item thay vì DataLoader.
- Trả nguyên error backend ra client (leak stack/internal).
- Cache response chứa field theo role mà key không gồm role/user.
- Tin `userId`/`tenantId` từ GraphQL args thay vì context; introspection bật ở prod; không depth/complexity limit.

## Output
RETURN SCHEMA: `review_result`, `coverage_pct`, `checklist_summary`, `needs_review[]`, `fix_loops_triggered`.
