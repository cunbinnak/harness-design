---
type: dogfood-report
wave: "{{WAVE_ID}}"
---

# Dogfood — {{WAVE_ID}}

> Sáu lăng kính × hai đợt, trên **hệ đang chạy**. Đây là thứ bắt được cái test-case mù: cảnh rỗng
> câm · lỗi bị nuốt im lặng · bấm hai lần ra hai bản ghi · vai A chạm dữ liệu vai B.
>
> Gate `dogfood_done` đòi đủ **6 lăng kính** (`edge` `newbie` `picky` `rushed` `breaker` `mobile`)
> và đủ **2 đợt**. Đợt 1 **DB SẠCH** (trạng thái rỗng chết ngay khi có bản ghi đầu tiên), đợt 2
> **DB CÓ DỮ LIỆU** (bảng dài mới tràn). Gộp một đợt là mất một nửa phép thử.

## 1. Đã chạy gì

| Đợt | Trạng thái DB | Lăng kính | Chạy trên | Ghi chú |
|---|---|---|---|---|
| đợt 1 | sạch | edge · newbie · picky | {{URL/endpoint}} | |
| đợt 1 | sạch | rushed · breaker · mobile | {{...}} | |
| đợt 2 | có dữ liệu | edge · newbie · picky | {{...}} | |
| đợt 2 | có dữ liệu | rushed · breaker · mobile | {{...}} | |

## 2. Phát hiện — mỗi dòng PHẢI có ô `Xử`

> **Từ vựng ĐÓNG.** Ô `Xử` chỉ nhận đúng một trong ba: `sửa ngay` · `chưa xử` · `wave sau`.
> **Ô trống nghĩa là chưa ai quyết** — không phải "không đáng". Gate đếm ô trống.
>
> Cách xếp loại (không tự chế thang riêng):
>
> | Loại phát hiện | Xử |
> |---|---|
> | Hỏng luồng lõi · mất dữ liệu · **thủng phân quyền** (vai A chạm được dữ liệu vai B) | `sửa ngay` — không hoãn |
> | **Gãy luồng của wave TRƯỚC** (`archive/wave-*/DELIVERED.md`) | `sửa ngay` — nặng ngang gãy luồng lõi |
> | Lệch `DESIGN-SYSTEM.md` / mockup user đã chốt: màu-cỡ ngoài token · thiếu trạng thái bắt buộc · sai khuôn rỗng/lỗi/đang tải | `sửa ngay` về **token**; cố ý giữ khác → `py scripts/decide.py` một dòng |
> | Nhỏ, sửa dưới 15 phút | `sửa ngay` |
> | Cần nhiều thời gian **nhưng trong scope wave này** | `chưa xử` — cột `Ở đâu` phải nói rõ đang nằm chỗ nào |
> | **Ngoài scope đã khoá** | `wave sau` — cột `Ở đâu` nói **vì sao ngoài scope** + **cần gì để làm**. KHÔNG ghi thẳng vào `WAVE-SEQUENCE.md` được (phase-lock chặn `docs/plans/**` ở đây); `/next-wave` sẽ đối chiếu và nhắc, muốn nhận thật thì lùi `/domain` chốt chia-wave |

| # | Lăng kính | FEAT/AC | Thao tác đã làm | Thấy gì trên màn hình | Xử | Ở đâu |
|---|---|---|---|---|---|---|
| D1 | {{picky}} | {{FEAT-A-001:AC-2}} | {{bấm Lưu hai lần liên tiếp}} | {{tạo hai bản ghi trùng}} | sửa ngay | {{commit abc123}} |

## 3. Kết luận

> Số, không phải tính từ. "Nhìn ổn" không đối chiếu được với gì.

```
Chạy trên      : local | môi trường thật
Luồng lõi      : đi hết được / gãy ở bước <n>
AC             : <x>/<y> LÀM ĐƯỢC THẬT (bấm ra kết quả, không phải đọc code suy ra)
Phân quyền     : <x>/<y> ô `cấm` trong ma trận vai × hành động đã thử — chặn đúng hết / thủng ở <đâu>
Wave trước     : <x>/<y> luồng trong archive/wave-*/DELIVERED.md còn chạy được
Mockup đã chốt : khớp / lệch ở <màn nào>   (n/a nếu không có UI)
Design system  : <x> màu-cỡ ngoài token · <y>/<z> component đủ trạng thái bắt buộc

Đã sửa ngay    : <danh sách>
Chưa xử        : <danh sách + đang nằm ở đâu>
Đẩy wave sau   : <danh sách + dòng nào trong WAVE-SEQUENCE.md>
```

## 4. Dấu hiệu dogfood giả

> Cả 6 lăng kính đều báo "không thấy vấn đề gì" ngay lượt đầu — **gần như chắc chắn chúng không
> thực sự dùng**. Sản phẩm vừa dựng xong luôn có chỗ vướng.
>
> Gặp vậy thì kiểm: agent có mở thật không, có bấm thật không, hay chỉ đọc code rồi suy ra. Rồi
> cho chạy lại, bắt nêu **thao tác cụ thể đã làm** và **thứ nhìn thấy trên màn hình** — hai cột đó
> ở §2 chính là chỗ phân biệt dùng thật với đọc code.
