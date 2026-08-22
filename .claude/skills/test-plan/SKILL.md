---
name: test-plan
description: Sinh test-case-registry.md cho wave — TC per AC + enterprise coverage matrix (error paths, tenant isolation, idempotency, rate limit, concurrency). Test pyramid.
---

# Test Plan Skill

## Khi load
`test-plan-agent` ở `/run-wave` (state TEST_PLAN). Input: `FEAT-*.md` (AC) + `BR-*.md` (rule enforce) + `api-{boundary}.md` + `PROJECT.md` (NFR) + `JOURNEY-*.md` (e2e) + `ux-{boundary}.md` (a11y).

> **Vai trò: THIẾT KẾ test case** (viết spec vào registry) — KHÔNG viết code test, KHÔNG chạy. Code test do **dev** viết khi code (mỗi AC có test, `rules §N`); `/run-wave` chạy + bổ sung test còn thiếu so với registry.

## Scope = wave plan (gate `registry_scope` — chống over-scope: test một feature chưa build)
Auto-TC **chỉ được trace FEAT thuộc wave plan ≤ wave hiện tại** (`docs/plans/wave-*.md` — registry tích luỹ nên FEAT wave trước vẫn hợp lệ để regression). FEAT chỉ xuất hiện ở wave TƯƠNG LAI / chưa plan → **KHÔNG sinh TC** (test-execute sẽ chạy vào feature chưa build → fail → bug rác chặn end-wave). FEAT/AC nằm trong `## Deferred to later waves` → TC **bắt buộc tag `@deferred`** (thiếu tag = gate chặn).

## Deferred-scope (để end-wave close sạch tự nhiên)
Đọc `## Deferred to later waves` trong `docs/plans/wave-{N}.md` + `tracking/wave-{N}/review-findings.md` (status wontfix/accepted có lý do defer). Mọi AC/feature **đã chủ động hoãn sang wave sau** (vd auth/idempotency/event ở wave-1 chỉ-CRUD):
- TC tương ứng VẪN viết (để wave sau reuse) nhưng đánh **tag `@deferred`** + `note: deferred wave-N` + KHÔNG đặt `pri P0`.
- Defer **chỉ có hiệu lực khi feature/AC đó được khai báo trong `## Deferred to later waves` của wave plan** — tag `@deferred` đơn lẻ (không khai báo) sẽ bị test-execute coi in-scope và vẫn phải chạy (chống lạm dụng tag để né test).
- Hệ quả: test-execute `skip(deferred)` không tính fail; `test_result` (harness derive) chỉ tính in-scope → đạt `pass` tự nhiên khi in-scope xanh, KHÔNG cần ép `test_result=pass` thủ công.

## UI coverage bắt buộc (gate `ui_test_present` — web boundary phải được MỞ thật)
Mỗi **web boundary trong wave** phải có **≥1 auto-TC UI in-scope** (`type=auto`, `boundary=<web-boundary>`, group `e2e`; thêm `accessibility` nếu wave full-stack FE). Nội dung tối thiểu của TC UI:
- Playwright mở màn hình chính (route theo `ux-{boundary}.md §screens`), assert luồng chính render + action chạy.
- **Assert style thật** (chống unstyled): computed style của element chính phải khớp design token (background/font/spacing từ `design-tokens.css`), KHÔNG phải browser default.
- **Screenshot** mỗi TC (pass hay fail) → `tracking/wave-{N}/screenshots/{TC}.png` (test-execute chụp; gate `test_evidence` đòi file thật).
UI TC để `type=manual` hết / tag `@deferred` để né → gate chặn (registry toàn API-TC vẫn pass là loophole đã đóng).

## Output: `tracking/wave-{N}/test-case-registry.md` (format BẢNG — mỗi TC = 1 HÀNG)
**Template ở `tracking/_templates/TEMPLATE.test-case-registry.md`** (đường dẫn ĐÚNG — đọc + copy cấu trúc, KHÔNG tự chế format / KHÔNG tìm chỗ khác). Cột: `TC | group | type | boundary | feature | AC | BR | pri | pre-condition | test-data | steps | expected | tags | note` + bảng **Coverage matrix** (AC → TC). (Template test-report + bugs cũng ở `tracking/_templates/`.)
- `group` = test_type bản chất (functional/integration/e2e/performance/security/accessibility + alias smoke/regression/uat) — enum + khi-nào-dùng ở `SEVERITY-TEST-TAXONOMY §4`.
- `type`: `auto` (test-execute chạy được bằng tool) | `manual` (UAT/QA tay) — TRỤC KHÁC với `group`.
- `AC`: `FEAT-N:AC-M` (mọi TC trace ≥1 AC, trừ smoke infra). `BR`: `BR-N` nếu TC enforce 1 business rule (optional).
- `pri`: P0|P1|P2 — quy tắc gán ở `SEVERITY-TEST-TAXONOMY §3`. `tags`: ≥1 `@FEAT-<id>` + ≥1 suite tag (`SEVERITY-TEST-TAXONOMY §5`).
- `test-data`/Steps/Expected giữ ngắn 1 cell; chi tiết dài (selector, payload, SQL fixture) → UAT script riêng / `test-execute` automation.

## Traceability TC↔AC (rigor bắt buộc — hai chiều, gate `ac_coverage` enforce bằng máy)
- Mỗi TC trace ≥1 `FEAT-N:AC-M` (+ `BR-N` nếu enforce rule). KHÔNG TC mồ côi (không trace AC nào — trừ `TC-S*` smoke infra).
- Mọi AC của FEAT in-scope → ≥1 TC (không AC mồ côi). Bảng **Coverage matrix** chứng minh: AC → TC list + count.
- Đọc FEAT § "Tiêu chí chấp nhận" (heading `### AC-n`, BDD Cho/Khi/Thì) → mỗi AC ánh xạ ≥1 TC. Parse đếm AC, so với count TC linked → assert phủ 100%.
- **Gate `ac_coverage` parse `### AC-n` trong FEAT-*.md vs cột feature+AC registry:** AC in-scope (trừ token deferred) không có TC = chặn; TC trace AC không tồn tại trong FEAT (sau `/domain` đổi AC) = stale = chặn — coverage matrix không còn là lời hứa.

## Cumulative registry + DEDUPE (registry sống qua wave)
- Registry là **pool tích luỹ** — TC từ wave trước GIỮ NGUYÊN, wave mới chỉ thêm/reuse.
- **Trước khi thêm TC mới**: check trùng trong registry — cùng `feature` + cùng `group` + steps tương tự ≥ ~70% → **REUSE** (đánh dấu `note: reuse W{prev}`, KHÔNG copy nội dung). Khác hẳn → **CREATE**. Mid (mơ hồ) → judgement, ghi lý do `note`.
- TC-ID không tái dùng cho nội dung khác (immutable). Regression `TC-R*` link `ref_bug` (bug đã fix) — chống tái phát.

## Remap khi AC đổi (qa-translator concept — single-repo, KHÔNG cần command mới)
Khi `/domain` refine AC của FEAT đã có TC:
- AC **xoá hẳn** / **mâu thuẫn lớn** (behavior đảo) → đánh dấu TC `note: STALE (FEAT-N AC đổi W{cr})` + re-author TC mới thay thế (giữ row cũ làm history, không xoá).
- AC **refine nhỏ** (reword / thêm precondition / thêm negative) → update steps/expected của TC tại chỗ, ghi `note: remap W{cr}`.
- AC **không đổi** → no-op. Coverage matrix re-verify sau remap.

## Test pyramid (phân bổ)
- **unit/isolation** (nhiều): domain/service thuần, mock infra. (Dev viết — không vào registry trừ invariant phức tạp.)
- **functional** (nhiều): 1 hành vi/feature theo 1 AC, scope hẹp.
- **integration** (vừa): api + DB thật (Testcontainers) / cross-boundary qua contract.
- **e2e** (ít): journey end-to-end. **2 dạng:** (a) **UI→DB** không stub — CHỈ wave full-stack BE+FE; (b) **journey đa-hop API-driven** (curl/RestAssured drive A→B→C liền, KHÔNG cần FE) — cho chuỗi `depends_on` ≥3 boundary, **kể cả wave backend-only**. Gate `journey_e2e_present` đòi ≥1 TC span cả chuỗi (boundary/tags tham chiếu đủ mọi boundary) — bug seam khi cả chuỗi chạy liền lọt pairwise (L10).
- **performance** (chỉ khi NFR latency) · **security** (chạm auth/payment/PII) · **accessibility** (CHỈ wave full-stack FE).

> test_type ưu tiên theo wave strategy (backend-heavy / frontend-heavy / full-stack): xem `SEVERITY-TEST-TAXONOMY §4.2`.

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
- **Dữ liệu test** (cột `test-data` + `pre-condition`): deterministic (seed cố định, inject Clock) · độc lập per TC · tự cleanup · KHÔNG dùng data prod. **Ghi ĐỦ CỤ THỂ để test-execute SEED được** (entity nào + field gì, tạo qua API nào) — không để mơ hồ; reference/sample data dùng chung ghi rõ "seed ở infra/init".

## Quy ước
1. Mỗi AC có ≥ 1 TC happy + TC cho error path/tenant/idempotency áp dụng được.
2. Smoke test cross-boundary cho mọi integration điểm (login + create + read). **Gate `contract_test_present`:** mỗi consumer boundary (có `depends_on` trong wave) PHẢI có ≥1 auto-TC group=contract|integration|e2e nối tới nó (boundary cell hoặc tags chứa consumer-id) — chống "thiếu liên kết BE-FE" lọt test (BUG-010/011/012).
   - **Gate `journey_e2e_present` (đa-hop):** khi có chuỗi `depends_on` **≥3 boundary** (A→B→C) trong wave → PHẢI có ≥1 auto-TC `group=e2e|integration` **span cả chuỗi** (boundary/tags tham chiếu ĐỦ A, B, C). Pairwise (contract_test_present) không phủ bug khi cả chuỗi chạy liền. **API-driven (curl) là đủ — KHÔNG cần FE**, nên backend-only wave vẫn validate được luồng đa-service sớm (không hoãn tới wave FE).
3. P0 = blocker release · P1 = must-have · P2 = nice-to-have (`SEVERITY-TEST-TAXONOMY §3`).
4. Contract TC: response/enum/error code khớp `api-{boundary}.md` (deep → `specialist-testing`).
5. **Traceability 2 chiều**: mọi AC `Must` → ≥1 TC (không AC mồ côi); mọi TC → đúng 1 AC (không TC thừa không trace).
6. **Forbidden trong narrative TC** (steps/expected cell vẫn được dùng selector/payload cho automation): không gắn tên class/SQL/DOM selector vào cột `expected` — TC mô tả behavior, sống lâu hơn implementation.

## Done
- Mọi AC `Must` trace ≥1 TC (2 chiều); coverage matrix phủ 100%; endpoint nhạy cảm có error paths + tenant isolation + idempotency + concurrency; event boundary có TC idempotent/DLQ; dedupe-check trước khi thêm TC (reuse vs create ghi `note`); priority + tags gán đúng theo `SEVERITY-TEST-TAXONOMY`.
