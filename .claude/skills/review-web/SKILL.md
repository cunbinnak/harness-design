---
name: review-web
description: Self-review web frontend: a11y, no biz logic, codegen up-to-date.
---

# Review Web Skill

## Khi load
`review-web-agent` sau `/review-dev` cho web boundary.

## Checklist
1. **Coverage**: ≥ 60%.
2. **a11y**: axe-core 0 critical.
3. **Codegen up-to-date**: `npm run codegen` no diff.
4. **No business logic** trong FE.
5. **INTEG-FE mapping**: op names match generated.
6. **Owned paths**.

## Output
RETURN SCHEMA.
