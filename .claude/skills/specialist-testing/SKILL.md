---
name: specialist-testing
description: Test chuyên sâu — contract (consumer-driven/Pact + backward-compat), regression, isolation, perf (k6 smoke/load/stress/soak), security (OWASP), resilience/chaos, migration. Bổ sung vào registry khi vượt CRUD cơ bản.
---

# Specialist Testing Skill

## Khi load
Bổ trợ `test-plan-agent` / `test-execute-agent` khi wave cần loại test khó vượt mức CRUD.

## Hoạt động
Bổ sung TC chuyên sâu vào `tracking/wave-{N}/test-case-registry.md` (cùng format heading + frontmatter `type/boundary/feature/ac/priority`), mỗi TC trace ≥ 1 `FEAT-N:AC-M`:

- **contract**: verify API/event contract khớp `api-{boundary}.md` / `{boundary}-events.md`.
  - Consumer-driven (Pact hoặc tương đương): consumer định nghĩa expectation → provider verification chạy ở CI provider.
  - Provider state setup cho từng interaction; verify path/method/field/enum/error code/response shape + event payload schema.
  - **Backward-compat (additive-only)**: thêm field optional / enum value OK; remove/rename/đổi type/bắt buộc field mới = **breaking → FAIL** (bắt sớm trước khi vỡ consumer).
- **regression**: `TC-R*` chốt lại bug đã fix (link `BUG-NNN`) — chống tái phát.
- **isolation**: unit/integration biên domain (mock infra) cho logic phức tạp / invariant.
- **perf** (khi NFR latency): k6, threshold = SLO từ `PROJECT.md` NFR (p95/p99 + error rate). Phân loại: **smoke** (vài VU, sanity) · **load** (tải kỳ vọng) · **stress** (tìm điểm gãy) · **soak** (chạy dài → phát hiện memory leak).
  ```javascript
  import http from 'k6/http'; import { check } from 'k6';
  export const options = { vus: 10, duration: '1m',
    thresholds: { http_req_duration: ['p(99)<500'] } };   // theo NFR PROJECT.md
  export default function () {
    const r = http.get(`${__ENV.BASE_URL}/v1/health`);
    check(r, { 'ok': (res) => res.status === 200 });
  }
  ```
- **security** (khi NFR security): theo `review-backend §B2` (OWASP) — injection (SQL/JPQL/native), SSRF, mass-assignment, deserialization; authz bypass + tenant leakage; secret trong response/log; **dependency scan (CVE nghiêm trọng)**; FE: XSS/CSRF/token storage; rate-limit/brute-force.
- **resilience/chaos** (khi NFR availability): inject downstream fail/timeout → verify timeout + circuit-breaker mở + fallback đúng; partial failure (DB commit nhưng event/cache fail) → reconcile/outbox bù.
- **migration** (khi đổi schema): chạy migration forward trên DB có data + verify **rollout an toàn** (thêm column NULLABLE → backfill → enforce NOT NULL ở migration sau); KHÔNG mất data, KHÔNG khoá bảng lâu.

## Done
- TC chuyên sâu vào registry, có AC trace + priority đúng (P0 blocker / P1 must / P2 nice). Contract/perf/security/resilience/migration chỉ thêm khi contract phức tạp / NFR yêu cầu / có đổi schema.
