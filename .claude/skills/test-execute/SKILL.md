---
name: test-execute
description: Build + run auto test theo registry per stack (mvn/gradle/pytest/jest/vitest/playwright/k6), ghi test-report.md, log bug (origin auto). KHÔNG fix — fix qua /fix-bugs ở MANUAL_TEST.
---

# Test Execute Skill

## Khi load
`test-execute-agent` ở `/test-execute` (state `TEST_EXECUTE`).

## Hoạt động
1. Đọc `tracking/wave-{N}/test-case-registry.md`.
2. Infra + service đã **UP + connectivity verified ở `/dev-handoff`** (giữ UP) — test-execute **KHÔNG tự dựng**. Sanity reachable (`docker compose ps` healthy / `curl -f /health/ready`); down → **STOP**, báo user chạy lại `/dev-handoff` (KHÔNG test ảo).
3. Foreach **auto** TC (P0 trước, rồi P1, P2) — chạy **black-box trên hệ thống ĐANG CHẠY** (KHÔNG build từ source, KHÔNG đo coverage — đó là việc DEV). Manual TC để dành `MANUAL_TEST`:
   - Run theo `type` (bảng dưới): **API smoke** (gọi endpoint thật theo `api-{boundary}.md` → assert status + shape + field nghiệp vụ) · **UI/e2e** (Playwright/integration_test — giao diện load, luồng chính render, action) · contract · perf.
   - Service/UI cần mà **chưa up → `skip`** (ghi lý do "service chưa up"), KHÔNG fail/fake.
   - Append kết quả vào `tracking/wave-{N}/test-report.md`: `TC-ID: pass|fail|skip` + timestamp + duration + log tail. Log chi tiết → `tracking/wave-{N}/test-logs/{TC-ID}.log`.
4. Foreach fail → **append 1 row** vào bảng `tracking/wave-{N}/bugs.md` (skill `bug-logging`; `origin: auto` + đủ cột `TC` + `AC` (từ `TC.ac` registry) + `error log` (excerpt `test-logs/{TC}.log`); **dedup theo TC — re-run cùng TC fail lại thì UPDATE row cũ, KHÔNG tạo row mới**). **KHÔNG spawn fix, KHÔNG loop** — bug auto fix qua `/fix-bugs` ở MANUAL_TEST.

## Loại TC + công cụ (black-box — hệ thống đang chạy)
| Loại TC | Công cụ | Kiểm |
|---|---|---|
| **API smoke** | curl / REST client / RestAssured / supertest | gọi endpoint thật → status + response shape + field nghiệp vụ (theo `api-{boundary}.md`) |
| **UI / e2e** | Playwright (web) / integration_test (mobile) | giao diện load, luồng chính render, action chạy, không lỗi console nghiêm trọng |
| contract | Pact | provider/consumer khớp |
| perf (NFR latency) | `k6 run` | threshold p99 |

> Unit/integration (white-box, build từ source) + coverage là của **DEV** (`/start-dev`), KHÔNG chạy lại ở đây.

## Coverage — KHÔNG đo ở đây
Coverage (unit/integration) là của **DEV** — đã gate ở `/review-dev` + `/dev-handoff` (per-kind: backend 80 / bff 70 / web·mobile 60). test-execute là **black-box smoke/e2e trên hệ thống đang chạy**, KHÔNG build source, **KHÔNG đo/gate coverage**.

## Chất lượng test (gate — không chỉ "pass")
- **Phủ registry**: mỗi **auto-TC trong registry phải được CHẠY thật** (gọi API / mở UI), không bỏ qua; skip chỉ khi service/UI chưa up (ghi lý do). KHÔNG đánh `pass` mà không gọi endpoint / không mở UI.
- **Deterministic**: dữ liệu test cô lập (seed/cleanup riêng); KHÔNG phụ thuộc state dư từ lần chạy trước.
- **Isolation**: mỗi TC tự setup + cleanup (xoá record nó tạo ra); KHÔNG phụ thuộc thứ tự chạy.
- **Flaky**: test chập chờn → tìm root cause (timing/shared-state/ordering), KHÔNG retry mù; chưa fix → quarantine + log bug.
- **Artifacts**: fail → lưu log tail + (e2e) screenshot/video vào `test-logs/`.

## Exit (auto-transition — KHÔNG cần command từ user)
- Chạy xong (pass HAY fail) → return `{test_result: "pass"|"fail", test_cases_count: N, coverage_pct, bugs_logged: [...]}` → harness auto-transition `TEST_EXECUTE → MANUAL_TEST` (kể cả còn bug auto).
- Fail → bug đã log (origin=auto) trong bugs.md → fix qua `/fix-bugs` ở MANUAL_TEST. Gate `no_open_bugs` (end-wave) đảm bảo đóng hết mới ship.
- **KHÔNG teardown infra** — giữ UP cho MANUAL_TEST (UAT + `/fix-bugs` re-run TC); teardown ở `/done-wave`.
- **Re-run từ MANUAL_TEST** (sau `/fix-bugs`): `/test-execute` chạy được lại để verify full suite. Dedup theo TC — TC fail lại → **reopen** (UPDATE row cũ = `status open`); TC pass → giữ `closed`; regression mới → log BUG mới. Lặp fix ↔ re-run tới khi sạch mới `/end-wave`.

> Format report: `tracking/_templates/TEMPLATE.test-report.md`. Bug model 1-file: `tracking/_templates/TEMPLATE.bugs.md`. Test chuyên sâu (contract/perf/security) → skill `specialist-testing`.
