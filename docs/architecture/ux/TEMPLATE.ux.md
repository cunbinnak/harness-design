# UX — {boundary_id}

> Trải nghiệm người dùng gắn boundary `{boundary_id}`. Với **fe**: màn hình, luồng, trạng thái UI. Backend: chỉ khi có UI admin/portal riêng — nếu không, ghi *N/A* ngắn.

## Hình thức thiết kế (chọn lúc lên plan — bước 4)

Ghi rõ quyết định trong `docs/plans/waves/{wave-id}/wave.md` §1. **Một** trong các hướng (hoặc kết hợp):

| Hình thức | Khi dùng | Đặt tài liệu / link |
|-----------|----------|---------------------|
| **Markdown** (mặc định) | MVP, spec text + bảng dưới | Nội dung trong file này |
| **Wireframe** | Cần layout thô, chưa visual | `docs/architecture/ux/assets/{boundary_id}/wireframes/` (PNG/SVG/PDF) hoặc link |
| **Figma** (hoặc tool tương đương) | Đã có design system / high-fidelity | Link Figma + frame chính; file này giữ **map** màn hình ↔ flow |

```yaml
# Gợi ý frontmatter (tùy chọn) — đồng bộ với wave plan
ux_deliverable: markdown | wireframe | figma | mixed
figma_url: ""          # nếu figma
wireframe_path: ""     # nếu wireframe trong repo
```

**Không bắt buộc** một loại cố định — team chọn theo wave; gate intake vẫn cần file `ux-{boundary_id}.md` (spec + link asset nếu có).

## Phạm vi UX

- **Persona / vai trò:**
- **FEAT liên quan:** (link `docs/product/FEAT-*.md`)
- **Tham chiếu dự án:** `docs/product/PROJECT.md`

## Nguyên tắc & ràng buộc

- Accessibility / ngôn ngữ / thiết bị:
- Nhất quán với design system (nếu có):

## Luồng người dùng (user flows)

| Flow ID | Tên | Bước chính | FEAT / AC |
|---------|-----|------------|-----------|
| UF-1 | | | |

```mermaid
flowchart LR
  %% ví dụ luồng checkout
```

## Màn hình / thành phần

| Screen / Component | Mục đích | Wireframe / Figma ref | Trạng thái UI | API / data |
|--------------------|----------|------------------------|---------------|------------|
| | | (link frame hoặc `assets/.../screen-x.png`) | empty/loading/error | |

## Trạng thái & thông báo

| Tình huống | Hành vi UI | Copy / message |
|------------|------------|----------------|
| | | |

## Liên kết kỹ thuật

| Loại | File |
|------|------|
| HLD FE | `docs/architecture/hld/hld-{boundary_id}.md` |
| API tiêu thụ | `docs/architecture/api/api-*.md` |
| Data hiển thị | `docs/architecture/data-model/data-model-*.md` |
| Wave plan (quyết định wireframe/figma) | `docs/plans/waves/{wave-id}/wave.md` §1 |

## Mở / chưa quyết

-
