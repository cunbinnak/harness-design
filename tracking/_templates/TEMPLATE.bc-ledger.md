---
type: backward-compatibility-ledger
scope: cross-wave
---

# Sổ tương thích ngược — {{PROJECT}}

> **Có hiệu lực từ wave 2** — khi đã có thứ giao cho người dùng thật. Wave 1 file này nằm im;
> gate tự biết theo số wave, không cần marker.
>
> Nguyên tắc: **legacy là hợp đồng — mặc định chỉ THÊM, không đổi/xoá.** Buộc phải phá →
> **DỪNG, hỏi user**, không tự quyết. Phá hợp đồng đã giao cho người dùng thật là loại quyết định
> không đảo ngược được, không thuộc thẩm quyền tự quyết của agent.
>
> Cưỡng chế bằng máy: gate `backward_compat` đếm §3 khi đóng wave — còn mục chưa rà thì không đóng được.

---

## 1. Sổ hợp đồng — surface đang giao ra ngoài

<!-- DANH SÁCH những gì các wave trước đã hứa: có thứ gì đó (client, code cũ, hệ thống ngoài, file
     người dùng tải về) đang PHỤ THUỘC vào hình dạng của nó. Điền ở wave TẠO RA surface đó; wave sau
     đối chiếu mọi thay đổi vào đây.

     TÍCH LUỸ VĨNH VIỄN — /next-wave KHÔNG BAO GIỜ xoá mục nào ở §1. Chỉ §3 được re-arm.
     Loại nào sản phẩm không có → ghi một dòng "KHÔNG CÓ" để chứng tỏ đã rà chứ không phải quên. -->

### 1a. API — endpoint + shape

| Endpoint | Version | Request: field bắt buộc | Response: field client đang dùng | Ai đang gọi | Wave giao |
|---|---|---|---|---|---|
| | | | | | |

### 1b. Bảng dữ liệu

| Bảng | Cột đang được code/báo cáo/export dùng | Ràng buộc đáng nhớ | Wave giao |
|---|---|---|---|
| | | | |

### 1c. Cache entity

| Key pattern | Shape (field trong value) | TTL | Version nằm trong key? | Wave giao |
|---|---|---|---|---|
| | | | | |

### 1d. Event / Message

| Topic / event-type | Payload schema | Producer → Consumer | Wave giao |
|---|---|---|---|
| | | | |

### 1e. Webhook

| Hướng | URL / event | Payload schema | Bên kia là ai | Wave giao |
|---|---|---|---|---|
| | | | | |

### 1f. Tích hợp khác

<!-- File export người dùng tải về, CSV import, cron gọi API bên thứ ba, SDK public, deep link,
     format QR… — mọi thứ có "hình dạng" mà bên ngoài phụ thuộc. -->

| Loại | Format / phiên bản | Ai phụ thuộc | Wave giao |
|---|---|---|---|
| | | | |

---

## 2. Luật đổi từng loại — additive-first

> Bảng tham chiếu, không tick. Đây là thứ khối "chỉ THÊM" trong prompt dev đối chiếu vào.

| Loại | Được làm thẳng | CẤM làm thẳng — muốn thì phải theo cách bên phải |
|---|---|---|
| **API** | Thêm endpoint mới · thêm field **optional** vào response · thêm field optional (có default) vào request | Đổi/xoá field, đổi type/ý nghĩa, đổi URL/status code đang có người gọi → mở **/v2 song song**, giữ v1 tới khi §1a hết người gọi |
| **DB** | Thêm bảng · cột nullable hoặc có default · index | RENAME/DROP/đổi type cột đang dùng → **expand → migrate → wave SAU mới contract**; migration nào cũng phải có đường xuống |
| **Cache** | Thêm field vào shape (reader cũ bỏ qua field lạ) | Đổi shape/ý nghĩa → **nâng version trong key** (`v2:…`) để code mới không đọc nhầm bản cũ; có kế hoạch flush/đợi TTL |
| **Event** | Thêm field optional; consumer viết kiểu tolerant reader | Đổi ngữ nghĩa/type, xoá field → **event-type hoặc topic MỚI**; không tái dùng tên cũ với nghĩa khác |
| **Webhook** | Thêm field vào payload gửi đi | Đổi URL/method/schema mà bên kia đang bám → đường mới + **giữ đường cũ** + báo bên kia trước |
| **Tích hợp khác** | Thêm cột cuối file export, thêm trường mới có default | Đổi format đang có người dùng → tên/phiên bản mới chạy **song song** bản cũ |

---

## 3. Checklist rà mỗi wave

<!-- /next-wave BỎ TICK TOÀN BỘ mục này khi mở wave mới — wave nào rà wave đó.
     Loại không có surface (đã ghi KHÔNG CÓ ở §1) → vẫn tick, thêm "n/a" phía sau.
     Tick nghĩa là "đã rà", không phải "có làm". -->

- [ ] **Sổ hợp đồng §1 cập nhật** — surface mới của wave này đã thêm dòng (kèm cột `Wave giao`); loại chưa có ghi `KHÔNG CÓ`
- [ ] **API**: từng thay đổi đối chiếu §1a — chỉ additive, hoặc đã version hoá theo §2
- [ ] **DB**: migration wave này chỉ expand; mọi đổi/xoá đi hai bước và có đường xuống
- [ ] **Cache**: shape đổi thì key đã nâng version; không còn code mới đọc bản cũ mà thiếu fallback
- [ ] **Event**: chỉ thêm field optional; đổi nghĩa đã tách event-type/topic mới
- [ ] **Webhook**: payload chỉ thêm; URL/schema hai chiều với bên ngoài không đổi
- [ ] **Tích hợp khác**: format export/import/cron/deep-link giữ nguyên hoặc version hoá song song
- [ ] **Regression**: luồng lõi mọi wave trước (`archive/wave-*/DELIVERED.md`) vẫn đi hết được — dogfood đã xác nhận
- [ ] **Phá có chốt**: mọi ngoại lệ ở trên đều được user chốt tường minh + ghi `tracking/decisions.md`

---

## 4. Đã cố tình bỏ qua

<!-- Bỏ qua có chủ đích thì ghi lại kèm rủi ro — đừng để trống mà lờ đi. -->

| Wave | Mục | Vì sao bỏ qua | Rủi ro chấp nhận | Làm lại khi |
|---|---|---|---|---|
| | | | | |
