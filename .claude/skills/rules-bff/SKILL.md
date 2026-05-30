---
name: rules-bff
description: Convention bắt buộc khi code BFF (Apollo Server / GraphQL gateway).
---

# Rules BFF Skill

## Khi load
Sub-agent kind=bff ở /start-dev, /fix-bugs cho boundary BFF.

## Quy ước bắt buộc
1. **Schema GraphQL**: SDL additive (deprecate, không remove); Relay-style Connection cho pagination.
2. **Resolver**: implement theo `docs/architecture/integrations/INTEG-INT-{bff}-to-*.md` (1 file per backend).
3. **DataLoader**: BẮT BUỘC cho mọi field có potential N+1.
4. **Auth context**: extract JWT, populate `userId/tenantId/roles[]` vào GraphQLContext.
5. **Error mapping**: backend HTTP status → GraphQL error code (UNAUTHORIZED/FORBIDDEN/VALIDATION/INTERNAL).
6. **Cache**: Redis key phải include `userId` hoặc `tenantId` cho sensitive data.
7. **Test**: Vitest unit + integration mock backend; coverage ≥ 70%.
8. **KG**: append GraphQL ops + DataLoader specs + cache keys.

## Done
- Build pass, typecheck pass, schema validate.
- DataLoader batching verified (no N+1).
- File chỉ trong `owned_paths`.
