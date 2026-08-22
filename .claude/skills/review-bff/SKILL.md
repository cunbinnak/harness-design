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
