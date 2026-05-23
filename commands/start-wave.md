# start-wave

Mở wave **thực thi** — chỉ sau **intake** + **review-document** (plan đã có trên disk).

**Agent:** [start-wave-agent.md](../agents/start-wave-agent.md)

```bash
py scripts/build_command_prompt.py start-wave
py scripts/harness.py start-wave complete '{"wave_title": "Wave 1"}'
```

**Gate:** `docs/plans/project/*`, `docs/plans/waves/*/wave.md` phải tồn tại từ intake.

Sau complete: `handoff/wave-*.md`, nạp roster → `STATE`.

Tiếp theo: `sync-boundaries`.

[docs/LUONG-PHAT-TRIEN-SAN-PHAM.md](../docs/LUONG-PHAT-TRIEN-SAN-PHAM.md)
