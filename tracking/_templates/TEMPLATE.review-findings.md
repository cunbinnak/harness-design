# Review Findings — wave-{N}

> **Mỗi finding = 1 HÀNG.** Sản phẩm của `review-dev` (review-{kind}-agent ghi). Đây là "cần sửa gì, ở đâu" để **MAIN** spawn fix Mode B — KHÔNG phải kết quả test (đó là `test-report.md`) hay phát hiện dùng thử (đó là `dogfood-report.md` §2).
> Vòng đời: review **append/cập nhật** row → MAIN spawn fix theo row → fix sửa code, set `status` = `resolved` → review re-review xác nhận.
> Gate `no_open_findings` chặn `review-dev complete` khi còn row `severity ∈ {BLOCKER, MAJOR}` mà `status = open` → ép fix sạch trước khi rời REVIEW_DEV.
>
> Enum — severity: `BLOCKER | MAJOR | MINOR | NIT | QUESTION` · status: `open | resolved | accepted | wontfix` · type: `rule | BR | AC | arch | security | test | other`.
> `MINOR/NIT/QUESTION` không chặn gate (reviewer set `accepted`/`wontfix` nếu không sửa). Chỉ `BLOCKER/MAJOR` còn `open` mới chặn.
> Map `severity` ↔ ô `Xử` của dogfood ↔ TC `pri`: xem `docs/architecture/SEVERITY-TEST-TAXONOMY.md` §2.

| FINDING | severity | status | boundary | file | type | description | hậu quả thật | suggested fix |
|---------|----------|--------|----------|------|------|-------------|--------------|---------------|
| RF-001 | BLOCKER | resolved | order | OrderService.java:42 | BR | BR-ORDER-001 (không cho đặt khi hết hàng) chưa enforce trước khi save | khách đặt được món đã hết → đơn treo, phải gọi xin lỗi và hoàn tiền | check tồn kho trước `repo.save()`; ném `OUT_OF_STOCK` |
| RF-002 | MAJOR | open | order | OrderController.java:88 | arch | logic tính tiền nằm trong controller | job/consumer gọi đường khác sẽ tính ra số tiền KHÁC — lệch tiền giữa hai đường | chuyển sang `OrderService.calculateTotal()` |
| RF-003 | QUESTION | open | order | OrderRepo.java:31 | security | truy vấn theo id, chưa thấy điều kiện chủ sở hữu | **chưa chắc** — nếu đúng thì user A đọc được đơn của user B | kiểm bằng: gọi API bằng token A với id đơn của B, xem có trả 200 không |

## Notes
- **ID** `RF-NNN` đánh số tăng dần trong wave (không reset theo boundary).
- **file** ghi `path:line` khi xác định được dòng — giúp fix nhắm đúng chỗ, không quét cả file.
- **hậu quả thật** — cột QUAN TRỌNG NHẤT: *chuyện gì xảy ra với người dùng thật* (mất dữ liệu ·
  lộ dữ liệu · sai kết quả · AC không chạy · wave trước gãy). **Viết không nổi câu này thì không
  phải finding** — đó là ý thích. Cột này thay cho một danh sách cấm dài: nó tự loại nhận xét vặt.
- **không chắc** → `severity: QUESTION` + cột `suggested fix` ghi **cách kiểm chứng**, không phải
  cách sửa. Đoán bừa làm MAIN đuổi theo thứ không tồn tại, đắt hơn bỏ sót một finding nhỏ.
- **type**: `rule` (convention `rules-{kind}`) · `BR`/`AC` (FEAT) · `arch` (layer/structure) · `security` · `test` (coverage/thiếu test) · `other`.
- Fix Mode B (spawn bởi MAIN) đọc các row `status=open` của boundary → sửa → set `status=resolved`. KHÔNG đụng row `accepted`/`wontfix`.
- File này **sống theo wave** (trước bàn giao): rà sạch thì đóng, không mang sang wave sau. Khác `test-report.md` (kết quả TC, máy chạy ra) và `dogfood-report.md` (phát hiện + quyết định xử). Ba sổ, ba loại sự thật, không chỗ nào chép chỗ nào.
