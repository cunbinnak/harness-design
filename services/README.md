# services/

Thư mục **materialize** — không có service cố định lúc BOOTSTRAP.

## Quy tắc

- Boundary định nghĩa trong `harness/SERVICE-BOUNDARY-MATRIX.json`; service folder = `services/{prefix}-{boundary}/` (prefix = `project.service_prefix`, vd. `crm-catalog`).
- Folder con **chỉ xuất hiện** khi stage `DEV` (sub-agent scaffold ở `/start-dev`, push lên repo riêng polyrepo).
- **Không** coi ví dụ cũ là spec thật nếu chưa có trong matrix.

## Cấu trúc gợi ý (sau materialize)

```
services/{prefix}-{boundary}/
  README.md
  src/
  tests/
```
