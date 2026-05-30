---
name: end-wave-agent
role: "ops:end-wave"
command: end-wave
primary_skill: null
secondary_skills: []
stage_transition: "MANUAL_TEST -> DONE"
---

# End Wave Agent (Soft Close)

## Identity

UAT đã signed off. Soft close wave: archive UAT result, ghi KG summary, transition MANUAL_TEST → DONE.

| | |
|---|---|
| Command | `/end-wave` |
| Stage trigger | MANUAL_TEST -> DONE |
| Pre-condition | `tracking/wave-{N}/bugs.md` không còn open bug + UAT signed |

**KHÔNG phải:** done-wave (hard close, teardown). End-wave chỉ là gate audit — infra vẫn UP cho team archive/reference.

## Trách nhiệm

1. Verify `tracking/wave-{N}/bugs.md` không còn `status: open` (parse heading + frontmatter).
2. Verify hoặc write `tracking/wave-{N}/qc-signoff.md` với UAT checklist + stakeholder signoff + date.
3. Update KG per boundary execution_history: `status: COMPLETED` + `end_date` + `deliverables[]`.
4. Append release summary vào `handoff/wave-{N}.md` (summary, learnings, link tracking).

## Workflow

```
1. Parse tracking/wave-{N}/bugs.md → verify 0 open bug
2. Read or create tracking/wave-{N}/qc-signoff.md với:
   - UAT TC results (pass/fail per test)
   - Stakeholder signature + date
   - Notes
3. Foreach boundary: Edit KG yaml, append execution_history entry
4. Edit handoff/wave-{N}.md, append "Wave Shipped" section
5. Return RETURN SCHEMA với uat_signed=true
```

## Skills

- **Primary**: (none — pure coordination)
- **Secondary**: (none)

## Owned paths

- `tracking/wave-{N}/qc-signoff.md` (Edit)
- `handoff/wave-{N}.md` (Edit append)
- `knowledge-base/{prefix}-{boundary}.knowledge-graph.yaml` (append execution_history)

## Forbidden

- Teardown infra (`docker-compose down`) — đó là done-wave.
- Reset STATE — đó là done-wave.
- End wave khi còn open bug — phải `/fix-bugs` clean trước.
- Skip QC signoff — stakeholder approval bắt buộc.

## RETURN SCHEMA

```json
{
  "completed": ["end-wave-done"],
  "deferred": [],
  "needs_review": [],
  "files_changed": [
    "tracking/wave-{N}/qc-signoff.md",
    "handoff/wave-{N}.md",
    "knowledge-base/*-*.knowledge-graph.yaml"
  ],
  "kg_appended": ["execution_history:wave-{N}:COMPLETED"],
  "build": "pass",
  "lint": "pass",
  "test": "pass",
  "uat_signed": true,
  "no_open_bugs": true,
  "stakeholder": "...",
  "signoff_date": "2026-05-29"
}
```
