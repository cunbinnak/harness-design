---
name: design-end
description: "Đóng stage DESIGN → PLAN sau khi technical design vừa ý. Verify gate (ADR≥3 + INTEG + per-boundary completeness) rồi transition. KHÔNG spawn agent author mới."
argument-hint: "(không cần arg)"
when_state: [DESIGN]
sets_stage: PLAN
gates: [{type: design_gate}, {type: todo_resolved}]
---

# /design-end

> Advance DESIGN → PLAN. Chỉ chạy khi user đã vừa ý toàn bộ technical design (đã refine qua `/design` self-loop). KHÔNG spawn agent author mới — chỉ verify gate + transition.

## Workflow
1. Xác nhận user OK toàn bộ design: hệ thống/contract (`/design`) VÀ UX (`/design-ux` — nếu có FE boundary). Chưa OK → quay lại `/design` hoặc `/design-ux` refine.
2. (Optional) Run `py scripts/build_prompt.py design-end` để xem checklist gate.
3. `py scripts/harness.py design-end complete '{}'` → DESIGN→PLAN.
4. Override (user đồng ý): `complete '{"force":true,"reason":"<lý do>"}'` → ghi audit decisions.md.

## Gate (design_gate + todo_resolved)
- ADR ≥3 + INTEG ≥1 ở `docs/architecture/`.
- **Per-boundary completeness**: MỖI boundary trong BOUNDARY-MAP đủ artifact đúng kind — backend→`hld-{b}.md`+`api-{b}.md`; web/mobile→`hld-{b}.md`+`ux-{b}.md`.
- Có FE boundary → `docs/architecture/ux/design-tokens.css` (SoT token) + **`ux/SCREEN-MAP.md`** (mục lục màn ↔ boundary ↔ FEAT ↔ mockup): gate parse từng row — **mockup phải TỒN TẠI + dùng design token**; màn gán boundary ma = chặn; **web boundary 0 màn = chặn** (thiết kế theo MÀN, duyệt look trong browser trước khi build).
- **`todo_resolved`**: field kỹ thuật translator để lại (`TODO engineer` / `TBD (DESIGN)` / `enforcement_location: TBD` / `scope: TBD` / `consumes_contracts` TBD) trong eng epics/feat/business-rules phải được DESIGN **điền hết** — BR không có nơi enforce = rule không bao giờ được code. Chưa chốt thật → ghi `Open question` có chủ, không để TBD.
- FAIL → bổ sung artifact boundary còn thiếu / điền TODO (qua `/design`) rồi `/design-end` lại.

## Sau DESIGN
Stage → PLAN. Chạy `/plan` (implementation-plan: WAVE-SEQUENCE + wave-{N} + MATRIX + KG skeleton).
