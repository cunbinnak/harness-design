---
name: review-bff
description: Self-review BFF code: schema additive, DataLoader, cache keys, owned_paths.
---

# Review BFF Skill

## Khi load
`review-bff-agent` sau `/review-dev` cho BFF boundary.

## Checklist
1. **Coverage**: ≥ 70%.
2. **Schema diff**: chỉ additive (compare vs main).
3. **DataLoader**: kiểm tra mọi resolver có batching khi N+1 risk.
4. **Cache key**: tenant/user prefix cho sensitive data.
5. **Error mapping**: enum codes khớp INTEG spec.
6. **No secrets**.
7. **Owned paths**.
8. **KG**.

## Output
RETURN SCHEMA.
