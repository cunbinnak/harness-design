---
name: specialist-testing
description: Test chuyên sâu — contract (consumer-driven/Pact + backward-compat), regression, isolation, perf (k6 smoke/load/stress/soak), security (OWASP), resilience/chaos, migration. Bổ sung vào registry khi vượt CRUD cơ bản.
---

# Specialist Testing Skill

## Khi load
Bổ trợ `test-plan-agent` / `test-execute-agent` khi wave cần loại test khó vượt mức CRUD.

## Hoạt động
Bổ sung TC chuyên sâu = **thêm row** vào bảng `tracking/wave-{N}/test-case-registry.md` (cùng cột template), mỗi TC trace ≥1 `FEAT-N:AC-M` (+ `BR-N` nếu enforce rule). **Dedupe trước**: registry tích luỹ qua wave — check trùng (cùng feature + group) → reuse thay vì tạo mới.

> `group` (test_type) enum + khi-nào-dùng + scope: SSOT ở `docs/architecture/SEVERITY-TEST-TAXONOMY §4`. Skill này KHÔNG định nghĩa enum đối nghịch — chỉ chi tiết rigor PER LOẠI.

## test_type taxonomy — khi nào dùng + scope (ref SSOT §4)
| group | Khi nào (wave strategy) | Scope | Nguồn input single-repo |
|---|---|---|---|
| `functional` | mọi wave (1 AC/1 luồng) | hẹp: 1 feature | `feat/FEAT-*.md` AC |
| `integration` | backend-heavy / full-stack | qua ranh giới boundary / BE↔FE contract | FEAT + `hld/`+`api/`+`events/` + `adr/` |
| `e2e` | CHỈ full-stack (BE+FE chạy thật) | dài: nhiều màn hình UI→DB | `journeys/JOURNEY-*.md` + `ux/` + FEAT |
| `performance` | backend-heavy / FEAT high-load | metric cụ thể (p95<Xms, RPS≥Y) | `hld/` perf targets + ADR scaling + `PROJECT.md` NFR |
| `security` | mọi wave chạm auth/payment/PII | negative testing là chính | `adr/` security + `BR-*.md` phân quyền + FEAT |
| `accessibility` | CHỈ full-stack FE (WCAG 2.1 AA) | FE-only, ref WCAG criterion ID | `ux/` + `journeys/` |

## Rigor per loại
- **contract**: verify API/event contract khớp `api-{boundary}.md` / `{boundary}-events.md`.
  - Consumer-driven (Pact hoặc tương đương): consumer định nghĩa expectation → provider verification chạy ở CI provider.
  - Provider state setup cho từng interaction; verify path/method/field/enum/error code/response shape + event payload schema.
  - **Backward-compat (additive-only)**: thêm field optional / enum value OK; remove/rename/đổi type/bắt buộc field mới = **breaking → FAIL** (bắt sớm trước khi vỡ consumer).
- **regression**: `TC-R*` chốt lại lỗi đã sửa (link `ref_tc=TC-NNN`) — chống tái phát. Tag `@regression`.
- **isolation**: unit/integration biên domain (mock infra) cho logic phức tạp / invariant.
- **performance** (khi NFR latency): k6, threshold = SLO từ `PROJECT.md` NFR (p95/p99 + error rate). Phân loại: **smoke** (vài VU, sanity) · **load** (tải kỳ vọng) · **stress** (tìm điểm gãy) · **soak** (chạy dài → phát hiện memory leak).
  ```javascript
  import http from 'k6/http'; import { check } from 'k6';
  export const options = { vus: 10, duration: '1m',
    thresholds: { http_req_duration: ['p(99)<500'] } };   // theo NFR PROJECT.md
  export default function () {
    const r = http.get(`${__ENV.BASE_URL}/v1/health`);
    check(r, { 'ok': (res) => res.status === 200 });
  }
  ```
- **security** (khi NFR security): theo `review-backend §B2` (OWASP) — injection (SQL/JPQL/native), SSRF, mass-assignment, deserialization; authz bypass + tenant leakage; secret trong response/log; **dependency scan (CVE nghiêm trọng)**; FE: XSS/CSRF/token storage; rate-limit/brute-force. Negative test: User A KHÔNG xem được resource User B → 403.
- **accessibility** (WCAG 2.1 AA, CHỈ full-stack FE): keyboard nav, screen reader, color contrast, focus management; tool axe/Lighthouse; ref WCAG criterion ID (vd 2.1.1, 4.1.2). FE-isolated dễ false positive → defer sang full-stack wave.
- **resilience/chaos** (khi NFR availability): inject downstream fail/timeout → verify timeout + circuit-breaker mở + fallback đúng; partial failure (DB commit nhưng event/cache fail) → reconcile/outbox bù.
- **migration** (khi đổi schema): chạy migration forward trên DB có data + verify **rollout an toàn** (thêm column NULLABLE → backfill → enforce NOT NULL ở migration sau); KHÔNG mất data, KHÔNG khoá bảng lâu.

## Done
- TC chuyên sâu vào registry, có AC trace + priority + tags đúng (`SEVERITY-TEST-TAXONOMY §3+§5`). Contract/perf/security/resilience/migration chỉ thêm khi contract phức tạp / NFR yêu cầu / có đổi schema. Dedupe-check trước khi tạo (reuse > create).
