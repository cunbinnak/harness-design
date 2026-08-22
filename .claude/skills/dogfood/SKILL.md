---
name: dogfood
description: Dùng thử sản phẩm ĐANG CHẠY bằng 6 lăng kính persona, hai đợt theo trạng thái DB — thay cho MANUAL_TEST thủ công. Mỗi vai đóng một persona thật từ persona-pool, vai breaker chạy đủ ma trận vai × hành động. Mỗi phát hiện một dòng ở dogfood-report §2 kèm ô Xử (sửa ngay / chưa xử / wave sau) — ô trống là chưa ai quyết. KHÔNG tự fix.
---

# Dogfood Skill

## Khi load
`/dogfood` ở stage MANUAL_TEST — sau `/run-wave`. Đây là **chỗ thay cho việc người phải tự ngồi chọc vào hệ**: 6 lăng kính dùng thử trên hệ ĐANG CHẠY thật, ghi bug `origin=manual`.

`/run-wave` chạy **test-case đã viết** — nó chỉ tìm được thứ ai đó nghĩ ra trước. Dogfood đi tìm thứ **không có trong registry**: màn rỗng không nói gì, lỗi bị nuốt im lặng, bấm hai lần ra hai bản ghi, vai A chạm được dữ liệu vai B. Hai việc khác nhau, không thay thế nhau.

## Điều kiện vào

| Cần | Ở đâu | Thiếu thì |
|---|---|---|
| Hệ đang chạy thật | `tracking/wave-{N}/health-proof.json` | STOP — chạy lại `/run-wave`, KHÔNG dogfood ảo |
| Persona + ma trận quyền | `docs/discovery/persona-pool.md` | STOP — ma trận là danh sách phép thử của vai breaker |
| Gán 6 vai ↔ persona + đợt | `persona-pool.md §Gán persona cho vai dogfood` | Mặc định: mọi vai đóng persona chính |
| Luồng lõi + AC của wave | `docs/plans/wave-{N}.md` + `docs/architecture/feat/FEAT-*.md` | STOP |
| **FEAT/AC wave trước đã giao** (wave ≥2) | `archive/wave-*/DELIVERED.md` | bỏ lượt regression — gãy tính năng cũ sẽ lọt |
| Giao diện đã chốt (nếu có UI) | `docs/architecture/ux/` + `design-tokens.css` | vai `picky` bỏ qua, ghi rõ lý do |

## Hai đợt — chia theo TRẠNG THÁI DỮ LIỆU, không theo độ khó

Lý do chia đợt không phải để dàn tải, mà vì **các vai dùng chung một hệ và một DB**. Thả cả 6 cùng lúc thì vai này ghi dữ liệu đè lên cảnh vai kia đang nhìn — và **trạng thái rỗng chết ngay khi có bản ghi đầu tiên**, đúng thứ vai `edge` coi là quan trọng nhất.

```
Đợt 1 — DB SẠCH, đọc là chính     : user-edge · user-newbie · user-picky
   ↓ seed lại dữ liệu mẫu
Đợt 2 — DB CÓ DỮ LIỆU, ghi và phá : user-rushed · user-breaker · user-mobile
```

**Ba ràng buộc cứng:** tối đa 3 vai một đợt · **không mở đợt 2 khi đợt 1 chưa trả kết quả đủ** · **giữa hai đợt phải seed lại**. Muốn đổi vai nào vào đợt nào thì sửa cột `Đợt` ở `persona-pool.md`, đừng đổi trong đầu.

Chưa có bước seed → tạo dữ liệu mẫu bằng tay theo `docs/plans/wave-{N}.md` và **ghi 1 dòng `/decide`**: thiếu seed là một phát hiện của chính lượt dogfood này, không phải chuyện vặt.

## Mỗi vai nhận gì trong prompt

1. URL/endpoint hệ đang chạy (lấy từ `health-proof.json`, không đoán)
2. **Persona được giao** — chân dung + năng lực được cấp + luồng chính, chép từ `persona-pool.md`. Lăng kính là *cách dùng*; persona là *ai đang dùng*. Thiếu persona thì vai thử như "người dùng nói chung", đúng thứ persona-pool sinh ra để tránh
3. Luồng lõi + AC liên quan của wave
4. Riêng `breaker`: **ma trận vai × hành động** đầy đủ + tài khoản thử cho từng vai
5. Riêng `picky`: màn hình liên quan ở `docs/architecture/ux/` + `design-tokens.css`

## Bằng chứng bộ ba — không có thì không tính là đã thử

Mọi phát hiện phải kèm đủ ba vế:

```
Tôi đã làm    : <thao tác chính xác — URL, dữ liệu đã gõ, nút đã bấm>
Tôi thấy      : <thứ hiện ra trên màn / mã lỗi / response thật>
Tôi mong đợi  : <thứ lẽ ra phải xảy ra, và vì sao — dẫn về AC/FEAT/ma trận>
```

Thiếu vế "Tôi đã làm" = suy từ code chứ chưa chạy. Vế "Tôi mong đợi" không dẫn được về tài liệu nào = ý kiến cá nhân, không phải bug.

## Dấu hiệu dogfood giả

- Cả 6 vai báo "không thấy vấn đề gì" ngay lần đầu — hệ mới dựng trong một wave luôn có chỗ vướng
- Báo cáo không nêu được mình đóng persona nào, hoặc đi luồng chẳng liên quan tới persona đó
- Không có thao tác cụ thể nào, chỉ có nhận xét chung ("giao diện ổn", "API hoạt động tốt")
- `breaker` báo "phân quyền đúng" mà không nêu được đã thử bao nhiêu ô `cấm` trên tổng bao nhiêu
- `picky` báo "khớp thiết kế" mà không nêu được một giá trị đo thật nào (computed style / mã màu)
- `edge` báo trạng thái rỗng OK nhưng đợt 1 chạy sau khi DB đã có dữ liệu

Dính bất kỳ dấu hiệu nào → **cho chạy lại vai đó**, yêu cầu nêu thao tác cụ thể + thứ nhìn thấy.

## Lượt regression — bắt buộc từ wave 2

`archive/wave-*/DELIVERED.md` là **hợp đồng của các wave trước**: FEAT + AC đã verify được, máy derive từ registry + report lúc đóng wave — không phải agent khai. Vai `rushed` và lượt tự đi của phiên chính phải **đi lại luồng lõi từng FEAT trong đó**, không chỉ luồng của wave này.

Wave mới xây chồng lên, không đập đi. Tính năng wave cũ gãy vì code wave mới là **regression** — nặng ngang gãy luồng lõi, xử trước mọi phát hiện khác.

## Xử phát hiện

| Loại | Xử |
|---|---|
| Hỏng luồng lõi · mất dữ liệu · **lỗ hổng phân quyền** | Bug **blocker** — chặn đóng wave |
| **Regression** — FEAT wave trước trong `DELIVERED.md` không còn chạy được | Bug **blocker**, xử đầu tiên |
| Lệch AC đã chốt | Bug thường, ghi rõ AC nào |
| Lệch giao diện đã chốt | Bug thường, dẫn về màn + token |
| Vướng nhưng không sai spec | Ghi backlog, KHÔNG tự nới scope |

Mọi lỗi phân quyền là **blocker**, không có ngoại lệ — nó là loại lỗi mà người dùng thật phát hiện ra trước mình.

## Ranh giới

- **KHÔNG tự fix.** Ghi dòng vào §2 rồi dừng — MAIN điều phối lượt sửa, để nhân quả rõ ràng.
- **KHÔNG sửa test-case-registry** cho khớp thứ vừa thấy.
- **KHÔNG sửa doc spec** — phase-lock chặn, và sửa spec cho khớp code là đúng anti-pattern harness sinh ra để chống.
- **KHÔNG teardown infra** — giữ UP cho lượt sửa + chạy lại test.
- Sản phẩm không có UI → các vai gọi API trực tiếp; `picky` soi shape response + error envelope thay cho giao diện; `mobile` soi độ trễ từ client yếu thay cho layout.

## Xử phát hiện — MỖI dòng phải có quyết định

Gộp phát hiện của cả 6 lăng kính × 2 đợt vào `tracking/wave-{N}/dogfood-report.md` §2.
**File có thể ĐÃ TỒN TẠI** với mục `## Mang sang từ wave <N-1>` — những dòng `chưa xử` của
wave trước, `/next-wave` chép sang với ô `Xử` bỏ trống. **APPEND vào, KHÔNG ghi đè**, và
quyết lại từng dòng đó (`sửa ngay` hay `wave sau`) — để nguyên chữ `chưa xử` là hoãn vô hạn.
Khuôn đầy đủ: `tracking/_templates/TEMPLATE.dogfood-report.md`. Cột `Xử` là **từ vựng đóng**, đúng
một trong ba — **ô trống nghĩa là chưa ai quyết**, không phải "không đáng":

| Loại phát hiện | Xử |
|---|---|
| Hỏng luồng lõi · mất dữ liệu · **thủng phân quyền** (vai A chạm được dữ liệu vai B) | `sửa ngay` — không hoãn |
| **Gãy luồng của wave TRƯỚC** (`archive/wave-*/DELIVERED.md`) | `sửa ngay` — nặng ngang gãy luồng lõi |
| Lệch design system / mockup user đã chốt: màu-cỡ ngoài token · thiếu trạng thái bắt buộc · sai khuôn rỗng/lỗi/đang tải | `sửa ngay` **về token**; cố ý giữ khác → `py scripts/decide.py` một dòng |
| Nhỏ, sửa dưới 15 phút | `sửa ngay` |
| Cần nhiều thời gian **nhưng trong scope wave này** | `chưa xử` — cột `Ở đâu` nói rõ đang nằm chỗ nào |
| **Ngoài scope đã khoá** | `wave sau` — cột `Ở đâu` nói **vì sao ngoài scope** + **cần gì để làm** |

`sửa ngay` xong thì chạy lại phần vừa sửa — sửa mà không dùng lại là chưa biết đã sửa được chưa.

Gate `dogfood_done` đọc đúng bảng này: thiếu ô `Xử` · khai `sửa ngay` mà không dẫn được vết sửa ·
đẩy `wave sau` mà không nói lý do → đỏ.

**Chỗ GHI khác chỗ NHẬN.** `docs/plans/**` bị phase-lock chặn ở đây, nên đừng cố ghi thẳng vào
`WAVE-SEQUENCE.md` — ghi lý do vào bảng này là đủ. `/next-wave` đối chiếu và nhắc dòng nào chưa
có chỗ nhận; muốn nhận thật thì lùi `/domain` (chốt chia-wave) — khoá chỉ mở ở đó. Không có sổ bug riêng: **kết quả test nằm ở
`test-report.md`, quyết định xử nằm ở đây**, hai chỗ không chép lẫn nhau.

## Done
- Đủ 2 đợt, mỗi vai một báo cáo có bằng chứng bộ ba.
- §2 mọi dòng có ô `Xử`; §3 Kết luận điền bằng **số**, không phải tính từ.
- Báo user tổng hợp → còn `sửa ngay` thì sửa + chạy lại; sạch → `/next-wave`.
