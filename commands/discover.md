---
name: discover
description: "Khám phá D0-D3: giả thuyết → persona + năng lực + ma trận quyền → event storming → boundary + PROJECT.md. Tự suy đang ở đâu; D3 đạt thì chốt sang Domain."
argument-hint: "(không arg — chạy tiếp D-wave đang đứng)  ·  hoặc <D0|D1|D2|D3>  ·  D0 kèm mô tả project"
when_state: [BOOTSTRAP, DISC_D0, DISC_D1, DISC_D2, DISC_D3]
sets_stage: DISC_D0
spawn:
  agent: "discovery-hypothesis-agent · capability-mapper-agent · event-stormer-agent · charter-author-agent"
  skills: [discovery-hypothesis, capability-mapping, event-storming, boundary-charter]
gates: [{type: discovery_advance}, {type: discovery_wave}]
---

# /discover — khám phá

Gộp `discovery-start` + `discovery-end`. Không arg → chạy tiếp D-wave đang đứng (suy từ `stage`); D3 đã đạt gate → **tự chốt** sang Domain.

| D | Agent | Ra cái gì | Gate |
|---|---|---|---|
| D0 | discovery-hypothesis | `hypothesis-log.md` | §1 Vision + §2 Problem · **mỗi pain + mỗi hypothesis có bằng chứng thật** · ≥3 hypothesis · ≥2 anti · **≥1 lỗ hổng §6** |
| D1 | capability-mapping | `persona-pool.md` + `capability-map.md` | ≥1 persona · ≥2 anti-persona · **ma trận vai × hành động KHÔNG ô trống + có ≥1 ô `cấm`** · ≥5 capability đã điền · ≥1 candidate domain |
| D2 | event-storming | `event-storming/ES-{domain}.md` | mỗi candidate domain có ES · §1 Events ≥10 |
| D3 | boundary-charter | `BOUNDARY-MAP` + `CHARTER` + `PROJECT.md` + service_prefix | BOUNDARY-MAP ≥1 row · CHARTER §1 Mission · PROJECT.md |

## Đây là chỗ được hỏi nhiều nhất

Mọi thứ không đào ra ở đây sẽ phải trả bằng một lần ngắt giữa lúc code, hoặc bằng một quyết định agent tự đoán.

- **KHÔNG có trần số câu hỏi.** Ngân sách là thời gian, không phải số câu. Xong D0 trong 10 phút gần như chắc chắn là hỏi hời hợt.
- **Hai chế độ hỏi**: mục **khám phá** (pain point, ai chịu, cách làm hiện tại, ai được/không được làm gì) hỏi bằng **hội thoại mở** — KHÔNG `AskUserQuestion`, vì option có sẵn mớm lời và user sẽ bấm cái nghe hợp lý thay vì kể thực tế của họ. Mục **quyết định** (gom domain nào, ưu tiên MVP hay Phase 2) mới dùng `AskUserQuestion` kèm đánh đổi.
- **Bốn luật đào sâu**: hỏi quá khứ cụ thể (không hỏi tương lai giả định) · mỗi pain ≥1 bằng chứng (chuyện thật / con số / hiện vật) · "thường/nhiều" quy ra số · đào theo mạch, một mục 3-4 lượt là bình thường.
- **Playback trước khi chốt**: đọc lại từng mục cho user xác nhận. Hiểu sai bắt ở đây tốn một phút, lọt tới DEV tốn nửa ngày.
- **Lỗ hổng → §6**, không treo sang D kế: tìm trong tài liệu → hỏi user → vẫn chưa có thì tự quyết + ghi `scripts/decide.py`.

## Ma trận vai × hành động (D1) — mục quan trọng nhất

Artifact **duy nhất** khai được *ai KHÔNG được làm gì*. Không có nó thì: phân quyền lúc code là agent tự đoán · test không sinh được ca âm · dogfood không có gì để phá.

Mỗi ô `cấm` sinh **một ca kiểm âm bắt buộc** ở `/run-wave` (chốt sinh test case) và là danh sách phép thử của vai `breaker` ở `/dogfood`.

Ô trống là **lỗi**, không phải "chưa cần" — gate chặn. Không chắc thì hỏi user; vẫn không rõ thì chọn `cấm` (chặt an toàn hơn mở) + ghi quyết định.

## Chốt D3 — rà chéo rồi KÝ, trước khi sang Domain

Trước đây Discovery là lớp **duy nhất không có chữ ký**: domain ký bằng `domain_approve.py`, design ký bằng `approve_document.py`, còn discovery thì template có sẵn field `status:` mà không ai stamp — xác nhận của bạn nằm trong chat, không thành hiện vật.

Và phải ký **ở đây**, không đợi `/approve-document`: domain + design + plan đều xây trên discovery. Đợi tới REVIEW mới đọc chéo nghĩa là tìm ra lỗ ở `hypothesis-log` sau khi đã dựng ba tầng lên trên — tháo ngược cả ba. Cùng lý do challenge đặt **trước** khi code chứ không dựa vào review sau khi code.

### Bước 1 — agent rà chéo

Cái mà từng D-wave riêng lẻ không thấy được, vì nó chỉ soi được artifact của chính nó:

```
hypothesis ↔ capability   mỗi giả thuyết có ≥1 capability validate nó?
capability ↔ persona      mỗi persona có ≥1 capability? capability nào không ai cần?
persona    ↔ ma trận      mọi persona có cột trong ma trận quyền? còn ô trống?
capability ↔ ES           mỗi candidate domain có ES? event nào không thuộc capability nào?
ES         ↔ boundary     mỗi domain map vào đúng 1 boundary?
boundary   ↔ PROJECT.md   danh sách boundary + service_prefix khớp nhau?
§6 lỗ hổng                còn lỗ nào chưa có cách xử?
```

Lệch chỗ nào → **sửa trước**, đừng đẩy sang cho user phát hiện hộ.

### Bước 2 — trình cho user ĐỌC, rồi DỪNG LẠI

Đây là một lần dừng **thật**. Đưa đủ để user đọc và tự đánh giá, không phải để user tin lời agent:

```
Discovery xong. Mời anh/chị đọc rồi cho biết duyệt hay chưa.

Đọc theo thứ tự này (mỗi file 1 dòng nói NÊN SOI GÌ):
  docs/discovery/hypothesis-log.md     — 3 giả thuyết + bằng chứng: có đúng cược của mình không?
  docs/discovery/persona-pool.md       — §Ma trận vai × hành động: có ô `cấm` nào SAI không?
  docs/discovery/capability-map.md     — §1: có năng lực nào THIẾU, hoặc thừa không?
  docs/discovery/event-storming/ES-*.md
  docs/discovery/BOUNDARY-MAP.md + boundaries/*/CHARTER.md
  docs/architecture/PROJECT.md         — scope + stack + service_prefix

Tôi đã rà chéo, kết quả:  <lệch gì đã sửa · còn lỗ nào chưa xử>
Chỗ tôi TỰ QUYẾT khi anh/chị chưa chốt:  <trỏ dòng tracking/decisions.md>
Chỗ tôi KHÔNG CHẮC nhất:  <nói thẳng ra, đây là chỗ đáng soi nhất>
```

**KHÔNG tự ký. KHÔNG chạy tiếp.** Chờ user trả lời.

### Bước 3 — theo câu trả lời

| User nói | Làm gì |
|---|---|
| Góp ý / chưa duyệt | Sửa theo góp ý → rà chéo lại → trình lại. Lặp không giới hạn. Góp ý chạm D-wave nào thì `/discover D<n>` đào lại wave đó |
| **Duyệt** | `py scripts/approve_document.py --layer discovery` (stamp `status: APPROVED`) → `py scripts/harness.py discovery-end complete` → DOMAIN |

**User duyệt = chữ ký** — cùng khuôn với `/domain`. Gate `discovery_stamped` chặn **complete chay**: state nói đã chốt mà file vẫn `DRAFT` thì không qua được.

## Chạy từng D-wave

Thứ tự bắt buộc: **transition trước, spawn sau**. STATE phải ở đúng `DISC_D{N}` ngay thì phase-lock mới cho agent ghi `docs/discovery/**`.

1. `py scripts/harness.py discovery-start complete` với evidence `{"wave": "D<n>"}`
2. `py scripts/build_prompt.py discovery-start --disc-wave D<n> --input "$ARGUMENTS"` → spawn
3. Agent iterate tới khi user confirm
4. Hết D3 → làm mục "Chốt D3" ở trên

## Forbidden

- Nhảy cách wave (D0 → D2). Gate chặn.
- Đổi tên/heading template — gate match regex, lệch là false-fail.
- Bịa số liệu/nguồn/domain. Số nào là giả định thì ghi §5 để D1 verify.
- Tạo `knowledge-base/*.yaml` (việc của `/plan` + `/run-wave`).
