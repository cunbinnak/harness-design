# UX — {boundary_id}

> **Purpose:** User flows + wireframes + UI states cho FE boundary `{boundary_id}`.
> **Owner:** `intake:solution-architect` (intake bước 3).
> **Audience:** `dev:frontend`, `review:frontend`, `test-plan` (E2E + manual TC), stakeholder UAT.
> **Out of scope:**
> - BE implementation → [`../hld/hld-{be_boundary}.md`](../hld/)
> - API endpoints → [`../api/api-{be_boundary}.md`](../api/)
> - DB schema → [`../data-model/data-model-{be_boundary}.md`](../data-model/)

---

## Tổng quan

| | |
|---|---|
| **Persona chính** | (vai trò — chi tiết user ở [PROJECT.md](../PROJECT.md)) |
| **Platform** | Web SPA / Mobile / Hybrid |
| **Design system** | (khớp ADR ui-kit nếu có) |
| **Ngôn ngữ** | (vi / en / multi) |
| **A11y target** | WCAG 2.1 AA |
| **BE boundaries phục vụ** | (list `{be_id}` — đọc API từ [`../api/`](../api/)) |

---

## User flows

> Mỗi FEAT Must có ít nhất 1 flow. ASCII navigation diagram.

### UF-1 — {tên flow} ({FEAT-001})

```
[Entry]
   │
   ▼
SCR-001 ── action ──► SCR-002 ── submit ──► SCR-003 (success)
                         │                       │
                  validation fail            error toast
                         ▼                       │
                   SCR-002 (errors)              ▼
                                            SCR-002 (retry)
```

**Mô tả ngắn:**
1. User vào `SCR-001` → thấy {content}
2. Action → `SCR-002` form
3. Submit → pass: `SCR-003` · fail: inline error

### UF-2 — (thêm flow per FEAT)

---

## Screens

> Per screen: wireframe + components + API calls + UI states. Bỏ qua sections KHÔNG áp dụng.

### SCR-001 — {Tên màn hình list}

**Route:** `/{path}` · **Mục đích:** (1 câu) · **States:** loading | empty | filled | error

#### Wireframe

```
┌─────────────────────────────────────────────────┐
│  Header                              [User] [⋮] │
├─────────────────────────────────────────────────┤
│  Page Title                  [+ Tạo mới]        │
│  [Tìm kiếm ___]  [Filter ▼]                     │
│  ┌─────────────────────────────────────────┐   │
│  │ # │ Tên     │ Status   │ Date   │ Action│   │
│  │ 1 │ {name}  │ ● Active │ 2026..│ [✎][🗑]│   │
│  └─────────────────────────────────────────┘   │
│  ◄ Prev  [1][2][3]…  Next ►                     │
└─────────────────────────────────────────────────┘
```

#### Components

| Component | Loại | Note |
|-----------|------|------|
| `<DataTable>` | display | sortable, paginated |
| `<SearchInput>` | input | debounce 300ms |

#### API calls

| Trigger | Endpoint | Method | Loading state |
|---------|----------|--------|--------------|
| Mount / filter | `/v1/{resource}?page=N&q=...` | GET | Skeleton |
| Delete row | `/v1/{resource}/{id}` | DELETE | Button disabled |

#### UI states

| State | Hiển thị | Trigger |
|-------|---------|---------|
| loading | Skeleton rows | API đang gọi |
| empty | "Chưa có dữ liệu. [+ Tạo mới]" | data.length === 0 |
| error | Toast "Lỗi tải. Thử lại" | API error |

---

### SCR-002 — {Tên form / modal}

**Type:** Modal / Full page · **Mục đích:** Create / Edit `{entity}` · **States:** idle | submitting | success | error

#### Wireframe

```
┌─────────────────────────────────────┐
│  {Title}                        [✕] │
├─────────────────────────────────────┤
│  Tên *  [___________________]       │
│   ! Tên không được để trống         │
│  Mô tả  [textarea, 3 rows]          │
│  Status: ○ Active ● Pending         │
├─────────────────────────────────────┤
│            [Hủy]    [Lưu]           │
└─────────────────────────────────────┘
```

#### Validation rules (FE-side)

| Field | Required | Rule | Error message |
|-------|----------|------|--------------|
| Tên | ✓ | 2–100 ký tự | "Tên không được để trống / quá dài" |
| Mô tả | ✗ | max 500 | "Tối đa 500 ký tự" |

#### API calls

| Action | Endpoint | Method | On success | On error |
|--------|----------|--------|------------|---------|
| Submit create | `/v1/{resource}` | POST | Close modal, refresh, ✓ toast | Inline error |
| Submit update | `/v1/{resource}/{id}` | PUT | Same | Inline error |

---

### SCR-003 — (thêm màn hình khác — bỏ qua section không áp dụng)

---

## Global UI patterns

### Notifications / Toasts

| Tình huống | Style | Vị trí | Nội dung mẫu |
|-----------|-------|--------|-------------|
| Success | green | top-right, 3s | "✓ Lưu thành công" |
| Error | red | top-right | "Lỗi hệ thống" |
| Confirm delete | dialog | center modal | "Bạn chắc muốn xóa?" |

### Routing & guards

```
/                     → Home / Dashboard
/{resource}           → SCR-001 (list)
/{resource}/new       → SCR-002 (create)
/{resource}/{id}      → SCR-003 (detail)
/{resource}/{id}/edit → SCR-002 (edit mode)
/login                → Login
/403, /404            → Error pages
```

- All `/{resource}*` → require auth token
- Redirect `/login?redirect={current}` nếu token invalid

### Responsive

| Breakpoint | Behavior |
|-----------|----------|
| Desktop (≥1024px) | Full layout, sidebar visible |
| Tablet (768–1023px) | Sidebar collapse |
| Mobile (<768px) | Stack, table → card |

### Accessibility checklist (WCAG 2.1 AA)

- [ ] Form input có `label` / `aria-label`
- [ ] Focus visible mọi interactive
- [ ] Color contrast ≥ 4.5:1
- [ ] Keyboard navigation (Tab/Enter/Esc)
- [ ] `role="dialog"` cho modal, `aria-live` cho toast
- [ ] Error msg gắn input qua `aria-describedby`

## Open questions

| # | Câu hỏi | Owner | Deadline |
|---|---------|-------|----------|
| | | | |
