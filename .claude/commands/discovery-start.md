---
name: discovery-start
description: "Discovery D0-D3 (clone tối giản ADLC): vào/ở 1 wave ideation + spawn agent (D0 hypothesis · D1 capability/persona · D2 event-storming · D3 charter+derive PROJECT)."
argument-hint: "<D0|D1|D2|D3>  (vd: /discovery-start D0)"
when_state: [BOOTSTRAP, DISC_D0, DISC_D1, DISC_D2, DISC_D3]
sets_stage: DISC_D0
spawn:
  agent: "discovery wave agent (theo D-wave): hypothesis | capability-mapper | event-stormer | charter-author"
  skills: [discovery-hypothesis, capability-mapping, event-storming, boundary-charter]
gates: [{type: non_empty, field: wave}]
---

# /discovery-start

> **Clone tối giản phase DISCOVERY của ADLC** (D0-D2 ideation + D3 charter). 2 command lái flow: `/discovery-start <D>` (wave này) + `/discovery-end <D>` (verify gate → wave kế). Sau D3 → DOMAIN_AUTHORING (`/domain-start`).

## Mục đích
Vào (hoặc ở lại) 1 Discovery wave + spawn agent sinh artifact wave đó. Mỗi wave có exit gate (`scripts/discovery_gate.py`).

| Wave | Agent / skill | Output | Gate |
|---|---|---|---|
| D0 | discovery-hypothesis | `docs/discovery/hypothesis-log.md` | §1 Vision + §2 Problem; ≥3 hypothesis; ≥2 anti-hypothesis |
| D1 | capability-mapping | `docs/discovery/persona-pool.md` + `capability-map.md` | ≥1 persona; ≥2 anti-persona; ≥5 capability; ≥1 candidate domain |
| D2 | event-storming | `docs/discovery/event-storming/ES-{domain}.md` (1/domain) | mỗi candidate domain có ES; §1 Events ≥10 |
| D3 | boundary-charter | `BOUNDARY-MAP` + `boundaries/{b}/CHARTER.md` + derive `docs/architecture/PROJECT.md` + chốt service_prefix (KHÔNG sinh FEAT — DOMAIN sở hữu) | BOUNDARY-MAP ≥1 row; CHARTER §1 Mission; PROJECT.md; service_prefix |

## Input
`$ARGUMENTS` = D-wave (`D0`..`D3`). D0 nhận thêm mô tả project nếu user truyền (`/discovery-start D0 "CRM cho công ty X..."`).

## Workflow
1. Parse `$1` = wave (D0|D1|D2|D3). Không có → mặc định D0 (hoặc wave hiện tại nếu đang ở DISC_*).
2. Run: `py scripts/build_prompt.py discovery-start --disc-wave $1 --input "$ARGUMENTS"`.
3. Spawn agent với prompt từ stdout (skill tương ứng tự load).
4. Agent đọc template `docs/discovery/TEMPLATE.*` — **giữ NGUYÊN heading** (gate match regex) — produce artifact, interactive với user (≤5 câu), iterate tới khi user confirm.
5. Verify artifact tồn tại + đúng cấu trúc (xem bảng gate).
6. Agent return có lỗi → STOP báo user, KHÔNG `/discovery-end`.
7. **KHÔNG đổi stage ở đây** trừ lần đầu (BOOTSTRAP→DISC_D0). Trong DISC_D{N} gọi lại `/discovery-start D{N}` = self-loop (re-spawn/refine).

## State semantics
- BOOTSTRAP + `/discovery-start D0` → DISC_D0.
- DISC_D{N} + `/discovery-start D{N}` → DISC_D{N} (self, re-spawn để bổ sung/refine).
- Tiến sang wave kế CHỈ qua `/discovery-end <D>` (verify gate).

## Sau khi agent confirm
Báo user: "Wave $1 xong. Review artifact. OK → `/discovery-end $1` (verify gate → wave kế). Cần sửa → `/discovery-start $1` lại."

## Forbidden
- Tạo `knowledge-base/*.yaml` (KG do implementation-plan/start-wave sau).
- Đổi tên/đổi heading template (gate sẽ false-fail).
- Bịa số liệu/nguồn/domain.

## Crash / resume
Re-run `/discovery-start <D>` — agent skip phần đã có (idempotent, update không blind-append).
