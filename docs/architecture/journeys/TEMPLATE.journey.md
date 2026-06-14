---
type: domain-artifact
artifact_kind: user-journey
id: "JOURNEY-{{PREFIX}}-{{NNN}}"
status: "DRAFT | REVIEW | APPROVED"
version: 1
tier: T2
owner_authority: business
owner: "{{người chịu trách nhiệm journey — single-person: chính bạn}}"
journey_type: "core | onboarding | recovery | administrative"
persona_refs: ["PERSONA-{{PREFIX}}-{{NNN}}"]   # persona thực hiện (đầu trùng persona chính), trỏ file thật
related_capabilities: ["CAP-{{NNN}}"]   # capability D1 journey hiện thực
related_boundary_hint: "{{FE boundary (kind web/mobile) hoặc TBD}}"
source: domain-author
last_reviewed: "{{YYYY-MM-DD}}"
---

> Điền NGẮN GỌN: ưu tiên bảng/bullet, không văn xuôi thừa, không lặp. Doc này agent downstream đọc nhiều lần — tiết kiệm context.

> Hành trình persona đi từ bối cảnh khởi đầu → kết quả, góc nhìn nghiệp vụ + cảm xúc. Ngôn ngữ NGHIỆP VỤ thuần — không endpoint/API/component/tên màn hình kỹ thuật/layer. Quality bar: ≥1 bước happy path đầy đủ (hành động–kỳ vọng–cảm xúc); có touchpoint mỗi giai đoạn; tiêu chí thành công NGHIỆP VỤ + ≥2 lỗi nghiệp vụ; persona_refs trỏ persona THẬT.

# JOURNEY-{{PREFIX}}-{{NNN}} — {{Tiêu đề hành trình}}

## 1. Bối cảnh + tình huống kích hoạt

{{2-3 câu: persona ở đâu, làm gì, sự kiện gì khởi động hành trình. Nêu áp lực/cảm xúc khởi điểm.}}

## 2. Người dùng + động cơ

> Persona chính trùng phần tử đầu `persona_refs`.

| Aspect | Value |
|---|---|
| Persona chính | {{PERSONA-XXX-NNN — link personas/}} |
| Persona phụ | {{...}} |
| Động cơ | {{Muốn gì? Vì sao quan trọng?}} |
| Tần suất | {{Hàng ngày / tuần / dịp đặc biệt}} |
| Khẩn cấp | {{Chờ được / ngay / phụ thuộc deadline khách}} |
| Cảm xúc khởi điểm | {{Bình thường / lo / bực / vội}} |

## 3. Tiền điều kiện (entry conditions)

- {{Persona đã đăng nhập, có quyền tại cửa hàng}}
- {{Đơn tồn tại, ở trạng thái cho thao tác}}

## 4. Các bước (hành động — kỳ vọng — cảm xúc)

> Cột "Kỳ vọng hệ thống" ở tầng nghiệp vụ (không "gọi endpoint"/"render component"). Nhóm theo Giai đoạn nếu journey dài.

| Bước | Giai đoạn | Hành động persona | Kỳ vọng hệ thống | Cảm xúc / lo ngại |
|---|---|---|---|---|
| 1 | {{Bắt đầu}} | {{Bấm "Hoàn tiền"}} | {{Hiện màn hình yêu cầu}} | {{Lo chọn nhầm đơn}} |
| 2 | {{Nhập liệu}} | {{Chọn đơn + nhập số tiền}} | {{Tự kiểm số dư, chặn nhập quá}} | {{An tâm vì có guard}} |
| 3 | {{Xác nhận}} | {{Bấm Xác nhận}} | {{Xử lý, hiện trạng thái chờ}} | {{Hồi hộp}} |
| 4 | {{Kết thúc}} | {{Đợi kết quả}} | {{Hiện chi tiết + "Đang chờ xử lý"}} | {{Yên tâm}} |

## 5. Điểm chạm (touchpoints)

> Chỉ kênh, KHÔNG tên component.

| Bước | Kênh | Ghi chú |
|---|---|---|
| {{1-4}} | {{Web admin}} | {{Máy tính ở văn phòng}} |
| {{Sau xác nhận}} | {{Email tự động}} | {{Xác nhận cho persona + khách}} |

## 6. Tiêu chí thành công nghiệp vụ

> Outcome nghiệp vụ, KHÔNG p99/throughput.

- {{Persona hoàn tất ≤ 2 phút}}
- {{Khách nhận xác nhận ≤ 5 phút}}
- {{Có dấu vết: ai xử lý, khi nào, lý do}}

## 7. Tình huống lỗi (business error scenarios)

> ≥2 tình huống. Ngôn ngữ nghiệp vụ — KHÔNG "HTTP 409"/"timeout".

| Tình huống | Persona thấy gì | Làm gì tiếp |
|---|---|---|
| {{Đơn đã hoàn 100%}} | {{"Đơn này đã hoàn xong"}} | {{Quay lại danh sách}} |
| {{Vượt số dư}} | {{"Tối đa X đồng"}} | {{Sửa số tiền}} |
| {{Đã có chargeback song song}} | {{"Không thể tự hoàn"}} | {{Liên hệ bộ phận thanh toán}} |

## 8. Kết quả + bước tiếp theo (post-conditions)

- {{Yêu cầu hoàn ở trạng thái "Đang chờ xử lý"}}
- {{Khách đã nhận xác nhận + biết thời gian dự kiến}}

## 9. Câu hỏi cần Business Authority xác nhận

> Liệt kê hết — assumption silent = risk drift.

- [ ] {{Giới hạn số lần hoàn / đơn?}}
- [ ] {{Persona nào được hoàn > X triệu (cần duyệt)?}}

## 10. References

- Persona: `docs/architecture/personas/PERSONA-{{PREFIX}}-{{NNN}}.md`
- Capability (D1): `docs/discovery/capability-map.md` ({{CAP-NNN}})
- Features hiện thực journey: `docs/architecture/feat/FEAT-{{PREFIX}}-*.md` (FEAT trỏ về qua `journey_refs`)

## 11. Change log

| Date | Version | Status | Author | Thay đổi |
|---|---|---|---|---|
| {{YYYY-MM-DD}} | 1 | DRAFT | {{tác giả}} | Initial |
| {{YYYY-MM-DD}} | 1 | APPROVED | Business Authority | Sign-off |
