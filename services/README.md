# services/

Thư mục **materialize** — không có service cố định lúc BOOTSTRAP.

## Quy tắc

- Boundary định nghĩa trong `harness/SERVICE-BOUNDARY-MATRIX.json` → `materialized_path` (vd. `services/catalog-api/`).
- Folder con **chỉ xuất hiện** khi stage `IMPLEMENTATION` (hoặc script `materialize_boundary`).
- **Không** coi `product-service/` / ví dụ cũ là spec thật nếu chưa có trong matrix.

## Cấu trúc gợi ý (sau materialize)

```
services/{boundary_id}/
  README.md
  src/
  tests/
```
