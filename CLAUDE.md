# ADLC Design Harness — CLAUDE.md

> **Router file.** Đọc top-to-bottom mỗi session. Tier-A only — chi tiết → routing table.

---

## NON-NEGOTIABLES

1. **Đọc `harness/STATE.json` trước mọi tool call** (hoặc xem header `[HARNESS ...]` đã được hook `UserPromptSubmit` inject).
2. **Edit chỉ trong `owned_paths`** của `active_boundary`. PreToolUse hook block; đừng cố lách.
3. **Stage transition CHỈ qua slash command** (`/start-wave`, `/dev-handoff`, `/end-wave`, …). KHÔNG sửa `stage` trong STATE.json bằng tay.
4. **Quyết định non-trivial → artifact ngay** (ADR / FEAT / CR / KG). Không để chỉ tồn tại trong chat.
5. **Cross-boundary change** phải qua `/apply-cr` + `/review-document` approve trước khi code.
6. **Không bypass test** (`--no-verify`, skip), không hardcode secrets. **Doc upstream PHASE-LOCKED** (hook enforce, không còn honor-system): mỗi lớp doc chỉ sửa được ở stage SỞ HỮU + REVIEW — discovery/PROJECT→DISC_*, epic/feat/journey/BR/persona→DOMAIN, adr/hld/api/data-model/ux/events/integrations→DESIGN, plans→PLAN. Muốn sửa khi đã qua stage → **LÙI** về stage sở hữu (`/design` từ PLAN, `/domain-start <mode>` từ DESIGN) rồi tiến lại (re-gate); sau ship → `/apply-cr`. (TEMPLATE.*/README + infra/KG/tracking/services KHÔNG khoá.)

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
| Scale | 17 states · 20 commands · N waves · M boundaries (boundary/wave set dynamic ở PLAN qua `/plan`) |
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
| (ZIP `-DOMAIN` repo: FEAT/EP/BR/journey/persona) | `DOMAIN_AUTHORING` | clone (author thẳng `docs/architecture/`) |
| **D3.5** standards-enrich · **D4** contracts · **D5** full CHARTER | `DESIGN` (`/design`) | **gộp** → ADR (stack) + HLD (=D5) + API/events/integrations (=D4); D3.5 coding-standard = skill `rules-{kind}`+`ref-{kind}-pattern` (cụ thể sẵn, không cần enrich) |
| **D7** WAVE-SEQUENCE | `PLAN` (`/plan`) | move → WAVE-SEQUENCE + wave-*.md + MATRIX |
| DISCOVERED + sync-to-specs | `REVIEW` | replace → approve → `/start-wave` |

**Bỏ có chủ đích (multi-repo plumbing, single-repo không cần):** contract-signing/hash-drift (D4), `_shared/*` placeholder-enrich layer (D3.5), `/sync-to-specs`/SPECS hub, SYSTEM-TOPOLOGY/CONTRACT-MAP tách rời, multi-role Authority sign-off, BLOCKED state. **FEAT KHÔNG sinh ở Discovery** (cả ZIP lẫn harness — DOMAIN sở hữu).

**Flow stage (17 state):** `BOOTSTRAP → DISC_D0 → DISC_D1 → DISC_D2 → DISC_D3 → DOMAIN_AUTHORING → DESIGN ↺ → PLAN → REVIEW → WAVE_OPEN → DEV → REVIEW_DEV → DEV_HANDOFF → TEST_PLAN → TEST_EXECUTE → MANUAL_TEST → DONE`. `DESIGN` self-loop (`/design` refine, `/design-end` advance). **Back-edge (lùi sửa doc phase-locked):** `PLAN --/design--> DESIGN`, `DESIGN --/domain-start--> DOMAIN_AUTHORING` (dùng lại lệnh entry, không command mới; tiến lại re-gate). `apply-cr`: `DONE → DOMAIN_AUTHORING` (CR feature mới author epic/feat/BR; CR kiến trúc-only → `/domain-end` qua thẳng → DESIGN). `done-wave`: `DONE → BOOTSTRAP` (docs giữ; discovery re-runnable idempotent cho increment kế). Boundary MỚI → done-wave→`/discovery-start D3`.

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
| "Epic / Feature / Business-rule?" | `docs/architecture/{epics/EP-*,feat/FEAT-*,business-rules/BR-*}.md` (DOMAIN author) |
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
/discovery-start <D0|D1|D2|D3>            Vào/ở 1 wave + spawn agent: D0 hypothesis-log · D1 capability+persona · D2 event-storming · D3 charter + derive PROJECT.md + chốt prefix (KHÔNG sinh FEAT)
/discovery-end <D0|D1|D2|D3>              Verify exit gate (discovery_gate.py) → wave kế. D3 → DOMAIN_AUTHORING. Override: force+reason ghi decisions.md

# Domain (2) — clone ADLC DOMAIN: author product chia nhỏ Epic/Feature/BR THẲNG vào docs/architecture/ (single-repo, no translate)
/domain-start <EPIC|FEATURE|JOURNEY|BR|PERSONA>  Spawn agent: po (EPIC/FEATURE/JOURNEY) · ba (BR/PERSONA) → docs/architecture/{epics,feat,journeys,business-rules,personas}. Self-loop author thêm
/domain-end                               Verify gate (≥1 epic + ≥1 feat + ≥1 BR) → DESIGN. Override: force+reason ghi decisions.md

# Design + Plan (3) — tách từ intake cũ, stage riêng
/design                                   (DESIGN→DESIGN, self-loop) Spawn solution-architect (technical-design): ADR/HLD/API/data-model/UX/events/integrations. Chạy lại để THẢO LUẬN/REFINE — KHÔNG advance
/design-end                               (DESIGN→PLAN) Đóng design khi vừa ý. Gate design_gate: ADR≥3 + INTEG≥1 + per-boundary completeness (backend/bff→hld+api, web/mobile→hld+ux). KHÔNG spawn author mới
/plan                                     (PLAN→REVIEW) Spawn program-planner (implementation-plan): WAVE-SEQUENCE+wave-{N}+MATRIX+KG. Gate: plan_gate + plan_integrity (FEAT-id có file + depends_on no-cycle) + matrix_coherence (phủ đủ boundary đúng kind)

# Core flow (review→wave)
/review-document "<feedback>" [--file X]  (REVIEW) Revision loop. User feed feedback, agent revise doc. Lặp đến khi user OK
/approve-document                         (REVIEW) User mark doc OK (approved=true). KHÔNG đổi state. Cho phép /start-wave
/start-wave <N>                           (REVIEW→WAVE_OPEN) Mở wave, materialize boundaries + agents + KG (gate: approved=true)
/start-dev <boundary>                     Vào DEV, spawn dev sub-agent boundary (auto detect kind)
/review-dev                               Review cả wave. Review ghi findings; MAIN spawn fix Mode B → re-review tới open_findings==0
/dev-handoff                              Gate all_boundaries_reviewed (mọi wave_boundary review pass + coverage theo kind BE80/BFF70/web|mobile60) → TEST_PLAN
/test-plan                                Sinh test-case-registry.md
/test-execute                             Build local + run auto test + log bug (origin=auto). KHÔNG fix. Auto-transition MANUAL_TEST (pass/fail); bug fix qua /fix-bugs
/end-wave                                 Soft close, infra UP → DONE (gate: UAT signed + test_result=pass + no_open_bugs)
/done-wave                                Hard close, teardown → BOOTSTRAP

# Branch (2)
/log-bug "<mô tả>"                        Ghi 1 bug manual (UAT) vào bugs.md (spawn log-bug-agent, origin=manual). Chỉ ghi, không fix
/fix-bugs [<bug-id>]                       Fix bug (Mode A). Không arg = sweep mọi bug open; có bug-id = fix 1 cái. MAIN spawn fix → re-run TC verify → close

# Side (1)
/apply-cr <CR-ID>                         (DONE→DOMAIN_AUTHORING) Change request re-enter DOMAIN: CR feature → /domain-start author epic/feat/BR; CR kiến trúc-only → /domain-end thẳng. Re-flow → /design → /design-end → /plan → REVIEW → /start-wave
```

Mỗi command tự document trong `.claude/commands/<name>.md` (sync từ `commands/<name>.md` qua `py scripts/sync_commands.py`).

---

## RUNTIME GUARANTEES (do hooks cung cấp)

- `SessionStart` hook in STATE summary (brief: stage/wave/boundary/last_completed/allowed_next). Non-negotiables inject vào spawn prompt sub-agent (build_prompt), KHÔNG ở SessionStart hook.
- `UserPromptSubmit` hook inject `[HARNESS stage={stage} wave={wave} boundary={b} | next: {gợi-ý-chính-xác}]` mỗi turn — `next` là **bước tiếp contextual** (lệnh + arg + nghĩa + back-edge), không phải list tên trống (policies.STAGE_NEXT_GUIDE). SessionStart brief cũng dùng.
- `PreToolUse(Bash)` hook check `harness <X> complete`: allowed_commands (theo STATE-MACHINE) + gate (gates.py). Gate single-repo nổi bật: `design_gate` = ADR≥3 + INTEG≥1 + **per-boundary completeness** (backend/bff→hld+api, web/mobile→hld+ux) ở `/design-end`; `/plan` = `plan_gate` + `plan_integrity` (FEAT-id trong MATRIX có file + `depends_on` no-cycle/no-dangling) + `matrix_coherence` (MATRIX phủ đủ boundary BOUNDARY-MAP đúng kind); `planning_lint` thêm **ref-integrity** epic↔feat↔BR↔journey↔persona — persona-ref dùng **file-id `PERSONA-{prefix}-NNN`** (file-backed, không dùng P-id pool). **Back-half content-gate (chống tự-khai, e2e-driven):** `/dev-handoff` = `infra_proof` (docker-ps.json: mọi wave service `State=running`) + `health_proof` (health-proof.json do `capture_infra_proof.py` HARNESS curl `/health/ready` → mọi service 2xx; State=running chưa đủ) + `code_compliance` (backend: cấm H2/`com.h2database`/`jdbc:h2`/`ddl-auto: create-drop`, bắt Dockerfile+config — G11) + `web_styling` (FE unstyled + G15: plain-CSS phải dùng design token `var(--...)` từ `ux/design-tokens.css`); `/test-plan` = (infra_proof + health_proof) + `contract_test_present` (consumer có depends_on trong wave phải có ≥1 auto-TC contract|integration|e2e — G4/G6); `/test-execute` = `test_evidence` (parse test-report+test-logs+bugs.md: auto-TC in-scope phải có network-call thật `METHOD path -> sts`; skip phải nêu service-down; **FAIL phải có bug reference cột TC** = chống miss-bug, mirror ZIP `lint_execution`; **harness DERIVE `test_result` từ report**, không lấy verbatim agent); `/plan` thêm `api_transport` (api spec KHÔNG truyền tenant-id qua query → header/JWT claim, G6) + `wave_sequence_lint` (WAVE-SEQUENCE §wave-NNN: enum class/strategy + target_count≤3/layer + strategy layer-purity + vertical parent_epic + inherited_active file tồn tại — port ZIP wave-sequence-validate, G16). Deferred-scope (G1): TC `@deferred` khai báo ở `wave-{N}.md §6 Deferred` → test-execute skip → end-wave close sạch không cần ép. Mọi gate force-bypass (`force:true,reason`) ghi audit `decisions.md`.
- `PreToolUse(Write|Edit)` hook block edit kernel files (`harness/STATE.json`, `STATE-MACHINE.json`, `SERVICE-BOUNDARY-MATRIX.json`, `.claude/settings.json`) + **phase-lock doc upstream** (`policies.phase_lock_violation`): doc thuộc lớp discovery/domain/design/plan chỉ sửa ở stage sở hữu (+REVIEW); stage khác → block kèm hướng lùi. Port single-repo của ZIP `pretooluse-readonly-inputs.py`. TEMPLATE.*/README + infra/KG/tracking/services miễn.
- `PreToolUse(Task)` hook KHÔNG block theo stage. Explore agent free. Inject reminder boundary cho dev-spawn + block spawn dev/fix/review bằng prompt tự viết tay (E-6: phải dùng `build_prompt.py` output).
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
| 2026-06-14 | — | **Doc phase-lock + back-edges + next-step hint (vá 2 gap user: hook hổng + báo-bước-tiếp mơ hồ):** (#2) port ZIP `pretooluse-readonly-inputs.py` sang single-repo = `policies.phase_lock_violation` ở `PreToolUse(Write|Edit)` — doc discovery/domain/design/plan chỉ sửa ở stage sở hữu (+REVIEW), stage sau frozen (NON-NEGOTIABLE #6 từ honor-system → hook-enforced; chống dev/test sửa spec khớp code + sửa FEAT/HLD lúc ở PLAN). Sửa upstream = **back-edge** `PLAN--/design-->DESIGN`, `DESIGN--/domain-start-->DOMAIN` (dùng lại lệnh entry, không command mới → parity giữ; tiến lại re-gate) hoặc `/apply-cr` sau ship. (#1) next-step hint contextual (`policies.STAGE_NEXT_GUIDE`: lệnh+arg+nghĩa+back-edge) thay list tên trống. policies selftest + smoke 32/32 (+2 back-edge) + state validate + parity. ZIP translate (plain↔eng DOMAIN→SPECS) giữ nguyên BỎ (single-repo author thẳng). |
| 2026-06-14 | backlog G15-now | **UI design-fidelity deterministic (e2e obs #6, Figma defer):** artifact dùng chung `docs/architecture/ux/design-tokens.css` (SoT `--color-*`/`--font-*`/`--space-*` + dark/hc theme, `TEMPLATE.design-tokens.css`) — mọi web boundary consume, không bịa palette per-boundary; nâng gate `web_styling`: web style bằng plain CSS phải dùng design token `var(--...)` (tailwind/CSS-in-JS miễn) → chống "FE bịa màu/spacing rời design system". Skill ux-design + rules-web (rule 44) trỏ shared token. G15-future (Figma design-to-code + visual diff) DEFER. |
| 2026-06-14 | backlog G16 | **Wave-sequence validator (e2e obs #7 + #5 verify):** port `scripts/wave_sequence_lint.py` từ ZIP `wave-sequence-validate.py` (single-repo: bỏ contract-signing, `inherited_active`→file-exists) → gate `wave_sequence_lint` @plan: enum `wave_class`/`wave_strategy` + `target_count_per_layer ≤ 3` + strategy layer-purity (horizontal-be/-fe) + vertical `parent_epic` + `inherited_active` file tồn tại. Field §2 WAVE-SEQUENCE từ "trang trí" → được gate; bỏ chữ "chưa gate"/"forward-looking" ở template + implementation-plan SKILL. Selftest hermetic (module + wiring) + smoke 30/30 + parity. **+ #5 verify doc-contract:** thêm invariant ZIP `lint_execution` "FAIL phải log bug" vào `test_evidence`; deferred SoT 1 nguồn (handoff §6 → wave §6). |
| 2026-06-14 | backlog G11+G4/G6 | **Dev-quality + integration-realism gate (e2e obs #1,#2):** (G11) gate `code_compliance` @dev-handoff — backend boundary cấm H2 (`com.h2database`/`jdbc:h2`/`ddl-auto: create-drop`) + bắt `Dockerfile` + `application.{yml,properties}` (đối xứng `web_styling`, chặn "test xanh nhờ H2" + "dev-done ≠ runnable"); (G4/G6-A) gate `contract_test_present` @test-plan — consumer (có `depends_on` trong wave) phải có ≥1 auto-TC contract/integration/e2e nối tới (chống thiếu liên kết BE-FE → bug); (G6-B) gate `api_transport` @plan — api spec KHÔNG truyền tenant-id qua query string (phải `X-Tenant-ID` header/JWT claim, api template §2 — chống drift BUG-012). Tất cả force-bypass+audit; selftest hermetic + smoke 30/30. |

