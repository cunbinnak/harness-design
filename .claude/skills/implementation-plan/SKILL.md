---
name: implementation-plan
description: Chia kế hoạch implement theo boundary, AC, và thứ tự phụ thuộc.
---

# Implementation Plan Skill

## Khi dùng

Stage `IMPLEMENTATION_PLAN` (sau `TECHNICAL_DESIGN`).

## Hoạt động

1. Map feature → boundary (`harness/SERVICE-BOUNDARY-MATRIX.json`).
2. `docs/plans/WAVE-SEQUENCE.md` (roadmap tổng các wave) + `docs/plans/wave-{N}.md` (chi tiết wave, boundaries §1).
3. Liệt kê task; UX deliverable (markdown / wireframe / Figma) trong §1 `wave-{N}.md`.

## Done

- Plan đã review; sẵn sàng vào `DEV` per boundary (qua `/start-wave` → `/start-dev`).
