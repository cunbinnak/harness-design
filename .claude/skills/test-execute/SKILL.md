---
name: test-execute
description: Build + run auto test theo registry per stack (mvn/gradle/pytest/jest/vitest/playwright/k6), ghi test-report.md, log bug (origin auto). KHÔNG fix — fix qua /fix-bugs ở MANUAL_TEST.
---

# Test Execute Skill

## Khi load
`test-execute-agent` ở `/test-execute` (state `TEST_EXECUTE`).

## Hoạt động
1. Đọc `tracking/wave-{N}/test-case-registry.md`.
2. `docker-compose up -d` (infra theo `docs/architecture/infra/docker-compose.yml`); chờ services healthy.
3. Foreach **auto** TC (P0 trước, rồi P1, P2) — manual TC để dành stage `MANUAL_TEST`:
   - Run cmd theo `type` (xem bảng framework dưới).
   - Append kết quả vào `tracking/wave-{N}/test-report.md`: `TC-ID: pass|fail|skip` + timestamp + duration + log tail.
   - Ghi log chi tiết vào `tracking/wave-{N}/test-logs/{TC-ID}.log`.
4. Foreach fail → **append 1 row** vào bảng `tracking/wave-{N}/bugs.md` (skill `bug-logging`; `origin: auto` + đủ cột `TC` + `AC` (từ `TC.ac` registry) + `error log` (excerpt `test-logs/{TC}.log`); **dedup theo TC — re-run cùng TC fail lại thì UPDATE row cũ, KHÔNG tạo row mới**). **KHÔNG spawn fix, KHÔNG loop** — bug auto fix qua `/fix-bugs` ở MANUAL_TEST.

## Framework + lệnh chạy theo stack
| Kind / Stack | Unit + Coverage | Integration | E2E / khác |
|---|---|---|---|
| backend Java/Spring | `mvn -q test jacoco:report` (hoặc `./gradlew test jacocoTestReport`) | `@SpringBootTest` + **Testcontainers** (DB thật, KHÔNG prod) | — |
| backend Python | `pytest --cov=. --cov-report=xml` | `TestClient` + testcontainers | — |
| bff/web Node | `npm test -- --coverage` / `npx vitest run --coverage` | `supertest` / MSW + Apollo mock | — |
| mobile Flutter | `flutter test --coverage` | widget + integration_test | — |
| e2e (web) | — | — | `npx playwright test` |
| perf (NFR latency) | — | — | `k6 run` (threshold p99) |

## Coverage gate (per-kind)
- Đọc coverage report (JaCoCo/coverage.xml/lcov) → so ngưỡng kind: **backend 80 / bff 70 / web·mobile 60**.
- Dưới ngưỡng = fail (ngưỡng coverage chính enforce ở `/dev-handoff`; ở đây report lại trong test_result).

## Chất lượng test (gate — không chỉ "pass")
- **Phủ registry**: mỗi **auto-TC trong registry phải có test code** trước khi chạy; thiếu → viết bổ sung (theo `type`/AC) rồi chạy. KHÔNG để TC registry không có code = sót AC.
- **Deterministic**: inject Clock/seed; KHÔNG dùng time/random/network thật → chạy lại cùng kết quả.
- **Isolation**: mỗi test tự setup + cleanup state (reset DB/cache giữa test); KHÔNG phụ thuộc thứ tự chạy.
- **Coverage có nghĩa**: ưu tiên branch coverage; loại generated code; KHÔNG viết test rỗng kéo %.
- **Flaky**: test chập chờn → tìm root cause (timing/shared-state/ordering), KHÔNG retry mù; chưa fix → quarantine + log bug.
- **Artifacts**: fail → lưu log tail + (e2e) screenshot/video vào `test-logs/`.

## Exit (auto-transition — KHÔNG cần command từ user)
- Chạy xong (pass HAY fail) → return `{test_result: "pass"|"fail", test_cases_count: N, coverage_pct, bugs_logged: [...]}` → harness auto-transition `TEST_EXECUTE → MANUAL_TEST` (kể cả còn bug auto).
- Fail → bug đã log (origin=auto) trong bugs.md → fix qua `/fix-bugs` ở MANUAL_TEST. Gate `no_open_bugs` (end-wave) đảm bảo đóng hết mới ship.
- **KHÔNG teardown infra** — giữ UP cho MANUAL_TEST (UAT + `/fix-bugs` re-run TC); teardown ở `/done-wave`.
- **Re-run từ MANUAL_TEST** (sau `/fix-bugs`): `/test-execute` chạy được lại để verify full suite. Dedup theo TC — TC fail lại → **reopen** (UPDATE row cũ = `status open`); TC pass → giữ `closed`; regression mới → log BUG mới. Lặp fix ↔ re-run tới khi sạch mới `/end-wave`.

> Format report: `tracking/_templates/TEMPLATE.test-report.md`. Bug model 1-file: `tracking/_templates/TEMPLATE.bugs.md`. Test chuyên sâu (contract/perf/security) → skill `specialist-testing`.
