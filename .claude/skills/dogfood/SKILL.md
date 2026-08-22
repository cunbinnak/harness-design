---
name: dogfood
description: Skill của 6 dogfood-{vai}-agent (chốt cuối /run-wave, hoặc lệnh /dogfood) — Dùng thử sản phẩm ĐANG CHẠY bằng 6 lăng kính persona, hai đợt theo trạng thái DB — thay cho MANUAL_TEST thủ công. Mỗi vai đóng một persona thật từ persona-pool, vai breaker chạy đủ ma trận vai × hành động. Mỗi phát hiện một dòng ở dogfood-report §2 kèm ô Xử (sửa ngay / chưa xử / wave sau) — ô trống là chưa ai quyết. KHÔNG tự fix. Gồm cả CÁCH MỞ TRÌNH DUYỆT: tool Playwright MCP, công thức theo từng lăng kính (màn nhỏ · mạng lỗi · bấm hai lần · nhập bậy + A↛B · đo computed style đối chiếu token).
---

# Dogfood Skill



## Khi load
`/dogfood` ở stage MANUAL_TEST — sau `/run-wave`. Đây là **chỗ thay cho việc người phải tự ngồi chọc vào hệ**: 6 lăng kính dùng thử trên hệ ĐANG CHẠY thật, ghi bug `origin=manual`.

`/run-wave` chạy **test-case đã viết** — nó chỉ tìm được thứ ai đó nghĩ ra trước. Dogfood đi tìm thứ **không có trong registry**: màn rỗng không nói gì, lỗi bị nuốt im lặng, bấm hai lần ra hai bản ghi, vai A chạm được dữ liệu vai B. Hai việc khác nhau, không thay thế nhau.

## Điều kiện vào

| Cần | Ở đâu | Thiếu thì |
|---|---|---|
| Hệ đang chạy thật | `tracking/wave-{N}/health-proof.json` | STOP — chạy lại `/run-wave`, KHÔNG dogfood ảo |
| Persona + ma trận quyền | `docs/discovery/persona-pool.md` | STOP — ma trận là danh sách phép thử của vai breaker |
| Gán 6 vai ↔ persona + đợt | `persona-pool.md §Gán persona cho vai dogfood` | Mặc định: mọi vai đóng persona chính |
| Luồng lõi + AC của wave | `docs/plans/wave-{N}.md` + `docs/architecture/feat/FEAT-*.md` | STOP |
| **FEAT/AC wave trước đã giao** (wave ≥2) | `archive/wave-*/DELIVERED.md` | bỏ lượt regression — gãy tính năng cũ sẽ lọt |
| Giao diện đã chốt (nếu có UI) | `docs/architecture/ux/` + `design-tokens.css` | vai `picky` bỏ qua, ghi rõ lý do |

## Hai đợt — chia theo TRẠNG THÁI DỮ LIỆU, không theo độ khó

Lý do chia đợt không phải để dàn tải, mà vì **các vai dùng chung một hệ và một DB**. Thả cả 6 cùng lúc thì vai này ghi dữ liệu đè lên cảnh vai kia đang nhìn — và **trạng thái rỗng chết ngay khi có bản ghi đầu tiên**, đúng thứ vai `edge` coi là quan trọng nhất.

```
Đợt 1 — DB SẠCH, đọc là chính     : user-edge · user-newbie · user-picky
   ↓ seed lại dữ liệu mẫu
Đợt 2 — DB CÓ DỮ LIỆU, ghi và phá : user-rushed · user-breaker · user-mobile
```

**Ba ràng buộc cứng:** tối đa 3 vai một đợt · **không mở đợt 2 khi đợt 1 chưa trả kết quả đủ** · **giữa hai đợt phải seed lại**. Muốn đổi vai nào vào đợt nào thì sửa cột `Đợt` ở `persona-pool.md`, đừng đổi trong đầu.

Chưa có bước seed → tạo dữ liệu mẫu bằng tay theo `docs/plans/wave-{N}.md` và **ghi 1 dòng bằng `py scripts/decide.py`**: thiếu seed là một phát hiện của chính lượt dogfood này, không phải chuyện vặt.

## Mỗi vai nhận gì trong prompt

1. URL/endpoint hệ đang chạy (lấy từ `health-proof.json`, không đoán)
2. **Persona được giao** — chân dung + năng lực được cấp + luồng chính, chép từ `persona-pool.md`. Lăng kính là *cách dùng*; persona là *ai đang dùng*. Thiếu persona thì vai thử như "người dùng nói chung", đúng thứ persona-pool sinh ra để tránh
3. Luồng lõi + AC liên quan của wave
4. Riêng `breaker`: **ma trận vai × hành động** đầy đủ + tài khoản thử cho từng vai
5. Riêng `picky`: màn hình liên quan ở `docs/architecture/ux/` + `design-tokens.css`

## Bằng chứng bộ ba — không có thì không tính là đã thử

Mọi phát hiện phải kèm đủ ba vế:

```
Tôi đã làm    : <thao tác chính xác — URL, dữ liệu đã gõ, nút đã bấm>
Tôi thấy      : <thứ hiện ra trên màn / mã lỗi / response thật>
Tôi mong đợi  : <thứ lẽ ra phải xảy ra, và vì sao — dẫn về AC/FEAT/ma trận>
```

Thiếu vế "Tôi đã làm" = suy từ code chứ chưa chạy. Vế "Tôi mong đợi" không dẫn được về tài liệu nào = ý kiến cá nhân, không phải bug.

## Dấu hiệu dogfood giả

- Cả 6 vai báo "không thấy vấn đề gì" ngay lần đầu — hệ mới dựng trong một wave luôn có chỗ vướng
- Báo cáo không nêu được mình đóng persona nào, hoặc đi luồng chẳng liên quan tới persona đó
- Không có thao tác cụ thể nào, chỉ có nhận xét chung ("giao diện ổn", "API hoạt động tốt")
- `breaker` báo "phân quyền đúng" mà không nêu được đã thử bao nhiêu ô `cấm` trên tổng bao nhiêu
- `picky` báo "khớp thiết kế" mà không nêu được một giá trị đo thật nào (computed style / mã màu)
- `edge` báo trạng thái rỗng OK nhưng đợt 1 chạy sau khi DB đã có dữ liệu

Dính bất kỳ dấu hiệu nào → **cho chạy lại vai đó**, yêu cầu nêu thao tác cụ thể + thứ nhìn thấy.

## Lượt regression — bắt buộc từ wave 2

`archive/wave-*/DELIVERED.md` là **hợp đồng của các wave trước**: FEAT + AC đã verify được, máy derive từ registry + report lúc đóng wave — không phải agent khai. Vai `rushed` và lượt tự đi của phiên chính phải **đi lại luồng lõi từng FEAT trong đó**, không chỉ luồng của wave này.

Wave mới xây chồng lên, không đập đi. Tính năng wave cũ gãy vì code wave mới là **regression** — nặng ngang gãy luồng lõi, xử trước mọi phát hiện khác.

## Ranh giới

- **KHÔNG tự fix.** Ghi dòng vào §2 rồi dừng — MAIN điều phối lượt sửa, để nhân quả rõ ràng.
- **KHÔNG sửa test-case-registry** cho khớp thứ vừa thấy.
- **KHÔNG sửa doc spec** — phase-lock chặn, và sửa spec cho khớp code là đúng anti-pattern harness sinh ra để chống.
- **KHÔNG teardown infra** — giữ UP cho lượt sửa + chạy lại test.
- Sản phẩm không có UI → các vai gọi API trực tiếp; `picky` soi shape response + error envelope thay cho giao diện; `mobile` soi độ trễ từ client yếu thay cho layout.


# Mở trình duyệt — CÁCH LÀM

> Bộ khung có gate đòi **screenshot thật** (`test_evidence`), đòi **computed style khớp token**
> (`web_styling`), đòi vai `picky` **đo chứ không nhìn**. Skill này là **cách làm** những việc đó.
> Đọc code rồi suy ra "chắc chạy được" **không tính** — và `dogfood_done` có mục *Dấu hiệu dogfood
> giả* để bắt đúng chuyện này.

### 1. Chạy bằng gì

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

### 2. Bốn tool dùng nhiều nhất

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

### 3. Công thức theo lăng kính

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

### 4. Chứng minh đã dùng thật

Mọi phát hiện phải nêu được **thao tác cụ thể** và **thứ thấy trên màn hình**. Ba thứ này là bằng chứng:

```
browser_snapshot          → trích đúng đoạn text/nhãn đã thấy
browser_take_screenshot   → ảnh chỗ hỏng  (TC web: lưu tracking/{wave}/screenshots/{TC}.png —
                            gate `test_evidence` đòi PNG thật)
browser_console_messages  → lỗi JS kèm nguyên văn
```

Báo "không thấy vấn đề gì" mà không kèm được thao tác đã làm thì gần như chắc chắn là **chưa dùng** —
xem `dogfood-report.md` §4 *Dấu hiệu dogfood giả*.

### 5. Ranh giới khi dùng trình duyệt

- Chỉ thao tác trên **localhost của project này** hoặc URL môi trường của chính nó. Không đụng trang khác.
- Skill này cho **web**. Boundary `kind=mobile` là app thật — chạy trên simulator/emulator, không phải
  viewport nhỏ của trình duyệt.
- **Không sửa file project.** Vai dogfood phát hiện thì GHI vào `dogfood-report.md` §2 kèm ô `Xử`;
  việc sửa là của MAIN.
- `browser_run_code_unsafe` chạy code tuỳ ý trong trang: dùng cho **mô phỏng mạng và nhịp bấm**,
  **KHÔNG** dùng để đi tắt qua UI rồi kết luận "luồng chạy được". **Đi tắt là hết dogfood.**

### 6. Hỏng thì xem đây

| Triệu chứng | Nguyên nhân thường gặp |
|---|---|
| Server MCP không lên | `npx` trong PATH là gói standalone đời cũ, không hiểu `-y`. Dùng `npm exec` — `npm` chỉ có một bản nên không nhập nhằng |
| Lần đầu rất lâu | Đang tải Chromium. Chạy trước `npx playwright install chromium` cho xong một lần |
| Trang trắng | Service chưa chạy. Lấy URL từ `tracking/{wave}/health-proof.json` — **đừng đoán cổng** |
| Không thấy tool `browser_*` | Chưa duyệt server MCP cho project này. Duyệt một lần khi Claude Code hỏi |

## Xử phát hiện — MỖI dòng phải có quyết định

Gộp phát hiện của cả 6 lăng kính × 2 đợt vào `tracking/wave-{N}/dogfood-report.md` §2.
**File có thể ĐÃ TỒN TẠI** với mục `## Mang sang từ wave <N-1>` — những dòng `chưa xử` của
wave trước, `/next-wave` chép sang với ô `Xử` bỏ trống. **APPEND vào, KHÔNG ghi đè**, và
quyết lại từng dòng đó (`sửa ngay` hay `wave sau`) — để nguyên chữ `chưa xử` là hoãn vô hạn.
Khuôn đầy đủ: `tracking/_templates/TEMPLATE.dogfood-report.md`. Cột `Xử` là **từ vựng đóng**, đúng
một trong ba — **ô trống nghĩa là chưa ai quyết**, không phải "không đáng":

| Loại phát hiện | Xử |
|---|---|
| Hỏng luồng lõi · mất dữ liệu · **thủng phân quyền** (vai A chạm được dữ liệu vai B) | `sửa ngay` — không hoãn |
| **Gãy luồng của wave TRƯỚC** (`archive/wave-*/DELIVERED.md`) | `sửa ngay` — nặng ngang gãy luồng lõi |
| Lệch design system / mockup user đã chốt: màu-cỡ ngoài token · thiếu trạng thái bắt buộc · sai khuôn rỗng/lỗi/đang tải | `sửa ngay` **về token**; cố ý giữ khác → `py scripts/decide.py` một dòng |
| Nhỏ, sửa dưới 15 phút | `sửa ngay` |
| Cần nhiều thời gian **nhưng trong scope wave này** | `chưa xử` — cột `Ở đâu` nói rõ đang nằm chỗ nào |
| **Ngoài scope đã khoá** | `wave sau` — cột `Ở đâu` nói **vì sao ngoài scope** + **cần gì để làm** |

`sửa ngay` xong thì chạy lại phần vừa sửa — sửa mà không dùng lại là chưa biết đã sửa được chưa.

Gate `dogfood_done` đọc đúng bảng này: thiếu ô `Xử` · khai `sửa ngay` mà không dẫn được vết sửa ·
đẩy `wave sau` mà không nói lý do → đỏ.

**Chỗ GHI khác chỗ NHẬN.** `docs/plans/**` bị phase-lock chặn ở đây, nên đừng cố ghi thẳng vào
`WAVE-SEQUENCE.md` — ghi lý do vào bảng này là đủ. `/next-wave` đối chiếu và nhắc dòng nào chưa
có chỗ nhận; muốn nhận thật thì lùi `/domain` (chốt chia-wave) — khoá chỉ mở ở đó. Không có sổ bug riêng: **kết quả test nằm ở
`test-report.md`, quyết định xử nằm ở đây**, hai chỗ không chép lẫn nhau.

## Done
- Đủ 2 đợt, mỗi vai một báo cáo có bằng chứng bộ ba.
- §2 mọi dòng có ô `Xử`; §3 Kết luận điền bằng **số**, không phải tính từ.
- Báo user tổng hợp → còn `sửa ngay` thì sửa + chạy lại; sạch → `/next-wave`.
