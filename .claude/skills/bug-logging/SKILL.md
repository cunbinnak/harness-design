---
name: bug-logging
description: Ghi bug vào 1 file bugs.md theo format gate parse được, để truy vết + chặn end-wave.
---

# Bug Logging Skill

## Khi load
`test-execute-agent` (bug `origin: auto`) và `/fix-bugs` chain (bug `origin: manual` từ MANUAL_TEST).

## Output: `tracking/wave-{N}/bugs.md` (1 FILE chung — KHÔNG mỗi bug 1 file)
Template: `tracking/_templates/TEMPLATE.bugs.md`.

Mỗi bug = 1 section, format **bắt buộc** (gate `no_open_bugs` parse heading + `status:`):

```markdown
## BUG-NNN — {tiêu đề ngắn}

```yaml
status: open          # open | in_progress | fixed | closed | wontfix
origin: auto          # auto (test-execute) | manual (UAT) | framework (tooling/review)
severity: high        # high | medium | low
boundary: {boundary}
detected_in: TC-XXX   # hoặc FEAT-N:AC-M nếu UAT
```

### Reproduce / Expected / Actual / Root cause / Fix
```

## Quy ước
1. `status` mở (`open`/`in_progress`) → gate `end-wave` (`no_open_bugs`) **chặn** soft-close.
2. `origin`: `auto` từ test-execute, `manual` từ UAT (MANUAL_TEST), `framework` từ review agent (vd axe-core).
3. Link `BUG-NNN` ↔ regression TC (`TC-R*`) sau khi fix; cập nhật `status: fixed` rồi `closed`.

## Done
- Bug có heading `## BUG-NNN`, `status`, reproduce steps, severity, boundary, owner.
