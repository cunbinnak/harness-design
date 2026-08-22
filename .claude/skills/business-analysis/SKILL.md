---
name: business-analysis
description: Lens phân tích AC/BR — kiểm AC testable + BR logical + scope rõ. Dùng bởi /review-document (review product DOMAIN/DESIGN) + /domain (phân tích tác động khi đổi phạm vi). Process flow / use case / edge case làm phương pháp.
---

# Business Analysis Skill

## Khi load
- **`/review-document`** (review-document-agent): soi product (FEAT/AC + BR) + design xem AC có testable, BR có logical, scope có rõ — trả issues cho user feed feedback.
- **`/domain`** (apply-cr-agent): analyze CR impact lên scope/AC/BR → vùng cần re-design.

Input: `docs/architecture/{PROJECT.md, feat/FEAT-*.md, business-rules/BR-*.md}` + (apply-cr) `tracking/change-requests/{cr-id}-*.md`.

## Cái cần đảm bảo (chất lượng AC/BR — FEAT do DOMAIN author)
1. **AC testable** — Given/When/Then (Cho/Khi/Thì) hoặc condition đo được; mỗi user story ≥ 1 AC; cover cả non-happy-path.
2. **Business rules `BR-*`** — phát biểu rõ + nguồn (policy/regulation/stakeholder) + ≥2 ví dụ; `related_features` ≥1.
3. **Scope rõ** — §Ngoài phạm vi đủ để QC biết KHÔNG test gì; bounded context rõ (boundary thật chốt ở DESIGN/PLAN).

> DOMAIN (`/domain`: author business → ký → dịch sinh eng) sở hữu FEAT/BR; skill này là LENS kiểm chất lượng (review) + phân tích thay đổi (CR) — KHÔNG tự author FEAT.

## Phương pháp phân tích (để ra AC/BR/boundaries chất lượng)
1. **Research** — chỉ khi domain phức tạp/chưa rõ và có WebSearch/WebFetch: business process pattern của industry, edge case/failure đã documented, compliance/regulatory. KHÔNG bịa nguồn.
2. **Actor & bounded context** — liệt kê tác nhân (role/system/external) → suy ra bounded context (gợi ý boundary; DESIGN chốt).
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

## Flow
- **review-document**: soi → trả `issues[]` (file + concern) cho user; KHÔNG tự sửa product (DOMAIN author sửa, hoặc revision loop).
- **apply-cr**: analyze CR → ghi impact vào CR file §Kế hoạch cập nhật + return `affected_docs`/`boundaries_affected`.

## Quality checklist (khi review / phân tích)
- [ ] Mỗi user story có ≥ 1 AC testable (Cho/Khi/Thì), gồm non-happy-path.
- [ ] BR-* có nguồn tham chiếu + ≥2 ví dụ + `related_features` ≥1.
- [ ] Scope rõ (§Ngoài phạm vi đủ cho QC); bounded context rõ.
- [ ] (Phương pháp) process flow / use case / edge case đã cân nhắc để không sót AC.
- [ ] (Nếu research) ≥ 1 nguồn thật, ghi link.

## Done
- review-document: trả issues list cho user feedback. apply-cr: CR impact analysis ghi vào CR file.
