---
type: domain-artifact
artifact_kind: persona
id: "PERSONA-{{PREFIX}}-{{NNN}}"
status: "DRAFT | REVIEW | APPROVED"
version: 1
tier: T2
owner_authority: business
owner: "{{người chịu trách nhiệm persona — single-person: chính bạn}}"
persona_kind: "primary | secondary | beneficiary | anti-persona"
persona_pool_ref: "docs/discovery/persona-pool.md#{{persona-row-anchor}}"   # gốc D1
source: "docs/domain/personas/PERSONA-{{PREFIX}}-{{NNN}}.md"   # file business nguồn (translator điền — gate translation_parity @domain-end đối chiếu 1-1)
domain_source_id: "PERSONA-{{PREFIX}}-{{NNN}}"
last_reviewed: "{{YYYY-MM-DD}}"
---

> Điền NGẮN GỌN: ưu tiên bảng/bullet, không văn xuôi thừa, không lặp. Doc này agent downstream đọc nhiều lần — tiết kiệm context.

> Chân dung người dùng đại diện dựa trên nghiên cứu thực tế (không bịa). KHÔNG tech stack/trình duyệt trừ khi là constraint nghiệp vụ thật. Quality bar: hồ sơ + ≥3 goal + ≥3 pain point cụ thể (không generic); có JTBD; có anti-persona; liên kết ngược persona-pool D1.

# PERSONA-{{PREFIX}}-{{NNN}} — {{Tên persona}}

## 1. Hồ sơ cơ bản

| Aspect | Value |
|---|---|
| Tên đại diện | {{Anh Minh / Chị Lan}} |
| Vai trò công việc | {{Merchant Admin cửa hàng F&B}} |
| Độ tuổi | {{30-45}} |
| Trình độ công nghệ | {{Cơ bản — smartphone, email}} |
| Quy mô / bối cảnh | {{1-3 chi nhánh, 5-20 nhân viên}} |
| Khu vực | {{Đô thị / nông thôn}} |
| persona_kind | {{primary / secondary / beneficiary / anti-persona}} |

## 2. Mục tiêu (goals) + Jobs-to-be-done

> Goal = muốn đạt gì trong context sản phẩm (3-5). JTBD format: "Khi {{tình huống}}, tôi muốn {{động cơ}}, để {{kết quả}}".

Goals:
- {{Xử lý hoàn tiền nhanh để giữ uy tín}}
- {{Có dấu vết để giải trình với chủ doanh nghiệp}}
- {{Giảm thời gian liên hệ qua email/điện thoại}}

Jobs-to-be-done:
- {{Khi khách than phiền cần hoàn, tôi muốn xử lý xong ngay tại quầy, để khách không phải chờ.}}

## 3. Nỗi đau (pain points)

> 3-5 pain point CỤ THỂ (định lượng nếu có), tránh generic.

- {{Gửi email + chờ kế toán — 30+ phút/yêu cầu}}
- {{Khách hỏi không biết yêu cầu đang ở bước nào}}
- {{Sợ thao tác nhầm — hệ thống cũ không có "Hủy"}}

## 4. Động cơ ra quyết định (decision drivers)

| Thúc đẩy (motivator) | Cản trở (barrier) |
|---|---|
| {{Giữ khách, tránh đánh giá xấu}} | {{Sợ sai số tiền, bị quy trách nhiệm}} |
| {{Tiết kiệm thời gian cao điểm}} | {{Quy trình rườm rà}} |

## 5. Kênh ưa dùng + bối cảnh

| Kênh | Mức độ | Khi nào / bối cảnh |
|---|---|---|
| {{Web admin máy tính}} | {{Cao}} | {{Giờ hành chính ở văn phòng}} |
| {{App di động}} | {{Trung bình}} | {{Khi đi gặp khách}} |
| {{Email}} | {{Cao}} | {{Nhận thông báo + hồ sơ}} |

## 6. Khả năng tiếp cận / hạn chế (accessibility & constraints)

> Hạn chế nghiệp vụ thật ảnh hưởng thiết kế (không phải tech preference). Bỏ trống nếu không có.

- {{Thao tác một tay khi bê đồ — cần nút lớn}}
- {{Môi trường ồn/sáng chói — cần phản hồi rõ bằng hình}}

## 7. Quote mẫu

"{{Tôi chỉ muốn bấm vài nút là xong việc hoàn tiền, không nhập lại từ đầu. Khách giận sẵn mà bắt chờ thì mất khách.}}"

## 8. Workflow điển hình hàng ngày

> Context để PO/BA biết tính năng fit vào đâu + tần suất.

- {{8h: Mở web admin, xem dashboard đơn đêm qua}}
- {{9h-12h: Xử lý yêu cầu khách (gồm hoàn tiền)}}
- {{13h-17h: Quản lý kho, theo dõi chỉ số}}

→ {{Tính năng hoàn tiền ~2-5 lần/ngày, mỗi lần ≤ 5 phút là chấp nhận được.}}

## 9. Anti-persona (KHÔNG phải target user)

> BẮT BUỘC. Làm rõ KHÔNG bao gồm ai — chống nhồi yêu cầu nhóm ngoài phạm vi.

- {{KHÔNG gồm: kế toán chuyên trách (dùng hệ thống riêng)}}
- {{KHÔNG gồm: khách cuối (chỉ nhận xác nhận, không vào trang quản trị)}}

## 10. Câu hỏi cần Business Authority xác nhận

- [ ] {{Cần tách persona theo quy mô (SME vs Enterprise)?}}
- [ ] {{Mức thành thạo công nghệ ảnh hưởng UX thế nào?}}

## 11. References

- Persona-pool gốc (D1): `docs/discovery/persona-pool.md`
- Journeys persona thực hiện: `docs/architecture/journeys/JOURNEY-{{PREFIX}}-*.md`
- Features persona dùng: `docs/architecture/feat/FEAT-{{PREFIX}}-*.md`

## 12. Change log

| Date | Version | Status | Author | Thay đổi |
|---|---|---|---|---|
| {{YYYY-MM-DD}} | 1 | DRAFT | {{tác giả}} | Initial từ persona-pool D1 |
| {{YYYY-MM-DD}} | 1 | APPROVED | Business Authority | Sign-off |
