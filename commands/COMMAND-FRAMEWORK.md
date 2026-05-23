# Khung Command

> Gates: `harness/COMMAND-GATES.json` · Hooks: `harness/HOOK-RULES.json`

## Luồng

```text
intake-requirement     ← nhận yêu cầu, phân tích, lập kế hoạch (chưa mở wave)
  → review-document
  → start-wave           ← mở wave + handoff (bắt buộc đã có plan)
  → sync-boundaries      → SERVICE-BOUNDARY-MATRIX.json
  → prepare-dev → start-dev --boundary X → review-dev
  → dev-handoff → test-plan → test-execute → fix-bugs / retest
  → release → end-wave
```

## Ai chạy?

| Command | Agent |
|---------|--------|
| start-wave | start-wave-agent |
| intake-requirement | 4 specialist (pipeline) |
| review-document, test-*, release, … | `*-agent.md` cố định |
| start-dev / fix-bugs / review-dev | `{prefix}{boundary}-agent.md` (tạo lúc plan) |

```bash
python scripts/build_command_prompt.py start-wave
python scripts/build_command_prompt.py start-dev --boundary order
python scripts/harness.py start-wave complete '{"wave_title": "Wave 1"}'
```

Hướng dẫn: [../HUONG-DAN-SETUP.md](../HUONG-DAN-SETUP.md)
