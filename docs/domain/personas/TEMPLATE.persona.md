---
type: domain-artifact
artifact_kind: persona
id: "PERSONA-{{PREFIX}}-{{NNN}}"
status: "DRAFT | REVIEW | APPROVED"
version: 1
tier: T2
owner_authority: business
persona_pool_ref: "docs/discovery/persona-pool.md#{{persona-row-anchor}}"
source: domain-author
last_reviewed: "{{YYYY-MM-DD}}"
---

# PERSONA-{{PREFIX}}-{{NNN}} — {{Tên persona}}

> **Persona** (lớp BUSINESS) = chân dung người dùng đại diện. Nhân khẩu, vai trò, mục tiêu, nỗi đau, kênh ưa dùng. KÝ (`status: APPROVED`) → eng persona ở `docs/architecture/personas/`.

---

## 1. Hồ sơ cơ bản
| Aspect | Value |
|---|---|
| Tên đại diện | {{...}} |
| Vai trò công việc | {{...}} |
| Độ tuổi · trình độ công nghệ | {{...}} |
| Quy mô · khu vực | {{...}} |

## 2. Mục tiêu (goals) — 3-5
- {{...}}

## 3. Nỗi đau (pain points) — 3-5
- {{...}}

## 4. Kênh ưa dùng
| Kênh | Mức độ | Khi nào |
|---|---|---|
| {{Web/Mobile/Email/SMS}} | {{Cao/TB/Thấp}} | {{...}} |

## 5. Quote mẫu
> "{{câu nói thật/tổng hợp của persona}}"

## 6. Workflow điển hình hàng ngày
{{1 ngày làm việc — context để tính năng fit vào đâu.}}

## 7. Anti-persona (KHÔNG phải target)
> Làm rõ persona này KHÔNG bao gồm ai.
- {{KHÔNG bao gồm: ...}}

## 8. Câu hỏi cần Business Authority xác nhận
> **Author HỎI NGAY sau khi viết** (AskUserQuestion) — KHÔNG để treo.
- [ ] {{Phân biệt theo quy mô / tech-savvy / ngôn ngữ ...?}}

## 9. References
- Persona pool (D1): `docs/discovery/persona-pool.md`
- Journeys: `docs/domain/journeys/JOURNEY-*.md`
- Features: `docs/domain/feat/FEAT-*.md`

## 10. Change log
| Date | Status | Author | Description |
|---|---|---|---|
| {{YYYY-MM-DD}} | DRAFT | {{BA}} | Initial từ persona-pool D1 |
| {{YYYY-MM-DD}} | APPROVED | Business Authority | KÝ (domain-approve) |
