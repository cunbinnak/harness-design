---
name: requirement-analysis
description: Intake step 1 (requirement-analyst) — nhận mô tả project, sinh PROJECT.md (scope + NFR + glossary) + FEAT-*.md draft + chốt service_prefix.
---

# Requirement Analysis Skill

## Khi load
`/intake-requirement` **step 1** — agent `requirement-analyst-agent`. Đây là bước **nhận yêu cầu** (đầu tiên của intake).
Input: **mô tả project** user truyền sau lệnh (`$ARGUMENTS`); nếu amendment → đọc CR `change_summary`.

## Deliverable của step 1 (đúng cái command verify)
1. **`docs/architecture/PROJECT.md`** — tối thiểu phải có (verify check): **scope** (in/out), **NFR** (targets project-wide), **glossary**. Điền theo `TEMPLATE.project.md`: vision/one-liner, đối tượng, phạm vi, mục tiêu & KPI, ràng buộc, NFR, nguyên tắc thiết kế, glossary, open questions.
2. **`docs/architecture/feat/FEAT-*.md` draft** (≥ 1) — mỗi capability 1 file: tiêu đề, mục tiêu, phạm vi (in/out), **AC sơ bộ** (Given/When/Then mức draft). *(AC testable + BR + boundaries_suggested để step 2 — business-analysis refine.)*
3. **Chốt `project.service_prefix`** — prefix ngắn kebab cho repo service polyrepo (vd `crm-hdpe`). Dùng cho `services/{prefix}-{boundary}/` về sau.

> Đây là output `build_prompt.py` step 1 + verify command yêu cầu. Đừng làm thay việc step 2 (đừng cố hoàn chỉnh AC testable / BR / boundaries ở đây).

## Phương pháp
1. **Phân loại yêu cầu**: chức năng (functional) vs phi chức năng (NFR: performance/availability/security/scalability/observability + coverage target).
2. **Scope in/out**: chốt rõ cái gì làm, cái gì KHÔNG làm (tránh scope creep).
3. **Tách capability → FEAT**: mỗi nhóm chức năng lớn = 1 FEAT draft; gắn ưu tiên (Must/Should/Could).
4. **Glossary**: định nghĩa thuật ngữ domain để mọi agent hiểu thống nhất.
5. **Ràng buộc & giả định**: compliance/pháp lý, tech stack bắt buộc, timeline/team; ghi `Open questions` cho chỗ chưa rõ.

## Flow step 1 (theo command)
- Nếu gọi không có mô tả: hỏi user "Mô tả project? (vd CRM cho công ty X, N module…)".
- Iterate với user: trình bày PROJECT.md + FEAT draft → "OK chưa? cần chỉnh gì?" → sửa. Lặp tới khi user confirm (không giới hạn số vòng).
- Sau user confirm: return RETURN SCHEMA với `user_confirmed: true`, `step: 1`.

## Quality checklist
- [ ] PROJECT.md có **scope (in/out) + NFR + glossary** (3 thứ verify bắt buộc).
- [ ] ≥ 1 FEAT draft; mỗi capability lớn 1 file, có mục tiêu + phạm vi + AC sơ bộ + ưu tiên.
- [ ] `project.service_prefix` đã chốt (kebab, ngắn, unique).
- [ ] Functional vs NFR phân loại rõ; assumption/constraint + open questions nêu rõ.

## Done
- PROJECT.md (scope + NFR + glossary) + ≥ 1 FEAT draft + `service_prefix` chốt (khớp verify intake step 1); user đã confirm.
