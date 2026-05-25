# FEAT-XXX: {title}

> **Purpose:** Mô tả một feature — user value, AC testable, business rules.
> **Owner:** `intake:requirement-analyst` (draft) → `intake:business-analyst` (refine AC + BR).
> **Audience:** dev (biết phải build gì), test-plan (biết phải test gì), reviewer (biết phải đối chiếu).
> **Out of scope:** Implementation (→ [`../hld/hld-{boundary}.md`](../hld/)), API (→ [`../api/api-{boundary}.md`](../api/)), UI wireframe (→ [`../ux/ux-{fe}.md`](../ux/)).

---

**Ưu tiên:** Must | Should | Could
**Boundary dự kiến:** (gợi ý — solution-architect chốt, materialize trong matrix)

## Mục tiêu

(1-2 câu — feature giải quyết vấn đề gì cho user, khớp [PROJECT.md](../PROJECT.md))

## Phạm vi feature

- **In scope:**
- **Out of scope:**

## Acceptance criteria

Mỗi AC phải **testable** (Given/When/Then hoặc condition đo được). test-plan-agent dùng AC này để sinh test case.

- [ ] **AC-1:** (Given ... When ... Then ...)
- [ ] **AC-2:**
- [ ] **AC-3:**

## Business rules

| ID | Rule | Apply at |
|----|------|----------|
| BR-1 | (rule cụ thể) | (endpoint / domain service / UI form) |
| BR-2 | | |

## Phụ thuộc

- **Depends on:** (FEAT-XXX hoặc —)
- **Blocks:** (FEAT-YYY hoặc —)

## Liên kết

- Wave: `../../plans/waves/{wave-id}/wave.md` §2 (assignment)
- KG backlog: `../../../knowledge-base/{boundary}.knowledge-graph.yaml` (`implementation.backlog`)
