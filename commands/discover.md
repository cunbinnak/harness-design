---
name: discover
description: "Khám phá D0-D3 → persona + ma trận quyền + capability + boundary + PROJECT.md. Chốt D3: rà chéo, user đọc + duyệt = ký."
argument-hint: "(không arg — tự suy)  ·  \"<mô tả project>\" ở lần đầu  ·  <D0|D1|D2|D3> để ép đào thêm"
when_state: [BOOTSTRAP, DISC_D0, DISC_D1, DISC_D2, DISC_D3]
sets_stage: DISC_D0
spawn:
  agent: "discovery-hypothesis-agent · capability-mapper-agent · event-stormer-agent · charter-author-agent"
  skills: [discovery-hypothesis, capability-mapping, event-storming, boundary-charter]
gates: [{type: discovery_advance}, {type: discovery_stamped}, {type: discovery_wave}]
---

# /discover

**Không cần arg.** Lệnh tự suy đang đứng ở đâu và đi đâu — cùng luật với 6 lệnh còn lại:

| Đang ở | `/discover` (không arg) làm gì |
|---|---|
| `BOOTSTRAP` | vào D0. Lần đầu thì kèm mô tả: `/discover "<sản phẩm giải quyết nỗi đau gì, cho ai>"` |
| `DISC_D0..D2` | chạy gate của wave đang đứng → **xanh thì TIẾN** sang wave kế · **đỏ thì Ở LẠI**, đào đúng chỗ gate báo thiếu |
| `DISC_D3` | D3 xanh → rà chéo cả lớp → **DỪNG cho user đọc và ký**. KHÔNG tự nhảy sang DOMAIN |

Arg `<D0|D1|D2|D3>` chỉ để **ép ở lại đào thêm** khi gate đã xanh mà mình thấy chưa đủ sâu
(`/discover D1` lúc đang ở `DISC_D1`). Không phải mode phải nhớ — mặc định là bỏ trống.

| D | Ra cái gì | Gate |
|---|---|---|
| D0 | `hypothesis-log.md` | §1+§2 · **bằng chứng thật mỗi pain + mỗi hypothesis** · ≥3 hypothesis · ≥2 anti · ≥1 lỗ hổng §6 |
| D1 | `persona-pool.md` + `capability-map.md` | ≥1 persona · ≥2 anti-persona · **ma trận vai × hành động: KHÔNG ô trống, ≥1 ô `cấm`** · ≥5 capability · ≥1 domain |
| D2 | `event-storming/ES-{domain}.md` | mỗi domain có ES · §1 Events ≥10 |
| D3 | `BOUNDARY-MAP` + `CHARTER` + `PROJECT.md` + service_prefix | ≥1 row · CHARTER §1 Mission · PROJECT.md |

## Cách hỏi

**Không trần số câu.** Ngân sách là thời gian.

| Loại | Cách |
|---|---|
| Khám phá — pain point, ai chịu, cách làm hiện tại, ai được/không được làm gì | hội thoại **mở**. KHÔNG `AskUserQuestion` (option mớm lời) |
| Quyết định — gom domain nào, ưu tiên MVP hay Phase 2 | `AskUserQuestion` + đánh đổi |

Bốn luật: hỏi quá khứ cụ thể · mỗi pain ≥1 bằng chứng (chuyện thật / con số / hiện vật) · "thường/nhiều" quy ra số · đào theo mạch.

Playback trước khi chốt mỗi D-wave. Lỗ hổng → §6 + `py scripts/decide.py`, không treo sang D kế.

## Ma trận vai × hành động (D1)

Mỗi ô `cấm` → 1 ca kiểm âm bắt buộc ở `/run-wave` + 1 phép thử của vai `breaker` ở `/dogfood`. Ô trống là lỗi — không chắc thì hỏi user; vẫn không rõ thì chọn `cấm` + ghi `decide.py`.

## Chốt D3

1. **Rà chéo**: hypothesis ↔ capability ↔ persona ↔ ma trận ↔ ES ↔ boundary ↔ PROJECT. Lệch → sửa trước.
2. **DỪNG.** Trình user: danh sách file + *mỗi file nên soi gì* · chỗ đã tự quyết (trỏ `decisions.md`) · **chỗ mình không chắc nhất**. KHÔNG tự ký, KHÔNG chạy tiếp.
3. Góp ý → sửa → trình lại. **Duyệt** → `py scripts/approve_document.py --layer discovery` → `py scripts/harness.py discovery-end complete`.

## Chạy từng D-wave

`harness discovery-start complete '{"wave":"D<n>"}'` **TRƯỚC** → `build_prompt.py discovery-start --disc-wave D<n>` → spawn. (STATE phải ở đúng `DISC_D{N}` thì phase-lock mới cho agent ghi `docs/discovery/**`.)

## Forbidden

- Nhảy cách wave (D0 → D2).
- Đổi tên/heading template (gate match regex).
- Bịa số liệu/nguồn/domain.
- Tạo `knowledge-base/*.yaml`.
- Tự ký thay user ở chốt D3.
