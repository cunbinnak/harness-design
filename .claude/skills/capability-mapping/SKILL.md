---
name: capability-mapping
description: Discovery D1 (capability-mapper) — từ hypothesis-log sinh persona-pool + capability-map (persona × capability → outcome → candidate domain). Capability TRƯỚC feature. Clone từ ADLC agent-capability-mapper.
---

# Capability Mapping Skill (D1)

## Khi load
`/discovery-start D1` — agent `capability-mapper-agent` (Business + Architecture co-author). Map **personas → capabilities → outcomes** và xác định **candidate domains** (input cho D2 event-storming).

Input: `docs/discovery/hypothesis-log.md` (D0).

## Deliverable (đúng cái gate D1 verify)
1. **`docs/discovery/persona-pool.md`** theo template — giữ heading `## P1 — Name`, `## Anti-personas`:
   - **≥1 persona** dạng `## P1 — <Name>` (role + goals + pains + workflow today + anti-persona + active waves).
   - **≥2 anti-persona** trong `## Anti-personas` (list).
2. **`docs/discovery/capability-map.md`** theo template — giữ heading `## 1.` / `## 3.`:
   - **§1 Persona × Capability matrix**: **≥5 capability row** (capability + persona cột + business outcome + candidate domain + **MVP/Phase priority** per capability — nguồn cho wave-sequencing ở PLAN).
   - **§3 Candidate domains**: **≥1 domain** (domain + capabilities served + priority). **Tên domain ở đây quyết định tên file ES ở D2** (`ES-<domain>.md`).

> Gate D1 (`discovery_gate.py D1`): ≥1 persona, ≥2 anti-persona, ≥5 capability, ≥1 candidate domain.

## Phương pháp (clone agent-capability-mapper)
1. **Persona seeding**: từ hypothesis-log + hỏi "Ai dùng product? 3-5 persona: role + motivation chính".
2. **Capability**: mỗi persona "làm được gì?" (verb-noun: 'pay invoice', 'view order'). Tách capability rộng ("manage orders") thành atomic ("place order", "track order", "cancel order").
3. **Outcome + priority**: mỗi capability → outcome + vì sao persona muốn + gắn **MVP / Phase 2 / Phase N** (feed wave-sequencing PLAN).
4. **Candidate domain**: capability chia sẻ core entity → 1 domain (group theo data/event similarity, KHÔNG theo tech). Đây là input D2.
5. **Anti-capability**: nêu rõ cái NOT supported.

## Quy tắc
- KHÔNG assign capability cho boundary (việc của D3 charter-author).
- KHÔNG sửa hypothesis-log (read-only ở D1).
- Candidate domain dùng tên kebab rõ ràng (vd `payment`, `auth`) → ES file D2 phải khớp `ES-<domain>.md`.
- **KHÔNG icon/checkmark** (`✓`/`✔`/emoji) trong bảng persona×capability hay bất kỳ đâu — dùng text (`x` / `có` / `-`). Convention no-icon toàn repo.

## Flow
- Interactive (AskUserQuestion ≤5). Idempotent re-run. Sau confirm: return `wave: "D1"`, `user_confirmed: true`.

## Quality checklist
- [ ] ≥1 persona (`## P\d —`) + ≥2 anti-persona.
- [ ] ≥5 capability row (§1, không tính header/_TBD_).
- [ ] ≥1 candidate domain (§3) đặt tên rõ để D2 dùng.
- [ ] Mỗi capability gắn MVP/Phase priority.
- [ ] Anti-capability listed.

## Done
- persona-pool + capability-map pass gate D1; user confirm → `/discovery-end D1`.
