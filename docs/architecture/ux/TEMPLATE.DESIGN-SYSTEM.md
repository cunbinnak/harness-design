---
type: design-system
status: DRAFT
---

# Design System — {{PROJECT}}

> **Chốt TRƯỚC khi vẽ mockup.** Đảo thứ tự là mất tác dụng: token rút ra từ mockup đã vẽ chỉ là
> bản mô tả những màu đã lỡ chọn, không phải quyết định.
>
> Giá trị token nằm ở `design-tokens.css` (SoT — máy đọc). File này khai phần **máy không suy được**:
> ý đồ thị giác · cặp tương phản phải đạt · kho component đóng · ba khuôn trạng thái.

---

## 1. Ý đồ thị giác

> Ba tính từ + **neo tham chiếu thật**. Neo là hiện vật user chỉ ra ("nhìn như app X"), không phải
> gu tự bịa. Không có neo thì mọi tranh luận "đẹp/xấu" về sau không có gì để đối chiếu.

| | |
|---|---|
| Ba tính từ | {{vd: gọn · rõ · không màu mè}} |
| Neo tham chiếu | {{app/trang user chỉ ra + vì sao họ thấy dễ nhìn}} |
| Tránh | {{cái user nói "nhìn là ngợp"}} |
| Dùng ở đâu | {{ngoài nắng / trong xưởng / văn phòng → ảnh hưởng cỡ chữ, tương phản}} |

## 2. Token

Giá trị ở `design-tokens.css`. **Mọi màu/cỡ/nhịp trong mockup và trong code FE phải qua `var(--…)`**;
thiếu token thì **thêm vào SoT**, không gõ thẳng giá trị tại chỗ.

## 3. Cặp tương phản phải đạt

> Gate tự tính tỉ số WCAG từ mã hex. Ngưỡng theo cột `Loại`: `thường` ≥ 4.5 · `lớn` ≥ 3.0
> · `thành phần` ≥ 3.0 (viền ô nhập, icon mang nghĩa).

| Cặp | Chữ (hex) | Nền (hex) | Loại | Dùng ở |
|---|---|---|---|---|
| {{văn bản chính}} | `#1f2937` | `#ffffff` | thường | {{mọi màn}} |
| {{chữ mờ}} | `#6b7280` | `#ffffff` | thường | {{chú thích, placeholder}} |
| {{nút chính}} | `#ffffff` | `#1d4ed8` | thường | {{CTA}} |
| {{viền ô nhập}} | `#e5e7eb` | `#ffffff` | thành phần | {{form}} |

## 4. Kho component — ĐÓNG

> **Đóng** nghĩa là: mockup và code FE **chỉ được lắp từ danh sách này**. Cần khối mới → thêm dòng
> ở đây trước, không vẽ khối lạ tại chỗ.
>
> Cột **Trạng thái bắt buộc** là thứ vai `picky` ở `/dogfood` đi kiểm trên app đã render — không khai
> thì nó không có gì để đối chiếu. Thiếu trạng thái "đang gửi" chính là cái bấm-hai-lần mà vai
> `rushed` sẽ tìm thấy ở đợt sau.
>
> Không để ô trống. Component không dùng ở màn nào → **xoá dòng**, đừng giữ cho đủ bộ.

| # | Component | Dùng ở màn | Trạng thái bắt buộc |
|---|---|---|---|
| C1 | Nút chính | {{S1, S2}} | thường · hover · **đang gửi (khoá lại)** · bị vô hiệu |
| C2 | Trường nhập | {{S1}} | rỗng · đang gõ · **sai (có câu báo lỗi tiếng Việt)** · chỉ đọc |
| C3 | Bảng/danh sách | {{S2}} | có dữ liệu · **rỗng** · **đang tải** · lỗi tải |
| C4 | {{...}} | {{...}} | {{...}} |

## 5. Ba khuôn dùng chung

> Năm màn không được đẻ ra năm kiểu báo lỗi. Khai một lần, mọi màn dùng lại.

| Khuôn | Hiện gì | Người dùng làm gì tiếp |
|---|---|---|
| **Rỗng** | {{câu nói rõ chưa có gì + vì sao}} | {{nút/hướng dẫn bước đầu tiên}} |
| **Lỗi** | {{nói CÁI GÌ hỏng bằng tiếng người, KHÔNG lộ mã kỹ thuật}} | {{cách thử lại / liên hệ ai}} |
| **Đang tải** | {{skeleton hay spinner, ở đâu}} | {{có huỷ được không}} |

## 6. Change log

> Đổi token sau khi đã chốt → ghi ở đây kèm lý do. Đổi lặng lẽ thì mockup đã duyệt và code sẽ lệch nhau.

| Ngày | Đổi gì | Vì sao |
|---|---|---|
| | | |
