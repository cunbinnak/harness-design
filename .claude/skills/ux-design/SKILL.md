---
name: ux-design
description: UX/UI cho FE boundary (stage DESIGN, /design-ux, ux-designer-agent — tách vai khỏi solution-architect) — user flow, wireframe, UI states đầy đủ, design tokens + Visual polish, a11y WCAG 2.1 AA, permission-based UI. Sinh ux-{boundary}.md + design-tokens.css.
---

# UX Design Skill

## Khi load
Command **`/design-ux`** (stage DESIGN, self-loop) — agent chuyên môn **`ux-designer-agent`**, tách vai khỏi solution-architect (`/design` lo hệ thống/contract). Chạy SAU khi `/design` đã chốt boundary + `api-{be}.md` (UX consume contract, không bịa endpoint).
Input: `PROJECT.md` (persona, platform, design system / ADR ui-kit) + `FEAT-*.md` (user story + AC) + `JOURNEY/PERSONA` + `api-{be}.md` (contract boundary phục vụ).

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
- **Shared design tokens:** tạo/giữ `docs/architecture/ux/design-tokens.css` (SoT 1 file dùng chung MỌI web boundary, theo `TEMPLATE.design-tokens.css`: `--color-*`/`--font-*`/`--space-*`/`--radius-*` + dark/hc theme). ux-{boundary}.md §4 tham chiếu token NÀY (không bịa palette per-boundary). Web FE consume qua `var(--...)`; mobile map `ThemeData`/`ColorScheme`. Gate `web_styling` ép plain-CSS phải dùng `var(--...)`.

## Visual polish (spec CỤ THỂ để dev implement được "đẹp" — không chung chung)
Ghi vào `ux-{boundary}.md §4` (dev implement + review-web/test-execute đối chiếu được):
- **App shell**: layout khung chuẩn (header + nav + content + footer) dùng chung mọi screen — screen chỉ đổi content, KHÔNG mỗi trang một khung.
- **Spacing rhythm**: MỌI padding/margin/gap từ `--space-*` (scale 4/8px) — cấm số lẻ tùy tiện; mật độ nhất quán (form row gap, card padding, section gap ghi rõ token nào).
- **Type scale**: heading/body/label dùng `--font-size-*` + `--font-weight-*`; mỗi screen có hierarchy rõ (1 h1, section h2, không nhảy cấp).
- **Component primitives**: Button (primary/secondary/danger + hover/focus/disabled), Input (+error state), Card, Table, Badge, Modal, Toast — định nghĩa 1 lần (style từ token), mọi screen compose lại; KHÔNG style ad-hoc per-page.
- **Interaction states**: element tương tác PHẢI có `:hover` + `:focus-visible` (outline token) + transition (`--motion-*`); loading = skeleton/spinner có style, empty = illustration/hint căn giữa (không text trần), error = màu `--color-danger` + hướng dẫn.
- **Elevation + depth**: card/modal dùng `--shadow-*` + `--radius-*` nhất quán — phân lớp rõ, không phẳng lì cũng không bóng đổ hỗn loạn.

## Phương pháp
1. **Research** — nếu domain/UX chưa rõ + có WebSearch: UX pattern cho product type (form/table/dashboard), WCAG 2.1 AA, enterprise design system (Ant/Material/Atlassian), mobile-first. KHÔNG bịa nguồn.
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
- [ ] Design tokens referenced — KHÔNG hardcode màu/spacing/typography; shared `design-tokens.css` tồn tại + §4 trỏ tới nó.
- [ ] Permission-based UI documented (ẩn/hiện theo quyền).
- [ ] A11y WCAG 2.1 AA checklist pass.
- [ ] Handoff notes có edge case dev dễ sót.

## Done
- `ux-{boundary}.md` (theo template) đủ user flow + screens + states + a11y + permission UI cho mọi FEAT Must của FE boundary.
