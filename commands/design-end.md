---
name: design-end
description: "Đóng stage DESIGN → PLAN sau khi technical design vừa ý. Verify gate (ADR≥3 + INTEG + per-boundary completeness) rồi transition. KHÔNG spawn agent author mới."
argument-hint: "(không cần arg)"
when_state: [DESIGN]
sets_stage: PLAN
gates: [{type: design_gate}]
---

# /design-end

> Advance DESIGN → PLAN. Chỉ chạy khi user đã vừa ý toàn bộ technical design (đã refine qua `/design` self-loop). KHÔNG spawn agent author mới — chỉ verify gate + transition.

## Workflow
1. Xác nhận user OK toàn bộ design (ADR/HLD/API/data-model/UX/events/integrations). Chưa OK → quay lại `/design` refine.
2. (Optional) Run `py scripts/build_prompt.py design-end` để xem checklist gate.
3. `py scripts/harness.py design-end complete '{}'` → DESIGN→PLAN.
4. Override (user đồng ý): `complete '{"force":true,"reason":"<lý do>"}'` → ghi audit decisions.md.

## Gate (design_gate)
- ADR ≥3 + INTEG ≥1 ở `docs/architecture/`.
- **Per-boundary completeness**: MỖI boundary trong BOUNDARY-MAP đủ artifact đúng kind — backend→`hld-{b}.md`+`api-{b}.md`; web/mobile→`hld-{b}.md`+`ux-{b}.md`.
- FAIL → bổ sung artifact boundary còn thiếu (qua `/design`) rồi `/design-end` lại.

## Sau DESIGN
Stage → PLAN. Chạy `/plan` (implementation-plan: WAVE-SEQUENCE + wave-{N} + MATRIX + KG skeleton).
