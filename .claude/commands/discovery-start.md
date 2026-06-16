---
name: discovery-start
description: "Discovery D0-D3 (clone tối giản ADLC): vào/ở 1 wave ideation + spawn agent (D0 hypothesis · D1 capability/persona · D2 event-storming · D3 charter+derive PROJECT)."
argument-hint: "<D0|D1|D2|D3>  (vd: /discovery-start D1 để tiến sang D1)"
when_state: [BOOTSTRAP, DISC_D0, DISC_D1, DISC_D2, DISC_D3]
sets_stage: DISC_D0
spawn:
  agent: "discovery wave agent (theo D-wave): hypothesis | capability-mapper | event-stormer | charter-author"
  skills: [discovery-hypothesis, capability-mapping, event-storming, boundary-charter]
gates: [{type: non_empty, field: wave}, {type: discovery_advance}]
---

# /discovery-start

> **Clone tối giản phase DISCOVERY của ADLC** (D0-D2 ideation + D3 charter). **`/discovery-start` TIẾN qua các wave D0→D1→D2→D3** (mỗi lần gọi với wave kế = gate wave hiện tại rồi vào wave kế; gọi lại cùng wave = refine). Hết D3 → **`/discovery-end`** (1 lần, không arg) chốt → DOMAIN_AUTHORING.

## Mục đích
Tiến tới (hoặc refine) 1 Discovery wave + spawn agent sinh artifact wave đó. Nhảy tiến sang wave kế = **gate wave hiện tại** trước (`scripts/discovery_gate.py`, gate `discovery_advance`); refine cùng wave / lần đầu D0 = không gate.

| Wave | Agent / skill | Output | Gate |
|---|---|---|---|
| D0 | discovery-hypothesis | `docs/discovery/hypothesis-log.md` | §1 Vision + §2 Problem; ≥3 hypothesis; ≥2 anti-hypothesis |
| D1 | capability-mapping | `docs/discovery/persona-pool.md` + `capability-map.md` | ≥1 persona; ≥2 anti-persona; ≥5 capability; ≥1 candidate domain |
| D2 | event-storming | `docs/discovery/event-storming/ES-{domain}.md` (1/domain) | mỗi candidate domain có ES; §1 Events ≥10 |
| D3 | boundary-charter | `BOUNDARY-MAP` + `boundaries/{b}/CHARTER.md` + derive `docs/architecture/PROJECT.md` + chốt service_prefix (KHÔNG sinh FEAT — DOMAIN sở hữu) | BOUNDARY-MAP ≥1 row; CHARTER §1 Mission; PROJECT.md; service_prefix |

## Input
`$ARGUMENTS` = D-wave (`D0`..`D3`). D0 nhận thêm mô tả project nếu user truyền (`/discovery-start D0 "CRM cho công ty X..."`).

## Workflow (THỨ TỰ QUAN TRỌNG — complete TRƯỚC, spawn SAU)
1. Parse `$1` = wave (D0|D1|D2|D3). Không có → wave hiện tại (refine) hoặc D0 nếu BOOTSTRAP.
2. **Transition NGAY (complete trước spawn):** `py scripts/harness.py discovery-start complete '{"wave":"$1"}'`.
   - BOOTSTRAP+D0 → DISC_D0 (first-entry, no gate). · DISC_D{N}+D{N} → DISC_D{N} (refine, no gate). · DISC_D{N}+D{N+1} → DISC_D{N+1} (**gate D{N}** qua `discovery_advance`).
   - **Vì sao complete TRƯỚC:** STATE phải ở đúng stage `DISC_D{N}` NGAY thì (a) **phase-lock** mới cho agent ghi `docs/discovery/**` (BOOTSTRAP/stage-sai → bị chặn); (b) next-step hint + Stop-hook đúng. (Giống `/start-dev` complete-before-spawn.)
   - Gate FAIL (nhảy tiến mà wave hiện tại chưa đạt) → complete reject → **STOP**, quay lại refine wave hiện tại (`/discovery-start D{N}`). Override: `{"wave":"$1","force":true,"reason":"..."}`.
3. Run `py scripts/build_prompt.py discovery-start --disc-wave $1 --input "$ARGUMENTS"` → spawn agent (STATE giờ đã ở DISC_D{N}).
4. Agent đọc template `docs/discovery/TEMPLATE.*` — **giữ NGUYÊN heading** (gate match regex) — produce artifact, interactive (≤5 câu), iterate tới khi user confirm.
5. Agent lỗi → STOP báo user.

## State semantics
- BOOTSTRAP + `/discovery-start D0` → DISC_D0 (no gate).
- DISC_D{N} + `/discovery-start D{N}` → DISC_D{N} (refine, no gate — bổ sung/sửa artifact).
- DISC_D{N} + `/discovery-start D{N+1}` → DISC_D{N+1} (**TIẾN**, gate D{N} qua `discovery_advance`). KHÔNG nhảy cách wave (D0→D2 reject).
- Chốt cuối: DISC_D3 + `/discovery-end` → DOMAIN_AUTHORING (gate D3).

## Sau khi agent confirm
Báo user: "Wave $1 xong. OK → `/discovery-start D{N+1}` (gate $1 → wave kế) · cần sửa → `/discovery-start $1` lại · nếu là D3 → `/discovery-end` (chốt → DOMAIN)."

## Forbidden
- Tạo `knowledge-base/*.yaml` (KG do implementation-plan/start-wave sau).
- Đổi tên/đổi heading template (gate sẽ false-fail).
- Bịa số liệu/nguồn/domain.

## Crash / resume
Re-run `/discovery-start <D>` — agent skip phần đã có (idempotent, update không blind-append).
