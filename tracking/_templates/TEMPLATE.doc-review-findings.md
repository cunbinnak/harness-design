# Doc Review Findings

> Ghi bởi `review-document-agent` mode **sanity-check** (`review-document` KHÔNG argument) ở stage REVIEW.
> Soi toàn bộ doc đã author (discovery + domain + design + plan) tìm **gap / mâu thuẫn / thiếu độ phủ** TRƯỚC khi approve → start-wave.
>
> **Mỗi gap = 1 HÀNG `DR-NNN`.** Gate `/approve-document` (`doc_review`) đọc file này:
> - Thiếu file → review chưa chạy → **chặn approve** (phải chạy `review-document` no-arg trước).
> - Còn row `severity ∈ {BLOCKER, MAJOR}` + `status` chưa đóng → **chặn approve** (ép vá gap).
> - Mọi gap đóng (`resolved`/`accepted`/`wontfix`) hoặc chỉ MINOR open → **pass**.
>
> Vá gap qua `review-document "<feedback>"` (revision mode) hoặc lùi `domain-po`·`domain-ba` author bổ sung (→ `domain-approve` → `domain-translate`); sau khi sửa, set `status=resolved`.
> **Luôn ghi file kể cả KHÔNG có gap** — để bảng rỗng (chỉ header) để chứng minh review đã chạy.

## Severity
- **BLOCKER** — thiếu năng lực nền sản phẩm bắt buộc (vd auth/đăng nhập/cấp token, phân quyền, multi-tenant) · mâu thuẫn làm doc không build được.
- **MAJOR** — AC `Must` không testable · cross-ref gãy · mâu thuẫn cross-doc đáng kể.
- **MINOR** — thiếu sót nhỏ, không chặn (typo, ví dụ BR thiếu, wording).

## Loại gap soi (lens — xem skill `business-analysis` §Coverage & gap analysis)
1. **Độ phủ năng lực** — `capability-map` + nhu cầu persona + journey → mọi năng lực có ≥1 FEAT phủ; năng lực nền đương nhiên cần mà KHÔNG có FEAT = BLOCKER.
2. **Mâu thuẫn cross-doc** — FEAT vs BR, AC vs api/data-model, HLD vs PROJECT scope, MATRIX vs BOUNDARY-MAP.
3. **AC testable** — Cho/Khi/Thì đo được, gồm non-happy-path.
4. **Cross-ref integrity** — epic↔feat↔BR↔journey↔persona không dangling.
5. **Câu hỏi cho Author chưa chốt** — còn `## Câu hỏi cho Author` / TODO chưa trả lời.

| finding | severity | concern | file | status |
|---------|----------|---------|------|--------|
| DR-001 | BLOCKER | Capability `auth` (capability-map §1) + nhu cầu mọi persona "đăng nhập" KHÔNG có FEAT phủ — thiếu luồng login/cấp token | docs/discovery/capability-map.md | open |
