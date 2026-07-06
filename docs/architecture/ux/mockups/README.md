# Mockups — thiết kế giao diện THẲNG bằng HTML, theo TỪNG MÀN

> KHÔNG có template. **Đơn vị thiết kế = MÀN (screen)** — `ux-designer-agent` (`/design-ux`) tự thiết kế giao diện hoàn chỉnh cho từng màn như một trang web thật, đẹp theo chuẩn `ux-design §Visual polish`. Đây là SoT về LOOK; `ux-{boundary}.md` là SoT về BEHAVIOR; **`../SCREEN-MAP.md` là MỤC LỤC** gắn màn ↔ boundary ↔ FEAT ↔ file mockup (gate `design_gate` parse — mockup phải tồn tại + dùng token).

## Cấu trúc

```
../SCREEN-MAP.md                    # mục lục: | screen | route | boundary | feat | mockup | note |
mockups/{boundary}/{screen}.html    # mỗi MÀN 1 file, đặt trong thư mục boundary mà màn thuộc về
```

Màn thuộc boundary nào (khi có nhiều FE boundary): theo FEAT `target_experience_hint`/`target_boundary_hint` → persona của experience (BOUNDARY-MAP/CHARTER) → mơ hồ thì ux-designer HỎI user, không đoán.

## Bài mẫu + luật màu

- **`EXAMPLE.reference.html`** = mức chất lượng TỐI THIỂU — mở browser xem trước khi vẽ, vẽ xong tự so (thua = làm lại). KHÔNG copy nội dung.
- **Neutral-first**: nền luôn `--color-surface/alt`; CẤM sơn màu semantic lên mảng lớn (màu = nhấn ~10%); ô trống im lặng (hover mới hiện affordance); booking = `--color-primary-soft` (KHÔNG đỏ — `--color-danger` chỉ cho lỗi).

## Luật (gate `design_gate` + skill `ux-design` enforce)

1. **HTML TĨNH 100%** — mở bằng `file://` là xem được. KHÔNG JS framework, KHÔNG build step, KHÔNG CDN/font ngoài.
2. **Mọi màu / spacing / chữ / bo góc / bóng qua `var(--...)`** từ `../../design-tokens.css` (link relative). KHÔNG hardcode hex/px trang trí — gate chặn mockup không reference token. Cần token mới → thêm vào design-tokens.css (SoT), không bịa giá trị tại chỗ.
3. **Nội dung THẬT** — text, số liệu mẫu đúng nghiệp vụ (không lorem ipsum), đúng ngôn ngữ sản phẩm.
4. **State phụ trong cùng file** — dưới màn chính thêm section cho loading / empty / error / permission-denied (khớp bảng Screen states ở `ux-{boundary}.md`).
5. **Responsive bằng media query thật** — thu nhỏ browser là thấy layout mobile.
6. **Đủ interaction states** — `:hover` + `:focus-visible` cho mọi element tương tác.

## Ai dùng

- **User** mở browser duyệt "đẹp/xấu" TRƯỚC khi build — chê thì `/design-ux` refine tới ưng rồi mới `/design-end`.
- **Dev FE** (`rules-web` rule 1): bám mockup làm SoT look — app shell/spacing/primitives phải khớp.
- **Reviewer** (`review-web` §6): mở app cạnh mockup so — lệch rõ = MAJOR.
- **Reset**: `reset_for_new_project.py` xoá `mockups/{boundary}/` (giữ README này).
