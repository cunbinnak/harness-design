# Bugs — wave-{N}

> **Mỗi bug = 1 HÀNG.** Gate `no_open_bugs` đếm `status ∉ {closed, fixed}` → chặn `/end-wave`.
> Cập nhật bởi: `test-execute` (append row, origin=auto) · `fix` (sửa → set `status` = closed) · `review` (origin=framework).
> Enum — status: `open | in_progress | fixed | closed | wontfix` · origin: `auto | manual | framework` · sev: `high | medium | low`.
>
> **Cột bắt buộc cho `origin: auto`** (đủ tín hiệu để fix Mode A, KHÔNG đoán mò): `TC` (detected_in) · `AC` (ac_violated FEAT-N:AC-M, lấy từ `TC.ac` registry) · `error log` (excerpt từ `test-logs/{TC}.log`) · reproduce/expected/actual.

| BUG | title | status | origin | sev | boundary | TC | AC | reproduce | expected | actual | error log | root cause | fix |
|-----|-------|--------|--------|-----|----------|----|----|-----------|----------|--------|-----------|------------|-----|
| BUG-001 | empty payload → 500 | closed | auto | high | order-mgmt | TC-I02 | FEAT-001:AC-2 | `POST /v1/orders -d '{}'` | 400 VALIDATION_ERROR | 500 | `expected 400 got 500` (TC-I02.log) | thiếu @Valid → NPE ở service | +@Valid +@NotNull; +TC-R01 |
| BUG-002 | pagination cursor invalid | open | manual | medium | order-mgmt | — | FEAT-001:AC-5 | Next page khi list >20 | cursor next 20 items | empty list | `cursor decode error` | _(fix điền)_ | _(fix điền)_ |
| BUG-003 | a11y color contrast | in_progress | framework | low | fe-web | — | — | axe-core scan button | contrast ≥ 4.5 (WCAG AA) | 2.85 (#999/#FFF) | `WCAG 1.4.3 fail` | text color #999 quá nhạt | → #666 |

## Notes
- `/end-wave` chỉ allow khi không còn bug `status ∈ {open, in_progress}` (gate `no_open_bugs` đọc cột `status`).
- **Fix Mode A** đọc HÀNG `BUG-NNN` → sửa → set ô `status` = `closed` + thêm regression `TC-R*` vào registry.
- `origin`: `auto` (test-execute) · `manual` (UAT/MANUAL_TEST) · `framework` (review tooling, vd axe-core).
- Findings của `/review-dev` **KHÔNG** vào đây (ephemeral, fix ngay trong review loop — Mode B). Chỉ bug `auto`/`manual`/`framework` mới log.
