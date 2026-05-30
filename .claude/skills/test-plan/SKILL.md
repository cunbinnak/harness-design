---
name: test-plan
description: Sinh test-case-registry.md cho wave (TC-IDs, scenarios, AC trace).
---

# Test Plan Skill

## Khi load
`test-plan-agent` ở `/test-plan`.

## Output: `tracking/wave-{N}/test-case-registry.md`

Cấu trúc:
- Heading per TC-ID: `## TC-{N}-{slug}`
- Frontmatter mỗi TC: `type: [api|e2e|ui|isolation|perf|security], boundary: X, feature: FEAT-N, ac: FEAT-N:AC-M, priority: P0|P1|P2`
- Section: Pre-conditions, Steps, Expected, Data setup, Cleanup.

## Quy ước
1. Mỗi AC trong FEAT phải có ≥ 1 TC trace tới.
2. Smoke test cross-boundary cho mọi integration điểm.
3. P0 = blocker release, P1 = must-have, P2 = nice-to-have.
