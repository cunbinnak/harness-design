---
name: review-backend
description: Self-review backend code: coverage, convention, KG, owned_paths.
---

# Review Backend Skill

## Khi load
`review-backend-agent` sau `/review-dev` cho backend boundary.

## Checklist
1. **Coverage**: ≥ 80% (JaCoCo).
2. **Convention**: code khớp `rules-backend` (layer, multi-tenant, API contract).
3. **Migration**: additive only, không sửa applied migration.
4. **No secrets**: grep audit `grep -r 'password\|api[_-]key\|secret' src/main/` clean.
5. **Owned paths**: `git diff` chỉ chứa file trong owned_paths.
6. **KG**: entity/event/decision đã append.
7. **Cross-boundary**: không import direct từ services/other/.

## Output
RETURN SCHEMA với `test: pass`, `coverage_pct`, `needs_review[]` nếu phát hiện.
