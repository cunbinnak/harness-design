---
type: domain-artifact
artifact_kind: epic
id: "EP-{{PREFIX}}-{{NNN}}"
status: "DRAFT | REVIEW | APPROVED"
version: 1
tier: T2
owner_authority: business
target_capability: "CAP-{{NNN}}"
target_boundary_hint: "{{boundary name hoặc TBD}}"
target_experience_hint: "{{web/mobile-experience hoặc TBD}}"
feature_refs: ["FEAT-{{PREFIX}}-{{NNN}}"]
priority: "P0 | P1 | P2 | P3"
source: domain-author
last_reviewed: "{{YYYY-MM-DD}}"
---

# EP-{{PREFIX}}-{{NNN}} — {{Tên Epic}}

> **Epic** (lớp BUSINESS) = chủ đề lớn nhóm nhiều feature cùng business outcome cho 1 persona. KÝ (`status: APPROVED`) rồi `domain-translate` → eng epic ở `docs/architecture/epics/`. **`feature_refs` ≥2 FEAT** (ZIP planning-rules: <2 → granularity sai). Tên + nội dung KHÔNG từ kỹ thuật.

---

## 1. Vision

{{2-3 đoạn: persona nào, đạt được gì, vì sao quan trọng?}}

---

## 2. Persona impact

| Persona | Vai trò trong epic | Tác động chính |
|---|---|---|
| {{PERSONA-XXX-001}} | {{Primary user}} | {{...}} |

---

## 3. Success metrics nghiệp vụ

> Metric NGHIỆP VỤ — KHÔNG kỹ thuật (p99 latency...).

- {{Thời gian xử lý trung bình ≤ ...}}
- {{Tỉ lệ tự động hóa ≥ ...}}

---

## 4. MVP scope

| Feature | Mô tả ngắn | Priority | Notes |
|---|---|---|---|
| [FEAT-{{PREFIX}}-001](../feat/FEAT-{{PREFIX}}-001.md) | {{...}} | P0 | Bắt buộc |
| [FEAT-{{PREFIX}}-002](../feat/FEAT-{{PREFIX}}-002.md) | {{...}} | P0 | Bắt buộc |

---

## 5. Phasing gợi ý

| Phase | Features | Outcome |
|---|---|---|
| Phase 1 (MVP) | FEAT-001, FEAT-002 | {{...}} |
| Phase 2 | FEAT-003 | {{...}} |

---

## 6. Ngoài phạm vi epic

- {{... — Epic riêng EP-XXX-002}}

---

## 7. Câu hỏi cần Business Authority xác nhận

> **Author HỎI NGAY sau khi viết** (AskUserQuestion) — KHÔNG để treo.

- [ ] {{Threshold / SLA / phạm vi MVP đúng chưa?}}

---

## 8. References

- Capability: `docs/discovery/capability-map.md` (CAP-{{NNN}})
- Hypothesis: `docs/discovery/hypothesis-log.md` (H-{{NNN}})
- Personas: `docs/domain/personas/PERSONA-*.md`
- Features con: `docs/domain/feat/FEAT-{{PREFIX}}-*.md`

---

## 9. Change log

| Date | Status | Author | Description |
|---|---|---|---|
| {{YYYY-MM-DD}} | DRAFT | {{PO}} | Initial epic |
| {{YYYY-MM-DD}} | APPROVED | Business Authority | KÝ (domain-approve) |
