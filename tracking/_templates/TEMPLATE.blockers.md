---
type: blockers
scope: cross-wave
---

# Blocker — {{PROJECT}}

> **Chặn cứng SAU KHI đã tự thử hết cách.** Đây là chỗ dừng hợp lệ thứ ba, khác hẳn hai chỗ kia:
>
> | Tình huống | Làm gì |
> |---|---|
> | Mơ hồ, nhưng suy được từ tài liệu | `py scripts/decide.py` → đi tiếp. **Không ghi ở đây** |
> | Ngoài scope wave này | đẩy wave sau (`dogfood-report` cột `Xử`, hoặc WAVE-SEQUENCE). **Không ghi ở đây** |
> | **Chặn cứng — đã thử hết cách vẫn không đi được** | ghi một dòng ở đây, **chuyển sang việc khác**, báo gộp cuối lượt |
>
> Không ghi để rồi ngồi chờ. Ghi xong là **đi làm việc khác ngay** — một blocker không được phép
> làm đứng cả lượt. Cột `Đã thử gì` là thứ phân biệt blocker thật với "chưa thử đủ": trống thì
> chưa phải blocker, mới là chưa làm.
>
> **Sổ này KHÔNG bị reset khi mở wave.** `/next-wave` đếm dòng còn `mở` rồi nhắc — blocker treo
> qua wave mà không ai đụng tới là thứ đáng biết trước khi cam kết scope wave mới.

| Ngày | Wave | Blocker | Đã thử gì | Trạng thái | Gỡ thế nào / ngày đóng |
|---|---|---|---|---|---|
| {{ISO}} | {{wave-001}} | {{cái gì chặn, cụ thể}} | {{đã thử A, B, C — vì sao vẫn không được}} | mở | |
