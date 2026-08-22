---
type: domain-artifact
artifact_kind: user-journey
id: "JOURNEY-{{PREFIX}}-{{NNN}}"
status: "DRAFT | REVIEW | APPROVED"
version: 1
tier: T2
owner_authority: business
persona_ref: "PERSONA-{{PREFIX}}-{{NNN}}"
related_capabilities: ["CAP-{{NNN}}"]
related_boundary_hint: "{{boundary hoặc TBD}}"
related_experience_hint: "{{web/mobile-experience hoặc TBD}}"
source: domain-author
last_reviewed: "{{YYYY-MM-DD}}"
---

# JOURNEY-{{PREFIX}}-{{NNN}} — {{Tiêu đề hành trình}}

> **User journey** (lớp BUSINESS) = tuần tự persona đi từ bối cảnh → kết quả, góc nhìn NGHIỆP VỤ. KHÔNG implementation (endpoint/API/component/layer). KÝ (`status: APPROVED`) → eng journey ở `docs/architecture/journeys/`.

---

## 1. Bối cảnh + tình huống kích hoạt
{{2-3 câu: persona ở đâu, làm gì, sự kiện gì khởi động.}}

## 2. Người dùng + động cơ
| Aspect | Value |
|---|---|
| Persona chính | {{link docs/domain/personas/}} |
| Động cơ | {{muốn gì, vì sao}} |
| Tần suất · khẩn cấp | {{...}} |

## 3. Các bước (hành động — kỳ vọng — cảm xúc)
| Bước | Hành động persona | Kỳ vọng hệ thống | Cảm xúc/lo ngại |
|---|---|---|---|
| 1 | {{...}} | {{...}} | {{...}} |
> Từ ngữ nghiệp vụ. KHÔNG "gọi endpoint", "render component".

## 4. Điểm chạm (touchpoints)
| Bước | Kênh | Ghi chú |
|---|---|---|
| 1-N | {{Web/Mobile/Email}} | {{...}} |

## 5. Tiêu chí thành công nghiệp vụ
- {{outcome nghiệp vụ, KHÔNG metric kỹ thuật}}

## 6. Tình huống lỗi (business error scenarios)
| Tình huống | Persona thấy gì | Làm gì tiếp |
|---|---|---|
| {{...}} | {{thông báo nghiệp vụ}} | {{...}} |
> KHÔNG "HTTP 409/5xx/timeout".

## 7. Câu hỏi cần Business Authority xác nhận
> **Author HỎI NGAY sau khi viết** (AskUserQuestion) — KHÔNG để treo.
- [ ] {{Giới hạn / quyền / điều kiện ...?}}

## 8. References
- Persona: `docs/domain/personas/{{PERSONA-XXX-NNN}}.md`
- Capability (D1): `docs/discovery/capability-map.md` (CAP-{{NNN}})
- Event storming (D2): `docs/discovery/event-storming/ES-{{domain}}.md`
- Features: `docs/domain/feat/FEAT-{{PREFIX}}-*.md`

## 9. Change log
| Date | Status | Author | Description |
|---|---|---|---|
| {{YYYY-MM-DD}} | DRAFT | {{PO/BA}} | Initial draft |
| {{YYYY-MM-DD}} | APPROVED | Business Authority | KÝ (domain-approve) |
