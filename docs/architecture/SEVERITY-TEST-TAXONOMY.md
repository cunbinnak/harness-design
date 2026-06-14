# Severity & Test Taxonomy — SSOT

> Single source of truth cho 3 thang phân loại của harness + enum test_type + tag taxonomy.
> Clone + adapt single-repo từ ADLC ZIP (`ADLC-TESTING/_shared/definitions/{SEVERITY-LADDER,TEST-TYPES,TAG-TAXONOMY}.md`).
>
> Harness có 3 artifact phân loại RIÊNG BIỆT (mỗi cái 1 vòng đời + 1 gate). File này không hợp nhất chúng thành 1 enum (làm thế sẽ vỡ parser trong `scripts/gates.py`) mà ĐỊNH NGHĨA mapping nhất quán giữa chúng để 2 gate `no_open_findings` (review-dev) và `no_open_bugs` (end-wave) tự nhiên đồng pha.
>
> KHÔNG icon/emoji. KHÔNG lint_frontmatter (đó là cơ chế multi-repo ZIP). Harness dùng format row-based (mỗi item = 1 hàng bảng) — enum sống ở header note của template + parse bằng `scripts/gates.py`.

---

## 0. Ba thang trong harness (đừng nhầm)

| Artifact | File | Thang | Vòng đời | Gate đọc |
|---|---|---|---|---|
| Bug | `tracking/wave-{N}/bugs.md` | `sev: high \| medium \| low` | test-execute (auto) / UAT (manual) sinh → fix qua /fix-bugs → close. Sống tới end-wave. | `no_open_bugs` đọc cột `status` (KHÔNG đọc `sev`) |
| Review finding | `tracking/wave-{N}/review-findings.md` | `severity: BLOCKER \| MAJOR \| MINOR \| NIT \| QUESTION` | review-dev ghi → fix Mode B → resolved. Ephemeral pre-handoff (theo wave). | `no_open_findings` đọc cột `severity` + `status` |
| Test case | `tracking/wave-{N}/test-case-registry.md` | `pri: P0 \| P1 \| P2` | test-plan sinh → test-execute chạy. | (không gate trực tiếp; điều phối thứ tự fix) |

Điểm mấu chốt về gate (đọc kỹ trước khi đổi enum bất kỳ):

- `check_no_open_bugs` (gates.py) parse bảng `bugs.md`, lọc row có `id` khớp `bug-\d+` và `status ∉ {closed, fixed, wontfix}`. Nó KHÔNG nhìn `sev`. Vì vậy mọi bug `sev` (high/med/low) còn `open`/`in_progress` đều chặn end-wave như nhau — severity ở đây chỉ để phân loại + ưu tiên fix, KHÔNG đổi hành vi gate.
- `check_no_open_findings` parse bảng `review-findings.md`, CHỈ chặn row có `severity ∈ {blocker, major}` và `status ∉ {resolved, accepted, wontfix, closed, fixed}`. `MINOR/NIT/QUESTION` KHÔNG chặn.
- `check_test_passed` (end-wave) đọc `STATE.test_result == pass` — độc lập 3 thang trên.

Hệ quả thiết kế: 2 ngưỡng chặn ship khác nhau (review-dev chặn ở BLOCKER/MAJOR; end-wave chặn ở mọi bug open). Bảng map §2 căn 2 ngưỡng này về cùng 1 trục "hậu quả" để phán đoán nhất quán.

---

## 1. Severity ladder (4 mức hậu quả — trục chuẩn)

Clone từ ZIP SEVERITY-LADDER (P1-P4). Đây là TRỤC GỐC để map sang 3 thang harness. Phân loại theo HẬU QUẢ, không theo cảm tính.

### S1 — Critical / Ship blocker
Tiêu chí: mất/hỏng dữ liệu; lỗ hổng bảo mật (auth bypass, data leak, escalation, cross-tenant leak); sập service (crash/hang/OOM ở normal load); sai số tiền / dữ liệu tài chính; block toàn bộ flow nghiệp vụ chính, không workaround.
Ví dụ: "Transfer 100k, balance chỉ trừ 10k"; "User A login thấy data User B"; "POST /orders luôn 5xx".

### S2 — Major / Pre-ship fix
Tiêu chí: major regression của feature production; workaround tồn tại nhưng bất tiện; visible UX defect ảnh hưởng phần lớn user; performance degrade > 50% so baseline.
Ví dụ: "Form submit 8s thay vì 1s"; "Email không gửi nhưng UI báo đã gửi".

### S3 — Minor / Next-wave backlog
Tiêu chí: edge case ít gặp; cosmetic UI; workaround dễ; inconsistency nhỏ wording/format.
Ví dụ: "Tooltip sai font ở Safari < 14"; "Pagination button disabled khi không cần".

### S4 — Trivial / Tech debt
Tiêu chí: không ảnh hưởng user; code smell / naming / refactor; improvement suggestion (chưa phải bug thật).
Ví dụ: "Log spam mỗi request ở test env"; "Error message tiếng Anh thay vì tiếng Việt (cosmetic)".

---

## 2. BẢNG MAP 3 thang (SSOT)

Đọc theo dòng: 1 mức hậu quả (S1-S4) ánh xạ sang giá trị enum của từng artifact harness. Cột "Chặn ship?" cho biết gate nào sẽ chặn.

| Hậu quả | bug `sev` (bugs.md) | review `severity` (review-findings.md) | TC `pri` (test-case-registry.md) | Chặn ship? |
|---|---|---|---|---|
| S1 Critical / ship-blocker | `high` | `BLOCKER` | `P0` | review-dev: CHẶN (BLOCKER open). end-wave: CHẶN (bug open). |
| S2 Major / pre-ship | `high` hoặc `medium` (xem note) | `MAJOR` | `P0` hoặc `P1` | review-dev: CHẶN (MAJOR open). end-wave: CHẶN (bug open). |
| S3 Minor / backlog | `low` | `MINOR` | `P1` hoặc `P2` | review-dev: KHÔNG chặn (set accepted/wontfix). end-wave: CHẶN nếu còn open bug (phải close/wontfix). |
| S4 Trivial / debt | `low` | `NIT` | `P2` | review-dev: KHÔNG chặn. end-wave: đóng bằng `status=wontfix` hoặc convert sang ADR/refactor. |
| (không phải defect — cần làm rõ) | — | `QUESTION` | — | review-dev: KHÔNG chặn; reviewer/dev trả lời rồi đóng. |

Note mapping bug `sev` (vì harness chỉ có 3 mức high/med/low cho 4 mức hậu quả):

- S1 luôn `high`.
- S2 mặc định `high` nếu thuộc luồng cốt lõi / critical-path; `medium` nếu có workaround chấp nhận được.
- S3 luôn `low`.
- S4 luôn `low` (hoặc không log thành bug mà chuyển thành finding `NIT` / refactor task).

Quy tắc nhất quán 2 gate (vì sao map như trên):

1. Mọi thứ "phải fix trước ship" (S1, S2) ở review = `BLOCKER`/`MAJOR` (chặn review-dev) VÀ ở bug = `high`/`medium` (chặn end-wave vì còn open). Hai gate đồng pha: không có trạng thái "review cho qua nhưng end-wave chặn" cho cùng 1 hậu quả nghiêm trọng, và ngược lại.
2. Mọi thứ "có thể ship" (S3, S4) ở review = `MINOR`/`NIT`/`QUESTION` (KHÔNG chặn review-dev). Nhưng nếu nó đã thành BUG (test-execute/UAT phát hiện), end-wave VẪN chặn tới khi row đó `status ∈ {closed, fixed, wontfix}` — tức S3/S4 backlog phải đóng tường minh bằng `wontfix` + lý do, không để lửng `open`. Đây là chủ ý: bug đã ghi nhận thì phải có quyết định, finding pre-handoff thì có thể bỏ qua.
3. `wontfix` là cách hợp lệ để "đẩy S3/S4 sang wave sau" mà vẫn cho end-wave pass — ghi lý do ở cột `fix`/`root cause`.

### 2.1 Severity → bug sev lookup khi TC fail (cho test-execute)

Khi 1 TC `pri` FAIL, hậu quả thực tế quyết định bug `sev` (không suy ra máy móc từ `pri`):

| TC pri | Hậu quả thực tế khi fail | bug `sev` | Map S |
|---|---|---|---|
| P0 | data loss / auth bypass / sập | `high` | S1 |
| P0 | workaround tồn tại nhưng UX kém | `high`/`medium` | S2 |
| P0 | edge case không reproduce 100% | `low` | S3 |
| P1 | visible UX defect | `medium` | S2 |
| P1 | cosmetic | `low` | S3 |
| P2 | rare scenario | `low` | S3/S4 |
| Any | PASS nhưng suboptimal | không phải bug, là improvement | S4 (finding NIT, không log bug) |

test-execute dùng bảng làm starting point; nếu lệch → ghi lý do ở cột `root cause`/`note`.

---

## 3. TC priority (P0/P1/P2) — quy tắc gán

Harness dùng 3 mức (ZIP dùng P1/P2/P3; map: ZIP-P1 = harness-P0, ZIP-P2 = harness-P1, ZIP-P3 = harness-P2).

| pri | Khi nào | Run trong wave |
|---|---|---|
| `P0` | TC bảo vệ luồng cốt lõi, AC bắt buộc của FEAT cornerstone, ship-blocker scenario, smoke infra, auth, tenant-isolation, endpoint xử lý tiền. | Mọi wave có FEAT liên quan. |
| `P1` | TC bảo vệ AC quan trọng nhưng không cốt lõi; edge case khả năng cao; a11y luồng chính. | Wave có FEAT liên quan + smoke regression. |
| `P2` | TC rare edge case, polish, boundary value hiếm. | Khi có thời gian / wave dedicated. |

Quy tắc gán nhanh:
- TC link FEAT cornerstone hoặc BR cornerstone → `P0`.
- Security/performance TC trên endpoint xử lý tiền/PII → `P0`.
- Tenant isolation / authz cross-tenant → `P0`.
- Accessibility TC luồng cốt lõi → `P1`.
- Còn lại → `P2` default.

---

## 4. test_type enum (6 loại)

Clone từ ZIP TEST-TYPES. Harness ghi loại test ở cột `group` của `test-case-registry.md` (và cột `type` = `auto|manual` là TRỤC KHÁC: cơ chế chạy, đừng nhầm). `test_type` dưới đây là PHÂN LOẠI BẢN CHẤT test, ghi ở `group`.

> Lưu ý 2 trục độc lập trong registry:
> - `group` (= test_type): `functional | integration | e2e | performance | security | accessibility` (+ alias harness: `smoke`, `regression` — xem §4.1).
> - `type`: `auto` (test-execute chạy được bằng tool) | `manual` (UAT/QA tay).

| test_type | Mục đích | Scope | Nguồn input (single-repo) | Khi nào |
|---|---|---|---|---|
| `functional` | 1 hành vi đơn lẻ của 1 feature theo AC | hẹp: 1 feature, 1 luồng | `docs/architecture/feat/FEAT-*.md` (AC BDD) | mọi wave |
| `integration` | tương tác giữa 2+ boundary / BE-FE qua contract | gọi qua ranh giới module | FEAT + `docs/architecture/hld/hld-{boundary}.md` + `api/api-{boundary}.md` + `events/{boundary}-events.md` + liên quan `adr/ADR-*.md` | wave backend; wave full-stack |
| `e2e` | user journey end-to-end UI tới DB, không stub | dài nhất, nhiều màn hình | `docs/architecture/journeys/JOURNEY-*.md` + `ux/ux-{boundary}.md` + FEAT | CHỈ wave có đủ stack BE + FE chạy thật |
| `performance` | non-functional: throughput, latency, concurrency, resource | có metric cụ thể (p95 < Xms, RPS >= Y) | `hld-{boundary}.md` (performance targets) + ADR scaling/cache/queue + `PROJECT.md` NFR | wave backend; FEAT high-load |
| `security` | authz/authn, input validation, OWASP top-10, data leakage | negative testing là chính | `adr/ADR-*.md` (security) + `business-rules/BR-*.md` (phân quyền) + FEAT | mọi wave chạm auth/payment/PII |
| `accessibility` | WCAG 2.1 AA: keyboard, screen reader, contrast, focus | FE-only, ref WCAG criterion ID | `ux/ux-{boundary}.md` + `journeys/JOURNEY-*.md` | CHỈ wave full-stack FE (FE-isolated dễ false positive) |

### 4.1 Quan hệ với `group` hiện hành của template

Template `test-case-registry.md` hiện liệt kê `group ∈ {smoke, integration, e2e, uat, regression}`. Hoà giải:

- `smoke` = subset của `functional`/`integration` chạy trước release (suite tag, không phải test_type riêng) → vẫn dùng làm `group` value, gắn thêm tag `@smoke`.
- `uat` = `functional`/`e2e` với `type=manual`, verifier=stakeholder → `group=e2e` (hoặc functional) + tag `@manual`.
- `regression` = TC bảo vệ behavior cũ (suite tag) → `group` giữ bản chất gốc (vd integration) + tag `@regression` + `ref_bug`.
- 6 test_type ZIP bổ sung `performance`, `security`, `accessibility` vào tập `group` hợp lệ (trước đây ẩn trong `integration`/`e2e`).

Tập `group` hợp lệ sau hoà giải: `smoke | functional | integration | e2e | performance | security | accessibility | regression | uat`. test-plan chọn test_type bản chất; suite (`smoke`/`regression`) + cơ chế (`uat`) biểu diễn bằng tag/`type`.

### 4.2 Ma trận test_type theo wave strategy (tham khảo PLAN)

| Strategy | functional | integration | e2e | performance | security | accessibility |
|---|---|---|---|---|---|---|
| backend-heavy | optional | required | — | required | required | — |
| frontend-heavy | required | optional | — | optional | optional | — |
| full-stack (vertical) | required | required | required | as needed | as needed | required |

"required" = test-plan expect >= 1 TC loại đó cho mỗi FEAT in-scope. (Harness MATRIX dùng field `kind` per boundary thay cho phân loại repo ZIP; strategy ở đây là gợi ý đọc theo mix kind của wave.)

---

## 5. Tag taxonomy (gọn)

Clone rút gọn từ ZIP TAG-TAXONOMY, bỏ phần index-file generation (`reindex_registry.py` là cơ chế multi-repo). Tag ghi ở cột `note` hoặc inline trong registry; dùng để filter regression / smoke / query cross-wave.

### 5.1 Suite tags (chọn test suite)
| Tag | Ý nghĩa |
|---|---|
| `@smoke` | TC quan trọng nhất, chạy trước mỗi release (subset). |
| `@regression` | bảo vệ behavior cũ, chạy mỗi wave phát hiện regression. |
| `@critical-path` | luồng nghiệp vụ cốt lõi (revenue, login, payment). |
| `@happy-path` | positive scenario (golden path). |
| `@edge-case` | boundary value, negative path, error scenario. |

### 5.2 Domain tags (link artifact docs/architecture)
| Pattern | Ví dụ | Ý nghĩa |
|---|---|---|
| `@FEAT-<id>` | `@FEAT-AUTH-001` | TC test 1 feature. Khuyến nghị >= 1 (mọi TC trace >= 1 AC). |
| `@BR-<id>` | `@BR-AUTH-005` | TC validate 1 business rule. |
| `@JOURNEY-<id>` | `@JOURNEY-CKO-001` | TC follow 1 journey (cho e2e). |
| `@PERSONA-<id>` | `@PERSONA-MRC-001` | TC từ góc nhìn 1 persona. |

### 5.3 Scope tags (link boundary — single-repo: KHÔNG có experience riêng)
| Pattern | Ví dụ | Ý nghĩa |
|---|---|---|
| `@boundary:<name>` | `@boundary:order`, `@boundary:web-checkout` | TC test boundary nào. FE là boundary `kind=web/mobile` — KHÔNG tách `@experience:` (đó là multi-repo ZIP). |
| `@platform:<name>` | `@platform:web`, `@platform:ios`, `@platform:android` | platform chạy (cho mobile/web). |

### 5.4 Technical tags (modifier)
| Tag | Ý nghĩa |
|---|---|
| `@manual` | chạy tay (a11y screen-reader, exploratory). |
| `@automated` | đã có script automation (Playwright/k6/...). |
| `@flaky` | lịch sử intermittent fail — cần retry/rewrite. |
| `@blocked` | block bởi dependency chưa sẵn sàng. |

### 5.5 Quy tắc tag
1. Khuyến nghị >= 1 tag `@FEAT-<id>` mỗi TC (trace DOMAIN).
2. Khuyến nghị >= 1 suite tag.
3. Tag prefix `@`, value lowercase kebab-case, không dấu cách, không tiếng Việt.
4. Adapt single-repo: bỏ `@experience:` (gộp vào `@boundary:`); bỏ rule "linter reject" (không có lint_frontmatter); tag mới ghi thêm vào §5.6.

### 5.6 Custom tags (project-specific)
| Tag | Ngày thêm | Ý nghĩa |
|---|---|---|
| (chưa có) | — | — |

---

## 6. Liên quan (nơi enum này được dùng)

| Nơi | Dùng gì từ file này |
|---|---|
| `.claude/skills/bug-logging/SKILL.md` + `tracking/_templates/TEMPLATE.bugs.md` | bug `sev: high\|medium\|low` → §1+§2 (map S1-S4) + §2.1 (TC fail → sev) |
| `.claude/skills/test-plan/SKILL.md` + `tracking/_templates/TEMPLATE.test-case-registry.md` | TC `pri: P0\|P1\|P2` → §3; test_type/`group` → §4; tag → §5 |
| `.claude/skills/review-{backend,bff,web,mobile}/SKILL.md` + `tracking/_templates/TEMPLATE.review-findings.md` | `severity: BLOCKER\|MAJOR\|MINOR\|NIT\|QUESTION` → §1+§2 |
| `scripts/gates.py` (`check_no_open_bugs`, `check_no_open_findings`, `check_test_passed`) | §0 giải thích gate đọc cột nào → đừng đổi enum value đang được parse |
| `tracking/README.md` | §0 (3 thang) + §2 (mapping) làm reference |

Không đổi enum value đang parse (gates.py). File này là tầng ngữ nghĩa thống nhất phía trên enum sẵn có.