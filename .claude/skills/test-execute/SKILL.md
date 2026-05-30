---
name: test-execute
description: Run auto test theo registry, ghi test-report.md, log bug (origin auto) nếu fail.
---

# Test Execute Skill

## Khi load
`test-execute-agent` ở `/test-execute` (state `TEST_EXECUTE`).

## Hoạt động
1. Đọc `tracking/wave-{N}/test-case-registry.md`.
2. `docker-compose up -d` (infra theo `docs/architecture/infra/docker-compose.yml`); chờ services healthy.
3. Foreach **auto** TC (P0 trước, rồi P1, P2) — manual TC để dành stage `MANUAL_TEST`:
   - Run cmd theo `type` (api → curl/httpie, e2e|ui → playwright/cypress, isolation → unit/integration runner).
   - Append kết quả vào `tracking/wave-{N}/test-report.md`: `TC-ID: pass|fail|skip` + timestamp + duration + log tail.
   - Ghi log chi tiết vào `tracking/wave-{N}/test-logs/{TC-ID}.log`.
4. Foreach fail → log bug `tracking/wave-{N}/bugs.md` (`origin: auto`, dùng skill `bug-logging`) → spawn `fix-{prefix}-{boundary}-agent` → quay lại bước 3 re-run TC đó. Internal loop tới khi pass.

## Exit (auto-transition — KHÔNG cần command từ user)
- Tất cả P0 pass → return `{test_result: "pass", test_cases_count: N}` → harness auto-transition `TEST_EXECUTE → MANUAL_TEST`.
- P0 còn fail sau loop → return `{test_result: "fail", ...}` → KHÔNG transition; báo blocker cho user.

> Format report: `tracking/_templates/TEMPLATE.test-report.md`. Bug model 1-file: `tracking/_templates/TEMPLATE.bugs.md`.
