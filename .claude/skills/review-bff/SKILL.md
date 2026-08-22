---
name: review-bff
description: Self-review BFF — schema additive, DataLoader (no N+1), cache keys, error mapping, security (auth context/query cost/DoS), owned_paths.
---

# Review BFF Skill

> Checklist source-of-truth cho `review-bff-agent` ở `/run-wave`. Fail → ghi `review-findings.md` (review KHÔNG spawn); MAIN spawn fix Mode B → re-review tới `open_findings==0`.

## Lệnh chạy
```bash
npm run -s test -- --coverage     # Vitest + coverage
npm run -s typecheck              # tsc --noEmit
npm run -s schema:check           # validate SDL + so diff vs main (additive)
git diff --name-only main...HEAD
```

## Checklist (PASS/FAIL/NA)
- **FEAT/AC (BLOCKER nếu thiếu)**: đọc `FEAT-*` boundary đảm nhận → MỌI AC cần data đều có resolver/field phục vụ đúng.
1. **Build + typecheck** xanh; test ≥ **70%**.
2. **Schema additive**: diff SDL vs `main` chỉ thêm field/type hoặc `@deprecated`; KHÔNG remove/rename breaking.
3. **DataLoader**: mọi resolver có quan hệ → field dùng loader batch; KHÔNG gọi backend trong vòng lặp (kiểm N+1 qua log/trace test).
4. **Cache key**: data nhạy cảm có prefix `userId`/`tenantId`. FAIL nếu cache global cho per-user data.
5. **Error mapping**: HTTP backend → `extensions.code` enum đúng (`UNAUTHENTICATED`/`FORBIDDEN`/`BAD_USER_INPUT`/`INTERNAL`), khớp `integrations/INTEG-INT-{bff}-to-*.md`.
6. **No business logic**: resolver chỉ orchestrate + shape; tính toán nghiệp vụ phải ở backend.
7. **Security (GraphQL gateway)**:
   - **Auth context**: verify token ở gateway; forward identity an toàn xuống backend — client KHÔNG override `userId`/`tenantId`/role.
   - **Query cost / DoS**: có depth + complexity limit + pagination; introspection tắt ở prod; schema không expose field nhạy cảm.
   - **Injection passthrough**: arg truyền xuống backend được validate; không nối raw input vào downstream query/URL.
   - **Error**: không leak stack/internal (đã ở mục 5); rate limit per user/tenant.
8. **No secrets**; **Owned paths** ⊆ boundary; **KG** appended (ops + loaders + cache keys).

## Anti-patterns cần flag
- Resolver `Promise.all` map gọi REST từng item thay vì DataLoader.
- Trả nguyên error backend ra client (leak stack/internal).
- Cache response chứa field theo role mà key không gồm role/user.
- Tin `userId`/`tenantId` từ GraphQL args thay vì context; introspection bật ở prod; không depth/complexity limit.



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
Kiểm ở **resolver/service**, không phải ở client.

**3. Phân quyền — chỗ hay thủng nhất.**
```bash
grep -rn "findUnique\|findFirst\|findById\|\.where(" --include=*.ts src/
```
Mỗi truy vấn lấy bản ghi theo id: **có kèm điều kiện chủ sở hữu / tenant không?** Thiếu là lỗ hổng,
và đây là loại nặng nhất. Đối chiếu `docs/discovery/persona-pool.md` §Ma trận vai × hành động:
mỗi ô `cấm` phải tìm được chỗ chặn ở server.

**4. Lỗi bị nuốt.**
```bash
grep -rn "catch *([a-z]*) *{ *}\|\.catch(() *=> *{ *})" --include=*.ts src/
```
`catch` rỗng = lỗi biến mất, người dùng thấy "thành công" trong khi không có gì xảy ra.

**5. Việc dở dang.**
```bash
grep -rn "TODO\|FIXME\|HACK\|XXX" --include=*.ts --include=*.js .
```
Cái nào **chặn một AC** → finding. Cái nào là nợ tương lai → ghi chú, không phải finding.

**6. Secret lọt vào code.**
```bash
grep -rnE '(api[_-]?key|secret|password|token)\s*[=:]\s*["'"'"'][A-Za-z0-9_-]{12,}' --include=*.ts --include=*.js .
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
