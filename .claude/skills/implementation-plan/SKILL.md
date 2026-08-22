---
name: implementation-plan
description: Stage PLAN (/domain, program-planner) — WAVE-SEQUENCE + wave-{N}.md cho MỌI wave (full plan toàn dự án, nhiều wave=sprint phụ thuộc nhau) + materialize MATRIX + KG skeleton. Sau DESIGN, trước REVIEW.
---

# Implementation Plan Skill

## Khi load
Command **`/domain`** (stage **PLAN** → REVIEW) — agent `program-planner-agent`, sau `/domain`.
Input: `docs/architecture/PROJECT.md` (Discovery D3) + product DOMAIN (`epics/`, `feat/` AC+BR, `business-rules/`, `journeys/`, `personas/`) + design (`adr/HLD/api/data-model/integrations/ux/events`) + charter boundaries (`docs/discovery/boundaries/*/CHARTER.md`).
WAVE-SEQUENCE theo `docs/plans/TEMPLATE.WAVE-SEQUENCE.md` (clone ADLC, adapt single-repo): có field `wave_class`/`wave_strategy`/`target_count_per_layer` + block YAML per-wave (`### §wave-NNN`) + `targets`=boundary_id từ MATRIX + contract trỏ `docs/architecture/{api,events,ux}/` — điền theo template. `start-wave` đọc wave-number → boundaries từ MATRIX; còn `wave_class`/`wave_strategy`/`targets` **được gate `wave_sequence_lint` ở `/domain`** (enum + cap≤3 + strategy layer-purity + vertical parent_epic + inherited_active file tồn tại) → phải điền §2 block YAML đúng schema.

## Wave = sprint — dự án chia thành NHIỀU wave
- **1 wave = 1 sprint** giao được 1 lát sản phẩm chạy end-to-end.
- **Dự án luôn chia thành nhiều wave** (≥ 2 khi có phụ thuộc) — KHÔNG gom hết mọi boundary/FEAT vào 1 wave.
- **Wave sau phụ thuộc wave trước** (tính năng này chờ tính năng khác): vd `order` chờ `auth` + `catalog`; `payment` chờ `order`; `customer-app` chờ API order/catalog.
- **Intake sinh FULL PLAN toàn dự án**: WAVE-SEQUENCE + **chi tiết MỌI wave** (`wave-001.md … wave-00N.md`) ngay từ đầu.

## Deliverable của /domain (đúng cái gate plan verify)
1. **`docs/plans/WAVE-SEQUENCE.md`** — **roadmap toàn dự án** theo `TEMPLATE.WAVE-SEQUENCE.md`: chia **toàn bộ** boundary/FEAT thành **nhiều wave** theo phụ thuộc. Mỗi wave: goal + boundaries in scope + features + **dependencies (cần gì từ wave trước)** + estimated effort + exit criteria. (Wave 1, Wave 2, Wave 3, …)
2. **`docs/plans/wave-001.md` … `wave-00N.md`** — chi tiết **MỌI wave** (mỗi wave 1 file theo `TEMPLATE.wave.md`): boundaries in scope, FEAT + AC count, thứ tự dev (foundation trước), cross-wave dependency, exit criteria. *(Scope đổi về sau → refine wave-{N}.md qua `/domain`.)*
3. **`harness/SERVICE-BOUNDARY-MATRIX.json`** — materialize từ decomposition: **≥ 1 boundary**, mỗi boundary `{boundary_id, kind, prefix, tech{language,framework,data_store}, wave, features[], ref_skills[], depends_on, consumed_by}` (+ `owned_paths`/`repo_url` nếu có).
   - `features[]` = FEAT-id boundary đảm nhận → nguồn cho `STATE.wave_features` khi `/run-wave` (mỗi FEAT gắn đúng boundary + wave).
   - `ref_skills[]` = **situational ref skill** boundary cần (ngoài scaffold pattern/config/logging tự động) — suy từ design step 3: boundary **phát/nhận event** (có `events/{boundary}-events.md`) → thêm ref event; **dùng cache/lock** → ref cache; nhu cầu khác (search, grpc…) → ref tương ứng. Tra tên skill có sẵn ở `.claude/skills/ref-{kind}-*`. Để rỗng `[]` nếu chỉ CRUD thuần. *(Đây là nơi DUY NHẤT quyết ref per-boundary → materialize vào dev agent + build_prompt.)*
4. **KG skeleton per boundary** — `knowledge-base/{boundary}.knowledge-graph.yaml` (chỉ `metadata`; các section còn RỖNG). **KHÔNG điền entities/business_rules/events ở đây** — docs còn sửa qua `/domain`. Phần design được **seed ở `/run-wave`** từ docs cuối (sau approve); phần kinh nghiệm do dev/fix/review append.

> **MATRIX là kernel file** (PreToolUse chặn Write/Edit tay) — KHÔNG ghi bằng Write tool. Materialize qua script:
> ```bash
> py scripts/materialize_matrix.py <boundaries.json>     # hoặc --json '[...]' ; --mode merge ; --dry-run
> ```
> Script gate `stage ∈ {BOOTSTRAP, PLAN}`, validate (kind hợp lệ, boundary_id unique, depends_on tồn tại) rồi ghi MATRIX + bump revision.

## Phương pháp chia wave
1. **Map FEAT → boundary**: từ charter boundaries (Discovery D3) + FEAT/`epic_ref` (DOMAIN) + decomposition (DESIGN).
2. **Dựng đồ thị phụ thuộc** boundary/FEAT (`depends_on`): cái gì cần cái gì ready trước.
3. **Topological → wave** (sprint):
   - **Wave 1 = foundation mỏng** (auth/shared + 1–2 capability core) đủ chạy **E2E sớm** (login + 1 luồng nghiệp vụ chính).
   - **Wave kế** = boundary/FEAT phụ thuộc wave trước, nhóm theo lát giá trị ship được cùng nhau; ghi rõ `dependencies` từ wave trước.
   - Lặp tới khi **mọi** boundary/FEAT đã vào 1 wave.
4. **Viết wave-{N}.md cho mọi wave** (theo `TEMPLATE.wave.md`).
5. **Materialize MATRIX** (mỗi boundary: `wave` + `features[]` + `ref_skills[]` + `depends_on`) + **KG skeleton** per boundary.

## Flow (/domain)
- Iterate với user: trình bày WAVE-SEQUENCE (toàn dự án) + tất cả wave-{N}.md + MATRIX → "OK chưa? chỉnh gì?" → sửa. Lặp tới khi user confirm (không giới hạn số vòng).
- Sau user confirm: return RETURN SCHEMA với `user_confirmed: true` → main chạy `py scripts/harness.py plan complete '{}'` (gate plan_gate: WAVE-SEQUENCE + MATRIX + wave files + KG) → transition PLAN → REVIEW.

## Quality checklist
- [ ] WAVE-SEQUENCE phủ **100% boundary + FEAT** (không sót, KHÔNG gom hết vào 1 wave). **Gate `plan_integrity` enforce chiều ngược:** FEAT-*.md không nằm trong `features[]` boundary nào = MỒ CÔI = chặn (chủ động hoãn/bỏ → frontmatter `status: deferred|dropped`).
- [ ] **Contract graph khớp MATRIX (gate `contract_graph_parity`):** `depends_on`/`consumed_by` trong MATRIX khớp 2 chiều với api-*.md `consumers[]` + INTEG-INT consumer/producer + events subscribers — cạnh gọi nhau phải có contract doc ghi nhận, contract không được khai cạnh MATRIX không có.
- [ ] **No orphan capability** — mỗi wave cover ≥1 capability từ CHARTER §3; mọi capability có wave (ZIP planning-rules).
- [ ] Chia **≥ 2 wave** khi có phụ thuộc; thứ tự topological (không phụ thuộc ngược/vòng).
- [ ] **Mỗi wave trong WAVE-SEQUENCE có file `wave-{N}.md` detail tương ứng** (full plan).
- [ ] Mỗi wave có goal + boundaries + features + **dependencies từ wave trước** + exit criteria.
- [ ] **MỌI wave điền đủ `wave_class` + `wave_strategy` + `targets` + §2 block YAML** (gate `wave_sequence_lint` parse: enum + `target_count_per_layer ≤ 3` + strategy layer-purity + vertical `parent_epic` + `inherited_active` file tồn tại — sai field này chặn `/domain`).
- [ ] Wave 1 mỏng, chạy được **E2E** (foundation + 1 lát core).
- [ ] **Deferred-scope khai báo tường minh**: AC/feature chủ động hoãn sang wave sau (auth/idempotency/event ở wave CRUD…) ghi vào `## 6 → Deferred to later waves` của `wave-{N}.md` (token `FEAT-NNN[:AC-M]`/`BR-NNN`). Đây là SoT để test-plan tag `@deferred` → test-execute skip → end-wave close sạch (không cần ép `test_result`).
- [ ] MATRIX mỗi boundary đủ `kind/prefix/tech/wave/features/depends_on`; `ref_skills[]` suy từ design (event/cache/extra → ref tương ứng; CRUD thuần để rỗng); KG skeleton mọi boundary.
- [ ] **Không có `TBD` / section trống mơ hồ** — chỗ chưa chốt ghi `Open question` (cần ai quyết + vì sao).

## Done
- WAVE-SEQUENCE + **wave-{N}.md cho mọi wave** + MATRIX (≥1 boundary) + KG skeleton (khớp gate plan_gate); user đã confirm → PLAN → REVIEW (rồi /approve-document → /run-wave).
