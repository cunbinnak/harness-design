---
name: business-analysis
description: Intake step 2 (business-analyst) — refine FEAT thành AC testable + BR + boundaries_suggested. Dùng process flow / use case / edge case làm phương pháp phân tích.
---

# Business Analysis Skill

## Khi load
`/intake-requirement` **step 2** — agent `business-analyst-agent`, sau step 1 (`requirement-analysis`).
Input: `docs/architecture/PROJECT.md` + `docs/architecture/feat/FEAT-*.md` (draft từ step 1).

## Deliverable của step 2 (đúng cái command verify)
**Refine mỗi `docs/architecture/feat/FEAT-*.md`** đạt 3 thứ:
1. **AC testable** — Given/When/Then hoặc condition đo được; mỗi user story ≥ 1 AC; cover cả non-happy-path.
2. **Business rules `BR-*`** — table: rule + nơi áp dụng (endpoint/domain service/UI) + nguồn (policy/regulation/stakeholder).
3. **`boundaries_suggested`** — bounded context → boundary nào đảm nhận (gợi ý; solution-architect chốt ở step 3).

> Đây là 3 thứ `build_prompt.py` step 2 + verify command yêu cầu. Mọi thứ khác là phương pháp để ra được chúng cho tốt.

## Phương pháp phân tích (để ra AC/BR/boundaries chất lượng)
1. **Research (optional)** — chỉ khi domain phức tạp/chưa rõ và có WebSearch/WebFetch: business process pattern của industry, edge case/failure đã documented, compliance/regulatory. KHÔNG bịa nguồn.
2. **Actor & bounded context** — liệt kê tác nhân (role/system/external) → suy ra `boundaries_suggested`.
3. **Process flow (Mermaid)** — As-Is (nếu có hệ thống cũ) + To-Be (theo PROJECT). Happy path + nhánh ngoại lệ → giúp tìm AC + edge case.
   ```mermaid
   flowchart TD
     A[Actor gửi request] --> B{Hợp lệ?}
     B -- No --> E[Lỗi VALIDATION]
     B -- Yes --> C[Service xử lý] --> D[(DB)] --> F[Phản hồi]
   ```
4. **Use case** — actor · precondition · main flow · alternate · postcondition → mỗi use case sinh ≥ 1 AC.
5. **Edge case & failure** — entity không tồn tại; trạng thái final; request trùng; thiếu quyền; tenant khác; external fail/timeout → thành AC + BR.
6. **Gap analysis** — current vs target: thiếu gì, assumption, constraint.

> Process flow / use case / edge case có thể **ghi kèm vào FEAT** (section phụ trợ sau Business rules) — không bắt buộc verify, nhưng giúp dev/test/reviewer hiểu rõ.

## Flow step 2 (theo command)
- Iterate với user: trình bày refine → hỏi "OK chưa? cần chỉnh gì?" → sửa. Lặp tới khi user confirm (không giới hạn số vòng).
- Sau user confirm: return RETURN SCHEMA với `user_confirmed: true`, `step: 2`.

## Quality checklist
- [ ] Mỗi user story có ≥ 1 AC testable (Given/When/Then), gồm non-happy-path.
- [ ] BR-* có nơi áp dụng + nguồn tham chiếu.
- [ ] `boundaries_suggested` cho mọi capability (bounded context → boundary).
- [ ] (Phương pháp) process flow / use case / edge case đã cân nhắc để không sót AC.
- [ ] Assumption + constraint nêu rõ.
- [ ] (Nếu research) ≥ 1 nguồn thật, ghi link.

## Done
- Mỗi FEAT có **AC testable + BR-* + boundaries_suggested** (khớp verify intake step 2); user đã confirm.
