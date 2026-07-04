# CR-NNN: (tiêu đề ngắn)

> **Harness:** file CR trong repo = **đã duyệt**. Không command approve riêng.

- **Status:** proposed | approved | implemented | rejected
- **Date:** YYYY-MM-DD
- **Wave ảnh hưởng:** wave-001, wave-002 (hoặc —)
- **Áp dụng từ:** DONE state → `/apply-cr` → DESIGN amendment
- **Loại:** scope | business-rule | ux | technical | bug-as-change

## Mô tả thay đổi

(điều gì thay đổi so với baseline đã duyệt)

## Tài liệu cần cập nhật

| File / vùng | Hành động |
|-------------|-----------|
| docs/architecture/feat/FEAT-xxx.md | sửa AC … |
| docs/plans/wave-{NNN}.md | bổ sung task … |
| docs/architecture/… | chỉ nếu ảnh hưởng boundary |

## Kế hoạch cập nhật

_(apply-cr agent điền — sau `apply-cr complete`: STATE → DESIGN; user chạy `/design` (amendment) → `/plan` → REVIEW)_

| File / vùng | Hành động |
|-------------|-----------|
| | |

- **Boundaries ảnh hưởng:** (chỉ id trong roster/matrix)
- **Cần re-design (DESIGN amendment):** yes / no
- **Blocker / open questions:**

## Phạm vi implement

- Boundary:
- Có cần `/design` (amendment) → `/plan` không: yes / no (CR đổi product → `/domain-po`·`/domain-ba` → ký → `/domain-translate` trước)

## Quyết định

- **Approved by:**
- **Ghi vào KG:** `decision:CR-NNN` trong `knowledge-base/{boundary}.knowledge-graph.yaml`
