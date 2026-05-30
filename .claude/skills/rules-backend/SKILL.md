---
name: rules-backend
description: Convention bắt buộc khi code backend boundary (Java/Spring hoặc tương đương). Hub — ref pattern + config.
---

# Rules Backend Skill

> **Primary skill** cho `kind=backend` (invoke ngay khi spawn dev/fix/review).
> On-demand refs:
> - Kiến trúc + cấu trúc thư mục → `ref-backend-pattern` (Layered/DDD theo **ADR backend-architecture**).
> - File cấu hình (application.yml, security, kafka, secrets…) → `ref-backend-config`.

## Khi load
Sub-agent `kind=backend` ở `/start-dev`, `/fix-bugs`, `/review-dev`.

## Quy ước bắt buộc
1. **Kiến trúc**: theo loại đã chốt trong **ADR backend-architecture** (Layered hoặc DDD tactical) — cấu trúc thư mục + layer responsibilities xem `ref-backend-pattern`.
2. **Multi-tenancy**: mọi entity, query MUST filter `tenant_id` từ auth context (nếu project multi-tenant).
3. **API**: contract khớp `docs/architecture/api/api-{boundary}.md`; KHÔNG đổi breaking không qua ADR.
4. **DB**: migration versioned, additive (không sửa migration đã apply); schema khớp `data-model-{boundary}.md`.
5. **Event**: publish/consume theo `docs/architecture/events/{boundary}-events.md` envelope chuẩn.
6. **Cross-boundary**: KHÔNG import code từ `services/{prefix}-{other}/`; gọi qua HTTP/event theo `docs/architecture/integrations/INTEG-*.md`.
7. **Config**: secrets qua env; không hardcode (chi tiết `ref-backend-config`).
8. **Test**: unit (domain/application) + integration (api + DB testcontainer); coverage ≥ **80%**.
9. **KG**: append entity/event/decision vào `knowledge-base/{prefix}-{boundary}.knowledge-graph.yaml` sau khi xong.

## Naming & package
- **File**: theo stack — `PascalCase.java` (Java) / `kebab-case.ts` (Node) / `snake_case.py` (Python).
- **Class**: `PascalCase` (`OrderService`). **Method**: `camelCase`/`snake_case` theo stack. **Constant**: `UPPER_SNAKE_CASE`.
- **Package/module**: theo layer của mô hình kiến trúc (`api`/`application`/`domain`/`infrastructure`) — xem `ref-backend-pattern`.
- **Test**: `{Unit}Test` / `test_{module}` theo runner.

## Done
- Build pass, lint pass, test pass coverage ≥ 80%.
- File chỉ thay đổi trong `owned_paths` của boundary.
- Cấu trúc khớp `ref-backend-pattern` (mô hình theo ADR) + `hld-{boundary}.md`.
- KG cập nhật, không có `discipline.blockers`.
