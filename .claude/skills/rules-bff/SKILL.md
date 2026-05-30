---
name: rules-bff
description: Convention bắt buộc khi code BFF (Apollo Server / GraphQL gateway). Hub — config inline.
---

# Rules BFF Skill

> **Primary skill** cho `kind=bff` (invoke ngay khi spawn dev/fix/review). BFF không có ref-skill riêng — config + pattern inline ở đây.

## Khi load
Sub-agent `kind=bff` ở `/start-dev`, `/fix-bugs`, `/review-dev`.

## Vai trò
BFF = GraphQL gateway: aggregate nhiều backend REST (`api-{backend}.md`) thành 1 graph cho FE. KHÔNG chứa business logic — chỉ orchestrate + shape data.

## Quy ước bắt buộc
1. **Schema GraphQL (SDL)**: additive — deprecate field cũ (`@deprecated`), KHÔNG remove/đổi type breaking. Relay-style `Connection` cho pagination.
2. **Resolver**: implement theo `integrations/INTEG-INT-{bff}-to-{backend}.md` (1 file/backend); gọi backend qua HTTP client, map response → GraphQL type.
3. **DataLoader**: BẮT BUỘC cho mọi field có N+1 risk (vd `order.customer`). Batch + cache per-request.
4. **Auth context**: extract JWT ở context factory → populate `userId / tenantId / roles[]` vào `GraphQLContext`; resolver đọc từ context, KHÔNG tự decode lại.
5. **Error mapping**: HTTP status backend → GraphQL error `extensions.code` (`UNAUTHENTICATED` / `FORBIDDEN` / `BAD_USER_INPUT` / `INTERNAL`).
6. **Cache**: Redis key cho sensitive data PHẢI include `userId`/`tenantId` (tránh leak cross-tenant).
7. **Test**: Vitest unit (resolver + mapper) + integration mock backend; coverage ≥ **70%**.
8. **KG**: append GraphQL ops + DataLoader specs + cache keys vào `knowledge-base/{prefix}-{boundary}.knowledge-graph.yaml`.

## Anti-patterns (review flag)
- ❌ Business logic (tính giá, eligibility) trong resolver → phải ở backend.
- ❌ Resolver gọi backend trong vòng lặp không qua DataLoader (N+1).
- ❌ Cache key thiếu tenant/user prefix cho data nhạy cảm.
- ❌ Remove/rename field trong SDL không qua deprecate cycle.
- ❌ Decode JWT lặp lại trong từng resolver thay vì context.

## Naming
- **Resolver file**: `{type}.resolver.ts`. **Loader**: `{entity}.loader.ts`. **Schema**: `{domain}.graphql`. **Test**: `*.spec.ts`.

## Done
- Build pass, typecheck pass, schema validate.
- DataLoader batching verified (no N+1), test ≥ 70%.
- File chỉ trong `owned_paths`; KG cập nhật.
