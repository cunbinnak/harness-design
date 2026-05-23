# Data model — {boundary_id}

> Mô hình dữ liệu **sở hữu** bởi boundary `{boundary_id}` (logical / physical tùy giai đoạn).

## Phạm vi

- **Aggregate / bounded context:**
- **Nguồn sự thật (source of truth):** boundary này

## Thực thể & quan hệ

| Entity | Mô tả | Khóa | Quan hệ |
|--------|--------|------|---------|
| | | | |

(sơ đồ ER / mermaid tùy chọn)

```mermaid
erDiagram
  %% ví dụ
```

## Thuộc tính quan trọng

| Entity | Field | Kiểu | Ràng buộc / ghi chú |
|--------|-------|------|---------------------|
| | | | |

## Vòng đời / trạng thái

| Entity | State machine / enum |
|--------|---------------------|
| | |

## Migration & lưu trữ (gợi ý)

- DB / store dự kiến:
- Chỉ mục / partition:

## Đồng bộ với API

- Operation nào đọc/ghi entity nào → `docs/architecture/api/api-{boundary_id}.md`

## Tham chiếu

- HLD: `docs/architecture/hld/hld-{boundary_id}.md`
- FEAT: `docs/product/FEAT-*.md`
