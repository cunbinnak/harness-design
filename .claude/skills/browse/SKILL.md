---
name: browse
description: >
  Skill của 6 dogfood-{vai}-agent + test-execute-agent (chốt cuối /run-wave và chốt chạy test) —
  mở trình duyệt THẬT trên hệ đang chạy: bấm, gõ, chụp màn, đọc lỗi console + lời gọi mạng, và ĐO
  computed style để đối chiếu design token. Chạy bằng Playwright MCP khai inline trong frontmatter
  từng vai nên mỗi vai một trình duyệt riêng. Gồm: cách gọi, hai chỗ dễ vấp, công thức cho từng
  lăng kính (màn nhỏ · mạng lỗi · bấm hai lần · nhập bậy · đo hình thức), và cách chứng minh đã
  dùng thật.
---

# browse — mở trình duyệt để dùng thật

> Bộ khung có gate đòi **screenshot thật** (`test_evidence`), đòi **computed style khớp token**
> (`web_styling`), đòi vai `picky` **đo chứ không nhìn**. Skill này là **cách làm** những việc đó.
> Đọc code rồi suy ra "chắc chạy được" **không tính** — và `dogfood_done` có mục *Dấu hiệu dogfood
> giả* để bắt đúng chuyện này.

## 1. Chạy bằng gì

Playwright MCP (`@playwright/mcp` — bản chính chủ). Khai ở hai nơi:

| Nơi khai | Dùng cho | Kiểu |
|---|---|---|
| `.mcp.json` gốc repo | phiên chính (MAIN tự tay dùng) | dùng chung cả phiên |
| `mcpServers` trong frontmatter mỗi `dogfood-*-agent` | 6 lăng kính | **inline — mỗi vai một trình duyệt riêng** |

Khai inline **có chủ ý**: server inline bật khi sub-agent bắt đầu, tắt khi nó xong, nên các vai
không giẫm chân nhau. Trỏ chung một server thì chúng tranh nhau một tab — vai này bấm, vai kia mất
trang đang nhìn.

> Trình duyệt riêng **KHÔNG** làm dữ liệu riêng. Service và DB vẫn dùng chung, nên vai ghi dữ liệu
> vẫn đè lên cảnh vai khác đang xem. Đó chính là lý do `/dogfood` chạy **hai đợt, mỗi đợt tối đa 3
> vai** — không phải cả 6 cùng lúc. Đợt 1 cần **DB sạch**: trạng thái rỗng chết ngay khi có bản ghi
> đầu tiên.

Không cần cài trước. Lần đầu npm tải gói + Playwright tải Chromium (vài trăm MB, một lần).

## 2. Bốn tool dùng nhiều nhất

| Tool | Việc |
|---|---|
| `browser_navigate` | Mở URL. **Luôn vào từ trang đầu**, không nhảy thẳng vào URL bên trong |
| `browser_snapshot` | Đọc trang dạng cây accessibility — đây là "nhìn màn hình". Gọi sau MỖI thao tác |
| `browser_click` · `browser_type` · `browser_fill_form` | Bấm và gõ |
| `browser_take_screenshot` | Bằng chứng cho báo cáo, và là cách bắt lỗi bố cục |

**Hai chỗ dễ vấp:**

1. `browser_click` / `browser_type` nhận **`target`**, không phải `ref`. `target` ăn cả ref từ
   snapshot (`e4`) lẫn CSS selector (`#submit`, `button[type=submit]`) — selector thường nhanh hơn
   vì khỏi snapshot trước. Trường `element` chỉ là mô tả cho người đọc.
2. `browser_navigate` **không trả nội dung trang** — nó ghi ra `.playwright-mcp/page-*.yml` rồi trả
   đường dẫn. Muốn thấy trang thì `Read` file đó, hoặc gọi thẳng `browser_snapshot` (tool này trả
   inline).

Còn lại: `browser_resize` · `browser_press_key` · `browser_navigate_back` · `browser_tabs` ·
`browser_hover` · `browser_select_option` · `browser_file_upload` · `browser_handle_dialog` ·
`browser_wait_for` · `browser_console_messages` · `browser_network_requests` · `browser_evaluate` ·
`browser_run_code_unsafe` · `browser_close`.

> **`browser_snapshot` hơn `browser_take_screenshot` khi cần biết trang CÓ GÌ** — nó trả text đọc
> được kèm ref để bấm, không phải ảnh phải đoán. Screenshot là để LƯU BẰNG CHỨNG, không phải để đọc.

## 3. Công thức theo lăng kính

### `mobile` — màn hình nhỏ
```
browser_resize  width=390 height=844     # điện thoại
browser_resize  width=360 height=640     # máy nhỏ
browser_resize  width=844 height=390     # xoay ngang
```

### `edge` — mạng lỗi, cảnh rỗng, phụ thuộc chết
```js
await page.context().setOffline(true);                    // mất mạng
await page.route('**/api/**', r => r.abort());            // chặn API, xem UI hiện gì
const c = await page.context().newCDPSession(page);       // mạng chậm
await c.send('Network.emulateNetworkConditions',
  { offline:false, latency:400, downloadThroughput:400*1024/8, uploadThroughput:400*1024/8 });
```
Rồi `browser_console_messages` + `browser_network_requests` xem lỗi THẬT là gì. Đối chiếu
`hld-{boundary}.md §9` (phụ thuộc ngoài hỏng → hệ làm gì) — code phải làm đúng như đã khai.

### `rushed` — bấm hai lần, nhiều tab, nút quay lại
```js
await Promise.all([ page.click('#submit'), page.click('#submit') ]);   // hai lần trong ~50ms
```
Tay người không bấm được nhanh vậy, nhưng **mạng lag thì có**. Đây là ca biên `gửi hai lần` ở
`hld §6.1` — kiểm xem có ra hai bản ghi không. `browser_tabs` mở tab thứ hai cùng trang ·
`browser_navigate_back` cho nút quay lại.

### `breaker` — nhập bậy + phân quyền
`browser_type` với: chuỗi 10.000 ký tự · emoji · `<script>alert(1)</script>` ·
`'; DROP TABLE x;--` · số âm · ngày 30/02.
Sau mỗi lần: `browser_snapshot` (có hiện ra **như chữ thường** không) · `browser_console_messages` ·
`browser_network_requests` (server trả mã gì — 400 hay 500?).

**Phép thử phân quyền A↛B** — chạy đủ mọi ô `cấm` trong `persona-pool.md` §Ma trận vai × hành động:
đăng nhập A tạo bản ghi → `browser_navigate` tới URL bản ghi đó **khi đang là B** → phải bị chặn.
Chặn ở UI không tính: xem `browser_network_requests`, server phải trả 403.

### `newbie` — người mới
Không tool đặc biệt. `browser_navigate` vào trang đầu rồi `browser_snapshot` — và **đọc như người
chưa biết gì**. Đừng dùng kiến thức về code để đoán ra cách dùng; **mất vai là mất giá trị lượt thử**.

### `picky` — ĐO, không nhìn

Đây là chỗ gate `web_styling` + `design_system_closed` đòi bằng chứng. `browser_evaluate` gom giá
trị **thật đang render**:

```js
() => {
  const seen = new Map();                        // "prop|giá trị" → selector đầu tiên gặp
  for (const el of document.querySelectorAll('*')) {
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;          // bỏ phần tử không hiển thị
    const cs = getComputedStyle(el);
    const sel = el.tagName.toLowerCase()
      + (el.id ? '#' + el.id : '')
      + (el.className && typeof el.className === 'string'
         ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : '');
    for (const p of ['color','background-color','border-color','font-family',
                     'font-size','padding','gap','border-radius','box-shadow']) {
      const v = cs.getPropertyValue(p);
      if (!v || v === 'none' || v === 'rgba(0, 0, 0, 0)' || v === '0px') continue;
      const k = p + '|' + v;
      if (!seen.has(k)) seen.set(k, sel);
    }
  }
  return [...seen].map(([k, sel]) => k + ' @ ' + sel).sort();
}
```

Trả về **tập giá trị thật + selector đầu tiên dùng nó** — đối chiếu thẳng với
`docs/architecture/ux/design-tokens.css`. Giá trị nào không có trong bảng token là **phát hiện**,
kèm selector nên fix biết sửa ở đâu.

Tương phản thì đọc đúng cặp chữ/nền của phần tử đang nghi — **phải leo lên tới tổ tiên có nền đục**,
vì nền trong suốt không phải nền thật:

```js
() => {
  const el = document.querySelector('.canh-bao');
  let bg = 'rgba(0, 0, 0, 0)', n = el;
  while (n && bg === 'rgba(0, 0, 0, 0)') { bg = getComputedStyle(n).backgroundColor; n = n.parentElement; }
  return { fg: getComputedStyle(el).color, bg, size: getComputedStyle(el).fontSize };
}
```

Ép hiện **trạng thái bắt buộc** của component (`ux/DESIGN-SYSTEM.md §4`): `browser_hover` cho hover ·
bấm submit rồi `browser_snapshot` **ngay** để bắt "đang gửi" · `page.route('**/api/**', r => r.abort())`
cho khuôn lỗi · DB sạch cho khuôn rỗng.

## 4. Chứng minh đã dùng thật

Mọi phát hiện phải nêu được **thao tác cụ thể** và **thứ thấy trên màn hình**. Ba thứ này là bằng chứng:

```
browser_snapshot          → trích đúng đoạn text/nhãn đã thấy
browser_take_screenshot   → ảnh chỗ hỏng  (TC web: lưu tracking/{wave}/screenshots/{TC}.png —
                            gate `test_evidence` đòi PNG thật)
browser_console_messages  → lỗi JS kèm nguyên văn
```

Báo "không thấy vấn đề gì" mà không kèm được thao tác đã làm thì gần như chắc chắn là **chưa dùng** —
xem `dogfood-report.md` §4 *Dấu hiệu dogfood giả*.

## 5. Ranh giới

- Chỉ thao tác trên **localhost của project này** hoặc URL môi trường của chính nó. Không đụng trang khác.
- Skill này cho **web**. Boundary `kind=mobile` là app thật — chạy trên simulator/emulator, không phải
  viewport nhỏ của trình duyệt.
- **Không sửa file project.** Vai dogfood phát hiện thì GHI vào `dogfood-report.md` §2 kèm ô `Xử`;
  việc sửa là của MAIN.
- `browser_run_code_unsafe` chạy code tuỳ ý trong trang: dùng cho **mô phỏng mạng và nhịp bấm**,
  **KHÔNG** dùng để đi tắt qua UI rồi kết luận "luồng chạy được". **Đi tắt là hết dogfood.**

## 6. Hỏng thì xem đây

| Triệu chứng | Nguyên nhân thường gặp |
|---|---|
| Server MCP không lên | `npx` trong PATH là gói standalone đời cũ, không hiểu `-y`. Dùng `npm exec` — `npm` chỉ có một bản nên không nhập nhằng |
| Lần đầu rất lâu | Đang tải Chromium. Chạy trước `npx playwright install chromium` cho xong một lần |
| Trang trắng | Service chưa chạy. Lấy URL từ `tracking/{wave}/health-proof.json` — **đừng đoán cổng** |
| Không thấy tool `browser_*` | Chưa duyệt server MCP cho project này. Duyệt một lần khi Claude Code hỏi |
