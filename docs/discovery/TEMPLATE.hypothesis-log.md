---
type: discovery
artifact_kind: hypothesis-log
status: DRAFT
tier: T1
owner_authority: Business Authority
wave: D0
last_reviewed: "{{DATE}}"
---

# Hypothesis Log — {{PROJECT_NAME}}

> Điền NGẮN GỌN: ưu tiên bảng/bullet, không văn xuôi thừa, không lặp. Doc này agent downstream đọc nhiều lần — tiết kiệm context.

> Artifact ĐẦU TIÊN của Discovery (D0, Business Authority). Vision + giả thuyết falsifiable TRƯỚC D1/D2.
> Gate D0: §1 + §2 có content thật · §3 ≥3 row (mỗi row có test method + status TESTABLE) · §4 ≥2 item.
> Downstream: D1 derive capability per hypothesis · D3 PROJECT.md §1 pull từ §1+§2.

---

## 1. Vision narrative

> 1-2 đoạn: giải quyết vấn đề gì, cho ai, vì sao bây giờ. Không đi vào giải pháp kỹ thuật. Không bịa số liệu (verify ở D1).

{{Đoạn 1 — what & for whom: làm gì, phục vụ ai, thay thế cách cũ ra sao.}}

{{Đoạn 2 — why now: bối cảnh/áp lực; pain ăn vào đâu (doanh thu / chi phí / quyết định / trải nghiệm).}}

---

## 2. Problem statement

> 2-3 đoạn. Mỗi pain: status quo (cách làm hiện tại) + cost of inaction (giá phải trả nếu không làm). Kết bằng hệ quả gộp.

**Pain point 1 — {{tên ngắn}}.** {{Mô tả. Status quo + cost of inaction.}}

**Pain point 2 — {{tên ngắn}}.** {{Mô tả. Status quo + cost of inaction.}}

**Hệ quả gộp.** {{Vì sao các pain cùng gốc; chi phí cách cũ tăng theo quy mô. Số định lượng nào là giả định verify ở D1.}}

---

## 3. Hypotheses

> Mỗi giả thuyết phải falsifiable. Expected outcome = tín hiệu đo được. Test method = cách kiểm chứng. ≥3 row TESTABLE để rời D0.

| ID | Statement (falsifiable) | Expected outcome (đo được) | Test method (experiment/interview/data) | Linked persona/cap (D1) | Status |
|---|---|---|---|---|---|
| H1 | {{Nếu làm X thì Y đổi — có thể bị bác bỏ}} | {{tín hiệu vs baseline}} | {{pilot A/B · phỏng vấn · đối chiếu data}} | _D1_ | TESTABLE |
| H2 | {{TBD}} | {{TBD}} | {{TBD}} | _D1_ | TESTABLE |
| H3 | {{TBD}} | {{TBD}} | {{TBD}} | _D1_ | TESTABLE |

Status: `TESTABLE → PROVEN | DISPROVEN | PIVOTED` (cập nhật qua change-log §6).

---

## 4. Anti-hypotheses (what we are NOT betting on)

> Những gì project KHÔNG cược vào — chặn scope-creep. Mỗi item: "không cược vào ... vì trọng tâm là ...". ≥2 item.

- {{KHÔNG cược vào ... — vì trọng tâm là ...}}
- {{KHÔNG cược vào ... — vì pain user nêu là ...}}

---

## 5. Risks + assumptions (verify ở D1)

| # | Loại | Mô tả | Verify ở | Mức độ |
|---|---|---|---|---|
| A1 | Assumption | {{vd: tỉ lệ lỗi hiện tại đủ cao}} | D1 (đo baseline) | high |
| A2 | Assumption | {{vd: persona X sẵn sàng đổi quy trình}} | D1 (phỏng vấn) | med |
| R1 | Risk | {{vd: nếu baseline đã tốt, ROI thấp}} | D1 | high |

---

## 6. Change log

| Date | Wave | Change | Author |
|---|---|---|---|
| {{DATE}} | D0 (pending) | Stub | — |
