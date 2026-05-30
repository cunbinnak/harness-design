---
name: review-backend
description: Self-review backend code — coverage, convention, migration, secrets, KG, owned_paths.
---

# Review Backend Skill

> Checklist là **source of truth** cho `review-backend-agent` ở `/review-dev` (state REVIEW_DEV). Fail → spawn `fix-{prefix}-{boundary}-agent` → re-review → loop tới pass.

## Lệnh chạy (Java/Spring ví dụ — tune theo stack)
```bash
mvn -q test                       # unit + integration
mvn -q jacoco:report              # coverage
mvn -q checkstyle:check spotbugs:check   # lint/static
git diff --name-only main...HEAD  # scope check
```

## Checklist (mỗi item PASS/FAIL/NA)
1. **Build + test**: `mvn test` xanh; integration (testcontainer DB) chạy thật, không skip.
2. **Coverage** ≥ **80%** (JaCoCo line/branch). FAIL nếu thấp hơn hoặc report không tồn tại.
3. **Convention** khớp `rules-backend`: layer đúng (`api/application/domain/infrastructure`), multi-tenant filter `tenant_id`, API khớp `api-{boundary}.md`.
4. **Migration**: additive-only; KHÔNG sửa migration đã apply (so `git diff` thư mục migration).
5. **No secrets**: `grep -rnE 'password|api[_-]?key|secret|token' src/main/` → 0 hardcode (chỉ env binding).
6. **Owned paths**: `git diff --name-only` ⊆ `owned_paths` của boundary. FAIL nếu chạm `services/{prefix}-{other}/`.
7. **Cross-boundary**: KHÔNG `import` trực tiếp package boundary khác — chỉ gọi qua HTTP/event theo `integrations/INTEG-*.md`.
8. **KG**: entity/event/decision đã append vào `knowledge-base/{prefix}-{boundary}.knowledge-graph.yaml`.

## Anti-patterns cần flag
- ❌ Business rule trong `api/` controller (chỉ parse + delegate).
- ❌ SQL/ORM trong `domain/` (chỉ trong `infrastructure/`).
- ❌ Test chỉ assert "không throw" mà không verify giá trị.
- ❌ `@Transactional` ở sai layer (nên ở `application/`).

## Output
RETURN SCHEMA với `review_result: pass|fail`, `coverage_pct`, `checklist_summary{total,passed,failed,skipped_na}`, `needs_review[]` (file + concern), `fix_loops_triggered`.
