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
> Gate D1 (persona): ≥1 persona `## P1 — Name` · ≥2 anti-persona ở `## Anti-personas`.
> Downstream: capability-map §1 ref `P1/P2/…` · event-storming §3 actors · DOMAIN FEAT ref persona.

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
| Anti-persona (NOT this) | {{...}} |
| Linked hypotheses | {{...}} |
| Active in waves | {{...}} |

> Lặp `## Pn — Name` mỗi persona. Cover đủ vai trò chạm luồng value chính (tuyến đầu, xử lý, giám sát, quyết định).

---

## Persona relationship map (tuỳ chọn)

> Ai handoff / giám sát ai — giúp D2 thấy actor handoff.

| Từ persona | Tới persona | Quan hệ / handoff |
|---|---|---|
| {{P1}} | {{P2}} | {{vd: chuyển đơn xuống bếp}} |

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
