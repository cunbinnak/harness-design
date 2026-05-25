---
description: "Harness command: fix-bugs"
argument-hint: "<boundary_id>"
---

# /fix-bugs <boundary_id>

Sửa bug — spawn `agents/fix-{boundary}-agent.md` (role `fix:backend` hoặc `fix:frontend`).

## Pre-condition

`requires_previous_any`: `test-execute` (auto fail), `retest` (re-fail), hoặc `end-wave` (manual fail trong stage MANUAL_TEST).

→ Stage có thể là: `BUG_LOGGING` (auto path) hoặc `MANUAL_TEST` (manual path).

## Slash

```bash
py scripts/build_command_prompt.py fix-bugs --boundary order
```

DOCS IN SCOPE auto-inject từ role:
- `tracking/waves/{wave-id}/bugs/**`
- `services/{boundary}/**`
- `docs/architecture/hld/hld-{boundary}.md` (BE) hoặc `ux-{boundary}.md` (FE)
- `docs/architecture/api/api-{boundary}.md`
- `knowledge-base/{boundary}.knowledge-graph.yaml`

## Complete

```bash
py scripts/harness.py fix-bugs complete '{"boundary_id": "order"}'
```

→ stage = `FIX_MANUAL_BUGS`, allowed_next = `["retest"]`.

## Sau fix-bugs

Bug ticket update: `status: fixed`. Sau đó chạy `/retest` — `retest` đọc field `origin` trong bug ticket để smart-route:
- `origin: auto` → quay về SPECIALIST_TESTING (re-run auto test)
- `origin: manual` → quay về MANUAL_TEST (stakeholder verify lại)