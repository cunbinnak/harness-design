# Bugs — wave-{N}

> **Mỗi bug = 1 HÀNG.** Gate `no_open_bugs` đếm `status ∉ {closed, fixed}` → chặn `/end-wave`. (Gate đọc cột `BUG` + `status`; KHÔNG đọc `sev`/`layer`.)
> Bug do **test-execute** (auto) / **UAT** (manual) sinh ra, fix qua `/fix-bugs` (Mode A). Cập nhật bởi: `test-execute` (append row) · `fix-bugs` (sửa → set `status` = closed).
> Enum — status: `open | in_progress | fixed | closed | wontfix` · origin: `auto | manual` · sev: `high | medium | low` · layer: `backend | frontend | integration | data | infra`.
> Gán `sev` theo HẬU QUẢ thực tế (S1-S4), KHÔNG suy máy móc từ TC pri (vd P0 fail nhưng chỉ edge-case không reproduce 100% → `low`). Map S1-S4 → sev + lookup TC-fail→sev: `docs/architecture/SEVERITY-TEST-TAXONOMY.md` §1, §2, §2.1.
>
> **Cột bắt buộc cho `origin: auto`** (đủ tín hiệu route + fix Mode A, KHÔNG đoán mò): `boundary` (route dev) · `layer` (route tầng) · `TC` (detected_in) · `AC` (ac_violated FEAT-N:AC-M, lấy từ `TC.ac` registry) · `error log` (excerpt từ `test-logs/{TC}.log`) · reproduce/expected/actual. Ghi `repro %` (100% / intermittent) trong `reproduce` nếu flaky.

| BUG | title | status | origin | sev | layer | boundary | TC | AC | reproduce | expected | actual | error log | root cause | fix |
|-----|-------|--------|--------|-----|-------|----------|----|----|-----------|----------|--------|-----------|------------|-----|
| BUG-001 | empty payload → 500 | closed | auto | high | backend | order-mgmt | TC-I02 | FEAT-001:AC-2 | `POST /v1/orders -d '{}'` (100%) | 400 VALIDATION_ERROR | 500 | `expected 400 got 500` (TC-I02.log) | thiếu @Valid → NPE ở service | +@Valid +@NotNull; +TC-R01 |
| BUG-002 | pagination cursor invalid | open | manual | medium | frontend | order-mgmt | — | FEAT-001:AC-5 | Next page khi list >20 (100%) | cursor next 20 items | empty list | `cursor decode error` | _(fix điền)_ | _(fix điền)_ |
| BUG-003 | FE gửi sai field name | open | auto | medium | integration | web-order | TC-E01 | FEAT-002:AC-1 | submit form create order | 201 created | 400 (FE↔BE field mismatch) | `unknown field 'qty'` (TC-E01.log) | _(fix điền)_ | _(fix điền)_ |

## Notes
- `/end-wave` chỉ allow khi không còn bug `status ∈ {open, in_progress}` (gate `no_open_bugs` đọc cột `status`).
- **Fix Mode A** đọc HÀNG `BUG-NNN` → sửa → set ô `status` = `closed` + thêm regression `TC-R*` vào registry. Dev route theo `boundary` + `layer` (integration → cả BE+FE đọc).
- `origin`: `auto` (test-execute sinh bug) · `manual` (UAT/MANUAL_TEST). Bug ở đây fix qua `/fix-bugs` (Mode A).
- **S3/S4 backlog** muốn ship: phải đóng tường minh `status=wontfix` + lý do ở cột `fix`/`root cause` (không để lửng `open`) — `SEVERITY-TEST-TAXONOMY §2` quy tắc 3.
