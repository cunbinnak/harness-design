# Tracking

Per-wave tracking artifacts. Flat structure (không nested).

## Cấu trúc

```
tracking/
├── README.md                          (this file)
├── _templates/
│   ├── TEMPLATE.test-case-registry.md (test-plan agent fill)
│   ├── TEMPLATE.test-report.md        (test-execute agent fill)
│   ├── TEMPLATE.bugs.md               (test-execute + fix-bugs append)
│   ├── TEMPLATE.qc-signoff.md         (end-wave agent fill)
│   └── TEMPLATE.cr.md                 (user create CR)
├── wave-001/
│   ├── change-requests/
│   │   └── CR-NNN-*.md                (CR affecting this wave)
│   ├── test-case-registry.md
│   ├── test-report.md
│   ├── test-logs/                     (per-TC proof, gitignored)
│   │   ├── TC-*.log
│   │   └── screenshots/
│   ├── bugs.md
│   └── qc-signoff.md
└── wave-002/
    └── ...
```

## Per-wave files

| File | Created by | Updated by | Purpose |
|------|-----------|------------|---------|
| `test-case-registry.md` | `/test-plan` (test-plan-agent) | Initial only | TC list, AC trace, type=auto\|manual |
| `test-report.md` | `/test-execute` (test-execute-agent) | Initial only | Aggregate test results với per-TC log refs |
| `test-logs/TC-*.log` | `/test-execute` | Per-TC append | Proof per TC: cmd, response, result |
| `test-logs/screenshots/*.png` | `/test-execute` | UI tests | UI test evidence (Playwright/Cypress) |
| `bugs.md` | `/test-execute` + `/fix-bugs` | Append per bug | Bug tickets với heading + frontmatter |
| `qc-signoff.md` | `/end-wave` (end-wave-agent) | Final signoff | UAT result + stakeholder approval |
| `change-requests/CR-*.md` | User manual | `/apply-cr` agent fill plan | CR affecting this wave's scope |

## Bugs.md format

Mỗi bug = heading `## BUG-NNN — title` + YAML frontmatter:

```markdown
## BUG-001 — Validation 500 instead of 400

```yaml
status: open | in_progress | fixed | closed | wontfix
origin: auto | manual | framework
severity: critical | high | medium | low
boundary: order-mgmt
detected_by: test-execute-agent
detected_at: "2026-05-29T..."
```

### Reproduce
...
### Expected
...
### Actual
...
### Fix
...
```

**Gate `no_open_bugs`** parse heading + status frontmatter → reject `/end-wave` nếu còn bug `status: open`.

## CR per-wave

Change Request lưu trong **wave folder bị ảnh hưởng**, không cross-wave global.

- CR-NNN raised mid wave-001 affecting wave-002 → `tracking/wave-002/change-requests/CR-NNN-*.md`
- Sau done-wave-001, user chạy `/apply-cr CR-NNN` → analyze CR + plan amendment cho intake wave-002

## Workflow

```
/test-plan
  → write tracking/wave-{N}/test-case-registry.md (from TEMPLATE)

/test-execute
  → run TCs với proof
  → write tracking/wave-{N}/test-report.md
  → append bugs.md nếu fail (origin: auto)
  → internal fix loop → re-test

(auto-transition) MANUAL_TEST
  → stakeholder UAT
  → user chạy /fix-bugs nếu phát hiện (origin: manual)
  → write qc-signoff.md với UAT results + sign

/end-wave
  → verify no_open_bugs + qc-signoff signed
  → finalize qc-signoff.md
  → state → DONE

/done-wave
  → teardown infra
  → archive vào handoff/wave-{N}.md
  → state → BOOTSTRAP
```

## Liên quan

- [agents/test-plan-agent.md](../agents/test-plan-agent.md)
- [agents/test-execute-agent.md](../agents/test-execute-agent.md)
- [agents/end-wave-agent.md](../agents/end-wave-agent.md)
- [agents/done-wave-agent.md](../agents/done-wave-agent.md)
- [agents/apply-cr-agent.md](../agents/apply-cr-agent.md)
- Root [CLAUDE.md](../CLAUDE.md) routing table
