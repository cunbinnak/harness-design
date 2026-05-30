---
name: specialist-testing
description: Thiết kế kiểm thử chuyên sâu (contract, regression, isolation, perf, security) bổ sung vào registry.
---

# Specialist Testing Skill

## Khi load
Bổ trợ `test-plan-agent` / `test-execute-agent` khi wave cần loại test khó vượt mức CRUD cơ bản.

## Hoạt động
1. Bổ sung TC chuyên sâu vào `tracking/wave-{N}/test-case-registry.md` — cùng format heading `## TC-{N}-{slug}` + frontmatter (`type`, `boundary`, `feature`, `ac`, `priority`):
   - **contract**: verify API/event contract khớp `api-{boundary}.md` / `{boundary}-events.md` (consumer ↔ provider).
   - **regression**: TC-R* chốt lại bug đã fix (link `BUG-NNN`).
   - **isolation**: unit/integration biên domain (mock infra).
   - **perf / security**: chỉ khi NFR trong `PROJECT.md` yêu cầu.
2. Mỗi TC trace tối thiểu 1 `FEAT-N:AC-M`. Kết quả chạy ghi ở `tracking/wave-{N}/test-report.md` (do test-execute).

## Done
- TC chuyên sâu đã vào registry, có AC trace, priority đúng (P0 blocker / P1 must / P2 nice).
