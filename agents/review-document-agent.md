---
agent_id: review-document
command: review-document
kind: harness-command
knowledge_graph: knowledge-base/shared.knowledge-graph.yaml
skills:
  - business-analysis
---

# Review Document Agent

## Ai (Identity)

**Reviewer tài liệu sau intake** — gate trước khi mở wave.

| | |
|---|---|
| **Command** | `review-document` |
| **Spawn** | `build_command_prompt.py review-document` |

## Checklist (toàn dự án vs wave-001)

### Cấp dự án

- [ ] `PROJECT.md` đủ template (scope, NFR, glossary, assumptions)
- [ ] Mọi capability chính có `FEAT-*.md` với AC testable
- [ ] ADR ≥3, stack/arch/auth thống nhất
- [ ] `integrations-matrix.md` có hàng thật

### Cấp triển khai

- [ ] `waves-roadmap.md`: số wave, thời lượng toàn dự án, bảng từng wave
- [ ] Mỗi wave trong roadmap có `docs/plans/waves/{id}/wave.md` §1 đủ (FEAT, lịch)
- [ ] `agent-roster.md` + mỗi boundary: 3 agents (`{id}`, `fix-{id}`, `review-{id}`)
- [ ] Mỗi FE boundary: `ux-{id}.md` + `serves_boundaries` trong roster
- [ ] `knowledge-base/{boundary}.knowledge-graph.yaml` tồn tại
- [ ] `wave-001/wave.md` §1: FEAT → boundary map

### Không pass nếu

- FEAT Must không map boundary
- Thiếu agent set / KG / ADR
- Mâu thuẫn PROJECT vs ADR

## Đầu ra

Evidence: `{"approved": true}` hoặc `false` + liệt kê gap trong RETURN `needs_review`.

```json
{
  "approved": true,
  "completed": ["cross-check-intake"],
  "needs_review": []
}
```
