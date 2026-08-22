---
name: review-web
description: Self-review web frontend — a11y, no biz logic, data layer khớp design, security (XSS/token/secret), coverage, owned_paths.
---

# Review Web Skill

> Checklist source-of-truth cho `review-web-agent` ở `/run-wave`. Fail → ghi `review-findings.md` (review KHÔNG spawn); MAIN spawn fix Mode B → re-review tới `open_findings==0`.

## Lệnh chạy
```bash
npm run -s test -- --coverage     # Vitest + RTL
npm run -s typecheck
npm run -s lint
npx axe-core (hoặc CI a11y job)   # a11y scan
git diff --name-only main...HEAD
# Styling/domain-fidelity (BẮT BUỘC — bắt 'FE trần'):
find src -name "*.css" -o -name "*.scss" | wc -l        # phải > 0 (hoặc tailwind/CSS-in-JS)
grep -rl "className=" src | wc -l                        # số file dùng className
grep -rE -- "--color-|--font-|--space-|theme\." src      # design token (CSS var) theo ux §4 có được dùng?
grep -rE -- "--[a-z-]+:\s" src; grep -rl "design-tokens" src   # token có được ĐỊNH NGHĨA/import trong bundle? (var không định nghĩa = resolve rỗng)
ls tailwind.config.* 2>/dev/null; grep -rl "styled\.\|@emotion\|makeStyles" src   # cơ chế styling khác
```

## Checklist (PASS/FAIL/NA)
- **FEAT/AC (BLOCKER nếu thiếu)**: đọc `FEAT-*` boundary đảm nhận → MỌI AC có màn hình/luồng implement đúng (đối chiếu AC, không chỉ design fidelity).
1. **Build + typecheck + lint** xanh; test ≥ **60%**.
2. **a11y**: axe-core 0 critical (contrast, label, role, focus order).
3. **Data layer khớp design**:
   - REST (default): client gọi đúng endpoint `api-{backend}.md`; type khớp DTO; có interceptor auth.
   - BFF (nếu design có bff): codegen up-to-date (`npm run codegen` no diff); op name khớp `integrations/INTEG-INT-{web}-to-{bff}.md`.
4. **No business logic** trong FE: price/score/eligibility lấy từ BE/BFF, không tự tính.
5. **State handling**: mọi async có loading / error / success (không UI treo khi fail).
6. **Design fidelity (BLOCKER — verify được, KHÔNG đánh giá bằng mắt suông)**: FE phải THỰC SỰ được style theo `ux-{boundary}.md §4 design tokens`, không chỉ markup:
   - **Có cơ chế styling**: tồn tại ≥1 file `.css/.scss` HOẶC tailwind config HOẶC CSS-in-JS (`styled`/`@emotion`/`makeStyles`). **`className` dùng khắp nơi mà 0 stylesheet = FE unstyled (không định dạng) = BLOCKER** (gate `web_styling` ở dev-handoff cũng chặn cứng).
   - **Design token thật**: màu/spacing/typography từ `ux §4` được map thành CSS var (`--color-primary` …) / theme config — KHÔNG hardcode hex/px rải rác, KHÔNG bỏ trống.
   - **Đúng ui-kit đã chốt (ADR ui-kit)**: ADR chọn component library (vd Ant Design) → app phải DÙNG component của library (grep `from 'antd'`...) + token map qua theme (`ConfigProvider`), tự dựng lại Button/Table/Modal thủ công song song = MAJOR; ADR plain-CSS → như dòng dưới.
   - **Token được ĐỊNH NGHĨA trong bundle** (nhánh plain-CSS): `design-tokens.css` được copy vào src / `@import` ở entry (main.tsx/index.css) — dùng `var(--...)` mà token không định nghĩa = var resolve rỗng = UI vẫn unstyled dù grep thấy var (gate `web_styling` chặn) = **BLOCKER**.
   - **Trạng thái visual đủ**: hover/focus cho element tương tác, loading/empty/error có style riêng (không chỉ text trần) — grep `:hover`/`:focus-visible` + component state.
   - **className có backing style**: mỗi class BEM trong markup phải có rule CSS định nghĩa (grep class ↔ CSS); class "mồ côi" (khai báo trong JSX nhưng không có CSS) = MAJOR.
   - **Render proof (khuyến nghị)**: build + serve (hoặc screenshot 1 screen chính) xác nhận trang KHÔNG trắng/không-style; lý tưởng có 1 visual/e2e TC ở registry.
   - **Khớp mockup HTML** (`docs/architecture/ux/mockups/{boundary}/*.html` — SoT về look): app shell/layout/spacing/primitives của app phải bám mockup (mở cả 2 so sánh); responsive breakpoint `ux §3.*`, theming `ux §4.6` nếu spec yêu cầu. Lệch mockup rõ rệt (khung khác, màu khác, thiếu state) = MAJOR.
7. **Security (FE)**:
   - **XSS**: không `dangerouslySetInnerHTML` với data chưa sanitize; không render HTML thô từ input/API.
   - **Token**: không lưu access/refresh token vào `localStorage` (XSS-exfil) — ưu tiên httpOnly cookie / in-memory; không log token.
   - **Auth UI ≠ enforcement**: ẩn/disable theo role chỉ là UX; BE vẫn enforce (không tin client).
   - **No secret in bundle**: không nhúng API secret/private key vào env public/bundle.
   - **Open redirect / link**: URL redirect từ input validate; external link `rel="noopener"`.
   - Dependency không có CVE nghiêm trọng đã biết.
8. **Owned paths** ⊆ boundary.
9. **Cấu trúc khớp `ref-frontend-pattern`** (`pages`/`components`/`hooks`/`api`/`stores`/`router`): đặt sai layout = **BLOCKER**; **folder/file thừa không dùng** (component/hook/util mồ côi, scaffold mẫu còn sót, dead code, import chết, "phòng khi cần") → **MAJOR (yêu cầu xóa)**.

## Anti-patterns cần flag
- `components/` gọi API trực tiếp (phải qua `hooks/` → `api/`).
- Tính tiền/giảm giá ở FE.
- Hardcode role string thay vì đọc `roles[]` từ JWT.
- Bỏ trạng thái error (chỉ render khi success).
- `dangerouslySetInnerHTML` / render HTML từ API chưa sanitize; token trong `localStorage`.
- **FE unstyled — `className` khắp nơi nhưng 0 CSS/tailwind/CSS-in-JS** (render HTML không màu/layout, trái `ux §4`) → BLOCKER. **Đừng đánh "design fidelity pass" nếu chưa grep ra stylesheet + design token.**
- Hardcode hex/px thay vì design token (CSS var) theo `ux §4`.
- Folder/file thừa không dùng (component/hook mồ côi, scaffold mẫu sót, dead code / import chết) — phải xóa, không để lại.



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
**Disable nút KHÔNG tính.** FE chỉ là lớp tiện; ràng buộc thật phải nằm ở BE — FE thiếu chặn là MINOR, BE thiếu chặn là BLOCKER (ghi finding cho boundary BE).

**3. Phân quyền — chỗ hay thủng nhất.**
```bash
grep -rn "fetch(\|axios\.\|useQuery(" --include=*.ts --include=*.tsx src/
```
Mỗi truy vấn lấy bản ghi theo id: **có kèm điều kiện chủ sở hữu / tenant không?** Thiếu là lỗ hổng,
và đây là loại nặng nhất. Đối chiếu `docs/discovery/persona-pool.md` §Ma trận vai × hành động:
mỗi ô `cấm` phải tìm được chỗ chặn ở server.

**4. Lỗi bị nuốt.**
```bash
grep -rn "catch *([a-z]*) *{ *}\|\.catch(() *=> *{ *})" --include=*.ts --include=*.tsx src/
```
`catch` rỗng = lỗi biến mất, người dùng thấy "thành công" trong khi không có gì xảy ra.

**5. Việc dở dang.**
```bash
grep -rn "TODO\|FIXME\|HACK\|XXX" --include=*.ts --include=*.tsx .
```
Cái nào **chặn một AC** → finding. Cái nào là nợ tương lai → ghi chú, không phải finding.

**6. Secret lọt vào code.**
```bash
grep -rnE '(api[_-]?key|secret|password|token)\s*[=:]\s*["'"'"'][A-Za-z0-9_-]{12,}' --include=*.ts --include=*.tsx .
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
