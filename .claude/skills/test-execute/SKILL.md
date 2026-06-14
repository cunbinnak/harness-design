---
name: test-execute
description: Chạy auto TC BLACK-BOX trên hệ thống ĐANG CHẠY (API qua curl/REST client, UI/e2e qua Playwright, perf k6) — KHÔNG build source, KHÔNG mvn/gradle/vitest, KHÔNG đo coverage (đó là việc DEV). Ghi test-report.md, log bug (origin auto). KHÔNG fix — fix qua /fix-bugs ở MANUAL_TEST.
---

# Test Execute Skill

## Khi load
`test-execute-agent` ở `/test-execute` (state `TEST_EXECUTE`).

## Hoạt động
1. Đọc `tracking/wave-{N}/test-case-registry.md`.
2. Infra + service đã **UP + connectivity verified ở `/dev-handoff`** (giữ UP) — test-execute **KHÔNG tự dựng**. Sanity reachable (`docker compose ps` healthy / `curl -f /health/ready`); down → **STOP**, báo user chạy lại `/dev-handoff` (KHÔNG test ảo).
3. Foreach **auto** TC (P0 trước, rồi P1, P2) — chạy **black-box trên hệ thống ĐANG CHẠY** (KHÔNG build từ source, KHÔNG đo coverage — đó là việc DEV). Manual TC để dành `MANUAL_TEST`:
   - **TC tag `@deferred` (G1)** — AC/feature đã khai báo `## Deferred to later waves` ở wave plan: `skip(deferred)`, ghi `note: deferred wave-N`, **KHÔNG log bug, KHÔNG tính fail** (out-of-scope, không chặn end-wave). (Tag mà wave plan KHÔNG khai báo → coi in-scope, vẫn phải chạy — chống né test.)
   - Run theo `group` (bảng dưới): **API smoke** (gọi endpoint thật theo `api-{boundary}.md` → assert status + shape + field nghiệp vụ) · **UI/e2e** (Playwright/integration_test — giao diện load, luồng chính render, action) · contract · perf.
   - `skip` CHỈ khi service/UI thật sự **down** (ghi lý do "service chưa up" **vào log file**), KHÔNG fail/fake. **Thiếu UI driver (Playwright) KHÔNG phải lý do skip** — provision là bước setup bắt buộc (`npx playwright install chromium`); cài fail thật → log bug `layer=infra`, KHÔNG skip cho qua.
   - Append kết quả vào `tracking/wave-{N}/test-report.md`: `TC-ID: pass|fail|skip` + timestamp + duration + **network-call** (`<METHOD> <path> → <status>`) + log tail. Log chi tiết → `tracking/wave-{N}/test-logs/{TC-ID}.log`.
4. Foreach fail → **append 1 row** vào bảng `tracking/wave-{N}/bugs.md` (skill `bug-logging`) với **routing metadata đủ để fix Mode A KHÔNG đoán mò** (bảng §Bug routing). **dedup theo TC — re-run cùng TC fail lại thì UPDATE row cũ, KHÔNG tạo row mới**. **KHÔNG spawn fix, KHÔNG loop** — bug auto fix qua `/fix-bugs` ở MANUAL_TEST.

> **Gate `test_evidence` (G12) sẽ chặn complete nếu thiếu bằng chứng đã-chạy** (không phải vì TC fail — fail là bug hợp lệ). Mỗi auto-TC in-scope phải: (a) có result trong test-report; (b) group integration/e2e/perf/security khi pass|fail phải có dòng `METHOD path -> status` trong `test-logs/{TC}.log`; (c) skip phải nêu lý do service-down trong log. **test_result do HARNESS DERIVE từ report** (auto-TC in-scope all-pass → pass) — tự khai pass mà report có fail in-scope sẽ bị end-wave chặn.

## Loại TC + công cụ (black-box — hệ thống đang chạy)
| Loại TC (`group`) | Công cụ | Kiểm |
|---|---|---|
| **API smoke / functional / integration** | curl / REST client / RestAssured / supertest | gọi endpoint thật → status + response shape + field nghiệp vụ (theo `api-{boundary}.md`) |
| **UI / e2e** | Playwright (web — `npx playwright install chromium` nếu thiếu) / integration_test (mobile) | giao diện load, **render đúng style/UX (không trắng/không-style)**, luồng chính render, action chạy, không lỗi console nghiêm trọng |
| contract | Pact | provider/consumer khớp |
| performance (NFR latency) | `k6 run` | threshold p95/p99 + error rate (SLO từ `PROJECT.md`) |
| security | curl negative + dependency scan | 401/403 đúng; injection/authz-bypass bị chặn |
| accessibility | axe / Lighthouse | 0 critical violation (CHỈ wave full-stack FE) |

> Unit/integration (white-box, build từ source) + coverage là của **DEV** (`/start-dev`), KHÔNG chạy lại ở đây.

## Anti-fake (real-test invariant — KHÔNG được giả PASS)
- **KHÔNG `echo PASS` / mock response / hardcode `{status:ok}`** — phải GỌI endpoint thật / mở UI thật.
- **Connectivity pre-check** mỗi target: unreachable → TC `skip` (lý do "service chưa up") + (nếu critical) STOP, KHÔNG giả vờ pass.
- **Network call bắt buộc** cho group ∈ {integration, e2e, performance, security}: log `<METHOD> <path> → <status>` (vd `POST /v1/auth/login → 200`) — không có = không tính đã chạy.
- **Evidence**: mỗi pass/fail có log tail thật trong `test-logs/`; fail (e2e) thêm screenshot/video.

## Bug routing metadata (cột bắt buộc cho `origin: auto` — đủ tín hiệu fix Mode A)
| Cột | Nguồn | Vì sao |
|---|---|---|
| `origin` | `auto` (test-execute) / `manual` (UAT) | dev filter nguồn |
| `boundary` | từ `TC.boundary` registry | route đúng dev boundary |
| `layer` | judgement: backend / frontend / integration / data / infra | route đúng tầng (vd FE↔BE mismatch = integration) |
| `sev` | hậu quả thực tế khi fail → `SEVERITY-TEST-TAXONOMY §2.1` (KHÔNG suy máy móc từ pri) | ưu tiên fix |
| `TC` | TC-ID detect ra bug | link verify |
| `AC` | `TC.ac` registry (`FEAT-N:AC-M`) | biết AC nào vỡ |
| reproduce / expected / actual | từ TC + observed | dev repro exact |
| `error log` | excerpt từ `test-logs/{TC}.log` | stack trace / status sai |

> sev gán theo HẬU QUẢ (data loss/auth bypass → high; UX defect → medium; cosmetic/edge → low), không từ TC pri máy móc — bảng lookup `SEVERITY-TEST-TAXONOMY §2.1`. Gate `no_open_bugs` đọc cột `status` (KHÔNG đọc `sev`), nên mọi bug open đều chặn end-wave như nhau.

## Coverage — KHÔNG đo ở đây
Coverage (unit/integration) là của **DEV** — đã gate ở `/review-dev` + `/dev-handoff` (per-kind: backend 80 / bff 70 / web·mobile 60). test-execute là **black-box smoke/e2e trên hệ thống đang chạy**, KHÔNG build source, **KHÔNG đo/gate coverage**.

## Chất lượng test (gate — không chỉ "pass")
- **Phủ registry**: mỗi **auto-TC trong registry phải được CHẠY thật** (gọi API / mở UI), không bỏ qua; skip chỉ khi service/UI chưa up (ghi lý do). KHÔNG đánh `pass` mà không gọi endpoint / không mở UI.
- **Deterministic**: dữ liệu test cô lập (seed/cleanup riêng); KHÔNG phụ thuộc state dư từ lần chạy trước.
- **Isolation**: mỗi TC tự setup + cleanup (xoá record nó tạo ra); KHÔNG phụ thuộc thứ tự chạy.
- **Flaky**: test chập chờn → tìm root cause (timing/shared-state/ordering), KHÔNG retry mù; chưa fix → quarantine + log bug.
- **Artifacts**: fail → lưu log tail + (e2e) screenshot/video vào `test-logs/`.

## Exit (auto-transition — KHÔNG cần command từ user)
- Chạy xong (pass HAY fail) → return `{test_result: "pass"|"fail", test_cases_count: N, bugs_logged: [...]}` (KHÔNG coverage_pct — black-box) → harness auto-transition `TEST_EXECUTE → MANUAL_TEST` (kể cả còn bug auto). **Harness DERIVE lại `test_result` từ test-report.md** (in-scope auto-TC all-pass → pass; deferred bỏ qua) — giá trị honest này là cái end-wave gate đọc.
- Fail → bug đã log (origin=auto) trong bugs.md → fix qua `/fix-bugs` ở MANUAL_TEST. Gate `no_open_bugs` (end-wave) đảm bảo đóng hết mới ship.
- **KHÔNG teardown infra** — giữ UP cho MANUAL_TEST (UAT + `/fix-bugs` re-run TC); teardown ở `/done-wave`.
- **Re-run từ MANUAL_TEST** (sau `/fix-bugs`): `/test-execute` chạy được lại để verify full suite. Dedup theo TC — TC fail lại → **reopen** (UPDATE row cũ = `status open`); TC pass → giữ `closed`; regression mới → log BUG mới. Lặp fix ↔ re-run tới khi sạch mới `/end-wave`.

## QC sign-off (tổng kết wave — trước/khi end-wave)
Sau khi suite xanh + bug đóng hết, ghi quyết định ship vào `tracking/wave-{N}/qc-signoff.md` (`TEMPLATE.qc-signoff.md`):
- **APPROVED**: không bug open; coverage đạt ngưỡng per-kind → ship-ready.
- **CONDITIONAL**: còn S3/S4 backlog đã `wontfix` + lý do, hoặc gap nhỏ → ship + list điều kiện verify wave sau.
- **REJECTED**: còn bug S1/S2 open hoặc exit criteria fail → block, quay lại fix.

> `/end-wave` gate: `uat_signed` + `test_result=pass` + `no_open_bugs`. QC sign-off là tài liệu quyết định; gate đọc STATE/bugs.md, không parse sign-off.

> Format report: `tracking/_templates/TEMPLATE.test-report.md`. Bug model 1-file: `tracking/_templates/TEMPLATE.bugs.md`. Sign-off: `tracking/_templates/TEMPLATE.qc-signoff.md`. Test chuyên sâu (contract/perf/security) → skill `specialist-testing`.
