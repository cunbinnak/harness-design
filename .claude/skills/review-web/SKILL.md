---
name: review-web
description: Skill của review-web-agent (chốt review-dev trong /run-wave) — soi web frontend theo 7 trục (AC · bảo mật FE · Forbidden patterns · data layer khớp contract · trạng thái UI + design fidelity · a11y/cấu trúc/test · lệch thứ đã chốt). Mỗi mục có lệnh tìm và chỗ nhìn.
---

# Review Web

Bạn soi code với con mắt độc lập — **bạn không phải người viết nó**, và đó là giá trị của bạn.
Chỉ đọc: hook chặn mọi lần ghi ngoài `tracking/{wave}/review-findings.md` · `tracking/blockers.md` ·
KG learnings. Không hỏi user.

## 1. Nạp trước

| Đọc | Để soi |
|---|---|
| `docs/architecture/feat/FEAT-*.md` boundary đảm nhận + `business-rules/BR-*.md` | trục 1 |
| `ux/ux-{boundary}.md` (states · API · validation · §4 token) · `ux/SCREEN-MAP.md` · `ux/mockups/{boundary}/*.html` · `ux/design-tokens.css` | trục 1, 5 |
| `api/api-{backend}.md` hoặc `integrations/INTEG-INT-{boundary}-to-{bff}.md` | trục 4 |
| `hld/hld-{boundary}.md` §6.1 ca biên | trục 1 |
| `docs/discovery/persona-pool.md` §Ma trận vai × hành động | trục 2 |
| skill `rules-web` §Forbidden patterns + §Done | trục 3, 6 |
| `tracking/decisions.md` · `docs/architecture/adr/ADR-*.md` (ui-kit, state, auth) | trục 7 |
| Wave ≥ 2: `tracking/BC-LEDGER.md` §1 · `archive/wave-*/DELIVERED.md` | trục 7 |

## 2. Phạm vi

Code ở `services/{prefix}-{boundary}/` (repo git riêng — mọi lệnh dưới chạy trong thư mục đó).

- **Vòng 1** — bảng `## Mốc review` của `review-findings.md` chưa có dòng boundary này → soi **cả boundary**.
- **Re-review** — có mốc → soi `git diff --stat <mốc>..HEAD` rồi `git diff <mốc>..HEAD`, và với **mỗi**
  row `resolved` của boundary: mở đúng `file:dòng`, lỗi hết thật chưa. Mốc không còn trong git → soi cả boundary.
- **Cuối lượt** cập nhật mốc = `git rev-parse --short HEAD`, tăng `Vòng`.

## 3. Chạy máy trước — đỏ là finding luôn

```bash
npm run -s typecheck && npm run -s lint && npm run -s build
npm run -s test -- --coverage              # Vitest + RTL — ngưỡng web 60%
npm run codegen && git diff --exit-code    # chỉ khi đi qua BFF: codegen phải không đổi gì
# a11y: app đang chạy → npx @axe-core/cli <url màn chính>; không chạy được → job a11y của CI
```
Đỏ → BLOCKER `type=test`. Coverage < 60% → BLOCKER. axe có critical → BLOCKER.

## 4. Soi theo trục

`grep` chỉ để **tìm chỗ phải đọc** — mọi dòng dưới đây kết thúc bằng mở file ra đọc.

### Trục 1 — Đúng AC

| Kiểm gì | Tìm ở đâu | Nặng |
|---|---|---|
| Mọi AC có màn/luồng làm đúng (không chỉ giống mockup) | AC → màn trong `SCREEN-MAP.md` → mở page + hook, lần tới lời gọi API | không thấy = BLOCKER · làm nửa = MAJOR |
| Validation + thông báo lỗi theo `ux` (field · form · global tách rõ, lỗi nằm gần field) | Đọc form | MAJOR |
| Ca biên `hld §6.1` phía FE: gửi hai lần (disable khi pending) · bản cũ (xử 409) · rỗng. FE chỉ là lớp tiện — BE thiếu chặn thì ghi finding cho **boundary BE** | Đọc mutation + form | FE thiếu = MINOR · BE thiếu = BLOCKER |

### Trục 2 — Bảo mật (phần FE chạm được)

| Nhóm | Kiểm gì | Tìm ở đâu | Nặng |
|---|---|---|---|
| Secret | Không secret trong bundle / env public | `grep -rni -e "VITE_.*secret" -e "NEXT_PUBLIC_.*secret" -e "REACT_APP_.*secret" -e "_PRIVATE" .env* src` · lệnh (a) | BLOCKER |
| | Không log token/PII | `grep -rn -e "console.log" -e "console.debug" src` | token = BLOCKER · khác = MINOR |
| Đầu vào | XSS: không render HTML thô chưa sanitize | `grep -rn -e dangerouslySetInnerHTML -e innerHTML src` | BLOCKER |
| | Validate client không phải chốt chặn duy nhất (giá, số lượng, quyền) | Mỗi form → `api-{backend}.md` có validate phía server không | BE thiếu = BLOCKER (ghi cho BE) |
| | Upload: size · type · extension · preview · progress · error theo `ux` | `grep -rn 'type="file"' src` | MAJOR |
| Danh tính & phân quyền | Token không nằm trong `localStorage`/`sessionStorage` | `grep -rn -e localStorage -e sessionStorage src` → key nào chứa token | BLOCKER |
| | Route cần đăng nhập có guard; role đọc từ `roles[]` claim, không hardcode | File router · `grep -rnE "role *===? *['\"]" src` | MAJOR |
| | Ẩn nút theo role không phải chặn — mỗi ô `cấm` của ma trận có chặn ở BE/BFF | Ô `cấm` → endpoint tương ứng trong `api-{backend}.md` | BE thiếu = BLOCKER (ghi cho BE) |
| | Đăng xuất xoá phiên + cache server-state | `grep -rn -e logout -e signOut src` → có `clear()`/reset store | MAJOR |
| Đường ra | Không hiện lỗi thô (stack, SQL, `error.message` của server) ra UI | `grep -rn -e "rr.message" -e "rror.message" -e ".stack" src/pages src/components` | MAJOR |
| | Open redirect: `?next=`/`?redirect=` chỉ nhận path nội bộ; link ngoài có `rel="noopener noreferrer"` | `grep -rn -e redirect -e returnUrl -e 'target="_blank"' src` | MAJOR |
| Dữ liệu | Không giữ dữ liệu nhạy cảm trong store persist hoặc URL query | `grep -rn -e "persist(" -e createJSONStorage src` | MAJOR |
| Phụ thuộc | Không lib có CVE nghiêm trọng; không thêm lib nặng vì một hàm | `npm audit --omit=dev --audit-level=high` | MAJOR |

```bash
# (a) secret hardcode
grep -rnE "(api[_-]?key|secret|password|private[_-]?key)\s*[:=]\s*[\"'][^\"']{8,}" src
```

### Trục 3 — Forbidden patterns

Mở `rules-web` §Forbidden patterns, đi **TỪNG dòng** bảng. Mỗi dòng tìm được trong code → một finding:
`description` mở bằng `[rules-web Forbidden: <cột Cấm>]`, `hậu quả thật` lấy từ cột `Vì sao` (viết cụ thể
cho chỗ này), `suggested fix` từ cột `Thay bằng`. Lệnh tìm cho các dòng chưa có ở trục 2:

```bash
grep -rn -e "fetch(" -e "axios." src/components src/pages   # UI gọi API trực tiếp
grep -rnE ":\s*any\b|as any|@ts-ignore" src                   # any / ts-ignore
grep -rn -e "console.log" -e debugger src                     # debug sót
grep -rnE "#[0-9a-fA-F]{3,8}\b" src --include=*.css --include=*.scss --include=*.tsx   # hex hardcode (ngoài file token)
grep -rn -A6 "useEffect" src | grep -E "fetch|axios"          # fetch trong effect: dependency đúng chưa
```

### Trục 4 — Data layer và contract

| Kiểm gì | Tìm ở đâu | Nặng |
|---|---|---|
| REST: gọi đúng endpoint/method `api-{backend}.md`; type khớp DTO; không invent field/status/error code; interceptor gắn auth + map lỗi | Đọc `src/api/` so với spec | sai endpoint = BLOCKER · khác = MAJOR |
| BFF: codegen up-to-date; operation khớp `INTEG-INT-{boundary}-to-{bff}.md` | Mục 3 | MAJOR |
| Không nghiệp vụ ở FE: giá/điểm/điều kiện lấy từ BE/BFF | `grep -rni -e price -e total -e discount -e score -e eligib src/components src/hooks` → có phép tính | BLOCKER |
| Server state thống nhất (React Query/SWR/Apollo theo config); query key tập trung; mutation invalidate đúng; rollback khi optimistic | Đọc `hooks/` | MAJOR |
| Pagination/filter/sort theo contract server, không lọc client khi BE đã có | Đọc màn list | MAJOR |
| Debounce search/filter gọi API; không fetch vô hạn | Lệnh trục 3 (useEffect) | MAJOR |

### Trục 5 — Trạng thái UI và design fidelity (kiểm được, không đánh giá bằng mắt suông)

| Kiểm gì | Tìm ở đâu | Nặng |
|---|---|---|
| Mọi màn có data: loading · empty · error · success (· disabled theo quyền) | `grep -rln -e isLoading -e isError -e isPending src/pages` → màn nào không có | MAJOR |
| Action không im lặng; toast không thay field error; hành động xoá/huỷ có confirm; chống double submit | Đọc form + nút | MAJOR |
| Có cơ chế styling: CSS/SCSS, tailwind hoặc CSS-in-JS. `className` khắp nơi mà 0 stylesheet = UI không định dạng (gate `web_styling` cũng chặn) | `find src -name "*.css" -o -name "*.scss"` · `ls tailwind.config.*` · `grep -rl -e "styled." -e "@emotion" src` | BLOCKER |
| Token `ux §4` được **dùng** và được **định nghĩa** trong bundle (`design-tokens.css` import ở entry) — `var(--x)` không định nghĩa resolve rỗng | `grep -rn -e "--color-" -e "--space-" -e "--font-" src` · `grep -rl design-tokens src` | BLOCKER |
| Đúng ui-kit ADR: dùng component của library + map token qua theme; tự dựng lại Button/Table/Modal song song | `grep -rn -e "from 'antd'" -e ConfigProvider src` | MAJOR |
| Mỗi `className` có rule CSS (class mồ côi) | Lấy class trong JSX → grep trong CSS | MAJOR |
| Trạng thái visual: `:hover` · `:focus-visible` · disabled; loading/empty/error có style riêng | `grep -rn -e ":hover" -e ":focus-visible" src` | MAJOR |
| Khớp mockup (khung, spacing, màu, state) + breakpoint `ux §3` + theming §4.6 nếu yêu cầu. Build + serve, mở mockup cạnh app, chụp màn chính — trang trắng/không style là thấy ngay | `docs/architecture/ux/mockups/{boundary}/*.html` | MAJOR |
| Text dài không vỡ layout; không inline style phức tạp | Đọc component list/card | MINOR |

### Trục 6 — a11y, cấu trúc, test

| Kiểm gì | Tìm ở đâu | Nặng |
|---|---|---|
| a11y: contrast · label · role · focus order; semantic HTML; icon button có `aria-label`; modal focus trap + Escape; màu không là tín hiệu duy nhất | axe (mục 3) · `grep -rn "<div[^>]*onClick" src` | critical = BLOCKER · khác = MAJOR |
| Cấu trúc khớp `ref-frontend-pattern` (`pages` · `components` · `hooks` · `api` · `stores` · `router`) | `find src -maxdepth 1 -type d` | lệch = BLOCKER |
| Không file/folder thừa: component/hook mồ côi, scaffold mẫu, import chết | `npx knip` nếu có; không có → grep tên export không ai import | MAJOR |
| Route/storage key/query key/role/status là constant; format ngày/tiền dùng helper chung; text qua i18n nếu project có | `grep -rnE "navigate\(['\"]/" src` | MINOR |
| Test: hành vi người dùng (query theo role/label/text, không className/testId); mock ở network (MSW/MockedProvider); mỗi màn chính có success · loading · error · submit lỗi · permission; không snapshot lớn; sửa bug có regression test | `grep -rn -e getByTestId -e toMatchSnapshot src` | MAJOR |
| Diff chỉ trong `owned_paths` | `git diff --name-only <mốc>..HEAD` | BLOCKER |

### Trục 7 — Lệch thứ đã chốt

| Kiểm gì | Tìm ở đâu | Nặng |
|---|---|---|
| Code làm khác một dòng `tracking/decisions.md` mà không có dòng mới đè lên | Mỗi dòng liên quan boundary → tìm chỗ code | MAJOR |
| Ui-kit / state lib / cách lưu token khác ADR | `package.json` so với ADR | MAJOR |
| Wave ≥ 2: route/URL đã giao vẫn mở được (deep link cũ), không đổi nghĩa màn | Router so với `DELIVERED.md` | BLOCKER |
| Thuật ngữ trên UI lệch FEAT/Glossary | Đọc label | MINOR |

## 5. Ghi finding

Append/cập nhật `tracking/{wave}/review-findings.md` theo `TEMPLATE.review-findings.md`, một row một finding:

```
| RF-NNN | severity | open | {boundary} | path:dòng | type | [nguồn] vấn đề | hậu quả thật | suggested fix |
```

- `[nguồn]`: `[FEAT-X AC-2]` · `[Bảo mật: <nhóm>]` · `[rules-web Forbidden: <cột Cấm>]` · `[ux §4 token]` · `[mockup <màn>]` · `[decisions <ngày>]`.
- **BLOCKER** — AC không chạy · lủng bảo mật · UI không định dạng · lệch cấu trúc · phá surface đã giao.
  **MAJOR** — nên sửa trước bàn giao. **MINOR/NIT** — không chặn. **QUESTION** — chưa chắc.
  Ý thích cá nhân không bao giờ là BLOCKER.
- Row `resolved` vòng trước: mở đúng `file:dòng` xác nhận; còn lỗi → đặt lại `open` + ghi vì sao. KHÔNG xoá row.

## 6. Bốn luật cho mọi finding

1. **Hậu quả thật** — chuyện gì xảy ra với người dùng thật: mất dữ liệu · lộ dữ liệu · sai kết quả · AC
   không chạy · wave trước gãy. Viết không nổi câu này thì không phải finding.
2. **Trục sạch thì nói sạch** — ghi thẳng "trục N sạch" trong phần trả về; đừng bịa nhận xét cho có.
3. **Mở file ra đọc** — `file:dòng` phải là dòng đã đọc thật; không suy từ tên hàm.
4. **Không chắc → `QUESTION`**, cột `suggested fix` ghi **cách kiểm chứng**.

Không góp ý: đặt tên cho đẹp · tách file cho gọn · trừu tượng hoá "để sau dễ mở rộng" · tối ưu khi chưa có số đo.

## 7. Kết luận

- `review_result = pass` chỉ khi: không còn row BLOCKER/MAJOR `open` của boundary · typecheck/lint/build/test
  xanh · coverage ≥ 60% · axe 0 critical.
- Không spawn fix, không tự loop — phiên chính đọc findings, spawn fix, rồi gọi bạn re-review. Gate
  `no_open_findings` chặn complete.
- Field JSON trả về theo prompt spawn (`build_prompt.py`) — skill không định nghĩa schema.
