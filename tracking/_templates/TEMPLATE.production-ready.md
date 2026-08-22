---
type: production-ready
scope: cross-wave
---

# Sẵn sàng vận hành — {{PROJECT}}

> Thứ phân biệt "sản phẩm chạy được" với "đồ dựng xong rồi vứt". Harness gác rất chặt *code có
> đúng thiết kế không*; file này hỏi *cái này vận hành được chưa*.

**Mục gắn `(sau môi trường thật)` chỉ làm được khi đã có nơi chạy thật** — không có hosting thì
không bật được backup, không có lượt dùng thì không đo được gì. Harness dừng ở `/next-wave`, chưa
có bước deploy, nên gate **không đếm** những mục này. Chúng vẫn phải nằm đây để không ai quên.

**Mục gắn `(mỗi wave)` phải kiểm LẠI mỗi wave** — chúng đúng cho tính năng wave trước, không tự
đúng cho tính năng wave này (đầu vào mới cần validate mới, hành động mới cần thử phân quyền mới).
`/next-wave` tự bỏ tick khi mở wave; mục hạ tầng giữ nguyên.

| Gate | Chạy ở | Đòi gì |
|---|---|---|
| `production_ready` | `/next-wave` | Mọi mục **không** gắn `(sau môi trường thật)`, đếm **theo từng nhóm** + khối Rollback đã điền |

Cách làm từng mục theo stack: `.claude/skills/rules-{kind}/SKILL.md`.

---

## Nhóm 1 — Nền kỹ thuật

- [ ] **Secret tách khỏi code** `(mỗi wave)` — không key nào trong repo; `.env` trong `.gitignore`; `.env.example` liệt kê đủ tên biến
      **Kiểm**: `git log -p | grep -iE '(api[_-]?key|secret|password|token)\s*=\s*["\x27][A-Za-z0-9]'` không ra gì
- [ ] **Migration có version + có đường xuống** `(mỗi wave)` — schema đổi bằng file đánh số, không sửa tay
      **Kiểm**: cộng-trước-xoá-sau — thêm cột mới → deploy code dùng cột mới → wave sau mới xoá cột cũ. Làm vậy mới rollback được
- [ ] **Health check** phân biệt *sống* và *sẵn sàng nhận việc*
      **Kiểm**: `curl -s $APP/health/ready` trả 200 kèm trạng thái DB; tắt DB → chuyển sang đỏ
- [ ] **Error tracking** — lỗi tự báo về một nơi, không chờ người dùng kêu
      **Kiểm**: cố tình ném một lỗi, thấy nó xuất hiện ở nơi gom lỗi
- [ ] **Structured log** — JSON có timestamp + mức + `traceId` xuyên request; che dữ liệu nhạy cảm
      **Kiểm**: lấy một `traceId` từ log, lần lại được đủ chặng của một request
- [ ] **Backup DB + ĐÃ THỬ KHÔI PHỤC một lần** `(sau môi trường thật)`
      **Kiểm**: khôi phục vào DB rỗng, đếm bản ghi khớp

## Nhóm 2 — Auth + bảo mật

- [ ] **Đăng nhập dùng thư viện/dịch vụ có sẵn**, không tự viết (trừ khi `PROJECT.md` chốt là không cần đăng nhập)
- [ ] **Validate đầu vào Ở SERVER** `(mỗi wave)` — mọi dữ liệu từ ngoài đều qua schema; không tin client
      **Kiểm**: gửi thẳng request thiếu/sai kiểu bằng curl, bỏ qua UI → server phải từ chối
- [ ] **Phân quyền enforce ở server** `(mỗi wave)` — mọi ô `cấm` trong ma trận vai × hành động ở `persona-pool.md` có ca kiểm âm
      **Kiểm**: đăng nhập A, gọi tài nguyên của B → 403. **Chặn ở UI không tính**
- [ ] **Rate limit** `(mỗi wave)` — ít nhất cho đăng nhập và endpoint ghi dữ liệu
      **Kiểm**: bắn quá ngưỡng → 429, không phải 500
- [ ] **HTTPS** `(sau môi trường thật)` — redirect http → https
- [ ] **Vòng lặp credential** — hết hạn, xoay, thu hồi có hiệu lực ngay
      **Kiểm**: thu hồi một token đang dùng → request kế tiếp bị từ chối

## Nhóm 3 — CI/CD + test tối thiểu

- [ ] **Build + lint + test chạy tự động** trên mỗi thay đổi, đỏ thì chặn `(mỗi wave)`
- [ ] **Smoke test luồng lõi** `(mỗi wave)` — gồm luồng của **mọi wave trước** (`archive/wave-*/DELIVERED.md`), giữ XANH
      **Kiểm**: đây là hàng rào chống wave sau đạp lên wave trước
- [ ] **Test luồng tiền/dữ liệu quan trọng** `(mỗi wave)` — chỗ nào sai là mất tiền hoặc mất dữ liệu
- [ ] **Push là deploy** `(sau môi trường thật)`

Không đặt mục tiêu coverage %. Test đúng chỗ quan trọng, không test cho đủ số. (Nguyên tắc, không phải mục phải tick.)

## Nhóm 4 — Đo phản ứng

> Nhóm này đóng vòng với `docs/discovery/hypothesis-log.md`: giả thuyết ghi ở D0 **chỉ chuyển được**
> từ `TESTABLE` sang `PROVEN`/`DISPROVEN` khi có số ở đây. Không có nhóm 4 thì sổ giả thuyết là
> danh sách phỏng đoán không ai đối chứng.

- [ ] **Ngưỡng quyết định** `(mỗi wave)` — đã ghi rõ **con số** nào thì làm tiếp, số nào thì đổi hướng, số nào thì dừng (nguồn: `hypothesis-log.md`)
- [ ] **Event tracking** `(mỗi wave)` — hành vi then chốt (đăng ký, hoàn tất luồng lõi, quay lại) đều bắn event; tên event khớp giả thuyết đang đo
- [ ] **Kênh feedback** — người dùng phản hồi được ngay trong sản phẩm
- [ ] **Đang đếm thật** `(sau môi trường thật)` — có lượt truy cập + nguồn đến

---

## Rollback

> Điền TRƯỚC khi giao. Lúc hệ hỏng không ai còn bình tĩnh đọc tài liệu dài. Gate đếm chỗ chưa điền.

```
Lệnh rollback   : _CHƯA ĐIỀN_
Mất bao lâu     : _CHƯA ĐIỀN_
Dữ liệu thì sao : _CHƯA ĐIỀN_   (migration có đường xuống không)
Ai bấm          : _CHƯA ĐIỀN_
```

## Đã cố tình bỏ qua

> Mục nào cố tình không làm thì ghi vào đây kèm **điều kiện làm lại** rồi mới tick — đừng để trống
> mà lờ đi. Cột "Làm lại khi" là thứ phân biệt *hoãn* với *bỏ*.

| Wave | Mục | Vì sao bỏ qua | Làm lại khi |
|---|---|---|---|
| | | | |
