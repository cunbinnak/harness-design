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
> Gate D0: §1 + §2 có content thật · **mỗi pain point + mỗi hypothesis có dòng `Bằng chứng:` không rỗng** · §3 ≥3 row (mỗi row có test method + status TESTABLE) · §4 ≥2 item · §6 ≥1 lỗ hổng.
> Downstream: D1 derive capability per hypothesis · D3 PROJECT.md §1 pull từ §1+§2.

> **Bằng chứng là gì.** Một câu chuyện thật đã xảy ra, một con số, hoặc một hiện vật (ảnh cuốn sổ,
> file Excel đang dùng, tin nhắn, log). KHÔNG phải diễn đạt lại câu trả lời cho mượt hơn.
> "Người dùng hay gặp khó khăn khi nhập đơn" không phải bằng chứng.
> "Tuần trước chị Lan nhập nhầm 3 đơn, mỗi đơn mất 20 phút gọi lại khách — có ảnh sổ tay" là bằng chứng.

---

## 1. Vision narrative

> 1-2 đoạn: giải quyết vấn đề gì, cho ai, vì sao bây giờ. Không đi vào giải pháp kỹ thuật. Không bịa số liệu (verify ở D1).

{{Đoạn 1 — what & for whom: làm gì, phục vụ ai, thay thế cách cũ ra sao.}}

{{Đoạn 2 — why now: bối cảnh/áp lực; pain ăn vào đâu (doanh thu / chi phí / quyết định / trải nghiệm).}}

---

## 2. Problem statement

> 2-3 đoạn. Mỗi pain: status quo (cách làm hiện tại) + cost of inaction (giá phải trả nếu không làm). Kết bằng hệ quả gộp.
> **Mỗi pain point PHẢI có dòng `Bằng chứng:`** — gate D0 đếm. "Thường", "nhiều", "hay bị" phải quy ra số.

**Pain point 1 — {{tên ngắn}}.** {{Mô tả. Status quo + cost of inaction.}}

Bằng chứng: {{câu chuyện thật đã xảy ra (ai, khi nào, mất gì) · hoặc con số (bao nhiêu lần/tuần, mỗi lần tốn bao nhiêu phút/tiền) · hoặc hiện vật (file/ảnh/tin nhắn đang dùng)}}

**Pain point 2 — {{tên ngắn}}.** {{Mô tả. Status quo + cost of inaction.}}

Bằng chứng: {{như trên}}

**Hệ quả gộp.** {{Vì sao các pain cùng gốc; chi phí cách cũ tăng theo quy mô. Số định lượng nào là giả định verify ở D1.}}

---

## 3. Hypotheses

> Mỗi giả thuyết phải falsifiable. Expected outcome = tín hiệu đo được. Test method = cách kiểm chứng. ≥3 row TESTABLE để rời D0.

| ID | Statement (falsifiable) | Ngưỡng (SỐ, ghi TRƯỚC) | Cách đo | Bằng chứng (vì sao tin điều này) | Wave đo | Số thật | Status |
|---|---|---|---|---|---|---|---|
| H1 | {{Nếu làm X thì Y đổi — có thể bị bác bỏ}} | {{≥30% trong 2 tuần — con số, không phải "tăng đáng kể"}} | {{event nào đếm · so với baseline nào}} | {{chuyện thật/con số/hiện vật khiến đặt cược này}} | {{wave-001}} | | TESTABLE |
| H2 | {{TBD}} | {{TBD}} | {{TBD}} | {{TBD}} | {{TBD}} | | TESTABLE |
| H3 | {{TBD}} | {{TBD}} | {{TBD}} | {{TBD}} | {{TBD}} | | TESTABLE |

`Status`: `TESTABLE → PROVEN | DISPROVEN | CHƯA ĐỦ DỮ LIỆU | PIVOTED`.

> **`Ngưỡng` phải là SỐ và phải ghi TRƯỚC khi nhìn dữ liệu.** "Tăng đáng kể" không bác bỏ được cái
> gì — giả thuyết nào cũng đúng nếu ngưỡng viết sau. Sửa ngưỡng sau khi thấy số là cách tự lừa mình
> một cách lịch sự; muốn đổi thì ghi một dòng ở §7 kèm lý do, để lần sau còn đọc lại được.
>
> **`Cách đo` phải trỏ tới thứ có thật**: một event trong `tracking/PRODUCTION-READY.md` nhóm 4, hoặc
> một truy vấn cụ thể. Không cài chỗ đo thì giả thuyết vĩnh viễn nằm ở `TESTABLE` — và cả sổ này
> thành danh sách phỏng đoán không ai đối chứng.
>
> **`CHƯA ĐỦ DỮ LIỆU` là kết luận hợp lệ.** Ép ra `PROVEN`/`DISPROVEN` khi số chưa đủ còn tệ hơn
> không kết luận: nó đóng một câu hỏi vẫn đang mở.
>
> `/next-wave` đối chiếu cột `Wave đo` — wave đóng mà giả thuyết của wave đó còn `TESTABLE` thì nhắc.

> Cột `Bằng chứng` trống = giả thuyết bịa từ suy luận, không từ thực tế Authority kể. Gate D0 chặn.

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

## 6. Lỗ hổng & cách xử

> **Chỗ Authority KHÔNG trả lời được, hoặc không có mặt để hỏi.** Bảng trống là dấu hiệu chưa đào —
> không buổi khai thác nào phủ hết mọi thứ ngay lần đầu. Gate D0 đòi ≥1 dòng.
>
> Thứ tự xử, đúng theo thứ tự này: (1) tìm trong tài liệu Authority đã đưa · (2) hỏi Authority
> · (3) Authority vắng/chưa quyết → **tự quyết phương án hợp lý nhất + ghi 1 dòng
> `tracking/decisions.md`** (có cột giả định) rồi đi tiếp. KHÔNG treo lỗ hổng sang D1.

| # | Lỗ hổng (thứ chưa rõ) | Đã tìm ở đâu | Cách xử | Vết |
|---|---|---|---|---|
| G1 | {{vd: chưa rõ ai chịu chi phí khi đơn nhầm}} | {{brief Authority · hỏi trực tiếp}} | {{hỏi Authority → đã trả lời · hoặc tự quyết}} | {{§2 pain 1 · hoặc decisions.md 2026-08-22}} |

---

## 7. Change log

| Date | Wave | Change | Author |
|---|---|---|---|
| {{DATE}} | D0 (pending) | Stub | — |
