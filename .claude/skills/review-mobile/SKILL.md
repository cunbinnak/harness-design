---
name: review-mobile
description: Self-review mobile — analyze, data layer khớp design, offline idempotency, security (secure storage/transport/deeplink), no hardcoded keys, coverage.
---

# Review Mobile Skill

> Checklist source-of-truth cho `review-mobile-agent` ở `/run-wave`. Fail → ghi `review-findings.md` (review KHÔNG spawn); MAIN spawn fix Mode B → re-review tới `open_findings==0`.

## Lệnh chạy
```bash
flutter analyze                   # static analysis
flutter test --coverage          # widget test + coverage
git diff --name-only main...HEAD
```

## Checklist (PASS/FAIL/NA)
- **FEAT/AC (BLOCKER nếu thiếu)**: đọc `FEAT-*` boundary đảm nhận → MỌI AC có màn hình/luồng implement đúng.
1. **Build + analyze** xanh (`flutter analyze` 0 error); test ≥ **60%**.
2. **Data layer khớp design**:
   - REST (default): client (Dio/http) gọi đúng `api-{backend}.md`; interceptor auth.
   - BFF (nếu có): codegen up-to-date (`build_runner`); op khớp `integrations/INTEG-INT-{mobile}-to-{bff}.md`.
3. **Offline queue**: mọi mutation "queue if offline" có idempotency strategy (key/dedup) — FAIL nếu retry gây double-write.
4. **No business logic** — validate ở BE/BFF.
5. **No hardcoded secrets**: FCM key, biometric data không persist/hardcode.
6. **State**: provider scope đúng (Riverpod), không global state rò rỉ giữa screen.
7. **Security (mobile)**:
   - **Token storage**: access/refresh token + dữ liệu nhạy cảm vào secure storage (Keychain/Keystore), KHÔNG `SharedPreferences` plain.
   - **Transport**: chỉ HTTPS; cert pinning cho API nhạy cảm (nếu yêu cầu).
   - **Deeplink / WebView**: validate input từ deeplink/intent; WebView không load URL không tin, tắt JS nếu không cần.
   - **No secret in bundle**: không hardcode API key/secret trong code/asset; bật obfuscation nếu yêu cầu.
   - **Logging**: không in token/PII ra log.
8. **Owned paths** ⊆ boundary.

## Anti-patterns cần flag
- Mutation offline retry không idempotent → tạo bản ghi trùng.
- Lưu token/biometric vào SharedPreferences plain (phải secure storage).
- Widget gọi API trực tiếp thay vì qua repository/provider.
- WebView load URL không tin / nhận deeplink không validate; hardcode API key trong asset.



## Lăng kính thứ hai: TRUY — code có làm đúng thứ tài liệu đã chốt không

Phần checklist ở trên là lăng kính **SOI** (code có sạch, có an toàn không). Lăng kính này khác hẳn:
**đi từ TÀI LIỆU xuống code**, không đi từ code lên. Hai lăng kính bắt hai loại lỗi khác nhau — code
sạch bong vẫn có thể thiếu hẳn một AC, và không mục nào ở trên bắt được điều đó.

Đây là **quy trình**, không phải lời dặn: làm đủ sáu bước, mỗi bước ra finding hoặc ra câu
"bước này sạch".

**1. Đi từng AC một.** Liệt kê AC của mọi `FEAT-*` boundary này đảm nhận. Với **mỗi** AC: tìm đoạn
code hiện thực nó. Ba kết quả, ba xử lý khác nhau:
`có và đúng` → sạch · `có nhưng chỉ làm một nửa` (thiếu nhánh lỗi/validation) → **MAJOR** ·
`không tìm thấy` → **BLOCKER**. **Không suy từ tên hàm** — `validateOrder` không chứng minh nó
validate AC nào; mở file ra đọc.

**2. Ca biên `hld-{boundary}.md` §6.1.** Mỗi dòng đã quyết (gửi hai lần · sửa đồng thời · xoá ·
sai thứ tự · hỏng nửa chừng · bản cũ · rỗng · thu hồi quyền) — tìm chỗ code chặn nó.
**Không tìm thấy nghĩa là CHƯA XỬ**, dù chạy thử trông vẫn ổn: ca biên chỉ nổ khi trùng thời điểm.
**Disable nút KHÔNG tính.** Ràng buộc thật ở BE; app chỉ hiển thị.

**3. Phân quyền — chỗ hay thủng nhất.**
```bash
grep -rn "\.doc(\|findById\|where(" --include=*.dart lib/
```
Mỗi truy vấn lấy bản ghi theo id: **có kèm điều kiện chủ sở hữu / tenant không?** Thiếu là lỗ hổng,
và đây là loại nặng nhất. Đối chiếu `docs/discovery/persona-pool.md` §Ma trận vai × hành động:
mỗi ô `cấm` phải tìm được chỗ chặn ở server.

**4. Lỗi bị nuốt.**
```bash
grep -rn "catch *([a-z]*) *{ *}\|on .* catch.*{ *}" --include=*.dart lib/
```
`catch` rỗng = lỗi biến mất, người dùng thấy "thành công" trong khi không có gì xảy ra.

**5. Việc dở dang.**
```bash
grep -rn "TODO\|FIXME\|HACK\|XXX" --include=*.dart .
```
Cái nào **chặn một AC** → finding. Cái nào là nợ tương lai → ghi chú, không phải finding.

**6. Secret lọt vào code.**
```bash
grep -rnE '(api[_-]?key|secret|password|token)\s*[=:]\s*["'"'"'][A-Za-z0-9_-]{12,}' --include=*.dart .
```

> Sáu bước này **không thay** checklist ở trên — chúng chạy song song. Checklist hỏi *"code này có
> vấn đề gì"*; sáu bước hỏi *"thứ đã hứa có ở đây không"*. Bỏ lăng kính thứ hai thì một FEAT thiếu
> hẳn vẫn qua được review sạch bong.

## Kỷ luật khi review — bốn luật, áp cho MỌI finding

**1. Mỗi finding phải nói được HẬU QUẢ THẬT.** Không phải "vi phạm mục X", mà *chuyện gì xảy ra
với người dùng thật*: mất dữ liệu · lộ dữ liệu · sai kết quả · AC không chạy được · wave trước gãy.
**Viết không nổi câu hậu quả thì đó không phải finding** — đó là ý thích. Luật này thay cho một
danh sách cấm dài: nó tự loại nhận xét vặt (đặt tên cho đẹp hơn, tách file cho gọn, trừu tượng hoá
"để sau dễ mở rộng") mà không cần liệt kê từng loại.

**2. Trục nào sạch thì NÓI SẠCH.** Soi hết một mục mà không thấy gì đáng nêu → ghi thẳng
"mục này ổn". **Đừng bịa một nhận xét cho có** để báo cáo trông chăm chỉ. Findings rác làm loãng
findings thật, và người đọc sẽ bắt đầu bỏ qua cả danh sách.

**3. MỞ FILE RA ĐỌC, đừng suy từ tên.** Tên hàm `validateOrder` không chứng minh nó validate gì.
Mọi finding phải chỉ được `file:dòng` cụ thể, và dòng đó phải đã được đọc thật.

**4. Không chắc thì NÓI không chắc, kèm cách kiểm chứng.** `severity: QUESTION` + một câu
"kiểm bằng cách nào". Đoán bừa làm MAIN mất thời gian đuổi theo thứ không tồn tại — đắt hơn hẳn
việc bỏ sót một finding nhỏ.

## Trục dễ quên: LỆCH THỨ ĐÃ CHỐT

Ngoài "code có đúng spec không", soi thêm **code có đi ngược quyết định đã ghi không**:

- `tracking/decisions.md` — code làm khác một dòng quyết định mà **không có dòng mới đè lên**
  (`Ghi chú: thay cho <ngày>`). Đổi ý thì được, đổi lặng lẽ thì không.
- `docs/architecture/adr/ADR-*.md` — dùng thư viện/kiểu kiến trúc khác ADR đã chốt.
- `hld-{boundary}.md` §6.1 — ca biên đã quyết mà code không chặn. **Chặn ở UI KHÔNG tính**:
  phải có ràng buộc ở DB hoặc kiểm ở tầng server.
- `archive/wave-*/DELIVERED.md` — surface wave trước bị đổi/xoá thay vì chỉ thêm vào.

Đây là loại lệch mà mọi checklist kỹ thuật ở trên đều mù, vì code trông vẫn "đúng chuẩn".

## Output
RETURN SCHEMA: `review_result`, `no_open_findings`, `findings_file`, `coverage_pct`, `checklist_summary`, `needs_review[]`.
