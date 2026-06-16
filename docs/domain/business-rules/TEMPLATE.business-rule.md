---
type: domain-artifact
artifact_kind: business-rule
id: "BR-{{PREFIX}}-{{NNN}}"
status: "DRAFT | REVIEW | APPROVED"
version: 1
tier: T2
owner_authority: business
domain_area: "{{payment | onboarding | billing | ...}}"
severity: "CORNERSTONE | NORMAL"
related_journeys: ["JOURNEY-{{PREFIX}}-{{NNN}}"]
related_features: ["FEAT-{{PREFIX}}-{{NNN}}"]
source: domain-author
last_reviewed: "{{YYYY-MM-DD}}"
---

# BR-{{PREFIX}}-{{NNN}} — {{Phát biểu ngắn quy tắc}}

> **Business rule** (lớp BUSINESS) = quy tắc nghiệp vụ MUST tuân thủ. Ngôn ngữ nghiệp vụ thuần — KHÔNG ghi enforcement layer (domain/API/DB); `/domain-translate` để `enforcement_location: TBD (DESIGN)` cho engineer điền. KÝ (`status: APPROVED`) → eng BR ở `docs/architecture/business-rules/`.
>
> Severity: `CORNERSTONE` = vi phạm thì hệ thống KHÔNG được tiếp tục · `NORMAL` = warn, có thể override theo business case.

---

## 1. Phát biểu quy tắc
{{1 câu rõ, ngôn ngữ nghiệp vụ.}}

## 2. Lý do tồn tại (reference nguồn — KHÔNG "best practice")
- [ ] Quy định pháp lý — {{Luật/Nghị định}}
- [ ] Quy tắc nội bộ — {{Policy doc}}
- [ ] Yêu cầu đối tác — {{contract}}
- [ ] Quyết định nghiệp vụ — {{decision-log row}}

## 3. Khi nào áp dụng (trigger nghiệp vụ)
{{Tình huống nghiệp vụ kích hoạt. KHÔNG "Khi gọi POST /...".}}

## 4. Ngoại lệ
{{Trường hợp KHÔNG áp dụng / override.}}

## 5. Hệ quả khi vi phạm
{{Persona thấy gì (thông báo nghiệp vụ). KHÔNG "trả 4xx / throw Exception".}}

## 6. Ví dụ cụ thể (≥2 — bắt buộc, QC seed test)
### Ví dụ 1 — Happy path
{{Số liệu + kết quả mong đợi.}}
### Ví dụ 2 — Vi phạm
{{Số liệu vi phạm + persona thấy gì.}}
### Ví dụ 3 — Edge (optional)

## 7. Câu hỏi cần Business Authority xác nhận
> **Author HỎI NGAY sau khi viết** (AskUserQuestion) — KHÔNG để treo.
- [ ] {{Áp dụng mọi persona hay chỉ ...?}}
- [ ] {{Có ngoại lệ VIP không?}}

## 8. References
- Journey: `docs/domain/journeys/JOURNEY-{{PREFIX}}-{{NNN}}.md`
- Feature dùng rule: `docs/domain/feat/FEAT-{{PREFIX}}-{{NNN}}.md`
- Hot-spot event storming: `docs/discovery/event-storming/ES-{{domain}}.md`

## 9. Change log
| Date | Status | Author | Description |
|---|---|---|---|
| {{YYYY-MM-DD}} | DRAFT | {{BA}} | Initial draft |
| {{YYYY-MM-DD}} | APPROVED | Business Authority | KÝ (/domain-approve) |
