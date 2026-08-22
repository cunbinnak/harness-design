---
name: capability-mapping
description: Discovery D1 (capability-mapper) — từ hypothesis-log sinh persona-pool (kèm MA TRẬN vai × hành động) + capability-map (persona × capability → outcome → candidate domain → wave giao). Capability TRƯỚC feature. Clone từ ADLC agent-capability-mapper.
---

# Capability Mapping Skill (D1)

## Khi load
`/discovery-start D1` — agent `capability-mapper-agent` (Business + Architecture co-author). Map **personas → capabilities → outcomes** và xác định **candidate domains** (input cho D2 event-storming).

Input: `docs/discovery/hypothesis-log.md` (D0).

## Hai chế độ hỏi (như D0 — không đổi)

| Loại mục | Cách hỏi |
|---|---|
| **Khám phá** — persona là ai, họ làm gì hôm nay, ai được/không được làm gì, vì sao | **Hội thoại MỞ**. KHÔNG dùng AskUserQuestion — option mớm lời |
| **Quyết định** — gom capability nào vào domain nào, ưu tiên MVP hay Phase 2 | `AskUserQuestion` + đánh đổi cụ thể |

**Không giới hạn số câu.** Bốn luật đào sâu của D0 áp nguyên: hỏi quá khứ cụ thể · mỗi persona phải
dẫn được về người thật/vai thật · "thường/nhiều" quy ra số · đào theo mạch.

Lỗ hổng không giải được → ghi 1 dòng `tracking/decisions.md` (kèm giả định) rồi đi tiếp, đừng treo.

## Deliverable (đúng cái gate D1 verify)

1. **`docs/discovery/persona-pool.md`** — giữ heading `## P1 — Name`, `## Ma trận vai × hành động`, `## Anti-personas`:
   - **≥1 persona** `## P1 — <Name>` (role + goals + pains + workflow today + **năng lực được cấp** + **KHÔNG được làm** + anti-persona + active waves).
   - **≥2 anti-persona**.
   - **Ma trận vai × hành động** — ≥1 hành động, **KHÔNG ô trống**.
   - **Gán persona cho vai dogfood** (6 lăng kính + cột Đợt).
2. **`docs/discovery/capability-map.md`** — giữ heading `## 1.` / `## 3.`:
   - **§1 Persona × Capability**: **≥5 capability row** (capability + persona cột + business outcome + candidate domain + MVP/Phase + **Wave giao** + **Trạng thái**).
   - **§3 Candidate domains**: **≥1 domain**. **Tên domain quyết định tên file ES ở D2** (`ES-<domain>.md`).

> Gate D1 (`discovery_gate.py D1`): ≥1 persona, ≥2 anti-persona, **ma trận không ô trống**, ≥5 capability THẬT (không tính dòng mẫu còn `{{…}}`), ≥1 candidate domain.

## Ma trận vai × hành động — mục quan trọng nhất của D1

Đây là artifact **duy nhất** trong toàn bộ vòng đời khai được *ai KHÔNG được làm gì*. Không có nó thì:
phân quyền lúc code là agent tự đoán · test không sinh được ca âm · dogfood không có gì để phá.

Cách dựng:
1. Liệt kê **hành động nghiệp vụ** (không phải endpoint, không phải màn hình) từ capability §1.
2. Mỗi persona một cột, cộng cột `chưa đăng nhập`.
3. Điền `có` / `cấm` — **mọi ô**. Ô có điều kiện ghi rõ: `có (chỉ bản ghi của mình)`.
4. Chỗ nào không chắc → **hỏi user**, đây vẫn là chỗ được hỏi. Vẫn không rõ → tự quyết theo hướng
   chặt hơn (`cấm`) + 1 dòng `tracking/decisions.md`. Mặc định chặt an toàn hơn mặc định mở.
5. Thêm **ca biên phân quyền** thứ ma trận không diễn tả được (A chạm dữ liệu của B; người submit
   tự duyệt bản của mình).

Ô trống là lỗi, không phải "chưa cần". Gate chặn.

## Phương pháp (clone agent-capability-mapper)
1. **Persona seeding**: từ hypothesis-log + hỏi mở "Ai chạm vào việc này? Kể một ngày làm việc của họ".
2. **Capability**: mỗi persona "làm được gì?" (verb-noun: 'pay invoice', 'view order'). Tách capability rộng ("manage orders") thành atomic ("place order", "track order", "cancel order").
3. **Năng lực được cấp / KHÔNG được làm** per persona → nguồn của ma trận.
4. **Outcome + priority**: mỗi capability → outcome + vì sao persona muốn + gắn **MVP / Phase 2 / Phase N** (feed wave-sequencing PLAN).
5. **Candidate domain**: capability chia sẻ core entity → 1 domain (group theo data/event similarity, KHÔNG theo tech). Đây là input D2.
6. **Anti-capability**: nêu rõ cái NOT supported.

## Capability-map là bảng SỐNG, không chết sau D1

Cột `Wave giao` để `_PLAN_` ở D1 (chưa chốt được khi chưa chia wave), PLAN điền — cắt lát được
(`1 (scaffold), 3 (đầy đủ)`). Cột `Trạng thái` cập nhật ở `/end-wave`. Nhờ hai cột này trả lời được
"còn bao nhiêu năng lực chưa giao" từ MỘT file, không phải đọc lại mọi wave.

## Quy tắc
- KHÔNG assign capability cho boundary (việc của D3 charter-author).
- KHÔNG sửa hypothesis-log (read-only ở D1).
- Candidate domain dùng tên kebab rõ ràng (vd `payment`, `auth`) → ES file D2 phải khớp `ES-<domain>.md`.
- **KHÔNG icon/checkmark** (`✓`/`✔`/emoji) ở bất kỳ đâu — dùng text (`x` / `có` / `cấm` / `-`). Convention no-icon toàn repo.

## Playback trước khi chốt
Đọc lại cho user: danh sách persona + ma trận quyền + danh sách capability. Ma trận là chỗ user hay
sửa nhất khi nghe đọc lại — vì nhìn bảng mới thấy mình vừa cấp nhầm quyền cho ai.

## Dấu hiệu hời hợt — dính ≥2 thì quay lại
- Persona bịa từ suy luận, không dẫn về được vai thật nào user kể
- Ma trận toàn `có`, không ô `cấm` nào — hệ thống nào cũng có ranh giới, không có nghĩa là chưa nghĩ tới
- Capability là tên màn hình / tên bảng chứ không phải động từ + đối tượng
- Mọi capability đều `MVP` — chưa cắt gì cả
- Không anti-capability nào

## Quality checklist
- [ ] ≥1 persona (`## P\d —`) + ≥2 anti-persona.
- [ ] Mỗi persona có `Năng lực được cấp` + `KHÔNG được làm`.
- [ ] Ma trận vai × hành động: ≥1 hành động, KHÔNG ô trống, có ≥1 ca biên.
- [ ] Bảng gán 6 vai dogfood đã điền persona + đợt.
- [ ] ≥5 capability row THẬT (§1, không tính dòng mẫu/_TBD_).
- [ ] ≥1 candidate domain (§3) đặt tên rõ để D2 dùng.
- [ ] Mỗi capability gắn MVP/Phase priority.
- [ ] Anti-capability listed.

## Done
- persona-pool + capability-map pass gate D1; đã playback; user confirm → `/discovery-start D2`.
- Return `wave: "D1"`, `user_confirmed: true`.
