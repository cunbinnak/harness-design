---
type: principles
artifact_kind: architecture-principles
status: ACTIVE
last_reviewed: "2026-06-14"
---

# Architecture Principles

> Nguyên tắc bất biến của ADLC Design Harness (single-repo). Mọi HLD (`hld/hld-{boundary}.md`), ADR (`adr/ADR-*.md`), contract (`api/`, `events/`, `ux/`), và code service (`services/{prefix}-{boundary}/`) phải nhất quán với file này.
>
> Đọc cùng `CLAUDE.md` (NON-NEGOTIABLES + ROUTING) + `harness/PROTOCOL.md`. Clone + adapt single-repo từ ADLC ZIP `ARCHITECTURE-PRINCIPLES.md`.

---

## 0. Quan hệ với CLAUDE.md / PROTOCOL.md

- `CLAUDE.md` + `harness/PROTOCOL.md` định nghĩa **policy + process** (stages, gates, commands, agents, failure modes).
- File này định nghĩa **invariants về thiết kế** — cách hệ thống tổ chức, contract, ranh giới, layering.

Conflict → NON-NEGOTIABLES của `CLAUDE.md` thắng (process precedence). Mọi quyết định thiết kế phải trace về một nguyên tắc dưới đây; không có nguyên tắc nào áp dụng → tạo ADR mới bổ sung/override (P4 decision-traceability).

---

## 1. Sáu nguyên tắc kiến trúc

### P1. Boundary + kind (một mô hình boundary, KHÔNG có fullstack boundary)

Repo này là **single-repo design + polyrepo code**: mỗi đơn vị giao hàng là một `boundary` có field `kind`. KHÔNG tách `boundaries/` vs `web-experiences/` vs `mobile-experiences/` (như ZIP multi-repo) — tất cả là `boundary` trong `harness/SERVICE-BOUNDARY-MATRIX.json`, phân biệt bởi `kind`.

| kind | Trách nhiệm | Source-of-truth | Code |
|---|---|---|---|
| `backend` | Quản lý dữ liệu + thực thi business rule | Domain model + DB schema (`data-model/`) | `services/{prefix}-{boundary}/` |
| `bff` | Aggregate/compose cho 1 FE app | API schema (`api/` + `api/bff-aggregation-*`) | `services/{prefix}-{boundary}/` |
| `web` / `mobile` | Hiển thị dữ liệu + thu thập intent người dùng | UI contract + user-flow (`ux/`) | `services/{prefix}-{boundary}/` |

**Hệ quả**:
- KHÔNG "fullstack boundary" — backend và frontend KHÔNG sống chung 1 boundary; mỗi boundary scaffold ra 1 service repo riêng (`services/{prefix}-{boundary}/`, gitignored ở design-repo).
- Backend chỉ biết contract (`api/`, `events/`), KHÔNG biết FE boundary nào tồn tại. FE chỉ biết contract của bff/backend.
- `data-model/` chỉ tồn tại cho `kind=backend`; FE boundary KHÔNG sở hữu data-model riêng (consume bff/backend).

### P2. Contract-first

Mọi touch-point cross-boundary phải có **contract artifact** trong `docs/architecture/` TRƯỚC khi code:

| Loại | Mục đích | Nằm ở |
|---|---|---|
| API | BE↔BE, BFF↔FE qua REST/GraphQL | `api/api-{boundary}.md` (+ `api/bff-aggregation-{boundary}.md` nếu fan-out ≥2 backend) |
| Event | BE↔BE qua message bus | `events/{boundary}-events.md` |
| UI | User-flow + screen + state cho FE | `ux/ux-{boundary}.md` |

**Hệ quả**:
- Contract là file markdown trong design-repo — KHÔNG `contracts/` repo riêng, KHÔNG hash-signing. "Đã có contract trước khi consume" enforce ở REVIEW (`review-document`) + `review-dev` (checklist contract per kind).
- Breaking change → **wave sau**: lùi `/domain` sửa hợp đồng + `/approve-document` khoá lại + đối chiếu lại consumer. KHÔNG sửa tại chỗ một wave đã ship.
- Code không match contract → bắt ở `review-dev` (contract-drift) hoặc test contract fail.
- **Common error envelope + generic codes (400/401/403/404/409/429/500) GIỐNG NHAU mọi boundary** (chuẩn chung ở ADR api-error-convention); per-endpoint chỉ ref code trong Domain error catalog.

### P3. Thin-context (boot-sequence-driven)

Agent KHÔNG bao giờ load full repo:
- **Boot sequence per agent** (`scripts/build_prompt.py`) liệt kê đúng file cần đọc cho stage/role — thay vai trò MANIFEST của ZIP.
- **Locality**: tài liệu 1 boundary ở đường dẫn đoán được (`hld/hld-{boundary}.md`, `api/api-{boundary}.md`, `knowledge-base/{boundary}.knowledge-graph.yaml`).
- **Indirection ≤ 1 cấp routing** (`CLAUDE.md` ROUTING → file). Không nested router 3 cấp.

**Hệ quả**: KHÔNG "đọc hết `docs/architecture/`" rồi code — targeted load theo boot sequence + ROUTING.

### P4. Decision-traceability

Mọi quyết định non-trivial phải trace code → decision-log → source artifact:

```
code commit (# DECISION-REF: ADR-{boundary}-018)
   → tracking/decisions.md (row: wave, boundary, agent, ref=ADR-{boundary}-018)
   → docs/architecture/adr/ADR-{boundary}-018-*.md (quyết định)
   → docs/architecture/business-rules/BR-{boundary}-002.md (rule)
```

**Hệ quả**: "Agent biết rule" không đủ — phải có ADR/BR đã tồn tại. Decision mới → ADR mới (Architecture Authority approve ở DESIGN/REVIEW) → ghi `tracking/decisions.md` → code. Reverse: code khó hiểu → grep `# DECISION-REF` → tìm về ADR/BR. ADR id theo `TEMPLATE.adr` `ADR-{boundary}-{NNN}` (cross-cutting như tech-stack/auth/api-error-convention dùng namespace chung).

### P5. Single source of truth (KHÔNG duplicate cross-cut view)

Mỗi thông tin thiết kế có **đúng một** nơi authored:

| Thông tin | Source duy nhất |
|---|---|
| Vision / scope / NFR / glossary | `docs/architecture/PROJECT.md` (D3 derive, gộp aggregate D6) |
| Topology boundary + quan hệ | `docs/discovery/BOUNDARY-MAP.md` + charter per boundary |
| Ownership / owned_paths / kind / repo_url | `harness/SERVICE-BOUNDARY-MATRIX.json` |
| Design per boundary | `hld/` `api/` `data-model/` `ux/` `events/` |
| Domain model + BR per boundary | `knowledge-base/{boundary}.knowledge-graph.yaml` |

**Hệ quả**: KHÔNG tạo file "aggregate/render" duplicate (SYSTEM-ARCHITECTURE tổng hợp, CONTRACT-MAP render) — góc nhìn cross-cut derive on-demand (grep / Explore), không lưu thành second source. `harness/{STATE.json, STATE-MACHINE.json}` + `.claude/settings.json` là kernel — hook block Edit tay; transition chỉ qua slash command.

### P6. Defense in depth (multi-gate)

Một rule không đủ — 5 lớp:

```
NON-NEGOTIABLES (CLAUDE.md)            → agent đọc mỗi session
   → slash command gate (commands/*.md ↔ gates.py GATE_RULES)
   → harness/STATE.json (stage/wave/active_boundary/owned_paths)
   → hook (PreToolUse / Stop / SubagentStop / PreCompact)
   → gate script (gates.py + discovery/design/plan_gate + planning_lint)
```

**Hệ quả**: tránh "documentation-only rule" — rule giá trị phải có lớp enforce (gate hoặc hook). Vd planning-rules (epic≥2 FEAT, ADR≥2 alternatives) enforce qua `scripts/planning_lint.py` ở `domain-end`/`plan` gate (force-bypassable + audit).

---

## 2. Non-negotiable invariants

- **I1. No business logic in frontend** — FE là presentation; business rule ở backend. FE chỉ enforce display/UX validation, KHÔNG thay backend validation.
- **I2/I3. Boundary chỉ biết contract** — backend KHÔNG đọc design FE; FE KHÔNG đọc HLD/business-rules backend. Chỉ consume contract (`api/events/ux`).
- **I4. No cross-boundary code without contract** — cross-boundary call (REST/event/shared schema) phải có contract trước; thiếu → `review-dev` reject (drift).
- **I5. No decision without artifact** — non-trivial change phải có `# DECISION-REF: ADR/BR/CONTRACT` + `tracking/decisions.md` row.
- **I6. No edit kernel files tay** — `STATE.json`/`STATE-MACHINE.json`/`SERVICE-BOUNDARY-MATRIX.json`/`settings.json` chỉ đổi qua script/transition (hook block).
- **I7. Orchestrator KHÔNG Edit code** — MAIN spawn dev/fix agent; dev spawn bằng `build_prompt.py` output (hook E-6).
- **I8. Non-additive edit cần xác nhận** — modify method body/rename/delete → return `needs_review` (PRE-EDIT checklist, FM-017).

---

## 3. Layering & dependency direction

### 3.1 Backend (hexagonal — chốt ở ADR backend-architecture)

```
infra/inbound  (HTTP controller, event consumer)
   → application (use-case, command/query handler)
   → domain (entities, value objects, domain events — PURE)
   ↑ infra/outbound (DB adapter, event publisher, external client)
```
- `domain` KHÔNG depend `infra`. `application` orchestrate, KHÔNG chứa business rule chi tiết (rule ở `domain`). Outbound qua adapter pattern.

### 3.2 Frontend (web/mobile)

```
app/ (routing, providers, layout) → features/<name>/ → shared/ (design-system, utils) → services/ (API client — consume contract)
```
- Feature KHÔNG depend lẫn nhau (qua `shared`). `services/` là **ONLY layer** call backend — component KHÔNG call API trực tiếp. `shared/` không depend `features/`.

---

## 4. Anti-patterns (cấm)

| Anti-pattern | Vi phạm | Thay bằng |
|---|---|---|
| Fullstack boundary (FE+BE chung 1 boundary) | P1 | Tách 2 boundary (kind backend + web/mobile) |
| Component call REST trực tiếp | P2/3.2 | Qua `services/` consume contract |
| Magic string/ID trong code | I5 | Constant + ADR ref |
| "Đọc hết docs/architecture/" rồi code | P3 | Targeted load theo boot sequence |
| Tạo file aggregate duplicate (SYSTEM-ARCH/CONTRACT-MAP) | P5 | Derive on-demand (grep/Explore) |
| Orchestrator Edit code | I7 | Spawn dev agent |
| Sửa kernel file tay | I6 | Qua script/transition |
| Quên `# DECISION-REF` cho non-trivial commit | I5 | Validate ở `review-dev` |
| FE đọc backend HLD / backend đọc FE | I2/I3 | Consume contract |
| "Documentation rule" không có gate/hook enforce | P6 | Add gate (vd planning_lint) hoặc hook |

---

## 5. Change log

| Date | Description |
|---|---|
| 2026-06-14 | Initial — clone ADLC ARCHITECTURE-PRINCIPLES, adapt single-repo (6 principles + 8 invariants + layering + anti-patterns). |
