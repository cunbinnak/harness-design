---
type: inventory
artifact_kind: boundary-map
status: ACTIVE
tier: T0
owner_authority: Architecture Authority
last_reviewed: "{{DATE}}"
---

# BOUNDARY-MAP — {{PROJECT_NAME}}

> Điền NGẮN GỌN: ưu tiên bảng/bullet, không văn xuôi thừa, không lặp. Doc này agent downstream đọc nhiều lần — tiết kiệm context.

> Inventory mọi backend boundary + web experience + mobile experience. Authored ở D3 (charter-author) từ aggregate D2 (`ES-*.md §5`). Updated qua `/apply-cr` sau DISCOVERED.
> `id` cột đầu (backtick) = tên target, khớp folder `boundaries/{id}/CHARTER.md` (BE) + `services/{prefix-id}/` ở DEV. `service_prefix` = `{{prefix}}` (chốt ở D3).
> Gate D3 (boundary): ≥1 row non-placeholder across §1/§2/§3 · mỗi target BE có folder + `CHARTER.md` §1 Mission thật.
> Status: `PROPOSED` (D3) → `DESIGNING` → `ACTIVE` → `MAINTENANCE` → `ARCHIVED`.

---

## 1. Backend boundaries

> Mỗi boundary = 1 service repo (`services/{prefix-id}/`). Owned data = entity boundary này write-authority (không overlap — verify chéo). 1 aggregate ≈ 1 boundary.

| Boundary | Mission (1-line) | Owned data (entities) | Primary domain (ES) | Consumes | Wave | Status |
|---|---|---|---|---|---|---|
| `{{boundary-id}}` | {{1 câu: tồn tại để làm gì}} | `{{Entity1}}`, `{{Entity2}}` | {{ES-domain}} | {{boundary / external}} | {{W1}} | PROPOSED |
| `{{boundary-id}}` | {{...}} | `{{...}}` | {{...}} | {{...}} | {{W2}} | PROPOSED |

## 2. Web experiences

> kind=web. Persona pool = ai dùng. Capabilities exposed = capability realize ở UI. Data-layer mặc định REST gọi thẳng boundary API (BFF optional — §4).

| Experience | Persona pool | Capabilities exposed | Consumes boundaries | Wave | Status |
|---|---|---|---|---|---|
| `{{experience-id}}` | {{P1, P2}} | {{capability list}} | {{boundary-id, …}} | {{W1}} | PROPOSED |
| `{{experience-id}}` | {{...}} | {{...}} | {{...}} | {{W2}} | PROPOSED |

## 3. Mobile experiences

> kind=mobile. Để trống/`DEFERRED` nếu web-first. Row có target vẫn cần `id` backtick.

| Experience | Platform | Persona pool | Capabilities exposed | Wave | Status |
|---|---|---|---|---|---|
| `{{mobile-id}}` | {{iOS+Android / Flutter}} | {{P1}} | {{...}} | {{W3}} | PROPOSED |

> Defer toàn bộ mobile: 1 row placeholder `_TBD — defer (web-first)_` (gate cần ≥1 row non-placeholder tổng across §1/§2/§3 — §1 đã đủ).

## 4. BFF (Backend-for-Frontend) — nếu có

> Optional. Chỉ thêm khi web/mobile cần aggregation cross-boundary phức tạp (đánh giá ở DESIGN). Mặc định gọi thẳng boundary REST.

| BFF | Aggregates from | Serves to | Wave | Status |
|---|---|---|---|---|
| `{{bff-id}}` hoặc `none-rest-default` | {{boundary list}} | {{experience list}} | {{W?}} | {{PROPOSED / n/a}} |

---

## 5. Dependency overview (tuỳ chọn)

> Phụ thuộc giữa target (định hướng wave-sequencing ở PLAN).

| Target | Depends on | Loại (sync API / event / read-model) |
|---|---|---|
| `{{boundary-id}}` | `{{other-boundary}}` | {{read-model / event}} |

---

## 6. Adding boundary/experience after DISCOVERED

> Sau REVIEW, BOUNDARY-MAP = baseline. Thêm/bớt target phải qua `/apply-cr` + `/review-document` approve (append row + ADR ref, không sửa lén). Xem CLAUDE.md §NON-NEGOTIABLES (5).

---

## 7. Change log

| Date | Wave | Change | DECISION-REF |
|---|---|---|---|
| {{DATE}} | D3 (pending) | Inventory created | — |
