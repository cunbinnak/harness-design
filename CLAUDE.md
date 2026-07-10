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
| "Feat nào xong / đang dở (clock-in)?" | `tracking/wave-{N}/feature-state.md` (HARNESS-derive: passing/active/not_started per FEAT; `py scripts/capture_feature_state.py` refresh) |
| "Bug đang open?" | `tracking/wave-{N}/bugs.md` |
| "Skills cho `kind` nào?" | `commands/start-dev.md` § kind_matrix |
| "Skills cho ``kind`` nào ở đâu?" | ``.claude/skills/<skill-name>/SKILL.md`` (auto-load on-demand bởi Claude Code) |
| "Cấu hình local dev (docker-compose)?" | `docs/architecture/infra/docker-compose.yml` |

---

## SLASH COMMANDS

> Xếp theo **thứ tự chạy trong một vòng phát triển** (happy path). Mỗi lệnh chỉ chạy sau khi lệnh trước xong (hook ép). Gate chi tiết → `harness/PROTOCOL.md §Gate evidence`; body lệnh → `.claude/commands/<name>.md`.

| Bước | Lệnh | Tác dụng |
|---|---|---|
| **1. Khám phá** | `/discovery-start <D0\|D1\|D2\|D3>` | Giả thuyết → persona/năng lực → event storming → chốt *boundary* + `PROJECT.md`. Gọi lại = sửa, gọi kế = tiến |
| | `/discovery-end` | Đóng khám phá → sang Domain |
| **2. Yêu cầu** | `/domain-po <EPIC\|FEATURE\|JOURNEY>` | PO ảo viết Epic / Feature / Journey (nghiệp vụ, plain VN), lặp tới khi ưng |
| | `/domain-ba <BR\|PERSONA>` | BA ảo viết Business Rule / Persona |
| | `/domain-approve [<id>]` | Ký duyệt tài liệu nghiệp vụ (bỏ trống = ký tất cả) |
| | `/domain-translate` | Dịch tài liệu đã ký sang bản kỹ thuật (eng) cho kỹ sư |
| | `/domain-end` | Đóng nghiệp vụ → sang Design |
| **3. Thiết kế** | `/design` | Kiến trúc + API + data-model + events + tích hợp (KHÔNG UX). Lặp refine |
| | `/design-ux` | Giao diện từng màn: SCREEN-MAP + mockup HTML + design-token. Chạy SAU `/design` |
| | `/design-end` | Đóng thiết kế → sang Plan |
| **4. Kế hoạch** | `/plan` | Chia *wave*: WAVE-SEQUENCE + kế hoạch wave + MATRIX + knowledge-graph |
| **5. Rà soát** | `/review-document ["<góp ý>"]` | Có góp ý = sửa theo comment; bỏ trống = tự soi lỗ hổng/thiếu sót → ghi findings |
| | `/approve-document` | Duyệt tài liệu OK → mới được mở wave |
| **6. Code** | `/start-wave <N>` | Mở wave N: dựng boundary + agent + KG |
| | `/start-dev <boundary>` | Code 1 boundary (dev ảo tự nhận backend/web/mobile); lần đầu tạo scaffold |
| | `/review-dev` | Rà code cả wave → tự vá tới hết lỗi |
| | `/dev-handoff` | Dựng service **chạy thật** (docker up) + kiểm chứng thật trước khi giao test |
| **7. Test** | `/test-plan` | Sinh danh sách test case (registry) |
| | `/test-execute` | Chạy test tự động trên hệ **đang chạy thật** + ghi bug auto (KHÔNG sửa) |
| | `/log-bug "<mô tả>"` | Ghi 1 bug tìm khi test tay (manual) |
| | `/fix-bugs [<bug-id>]` | Sửa bug (bỏ trống = sửa hết); xong re-test rồi đóng bug |
| **8. Đóng** | `/end-wave` | Đóng mềm: dừng service (giữ image + dữ liệu) khi UAT ký + test pass + hết bug + **mọi feat done** (features_complete: không feat `active`/làm-dở) |
| | `/done-wave` | Đóng cứng: teardown về trạng thái ban đầu, sẵn sàng tính năng kế |
| **Ngoài luồng** | `/apply-cr <CR-ID>` | Đổi/thêm sau khi ship: quay lại Domain rồi chạy lại luồng thiết kế → plan → review → wave |

Mỗi command tự document trong `.claude/commands/<name>.md` (sync từ `commands/<name>.md` qua `py scripts/sync_commands.py`).

---

## RUNTIME GUARANTEES (hooks — chi tiết: `harness/PROTOCOL.md` §Hooks + §Gate evidence)

> Hook đọc từ `gates.py` / `STATE-MACHINE.json` / `policies.py` — **KHÔNG đọc file này**. Bảng dưới chỉ là *awareness* (đủ để biết cái gì sẽ chặn bạn); rule đầy đủ + FM-ID → PROTOCOL.md.

| Hook | Bạn cần biết (chi tiết → PROTOCOL.md) |
|---|---|
| `SessionStart` · `UserPromptSubmit` · `Notification` | Inject header `[HARNESS stage=… \| next: …]` + **reset turn-flag** mỗi turn |
| `PreToolUse(Bash)` — gate | Deny `harness <cmd> complete` nếu sai `allowed_commands` hoặc fail gate — §Gate evidence |
| `PreToolUse(Bash)` — turn-flag (#11) | Chỉ **1** `harness complete`/user-turn (chống MAIN tự nối lệnh); gate-fail KHÔNG tiêu cờ — §Turn-flag |
| `PreToolUse(Write\|Edit)` | Block kernel files + 3 proof file (chỉ `capture_infra_proof.py` sinh, FM-PROOF-FORGE) + doc phase-locked ngoài stage sở hữu + `services/**` khi dev-handoff-agent (#12) |
| `PreToolUse(Task)` | Block spawn command-agent bằng prompt tự viết (E-6: phải dùng `build_prompt.py`); Explore free |
| `PreToolUse(Skill\|SlashCommand)` | Chặn MAIN tự invoke harness slash-command ∈ GATE_RULES; user **gõ tay** không ảnh hưởng |
| `SubagentStop` | Validate RETURN SCHEMA (7 field: completed/deferred/needs_review/files_changed/build/lint/test) |
| `Stop` | Build/lint/test **wave-scoped** khi sửa `services/` ở {DEV, REVIEW_DEV, TEST_EXECUTE}; đỏ → block (cache git-hash) |
| `PreCompact` | Pin STATE (stage+wave+boundary) vào summary |

> Fail-open: hook crash → allow. Mọi gate force-bypass (`force:true,reason`) → audit `tracking/decisions.md`. Config: `.claude/settings.json` · scripts `scripts/hooks/`.

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

> **Tách ra [`HARNESS-CHANGELOG.md`](HARNESS-CHANGELOG.md)** (append-only, cùng thư mục router) — router này chỉ giữ trạng thái HIỆN TẠI. Thay đổi non-trivial → thêm row ở CUỐI file changelog (mới nhất dưới cùng), KHÔNG ghi vào đây.
