---
name: event-storming
description: Discovery D2 (event-stormer) — facilitate event storming cho 1 domain → ES-{domain}.md (events ≥10 + commands + aggregates + hot-spots + external systems). 1 spawn/domain. Clone từ ADLC agent-event-stormer.
---

# Event Storming Skill (D2)

## Khi load
`/discovery-start D2` — agent `event-stormer-agent` (Architecture + Business). Facilitate event storming cho **MỘT domain mỗi lần**, theo candidate domains ở `capability-map.md §3`. Interactive — dùng AskUserQuestion nhiều.

Input: `docs/discovery/capability-map.md §3` (candidate domains) + `persona-pool.md` (actors).

## Deliverable (đúng cái gate D2 verify)
**`docs/discovery/event-storming/ES-{domain}.md`** theo `TEMPLATE.ES.md` cho **mỗi candidate domain** ở capability-map §3. Tên file PHẢI khớp domain (kebab) — gate D2 đọc domain từ §3 rồi tìm `ES-<domain>.md`.

Mỗi ES file:
- **§1 Events**: **≥10 event** (numbered list, past-tense, chronological). Gate đếm dòng list ở section "1. Events".
- §4 Commands → events (mỗi event có command + actor).
- §5 Aggregates (≥1, state machine proto).
- §6 External systems (≥1).
- §7 Hot-spots (unresolved — output giá trị nhất).
- §9 Open questions cho Architecture Authority (hand-off chính thức sang D3 charter).

> Gate D2 (`discovery_gate.py D2`): mỗi candidate domain có ES file; §1 Events ≥10. Lệch heading "1. Events" → gate đếm 0 → fail.

## Phương pháp (clone agent-event-stormer — 4 phase)
1. **Events (past tense)**: "Sự kiện gì xảy ra trong domain? (OrderPlaced, RefundIssued...)". Thu 10-30, đừng over-constrain sớm. → §1.
2. **Commands + Actors**: mỗi event "command nào trigger? ai issue (persona/system)?" → §4.
3. **Aggregates**: group events mutate cùng entity → tên aggregate + state machine proto → §5.
4. **Hot-spots + external + reactor**: cái chưa chắc/contentious (§7), system ngoài (§6), event→event chain (§8).

## Quy tắc
- KHÔNG quyết boundary ownership (việc của D3).
- 2 event cùng concept khác tên → push canonical naming (ubiquitous language seed §10).
- KHÔNG sửa capability-map/persona-pool (read-only). Chỉ ghi ES file.
- REFINE mode: ES file đã có → đọc + tìm delta, KHÔNG rewrite from scratch.

## Flow
- 1 spawn = 1 domain. Nhiều domain → main gọi `/discovery-start D2` lặp (mỗi lần 1 domain) tới khi mọi candidate domain có ES.
- Interactive (AskUserQuestion ≤5). Sau confirm: return `wave: "D2"`, `user_confirmed: true`, `files_changed: [ES-...]`.

## Quality checklist
- [ ] Mỗi candidate domain (capability-map §3) có `ES-<domain>.md`.
- [ ] §1 Events ≥10 (numbered, past-tense, chronological).
- [ ] Mỗi event có command + actor (§4).
- [ ] ≥1 aggregate (§5) + ≥1 external (§6) + hot-spots flagged (§7) + open-questions cho Authority (§9).

## Done
- Mọi candidate domain có ES file pass gate D2; user confirm → `/discovery-start D3` (tiến wave, gate D2 verify lúc đó).
