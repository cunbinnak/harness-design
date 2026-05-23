---
description: "Harness: start-wave — m? wave (sau intake + review, ?ã có plan)"
argument-hint: "<wave-title>"
---

# /start-wave <wave-title>

M? wave th?c thi — **sau** `/intake-requirement` và `/review-document`. B?t bu?c ?ã có plan trên disk.

**T? ??ng khi complete:** handoff, n?p roster, ??ng b? `SERVICE-BOUNDARY-MATRIX.json`.

```bash
py scripts/build_command_prompt.py start-wave
py scripts/harness.py start-wave complete '{"wave_title": "Wave 1"}'
```

Ti?p theo: `/start-dev` (có `--boundary <id>`).

Gates: [`harness/COMMAND-GATES.json`](../harness/COMMAND-GATES.json)
