# Plans

Roadmap dự án + per-wave plans. Flat structure (không nested).

## Cấu trúc

```
docs/plans/
├── README.md
├── TEMPLATE.WAVE-SEQUENCE.md   (template roadmap)
├── TEMPLATE.wave.md            (template per-wave)
├── WAVE-SEQUENCE.md            (plan sinh, full project roadmap)
├── wave-001.md                 (plan sinh, wave 1 detail)
├── wave-002.md
└── wave-NNN.md
```

## Files

| File | Created by | Purpose |
|------|-----------|---------|
| `TEMPLATE.WAVE-SEQUENCE.md` | repo (template) | Skeleton cho overall roadmap |
| `TEMPLATE.wave.md` | repo (template) | Skeleton cho per-wave detail |
| `WAVE-SEQUENCE.md` | program-planner-agent (stage PLAN, `plan`) | Full project roadmap: số wave, boundary breakdown, timeline, resource, risks |
| `wave-{NNN}.md` | program-planner-agent (stage PLAN, `plan`) | Per-wave plan: boundaries, features, dependencies, exit criteria, rollback |

## Workflow

```
plan — stage PLAN (program-planner):
  → Read PROJECT.md + FEAT-*.md + ADR + HLD per boundary
  → Write WAVE-SEQUENCE.md (overall roadmap với N waves)
  → Write wave-001.md … wave-00N.md (chi tiết MỌI wave)
  → Materialize harness/SERVICE-BOUNDARY-MATRIX.json (boundary metadata; gate stage ∈ {BOOTSTRAP, PLAN})
  → KG skeleton per boundary
  → Gate plan_gate → PLAN → REVIEW

start-wave <N>:  (sau /approve-document ở REVIEW)
  → Read wave-{NNN}.md
  → Verify boundaries trong MATRIX
  → Transition REVIEW → WAVE_OPEN
```

## Per-wave structure

Mỗi `wave-{NNN}.md` chứa:
- Overview (wave ID, goal, duration)
- Boundaries in scope
- Features in scope với AC count
- Dependencies cross-wave
- Implementation order
- Risks + mitigations
- Exit criteria
- Rollback plan

## Relationship với tracking/

`docs/plans/wave-{NNN}.md` = **kế hoạch trước khi làm**.
`tracking/wave-{NNN}/` = **artifacts trong và sau khi làm** (test cases, report, bugs, signoff).

## Liên quan

- [agents/program-planner-agent.md](../../agents/program-planner-agent.md)
- [agents/start-wave-agent.md](../../agents/start-wave-agent.md)
- [harness/SERVICE-BOUNDARY-MATRIX.json](../../harness/SERVICE-BOUNDARY-MATRIX.json)
- [tracking/README.md](../../tracking/README.md)
- Root [CLAUDE.md](../../CLAUDE.md)
