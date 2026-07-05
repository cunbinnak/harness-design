---
type: design
artifact_kind: ux-spec
boundary: "{{fe-boundary-name}}"   # boundary kind=web/mobile trong MATRIX
status: "DRAFT | APPROVED | DEPRECATED"
platform: ["web"]                  # ["web"] | ["mobile"] | ["web","mobile"]
a11y_target: "WCAG 2.1 AA"
last_reviewed: "{{DATE}}"
---

> Điền NGẮN GỌN: ưu tiên bảng/bullet, không văn xuôi thừa, không lặp. Doc này agent downstream đọc nhiều lần — tiết kiệm context.

# UX — `{{boundary}}` (FE)

> 1 file / FE boundary (kind=web/mobile): user-flow + nhiều screen + design tokens + component API + global UI patterns. **Visual = MOCKUP HTML** per screen ở `ux/mockups/{{boundary}}/{{screen}}.html` (theo `mockups/TEMPLATE.mockup.html` — tĩnh, mở browser xem được, chỉ dùng `var(--...)` từ design-tokens.css; gate `design_gate` đòi ≥1 mockup/web boundary). KHÔNG ASCII wireframe. Author ở DESIGN (`/design-ux`, ux-designer). File .md này tả BEHAVIOR (states/API/validation/a11y) — mockup tả LOOK.

---

## 1. Tổng quan

| Aspect | Value |
|---|---|
| Boundary | `{{boundary}}` (kind {{web/mobile}}) |
| Personas | `personas/PERSONA-{{name}}.md` (chính + phụ) |
| Platform | {{web desktop+mobile / iOS+Android}} |
| Design system / ui-kit | theo **ADR ui-kit** (`adr/ADR-*-ui-kit.md`) — màu/spacing/typography qua **design tokens** (§4), KHÔNG hardcode |
| A11y target | WCAG 2.1 AA (§9) |
| Theming | light + dark + high-contrast (§4.6) |
| BE boundaries phục vụ | `{{be-boundary}}` (`api/api-{{be-boundary}}.md`) |
| FEAT trong boundary | `feat/FEAT-*.md` (mỗi FEAT Must ≥1 flow §2) |

---

## 2. User flows

> Mỗi FEAT Must ≥ 1 flow: entry → screens → nhánh success/error. ASCII nav hoặc Mermaid.

### 2.1 Flow: {{FEAT-NNN — tên flow}}

```
[Danh sách đơn] --bấm "Hoàn tiền"--> [Form hoàn tiền] --submit hợp lệ--> [Chi tiết yêu cầu] (toast OK)
                                          └--lỗi BR--> [Form + field error] (form re-enable)
```

<!-- Thêm flow cho mỗi FEAT Must -->

---

## 3. Screens

> Lặp block cho MỖI screen. Visual = mockup HTML (link dưới). Component states đầy đủ. API call khớp `api-{{be}}.md`.

### 3.1 Screen: {{Tên màn}} (`/refunds/new`)

**Mục tiêu**: {{1 câu user làm gì}}.

**Mockup**: [`mockups/{{boundary}}/{{screen}}.html`](mockups/{{boundary}}/{{screen}}.html) — mở bằng browser để duyệt look & feel (state phụ loading/empty/error là các section trong cùng file). Layout/spacing/màu là SoT ở mockup; bảng dưới là SoT về BEHAVIOR.

**Component states** (mỗi component nêu đủ trong: `default / hover / focus / disabled / loading / error / empty`):

| Component | States cần | Ghi chú |
|---|---|---|
| `<RefundForm>` | default · editing-valid · editing-invalid · submitting · be-error | submit disabled khi invalid/submitting |
| `<AmountInput>` | default · focus · error | currency prefix |
| `<AttachmentUploader>` | empty · uploading · done · rejected | progress per file |

**API calls** (khớp `api/api-{{be-boundary}}.md`):

| Trigger | Operation | Method | Loading state |
|---|---|---|---|
| Submit form | `POST /refunds` | POST | submit spinner + form lock |
| Load card đơn | `GET /payments/:id` | GET | skeleton card |

**Validation FE-side** (UX shortcut — BE owns truth qua BR; map BE `error.code` → field):

| Field | Required | Rule | BE error.code → field |
|---|---|---|---|
| amount | Yes | ≥0, ≤ payment.balance, 2 decimals | `REFUND_TOO_LARGE` |
| reason | Yes | 5–500 ký tự | `VALIDATION_FAILED` (details.field=reason) |
| attachments | No | ≤10MB, jpg/png/pdf | `ATTACHMENT_REJECTED` |

**Screen states**:

| State | Visual cue |
|---|---|
| Initial / empty | Form blank, submit disabled |
| Editing (invalid) | Field error visible, submit disabled |
| Submitting | Submit disabled + spinner, form locked |
| Success | Toast + redirect `/refunds/:id` |
| BE error (4xx/422) | Field/form error theo `error.code`, form re-enabled |
| Network error (5xx) | Toast + retry |
| Offline | Banner + queue submit |

**Responsive**:

| Breakpoint | Layout |
|---|---|
| Mobile (<768px) | 1 cột; card collapse |
| Tablet (768–1024) | form 2 cột; card sticky |
| Desktop (>1024) | mặc định wireframe trên |

<!-- Lặp §3.x cho màn tiếp -->

---

## 4. Design tokens

> Token semantic — lấy từ **ADR ui-kit** (`adr/ADR-*-ui-kit.md`). KHÔNG hardcode hex/px trong code. Web → CSS var / Tailwind; mobile → theme object (Flutter `ColorScheme`/`TextTheme`).

### 4.1 Color (semantic)

| Token | Giá trị | Dùng cho |
|---|---|---|
| `color.primary` / `color.primary-fg` | `{{#1E40AF}}` / `{{#FFFFFF}}` | Hành động chính / chữ trên primary |
| `color.surface` / `color.text` / `color.text-muted` | `{{#FFFFFF}}` / `{{#0F172A}}` / `{{#64748B}}` | Nền / chữ chính / chữ phụ |
| `color.success` / `color.warning` / `color.error` | `{{#16A34A}}` / `{{#F59E0B}}` / `{{#DC2626}}` | OK / cảnh báo / lỗi |
| `color.border` / `color.border-focus` | `{{#E5E7EB}}` / `{{#3B82F6}}` | Viền / focus ring |

### 4.2 Typography

| Token | Giá trị |
|---|---|
| `font.family-sans` | `{{'Inter', system-ui, sans-serif}}` |
| `font.size.sm/base/lg/xl` | `{{14/16/18/20}}px` |
| `font.size.2xl/3xl/4xl` | `{{24/30/36}}px` (h3/h2/h1) |
| `font.weight.normal/medium/semibold/bold` | `{{400/500/600/700}}` |
| `font.leading.tight/normal/relaxed` | `{{1.2/1.5/1.75}}` |

### 4.3 Spacing

| Token | Giá trị |
|---|---|
| `space.1/2/3/4` | `{{4/8/12/16}}px` |
| `space.6/8/12/16` | `{{24/32/48/64}}px` |

### 4.4 Radius / elevation / motion

| Token | Giá trị |
|---|---|
| `radius.sm/md/lg/full` | `{{4/8/12/9999}}px` |
| `elevation.1/2/3` | `{{0 1px 2px / 0 4px 8px / 0 12px 24px}}` |
| `motion.fast/base/slow` | `{{120/200/320}}ms` · `motion.ease` `{{cubic-bezier(0.4,0,0.2,1)}}` |

### 4.5 Codegen mapping

| Nhóm | Web | Mobile (Flutter) |
|---|---|---|
| Color | `--color-primary` | `ColorScheme.primary` |
| Typography | `--font-size-base` | `TextTheme` entry |
| Spacing | Tailwind / CSS var | `EdgeInsets.all(Spacing.md)` |
| Radius / Motion | CSS var / transition | `BorderRadius` / `Duration+Curves` |

### 4.6 Theming

| Mode | Bắt buộc | Override |
|---|---|---|
| Light | Yes | default |
| Dark | Yes | system preference + user override (`color-dark.*`) |
| High contrast | Yes | map từ OS / forced-colors |

---

## 5. Component API (boundary-level / shared)

> API component dùng chung (prop contract, KHÔNG implementation). Lặp block cho mỗi component đáng tài liệu hoá.

### 5.1 `<Button>`

| Prop | Type | Default | Bắt buộc | Mô tả |
|---|---|---|---|---|
| `variant` | `"primary"\|"secondary"\|"ghost"\|"danger"` | `"primary"` | no | Mức nhấn |
| `size` | `"sm"\|"md"\|"lg"` | `"md"` | no | Kích thước |
| `disabled` / `loading` | `boolean` | `false` | no | Vô hiệu / spinner+disable |
| `iconLeft / iconRight` | `IconName?` | — | no | Icon kèm |
| `aria-label` | `string?` | — | yes nếu icon-only | Nhãn a11y |
| `onClick` | `(e) => void` | — | no | Handler |

**Behavior**: disabled = no focus + `aria-disabled` + opacity .5; loading = `aria-busy` + spinner, label giữ. Touch target ≥ 48px (mobile) / 40px (web).
**A11y**: `<button>` semantic; Space+Enter trigger; focus ring 2px `border-focus` offset 2px.

### 5.2 `<Input>` / `<Dialog>` / `<Toast>` …

{{Lặp shape §5.1: props table + behavior + a11y}}

---

## 6. Content (copy → i18n)

> Mọi text user-facing qua i18n key — KHÔNG hardcode.

| Element | i18n key | vi |
|---|---|---|
| Page title | `refunds.form.title` | "Yêu cầu hoàn tiền" |
| Submit | `refunds.form.submit` | "Gửi yêu cầu" |
| Lỗi `REFUND_TOO_LARGE` | `refunds.errors.too_large` | "Số tiền vượt số dư có thể hoàn" |

---

## 7. Permission-based UI

> Ẩn/hiện theo `roles[]` (JWT). Defense-in-depth: BE VẪN enforce — ẩn UI chỉ cho UX.

| Element | Role cần | Khi thiếu quyền |
|---|---|---|
| Nút "Gửi yêu cầu" | `refund-issuer` | ẩn nút |
| Tab "Duyệt" | `manager` | ẩn tab |

---

## 8. Global UI patterns

- **Toast**: success/error/warning — vị trí + thời gian + `aria-live`.
- **Routing/guards**: route nào cần auth/role; redirect khi 401/403.
- **Responsive**: breakpoint chung (sidebar collapse, table → card).
- **Empty/overflow**: quy ước chung. **Loading**: skeleton (initial) vs spinner (action).

---

## 9. Accessibility (WCAG 2.1 AA)

| Aspect | Implementation |
|---|---|
| Heading | `<h1>` page title, không skip level |
| Form labels | `<label for>` mọi input |
| Required | `aria-required="true"` + dấu * |
| Error association | `aria-describedby` input → error |
| Submit feedback | `aria-busy` khi submitting |
| Focus | field invalid đầu tiên nhận focus khi submit |
| Keyboard | Tab order rõ; Enter submit; Esc đóng modal; focus trap trong dialog |
| Contrast | ≥ 4.5:1 (text), ≥ 3:1 (UI component/icon) |
| Touch target | ≥ 44pt iOS / 48dp Android / 40px web |
| Reduced motion | tắt animation khi `prefers-reduced-motion` |
| Screen reader | semantic markup; aria tối thiểu-đúng; live region async update |
| Forced colors | high-contrast Windows: component vẫn dùng được |

---

## 10. Edge cases + dev handoff

- [ ] Đơn đã hoàn hết → chặn từ list; URL trực tiếp → "không còn số dư" + back.
- [ ] Concurrent: admin khác hoàn cùng đơn → optimistic lock `409 CONFLICT` → reload.
- [ ] User tier đổi giữa session → refresh role check khi submit; cấm → `403` friendly.
- [ ] Browser back sau submit success → về `/refunds`, KHÔNG quay lại form.
- [ ] Animation/transition + overflow text + breakpoint — note cho dev.

---

## 11. Open questions

- [ ] {{Câu hỏi cần Business/Architecture chốt}}

---

## 12. References

- FEAT: `feat/FEAT-*.md` · Persona: `personas/PERSONA-*.md` · Flow: `hld/hld-{{boundary}}.md §4`
- Backend contract: `api/api-{{be-boundary}}.md` · Tokens/ui-kit: `adr/ADR-*-ui-kit.md` · Convention: `rules-web` / `rules-mobile`

---

## 13. Change log

| Date | Author | Description |
|---|---|---|
| {{DATE}} | solution-architect | Initial UX spec cho `{{boundary}}` |
