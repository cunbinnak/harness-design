# Wave {N} — {wave-title}

> Per-wave plan chi tiết. Sinh bởi program-planner-agent ở intake step 4.
> Updated khi `/apply-cr` thay đổi scope wave này.

## Overview

| Field | Value |
|-------|-------|
| Wave ID | wave-{NNN} |
| Wave title | {short name} |
| Goal | {1-2 sentences} |
| Estimated duration | {N weeks} |
| Status | PLANNED / IN_PROGRESS / COMPLETED |
| Start date | {date} |
| End date target | {date} |

## Boundaries in scope

Liệt kê boundaries tham gia wave này (subset của MATRIX). Mỗi boundary có:

### {boundary-1}

- **Kind**: backend / bff / web / mobile
- **Prefix**: {prefix} (vd crm-hdpe)
- **Tech**: {language + framework}
- **Owned paths**: xem `harness/SERVICE-BOUNDARY-MATRIX.json`
- **Features wave này**: `FEAT-001`, `FEAT-002`
- **AC count**: {N}
- **Dependencies trong wave**: cần {boundary-x} ready trước (vd auth trước customer-mgmt)

### {boundary-2}

...

## Features in scope

| FEAT | Boundary | Priority | AC count | Notes |
|------|----------|----------|----------|-------|
| FEAT-001 | {boundary} | Must | 3 | Authentication |
| FEAT-002 | {boundary} | Must | 5 | Customer CRUD |
| FEAT-003 | {boundary} | Should | 2 | Customer search |

## Dependencies (cross-wave)

Liệt kê những gì wave này phụ thuộc từ wave trước:

| From wave | Deliverable | Why needed |
|-----------|-------------|------------|
| Wave 0 (infra) | docker-compose template | Để build local stack |
| Wave {N-1} | {deliverable} | {reason} |

## Implementation order (within wave)

Thứ tự dev:

1. **Phase 1** (week 1): {boundary-foundation} (vd auth)
2. **Phase 2** (week 2): {boundaries dependent on foundation}
3. **Phase 3** (week 3): {FE/BFF integration}
4. **Phase 4** (week 4): test + UAT + release

## Risks for this wave

| Risk | Impact | Mitigation |
|------|--------|-----------|
| {risk 1} | {high/medium/low} | {action} |

## Exit criteria (wave done)

- [ ] All FEAT 'Must' implemented và test pass
- [ ] Coverage threshold met (BE >= 80%, FE >= 60%)
- [ ] docker-compose có entries cho mọi boundary trong wave
- [ ] Smoke functional pass (login + create entity + FE accessible)
- [ ] Test cases registry có >= 1 TC per AC
- [ ] Auto test all P0 pass
- [ ] UAT signed off bởi stakeholder
- [ ] `tracking/wave-{NNN}/qc-signoff.md` filled với chữ ký
- [ ] No open bug

## Rollback plan

Nếu wave deploy fail:
1. Revert docker-compose về wave {N-1}
2. Rollback database migration: `flyway undo` (nếu support) hoặc compensating migration
3. Trigger alert oncall

## Related artifacts

- [WAVE-SEQUENCE.md](WAVE-SEQUENCE.md) — overall roadmap
- [tracking/wave-{NNN}/](../../tracking/) — test cases + report + bugs + signoff
- [handoff/wave-{NNN}.md](../../handoff/) — dev handoff doc
