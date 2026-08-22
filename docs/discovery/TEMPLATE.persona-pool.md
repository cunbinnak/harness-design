---
type: discovery
artifact_kind: persona-pool
status: DRAFT
tier: T1
owner_authority: Business Authority
wave: D1
last_reviewed: "{{DATE}}"
---

# Persona Pool — {{PROJECT_NAME}}

> Điền NGẮN GỌN: ưu tiên bảng/bullet, không văn xuôi thừa, không lặp. Doc này agent downstream đọc nhiều lần — tiết kiệm context.

> Authored ở D1 (capability-mapper), input = hypothesis-log (D0). Mỗi persona = 1 vai trò vận hành (không phải cá nhân).
> Gate D1 (persona): ≥1 persona `## P1 — Name` · ≥2 anti-persona ở `## Anti-personas` · **`## Ma trận vai × hành động` có ≥1 hành động và KHÔNG còn ô trống**.
> Downstream: capability-map §1 ref `P1/P2/…` · event-storming §3 actors · DOMAIN FEAT ref persona ·
> **ma trận → spec phân quyền khi code, và là danh sách phép thử bắt buộc của `/dogfood`** (mỗi ô `cấm` = 1 ca phải thử).

---

## P1 — {{Persona Name}}

| Field | Value |
|---|---|
| Role | {{vai trò vận hành, vd "thu ngân tuyến đầu" / "chủ chuỗi giám sát đa chi nhánh"}} |
| Goals | {{2-4 mục tiêu chính, ngăn `;`}} |
| Pains | {{2-4 nỗi đau hiện tại, gắn status quo}} |
| Workflow today | {{persona làm việc thế nào HÔM NAY, chưa có hệ thống mới — thấy pain ở đâu}} |
| Jobs-to-be-done | {{"Khi <tình huống>, tôi muốn <động lực>, để <kết quả>" — 1-2 job}} |
| Frequency / volume | {{tần suất: liên tục / vài lần/ngày / cuối ca / cuối tuần}} |
| Tech savviness | {{low / med / high}} |
| Success metric | {{"thành công" khi nào — đo được, link hypothesis}} |
| Năng lực được cấp | {{persona này ĐƯỢC làm gì — liệt kê hành động, không phải màn hình}} |
| KHÔNG được làm | {{persona này bị CẤM làm gì — nguồn của ô `cấm` trong ma trận dưới}} |
| Anti-persona (NOT this) | {{phân biệt với ai để tránh nhầm scope}} |
| Linked hypotheses | {{H1, H2}} |
| Active in waves | {{W1, W2 — chốt cứng ở PLAN}} |

## P2 — {{Persona Name}}

| Field | Value |
|---|---|
| Role | {{...}} |
| Goals | {{...}} |
| Pains | {{...}} |
| Workflow today | {{...}} |
| Jobs-to-be-done | {{...}} |
| Frequency / volume | {{...}} |
| Tech savviness | {{...}} |
| Success metric | {{...}} |
| Năng lực được cấp | {{...}} |
| KHÔNG được làm | {{...}} |
| Anti-persona (NOT this) | {{...}} |
| Linked hypotheses | {{...}} |
| Active in waves | {{...}} |

> Lặp `## Pn — Name` mỗi persona. Cover đủ vai trò chạm luồng value chính (tuyến đầu, xử lý, giám sát, quyết định).

---

## Ma trận vai × hành động

> **Spec phân quyền + danh sách phép thử.** Mỗi hành động một dòng, mỗi vai một cột, cộng cột
> `chưa đăng nhập`. Điền `có` (được làm) hoặc `cấm` (bị chặn) — ô có điều kiện thì ghi rõ:
> `có (chỉ bản ghi của mình)`.
>
> **KHÔNG được để ô trống.** Ô trống nghĩa là chưa ai quyết, và chỗ chưa ai quyết ở D1 sẽ thành
> chỗ code tự đoán ở DEV. Gate D1 chặn ô trống — đây là điểm khác biệt với một bảng tham khảo.
>
> Mỗi ô `cấm` sinh **một ca kiểm âm bắt buộc**: đăng nhập đúng vai đó (hoặc không đăng nhập),
> gọi thẳng URL/API tới hành động bị cấm, phải bị chặn **ở server**. `/dogfood` vai `user-breaker`
> chạy đúng bảng này; `/test-plan` sinh TC âm từ đúng bảng này.
>
> Hành động viết bằng ngôn ngữ nghiệp vụ (`Huỷ đơn của người khác`), không phải endpoint.
> Không dùng icon — chỉ `có` / `cấm` (grep được).

| Hành động | P1 {{tên}} | P2 {{tên}} | chưa đăng nhập |
|---|---|---|---|
| {{vd: Tạo đơn}} | có | cấm | cấm |
| {{vd: Xem đơn của người khác}} | cấm | có (chỉ chi nhánh mình) | cấm |
| {{vd: Xoá đơn đã chốt}} | cấm | cấm | cấm |

**Ca biên phân quyền phải kiểm** (thứ ma trận không diễn tả được):

- {{vd: A tạo bản ghi, B gọi thẳng URL tới id của A — phải bị chặn}}
- {{vd: người submit tự duyệt bản của chính mình — phải bị chặn (separation-of-duty)}}

---

## Persona relationship map (tuỳ chọn)

> Ai handoff / giám sát ai — giúp D2 thấy actor handoff.

| Từ persona | Tới persona | Quan hệ / handoff |
|---|---|---|
| {{P1}} | {{P2}} | {{vd: chuyển đơn xuống bếp}} |

---

## Gán persona cho vai dogfood

> `/dogfood` chạy 6 lăng kính trên hệ ĐANG CHẠY. Lăng kính là *cách dùng*; persona là *ai đang dùng*.
> Bảng này gán mỗi lăng kính vào một persona thật ở trên — thiếu nó thì các vai thử như "người dùng
> nói chung", đúng thứ persona-pool sinh ra để tránh.
>
> **Cột `Đợt`** chia theo **trạng thái dữ liệu**, không theo độ khó: đợt 1 cần DB sạch (trạng thái
> rỗng chết ngay khi có bản ghi đầu tiên), đợt 2 cần DB có dữ liệu. Giữa hai đợt seed lại.
> Tối đa 3 vai một đợt — hệ và DB dùng chung, thả cả 6 cùng lúc là vai này đè cảnh vai kia.

| Lăng kính | Persona đóng | Đợt | Ghi chú |
|---|---|---|---|
| `user-edge` — rỗng / mất mạng / lỗi / nhiều dữ liệu | {{P1}} | 1 | đo trạng thái rỗng TRƯỚC khi ai ghi gì |
| `user-newbie` — lần đầu, không biết gì | {{P1}} | 1 | |
| `user-picky` — khó tính về hình thức | {{P2}} | 1 | đối chiếu design-tokens + mockup đã chốt |
| `user-rushed` — bấm nhanh, bỏ giữa chừng, quay lại | {{P1}} | 2 | |
| `user-breaker` — nhập bậy, gửi hai lần, vượt quyền | {{P2}} | 2 | chạy đủ ma trận vai × hành động ở trên |
| `user-mobile` — màn hình nhỏ | {{P1}} | 2 | theo thiết bị chính của persona |

> Sản phẩm không có UI (API/CLI/worker) → ghi `KHÔNG CÓ UI` ở dòng đầu mục này; `/dogfood` chuyển
> sang gọi API trực tiếp, `user-picky` soi shape response/error envelope thay cho giao diện.

---

## Anti-personas (people we are NOT designing for)

> Giữ scope honest (≥2). Mỗi item: tên nhóm + vì sao KHÔNG thiết kế cho họ (link anti-hypothesis nếu có).

- **{{Tên nhóm}}**: {{ngoài scope — trọng tâm là ...}}
- **{{Tên nhóm}}**: {{vì sao ngoài scope}}

---

## Change log

| Date | Wave | Change | Author |
|---|---|---|---|
| {{DATE}} | D1 (pending) | Stub | — |
