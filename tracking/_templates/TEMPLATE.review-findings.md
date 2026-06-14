# Review Findings — wave-{N}

> **Mỗi finding = 1 HÀNG.** Sản phẩm của `/review-dev` (review-{kind}-agent ghi). Đây là "cần sửa gì, ở đâu" để **MAIN** spawn fix Mode B — KHÔNG phải bug test/UAT (đó là `bugs.md`).
> Vòng đời: review **append/cập nhật** row → MAIN spawn fix theo row → fix sửa code, set `status` = `resolved` → review re-review xác nhận.
> Gate `no_open_findings` chặn `/review-dev complete` khi còn row `severity ∈ {BLOCKER, MAJOR}` mà `status = open` → ép fix sạch trước khi rời REVIEW_DEV.
>
> Enum — severity: `BLOCKER | MAJOR | MINOR | NIT | QUESTION` · status: `open | resolved | accepted | wontfix` · type: `rule | BR | AC | arch | security | test | other`.
> `MINOR/NIT/QUESTION` không chặn gate (reviewer set `accepted`/`wontfix` nếu không sửa). Chỉ `BLOCKER/MAJOR` còn `open` mới chặn.
> Map `severity` ↔ bug `sev` ↔ TC `pri`: xem `docs/architecture/SEVERITY-TEST-TAXONOMY.md` §2.

| FINDING | severity | status | boundary | file | type | description | suggested fix |
|---------|----------|--------|----------|------|------|-------------|---------------|
| RF-001 | BLOCKER | resolved | order | OrderService.java:42 | BR | BR-ORDER-001 (không cho đặt khi out-of-stock) chưa enforce trước khi save | check tồn kho trước `repo.save()`; ném `OUT_OF_STOCK` |
| RF-002 | MAJOR | open | order | OrderController.java:88 | arch | business logic (tính total) nằm trong controller | chuyển sang `OrderService.calculateTotal()` |
| RF-003 | MINOR | accepted | order | OrderMapper.java | rule | tên method map chưa theo convention | _(chấp nhận — không chặn)_ |

## Notes
- **ID** `RF-NNN` đánh số tăng dần trong wave (không reset theo boundary).
- **file** ghi `path:line` khi xác định được dòng — giúp fix nhắm đúng chỗ, không quét cả file.
- **type**: `rule` (convention `rules-{kind}`) · `BR`/`AC` (FEAT) · `arch` (layer/structure) · `security` · `test` (coverage/thiếu test) · `other`.
- Fix Mode B (spawn bởi MAIN) đọc các row `status=open` của boundary → sửa → set `status=resolved`. KHÔNG đụng row `accepted`/`wontfix`.
- File này **ephemeral theo wave** (pre-handoff), khác `bugs.md` (bug auto/manual từ test-execute/UAT, sống tới end-wave).
