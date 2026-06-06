---
name: test-plan
description: Sinh test-case-registry.md cho wave — TC per AC + enterprise coverage matrix (error paths, tenant isolation, idempotency, rate limit, concurrency). Test pyramid.
---

# Test Plan Skill

## Khi load
`test-plan-agent` ở `/test-plan` (state TEST_PLAN). Input: `FEAT-*.md` (AC) + `api-{boundary}.md` + `PROJECT.md` (NFR).

> **Vai trò: THIẾT KẾ test case** (viết spec vào registry) — KHÔNG viết code test, KHÔNG chạy. Code test do **dev** viết khi code (mỗi AC có test, `rules §N`); `/test-execute` chạy + bổ sung test còn thiếu so với registry.

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
| **Event/async** (boundary phát/nhận) | consumer xử lý đúng; **trùng event → idempotent** (no dup effect); lỗi → **DLQ/retry**; KHÔNG giả định thứ tự |
| **Security** (khi NFR security) | theo `review-backend §B2` (OWASP): injection / SSRF / mass-assignment / deserialization / authz-bypass |

## Kỹ thuật thiết kế TC + dữ liệu test
- **Boundary value**: field có range/length → test `min`, `min-1`, `max`, `max+1`, `0`, rỗng.
- **Equivalence partition**: nhóm input tương đương → 1 TC/nhóm (1 hợp lệ + từng loại không hợp lệ).
- **Decision table**: BR nhiều điều kiện → bảng tổ hợp điều kiện → kết quả kỳ vọng (phủ tổ hợp quan trọng).
- **State-transition**: entity có `status` → test MỌI chuyển hợp lệ + ≥1 chuyển bị cấm (khớp state machine `data-model`).
- **Edge data**: null/empty · unicode/ký tự đặc biệt · số âm/0 · precision tiền tệ · timezone/DST · chuỗi cực dài.
- **Dữ liệu test**: deterministic (seed cố định, inject Clock) · độc lập per TC (không phụ thuộc TC khác) · tự cleanup · KHÔNG dùng data prod.

## Quy ước
1. Mỗi AC có ≥ 1 TC happy + TC cho error path/tenant/idempotency áp dụng được.
2. Smoke test cross-boundary cho mọi integration điểm (login + create + read).
3. P0 = blocker release · P1 = must-have · P2 = nice-to-have.
4. Contract TC: response/enum/error code khớp `api-{boundary}.md` (deep → `specialist-testing`).
5. **Traceability 2 chiều**: mọi AC `Must` → ≥1 TC (không AC mồ côi); mọi TC → đúng 1 AC (không TC thừa không trace).

## Done
- Mọi AC trace ≥ 1 TC (2 chiều); endpoint nhạy cảm có error paths + tenant isolation + idempotency + concurrency; event boundary có TC idempotent/DLQ; priority gán đúng.
