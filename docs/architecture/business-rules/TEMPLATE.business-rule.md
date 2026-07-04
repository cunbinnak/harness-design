---
type: domain-artifact
artifact_kind: business-rule
id: "BR-{{PREFIX}}-{{NNN}}"
status: "DRAFT | REVIEW | APPROVED"
version: 1
tier: T2
owner_authority: business
owner: "{{người chịu trách nhiệm rule — single-person: chính bạn}}"
domain_area: "{{payment | onboarding | billing | ordering | customer-care}}"
rule_type: "validation | calculation | constraint | authorization | lifecycle | rate-limit"
severity: "CORNERSTONE | NORMAL"
source_type: "legal | company-policy | partner-contract | business-decision"
related_journeys: ["JOURNEY-{{PREFIX}}-{{NNN}}"]
related_features: ["FEAT-{{PREFIX}}-{{NNN}}"]   # ≥1 FEAT (gate planning_lint, trỏ file thật)
enforcement_location: "TBD (DESIGN)"   # TODO engineer — DESIGN điền NƠI enforce (vd "api: scheduling POST /bookings — 422 ROOM_TIME_CONFLICT" / "data-model: unique constraint" / "event handler"); gate todo_resolved chặn /design-end khi còn TBD
error_code: "TBD (DESIGN)"   # map vào Domain error catalog api §4.2 (nếu rule lộ qua API)
source: "docs/domain/business-rules/BR-{{PREFIX}}-{{NNN}}.md"   # file business nguồn (translator điền — gate translation_parity @domain-end đối chiếu 1-1)
domain_source_id: "BR-{{PREFIX}}-{{NNN}}"
last_reviewed: "{{YYYY-MM-DD}}"
---

> **LỚP ENGINEERING** — bản dịch từ business (`source`) do `/domain-translate` sinh, KHÔNG author tay. Khác bản business: `enforcement_location` + `error_code` (TODO engineer — BR không có nơi enforce = rule không bao giờ được code, gate `todo_resolved` đòi DESIGN điền). Sửa NGHIỆP VỤ → lùi `/domain-ba` → re-ký → re-dịch. Điền NGẮN GỌN: ưu tiên bảng/bullet.

> Quy tắc nghiệp vụ MUST tuân thủ, dùng chung bởi ≥1 feature. Ngôn ngữ nghiệp vụ THUẦN — KHÔNG ghi nơi enforce (layer/API/DB), không endpoint/4xx/throw/tên bảng. severity: CORNERSTONE=vi phạm thì dừng, bắt buộc test, không override mặc định; NORMAL=cảnh báo, override được. rule_type định hướng cách viết (validation/calculation/constraint/authorization/lifecycle/rate-limit). APPROVED khi: ≥1 related_features trỏ file THẬT; phát biểu duy nhất không nhập nhằng; ≥2 ví dụ có số liệu (1 happy + 1 vi phạm); liệt kê ngoại lệ; source_type + rationale cụ thể.

# BR-{{PREFIX}}-{{NNN}} — {{Phát biểu ngắn quy tắc}}

## 1. Phát biểu quy tắc

{{1 câu rõ ràng, ngôn ngữ nghiệp vụ. Một quy tắc = một phát biểu — cần "và/hoặc" nhiều logic độc lập thì tách BR.}}

## 2. Lý do tồn tại (rationale)

{{1-2 đoạn nguồn gốc, gắn source_type, không "vì best practice".}}

Nguồn (đánh dấu đúng `source_type`):
- [ ] `legal` — tham chiếu: {{Luật/Nghị định + điều khoản}}
- [ ] `company-policy` — tham chiếu: {{policy doc + mục}}
- [ ] `partner-contract` — tham chiếu: {{hợp đồng + điều khoản}}
- [ ] `business-decision` — tham chiếu: {{ai quyết, khi nào, vì sao}}

## 3. Khi nào áp dụng (trigger)

{{Tình huống nghiệp vụ kích hoạt. Từ nghiệp vụ — KHÔNG "khi gọi POST /refunds".}}

## 4. Logic quy tắc (điều kiện → kết quả)

> Bảng quyết định để không bỏ sót nhánh (validation/constraint/authorization/lifecycle). rule_type=calculation thì dùng §4b.

| Điều kiện nghiệp vụ | Kết quả mong đợi |
|---|---|
| {{Số tiền hoàn ≤ số dư còn lại}} | {{Chấp nhận}} |
| {{Số tiền hoàn > số dư còn lại}} | {{Từ chối + báo số tối đa}} |
| {{Số dư = 0}} | {{Từ chối + "đã hoàn xong"}} |

### 4b. Công thức (chỉ rule_type = calculation)

{{Công thức bằng đại lượng nghiệp vụ, vd "Số dư có thể hoàn = Giá trị đơn − Tổng đã hoàn". Không tên cột/bảng.}}

## 5. Ngoại lệ

{{Trường hợp không áp dụng / có override. Không có thì ghi "Không có ngoại lệ".}}

## 6. Hệ quả khi vi phạm

{{Hệ quả nghiệp vụ + persona THẤY gì. Không "trả 4xx"/"throw Exception".}}

## 7. Ví dụ cụ thể (≥2 — BẮT BUỘC, QC seed test case)

> Mỗi ví dụ có số liệu + kết quả. Tối thiểu 1 happy + 1 vi phạm; nên thêm edge case.

- **Ví dụ 1 (happy):** {{số liệu → CHẤP NHẬN. Vd: đơn 1.000.000đ, đã hoàn 200.000đ, hoàn thêm 500.000đ → CHẤP NHẬN}}
- **Ví dụ 2 (vi phạm):** {{số liệu vi phạm + persona thấy gì. Vd: đã hoàn 800.000đ, hoàn thêm 500.000đ → TỪ CHỐI "tối đa 200.000đ"}}
- **Ví dụ 3 (edge, khuyến nghị):** {{biên: 0đ / đã hoàn hết / đúng giới hạn}}

## 8. Câu hỏi cần Business Authority xác nhận

- [ ] {{Áp dụng cho mọi persona hay chỉ Merchant Admin?}}
- [ ] {{Có ngoại lệ cho khách VIP?}}

## 9. References

> ≥1 feature ở `related_features` trỏ file THẬT (planning_lint).

- Features dùng rule: `docs/architecture/feat/FEAT-{{PREFIX}}-*.md`
- Journeys liên quan: `docs/architecture/journeys/JOURNEY-{{PREFIX}}-{{NNN}}.md`
- Capability (D1): `docs/discovery/capability-map.md` ({{CAP-NNN}})

## 10. Change log

| Date | Version | Status | Author | Thay đổi |
|---|---|---|---|---|
| {{YYYY-MM-DD}} | 1 | DRAFT | {{tác giả}} | Initial |
| {{YYYY-MM-DD}} | 1 | APPROVED | Business Authority | Sign-off |
