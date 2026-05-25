# Framework Test — Concrete Example

> **Purpose:** Walkthrough đầy đủ với **bài toán nghiệp vụ cụ thể** — verify framework end-to-end.
> **Test project:** CRM cho doanh nghiệp phân phối nhựa HDPE (B2B).
> **Phương pháp:** Input là **bài toán nghiệp vụ**, KHÔNG có quyết định kỹ thuật/wave/feature trước — để intake agent tự phân tích và đề xuất.

---

## Setup

```bash
py scripts/reset_for_new_project.py --confirm \
    --project-id crm-hdpe \
    --display-name "CRM nhựa HDPE"

py scripts/harness.py state
```

**Kết quả mong muốn:**
- `project.id: crm-hdpe`
- `stage: BOOTSTRAP`
- `wave.id: null`
- `workflow.allowed_next: ["intake-requirement"]`
- `agents/` chỉ 16 core agents, chưa có boundary agents
- `harness/SERVICE-BOUNDARY-MATRIX.json`: `{"version":1,"boundaries":[]}`

---

## Step 1 — `/intake-requirement` step 1: Requirement Analyst

### Input (bài toán nghiệp vụ — KHÔNG decision kỹ thuật)

```bash
py scripts/build_command_prompt.py intake-requirement --step 1 --input "
Doanh nghiệp HDP Plastic chuyên phân phối nhựa HDPE (ống, phụ kiện, tấm) cho công trình xây dựng và nhà máy. Đang quản lý bằng Excel + Zalo, gặp các vấn đề:

- Sales pipeline B2B dài (1-3 tháng), khó theo dõi từng lead/cơ hội
- Báo giá tốn thời gian: mỗi đơn 10-30 SKU, công thức giá theo lượng + nhóm khách (VIP/Thường), discount tier
- Khách hàng phân tán Excel, hay quên follow up
- Giám đốc không có dashboard doanh thu / sales rep / khách
- Công nợ B2B phức tạp (khách trả chậm 30-60 ngày), kế toán đối soát thủ công

Cần CRM web-based, dùng cho:
- Sales rep (10-15 người): quản lý lead, khách, báo giá, đơn hàng, follow up
- Sales manager (2-3): duyệt báo giá vượt limit, xem pipeline team, KPI sales
- Kế toán (3 người): theo dõi công nợ, đối soát thanh toán
- Giám đốc (1): dashboard tổng, doanh thu, top khách, top SP

Yêu cầu:
- Ưu tiên Việt hóa hoàn toàn
- Budget timeline ~3 tháng (team 4-6 dev)
- Phase đầu chưa cần mobile app
- Tích hợp tương lai: kế toán Misa (qua API)
"
```

**Spawn:** `requirement-analyst-agent.md` (role `intake:requirement-analyst`)

### Kết quả mong muốn (shape — agent tự quyết detail)

#### 📄 `docs/architecture/PROJECT.md` (sample content — agent tự generate)

```markdown
# PROJECT — CRM nhựa HDPE (HDP Plastic)

## Tổng quan
- One-liner: CRM B2B cho doanh nghiệp phân phối nhựa HDPE — quản lý lead/khách/báo giá/đơn hàng/công nợ
- Vấn đề: Sales chu kỳ dài, báo giá phức tạp, không có visibility cho sếp + kế toán

## Đối tượng
- Persona: Sales rep, Sales manager, Kế toán, Giám đốc
- Bên liên quan: Khách hàng B2B (công trình, nhà máy)

## Phạm vi (cấp dự án)
| In scope | Out of scope |
|----------|--------------|
| Lead, Customer, Quote, Order, AR (công nợ), Dashboard | Mobile app, e-commerce B2C, AI suggest |

## KPI
- Giảm 50% thời gian lập báo giá
- 80% lead có follow-up đúng SLA (3 ngày)
- 100% công nợ visible realtime cho kế toán
- Dashboard giám đốc < 5 giây load

## NFR
| Performance | p95 < 500ms (báo cáo), < 200ms (CRUD) |
| Availability | 99% (giờ làm việc) |
| Security | RBAC theo role, audit log đầy đủ |
| Coverage | BE ≥ 80%, FE ≥ 60% |
| i18n | Việt hóa 100%, formatter VND |

## Ràng buộc
- Timeline: ~3 tháng
- Team: 4-6 dev
- Integration tương lai: Misa accounting (qua API)

## Open questions
- [ ] Quote approval workflow chi tiết (cấp duyệt theo giá trị nào)?
- [ ] Discount tier công thức cụ thể?
- [ ] SLA follow-up: cảnh báo qua app hay email?
```

#### 📄 FEAT files (agent đề xuất, ví dụ — số lượng tự quyết)

Có thể có 6-10 FEAT, ví dụ:
- `FEAT-001-lead-management.md` — Quản lý lead (nguồn, scoring, convert)
- `FEAT-002-customer-management.md` — Khách hàng (info, history, segment VIP/Thường)
- `FEAT-003-product-catalog.md` — Catalog HDPE (SKU theo size/grade/color)
- `FEAT-004-quotation.md` — Báo giá (multi-line, công thức giá, version)
- `FEAT-005-order-management.md` — Đơn hàng (từ quote, theo dõi giao)
- `FEAT-006-accounts-receivable.md` — Công nợ (aging report, đối soát)
- `FEAT-007-activity-followup.md` — Activity log + follow-up reminder
- `FEAT-008-dashboard-reporting.md` — Dashboard cho từng role
- `FEAT-009-rbac-auth.md` — Auth + role permissions
- (có thể thêm: notification, audit log...)

Mỗi FEAT có frontmatter `Priority: Must | Should | Could` + draft AC.

### Verify (shape, không số chính xác)

```bash
ls docs/architecture/PROJECT.md
ls docs/architecture/feat/FEAT-*.md | wc -l   # Expect ≥ 5
grep -l "Must" docs/architecture/feat/FEAT-*.md | wc -l   # Có FEAT Must
```

---

## Step 2 — `/intake-requirement` step 2: Business Analyst

```bash
py scripts/build_command_prompt.py intake-requirement --step 2
```

**Spawn:** `business-analyst-agent.md` (role `intake:business-analyst`)

### Kết quả mong muốn — FEAT files refined với AC testable + BR

#### 📄 `FEAT-004-quotation.md` (sau refine — sample)

```markdown
## Acceptance criteria
- [ ] AC-1: **Given** sales rep đã login, **when** POST /v1/quotes với customer_id + ≥1 line items, **then** 201 + quote.id, status=DRAFT, version=1
- [ ] AC-2: **Given** quote có line item, **when** GET /v1/quotes/{id}, **then** trả về subtotal + discount + VAT + total đúng công thức
- [ ] AC-3: **Given** quote DRAFT, **when** submit, **then** chuyển status=PENDING_APPROVAL nếu total > limit của sales rep, hoặc APPROVED nếu ≤ limit
- [ ] AC-4: **Given** quote APPROVED, **when** convert to order, **then** tạo order với cùng line items, quote status=CONVERTED
- [ ] AC-5: **Given** quote PENDING_APPROVAL, **when** manager duyệt, **then** status=APPROVED + log approver_id + timestamp
- [ ] AC-6: **Given** quote CONVERTED, **when** thử edit, **then** 409 CONFLICT

## Business rules
| ID | Rule |
|----|------|
| BR-1 | Mỗi line item: quantity > 0, unit_price tự tính theo công thức (base_price × discount_tier × volume_discount) |
| BR-2 | Customer VIP → áp dụng tier giá VIP (config trong customer record) |
| BR-3 | Sales rep limit: 50M VND. Trên → cần manager approve |
| BR-4 | Quote version tăng khi customer requests điều chỉnh (giữ history) |
| BR-5 | Quote CONVERTED không sửa được — phải tạo quote mới (revision) |
```

#### 📄 `FEAT-006-accounts-receivable.md` (refine)

```markdown
## Acceptance criteria
- [ ] AC-1: Khi order shipped → tự động tạo AR entry với due_date = ship_date + customer.payment_terms (vd 30 ngày)
- [ ] AC-2: Aging report group theo bucket: Current, 1-30 days, 31-60 days, > 60 days overdue
- [ ] AC-3: Kế toán record payment → match với AR entries (FIFO), update balance
- [ ] AC-4: Khách quá hạn 60 ngày → cảnh báo, không cho quote mới (override bởi manager)

## Business rules
| BR-1 | Payment terms theo customer record (Net 30 / Net 45 / Net 60) |
| BR-2 | Partial payment cho phép, balance carry over |
| BR-3 | Overdue > 60 days → block quote new (override role: manager+) |
```

### Output handoff trong RETURN

```json
{
  "completed": ["business-rules", "ac-complete"],
  "features_refined": ["FEAT-001", "FEAT-002", ..., "FEAT-009"],
  "boundaries_suggested": [
    "lead", "customer", "product", "quote", "order", "accounting", "reporting", "auth", "fe-crm"
  ],
  "unresolved_questions": [
    "Discount tier cụ thể: cần xác nhận với business owner",
    "Email notification provider: SendGrid hay tự SMTP server?"
  ]
}
```

### Verify

```bash
grep -lE "AC-[0-9]" docs/architecture/feat/FEAT-*.md | wc -l   # Mọi FEAT có AC
grep -lE "BR-[0-9]" docs/architecture/feat/FEAT-*.md | wc -l   # Mọi FEAT có BR
```

---

## Step 3 — `/intake-requirement` step 3: Solution Architect

```bash
py scripts/build_command_prompt.py intake-requirement --step 3
```

**Spawn:** `solution-architect-agent.md`

### Kết quả mong muốn — architect đề xuất stack + boundaries

#### 📁 ADR (architect chốt — ví dụ)

```
docs/architecture/adr/
├── ADR-001-tech-stack.md           # Backend: NestJS/TypeScript + PostgreSQL; FE: React+Vite+MUI
├── ADR-002-backend-architecture.md # Layered per ref-back-end-pattern (api/domain/infra)
├── ADR-003-auth-security.md        # JWT + RBAC; roles: SALES_REP, SALES_MGR, ACCOUNTING, ADMIN
├── ADR-004-ui-kit.md               # Material UI v5, design tokens Việt hóa
├── ADR-005-money-handling.md       # VND, decimal precision, formatter "1.234.567 ₫"
├── ADR-006-state-machine.md        # Quote state machine OWN trong data-model-quote
└── ADR-007-integration-misa.md     # API contract Misa, retry/circuit breaker
```

#### 📁 Boundaries đề xuất (architect chốt từ BA suggestion)

Có thể consolidate hoặc giữ — ví dụ:
```
- lead          (BE) — lead lifecycle, scoring
- customer      (BE) — customer + segment + payment_terms
- product       (BE) — HDPE catalog, pricing rules
- quote         (BE) — quotation + approval workflow + state machine
- order         (BE) — order from quote, fulfillment status
- accounting    (BE) — AR, payments, aging
- reporting     (BE) — dashboards, aggregations
- auth          (BE) — JWT + RBAC
- fe-crm        (FE) — SPA cho mọi role
```

→ **9 boundaries** (architect tự quyết — có thể consolidate `lead+customer` thành 1, hoặc `quote+order` thành 1).

#### 📁 HLD per boundary (9 file)

Mỗi HLD có:
- System context (C4 L1): vị trí boundary trong CRM
- Internal components (theo `ref-back-end-pattern`)
- Sequence flows cho mỗi FEAT Must
- Resilience cho outbound (vd: `accounting` gọi `misa-integration` có timeout + retry)
- NFR refinements (vd: `reporting` cần p95 < 5s, không phải 200ms như CRUD)

#### 📁 API contracts (9 file)

Ví dụ `api-quote.md` có endpoints:
- POST /v1/quotes
- GET /v1/quotes?status=&customer_id=&page=
- GET /v1/quotes/{id}
- PUT /v1/quotes/{id}
- POST /v1/quotes/{id}/submit
- POST /v1/quotes/{id}/approve (role: SALES_MGR)
- POST /v1/quotes/{id}/convert (→ order)

#### 📁 Data models (9 file)

Ví dụ `data-model-quote.md` định nghĩa:
- Entity: `quote`, `quote_line_item`, `quote_version`
- State machine: `DRAFT → PENDING_APPROVAL → APPROVED → CONVERTED | REJECTED`
- Indexes: `(customer_id, status)`, `(created_by, created_at)`

#### 📁 UX wireframes

`docs/architecture/ux/ux-fe-crm.md` có:
- SCR-001 Dashboard (theo role: sales rep / manager / accounting / director)
- SCR-002 Lead list + form
- SCR-003 Customer detail (tabs: info, quotes, orders, AR)
- SCR-004 Quote builder (multi-line, công thức giá realtime)
- SCR-005 Order tracking
- SCR-006 AR aging report
- SCR-007 Approval inbox (sales manager)

#### 📄 `docs/architecture/integrations-matrix.md`

```markdown
## Sync calls
| from | to | kind | contract | trigger |
|------|----|----|----------|---------|
| fe-crm | auth | http | api-auth.md | Login |
| fe-crm | quote | http | api-quote.md | Quote builder |
| fe-crm | reporting | http | api-reporting.md | Dashboard |
| quote | customer | http | api-customer.md | Get customer + tier |
| quote | product | http | api-product.md | Get prices |
| order | accounting | http | api-accounting.md | Create AR on ship |
| reporting | * | http (batch) | * | Daily aggregation |

## Async (future)
| accounting | misa-integration | event | events/ar-sync.json | AR posted |
```

### Verify

```bash
ls docs/architecture/adr/ADR-*.md | wc -l        # ≥ 3 (expect 5-7)
ls docs/architecture/hld/hld-*.md                # 1 per backend boundary
ls docs/architecture/api/api-*.md                # tương ứng
ls docs/architecture/data-model/data-model-*.md
ls docs/architecture/ux/ux-*.md                  # ≥ 1 cho FE
cat docs/architecture/integrations-matrix.md | grep -c "^|"   # có rows thật
```

---

## Step 4 — `/intake-requirement` step 4: Program Planner

```bash
py scripts/build_command_prompt.py intake-requirement --step 4
```

**Spawn:** `program-planner-agent.md`

### Kết quả mong muốn — planner quyết wave count + assignment

#### 📄 `docs/plans/project/waves-roadmap.md` (planner tự chia)

Vd planner quyết **3 wave** (KHÔNG fix sẵn — agent quyết theo dependency):

```markdown
| Wave | Title | Duration | Goal | Boundaries |
|------|-------|----------|------|------------|
| wave-001 | Foundation (auth + master data) | 4 weeks | Login, RBAC, customer, product catalog | auth, customer, product, fe-crm (partial) |
| wave-002 | Sales (quote + order) | 5 weeks | Lead, quote workflow, order tracking | lead, quote, order, fe-crm (extend) |
| wave-003 | Reporting (AR + dashboard) | 3 weeks | Công nợ, aging, dashboards | accounting, reporting, fe-crm (extend) |

Total: 12 weeks (vs PROJECT estimate 12 weeks ✓)
```

#### 📄 `docs/plans/project/agent-roster.md`

```markdown
| boundary_id | layer | waves_participating | serves_boundaries | fe_surface |
|-------------|-------|--------------------|--------------------|------------|
| auth | backend | wave-001 | — | — |
| customer | backend | wave-001, wave-002, wave-003 | — | — |
| product | backend | wave-001, wave-002 | — | — |
| lead | backend | wave-002 | — | — |
| quote | backend | wave-002 | — | — |
| order | backend | wave-002, wave-003 | — | — |
| accounting | backend | wave-003 | — | — |
| reporting | backend | wave-003 | — | — |
| fe-crm | fe | wave-001, wave-002, wave-003 | (all BE) | web-app |
```

#### 📄 `docs/plans/waves/wave-001/wave.md` (§1)

```markdown
## §1. Plan (intake step 4)
- Wave: wave-001 (Foundation)
- Duration: 4 weeks
- FEAT: FEAT-002 (customer), FEAT-003 (product), FEAT-009 (auth)
- Boundaries: auth, customer, product, fe-crm
- Order: auth → customer + product (parallel) → fe-crm login + 2 list pages
```

`wave-002/wave.md`, `wave-003/wave.md` tương tự.

#### Materialized agents

9 boundaries × 3 roles (dev/fix/review) = **27 boundary agent files** mới:

```
agents/
├── auth-agent.md, fix-auth-agent.md, review-auth-agent.md
├── customer-agent.md, fix-customer-agent.md, review-customer-agent.md
├── product-agent.md, ...
├── lead-agent.md, ...
├── quote-agent.md, ...
├── order-agent.md, ...
├── accounting-agent.md, ...
├── reporting-agent.md, ...
└── fe-crm-agent.md, fix-fe-crm-agent.md, review-fe-crm-agent.md
```

Tất cả BE agent có:
- `role: dev:backend` (hoặc `fix:backend`/`review:backend`)
- Skills frontmatter: `implementation`, `tech-stack`, `backend-conventions`, `ref-back-end-pattern`, `ref-back-end-config`

FE agent `fe-crm-agent.md` có:
- `role: dev:frontend`
- Skills: `frontend-implementation`, `tech-stack`, `frontend-conventions`, `ref-front-end-pattern`, `ref-front-end-config`

#### KG per boundary

```
knowledge-base/
├── shared.knowledge-graph.yaml
├── auth.knowledge-graph.yaml
├── customer.knowledge-graph.yaml
├── product.knowledge-graph.yaml
├── lead.knowledge-graph.yaml
├── quote.knowledge-graph.yaml
├── order.knowledge-graph.yaml
├── accounting.knowledge-graph.yaml
├── reporting.knowledge-graph.yaml
└── fe-crm.knowledge-graph.yaml
```

#### Matrix synced

`harness/SERVICE-BOUNDARY-MATRIX.json` có 9 boundaries với owned_paths + integrations từ matrix.

### Complete

```bash
py scripts/harness.py intake-requirement complete '{}'
```

### Verify

```bash
py scripts/harness.py state
# stage: IMPLEMENTATION_PLAN, allowed_next: [review-document]

ls agents/*-agent.md | wc -l   # 16 core + 27 boundary = 43
cat harness/SERVICE-BOUNDARY-MATRIX.json | python -c "import json,sys; print(len(json.load(sys.stdin)['boundaries']))"
# 9
```

---

## Step 5 — `/review-document`

```bash
py scripts/build_command_prompt.py review-document
py scripts/harness.py review-document complete '{"approved": true}'
```

**Kết quả:** `stage: IMPLEMENTATION_PLAN`, `allowed_next: [start-wave, apply-cr]`.

---

## Step 6 — `/start-wave wave-001`

```bash
py scripts/build_command_prompt.py start-wave --wave wave-001
py scripts/harness.py start-wave complete '{"wave_id":"wave-001","wave_title":"Foundation"}'
```

### STATE sau complete

```json
{
  "stage": "IMPLEMENTATION_PLAN",
  "wave": {"id": "wave-001", "number": 1, "title": "Foundation"},
  "features_in_flight": ["FEAT-002", "FEAT-003", "FEAT-009"],
  "boundaries_in_flight": ["auth", "customer", "product", "fe-crm"],
  "handoff.file": "handoff/wave-001.md",
  "workflow.allowed_next": ["start-dev", "register-boundary", "apply-cr"]
}
```

`boundaries_in_flight` chỉ load 4 boundaries có `wave-001` trong `waves_participating` — KHÔNG bao gồm `lead`, `quote`, `order`, `accounting`, `reporting` (wave 2/3).

---

## Step 7-9 — Dev cycle wave-001 (auth → customer → product → fe-crm partial)

> Lặp `/start-dev` → `/review-dev` cho từng boundary. Code vào `services/{boundary}/`.

### Đặc thù BE agent (vd `quote-agent.md` — chỉ liên quan wave-002, nhưng minh họa scope)

DOCS IN SCOPE auto-resolve (role `dev:backend`):
```
- docs/architecture/PROJECT.md
- docs/plans/waves/wave-001/wave.md
- docs/architecture/hld/hld-customer.md     ← chỉ boundary mình
- docs/architecture/api/api-customer.md
- docs/architecture/data-model/data-model-customer.md
- docs/architecture/integrations-matrix.md
- knowledge-base/customer.knowledge-graph.yaml
```

KHÔNG có: `ux-fe-crm.md`, `hld-quote.md`, `data-model-product.md` (ngoài scope).

### Đặc thù FE agent (`fe-crm-agent.md` — wave-001 implement login + 2 màn list)

DOCS IN SCOPE auto-resolve (role `dev:frontend`):
```
- docs/architecture/PROJECT.md
- docs/plans/waves/wave-001/wave.md
- docs/architecture/ux/ux-fe-crm.md         ← UX wireframes
- docs/architecture/api/api-*.md             ← cross-boundary contracts (BE mà FE gọi)
- docs/architecture/integrations-matrix.md
- knowledge-base/fe-crm.knowledge-graph.yaml
```

KHÔNG có: HLD/data-model BE internals.

### Coverage threshold (Rule BE-/FE-* check trong review)

- BE: ≥ 80%
- FE: ≥ 60%

---

## Step 10-12 — Dev handoff → test plan → test execute

```bash
py scripts/build_command_prompt.py dev-handoff
# Agent: pytest --cov × N boundaries, docker-compose up --build, curl health × N services
py scripts/harness.py dev-handoff complete '{
  "coverage_pct": 84,
  "coverage_fe_pct": 65,
  "handoff_ready": true
}'

py scripts/build_command_prompt.py test-plan
# Agent tạo tracking/waves/wave-001/test-cases.md
py scripts/harness.py test-plan complete

py scripts/build_command_prompt.py test-execute
# Agent chạy auto tests
py scripts/harness.py test-execute complete '{"test_result": "pass"}'
```

`test-cases.md` wave-001 ví dụ có:
- TC-S01..03 Smoke (auth/customer/product/fe-crm health)
- TC-I01..15 Integration (login, register customer, product CRUD, RBAC test)
- TC-E01..03 E2E (Cypress: login → customer list → create customer)
- TC-M01 Manual: Việt hóa form messages
- TC-M02 Manual: VND formatter "1.234.567 ₫"

---

## Step 13 — `/release`

```bash
py scripts/harness.py release complete '{"release_ok": true}'
```

`tracking/waves/wave-001/release-notes.md` có nội dung wave-001:
- FEAT shipped: customer master, product catalog, auth + RBAC
- Coverage: 84% BE, 65% FE
- Breaking: none (release đầu)
- Next: wave-002 sales workflow

`stage: DONE`.

---

## Step 14 — `/end-wave` (soft close — wait UAT)

```bash
py scripts/harness.py end-wave complete '{"end_wave_ok": true}'
```

**Kết quả:**
- `stage: MANUAL_TEST`
- Infra vẫn UP (CRM accessible `http://localhost:3000`)
- `tracking/waves/wave-001/manual-test-log.md` skeleton tạo

---

## Step 15 — Stakeholder UAT (ngoài harness)

Giám đốc + sales manager test thử. Tìm thấy 2 bug:

#### BUG-001 (manual, FE)
```yaml
---
id: BUG-001
wave: wave-001
origin: manual
severity: medium
boundary: fe-crm
detected_by: sales_manager
---
# BUG-001 — Format số tiền không có phân cách hàng nghìn
Hiện: "1234567 ₫" → kỳ vọng "1.234.567 ₫"
```

#### BUG-002 (manual, BE)
```yaml
---
id: BUG-002
wave: wave-001
origin: manual
severity: high
boundary: customer
detected_by: accountant
---
# BUG-002 — Payment terms không cập nhật được cho customer hiện có
PUT /v1/customers/{id} với payment_terms_days bị ignore (return 200 nhưng DB không đổi)
```

---

## Step 16 — Fix loop (2 bugs)

### BUG-001 (FE)

```bash
py scripts/build_command_prompt.py fix-bugs --boundary fe-crm
# Agent fix-fe-crm-agent: add VND formatter using Intl.NumberFormat
py scripts/harness.py fix-bugs complete '{"boundary_id":"fe-crm"}'
```

### BUG-002 (BE)

```bash
py scripts/build_command_prompt.py fix-bugs --boundary customer
# Agent fix-customer-agent: fix mapper bỏ sót field payment_terms_days
py scripts/harness.py fix-bugs complete '{"boundary_id":"customer"}'
```

### Retest (smart route)

```bash
py scripts/harness.py retest complete '{"test_result": "pass"}'
```

Smart routing: bug origin = `manual` → quay về **MANUAL_TEST** (không phải SPECIALIST_TESTING). Stakeholder verify lại 2 TC tương ứng → pass → ký sign-off.

---

## Step 17 — `/done-wave` (hard close)

```bash
py scripts/harness.py done-wave complete '{"done_wave_ok": true}'
```

**Kết quả:**
- `stage: BOOTSTRAP`
- `wave.id: null`
- Infra DOWN
- KG `shared.yaml` thêm:
  ```yaml
  implementation.completed:
    - wave-wave-001-shipped
    - wave-wave-001-done
  discipline.do_not_repeat:
    - "wave-001 (FE): VND format luôn dùng Intl.NumberFormat('vi-VN') — không string concat (BUG-001)"
    - "wave-001 (BE customer): Check mapper coverage cho mọi field DTO ↔ entity (BUG-002)"
  decisions:
    - id: DEC-WAVE-001
      decision: "Wave 1 shipped: auth + RBAC + customer + product catalog"
  ```

---

## Step 18 — Wave 2 (Sales workflow)

```bash
py scripts/build_command_prompt.py start-wave --wave wave-002
py scripts/harness.py start-wave complete '{"wave_id":"wave-002","wave_title":"Sales"}'
```

### Kết quả mong muốn

- `wave.id: wave-002`
- `features_in_flight`: FEAT-001 (lead), FEAT-004 (quote), FEAT-005 (order), FEAT-007 (activity)
- `boundaries_in_flight`: `lead, quote, order, customer (extend), product (extend), fe-crm (extend)` — load từ roster

**Cross-wave KG verify:** Khi `/start-dev --boundary quote`, agent đọc `knowledge-base/shared.yaml` và thấy do_not_repeat từ wave-1 → tránh lặp lỗi VND format, mapper coverage.

Lặp dev cycle (step 7-17) cho wave-002.

---

## Step 19 — Wave 3 (Reporting + AR)

Tương tự wave-002, boundaries: `accounting`, `reporting`, `fe-crm` (extend dashboard).

---

## Final outcome — Project shipped

Sau wave-003 done-wave:

### State cuối
```bash
py scripts/harness.py state
```
- `stage: BOOTSTRAP`
- `wave.id: null`
- `project.id: crm-hdpe`

### Artifacts đầy đủ

```
docs/architecture/
  PROJECT.md
  feat/FEAT-001..009.md (9 file)
  adr/ADR-001..007.md (7 file)
  hld/hld-{auth,customer,product,lead,quote,order,accounting,reporting,fe-crm}.md
  api/api-*.md (9 file)
  data-model/data-model-*.md (9 file BE)
  ux/ux-fe-crm.md
  integrations-matrix.md
  infra/docker-compose.yml + local-dev.md

docs/plans/
  project/waves-roadmap.md, agent-roster.md
  waves/wave-001/wave.md, wave-002/wave.md, wave-003/wave.md

agents/
  16 core + 27 boundary (9 × 3) = 43 files

knowledge-base/
  shared.yaml + 9 boundary KG

services/
  auth/, customer/, product/, lead/, quote/, order/, accounting/, reporting/, fe-crm/

tracking/
  change-requests/ (rỗng nếu không CR)
  waves/wave-001/, wave-002/, wave-003/
    mỗi wave: test-cases, test-results, manual-test-log, release-notes, bugs/

handoff/
  wave-001.md, wave-002.md, wave-003.md (đều sign-off Wave Done)
```

### Business outcome (theo KPI PROJECT)

- ✓ Sales rep nhập lead/quote → giảm 50% thời gian báo giá
- ✓ Sales manager duyệt qua workflow
- ✓ Kế toán theo dõi AR realtime
- ✓ Giám đốc có dashboard
- ✓ Việt hóa 100%, VND formatter đúng

---

## ✅ Acceptance — Framework PASS khi

- [ ] Reset script → BOOTSTRAP clean
- [ ] Intake 4 step tự quyết: ≥ 5 FEAT, ≥ 3 ADR, ≥ 5 boundaries, ≥ 2 wave (planner tự chia)
- [ ] Step 4 materialize đủ {N_boundary × 3} agent files + KG + matrix tương ứng
- [ ] `start-wave` chỉ load boundaries có wave hiện tại trong roster
- [ ] BE agent prompt KHÔNG có UX/HLD-other-boundary; FE agent prompt KHÔNG có HLD/data-model BE internals
- [ ] Smart retest route đúng theo bug origin (auto → SPECIALIST_TESTING, manual → MANUAL_TEST)
- [ ] `end-wave` (soft) giữ infra + stage MANUAL_TEST
- [ ] `done-wave` (hard) teardown + stage BOOTSTRAP
- [ ] Mỗi wave có per-wave folder `tracking/waves/{wave-id}/` với 5 artifact types
- [ ] KG shared persist learnings cross-wave (wave-2 agent đọc được do_not_repeat từ wave-1)
- [ ] Hooks chặn bypass (sai stage, sai command, thiếu evidence, thiếu kg_appended, KG blocker)

---

## Lưu ý quan trọng

**Input nghiệp vụ, KHÔNG quyết định kỹ thuật:** User không nên nhét sẵn "2 wave: MVP + Reporting" vào input — để intake agents tự phân tích. Output (số wave, boundary, FEAT) **agent tự quyết**, test chỉ verify SHAPE (≥ thresholds) chứ không exact count.

**Variation acceptable:** Cùng input có thể cho output khác nhau giữa các run (vd: planner chia 2 vs 3 wave). Framework PASS khi:
- Process state transitions đúng
- Per-layer scope đúng
- Smart routing đúng
- Hooks enforce đúng

Không PASS khi:
- Mất artifact (vd: thiếu ADR / KG / matrix)
- Boundary leak (BE đọc UX, FE đọc data-model BE internals)
- State jump (skip stage)
- KG không persist cross-wave
