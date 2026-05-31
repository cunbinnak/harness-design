---
name: ux-design
description: UX/UI cho FE boundary (intake step 3) — user flow, wireframe, UI states đầy đủ, design tokens, a11y WCAG 2.1 AA, permission-based UI. Sinh ux-{boundary}.md.
---

# UX Design Skill

## Khi load
Intake **step 3** (`solution-architect`) khi thiết kế UX cho **FE boundary** (kind `web`/`mobile`). Là **sub-skill** — `technical-design` invoke tới khi làm UX cho FE boundary (không phải step riêng).
Input: `PROJECT.md` (persona, platform, design system / ADR ui-kit) + `FEAT-*.md` (user story + AC) + `api-{be}.md` (contract boundary phục vụ).

## Deliverable
`docs/architecture/ux/ux-{boundary}.md` theo `TEMPLATE.ux.md` — mỗi FE boundary 1 file:
- **Tổng quan**: persona, platform, design system, a11y target, BE boundaries phục vụ.
- **User flows**: mỗi FEAT Must ≥ 1 flow.
- **Screens**: wireframe + components + API calls + UI states + validation FE.
- **Global UI patterns**: toasts, routing/guards, responsive, a11y checklist.
- **Open questions**.

## Design system trước khi vẽ
- Project có design system / **ADR ui-kit** → TUÂN THEO (layout, color, component pattern, mobile nav).
- Chưa có → tự define dựa `PROJECT.md` + best practice, rồi ghi vào **ADR ui-kit**.
- KHÔNG hardcode color/spacing/typography → **reference design tokens**.

## Phương pháp
1. **Research (optional)** — nếu domain/UX chưa rõ + có WebSearch: UX pattern cho product type (form/table/dashboard), WCAG 2.1 AA, enterprise design system (Ant/Material/Atlassian), mobile-first. KHÔNG bịa nguồn.
2. **User flow** per FEAT Must: entry → screens → nhánh success/error (ASCII nav hoặc Mermaid).
3. **Per screen**:
   - Wireframe ASCII có annotation rõ.
   - **Component states đầy đủ**: default / hover / disabled / loading / error / empty.
   - **API calls**: trigger → endpoint → method → loading state, khớp `api-{be}.md`.
   - **Validation FE-side**: field · required · rule · error message.
   - Mobile layout riêng nếu khác desktop đáng kể.
4. **Permission-based UI**: ẩn/hiện element theo role (`roles[]` từ JWT) — ghi rõ phần tử nào cần quyền gì.
5. **Responsive**: breakpoint desktop / tablet / mobile + hành vi (sidebar collapse, table → card…).
6. **Accessibility (WCAG 2.1 AA)**: label/`aria-label`, focus visible, contrast ≥ 4.5:1, keyboard nav (Tab/Enter/Esc), `role`/`aria-live` cho modal/toast, error gắn input qua `aria-describedby`.
7. **Dev handoff notes**: animation/transition, edge case (empty / long text / overflow), breakpoint, a11y.

## Quality checklist
- [ ] Mọi FEAT Must có user flow.
- [ ] Mọi màn hình mới có wireframe (desktop + mobile nếu khác).
- [ ] Mọi component có đủ states (default/hover/disabled/loading/error/empty).
- [ ] API call mỗi screen khớp `api-{be}.md` (op name, method, loading state).
- [ ] Design tokens referenced — KHÔNG hardcode màu/spacing/typography.
- [ ] Permission-based UI documented (ẩn/hiện theo quyền).
- [ ] A11y WCAG 2.1 AA checklist pass.
- [ ] Handoff notes có edge case dev dễ sót.

## Done
- `ux-{boundary}.md` (theo template) đủ user flow + screens + states + a11y + permission UI cho mọi FEAT Must của FE boundary.
