---
type: plan
artifact_kind: wave-detail
wave: wave-{{NNN}}
wave_class: {{slice|integration}}
wave_strategy: {{vertical|horizontal-be|horizontal-fe}}
status: PLANNED
last_reviewed: "{{DATE}}"
---

> Điền NGẮN GỌN: ưu tiên bảng/bullet, không văn xuôi thừa, không lặp. Doc này agent downstream đọc nhiều lần — tiết kiệm context.

# Wave {{N}} — {{wave-title}}

> Per-wave plan chi tiết (cho người). Sinh bởi `program-planner-agent` ở **PLAN** (`plan`); update khi wave sau (lùi `/domain` chốt chia-wave) đổi scope.
>
> **Machine SOT = `harness/SERVICE-BOUNDARY-MATRIX.json`**: `start-wave` đọc MATRIX (wave-number → boundary_id + kind + features), KHÔNG đọc file này. `targets` + boundary list dưới đây **mirror** MATRIX; lệch → MATRIX thắng. KHÔNG có MANIFEST/contract-sign/hash. Thin-context per boundary materialize qua `start-wave` + `build_prompt.py`.

---

## 0. Overview

| Field | Value |
|---|---|
| Wave ID · title | wave-{{NNN}} · {{short name}} |
| Goal | {{1-2 câu — lát sản phẩm gì giao được}} |
| Class · strategy | `{{slice|integration}}` · `{{vertical|horizontal-be|horizontal-fe}}` |
| Estimated duration | {{N ngày/tuần}} |
| Status | PLANNED / IN_PROGRESS / COMPLETED |
| Start · end target | {{date}} · {{date}} |

### Targets (structured — mirror MATRIX, encode layer)

```yaml
targets:
  boundaries: ["{{backend/bff boundary_id}}"]      # kind=backend/bff
  web_experiences: ["{{web boundary_id}}"]         # kind=web
  mobile_experiences: ["{{mobile boundary_id}}"]   # kind=mobile
constraints:
  target_count_per_layer: {{≤ 3}}                  # max(len(boundaries), len(web)+len(mobile))
```

> `horizontal-be` → web/mobile rỗng. `horizontal-fe` → boundaries rỗng. `vertical` → cả 2 layer, pair BE↔FE.

---

## 1. Strategy + rationale

**`{{wave_strategy}}`** — {{1-2 câu vì sao chọn strategy này. Vd vertical: pair BE auth + FE customer-app ship 1 lát E2E. Vd horizontal-be: dựng nền BE multi-boundary, FE consume sau}}.

- Class × strategy reference: `WAVE-SEQUENCE.md §0`.
- `horizontal-fe` phải kế thừa contract ACTIVE từ wave trước (§4 + `inherited_active`).

---

## 2. Boundaries in scope (thin-context per boundary)

> Mỗi boundary trong wave (subset MATRIX) = per-boundary thin-context (owned paths, contract produce/consume, ref skills, FEAT+AC, exit, demo signature). Agent DEV load đúng khối của mình.

### {{boundary-1}}

| Field | Value |
|---|---|
| Kind | backend / bff / web / mobile |
| Layer target | `boundaries/{{boundary-1}}` (hoặc `web-experiences/...` / `mobile-experiences/...`) |
| Prefix | {{prefix}} (vd fnb) |
| Tech | {{language + framework + data_store}} (từ MATRIX `tech`) |
| Owned paths | `services/{{prefix}}-{{boundary-1}}/` (MATRIX `owned_paths` — PreToolUse enforce) |
| Ref skills | {{ref-backend-redis, ref-backend-kafka, ...}} (situational, MATRIX `ref_skills`; rules-{kind} + ref-{kind}-pattern/config auto-load) |
| Depends on (trong wave) | {{boundary ready trước — vd auth trước ordering}} (MATRIX `depends_on`) |

**FEAT + AC trong scope:**

| FEAT | Title | AC count | AC file | Priority |
|---|---|---|---|---|
| `FEAT-{{NNN}}` | {{title}} | {{N}} | `docs/architecture/feat/FEAT-{{NNN}}-*.md` | Must / Should |

**Contracts (tham chiếu `docs/architecture/` — KHÔNG hash/sign):**

| Contract | Role | Path |
|---|---|---|
| api-{{boundary-1}} | produce | `docs/architecture/api/api-{{boundary-1}}.md` |
| {{x}}-events | produce / consume | `docs/architecture/events/{{boundary-1}}-events.md` |
| api-{{other}} | consume | `docs/architecture/api/api-{{other}}.md` |
| ux-{{boundary-1}} | consume (FE) | `docs/architecture/ux/ux-{{boundary-1}}.md` |

> Single-repo: consume cross-boundary qua contract doc + (runtime) HTTP/event — KHÔNG đọc HLD/business-rule boundary khác. `inherited_active` (FE horizontal-fe) = contract ACTIVE ship từ wave trước.

**Design source (FE boundary — bỏ qua nếu BE):**

| Priority | Source | Path |
|---|---|---|
| 1 | UX spec / wireframe | `docs/architecture/ux/ux-{{boundary-1}}.md` |
| 2 | Figma (read-only) | {{Figma URL nếu có}} |

**Exit criteria (boundary này, trong wave):**

- [ ] Mọi AC trong scope pass.
- [ ] Build + lint + test green (lệnh theo kind, `start-dev` materialize per stack).
- [ ] Coverage ≥ ngưỡng theo kind: **BE 80%** / **BFF 70%** / **web|mobile 60%** (gate `dev-handoff`).
- [ ] Contract produce ổn định (review-dev pass).
- [ ] KG boundary (`knowledge-base/{{boundary-1}}.knowledge-graph.yaml`) cập nhật entity/rule mới.

**Demo signature (integration wave — chứng cứ góp vào demo E2E):**

- {{Vd: "POST /auth/login trả token hợp lệ → customer-app render trang chủ với tên user."}}

### {{boundary-2}}

{{Lặp cấu trúc trên cho mỗi boundary. Horizontal wave nhiều boundary cùng layer; vertical pair BE + FE.}}

---

## 3. Features in scope (tổng hợp wave)

| FEAT | Target (layer/boundary) | Paired with | Priority | AC count | Parent epic | Notes |
|---|---|---|---|---|---|---|
| FEAT-{{NNN}} | boundaries/{{boundary-1}} | FEAT-{{MMM}} | Must | {{N}} | EP-{{XXX}} | {{ngữ cảnh}} |
| FEAT-{{MMM}} | web-experiences/{{boundary-2}} | FEAT-{{NNN}} | Must | {{N}} | EP-{{XXX}} | {{ngữ cảnh}} |

> `target` encode layer (đọc bởi `wave_strategy` validation). `paired_with` chỉ điền cho `vertical` wave.

---

## 4. Dependencies (cross-wave)

> `inherited_active` = contract đã ship + ACTIVE.

| From wave | Deliverable / contract | Path | Why needed |
|---|---|---|---|
| Wave 0 (infra) | docker-compose skeleton | `docs/architecture/infra/docker-compose.yml` | Build local stack cho test handoff |
| wave-{{N-1}} | {{contract / capability}} | `docs/architecture/{{api\|events\|ux}}/...` | {{reason}} |

---

## 5. Implementation order (within wave)

> Foundation trước, dependent sau.

1. **Phase 1**: {{boundary-foundation}} (vd auth / shared) — `start-dev {{boundary-foundation}}`.
2. **Phase 2**: {{boundary phụ thuộc foundation}}.
3. **Phase 3**: {{FE / BFF integration}} (consume API phase trước).
4. **Phase 4**: review-dev → dev-handoff → test-plan → test-execute → UAT.

---

## 6. Test scope

```yaml
test_scope:
  required: [{{unit, component, ...}}]       # theo class × strategy matrix
  conditional: [{{integration, e2e, contract, visual, a11y}}]
```

| Test type | Áp dụng cho | Ghi chú |
|---|---|---|
| unit | mọi boundary | mỗi AC ≥ 1 TC |
| component / visual | FE boundary | khớp design source §2 |
| integration | vertical wave | cross-boundary thật (infra local UP) |
| contract | producer boundary | api/event ổn định |
| e2e | integration wave | demo path xanh |

> Chi tiết TC sinh ở TEST_PLAN (`test-plan` → `tracking/wave-{{NNN}}/test-case-registry.md`). Enterprise coverage (error path, tenant isolation, idempotency, rate-limit, concurrency) thêm ở test-plan.

### Deferred to later waves (SoT cho test-plan đánh `@deferred`)

> Liệt kê AC/feature/BR **chủ động hoãn** sang wave sau (vd wave-1 chỉ CRUD: auth/idempotency/event để wave-2). test-plan đọc mục này → TC tương ứng tag `@deferred` → test-execute `skip(deferred)` (không bug, không chặn end-wave). **Chỉ token liệt kê ở ĐÂY mới được defer** (tag đơn lẻ vô tác dụng — chống né test). Token: `FEAT-{{NNN}}` · `FEAT-{{NNN}}:AC-{{M}}` · `BR-{{NNN}}`.

| Token | Lý do hoãn | Wave dự kiến |
|---|---|---|
| {{FEAT-{{NNN}}:AC-{{M}}}} | {{vd: auth out-of-scope wave CRUD}} | wave-{{N+1}} |

> Wave không hoãn gì → để bảng rỗng (mọi auto-TC = in-scope, phải chạy thật).

---

## 7. Risks + assumptions

| Risk / Assumption | Impact | Mitigation / Verification |
|---|---|---|
| {{risk 1}} | high / medium / low | {{action}} |
| {{assumption 1}} | — | {{cách verify}} |

---

## 8. Exit criteria (wave done)

> Gate thực thi ở back-half (review-dev coverage, dev-handoff, end-wave). Checklist này là chuẩn người plan kỳ vọng.

- [ ] Mọi FEAT `Must` implemented + test pass.
- [ ] Coverage theo kind: BE ≥ 80% / BFF ≥ 70% / web|mobile ≥ 60% (gate `dev-handoff`).
- [ ] `review-dev` pass cho **mọi** boundary (open_findings == 0).
- [ ] docker-compose có entry mọi boundary; infra local UP (gate `dev-handoff` → `test-plan`).
- [ ] `tracking/wave-{{NNN}}/test-case-registry.md` có ≥ 1 TC per AC.
- [ ] Auto test xanh (`test-execute` → `test_result=pass`), không bug auto open.
- [ ] Exit signal đạt: {{demo_target / bd_increment_milestone / ui_increment_milestone}} (§2 demo signature).
- [ ] UAT signed off (gate `end-wave`: `uat_signed`). Không còn TC đỏ (`test_passed`). KG mọi boundary cập nhật.

---

## 9. Rollback plan

1. Revert docker-compose về wave {{N-1}}.
2. Rollback DB migration: compensating migration (hoặc `flyway undo` nếu support).
3. Đánh dấu wave `IN_PROGRESS` lại; ghi nguyên nhân vào `tracking/wave-{{NNN}}/`.

---

## 10. Related artifacts

- `WAVE-SEQUENCE.md` — roadmap toàn dự án (§0 strategy matrix, dependency graph)
- `harness/SERVICE-BOUNDARY-MATRIX.json` — machine SOT (boundary_id + kind + wave + features + owned_paths + ref_skills)
- `knowledge-base/{{boundary}}.knowledge-graph.yaml` — KG per boundary
- `tracking/wave-{{NNN}}/` — test-case-registry + test-report + bugs + qc-signoff
- `docs/architecture/{api,events,ux,hld}/` — contract + design per boundary

---

## 11. Change log

| Date | Change | By |
|---|---|---|
| {{DATE}} | Initial wave-{{NNN}} detail | program-planner |
