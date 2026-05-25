---
description: "Harness command: done-wave"
argument-hint: ""
---

# /done-wave

Đóng wave thực sự → teardown infra + reset STATE cho wave kế tiếp.

**Agent:** [done-wave-agent.md](../agents/done-wave-agent.md) · **Role:** `done-wave`

## Pre-condition

- Stage hiện tại = `MANUAL_TEST` (sau `end-wave complete`)
- UAT clean: **không còn bug "Open"** trong `tracking/waves/{wave-id}/bugs/`

## Hành vi

| | Trước | Sau |
|---|------|-----|
| Stage | MANUAL_TEST | **BOOTSTRAP** |
| Infra | Up | **Down** (`docker-compose down`) |
| `wave.id` | `wave-001` | `null` (reset) |
| `boundaries_in_flight` | `[...]` | `[]` |
| `allowed_next` | — | `["start-wave", "intake-requirement", "apply-cr"]` |

## Output

1. `docker-compose down` (BẮT BUỘC)
2. KG shared: `wave-{wave-id}-done` decision + learnings từ UAT
3. Finalize `handoff/{wave-id}.md` — section "Wave Done"

## Chạy

```bash
py scripts/build_command_prompt.py done-wave
py scripts/harness.py done-wave complete '{"done_wave_ok": true}'
```

Gate: `done_wave_ok: true`. Hook check không còn bug Open.

## Sau done-wave

| Tình huống | Lệnh |
|-----------|------|
| Wave kế tiếp đã plan, không đổi scope | `/start-wave` với `wave_id` mới |
| Có CR / thay đổi nghiệp vụ | `/apply-cr` → `/intake-requirement` (amendment) → `/review-document` → `/start-wave` |