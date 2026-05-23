---
description: "Harness: intake-requirement"
argument-hint: "<input>"
---

# /intake-requirement <input>

Nhận yêu cầu → **thiết kế toàn cục** (waves, agent roster) + tài liệu wave hiện tại.

**Pre:** [`start-wave`](start-wave.md) đã complete.

**Agent:** [`agents/intake-requirement-agent.md`](../agents/intake-requirement-agent.md)

**Artifact:** `handoff/wave-NNN.md`, `docs/product/FEAT-*.md`, `docs/plans/*.md`

```bash
python scripts/harness.py can intake-requirement
python scripts/harness.py intake-requirement complete
```

