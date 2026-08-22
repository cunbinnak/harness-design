---
type: challenge-log
scope: cross-wave
---

# Challenge log — {{PROJECT}}

> **Đối kháng nội bộ thay cho reviewer bên ngoài.** Trước khi viết dòng code đầu tiên của một mảng
> việc lớn, agent tự ra **một câu hỏi khó dựa trên spec THẬT của dự án này** — loại chỉ trả lời được
> nếu đã đọc và hiểu FEAT/HLD/BR, không phải câu hỏi kiến thức chung. Tự chấm PASS/FAIL trung thực.
>
> **FAIL = đọc lại spec, ra câu khác, trả lời lại. KHÔNG ĐƯỢC CODE.**
>
> Vì sao có: review-dev bắt lỗi SAU khi code xong — lúc đó cái giá đã trả rồi. Challenge bắt đúng
> chỗ "tưởng đã hiểu mà chưa", trước khi nó thành code.
>
> **HAI lượt chất vấn, hai giai đoạn khác nhau** — cột `Giai đoạn`:
>
> | Giai đoạn | Khi nào | Đòi gì | Câu không trả lời được nghĩa là |
> |---|---|---|---|
> | `tài liệu` | trước `/approve-document` (KHOÁ SCOPE) | **≥3 câu khó nhất**, trả lời **CHỈ bằng những gì đã ghi trong tài liệu** | **một lỗ trong tài liệu** — vá rồi mới chấm PASS, đừng chấm PASS bằng kiến thức ngoài |
> | `code` | trước dòng code đầu tiên của một boundary | ≥1 câu, dựa trên FEAT/HLD/BR thật | mình tưởng đã hiểu spec mà chưa |
>
> Lượt `tài liệu` là lượt đắt nhất: khoá scope xong thì mọi lỗ tài liệu phải trả bằng code sai.
> Lượt `code` bắt chỗ đọc hiểu lệch — rẻ hơn, nhưng muộn hơn.
>
> Gate `challenge_doc` @ `/approve-document` · gate `challenge_passed` @ chốt review-dev.
> Cả hai lọc theo wave: dòng của wave trước KHÔNG gánh hộ wave này.

## Câu hỏi thế nào là tốt

Nguồn ra câu hỏi tốt — đều là chỗ spec **có thể mâu thuẫn hoặc chưa phủ**:

- Mâu thuẫn tiềm tàng giữa hai AC của cùng một FEAT
- Ca biên ở HLD mà mô hình dữ liệu hiện tại chưa chặn được
- **Ô `cấm` trong ma trận vai × hành động** mà thiết kế hiện tại chưa chặn ở server
- Trạng thái bắt buộc của component (đang gửi, lỗi) mà API chưa phân biệt được để hiển thị
- Thứ nằm trong FEAT nhưng **không** thuộc scope wave này, dễ bị làm nhầm
- Ranh giới module mà thiết kế đang định làm sẽ vi phạm
- **Surface wave trước đã giao** (`tracking/BC-LEDGER.md §1`) mà việc sắp làm sẽ đụng vào

Câu hỏi **xấu**: trả lời được mà không cần mở file nào ("idempotency là gì", "nên dùng index không").
Ra câu dễ cho qua là tự lừa mình — và cái giá trả ở dogfood.

## Log

| Ngày | Wave | Giai đoạn | Mảng việc | Câu hỏi | Trả lời (dẫn về đâu) | Phán quyết |
|---|---|---|---|---|---|---|
| {{ISO}} | {{wave-001}} | tài liệu | {{lớp doc}} | {{câu hỏi khó}} | {{trả lời + file/mục dẫn ra nó}} | PASS |
| {{ISO}} | {{wave-001}} | code | {{boundary/feat}} | {{câu hỏi khó}} | {{trả lời + file/mục dẫn ra nó}} | PASS |
