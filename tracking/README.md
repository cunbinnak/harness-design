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
| `qc-signoff.md` | `/end-wave` (end-wave-agent) | Final signoff | UAT result + stakeholder approval |

## Ba sổ, ba loại sự thật

Không có sổ bug. Kết quả test vốn đã nằm ở `test-report.md`; thêm một sổ `BUG-NNN` chỉ là bản sao
thứ hai của cùng một sự thật, và hai bản sao thì sớm muộn lệch nhau.

| Sổ | Ai ghi | Chứa gì | Gate đọc |
|---|---|---|---|
| `test-report.md` + `test-logs/<TC>.log` | máy chạy ra | TC nào đỏ, **vì sao đỏ** (status + assert/exception) | `test_evidence` (FAIL phải đọc ra được nguyên nhân) · `test_passed` (còn đỏ thì không đóng wave) |
| `dogfood-report.md` §2 | người/agent quyết | phát hiện + **ô `Xử`** (`sửa ngay` · `chưa xử` · `wave sau`) | `dogfood_done` (ô trống = chưa ai quyết) |
| `review-findings.md` | review-agent | finding trước bàn giao, sống theo wave | `no_open_findings` (BLOCKER/MAJOR) |

Lượt sửa: `py scripts/build_prompt.py fix --tc TC-NNN --boundary <b>` → sửa → chạy lại chốt
`test-execute`. Report tự xanh, **không sổ nào phải đóng bằng tay**.

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
