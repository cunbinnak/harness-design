---
type: domain-artifact
artifact_kind: feature-intent
id: "FEAT-{{PREFIX}}-{{NNN}}"
status: "DRAFT | REVIEW | APPROVED"
version: 1
tier: T2
owner_authority: business
journey_refs: ["JOURNEY-{{PREFIX}}-{{NNN}}"]
business_rule_refs: ["BR-{{PREFIX}}-{{NNN}}"]
persona_refs: ["PERSONA-{{PREFIX}}-{{NNN}}"]
epic_ref: "EP-{{PREFIX}}-{{NNN}}"
target_boundary_hint: "{{boundary name hoặc TBD}}"
target_experience_hint: "{{web-experience hoặc mobile-experience hoặc TBD}}"
has_ui_touchpoint: true
source: domain-author
last_reviewed: "{{YYYY-MM-DD}}"
---

# FEAT-{{PREFIX}}-{{NNN}} — {{Tên tính năng}}

> **Feature intent** (lớp BUSINESS) = ý định nghiệp vụ về 1 tính năng. KÝ (`status: APPROVED`) rồi `domain-translate` dịch sang ENG FEAT ở `docs/architecture/feat/` (backend + frontend nếu `has_ui_touchpoint=true`).
>
> AC viết theo BDD plain Vietnamese: Cho / Khi / Thì. KHÔNG ghi endpoint, contract path, error code, i18n key, tên class (jargon → gate `domain_no_jargon` chặn lúc ký).

---

## 1. Mục tiêu nghiệp vụ

{{1-2 câu: tính năng này giải quyết vấn đề gì cho persona?}}

---

## 2. Persona dùng tính năng

| Persona | Vai trò trong tính năng |
|---|---|
| {{PERSONA-XXX-001}} | {{Người chính dùng tính năng}} |

---

## 3. User story

**Là** {{persona}}, **tôi muốn** {{khả năng}}, **để** {{đạt được mục tiêu nghiệp vụ}}.

---

## 4. Tiêu chí chấp nhận (Acceptance Criteria)

> Mỗi AC theo BDD: **Cho** (tiền đề) / **Khi** (hành động) / **Thì** (kết quả). KHÔNG "endpoint/API/JSON/HTTP status/i18n key/component name". ≥4 AC (happy + validation + error + accessibility).

### AC-1: {{tên}}
**Cho** {{tiền đề}} · **Khi** {{hành động}} · **Thì** {{kết quả nghiệp vụ}}

### AC-2: Validation
**Cho** {{...}} · **Khi** {{input sai, xem BR-{{PREFIX}}-001}} · **Thì** {{thông báo lỗi nghiệp vụ}}

### AC-3: Happy path
### AC-4: Xử lý lỗi nghiệp vụ
### AC-5: Khả năng tiếp cận (a11y)
<!-- Thêm AC tùy nhu cầu. Mỗi AC testable, mô tả HÀNH VI nghiệp vụ. -->

---

## 5. Quy tắc liên quan

| Business Rule | Vai trò trong feature |
|---|---|
| [BR-{{PREFIX}}-001](../business-rules/BR-{{PREFIX}}-001.md) | {{...}} |

---

## 6. Ngoài phạm vi (QC dựa vào để biết KHÔNG test gì)

- {{... — feature riêng FEAT-XXX-NNN}}

---

## 7. Câu hỏi cần Business Authority xác nhận

> **Author HỎI NGAY sau khi viết** (AskUserQuestion) — KHÔNG để treo. Liệt kê hết câu mở.

- [ ] {{Có giới hạn N yêu cầu / đơn không?}}
- [ ] {{Lý do preset list hay free text?}}

---

## 8. References

- Epic: `docs/domain/epics/{{EP-PREFIX-NNN}}.md`
- Journey: `docs/domain/journeys/{{JOURNEY-PREFIX-NNN}}.md`
- Personas: `docs/domain/personas/{{PERSONA-XXX}}.md`
- Business rules: `docs/domain/business-rules/BR-*.md`

---

## 9. Change log

| Date | Status | Author | Description |
|---|---|---|---|
| {{YYYY-MM-DD}} | DRAFT | {{PO}} | Initial feature intent |
| {{YYYY-MM-DD}} | APPROVED | Business Authority | KÝ (domain-approve) — cho translate sang eng |
