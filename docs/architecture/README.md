# docs/architecture — Thiết kế kỹ thuật (theo boundary)

Mỗi `boundary_id` (từ architect, bước 3 intake) có **bộ 4 tài liệu** — agent làm theo template tương ứng:

| Thư mục | File output | Template |
|---------|-------------|----------|
| `hld/` | `hld-{boundary_id}.md` | [hld/TEMPLATE.hld.md](hld/TEMPLATE.hld.md) |
| `api/` | `api-{boundary_id}.md` | [api/TEMPLATE.api.md](api/TEMPLATE.api.md) |
| `data-model/` | `data-model-{boundary_id}.md` | [data-model/TEMPLATE.data-model.md](data-model/TEMPLATE.data-model.md) |
| `ux/` | `ux-{boundary_id}.md` | [ux/TEMPLATE.ux.md](ux/TEMPLATE.ux.md) |

**Bắt buộc UX:** boundary **`fe`** (hoặc `frontend`) — `ux-fe.md` phải có luồng + màn hình. Backend chỉ cần `ux-{id}.md` nếu có UI (admin, portal); không thì một dòng N/A trong file hoặc bỏ qua.

**Ví dụ** boundaries `order`, `product`, `fe`:

```text
docs/architecture/
  hld/hld-order.md, hld-product.md, hld-fe.md
  api/api-order.md, ...
  data-model/data-model-order.md, ...
  ux/ux-fe.md                    # bắt buộc khi có UI
  ux/ux-order.md                 # tùy chọn (admin API UI)
```

HLD tham chiếu API, data-model và UX (không copy nguyên khối). Matrix: `harness/SERVICE-BOUNDARY-MATRIX.json`.
