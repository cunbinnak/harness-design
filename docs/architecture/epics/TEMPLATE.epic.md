---
type: domain-artifact
artifact_kind: epic
id: "EP-{{PREFIX}}-{{NNN}}"
status: "DRAFT | REVIEW | APPROVED"
version: 1
tier: T2
owner_authority: business
priority: "P0 | P1 | P2 | P3"
owner: "{{người chịu trách nhiệm epic — single-person: chính bạn}}"
target_capability: "{{CAP-NNN hoặc tên capability từ capability-map}}"
target_persona: "PERSONA-{{PREFIX}}-{{NNN}}"   # persona CHÍNH epic phục vụ
target_boundary_hint: "{{boundary name (kind backend/web/mobile) hoặc TBD}}"   # gợi ý, DESIGN/PLAN chốt
hypothesis_refs: ["H-{{NNN}}"]   # giả thuyết D0 epic kiểm chứng
feature_refs: ["FEAT-{{PREFIX}}-{{NNN}}", "FEAT-{{PREFIX}}-{{NNN}}"]   # ≥2 FEAT (gate planning_lint), trỏ file thật
source: domain-author
last_reviewed: "{{YYYY-MM-DD}}"
---

> Điền NGẮN GỌN: ưu tiên bảng/bullet, không văn xuôi thừa, không lặp. Doc này agent downstream đọc nhiều lần — tiết kiệm context.

> Ngôn ngữ NGHIỆP VỤ thuần — không tech (endpoint/API/SQL/cache/service/Kafka/layer/component). Dùng "thao tác"/"luồng nghiệp vụ"/"module nghiệp vụ". APPROVED khi: vision đủ persona-outcome-vì sao; ≥2 FEAT; metric nghiệp vụ đo được (không p99/latency); có "Ngoài phạm vi"; mọi ref trỏ file thật.

# EP-{{PREFIX}}-{{NNN}} — {{Tên Epic}}

## 1. Vision

{{2-3 đoạn: (a) persona nào, (b) outcome nghiệp vụ gì, (c) vì sao cấp thiết. Nêu status đau trước, rồi thay đổi epic mang lại.}}

## 2. Persona impact

> Persona chính trùng `target_persona`. Liệt kê cả persona phụ + beneficiary (hưởng lợi gián tiếp).

| Persona | Vai trò trong epic | Tác động chính (outcome nghiệp vụ) |
|---|---|---|
| {{PERSONA-MRC-001 — Merchant Admin}} | {{Primary — tạo + theo dõi yêu cầu}} | {{Tiết kiệm ~25 phút/yêu cầu}} |
| {{PERSONA-CUS-001 — Khách cuối}} | {{Beneficiary — không thao tác}} | {{Nhận tiền nhanh hơn}} |

## 3. Success metrics nghiệp vụ

> Metric NGHIỆP VỤ (không p99/throughput/error rate). Mỗi metric: hướng + mốc (hoặc "chốt sau baseline") + cách đo.

| Metric nghiệp vụ | Baseline | Mục tiêu | Cách đo |
|---|---|---|---|
| {{Thời gian nhận yêu cầu → khách xác nhận}} | {{~30 phút}} | {{≤ 5 phút}} | {{Log thời điểm tạo vs xác nhận}} |
| {{Tỉ lệ xử lý tự động}} | {{0%}} | {{≥ 80%}} | {{Đếm yêu cầu không có bước manual}} |

## 4. MVP scope

> Feature tối thiểu để epic deliver value. Mỗi dòng link FEAT THẬT (planning_lint chặn dangling). Tối thiểu 2 FEAT.

| Feature | Mô tả ngắn (nghiệp vụ) | Priority | Lý do MVP / hoãn |
|---|---|---|---|
| [FEAT-{{PREFIX}}-001](../feat/FEAT-{{PREFIX}}-001.md) | {{Tạo yêu cầu hoàn tiền}} | P0 | {{Core value}} |
| [FEAT-{{PREFIX}}-002](../feat/FEAT-{{PREFIX}}-002.md) | {{Xem chi tiết + lịch sử}} | P0 | {{Khép vòng theo dõi}} |

## 5. Phasing gợi ý

> Gợi ý thứ tự release. PLAN (`/plan`) chốt thật qua WAVE-SEQUENCE.

| Phase | Features | Outcome |
|---|---|---|
| Phase 1 (MVP) | {{FEAT-001, FEAT-002}} | {{Tạo + theo dõi cơ bản}} |
| Phase 2 | {{FEAT-003}} | {{Tự động hoá xác nhận}} |

## 6. Ngoài phạm vi epic

> BẮT BUỘC. Mỗi mục nói rõ "thuộc đâu" (epic khác / phase sau / ngoài dự án).

- {{Hoàn tiền tự động theo lịch — Epic riêng}}
- {{Báo cáo analytics — domain reporting}}

## 7. Phụ thuộc + rủi ro nghiệp vụ

| Loại | Mô tả | Mức độ | Giảm thiểu |
|---|---|---|---|
| Phụ thuộc | {{Cần dữ liệu đơn đã thanh toán từ domain khác}} | {{Cao}} | {{Xác nhận domain nguồn sẵn sàng}} |
| Rủi ro | {{Ngưỡng duyệt sai → hoàn nhầm}} | {{Cao}} | {{Authority chốt ngưỡng trước APPROVED}} |

## 8. Câu hỏi cần Business Authority xác nhận

> Liệt kê HẾT điểm chưa chắc, kèm phương án mặc định để Authority chỉ xác nhận/bác.

- [ ] {{Ngưỡng duyệt đúng chưa? (mặc định: 5 triệu)}}
- [ ] {{Có cam kết thời gian khách nhận tiền không?}}

## 9. References

- Capability (D1): `docs/discovery/capability-map.md` ({{CAP-NNN}})
- Hypothesis (D0): `docs/discovery/hypothesis-log.md` ({{H-NNN}})
- Personas: `docs/architecture/personas/PERSONA-{{PREFIX}}-*.md`
- Features con: `docs/architecture/feat/FEAT-{{PREFIX}}-*.md`

## 10. Change log

| Date | Version | Status | Author | Thay đổi |
|---|---|---|---|---|
| {{YYYY-MM-DD}} | 1 | DRAFT | {{tác giả}} | Initial |
| {{YYYY-MM-DD}} | 1 | APPROVED | Business Authority | Sign-off |
