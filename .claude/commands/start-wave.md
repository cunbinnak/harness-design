---
description: "Harness: start-wave"
argument-hint: "<wave-title>"
---

# /start-wave <wave-title>

M? wave m?i — `STATE.wave`, handoff, trigger `start_wave`. **Bu?c d?u** m?i vòng.

**Agent:** [`agents/start-wave-agent.md`](../agents/start-wave-agent.md)

**Input:** title (optional) — evidence `wave_title`

```bash
python scripts/harness.py start-wave complete '{"wave_title": "Wave 1"}'
python scripts/harness.py can start-wave
```

Ti?p theo: `intake-requirement`.

