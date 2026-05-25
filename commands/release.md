# release

Tạo release notes, verify test pass, đánh dấu RC → shipped.

**Agent:** [release-agent.md](../agents/release-agent.md) · **Role:** `release`

## Gate

- `test-execute` hoặc `retest` với `test_result=pass` trong `state.checkpoints[]`
- `wave_active`
- Evidence `release_ok: true`

## Output

```
tracking/waves/{wave-id}/release-notes.md
```

## Nội dung release notes

- Features released (FEAT list từ wave plan)
- Bug fixes (auto + manual, từ `tracking/waves/{wave-id}/bugs/`)
- Coverage numbers (BE/FE)
- Deferred items
- Breaking changes

## STATE update

| Trước | Sau |
|-------|-----|
| Stage = RELEASE_CANDIDATE | **Stage = DONE** |
| — | `allowed_next = ["end-wave"]` |

## Chạy

```bash
py scripts/build_command_prompt.py release
py scripts/harness.py release complete '{"release_ok": true}'
```

## Sau release

`/end-wave` (soft close) → MANUAL_TEST → UAT → `/done-wave` (hard reset).
