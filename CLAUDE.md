# ADLC Design Harness — CLAUDE.md

> **Router file.** Đọc top-to-bottom mỗi session. Tier-A only — chi tiết → routing table.

---

## NON-NEGOTIABLES

1. **Đọc `harness/STATE.json` trước mọi tool call** (hoặc xem header `[HARNESS ...]` đã được hook `UserPromptSubmit` inject).
2. **Edit chỉ trong `owned_paths`** của `active_boundary`. PreToolUse hook block; đừng cố lách.
3. **Stage transition CHỈ qua slash command** (`/start-wave`, `/dev-handoff`, `/end-wave`, …). KHÔNG sửa `stage` trong STATE.json bằng tay. **MAIN KHÔNG TỰ NỐI LỆNH:** mỗi user prompt chỉ chạy **1 stage-command** (`harness <cmd> complete`) rồi DỪNG, báo kết quả + bước kế, CHỜ user gõ lệnh tiếp — KHÔNG tự chạy `/dev-handoff`/`/test-plan`/… sau khi xong stage trước (hook turn-flag enforce; chỉ `_auto` TEST_EXECUTE→MANUAL_TEST là tự).
4. **Quyết định non-trivial → artifact ngay** (ADR / FEAT / CR / KG). Không để chỉ tồn tại trong chat.
5. **Cross-boundary change** phải qua `/apply-cr` + `/review-document` approve trước khi code.
6. **Không bypass test** (`--no-verify`, skip), không hardcode secrets. **Doc upstream PHASE-LOCKED** (hook enforce, không còn honor-system): mỗi lớp doc chỉ sửa được ở stage SỞ HỮU + REVIEW — discovery/PROJECT→DISC_*, epic/feat/journey/BR/persona→DOMAIN, adr/hld/api/data-model/ux/events/integrations→DESIGN, plans→PLAN. Muốn sửa khi đã qua stage → **LÙI** về stage sở hữu (`/design` từ PLAN, `/domain-po`/`/domain-ba` từ DESIGN) rồi tiến lại (re-gate); sau ship → `/apply-cr`. (TEMPLATE.*/README + infra/KG/tracking/services KHÔNG khoá.)

> Vi phạm sẽ bị hook block. Refusal message tham chiếu `harness/PROTOCOL.md` § Failure Modes (FM-ID).

---

## IDENTITY

| Field | Value |
|---|---|
| Project | **ADLC Design Harness** — bộ khung orchestrator cho workflow ADLC (Architecture-Driven Lifecycle), kết hợp agent + người theo chuẩn harness |
| Repo type | **Design repo** — chứa harness kernel + docs + plans + agents + skills + commands + tracking + knowledge-base. KHÔNG chứa code service. |
| Strategy | **Polyrepo** — mỗi boundary scaffolded ở `/start-dev` là 1 repo riêng (`{prefix}-{boundary}`). Service repos sống ngoài, link qua `SERVICE-BOUNDARY-MATRIX.json` field `repo_url`. |
| Kernel stack | Python 3.14 (state engine + hooks + materialize + build_prompt) |
| Service stack | Per-boundary, set ở DESIGN (`/design`, technical-design). Vd: Java 21 + Spring Boot 3.4, Node.js 22 + Apollo, React 19 + Vite, Flutter 3, … |
| Scale | 17 states · 24 commands · N waves · M boundaries (boundary/wave set dynamic ở PLAN qua `/plan`) |
| `services/` trong repo này | **gitignored** — chỉ working dir tạm khi sub-agent scaffold (push lên repo riêng, không track ở đây) |

> Khi fork harness này cho project mới: Discovery D3 (`/discovery-start D3`) sẽ derive IDENTITY (project name, prefix, scale) vào `docs/architecture/PROJECT.md` (gộp vai trò aggregate D6 của ADLC).

---

## ADLC MAPPING — phủ ĐỦ D0-D7 (gộp single-repo)

> Harness **phủ 100% intent D0-D7** của ADLC ZIP (multi-repo), nhưng **gộp** 8 ZIP-wave → 4 discovery wave + 3 stage (single-repo không có handoff cross-repo). KHÔNG drop chức năng.

| ZIP wave (multi-repo) | → Harness (gộp) | Cách |
|---|---|---|
| D0 hypothesis | `DISC_D0` | clone |
| D1 persona + capability | `DISC_D1` | clone |
| D2 event-storming | `DISC_D2` | clone |
| D3 boundary + charter + stack-ADR · **D6** aggregate (PRD/ROADMAP/SYS-ARCH/TECHSTACK) | `DISC_D3` → BOUNDARY-MAP + CHARTER + **PROJECT.md** | clone D3 + **fold D6** (stack-ADR move sang DESIGN; SYS-ARCH/TECHSTACK rải PROJECT+BOUNDARY-MAP+HLD) |
| (ZIP `-DOMAIN` repo: FEAT/EP/BR/journey/persona + translate) | `DOMAIN_AUTHORING` | clone A1: author BUSINESS plain VN `docs/domain/` (`/domain-po`,`/domain-ba`) → KÝ `/domain-approve` (`status: APPROVED`) → `/domain-translate` (domain-translator) dịch sang eng `docs/architecture/`. Bỏ SPECS-hub/cross-repo-sync (plumbing multi-repo); GIỮ 2-lớp business↔eng + ký + jargon-lint |
| **D3.5** standards-enrich · **D4** contracts · **D5** full CHARTER | `DESIGN` (`/design`) | **gộp** → ADR (stack) + HLD (=D5) + API/events/integrations (=D4); D3.5 coding-standard = skill `rules-{kind}`+`ref-{kind}-pattern` (cụ thể sẵn, không cần enrich) |
| **D7** WAVE-SEQUENCE | `PLAN` (`/plan`) | move → WAVE-SEQUENCE + wave-*.md + MATRIX |
| DISCOVERED + sync-to-specs | `REVIEW` | replace → approve → `/start-wave` |

**Bỏ có chủ đích (multi-repo plumbing, single-repo không cần):** contract-signing/hash-drift (D4), `_shared/*` placeholder-enrich layer (D3.5), `/sync-to-specs`/SPECS hub, SYSTEM-TOPOLOGY/CONTRACT-MAP tách rời, multi-role Authority sign-off, BLOCKED state. **FEAT KHÔNG sinh ở Discovery** (cả ZIP lẫn harness — DOMAIN sở hữu).

**Flow stage (17 state):** `BOOTSTRAP → DISC_D0 → DISC_D1 → DISC_D2 → DISC_D3 → DOMAIN_AUTHORING → DESIGN ↺ → PLAN → REVIEW → WAVE_OPEN → DEV → REVIEW_DEV → DEV_HANDOFF → TEST_PLAN → TEST_EXECUTE → MANUAL_TEST → DONE`. `DESIGN` self-loop (`/design` hệ-thống/contract + `/design-ux` UX/UI — cả 2 refine được, `/design-end` advance). **Back-edge (lùi sửa doc phase-locked):** `PLAN --/design,/design-ux--> DESIGN`, `DESIGN --/domain-po,/domain-ba--> DOMAIN_AUTHORING` (dùng lại lệnh entry; tiến lại re-gate). `apply-cr`: `DONE → DOMAIN_AUTHORING` (CR feature mới author epic/feat/BR; CR kiến trúc-only → `/domain-end` qua thẳng → DESIGN). `done-wave`: `DONE → BOOTSTRAP` (docs giữ; discovery re-runnable idempotent cho increment kế). Boundary MỚI → done-wave→`/discovery-start D3`.

---

## ROUTING (load on demand)

| Câu hỏi | File / Command |
|---|---|
| "Tôi đang ở stage nào?" | `py scripts/harness.py state` |
| "Command nào được phép gọi tiếp?" | `state` output `allowed_commands[]` |
| "Quy trình state X?" | `harness/PROTOCOL.md` § `<state>` |
| "Gate của command Y?" | `commands/<Y>.md` frontmatter `gates:` |
| "Failure mode đã biết?" | `harness/PROTOCOL.md` § FM-* + `grep knowledge-base/` |
| "Ý tưởng/giả thuyết project (tổng quan)?" | `docs/discovery/hypothesis-log.md` (D0) |
| "Persona + capability map?" | `docs/discovery/persona-pool.md` + `docs/discovery/capability-map.md` (D1) |
| "Event storming domain?" | `docs/discovery/event-storming/ES-{domain}.md` (D2) |
| "Boundary nào, charter ra sao?" | `docs/discovery/BOUNDARY-MAP.md` + `docs/discovery/boundaries/{b}/CHARTER.md` (D3) |
| "Epic / Feature / Business-rule (BUSINESS, plain VN — PO/BA ký)?" | `docs/domain/{epics/EP-*,feat/FEAT-*,business-rules/BR-*,journeys,personas}.md` (lớp business, A1) |
| "Epic / Feature / Business-rule (ENG — dịch từ business, DESIGN/PLAN đọc)?" | `docs/architecture/{epics/EP-*,feat/FEAT-*,business-rules/BR-*}.md` (đầu ra `/domain-translate`) |
| "Project này làm gì? Stack? Scope?" | `docs/architecture/PROJECT.md` |
| "Nguyên tắc kiến trúc / invariants bất biến?" | `docs/architecture/ARCHITECTURE-PRINCIPLES.md` |
| "Severity / test-type / tag taxonomy?" | `docs/architecture/SEVERITY-TEST-TAXONOMY.md` |
| "Feature X yêu cầu gì?" | `docs/architecture/feat/FEAT-X-*.md` |
| "Boundary design ra sao?" | `docs/architecture/hld/hld-{boundary}.md` |
| "API contract boundary?" | `docs/architecture/api/api-{boundary}.md` |
| "Schema boundary?" | `docs/architecture/data-model/data-model-{boundary}.md` |
| "Màn nào thuộc boundary nào / mockup ở đâu?" | `docs/architecture/ux/SCREEN-MAP.md` (mục lục màn ↔ boundary ↔ FEAT ↔ mockup) |
| "UX behavior boundary (states/API/validation)?" | `docs/architecture/ux/ux-{boundary}.md` |
| "Look màn X?" | `docs/architecture/ux/mockups/{boundary}/{screen}.html` (mở browser) |
| "Design tokens dùng chung (màu/spacing/typography)?" | `docs/architecture/ux/design-tokens.css` (SoT mọi web boundary, G15) |
| "Event boundary phát/nhận?" | `docs/architecture/events/{boundary}-events.md` |
| "Tích hợp service nội bộ / external?" | `docs/architecture/integrations/INTEG-{INT\|EXT}-*.md` |
| "Wave N kế hoạch?" | `docs/plans/WAVE-SEQUENCE.md` + `docs/plans/wave-{N}.md` |
| "Boundary ownership / owned_paths / repo_url?" | `harness/SERVICE-BOUNDARY-MATRIX.json` |
| "Lịch sử quyết định kiến trúc?" | `docs/architecture/adr/ADR-*.md` |
| "Domain model + business rule per boundary?" | `knowledge-base/{boundary}.knowledge-graph.yaml` |
| "Test cases wave hiện tại?" | `tracking/wave-{N}/test-case-registry.md` |
| "Bug đang open?" | `tracking/wave-{N}/bugs.md` |
| "Skills cho `kind` nào?" | `commands/start-dev.md` § kind_matrix |
| "Skills cho ``kind`` nào ở đâu?" | ``.claude/skills/<skill-name>/SKILL.md`` (auto-load on-demand bởi Claude Code) |
| "Cấu hình local dev (docker-compose)?" | `docs/architecture/infra/docker-compose.yml` |

---

## SLASH COMMANDS

```
# Discovery (2) — clone tối giản ADLC DISCOVERY (D0-D3 ideation), chạy TRƯỚC domain
/discovery-start <D0|D1|D2|D3>            TIẾN qua wave (D0→D1→D2→D3): nhảy tiến = gate wave hiện tại (discovery_advance) rồi spawn agent wave kế; gọi lại cùng wave = refine. complete-before-spawn (STATE đổi NGAY để phase-lock cho agent ghi docs/discovery). Agent: D0 hypothesis · D1 capability+persona · D2 event-storming · D3 charter+PROJECT.md+prefix (KHÔNG sinh FEAT)
/discovery-end                            CHỐT Discovery (1 lần, ở DISC_D3, KHÔNG arg): verify gate D3 → DOMAIN_AUTHORING. Override: force+reason ghi decisions.md

# Domain (5) — clone ADLC DOMAIN (A1): author BUSINESS plain VN (docs/domain/) → KÝ → TRANSLATE sang eng (docs/architecture/)
/domain-po <EPIC|FEATURE|JOURNEY>         Spawn po-author → viết BUSINESS vào docs/domain/{epics,feat,journeys}. **Loop tới khi user OK + hỏi "Câu hỏi cho Author" ngay sau khi viết.** status DRAFT (KHÔNG approve). Self-loop
/domain-ba <BR|PERSONA>                   Spawn ba-author → viết BUSINESS vào docs/domain/{business-rules,personas}. Loop + hỏi ngay. status DRAFT
/domain-approve [<id>]                    KÝ business doc (`status: APPROVED`) — lẻ `<id>` hoặc **toàn bộ (không arg = all)**. jargon-check + stamp (`domain_approve.py` — BẮT BUỘC chạy script). Gate `domain_no_jargon` + `domain_stamped` (file trên disk phải ĐÃ stamp lúc complete — chặn "approve chay" khiến doc vẫn DRAFT)
/domain-translate                         Spawn domain-translator → DỊCH docs/domain/ (đã ký) sang eng `docs/architecture/` (giữ ý nghiệp vụ, field kỹ thuật = TODO-engineer). Gate `domain_signed` (mọi doc ký)
/domain-end                               Verify gate (≥1 eng epic+feat+BR ở docs/architecture/) → DESIGN. Override: force+reason ghi decisions.md

# Design + Plan (4) — tách từ intake cũ, stage riêng; UX tách vai riêng
/design                                   (DESIGN→DESIGN, self-loop) Spawn solution-architect (technical-design): ADR/HLD/API/data-model/events/integrations — hệ thống/contract, KHÔNG UX. Chạy lại để THẢO LUẬN/REFINE — KHÔNG advance
/design-ux                                (DESIGN→DESIGN, self-loop) Spawn ux-designer (ux-design): THIẾT KẾ THEO TỪNG MÀN bằng HTML — SCREEN-MAP.md trước (mục lục màn↔boundary↔FEAT↔mockup; gán theo hint FEAT/persona, mơ hồ hỏi user) → mockup tĩnh per MÀN `ux/mockups/{b}/{screen}.html` (mở browser duyệt look, chỉ var(--...), KHÔNG ASCII) + ux-{boundary}.md (behavior) + design-tokens.css — chạy SAU /design (consume api-{be}.md). Refine tới vừa ý
/design-end                               (DESIGN→PLAN) Đóng design khi CẢ /design lẫn /design-ux vừa ý. Gate design_gate: ADR≥3 + INTEG≥1 + per-boundary completeness (backend/bff→hld+api, web/mobile→hld+ux) + design-tokens.css khi có web. KHÔNG spawn author mới
/plan                                     (PLAN→REVIEW) Spawn program-planner (implementation-plan): WAVE-SEQUENCE+wave-{N}+MATRIX+KG. Gate: plan_gate + plan_integrity (FEAT-id có file + depends_on no-cycle) + matrix_coherence (phủ đủ boundary đúng kind)

# Core flow (review→wave)
/review-document ["<feedback>"] [--file X] (REVIEW) 2 mode: CÓ arg = revision (sửa doc theo comment user, lặp tới OK); KHÔNG arg = sanity-check (soi gap/mâu-thuẫn/thiếu-độ-phủ năng-lực → ghi tracking/doc-review-findings.md DR-NNN; bắt thiếu auth/login trước build)
/approve-document                         (REVIEW) User mark doc OK (approved=true) + STAMP status vào doc (`approve_document.py`: adr/hld/data-model/ux/integ → APPROVED; api/events → ACTIVE). KHÔNG đổi state. Gate doc_review (sanity-check đã chạy + no open BLOCKER/MAJOR) + doc_stamped (stamp phải đã xảy ra trên disk). Cho phép /start-wave
/start-wave <N>                           (REVIEW→WAVE_OPEN) Mở wave, materialize boundaries + agents + KG (gate: approved=true)
/start-dev <boundary>                     Vào DEV, spawn dev sub-agent boundary (auto detect kind)
/review-dev                               Review cả wave. Review ghi findings; MAIN spawn fix Mode B → re-review tới open_findings==0
/dev-handoff                              Gate all_boundaries_reviewed (mọi wave_boundary review pass + coverage theo kind BE80/BFF70/web|mobile60 — coverage HARNESS DERIVE từ report thật jacoco/coverage-summary/lcov khi service đã scaffold, không tin số tự khai) → TEST_PLAN
/test-plan                                Sinh test-case-registry.md
/test-execute                             Build local + run auto test + log bug (origin=auto). KHÔNG fix. Auto-transition MANUAL_TEST (pass/fail); bug fix qua /fix-bugs
/end-wave                                 Soft close, STOP service (docker compose stop — giữ image+volume) → DONE (gate: UAT signed + test_result=pass + no_open_bugs)
/done-wave                                Hard close, teardown (down --volumes) → BOOTSTRAP

# Branch (2)
/log-bug "<mô tả>"                        Ghi 1 bug manual (UAT) vào bugs.md (spawn log-bug-agent, origin=manual). Chỉ ghi, không fix
/fix-bugs [<bug-id>]                       Fix bug (Mode A). Không arg = sweep mọi bug open; có bug-id = fix 1 cái. MAIN spawn fix → re-run TC verify → close

# Side (1)
/apply-cr <CR-ID>                         (DONE→DOMAIN_AUTHORING) Change request re-enter DOMAIN: CR feature → /domain-po//domain-ba author business → /domain-approve → /domain-translate; CR kiến trúc-only → /domain-end thẳng. Re-flow → /design → /design-end → /plan → REVIEW → /start-wave
```

Mỗi command tự document trong `.claude/commands/<name>.md` (sync từ `commands/<name>.md` qua `py scripts/sync_commands.py`).

---

## RUNTIME GUARANTEES (do hooks cung cấp)

- `SessionStart` hook in STATE summary (brief: stage/wave/boundary/last_completed/allowed_next). Non-negotiables inject vào spawn prompt sub-agent (build_prompt), KHÔNG ở SessionStart hook.
- `UserPromptSubmit` hook inject `[HARNESS stage={stage} wave={wave} boundary={b} | next: {gợi-ý-chính-xác}]` mỗi turn — `next` là **bước tiếp contextual** (lệnh + arg + nghĩa + back-edge), không phải list tên trống (policies.STAGE_NEXT_GUIDE). SessionStart brief cũng dùng. **+ reset turn-flag** (`harness/.turn-advance.flag`) → mở 1 lượt cho **1 stage-command** (chống MAIN tự nối lệnh — xem PreToolUse(Bash)).
- `PreToolUse(Bash)` hook check `harness <X> complete`: allowed_commands (theo STATE-MACHINE) + gate (gates.py). Gate single-repo nổi bật: `/domain-end` thêm `translation_parity` (**business đã KÝ ↔ eng doc 1-1** qua frontmatter `source`/`domain_source_id` — translate bỏ sót = chặn; eng epics/feat/BR không có source = mồ côi = chặn); `design_gate` = ADR≥3 + INTEG≥1 + **per-boundary completeness** (backend/bff→hld+api, web/mobile→hld+ux) + **có FE boundary → `ux/design-tokens.css` + `ux/SCREEN-MAP.md` (parse từng row: mockup phải TỒN TẠI + dùng token; màn gán boundary ma / web boundary 0 màn = chặn; màn TUÂN THỦ FEAT: trace FEAT ma = chặn, FEAT `has_ui_touchpoint` không deferred mà 0 màn = chặn)** — thiết kế theo MÀN nhưng FEAT là nguồn sinh màn — ở `/design-end` + `todo_resolved` (**marker `TODO engineer`/`TBD (DESIGN)` translator để lại phải điền hết** — BR không có enforcement_location = rule không được code); `/plan` = `plan_gate` + `plan_integrity` (FEAT-id trong MATRIX có file + **chiều ngược: FEAT-*.md không vào `features[]` boundary nào = MỒ CÔI = chặn**, opt-out `status: deferred|dropped` + `depends_on` no-cycle/no-dangling) + `matrix_coherence` (MATRIX phủ đủ boundary BOUNDARY-MAP đúng kind) + `contract_graph_parity` (**đồ thị contract**: api-*.md `consumers[]` + INTEG-INT consumer/producer + events subscribers ↔ MATRIX `depends_on`/`consumed_by` khớp 2 chiều — cạnh gọi nhau không contract doc / contract khai cạnh ma = chặn); `planning_lint` thêm **ref-integrity** epic↔feat↔BR↔journey↔persona — persona-ref dùng **file-id `PERSONA-{prefix}-NNN`** (file-backed, không dùng P-id pool). `/approve-document` = `doc_review` (sanity-check `/review-document` **no-arg** phải đã chạy ghi `tracking/doc-review-findings.md` + KHÔNG còn gap BLOCKER/MAJOR open — bắt **thiếu năng lực nền vd auth/login** + mâu thuẫn + thiếu-độ-phủ TRƯỚC khi build; mirror `review-dev no_open_findings` cho TÀI LIỆU). **Back-half content-gate (chống tự-khai, e2e-driven):** `/dev-handoff` = `infra_proof` (docker-ps.json: mọi wave service `State=running`) + `health_proof` (health-proof.json do `capture_infra_proof.py` HARNESS curl `/health/ready` → mọi service 2xx; State=running chưa đủ) + `code_compliance` (backend: cấm H2/`com.h2database`/`jdbc:h2`/`ddl-auto: create-drop`, bắt Dockerfile + base `application.yml` + **≥1 profile file `application-<env>.yml`** theo ref-backend-config — G11) + `web_styling` (FE unstyled + G15: plain-CSS phải dùng design token `var(--...)` từ `ux/design-tokens.css` **VÀ token phải được định nghĩa/import trong bundle** — var không định nghĩa = resolve rỗng = vẫn unstyled) + `api_contract_proof` (**endpoint khai `api-{b}.md` phải tồn tại trong runtime OpenAPI** — `capture_infra_proof.py` fetch `/v3/api-docs` mỗi backend → `api-proof.json`; bắt contract↔implementation drift kiểu BUG-006 trước khi test; boundary GraphQL/không api doc → miễn); `/test-plan` = (infra_proof + health_proof) + `contract_test_present` (consumer có depends_on trong wave phải có ≥1 auto-TC contract|integration|e2e — G4/G6) + `ui_test_present` (**mỗi web boundary ≥1 auto-TC UI in-scope** — chống UI toàn manual/vắng không bao giờ được mở thật) + `registry_scope` (**auto-TC chỉ trace FEAT thuộc wave plan ≤ wave hiện tại; FEAT/AC deferred phải tag @deferred** — chống over-scope test feature chưa build sinh bug rác) + `ac_coverage` (**FEAT.AC ↔ TC 2 chiều**: parse `### AC-n` trong FEAT-*.md vs cột feature+AC registry — AC in-scope không TC = mồ côi; TC trace AC không tồn tại = stale sau /apply-cr); `/test-execute` = `test_evidence` (parse test-report+test-logs+bugs.md+screenshots+health-proof: auto-TC in-scope phải có network-call thật `METHOD path -> sts`; skip phải nêu service-down bằng **marker cụm-từ cụ thể** VÀ **không mâu thuẫn health-proof** (proof nói UP → skip bị chặn, service chết thật → re-run capture_infra_proof.py); **TC web boundary pass|fail phải có screenshot PNG/JPEG thật** `screenshots/{TC}*.png` (magic-bytes) = chống UI-test khống; **FAIL phải có bug reference cột TC** = chống miss-bug, mirror ZIP `lint_execution`; **harness DERIVE `test_result` từ report**, không lấy verbatim agent); `/plan` thêm `api_transport` (api spec KHÔNG truyền tenant-id qua query → header/JWT claim, G6) + `wave_sequence_lint` (WAVE-SEQUENCE §wave-NNN: enum class/strategy + target_count≤3/layer + strategy layer-purity + vertical parent_epic + inherited_active file tồn tại — port ZIP wave-sequence-validate, G16). Deferred-scope (G1): TC `@deferred` khai báo ở `wave-{N}.md §6 Deferred` → test-execute skip → end-wave close sạch không cần ép. Mọi gate force-bypass (`force:true,reason`) ghi audit `decisions.md`. **+ turn-flag (#11): chỉ 1 `harness complete` mỗi user-turn** — complete thứ 2 trong cùng lượt bị deny ("MAIN tự nối lệnh"); gate-fail KHÔNG tiêu cờ (cho retry). Reset ở UserPromptSubmit/SessionStart.
- `PreToolUse(Write|Edit)` hook block edit kernel files (`harness/STATE.json`, `STATE-MACHINE.json`, `SERVICE-BOUNDARY-MATRIX.json`, `.claude/settings.json`) + **3 proof file harness-đo** (`tracking/*/{docker-ps,health-proof,api-proof}.json` — CHỈ `capture_infra_proof.py` được sinh; agent ghi tay = fake bằng chứng, FM-PROOF-FORGE) + **phase-lock doc upstream** (`policies.phase_lock_violation`): doc thuộc lớp discovery/domain/design/plan chỉ sửa ở stage sở hữu (+REVIEW); stage khác → block kèm hướng lùi. Port single-repo của ZIP `pretooluse-readonly-inputs.py`. TEMPLATE.*/README + infra/KG/tracking/services miễn (riêng services/ bị chặn khi `spawn.active=dev-handoff-agent` — #12). **#12 dev-handoff infra-only:** `_pre_task` set `spawn.active=dev-handoff-agent` khi spawn agent đó → `PreToolUse(Write|Edit)` block sửa `services/**` (lỗi code boundary → fix-agent, không dev-handoff tự vá).
- `PreToolUse(Task)` hook KHÔNG block theo stage. Explore agent free. Inject reminder boundary cho dev-spawn + **block spawn MỌI command-agent bằng prompt tự viết tay** (E-6: phải dùng `build_prompt.py` output). Detect 2 nhánh: keyword `DEV_SPAWN_KEYWORDS` (`start-dev`/`fix-bugs`/`review-dev`/`domain-po`/`domain-ba`/`domain-translate`/`design-ux`/**`test-plan`/`test-execute`**) HOẶC tên-agent registry (`agents/*-agent.md`). Prompt thiếu chữ ký `# SPAWN PROMPT`/`STATE BUNDLE` = block (`MAIN KHÔNG tự build prompt`).
- `PreToolUse(Skill|SlashCommand)` hook **chặn MAIN TỰ chạy harness slash-command** (auto-nối pipeline ở auto mode): MAIN gọi Skill/SlashCommand tool để chạy lệnh ∈ `GATE_RULES` (`/dev-handoff`,`/test-plan`,`/test-execute`,`/start-wave`,…) → deny ("MAIN KHÔNG TỰ NỐI LỆNH"). Lệnh user **GÕ tay** = pre-loaded (MAIN không gọi tool) → không ảnh hưởng; skill ngoài-harness (research/code-review/…) → cho qua. Vá lỗ hổng turn-flag: invoke slash-command fire lại `UserPromptSubmit` → reset cờ → `harness complete` kế lọt; chặn NGAY tại nguồn (trước khi slash-command reset cờ).
- `PostToolUse(Bash)` hook no-op (STATE.json chỉ giữ trạng thái hiện tại — KHÔNG ghi history/checkpoint).
- `SubagentStop` hook validate RETURN SCHEMA (7 field bắt buộc: completed/deferred/needs_review/files_changed/build/lint/test). `kg_appended` chỉ soft-guidance trong spawn prompt, KHÔNG enforce ở hook.
- `Stop` hook chạy build/lint/test **wave-scoped** (mọi `wave_boundaries` theo `kind`) khi `stage` ∈ {DEV, REVIEW_DEV, TEST_EXECUTE} VÀ turn có sửa file trong `services/{prefix-boundary}/`. Đỏ → block stop kèm 40 dòng output cuối; xanh → allow. Cache theo git hash, không rerun nếu code không đổi.
- `PreCompact` hook pin STATE hiện tại (stage + active wave + boundary) vào summary.

> Hook config: `.claude/settings.json`. Scripts: `scripts/hooks/`.

---

## TIER B / C — load on demand

- **Tier B** (load khi vào stage):
  - `docs/plans/wave-{N}.md`
  - `hld/api/data-model/events/ux` của `active_boundary`
  - `knowledge-base/{boundary}.knowledge-graph.yaml`
  - `tracking/wave-{N}/*.md`
- **Tier C** (queried bằng `grep` / Explore subagent):
  - Toàn bộ `docs/architecture/{adr,feat,integrations,infra}/`
  - `commands/*.md` body (frontmatter đã inline ở SLASH COMMANDS trên)

> KHÔNG đọc full `docs/architecture/` rồi mới code. Targeted loads only.

---

## Change Log

> **Tách ra [`docs/HARNESS-CHANGELOG.md`](docs/HARNESS-CHANGELOG.md)** (append-only) — router này chỉ giữ trạng thái HIỆN TẠI. Thay đổi non-trivial → thêm row ở CUỐI file changelog (mới nhất dưới cùng), KHÔNG ghi vào đây.
