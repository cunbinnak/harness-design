# Wave Sequence — {project-name}

> Roadmap toàn dự án. Sinh bởi program-planner-agent ở intake step 4.
> Updated khi `/apply-cr` thay đổi scope dự án.

## Project overview

| Field | Value |
|-------|-------|
| Project | {project name} |
| Service prefix | {prefix vd: crm-hdpe} |
| Total duration estimate | {N weeks} |
| Total waves | {N} |
| Created | {date} |
| Author | program-planner-agent (intake step 4) |

## Wave breakdown

### Wave 1 — {tên ngắn vd "MVP"}

- **Goal**: Mục tiêu chính của wave này (1-2 câu).
- **Boundaries in scope**: `{boundary-1}`, `{boundary-2}`, ...
- **Features**: `FEAT-001`, `FEAT-002`, ...
- **Estimated effort**: {N weeks}
- **Rationale**: Vì sao wave 1 chọn các boundaries/features này (vd: auth + customer là foundation cho mọi tính năng sau).
- **Exit criteria**: Khi nào wave 1 considered done (vd: smoke test + UAT pass, có thể deploy staging).
- **Plan detail**: [wave-001.md](wave-001.md)

### Wave 2 — {tên}

- **Goal**: ...
- **Boundaries in scope**: ...
- **Features**: ...
- **Estimated effort**: ...
- **Rationale**: Vì sao wave 2 follow sau wave 1 (vd: cần customer trong wave 1 mới làm order ở wave 2 được).
- **Dependencies**: Phải có gì từ wave 1 (vd: customer-mgmt deployed).
- **Plan detail**: [wave-002.md](wave-002.md)

### Wave 3 — ...

...

## Cross-wave concerns

- **Tech stack** chốt ở ADR-001 (không đổi giữa các wave trừ khi có ADR mới).
- **Data migration strategy**: Mỗi wave có migration script riêng (Flyway versioned).
- **Backward compatibility**: Wave N+1 phải backward-compat với Wave N (rolling deployment).
- **Rollback**: Mỗi wave có rollback plan ghi trong wave-{N}.md.

## Resource estimation

| Wave | Backend devs | BFF devs | Web devs | Mobile devs | QA | Total weeks |
|------|--------------|----------|----------|-------------|-----|-------------|
| Wave 1 | 2 | 1 | 1 | 0 | 1 | 4 |
| Wave 2 | 2 | 1 | 1 | 0 | 1 | 4 |
| Wave 3 | 1 | 1 | 1 | 1 | 1 | 4 |
| **Total** | | | | | | **{N}** |

## Risks + mitigations

| Risk | Wave affected | Mitigation |
|------|---------------|-----------|
| {risk 1} | Wave N | {how to mitigate} |
| ... | ... | ... |

## Change history

| Date | CR / event | Change summary |
|------|-----------|----------------|
| {date} | initial | Created by program-planner-agent |
| {date} | CR-001 | Wave 2 add boundary X |
