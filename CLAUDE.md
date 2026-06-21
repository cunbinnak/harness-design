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
| Scale | 17 states · 23 commands · N waves · M boundaries (boundary/wave set dynamic ở PLAN qua `/plan`) |
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

**Flow stage (17 state):** `BOOTSTRAP → DISC_D0 → DISC_D1 → DISC_D2 → DISC_D3 → DOMAIN_AUTHORING → DESIGN ↺ → PLAN → REVIEW → WAVE_OPEN → DEV → REVIEW_DEV → DEV_HANDOFF → TEST_PLAN → TEST_EXECUTE → MANUAL_TEST → DONE`. `DESIGN` self-loop (`/design` refine, `/design-end` advance). **Back-edge (lùi sửa doc phase-locked):** `PLAN --/design--> DESIGN`, `DESIGN --/domain-po,/domain-ba--> DOMAIN_AUTHORING` (dùng lại lệnh entry; tiến lại re-gate). `apply-cr`: `DONE → DOMAIN_AUTHORING` (CR feature mới author epic/feat/BR; CR kiến trúc-only → `/domain-end` qua thẳng → DESIGN). `done-wave`: `DONE → BOOTSTRAP` (docs giữ; discovery re-runnable idempotent cho increment kế). Boundary MỚI → done-wave→`/discovery-start D3`.

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
| "UX / wireframe boundary?" | `docs/architecture/ux/ux-{boundary}.md` |
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
/domain-approve [<id>]                    KÝ business doc (`status: APPROVED`) — lẻ `<id>` hoặc **toàn bộ (không arg = all)**. jargon-check + stamp (`domain_approve.py`). Gate `domain_no_jargon`
/domain-translate                         Spawn domain-translator → DỊCH docs/domain/ (đã ký) sang eng `docs/architecture/` (giữ ý nghiệp vụ, field kỹ thuật = TODO-engineer). Gate `domain_signed` (mọi doc ký)
/domain-end                               Verify gate (≥1 eng epic+feat+BR ở docs/architecture/) → DESIGN. Override: force+reason ghi decisions.md

# Design + Plan (3) — tách từ intake cũ, stage riêng
/design                                   (DESIGN→DESIGN, self-loop) Spawn solution-architect (technical-design): ADR/HLD/API/data-model/UX/events/integrations. Chạy lại để THẢO LUẬN/REFINE — KHÔNG advance
/design-end                               (DESIGN→PLAN) Đóng design khi vừa ý. Gate design_gate: ADR≥3 + INTEG≥1 + per-boundary completeness (backend/bff→hld+api, web/mobile→hld+ux). KHÔNG spawn author mới
/plan                                     (PLAN→REVIEW) Spawn program-planner (implementation-plan): WAVE-SEQUENCE+wave-{N}+MATRIX+KG. Gate: plan_gate + plan_integrity (FEAT-id có file + depends_on no-cycle) + matrix_coherence (phủ đủ boundary đúng kind)

# Core flow (review→wave)
/review-document ["<feedback>"] [--file X] (REVIEW) 2 mode: CÓ arg = revision (sửa doc theo comment user, lặp tới OK); KHÔNG arg = sanity-check (soi gap/mâu-thuẫn/thiếu-độ-phủ năng-lực → ghi tracking/doc-review-findings.md DR-NNN; bắt thiếu auth/login trước build)
/approve-document                         (REVIEW) User mark doc OK (approved=true). KHÔNG đổi state. Gate doc_review: sanity-check phải đã chạy + no open BLOCKER/MAJOR gap. Cho phép /start-wave
/start-wave <N>                           (REVIEW→WAVE_OPEN) Mở wave, materialize boundaries + agents + KG (gate: approved=true)
/start-dev <boundary>                     Vào DEV, spawn dev sub-agent boundary (auto detect kind)
/review-dev                               Review cả wave. Review ghi findings; MAIN spawn fix Mode B → re-review tới open_findings==0
/dev-handoff                              Gate all_boundaries_reviewed (mọi wave_boundary review pass + coverage theo kind BE80/BFF70/web|mobile60) → TEST_PLAN
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
- `PreToolUse(Bash)` hook check `harness <X> complete`: allowed_commands (theo STATE-MACHINE) + gate (gates.py). Gate single-repo nổi bật: `design_gate` = ADR≥3 + INTEG≥1 + **per-boundary completeness** (backend/bff→hld+api, web/mobile→hld+ux) ở `/design-end`; `/plan` = `plan_gate` + `plan_integrity` (FEAT-id trong MATRIX có file + `depends_on` no-cycle/no-dangling) + `matrix_coherence` (MATRIX phủ đủ boundary BOUNDARY-MAP đúng kind); `planning_lint` thêm **ref-integrity** epic↔feat↔BR↔journey↔persona — persona-ref dùng **file-id `PERSONA-{prefix}-NNN`** (file-backed, không dùng P-id pool). `/approve-document` = `doc_review` (sanity-check `/review-document` **no-arg** phải đã chạy ghi `tracking/doc-review-findings.md` + KHÔNG còn gap BLOCKER/MAJOR open — bắt **thiếu năng lực nền vd auth/login** + mâu thuẫn + thiếu-độ-phủ TRƯỚC khi build; mirror `review-dev no_open_findings` cho TÀI LIỆU). **Back-half content-gate (chống tự-khai, e2e-driven):** `/dev-handoff` = `infra_proof` (docker-ps.json: mọi wave service `State=running`) + `health_proof` (health-proof.json do `capture_infra_proof.py` HARNESS curl `/health/ready` → mọi service 2xx; State=running chưa đủ) + `code_compliance` (backend: cấm H2/`com.h2database`/`jdbc:h2`/`ddl-auto: create-drop`, bắt Dockerfile + base `application.yml` + **≥1 profile file `application-<env>.yml`** theo ref-backend-config — G11) + `web_styling` (FE unstyled + G15: plain-CSS phải dùng design token `var(--...)` từ `ux/design-tokens.css`); `/test-plan` = (infra_proof + health_proof) + `contract_test_present` (consumer có depends_on trong wave phải có ≥1 auto-TC contract|integration|e2e — G4/G6); `/test-execute` = `test_evidence` (parse test-report+test-logs+bugs.md: auto-TC in-scope phải có network-call thật `METHOD path -> sts`; skip phải nêu service-down; **FAIL phải có bug reference cột TC** = chống miss-bug, mirror ZIP `lint_execution`; **harness DERIVE `test_result` từ report**, không lấy verbatim agent); `/plan` thêm `api_transport` (api spec KHÔNG truyền tenant-id qua query → header/JWT claim, G6) + `wave_sequence_lint` (WAVE-SEQUENCE §wave-NNN: enum class/strategy + target_count≤3/layer + strategy layer-purity + vertical parent_epic + inherited_active file tồn tại — port ZIP wave-sequence-validate, G16). Deferred-scope (G1): TC `@deferred` khai báo ở `wave-{N}.md §6 Deferred` → test-execute skip → end-wave close sạch không cần ép. Mọi gate force-bypass (`force:true,reason`) ghi audit `decisions.md`. **+ turn-flag (#11): chỉ 1 `harness complete` mỗi user-turn** — complete thứ 2 trong cùng lượt bị deny ("MAIN tự nối lệnh"); gate-fail KHÔNG tiêu cờ (cho retry). Reset ở UserPromptSubmit/SessionStart.
- `PreToolUse(Write|Edit)` hook block edit kernel files (`harness/STATE.json`, `STATE-MACHINE.json`, `SERVICE-BOUNDARY-MATRIX.json`, `.claude/settings.json`) + **phase-lock doc upstream** (`policies.phase_lock_violation`): doc thuộc lớp discovery/domain/design/plan chỉ sửa ở stage sở hữu (+REVIEW); stage khác → block kèm hướng lùi. Port single-repo của ZIP `pretooluse-readonly-inputs.py`. TEMPLATE.*/README + infra/KG/tracking/services miễn (riêng services/ bị chặn khi `spawn.active=dev-handoff-agent` — #12). **#12 dev-handoff infra-only:** `_pre_task` set `spawn.active=dev-handoff-agent` khi spawn agent đó → `PreToolUse(Write|Edit)` block sửa `services/**` (lỗi code boundary → fix-agent, không dev-handoff tự vá).
- `PreToolUse(Task)` hook KHÔNG block theo stage. Explore agent free. Inject reminder boundary cho dev-spawn + **block spawn MỌI command-agent bằng prompt tự viết tay** (E-6: phải dùng `build_prompt.py` output). Detect 2 nhánh: keyword `DEV_SPAWN_KEYWORDS` (`start-dev`/`fix-bugs`/`review-dev`/`domain-po`/`domain-ba`/`domain-translate`/**`test-plan`/`test-execute`**) HOẶC tên-agent registry (`agents/*-agent.md`). Prompt thiếu chữ ký `# SPAWN PROMPT`/`STATE BUNDLE` = block (`MAIN KHÔNG tự build prompt`).
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

| Date | CR/ADR | Summary |
|---|---|---|
| 2026-05-29 | — | Initial CLAUDE.md (router style v4 rebuild) — polyrepo, 10 states, 13 commands |
| 2026-06-13 | — | Clone DISCOVERY (D0-D3 ideation) từ ADLC: +4 state `DISC_D0..D3`, +2 command `/discovery-start`,`/discovery-end`, +gate `discovery_gate.py`, +docs/discovery/*. |
| 2026-06-13 | — | Tách intake hoàn toàn (bỏ `/intake-requirement`), khớp cách chia nhỏ của ADLC: front-half = DISCOVERY(D0-D3) → DOMAIN_AUTHORING → DESIGN → PLAN → REVIEW (rename từ INTAKE). DOMAIN author Epic/Feature/BR **thẳng vào `docs/architecture/{epics,feat,business-rules}`** (1 stage, no translate/sync/docs-domain — đó là plumbing multi-repo); skill domain-po (EPIC/FEATURE) + domain-ba (BR) + agent; template ZIP. DESIGN=`/design` (technical-design), PLAN=`/plan` (implementation-plan) tách stage riêng, gate force-capable (design_gate/plan_gate). MATRIX materialize ở PLAN (ALLOW_STAGES). apply-cr → DESIGN. |
| 2026-06-13 | — | **Audit sync ADLC→harness (fix drift)**: sửa số liệu IDENTITY (10→17 states, 14→19 commands); cập nhật tham chiếu chết (intake step3/4, `/intake-requirement`) → DESIGN / Discovery D3; bổ sung mode `JOURNEY`+`PERSONA` vào chữ ký `/domain-start` ở CLAUDE.md + đồng bộ `commands/domain-start.md` (frontmatter, bước 1&5, dòng cuối); bỏ `WIREFRAME` (mode đã xoá) và `DOMAIN_TRANSLATING`/`TRANSLATE` (plumbing multi-repo đã bỏ) trong message "Sau D3" của `build_prompt.py`. |
| 2026-06-13 | — | **Quyết định: KHÔNG clone các tính năng ADLC sau** (single-repo nên không cần / hoãn): SPECS hub + translate/sync + ORCHESTRATOR UI + repo UIUX/BOUNDARIES/EXPERIENCES tách rời (đã bỏ có chủ đích từ đầu). **Hoãn (gap đã nhận diện, chưa làm)**: (1) state `BLOCKED` + `/blocker-raise`/`/blocker-resolve` (escape hatch khi agent kẹt); (2) design-system/design-tokens/component-library dùng chung (hiện chỉ UX per-boundary qua `ux-design`); (3) `/cr-raise` giữa luồng (hiện chỉ `/apply-cr` từ DONE); (4) `/import-baseline` brownfield Wave 0; (5) qa-translator re-map TC khi AC đổi + dedupe-registry; (6) governance util `/decision-log`,`/memory-audit`,`/reset-question-budget`,`/scope-extend`; (7) doc tổng quan system-level (SYSTEM-ARCHITECTURE/SYSTEM-TOPOLOGY/CONTRACT-MAP) — hiện rải ở HLD per-boundary + BOUNDARY-MAP. Cân nhắc bổ sung khi có nhu cầu thực tế. |
| 2026-06-14 | — | **DESIGN tách self-loop + `/design-end`** (19→20 command): `/design` giờ `DESIGN→DESIGN` (thảo luận/refine, KHÔNG advance), `/design-end` `DESIGN→PLAN` (verify gate, không spawn author mới); per-role docs-to-read tối ưu. **3 gate single-repo** chắt lọc ZIP per-target MANIFEST: `design_gate` per-boundary completeness (backend/bff→hld+api, web/mobile→hld+ux), `plan_integrity` (FEAT-id MATRIX có file + depends_on no-cycle/no-dangling), `matrix_coherence` (MATRIX phủ đủ boundary đúng kind) + `planning_lint` ref-integrity mở rộng journey/persona, persona-ref chuẩn-hoá file-id `PERSONA-{prefix}-NNN` (bỏ P-id pool). **23 template** chuẩn-hoá theo ZIP rồi trim lean. |
| 2026-06-14 | — | **`apply-cr` re-enter `DOMAIN_AUTHORING`** (was DESIGN) — vá gap mở-rộng-feature-sau-ship: CR thêm feature → `/domain-start` author epic/feat/BR rồi chảy DOMAIN→DESIGN→PLAN→REVIEW→start-wave; CR kiến trúc-only → `/domain-end` qua thẳng. Boundary MỚI vẫn dùng done-wave→`/discovery-start D3` (discovery re-runnable idempotent vì done-wave giữ docs). smoke +1 step (apply-cr→DOMAIN). |
| 2026-06-14 | backlog G12+G13+G1 | **Back-half honest-gate (rút từ e2e ClinicBook — META "giàu spec nghèo enforcement máy"):** (G13) `scripts/capture_infra_proof.py` HARNESS tự curl `/health/ready` → `health-proof.json` + gate `health_proof` @dev-handoff/test-plan (State=running chưa đủ; app phải trả 2xx); (G12) gate `test_evidence` @test-execute parse test-report+test-logs (auto-TC in-scope phải có network-call thật, cấm silent-skip) + **DERIVE `test_result`** từ report (không tin agent tự khai); (G1) deferred-scope: `wave-{N}.md §6 Deferred` là SoT → test-plan tag `@deferred` → test-execute skip(deferred) không log bug → `/end-wave` close sạch tự nhiên, hết ép `test_result=pass`. Tag không khai báo wave plan → coi in-scope (chống né test). Gate selftest hermetic + smoke 30/30. |
| 2026-06-16 | nhận-xét #2+#3+#9 | **DOMAIN 2-lớp business↔eng + KÝ + TRANSLATE (clone ZIP, adapt single-repo) + E-6 chặt.** (A1) lớp BUSINESS plain VN `docs/domain/{epics,feat,journeys,business-rules,personas}` (template clone ZIP, có "Câu hỏi cho Author") — `/domain-po`(EPIC/FEATURE/JOURNEY) + `/domain-ba`(BR/PERSONA) author (loop tới khi OK + hỏi-author-questions ngay, status DRAFT). (#3) `/domain-approve <id|all>` KÝ (`status: APPROVED`, ký TRƯỚC dịch SAU) — `domain_approve.py` jargon-check + stamp; gate `domain_no_jargon`. (#2) `/domain-translate` spawn `domain-translator` (clone ZIP agent: DỊCH-KHÔNG-sáng-tác, field kỹ thuật = TODO-engineer) dịch `docs/domain/`→`docs/architecture/` eng; gate `domain_signed` (mọi doc ký). Bỏ SPECS-hub/cross-repo-sync. command 20→23 (bỏ `domain-start`, +`domain-po`/`-ba`/`-approve`/`-translate`); back-edge DESIGN→DOMAIN qua po/ba; phase-lock +`docs/domain/`. (#9/E-6) hook chặn spawn tự-viết-tay MỌI workflow agent: detect theo **registry tên-agent** (`agents/*.md`) + keyword → thiếu chữ ký build_prompt = block. gates+policies selftest + smoke 35/35 + state validate + parity xanh. |
| 2026-06-16 | nhận-xét #1 | **Discovery: gộp cơ chế start D0→Dn + complete-before-spawn.** `/discovery-start` giờ TIẾN qua wave (nhảy tiến `D{N}→D{N+1}` = gate wave hiện tại qua `discovery_advance`; gọi lại cùng wave = refine, no gate); bỏ 3 transition `discovery-end` tiến-wave, `/discovery-end` chỉ còn 1 (DISC_D3→DOMAIN, không arg). **complete-before-spawn**: command transition STATE NGAY (trước build_prompt+spawn) → STATE đúng stage để phase-lock cho agent ghi `docs/discovery/**` + next-step/Stop-hook đúng (giống `/start-dev`). `find_transition` thành **evidence-aware** (phân biệt refine vs advance cùng `(from,trigger)`). gates selftest + smoke **32/32** + state validate + parity xanh. |
| 2026-06-16 | nhận-xét #6+#7+#8+#10+#11+#12+#13+#14 | **Batch dev-quality + flow-control (từ chạy thật tới test-execute):** (#6) entity Java → `{Resource}Entity` + folder `entities/` (rules-backend + ref-backend-pattern). (#7) **Gradle default** mọi backend (`build.gradle` Groovy DSL; Maven opt-in qua ADR) — rules/ref/review/template + dispatcher `_build_test_cmd` Gradle-first. (#8) review-backend §L2 ép check tuân-thủ `rules-backend` + ref-skill (cấm **FQCN** inline — phải import) + §N schema-drift (entity↔migration qua Testcontainers `ddl-auto:validate`). (#10) `/review-dev complete{}` ép `review_results` (gate `non_empty`) chống STATE rỗng kẹt dev-handoff; `all_boundaries_reviewed` thêm force-bypass. (#11) **turn-flag**: 1 `harness complete`/user-turn (marker `harness/.turn-advance.flag`, reset UserPromptSubmit/SessionStart) — complete thứ 2 deny "MAIN tự nối lệnh"; gate-fail KHÔNG tiêu cờ. (#12) dev-handoff **INFRA-ONLY**: `_pre_task` set `spawn.active=dev-handoff-agent` → `PreToolUse(Write\|Edit)` block `services/**` (FM-HANDOFF-NO-CODE-FIX) — lỗi code boundary → fix-agent, không tự vá. (#13) test-plan + test-execute trỏ template `tracking/_templates/TEMPLATE.test-case-registry.md`. (#14) test-execute SEED test-data (cột `test-data`/`pre-condition` đủ cụ thể) trước chạy + cleanup. gates+policies selftest + smoke 35/35 + parity. |
| 2026-06-21 | service-lifecycle wave | **End-wave TẮT service + handoff reuse rõ ràng.** (1) `/end-wave` thêm `docker compose stop` (dừng container, GIỮ image+volume) — UAT đã xong ở MANUAL_TEST (handoff §5 sửa nhãn "sau end-wave"→"ở MANUAL_TEST trước end-wave") nên không cần service chạy; trước đây giữ UP "post-mortem" (lý do yếu). KHÔNG `down --volumes` (vẫn là việc `/done-wave`). build_end_wave + end-wave-agent (+skill infra-local-dev, +`infra_stopped`) + command + handoff §8. (2) Handoff wave kế **tái dùng** service wave trước: `docker compose up -d --build` idempotent — image+volume từ `end-wave stop` giữ nguyên → khởi động NHANH, chỉ boundary mới/đổi mới build; KHÔNG `down` trước (ghi rõ ở build_dev_handoff). smoke 35/35 + selftest + parity. |
| 2026-06-21 | turn-flag auto-mode hole | **Vá MAIN tự nối slash-command ở auto mode.** Lỗ hổng: turn-flag (#11) reset ở `UserPromptSubmit`; khi MAIN TỰ invoke slash-command kế (Skill/SlashCommand tool) để chạy `/test-plan`/`/test-execute`… → fire lại `UserPromptSubmit` → xoá cờ → `harness complete` kế lọt → nối trọn pipeline (auto mode không có ma sát phê duyệt). Fix: thêm `PreToolUse(Skill\|SlashCommand)` hook (`dispatcher._pre_skill`) chặn MAIN gọi tool chạy lệnh ∈ `GATE_RULES` (deny tại NGUỒN, trước khi slash-command reset cờ); lệnh user GÕ tay pre-loaded → không qua tool → không ảnh hưởng; skill ngoài-harness cho qua. +matcher `Skill\|SlashCommand` ở `.claude/settings.json`. dispatcher selftest + gates/policies selftest + smoke 35/35 + parity. |
| 2026-06-21 | backend-lombok-consistency | **Vá mâu thuẫn ref backend ↔ hub (dev+review hiểu sai `@RequiredArgsConstructor`/`@Slf4j`):** `rules-backend` (hub) ĐÚNG bắt `@RequiredArgsConstructor` + `@Slf4j`, nhưng VÍ DỤ CODE ở ref skills lại viết NGƯỢC (constructor tay `Impl(...){this.x=x;}` + `LoggerFactory.getLogger(...)` thủ công) → dev copy ref → sai, review không có mục bắt → lọt. Sửa ví dụ cho khớp hub ở `ref-backend-pattern` (service), `ref-backend-logging` (`@Slf4j`, bỏ LoggerFactory), `ref-backend-redis` (RedisServiceImpl), `ref-backend-kafka` (4 bean: publisher/command-service/relay/consumer); thêm forbidden `LoggerFactory.getLogger` thủ công. `review-backend §L2` thêm mục bắt **DI manual-constructor/`@Autowired`-field + manual-LoggerFactory = MAJOR**. Constructor tay hợp lệ giữ nguyên (enum `OrderErrorCode`, exception `BusinessException`); component stateless (interceptor/mapper) không cần annotation. |
| 2026-06-21 | E-6 test-spawn | **E-6 keyword phủ test-plan/test-execute (vá MAIN tự build prompt spawn test).** `DEV_SPAWN_KEYWORDS` += `test-plan`, `test-execute` → `PreToolUse(Task)` block spawn 2 agent này bằng prompt tự-viết-tay (trước đây chỉ nhánh tên-agent `test-*-agent` chặn → MAIN né bằng cách không nhắc tên agent). build_prompt output (`# SPAWN PROMPT`) vẫn pass; space-form "test plan" KHÔNG false-positive. policies selftest + smoke 35/35 + parity. |
| 2026-06-16 | nhận-xét #15 | **Gate `doc_review` @ `/approve-document` — doc-review 2 mode.** `/review-document` **CÓ arg** = revision (sửa theo comment user, vòng đã có); **KHÔNG arg** = sanity-check soi 5 lens (độ-phủ năng-lực `capability-map`+persona+journey→FEAT; mâu-thuẫn cross-doc; AC testable; cross-ref; câu-hỏi-author chưa chốt) → ghi `tracking/doc-review-findings.md` (`DR-NNN` + severity, template `tracking/_templates/`). Gate `check_doc_review`: thiếu file (chưa chạy sanity-check) HOẶC còn gap **BLOCKER/MAJOR** open → **chặn approve** (mirror `review-dev no_open_findings` cho TÀI LIỆU; bắt **thiếu năng lực nền vd auth/login** trước build). Lens đặt ở build_prompt + `review-document-agent` (KHÔNG đụng skill `business-analysis`). force-bypass+audit `decisions.md`. gates selftest +doc_review hermetic + smoke 35/35 + parity. |
| 2026-06-14 | — | **Doc phase-lock + back-edges + next-step hint (vá 2 gap user: hook hổng + báo-bước-tiếp mơ hồ):** (#2) port ZIP `pretooluse-readonly-inputs.py` sang single-repo = `policies.phase_lock_violation` ở `PreToolUse(Write|Edit)` — doc discovery/domain/design/plan chỉ sửa ở stage sở hữu (+REVIEW), stage sau frozen (NON-NEGOTIABLE #6 từ honor-system → hook-enforced; chống dev/test sửa spec khớp code + sửa FEAT/HLD lúc ở PLAN). Sửa upstream = **back-edge** `PLAN--/design-->DESIGN`, `DESIGN--/domain-start-->DOMAIN` (dùng lại lệnh entry, không command mới → parity giữ; tiến lại re-gate) hoặc `/apply-cr` sau ship. (#1) next-step hint contextual (`policies.STAGE_NEXT_GUIDE`: lệnh+arg+nghĩa+back-edge) thay list tên trống. policies selftest + smoke 32/32 (+2 back-edge) + state validate + parity. ZIP translate (plain↔eng DOMAIN→SPECS) giữ nguyên BỎ (single-repo author thẳng). |
| 2026-06-14 | backlog G15-now | **UI design-fidelity deterministic (e2e obs #6, Figma defer):** artifact dùng chung `docs/architecture/ux/design-tokens.css` (SoT `--color-*`/`--font-*`/`--space-*` + dark/hc theme, `TEMPLATE.design-tokens.css`) — mọi web boundary consume, không bịa palette per-boundary; nâng gate `web_styling`: web style bằng plain CSS phải dùng design token `var(--...)` (tailwind/CSS-in-JS miễn) → chống "FE bịa màu/spacing rời design system". Skill ux-design + rules-web (rule 44) trỏ shared token. G15-future (Figma design-to-code + visual diff) DEFER. |
| 2026-06-14 | backlog G16 | **Wave-sequence validator (e2e obs #7 + #5 verify):** port `scripts/wave_sequence_lint.py` từ ZIP `wave-sequence-validate.py` (single-repo: bỏ contract-signing, `inherited_active`→file-exists) → gate `wave_sequence_lint` @plan: enum `wave_class`/`wave_strategy` + `target_count_per_layer ≤ 3` + strategy layer-purity (horizontal-be/-fe) + vertical `parent_epic` + `inherited_active` file tồn tại. Field §2 WAVE-SEQUENCE từ "trang trí" → được gate; bỏ chữ "chưa gate"/"forward-looking" ở template + implementation-plan SKILL. Selftest hermetic (module + wiring) + smoke 30/30 + parity. **+ #5 verify doc-contract:** thêm invariant ZIP `lint_execution` "FAIL phải log bug" vào `test_evidence`; deferred SoT 1 nguồn (handoff §6 → wave §6). |
| 2026-06-14 | backlog G11+G4/G6 | **Dev-quality + integration-realism gate (e2e obs #1,#2):** (G11) gate `code_compliance` @dev-handoff — backend boundary cấm H2 (`com.h2database`/`jdbc:h2`/`ddl-auto: create-drop`) + bắt `Dockerfile` + `application.{yml,properties}` (đối xứng `web_styling`, chặn "test xanh nhờ H2" + "dev-done ≠ runnable"); (G4/G6-A) gate `contract_test_present` @test-plan — consumer (có `depends_on` trong wave) phải có ≥1 auto-TC contract/integration/e2e nối tới (chống thiếu liên kết BE-FE → bug); (G6-B) gate `api_transport` @plan — api spec KHÔNG truyền tenant-id qua query string (phải `X-Tenant-ID` header/JWT claim, api template §2 — chống drift BUG-012). Tất cả force-bypass+audit; selftest hermetic + smoke 30/30. |

