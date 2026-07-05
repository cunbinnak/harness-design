---
name: ux-design
description: UX/UI cho FE boundary (stage DESIGN, /design-ux, ux-designer-agent — tách vai khỏi solution-architect) — user flow, MOCKUP HTML tĩnh per screen (design bằng HTML, không ASCII), UI states đầy đủ, design tokens + Visual polish, a11y WCAG 2.1 AA, permission-based UI. Sinh ux-{boundary}.md + mockups/{boundary}/*.html + design-tokens.css.
---

# UX Design Skill

## Khi load
Command **`/design-ux`** (stage DESIGN, self-loop) — agent chuyên môn **`ux-designer-agent`**, tách vai khỏi solution-architect (`/design` lo hệ thống/contract). Chạy SAU khi `/design` đã chốt boundary + `api-{be}.md` (UX consume contract, không bịa endpoint).
Input: `PROJECT.md` (persona, platform, design system / ADR ui-kit) + `FEAT-*.md` (user story + AC) + `JOURNEY/PERSONA` + `api-{be}.md` (contract boundary phục vụ).

## Deliverable
**Đơn vị thiết kế = MÀN (screen)** — boundary chỉ là nơi màn thuộc về. Sản phẩm gồm:
- **`docs/architecture/ux/SCREEN-MAP.md`** — MỤC LỤC MÀN, sinh TRƯỚC khi vẽ (gate `design_gate` parse): bảng `| screen | route | boundary | feat | mockup | note |` — mỗi màn 1 row, gắn rõ màn ↔ FE boundary ↔ FEAT:AC ↔ đường dẫn mockup. **Luật gán màn → boundary** (quan trọng khi NHIỀU FE boundary): (1) FEAT frontmatter `target_experience_hint`/`target_boundary_hint`; (2) không có hint → journey + persona của FEAT so với persona pool của experience (BOUNDARY-MAP §2/§3 + CHARTER); (3) vẫn mơ hồ → **hỏi user**, KHÔNG đoán. Mỗi FEAT `has_ui_touchpoint=true` phải có ≥1 màn; màn dùng chung nhiều FEAT (list/detail) = 1 row ghi nhiều FEAT.
- **`docs/architecture/ux/ux-{boundary}.md`** — BEHAVIOR (không template — viết thẳng theo outline này, ngắn gọn bảng/bullet):
  `## 1 Tổng quan` (persona/platform/BE phục vụ) · `## 2 User flows` (mỗi FEAT Must ≥1) · `## 3 Screens` (mỗi screen: link mockup + bảng Screen states + API calls khớp `api-{be}.md` + validation FE map `error.code`→field) · `## 4 Permission UI` (ẩn/hiện theo role) · `## 5 Global patterns` (toast/routing-guard/loading-empty quy ước chung) · `## 6 A11y` (WCAG 2.1 AA checklist) · `## 7 Edge cases + handoff notes` · `## 8 Open questions`.
  **KHÔNG chép giá trị token vào .md** — `design-tokens.css` là SoT duy nhất về màu/spacing/chữ (chép = drift).
- **`docs/architecture/ux/mockups/{boundary}/{screen}.html`** — LOOK **per MÀN**: **THIẾT KẾ THẲNG giao diện hoàn chỉnh bằng HTML** (không có template — bạn là designer, tự dựng app shell + screen đẹp theo §Visual polish, như trang web thật). Khi thiết kế 1 màn, đọc ĐÚNG tài liệu của màn đó: FEAT (AC) trong row SCREEN-MAP + `api-{be}.md` mà flow màn gọi — không đọc cả đống boundary khác. Luật (mockups/README.md): HTML TĨNH mở `file://` xem được (không JS/build/CDN) · style CHỈ `var(--...)` từ design-tokens.css (thiếu token → thêm vào SoT, không bịa tại chỗ) · nội dung thật không lorem · state phụ (loading/empty/error) = section trong cùng file · responsive media query · đủ `:hover`/`:focus-visible`. **Gate `design_gate` parse SCREEN-MAP: mọi row mockup phải TỒN TẠI + dùng token; web boundary không có màn nào = chặn.** User duyệt "đẹp/xấu" TRÊN MOCKUP trước khi build; dev FE (rules-web) bám mockup; reviewer đối chiếu.

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
2. **SCREEN-MAP trước** (mục lục màn): từ FEAT `has_ui_touchpoint` + journeys derive danh sách MÀN → gán boundary theo luật (hint → persona → hỏi) → ghi bảng SCREEN-MAP.md. Đây là kế hoạch thiết kế — user thấy được toàn cảnh màn nào thuộc đâu trước khi vẽ.
3. **Thiết kế TỪNG MÀN** (đơn vị công việc — đi theo SCREEN-MAP, ưu tiên màn trong flow FEAT Must):
   - Đọc đúng tài liệu của màn: FEAT:AC trong row + `api-{be}.md` mà flow gọi + journey liên quan.
   - **Mockup HTML** (`mockups/{boundary}/{screen}.html`): THIẾT KẾ giao diện hoàn chỉnh — app shell + nội dung screen thật, compose từ token, link `../../design-tokens.css`. Mockup là SoT về look — làm "đẹp" ở ĐÂY theo §Visual polish, không tả suông, không skeleton chờ điền.
   - **Component states đầy đủ**: default / hover / disabled / loading / error / empty — state chính render trong mockup, bảng behavior ở ux-*.md.
   - **API calls**: trigger → endpoint → method → loading state, khớp `api-{be}.md`.
   - **Validation FE-side**: field · required · rule · error message.
   - Mobile layout riêng nếu khác desktop đáng kể.
4. **Permission-based UI**: ẩn/hiện element theo role (`roles[]` từ JWT) — ghi rõ phần tử nào cần quyền gì.
5. **Responsive**: breakpoint desktop / tablet / mobile + hành vi (sidebar collapse, table → card…).
6. **Accessibility (WCAG 2.1 AA)**: label/`aria-label`, focus visible, contrast ≥ 4.5:1, keyboard nav (Tab/Enter/Esc), `role`/`aria-live` cho modal/toast, error gắn input qua `aria-describedby`.
7. **Dev handoff notes**: animation/transition, edge case (empty / long text / overflow), breakpoint, a11y.

## Quality checklist
- [ ] **SCREEN-MAP đủ**: mọi FEAT `has_ui_touchpoint` có ≥1 màn; mọi màn gán đúng boundary (mơ hồ đã hỏi user); mọi web boundary có ≥1 màn.
- [ ] Mọi FEAT Must có user flow.
- [ ] Mọi màn trong SCREEN-MAP có **mockup HTML tồn tại** mở browser xem được (responsive trong cùng file; đủ section state phụ) — gate parse từng row.
- [ ] Mockup CHỈ dùng `var(--...)` — không hardcode hex/px (gate design_gate check reference token).
- [ ] Mọi component có đủ states (default/hover/disabled/loading/error/empty).
- [ ] API call mỗi screen khớp `api-{be}.md` (op name, method, loading state).
- [ ] Design tokens referenced — KHÔNG hardcode màu/spacing/typography; shared `design-tokens.css` tồn tại + §4 trỏ tới nó.
- [ ] Permission-based UI documented (ẩn/hiện theo quyền).
- [ ] A11y WCAG 2.1 AA checklist pass.
- [ ] Handoff notes có edge case dev dễ sót.

## Done
- `ux-{boundary}.md` (theo template) đủ user flow + screens + states + a11y + permission UI cho mọi FEAT Must của FE boundary.
