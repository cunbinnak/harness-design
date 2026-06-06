---
name: test-execute
description: Build + run auto test theo registry per stack (mvn/gradle/pytest/jest/vitest/playwright/k6), ghi test-report.md, log bug (origin auto), loop fix tới pass.
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
4. Foreach fail → log bug `tracking/wave-{N}/bugs.md` (`origin: auto`, skill `bug-logging`; **dedup theo TC-ID — re-run cùng TC fail lại thì UPDATE bug cũ, KHÔNG tạo bug mới**) → spawn `fix-{prefix}-{boundary}-agent` → quay lại bước 3 re-run TC đó. Internal loop tới khi pass.

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
- Dưới ngưỡng = fail → loop fix (hoặc báo blocker).

## Chất lượng test (gate — không chỉ "pass")
- **Phủ registry**: mỗi **auto-TC trong registry phải có test code** trước khi chạy; thiếu → viết bổ sung (theo `type`/AC) rồi chạy. KHÔNG để TC registry không có code = sót AC.
- **Deterministic**: inject Clock/seed; KHÔNG dùng time/random/network thật → chạy lại cùng kết quả.
- **Isolation**: mỗi test tự setup + cleanup state (reset DB/cache giữa test); KHÔNG phụ thuộc thứ tự chạy.
- **Coverage có nghĩa**: ưu tiên branch coverage; loại generated code; KHÔNG viết test rỗng kéo %.
- **Flaky**: test chập chờn → tìm root cause (timing/shared-state/ordering), KHÔNG retry mù; chưa fix → quarantine + log bug.
- **Artifacts**: fail → lưu log tail + (e2e) screenshot/video vào `test-logs/`.

## Exit (auto-transition — KHÔNG cần command từ user)
- Tất cả P0 pass + coverage đạt → return `{test_result: "pass", test_cases_count: N, coverage_pct: ...}` → harness auto-transition `TEST_EXECUTE → MANUAL_TEST`.
- P0 còn fail sau loop → return `{test_result: "fail", ...}` → KHÔNG transition; báo blocker.

> Format report: `tracking/_templates/TEMPLATE.test-report.md`. Bug model 1-file: `tracking/_templates/TEMPLATE.bugs.md`. Test chuyên sâu (contract/perf/security) → skill `specialist-testing`.
