---
type: discovery
artifact_kind: event-storming
domain: "{{domain-name}}"
status: ACTIVE
tier: T0
owner_authority: Architecture Authority + Business Authority
last_reviewed: "{{DATE}}"
facilitator: "event-stormer (D2)"
---

# Event Storming — `{{domain-name}}`

> Điền NGẮN GỌN: ưu tiên bảng/bullet, không văn xuôi thừa, không lặp. Doc này agent downstream đọc nhiều lần — tiết kiệm context.

> Output `/discovery-start D2` cho 1 domain. Tên file `ES-{{domain-name}}.md` khớp domain ở `capability-map.md §3`.
> Gate D2: §1 Events ≥10 (chronological, past-tense) · ≥1 aggregate (§5) · hot-spot flagged kể cả "no hot-spot" (§7).

---

## 1. Events (timeline, chronological)

> Past-tense verb (`OrderPlaced`, không `PlaceOrder`), theo thứ tự xảy ra. ≥10 events (gate đếm dòng list ở section này). Kèm trigger / effect / immediate|async|delayed.

1. {{EventName}} — trigger: {{command/signal}} · effect: {{state change}} · {{immediate}}
2. {{EventName}} — trigger: {{...}} · effect: {{...}} · {{async}}
3. {{EventName}}
4. {{EventName}}
5. {{EventName}}
6. {{EventName}}
7. {{EventName}}
8. {{EventName}}
9. {{EventName}}
10. {{EventName}}

> Tuỳ chọn đánh dấu `(optional)` / `(terminal)` để thấy nhánh.

---

## 2. Domain summary

**Name**: `{{domain-name}}`

**Description**: {{2-3 câu — domain về cái gì, trả lời business question nào, source-of-truth cho state nào.}}

**Capabilities served** (từ `capability-map.md §1`): {{C1, C2 — name}}

**Relationships**: Upstream (depends on): {{domain-X / external Y}} · Downstream (feeds): {{domain-Z}}

---

## 3. Personas + actors involved

> Ai trigger event. Persona pull từ `persona-pool.md`; thêm system/external actor.

| Actor | Type | Role in this domain |
|---|---|---|
| `P1` ({{name}}) | Persona | {{vd: tạo đơn}} |
| `SYSTEM-{{scheduler}}` | System | {{vd: trigger job định kỳ}} |
| `EXT-{{provider}}` | External | {{vd: authorize/capture}} |

---

## 4. Commands → events mapping

| Command | Actor | Triggers event | Pre-conditions |
|---|---|---|---|
| `{{DoSomething(args)}}` | {{actor}} | `{{SomethingHappened}}` | {{state hợp lệ / quyền}} |
| `{{...}}` | {{...}} | `{{...}}` | {{...}} |

---

## 5. Aggregates identified

> Gom event mutate cùng root entity thành aggregate (consistency boundary). ≥1 aggregate. 1 aggregate ≈ 1 boundary candidate ở D3.

### Aggregate 1: `{{Root}}`

**Events emitted**: {{Event1, Event2, …}}

**State machine (proto)**: `INITIATED → {{...}} → {{TERMINAL}}` (nhánh: `→ {{ALT-TERMINAL}}`)

**Invariants observed**:
- {{vd: không capture nếu chưa AUTHORIZED}}
- {{vd: amount ≤ balance}}

### Aggregate 2: `{{Root}}` (nếu có)

**Events emitted**: {{...}} · **State machine**: {{...}} · **Invariants**: {{...}}

---

## 6. External systems

| External | Type | Interaction | Direction |
|---|---|---|---|
| {{provider}} | {{payment / notification}} | {{authorize, capture}} | {{Outbound HTTP / event publish}} |

---

## 7. Hot-spots (unresolved)

> Thứ chưa chắc — câu hỏi mở / mâu thuẫn / edge-case. Output giá trị NHẤT (signal risk) → ADR (Architecture) hoặc CR (Business). Phải declare kể cả khi không có.

| Hot-spot | Status | Assigned to |
|---|---|---|
| **{{câu hỏi mở}}** | OPEN | Architecture — cần ADR |
| **{{edge case}}** | OPEN | Business — cần quyết định |
| **{{out-of-scope MVP}}** | DEFERRED | Phase 2 |

_Nếu không có: ghi "No open hot-spot — domain flow rõ ràng, đã xác nhận với user."_

---

## 8. Reactor patterns (event → event chains)

> Event tự kích hoạt event/command khác (chuỗi phản ứng) — định hướng subscriber wiring ở DESIGN.

| Trigger event | Reaction (event/command) | Handler |
|---|---|---|
| `{{XHappened}}` | → `{{YTriggered}}` (downstream) | {{handler}} |

---

## 9. Open questions for Architecture Authority

- [ ] {{Aggregate boundary: A ≠ B là 2 aggregate riêng?}}
- [ ] {{Cross-aggregate consistency: saga vs event-sourcing?}}
- [ ] {{State machine: explicit vs implicit (status + validation)?}}

---

## 10. Ubiquitous language seeds

> Thuật ngữ canonical nổi lên; Architecture chốt cho boundary HLD.

| Term | Definition (provisional) | Distinct from |
|---|---|---|
| **{{Term}}** | {{định nghĩa}} | {{từ dễ nhầm}} |

---

## 11. Workshop session info

- **Date**: {{date}} · **Facilitator**: event-stormer (D2) · **Participants**: {{names}} · **Mode**: NEW / REFINE

---

## 12. Acceptance criteria (DONE khi)

- [ ] ≥10 events chronological past-tense (§1) · mỗi event có command+actor (§4)
- [ ] ≥1 aggregate với state machine + invariants (§5) · ≥1 external system (§6)
- [ ] Hot-spots flagged kể cả "no hot-spot" (§7) · reactor (§8) · ubiquitous language (§10)
- [ ] User confirm output

---

## 13. Hand-off

- D3 charter-author: §5 Aggregates → boundary candidate (1 aggregate ≈ 1 boundary).
- DESIGN: derive event/api contract từ §1 + §4 + §8.
- capability-mapper: refine `capability-map.md` nếu lộ capability mới.

---

## 14. References

`capability-map.md §3` (domain nguồn) · `persona-pool.md` (actor) · `hypothesis-log.md` (hypothesis) · `BOUNDARY-MAP.md` (map domain → boundary ở D3).

---

## 15. Change log

| Date | Mode | Update | Facilitator |
|---|---|---|---|
| {{DATE}} | NEW | Initial event storming session | event-stormer |
