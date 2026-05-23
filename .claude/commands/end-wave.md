---
description: "Harness: end-wave"
argument-hint: ""
---

# /end-wave

Đóng wave sau `release` — reset STATE, sẵn sàng wave mới.

**Agent:** [`agents/end-wave-agent.md`](../agents/end-wave-agent.md)

**Pre:** [`release`](release.md) đã complete.

**Evidence:** `{"end_wave_ok": true}` — `'{"end_wave_ok": true}'`

```bash
python scripts/harness.py end-wave complete '{"end_wave_ok": true}'
```

Tiếp theo: [`start-wave`](start-wave.md).

