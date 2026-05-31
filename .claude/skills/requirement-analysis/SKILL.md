---
name: requirement-analysis
description: Intake step 1 (requirement-analyst / product owner) — mô tả project → PRD trong PROJECT.md (scope/NFR số/security+compliance/success metrics) + FEAT draft (user story + Gherkin AC) + service_prefix.
---

# Requirement Analysis Skill

## Khi load
`/intake-requirement` **step 1** — agent `requirement-analyst-agent` (vai **Product Owner**): biến goal/business thành **product requirement** rõ, không mơ hồ, team kỹ thuật làm được ngay.
Input: **mô tả project** user truyền (`$ARGUMENTS`); amendment → đọc CR `change_summary`.

## Deliverable của step 1 (đúng cái command verify)
1. **`docs/architecture/PROJECT.md`** — tối thiểu (verify): **scope** (in/out), **NFR**, **glossary**. Điền đầy theo `TEMPLATE.project.md`:
   - **Vision / one-liner** + vấn đề giải quyết + persona + bên liên quan.
   - **Scope in/out** (out-of-scope nêu **rõ ràng** — chống scope creep).
   - **NFR có SỐ cụ thể**: performance (vd p99 < 300ms), availability (vd ≥ 99.5%), scalability (N req/s @ M users), security, observability, coverage.
   - **Security & compliance**: auth model (JWT/OAuth2), data classification (PII/nhạy cảm), ràng buộc pháp lý theo domain (PDPA/GDPR/PCI-DSS/HIPAA nếu áp dụng).
   - **Integration (cấp dự án)**: hệ thống ngoài phải tích hợp (payment gateway, SMS, email…) — *liệt kê; INTEG chi tiết để step 3.*
   - **Success metrics / KPI** đo được (vd: 90% đơn xử lý < 5s; churn < X%).
   - Ràng buộc (tech stack bắt buộc, timeline/team) + **Open questions**.
2. **`docs/architecture/feat/FEAT-*.md` draft** (≥ 1) — mỗi capability 1 file: tiêu đề, mục tiêu, scope (in/out), ưu tiên (Must/Should/Could), **user story + AC sơ bộ Gherkin** (Given/When/Then). *(AC testable + BR + boundaries_suggested để step 2 — business-analysis refine.)*
3. **Chốt `project.service_prefix`** — prefix ngắn kebab cho repo polyrepo (vd `crm-hdpe`) → `services/{prefix}-{boundary}/`.

> Đây là output `build_prompt.py` step 1. Đừng làm thay step 2 (đừng cố hoàn chỉnh AC testable / BR / boundaries).

## Bước 0 — Research (chỉ khi domain phức tạp / chưa rõ + có WebSearch)
- Tính năng tiêu chuẩn của loại sản phẩm này trong industry.
- NFR thường gặp (performance/availability/compliance) + benchmark sản phẩm tương đương.
- Regulatory bắt buộc theo domain (PDPA/GDPR/PCI-DSS/HIPAA). KHÔNG bịa nguồn.

## Phương pháp (PRD dimensions)
1. **Phân loại yêu cầu**: functional (→ FEAT) vs non-functional (→ NFR).
2. **Functional → FEAT**: tách capability lớn thành FEAT; mỗi FEAT có user story + Gherkin AC draft + ưu tiên.
3. **NFR có số**: mỗi attribute 1 target đo được (không "nhanh", "ổn định" chung chung).
4. **Security & compliance**: auth model + data classification + regulatory.
5. **Integration**: liệt kê external system phải tích hợp.
6. **Success metrics**: KPI đo được cấp dự án.
7. **Scope & glossary**: out-of-scope rõ; thuật ngữ domain định nghĩa thống nhất; chỗ chưa rõ → Open questions.

## Flow step 1 (theo command)
- Gọi không có mô tả → hỏi user "Mô tả project? (vd CRM cho công ty X, N module…)".
- Iterate với user: trình bày PROJECT.md + FEAT draft → "OK chưa? chỉnh gì?" → sửa. Lặp tới khi user confirm (không giới hạn số vòng).
- Sau confirm: return RETURN SCHEMA với `user_confirmed: true`, `step: 1`.

## Quality checklist
- [ ] PROJECT.md có **scope (in/out) + NFR + glossary** (verify bắt buộc).
- [ ] **NFR có số cụ thể** (p99 < Xms, uptime ≥ 99.X%, N req/s…) — không chung chung.
- [ ] **Security + compliance** có mặt (auth model, data classification, regulatory theo domain).
- [ ] **Out-of-scope nêu rõ ràng**; **success metrics đo được**.
- [ ] ≥ 1 FEAT draft; mỗi capability có **user story + Gherkin AC** + ưu tiên.
- [ ] `project.service_prefix` chốt (kebab, ngắn, unique).
- [ ] (Nếu research) ≥ 1 nguồn thật, ghi link.

## Done
- PROJECT.md (scope + NFR số + security/compliance + success metrics + glossary) + ≥ 1 FEAT draft (user story + Gherkin AC) + `service_prefix` chốt (khớp verify step 1); user đã confirm.
