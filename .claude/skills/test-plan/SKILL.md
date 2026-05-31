---
name: test-plan
description: Sinh test-case-registry.md cho wave — TC per AC + enterprise coverage matrix (error paths, tenant isolation, idempotency, rate limit, concurrency). Test pyramid.
---

# Test Plan Skill

## Khi load
`test-plan-agent` ở `/test-plan` (state TEST_PLAN). Input: `FEAT-*.md` (AC) + `api-{boundary}.md` + `PROJECT.md` (NFR).

## Output: `tracking/wave-{N}/test-case-registry.md`
- Heading per TC: `## TC-{N}-{slug}`
- Frontmatter: `type: [api|e2e|ui|isolation|perf|security|contract], boundary: X, feature: FEAT-N, ac: FEAT-N:AC-M, priority: P0|P1|P2`
- Section: Pre-conditions · Steps · Expected · Data setup · Cleanup.

## Test pyramid (phân bổ)
- **unit/isolation** (nhiều): domain/service thuần, mock infra.
- **integration** (vừa): api + DB thật (Testcontainers), khớp contract.
- **e2e** (ít): luồng theo AC (Playwright cho FE).
- **perf** (chỉ khi NFR latency) · **security** (chỉ khi NFR security).

## Coverage matrix per AC (enterprise — không chỉ happy path)
Mỗi AC sinh TC cho các nhánh sau (bỏ nhánh không áp dụng):

| Nhánh | TC kỳ vọng |
|---|---|
| Happy path | đúng AC, status 2xx, response shape khớp `api-{boundary}.md` |
| Validation | input sai → **400** + error code |
| AuthN | thiếu/invalid token → **401** |
| AuthZ | sai role/permission → **403** |
| Not found | resource không tồn tại → **404** |
| Conflict | trạng thái xung đột / duplicate unique → **409** |
| Rate limit | vượt limit → **429** (nếu có) |
| **Tenant isolation** | tenant khác / sai `tenantId` → **403/404** (KHÔNG lộ data tenant khác) |
| **Ownership** | user không sở hữu resource → 403/404 |
| **Idempotency** | gửi trùng (callback/mutation có key) → KHÔNG tạo bản ghi/effect trùng |
| **Concurrency** | 2 update đồng thời → optimistic locking đúng (1 thắng, 1 báo conflict) |
| State transition | chuyển trạng thái không hợp lệ → bị chặn |

## Quy ước
1. Mỗi AC có ≥ 1 TC happy + TC cho error path/tenant/idempotency áp dụng được.
2. Smoke test cross-boundary cho mọi integration điểm (login + create + read).
3. P0 = blocker release · P1 = must-have · P2 = nice-to-have.
4. Contract TC: response/enum/error code khớp `api-{boundary}.md` (deep → `specialist-testing`).

## Done
- Mọi AC trace ≥ 1 TC; endpoint nhạy cảm có error paths + tenant isolation + idempotency + concurrency; priority gán đúng.
