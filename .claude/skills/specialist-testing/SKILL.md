---
name: specialist-testing
description: Test chuyên sâu — contract (consumer-driven/Pact), regression, isolation, perf (k6), security. Bổ sung vào registry khi vượt CRUD cơ bản.
---

# Specialist Testing Skill

## Khi load
Bổ trợ `test-plan-agent` / `test-execute-agent` khi wave cần loại test khó vượt mức CRUD.

## Hoạt động
Bổ sung TC chuyên sâu vào `tracking/wave-{N}/test-case-registry.md` (cùng format heading + frontmatter `type/boundary/feature/ac/priority`), mỗi TC trace ≥ 1 `FEAT-N:AC-M`:

- **contract**: verify API/event contract khớp `api-{boundary}.md` / `{boundary}-events.md`.
  - Consumer-driven (Pact hoặc tương đương): consumer định nghĩa expectation → provider verification chạy ở CI provider.
  - Verify: path/method/field/enum/error code/response shape + event payload schema. Bắt breaking change sớm.
- **regression**: `TC-R*` chốt lại bug đã fix (link `BUG-NNN`) — chống tái phát.
- **isolation**: unit/integration biên domain (mock infra) cho logic phức tạp / invariant.
- **perf** (khi NFR latency): k6 smoke + threshold p99.
  ```javascript
  import http from 'k6/http'; import { check } from 'k6';
  export const options = { vus: 10, duration: '1m',
    thresholds: { http_req_duration: ['p(99)<500'] } };   // theo NFR PROJECT.md
  export default function () {
    const r = http.get(`${__ENV.BASE_URL}/v1/health`);
    check(r, { 'ok': (res) => res.status === 200 });
  }
  ```
- **security** (khi NFR security): authz bypass, tenant leakage, injection, secret trong response/log — theo NFR.

## Done
- TC chuyên sâu vào registry, có AC trace + priority đúng (P0 blocker / P1 must / P2 nice). Contract/perf/security chỉ thêm khi contract phức tạp hoặc NFR yêu cầu.
