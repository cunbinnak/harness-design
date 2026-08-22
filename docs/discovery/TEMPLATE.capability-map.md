---
type: discovery
artifact_kind: capability-map
status: DRAFT
tier: T1
owner_authority: Business Authority
wave: D1
last_reviewed: "{{DATE}}"
---

# Capability Map — {{PROJECT_NAME}}

> Điền NGẮN GỌN: ưu tiên bảng/bullet, không văn xuôi thừa, không lặp. Doc này agent downstream đọc nhiều lần — tiết kiệm context.

> Authored ở D1 sau persona-pool. Map: hypothesis → persona → capability → outcome → candidate domain. Capability TRƯỚC feature (FEAT sinh ở DOMAIN).
> Gate D1 (capability): §1 ≥5 capability row (mỗi row có ≥1 persona x + outcome + candidate domain) · §3 ≥1 candidate domain.
> Downstream: D2 mỗi candidate domain (§3) → 1 file `ES-{domain}.md` · D3 boundary identification.

---

## 1. Persona × Capability matrix

> Capability = động từ + đối tượng (không phải UI cụ thể). Cột `P1/P2/…` đánh `x` nếu persona cần. Business outcome đo được, gắn hypothesis (vd "(H1)"). Candidate domain = nhóm capability cohesion → input D2. ≥5 row.
>
> **Bảng này KHÔNG chết sau D1.** Hai cột cuối làm nó thành bảng theo dõi giao hàng xuyên suốt dự án:
> `Wave giao` chốt ở PLAN (cắt lát được: `1 (scaffold) → 3 (đầy đủ)`), `Trạng thái` cập nhật ở
> `/end-wave`. Nhờ vậy trả lời được "còn bao nhiêu năng lực chưa giao" mà không phải đọc lại mọi wave.

| # | Capability | P1 | P2 | P3 | … | Business outcome (đo được, ↔ hypothesis) | Candidate domain | Priority | MVP/Phase | Wave giao | Trạng thái |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | {{vd "Nhập đơn có cấu trúc"}} | x | | x | | {{vd "giảm tỉ lệ đơn nhầm (H1)"}} | {{vd "ordering"}} | high | MVP | _PLAN_ | chưa giao |
| C2 | {{TBD}} | | x | | | {{TBD}} | {{TBD}} | high | MVP | _PLAN_ | chưa giao |
| C3 | {{TBD}} | x | | | | {{TBD}} | {{TBD}} | med | Phase 2 | _PLAN_ | chưa giao |
| C4 | {{TBD}} | | | x | | {{TBD}} | {{TBD}} | med | Phase 2 | _PLAN_ | chưa giao |
| C5 | {{TBD}} | | | | | {{TBD}} | {{TBD}} | low | Phase N | _PLAN_ | chưa giao |

> Legend: `x` = persona cần · Priority `high|med|low` · MVP/Phase `MVP | Phase 2 | Phase N`
> · Wave giao `_PLAN_` (chưa chốt) → `1` / `1 (scaffold), 3 (đầy đủ)` · Trạng thái `chưa giao | đang làm | đã giao`.

---

## 2. Anti-capabilities (out of scope)

> Capability KHÔNG thuộc scope (link `hypothesis-log §4`). Chặn scope-creep.

- **{{Capability ngoài scope}}**: {{vì sao không làm phase này}}
- **{{Capability ngoài scope}}**: {{vì sao}}

---

## 3. Candidate domains (for D2 event storming)

> Mỗi domain = nhóm capability cohesion cao (cùng dữ liệu / vòng đời). Mỗi domain → 1 file `ES-{domain}.md` bắt buộc ở D2 (gate đối chiếu tên). Đặt tên `kebab-case` khớp tên file ES. ≥1 domain.

| Domain | Capabilities served | Rationale (vì sao gom) | Priority |
|---|---|---|---|
| {{kebab-case}} | C1, C2 | {{cohesion: cùng dữ liệu / vòng đời}} | high |
| {{kebab-case}} | C3 | {{...}} | med |

---

## 4. Capability dependencies (tuỳ chọn)

> Capability nào tiền đề cho cái khác (ảnh hưởng thứ tự wave ở PLAN).

| Capability | Phụ thuộc | Vì sao |
|---|---|---|
| {{Cn}} | {{Cm}} | {{Cm là tiền đề: ...}} |

---

## 5. Traceability check (self-check)

- [ ] Mỗi hypothesis (`hypothesis-log §3`) có ≥1 capability validate.
- [ ] Mỗi persona (`persona-pool`) có ≥1 capability đánh x.
- [ ] Mỗi capability thuộc đúng 1 candidate domain.
- [ ] Mỗi candidate domain §3 sẽ có file ES ở D2.

---

## Change log

| Date | Wave | Change | Author |
|---|---|---|---|
| {{DATE}} | D1 (pending) | Stub | — |
