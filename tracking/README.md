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
│   ├── TEMPLATE.review-findings.md    (review-dev: review ghi, fix set resolved)
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
│   ├── review-findings.md             (review-dev pre-handoff, ephemeral theo wave)
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
| `review-findings.md` | `/review-dev` (review-{kind}-agent ghi) | review append/update row + fix set `resolved` | Findings review pre-handoff dạng **bảng** (1 row/finding); gate `no_open_findings` |
| `bugs.md` | `/test-execute` + `/fix-bugs` | Append per bug (row) | Bug tickets dạng **bảng** (1 row/bug) |
| `qc-signoff.md` | `/end-wave` (end-wave-agent) | Final signoff | UAT result + stakeholder approval |
| `change-requests/CR-*.md` | User manual | `/apply-cr` agent fill plan | CR affecting this wave's scope |

## Bugs.md format

**Format BẢNG — mỗi bug = 1 HÀNG** (theo `_templates/TEMPLATE.bugs.md`):

```markdown
| BUG | title | status | origin | sev | boundary | TC | AC | reproduce | expected | actual | error log | root cause | fix |
|-----|-------|--------|--------|-----|----------|----|----|-----------|----------|--------|-----------|------------|-----|
| BUG-001 | empty payload → 500 | closed | auto | high | order-mgmt | TC-I02 | FEAT-001:AC-2 | `POST /orders -d '{}'` | 400 | 500 | `got 500` | thiếu @Valid | +@Valid |
```

- Auto-bug (test-execute) bắt buộc đủ `TC` + `AC` + `error log` (excerpt `test-logs/{TC}.log`).

**Gate `no_open_bugs`** parse cột `status` của bảng → reject `/end-wave` nếu còn bug `status ∈ {open, in_progress}`.

## Review-findings.md format

**Format BẢNG — mỗi finding = 1 HÀNG** (theo `_templates/TEMPLATE.review-findings.md`). Sản phẩm của `/review-dev` (review ghi, MAIN spawn fix theo row, fix set `resolved`):

```markdown
| FINDING | severity | status | boundary | file | type | description | suggested fix |
|---------|----------|--------|----------|------|------|-------------|---------------|
| RF-001 | BLOCKER | resolved | order | OrderService.java:42 | BR | BR-001 chưa enforce | check trước save |
```

- review ghi row `status=open`; fix Mode B sửa → set `resolved`; review re-review xác nhận.
- **Gate `no_open_findings`** reject `/review-dev complete` nếu còn row `severity ∈ {BLOCKER, MAJOR}` mà `status=open`. `MINOR/NIT/QUESTION` không chặn (set `accepted`/`wontfix`).
- Khác `bugs.md`: findings là **pre-handoff, ephemeral theo wave**; bugs là auto/manual (test-execute/UAT) sống tới end-wave.

## CR per-wave

Change Request lưu trong **wave folder bị ảnh hưởng**, không cross-wave global.

- CR-NNN raised mid wave-001 affecting wave-002 → `tracking/wave-002/change-requests/CR-NNN-*.md`
- Sau done-wave-001, user chạy `/apply-cr CR-NNN` → analyze CR + plan amendment cho intake wave-002

## Workflow

```
/review-dev
  → review-{kind}-agent ghi tracking/wave-{N}/review-findings.md (row/finding)
  → MAIN đọc findings → spawn fix Mode B → fix set status=resolved → re-review
  → gate no_open_findings chặn complete tới khi BLOCKER/MAJOR sạch

/test-plan
  → write tracking/wave-{N}/test-case-registry.md (from TEMPLATE)

/test-execute
  → run TCs với proof
  → write tracking/wave-{N}/test-report.md
  → append bugs.md nếu fail (origin: auto). KHÔNG fix ở đây
  → transition MANUAL_TEST (pass HAY fail); bug auto fix qua /fix-bugs

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
