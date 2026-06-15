---
type: plan
artifact_kind: wave-sequence
status: ACTIVE
version: 1.0
tier: T2
owner: program-planner
last_reviewed: "{{DATE}}"
---

> Điền NGẮN GỌN: ưu tiên bảng/bullet, không văn xuôi thừa, không lặp. Doc này agent downstream đọc nhiều lần — tiết kiệm context.

# Wave Sequence — {{PROJECT_NAME}}

> Source-of-truth (cho người) về thứ tự + scope mỗi wave. Author bởi `program-planner-agent` ở stage **PLAN** (`/plan`); refine qua `/apply-cr` (từ DONE).
>
> Mỗi wave 2 dimension độc lập (clone ADLC, adapt single-repo):
> - `wave_class`: `slice` (nhỏ ≈ 1 boundary-day, test cấp 1) | `integration` (lát E2E full + demo)
> - `wave_strategy`: `vertical` (pair BE+FE) | `horizontal-be` (kind=backend/bff) | `horizontal-fe` (kind=web/mobile)
>
> **Machine SOT = `harness/SERVICE-BOUNDARY-MATRIX.json`**: `start-wave` đọc MATRIX (wave-number → `boundary_id` + `kind` + `features[]`) derive `STATE.wave_boundaries`/`wave_features`; KHÔNG đọc file `.md` này. `targets.*` ở đây **mirror** MATRIX cùng wave-number; lệch → MATRIX thắng. **`wave_class`/`wave_strategy`/`targets`/`target_count` ĐƯỢC GATE** ở `/plan` qua `wave_sequence_lint` (G16): enum + `target_count_per_layer ≤ 3` + strategy layer-purity + vertical `parent_epic` + `inherited_active` file tồn tại. Điền §2 block YAML đúng schema dưới (validator parse trực tiếp).

---

## 0. Strategy reference

### Class × Strategy matrix

| `wave_class` | `wave_strategy` | Typical scope | Test depth | Exit signal | Khi dùng |
|---|---|---|---|---|---|
| `slice` | `horizontal-be` | ≤ 3 boundary backend/bff, BE FEAT | unit + contract | `bd_increment_milestone`: unit green + producer contract ổn định | BE foundation, infra increment |
| `slice` | `horizontal-fe` | ≤ 3 boundary web/mobile, FE FEAT | component + visual | `ui_increment_milestone`: component/visual green, consume contract wave trước | UI rollout, design-system, a11y |
| `integration` | `vertical` | ≤ 2 BE + ≤ 2 FE, pair | unit+integration+component+e2e | `demo_target`: demo E2E user-visible + e2e green | Ship pillar feature, lát tích hợp |
| `slice` | `vertical` | hợp lệ schema | shallow | (hiếm — warn) | Spike / prototype |
| `integration` | `horizontal-be`/`-fe` | hợp lệ schema | full | (hiếm — warn) | BE-only/FE-only milestone test sâu |

**Hard constraints**:
- `target_count_per_layer ≤ 3` mọi wave: `targets.boundaries` ≤ 3 VÀ `web_experiences`+`mobile_experiences` ≤ 3.
- `horizontal-*` KHÔNG mix BE+FE — đúng 1 layer. `horizontal-be` → web/mobile rỗng; `horizontal-fe` → boundaries rỗng.
- `horizontal-fe` phải cite `contracts.inherited_active` từ wave trước (FE consume API/event đã produce).
- Wave 1 mỏng + chạy **E2E sớm** (auth/shared + 1 lát nghiệp vụ core).

> **`target_count` rationale (context budget)**: mỗi DEV/review agent load thin-context per boundary; giữ wave nhỏ để tổng context dưới ceiling ~80KB (BE ≤3×~20KB; FE ≤3×~15KB; vertical 2BE+2FE ≈70KB). `target_count` là kỷ luật người plan tự giữ.

---

## 1. Wave inventory

> Toàn bộ wave dự kiến (full plan, nhiều sprint phụ thuộc nhau). Status: PLANNED | ACTIVE | DELIVERED.

| # | Wave | Class | Strategy | Demo / Milestone | Status | Notes |
|---|---|---|---|---|---|---|
| 1 | wave-001 | {{integration}} | {{vertical}} | {{1-line demo}} | PLANNED | Foundation — lát E2E đầu |
| 2 | wave-002 | {{slice}} | {{horizontal-be}} | {{1-line milestone}} | PLANNED | — |
<!-- Thêm wave entries — phủ 100% boundary + FEAT, KHÔNG gom hết vào 1 wave -->

---

## 2. Per-wave entries

> Mỗi wave 1 block YAML dưới; chi tiết đầy đủ → `wave-{NNN}.md` (theo `TEMPLATE.wave.md`).
>
> **`targets` STRUCTURED** (mirror MATRIX, encode BE/FE layer): `boundaries` = kind=backend/bff · `web_experiences` = kind=web · `mobile_experiences` = kind=mobile.
> `features_in_scope[].target` = `<layer>/<boundary_id>` (`boundaries/...` | `web-experiences/...` | `mobile-experiences/...`) — encode layer cho `wave_strategy` validation. `paired_with` chỉ điền cho `vertical` wave.

### §wave-001

```yaml
wave_class: integration
wave_strategy: vertical
rationale: |
  Lát đầu ship E2E — validate luồng nghiệp vụ chính sớm.
  Vertical pair: BE auth (backend) + FE customer-app (web): login + 1 luồng core.

targets:                                  # mirror boundary_id trong MATRIX (cùng wave)
  boundaries: ["auth"]                    # kind=backend/bff
  web_experiences: ["customer-app"]       # kind=web
  mobile_experiences: []                  # kind=mobile

features_in_scope:
  - feat_id: FEAT-001
    target: boundaries/auth               # encode layer (BE)
    parent_epic: EP-001
    paired_with: FEAT-101                 # chỉ vertical wave
  - feat_id: FEAT-101
    target: web-experiences/customer-app  # encode layer (FE)
    parent_epic: EP-001
    paired_with: FEAT-001

contracts:                                # tham chiếu docs/architecture/ (KHÔNG hash/sign)
  produce:
    - docs/architecture/api/api-auth.md
  consume: []
  inherited_active: []

exit_signal:
  type: demo_target
  description: "User đăng nhập + chạy 1 luồng core end-to-end trên customer-app."

test_scope:
  required: [unit, component]
  conditional: [integration, e2e]

constraints:
  target_count_per_layer: 1               # max(len(boundaries), len(web)+len(mobile))
  context_budget_estimate_kb: 35
```

### §wave-002

```yaml
wave_class: slice
wave_strategy: horizontal-be
rationale: |
  BE foundation — chỉ boundary backend, slice nhanh, test unit + contract; experiences rỗng (no FE mix).

targets:
  boundaries: ["catalog", "inventory"]
  web_experiences: []
  mobile_experiences: []

features_in_scope:
  - feat_id: FEAT-201
    target: boundaries/catalog
    parent_epic: EP-002
  - feat_id: FEAT-211
    target: boundaries/inventory
    parent_epic: EP-002

contracts:
  produce:
    - docs/architecture/events/catalog-events.md
  consume: []
  inherited_active: []

exit_signal:
  type: bd_increment_milestone
  description: "Unit suite green cho 2 boundary; producer contract (api/event) ổn định."

test_scope:
  required: [unit]
  conditional: [contract]

constraints:
  target_count_per_layer: 2
  context_budget_estimate_kb: 40
```

### §wave-003

```yaml
wave_class: slice
wave_strategy: horizontal-fe
rationale: |
  FE render dashboard 2 experience — consume API auth (wave-001) + event catalog (wave-002) đã ship.
  Horizontal-fe: boundaries rỗng; phải cite inherited_active.

targets:
  boundaries: []
  web_experiences: ["ops-portal", "merchant-portal"]
  mobile_experiences: []

features_in_scope:
  - feat_id: FEAT-301
    target: web-experiences/ops-portal
    parent_epic: EP-003
  - feat_id: FEAT-311
    target: web-experiences/merchant-portal
    parent_epic: EP-003

contracts:
  produce: []
  consume:
    - docs/architecture/ux/ux-ops-portal.md
  inherited_active:
    - docs/architecture/api/api-auth.md
    - docs/architecture/events/catalog-events.md

exit_signal:
  type: ui_increment_milestone
  description: "Component + visual green; FE consume contract inherited từ wave-001 + wave-002."

test_scope:
  required: [component, visual]
  conditional: [a11y]

constraints:
  target_count_per_layer: 2
  context_budget_estimate_kb: 30
```

<!-- Thêm §wave-004, ... tới khi phủ hết boundary + FEAT trong MATRIX -->

---

## 3. Dependencies

> `inherited_active` = contract (api/event/ux trong `docs/architecture/`) đã ship từ wave produce. Thứ tự topological — không phụ thuộc ngược/vòng.

| Wave | Depends on | Reason |
|---|---|---|
| wave-001 | — | Foundation |
| wave-002 | — | Song song wave-001 (no cross-dep) |
| wave-003 | wave-001 (auth API), wave-002 (catalog event) | FE consume contract ship trước |

### Dependency graph (boundary-level)

```
wave-001: auth ──────────────┐
                             ├──> wave-003: ops-portal, merchant-portal (consume auth + catalog)
wave-002: catalog, inventory ┘
```

> Mũi tên = "consume contract / cần ready trước".

---

## 4. Change log

| Date | Wave | Change | By |
|---|---|---|---|
| {{DATE}} | — | Initial WAVE-SEQUENCE (full plan toàn dự án) | program-planner |

---

## 5. References

- `harness/SERVICE-BOUNDARY-MATRIX.json` — **machine SOT** (boundary_id + kind + wave + features; nguồn `start-wave` derive)
- `docs/plans/wave-{NNN}.md` — detail per-wave (theo `TEMPLATE.wave.md`) · `docs/architecture/{api,events,ux}/` — contract produce/consume
- `docs/architecture/PROJECT.md` — scope + stack (Discovery D3) · `scripts/gates.py` `plan_gate` · `.claude/skills/implementation-plan/SKILL.md`
