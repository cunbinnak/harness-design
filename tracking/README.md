# Tracking

Per-wave tracking artifacts. Flat structure (không nested).

> **3 thang phân loại** (bug `sev` high/med/low · review `severity` BLOCKER/MAJOR/MINOR/NIT/QUESTION · TC `pri` P0/P1/P2) — mapping nhất quán + test_type/tag taxonomy: `docs/architecture/SEVERITY-TEST-TAXONOMY.md` (SSOT).

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
| `bugs.md` | `/test-execute` (auto) + `/log-bug` (manual) + `/fix-bugs` (close) | Append per bug (row) | Bug tickets dạng **bảng** (1 row/bug) |
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
- Findings sống **theo wave, trước bàn giao**: rà sạch thì đóng, không mang sang wave sau.

## Đổi ý giữa chừng

Không có sổ change-request riêng. Phát hiện thiếu sót sau khi wave đã chốt scope → **đẩy sang wave
sau**: lùi `/domain` (gọi được từ DESIGN/PLAN/REVIEW) sửa tài liệu, wave kế nhận. Sửa tại chỗ một
wave đã ship là cách chắc chắn nhất làm gãy thứ wave đó đã giao.

## Chốt nào ghi cái gì

```
review-dev
  review-{kind}-agent  → review-findings.md (mỗi finding một row)
  MAIN đọc findings    → spawn fix → fix set status=resolved → review lại
  gate no_open_findings chặn tới khi BLOCKER/MAJOR sạch

test-plan
  test-plan-agent      → test-case-registry.md

test-execute
  test-execute-agent   → test-report.md (BLACK-BOX: gọi API/UI hệ đang chạy)
  TC fail              → sửa rồi chạy lại chốt này; test_report là nơi duy nhất giữ kết quả

dogfood
  dogfood-{vai}-agent  → dogfood-report.md (6 lăng kính x 2 đợt)

end-wave
  qc-signoff.md ký + test_result=pass + backward_compat + production_ready → DONE

next-wave
  next_wave.py         → archive/wave-{N}/ (snapshot TOÀN BỘ tài liệu) + DELIVERED.md
                         BC-LEDGER §3 và mục "(mỗi wave)" của PRODUCTION-READY bị bỏ tick
```

## Sổ sống xuyên wave

| File | Vai trò |
|---|---|
| `BC-LEDGER.md` | Sổ hợp đồng surface — §1 tích luỹ vĩnh viễn, §3 rà lại mỗi wave |
| `PRODUCTION-READY.md` | Sẵn sàng vận hành, 4 nhóm — mục `(mỗi wave)` re-arm khi mở wave |
| `challenge-log.md` | Chất vấn spec trước khi code — FAIL thì chưa được code |
| `decisions.md` | Quyết định agent tự ra lúc gặp mơ hồ (`py scripts/decide.py`) |

## Liên quan

- [agents/test-plan-agent.md](../agents/test-plan-agent.md)
- [agents/test-execute-agent.md](../agents/test-execute-agent.md)
- [agents/end-wave-agent.md](../agents/end-wave-agent.md)
- Router [CLAUDE.md](../CLAUDE.md)
