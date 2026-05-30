---
name: rules-backend
description: Convention bắt buộc khi code backend boundary (Java/Spring hoặc tương đương).
---

# Rules Backend Skill

## Khi load
Sub-agent kind=backend ở /start-dev, /fix-bugs cho boundary backend.

## Quy ước bắt buộc
1. **Layer**: api → application → domain → infrastructure (hoặc DDD tactical theo ADR-002).
2. **Multi-tenancy**: mọi entity, query MUST filter `tenant_id` từ auth context.
3. **API**: contract khớp `docs/architecture/api/api-{boundary}.md`; KHÔNG đổi breaking không qua ADR.
4. **DB**: migration versioned, additive (không sửa migration đã apply).
5. **Event**: publish/consume theo `docs/architecture/events/{boundary}-events.md` envelope chuẩn.
6. **Config**: secrets qua env; không hardcode.
7. **Test**: unit (domain/application) + integration (api + DB testcontainer); coverage ≥ 80%.
8. **KG**: append entity/event/decision vào `knowledge-base/{boundary}.knowledge-graph.yaml` sau khi xong.

## Done
- Build pass, lint pass, test pass coverage ≥ 80%.
- File chỉ thay đổi trong `owned_paths` của boundary.
- KG cập nhật, không có discipline.blockers.
