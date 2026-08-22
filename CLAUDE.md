# ADLC Design Harness — CLAUDE.md

> **Router file.** Đọc top-to-bottom mỗi session. Tier-A only — chi tiết → routing table.

---

## NON-NEGOTIABLES

1. **Đọc `harness/STATE.json` trước mọi tool call** (hoặc xem header `[HARNESS ...]` đã được hook `UserPromptSubmit` inject).
2. **Edit chỉ trong `owned_paths`** của `active_boundary`. PreToolUse hook block; đừng cố lách.
3. **Stage transition CHỈ qua slash command.** KHÔNG sửa `stage` trong STATE.json bằng tay. Một lệnh được chạy **nhiều** `harness <cmd> complete` (hành lang `/run-wave` gộp 7 chốt) — thứ chặn "đi tiếp khi chưa đủ điều kiện" là **gate của từng chốt**, chạy đủ như cũ. **Chốt nào đỏ → DỪNG ngay tại đó**, báo user thiếu gì, KHÔNG bỏ qua, KHÔNG `force`.
4. **Quyết định non-trivial → artifact ngay** (ADR / FEAT / CR / KG). Không để chỉ tồn tại trong chat.
5. **Cross-boundary change** phải qua chốt rà chéo của `/domain` + `/approve-document` trước khi code. Sau khi wave đã ship: thay đổi = **wave sau**, không sửa tại chỗ.
6. **Không bypass test** (`--no-verify`, skip), không hardcode secrets. **Doc upstream PHASE-LOCKED** (hook enforce, không còn honor-system): mỗi lớp doc chỉ sửa được ở stage SỞ HỮU + REVIEW — discovery/PROJECT→DISC_*, epic/journey/persona→DOMAIN (business thuần), **feat/BR→DOMAIN+DESIGN** (dual-owner: narrative/AC do DOMAIN dịch, field kỹ thuật `enforcement_location`/`consumes_contracts` do DESIGN điền — gate `todo_resolved`), adr/hld/api/data-model/ux/events/integrations→DESIGN, plans→PLAN. Muốn sửa khi đã qua stage → **LÙI** về stage sở hữu (`/domain` gọi được từ DESIGN/PLAN/REVIEW — tự chạy tiếp từ chốt đang đứng) rồi tiến lại (re-gate); sau ship → wave kế. (TEMPLATE.*/README + infra/KG/tracking/services KHÔNG khoá.)

> Vi phạm sẽ bị hook block. Refusal message tham chiếu `harness/PROTOCOL.md` § Failure Modes (FM-ID).

---

## IDENTITY

| Field | Value |
|---|---|
| Project | **ADLC Design Harness** — bộ khung orchestrator cho workflow ADLC (Architecture-Driven Lifecycle), kết hợp agent + người theo chuẩn harness |
| Repo type | **Design repo** — chứa harness kernel + docs + plans + agents + skills + commands + tracking + knowledge-base. KHÔNG chứa code service. |
| Strategy | **Polyrepo** — mỗi boundary scaffolded ở chốt code của `/run-wave` là 1 repo riêng (`{prefix}-{boundary}`). Service repos sống ngoài, link qua `SERVICE-BOUNDARY-MATRIX.json` field `repo_url`. |
| Kernel stack | Python 3.14 (state engine + hooks + materialize + build_prompt) |
| Service stack | Per-boundary, set ở DESIGN (chốt thiết kế của `/domain`, skill `technical-design`). Vd: Java 21 + Spring Boot 3.4, Node.js 22 + Apollo, React 19 + Vite, Flutter 3, … |
| Scale | 17 states · **7 commands** · N waves · M boundaries (boundary/wave set dynamic ở chốt chia-wave của `/domain`) |
| `services/` trong repo này | **gitignored** — chỉ working dir tạm khi sub-agent scaffold (push lên repo riêng, không track ở đây) |

> Khi fork harness này cho project mới: Discovery D3 (`/discover D3`) sẽ derive IDENTITY (project name, prefix, scale) vào `docs/architecture/PROJECT.md` (gộp vai trò aggregate D6 của ADLC).

---

## ADLC MAPPING — phủ ĐỦ D0-D7 (gộp single-repo)

> Harness **phủ 100% intent D0-D7** của ADLC ZIP (multi-repo), nhưng **gộp** 8 ZIP-wave → 4 discovery wave + 3 stage (single-repo không có handoff cross-repo). KHÔNG drop chức năng.

| ZIP wave (multi-repo) | → Harness (gộp) | Cách |
|---|---|---|
| D0 hypothesis | `DISC_D0` | clone |
| D1 persona + capability | `DISC_D1` | clone |
| D2 event-storming | `DISC_D2` | clone |
| D3 boundary + charter + stack-ADR · **D6** aggregate (PRD/ROADMAP/SYS-ARCH/TECHSTACK) | `DISC_D3` → BOUNDARY-MAP + CHARTER + **PROJECT.md** | clone D3 + **fold D6** (stack-ADR move sang DESIGN; SYS-ARCH/TECHSTACK rải PROJECT+BOUNDARY-MAP+HLD) |
| (ZIP `-DOMAIN` repo: FEAT/EP/BR/journey/persona + translate) | `DOMAIN_AUTHORING` | clone A1: author BUSINESS plain VN `docs/domain/` → ký → dịch sang eng `docs/architecture/` — cả ba nằm trong `/domain`. Bỏ SPECS-hub/cross-repo-sync (plumbing multi-repo); GIỮ 2-lớp business↔eng + ký + jargon-lint |
| **D3.5** standards-enrich · **D4** contracts · **D5** full CHARTER | `DESIGN` (chốt thiết kế của `/domain`) | **gộp** → ADR (stack) + HLD (=D5) + API/events/integrations (=D4); D3.5 coding-standard = skill `rules-{kind}`+`ref-{kind}-pattern` (cụ thể sẵn, không cần enrich) |
| **D7** WAVE-SEQUENCE | `PLAN` (chốt chia-wave của `/domain`) | move → WAVE-SEQUENCE + wave-*.md + MATRIX |
| DISCOVERED + sync-to-specs | `REVIEW` | replace → approve → `/run-wave` |

**Bỏ có chủ đích (multi-repo plumbing, single-repo không cần):** contract-signing/hash-drift (D4), `_shared/*` placeholder-enrich layer (D3.5), `/sync-to-specs`/SPECS hub, SYSTEM-TOPOLOGY/CONTRACT-MAP tách rời, multi-role Authority sign-off, BLOCKED state. **FEAT KHÔNG sinh ở Discovery** (cả ZIP lẫn harness — DOMAIN sở hữu).

**Flow stage (17 state):** `BOOTSTRAP → DISC_D0 → DISC_D1 → DISC_D2 → DISC_D3 → DOMAIN_AUTHORING → DESIGN ↺ → PLAN → REVIEW → WAVE_OPEN → DEV → REVIEW_DEV → DEV_HANDOFF → TEST_PLAN → TEST_EXECUTE → MANUAL_TEST → DONE`. `DESIGN`/`PLAN` là chốt bên trong `/domain` (tự làm UX nếu có boundary web/mobile). **Back-edge (lùi sửa doc phase-locked):** `/domain` gọi được từ DESIGN/PLAN/REVIEW — tự chạy tiếp từ chốt đang đứng; tiến lại re-gate. `next-wave`: `MANUAL_TEST → DONE → WAVE_OPEN` khi WAVE-SEQUENCE còn wave (**KHÔNG reset** — snapshot `archive/wave-N/` + đánh dấu kết quả theo wave); hết wave → teardown `DONE → BOOTSTRAP` (docs giữ nguyên). Boundary MỚI → `/discover D3`.

---

## ROUTING (load on demand)

| Câu hỏi | File / Command |
|---|---|
| "Tôi đang ở stage nào?" | `/status` |
| "Command nào được phép gọi tiếp?" | `state` output `allowed_commands[]` |
| "Quy trình state X?" | `harness/PROTOCOL.md` § `<state>` |
| "Gate của command Y?" | `commands/<Y>.md` frontmatter `gates:` |
| "Failure mode đã biết?" | `harness/PROTOCOL.md` § FM-* + `grep knowledge-base/` |
| "Ý tưởng/giả thuyết project (tổng quan)?" | `docs/discovery/hypothesis-log.md` (D0) |
| "Persona + capability map?" | `docs/discovery/persona-pool.md` + `docs/discovery/capability-map.md` (D1) |
| "Tình huống X xử ra sao?" (gửi 2 lần · sửa đồng thời · xoá · sai thứ tự · hỏng nửa chừng · bản cũ · rỗng · thu hồi quyền) | `hld-{boundary}.md` **§6.1 Ca biên đã quyết** — bảng TRA, checklist đóng 8 dòng, `n/a` hợp lệ nhưng **ô trống thì không** (gate `edge_cases_decided`). Ca biên HÀNH VI → `FEAT-*` §6.1. Ranh giới liên boundary (KHÔNG được gọi qua đường nào) → `hld` §6.2 |
| "Ai được / KHÔNG được làm gì?" | `docs/discovery/persona-pool.md` §Ma trận vai × hành động (`có`/`cấm`, không ô trống — gate D1 chặn). Spec phân quyền khi code · nguồn TC âm khi sinh test case · danh sách phép thử của vai `breaker` ở `/dogfood` |
| "Năng lực nào đã giao, còn bao nhiêu?" | `docs/discovery/capability-map.md` §1 cột `Wave giao` + `Trạng thái` (bảng SỐNG — PLAN điền wave, `/next-wave` cập nhật trạng thái) |
| "Surface nào đã giao ra ngoài, đổi được không?" | `tracking/BC-LEDGER.md` — §1 sổ hợp đồng (**tích luỹ vĩnh viễn**, không wave nào xoá) · §2 luật additive-first · §3 checklist rà mỗi wave (`/next-wave` re-arm; gate `backward_compat` chặn đóng wave ≥2) |
| "Đã chất vấn spec chưa?" | `tracking/challenge-log.md` — **hai lượt**, cột `Giai đoạn`: `tài liệu` (≥3 câu, trước `/approve-document`, trả lời CHỈ bằng tài liệu — câu nào phải đoán là **một lỗ tài liệu**) · `code` (≥1 câu, trước dòng code đầu). Gate `challenge_doc` + `challenge_passed`, lọc theo wave |
| "Chỗ nào tắc cứng, ai đang chờ gì?" | `tracking/blockers.md` (khuôn: `tracking/_templates/TEMPLATE.blockers.md`) — chỗ dừng hợp lệ THỨ BA (khác mơ hồ→`decide.py`, khác ngoài-scope→wave sau). Ghi xong **đi làm việc khác ngay**; cột `Đã thử gì` trống thì chưa phải blocker. Không reset khi mở wave — `/next-wave` đếm và nhắc |
| "Lớp doc nào đã được KÝ?" | discovery → ký ở chốt D3 của `/discover` · domain → ký trong `/domain` · design → ký ở `/approve-document`. Cả ba đều stamp `status: APPROVED` vào frontmatter; gate `*_stamped` chặn complete chay (state nói đã ký mà file còn `DRAFT`) |
| "Quyết định tự quyết khi mơ hồ ghi ở đâu?" | `tracking/decisions.md` — agent tự ghi bằng `py scripts/decide.py` khi gặp mơ hồ lúc làm (KHÔNG phải slash command); cột *giả định đang mang* + *đảo ngược được không* |
| "Event storming domain?" | `docs/discovery/event-storming/ES-{domain}.md` (D2) |
| "Boundary nào, charter ra sao?" | `docs/discovery/BOUNDARY-MAP.md` + `docs/discovery/boundaries/{b}/CHARTER.md` (D3) |
| "Epic / Feature / Business-rule (BUSINESS, plain VN — PO/BA ký)?" | `docs/domain/{epics/EP-*,feat/FEAT-*,business-rules/BR-*,journeys,personas}.md` (lớp business, A1) |
| "Epic / Feature / Business-rule (ENG — dịch từ business, DESIGN/PLAN đọc)?" | `docs/architecture/{epics/EP-*,feat/FEAT-*,business-rules/BR-*}.md` (đầu ra bước dịch của `/domain`) |
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
| "TC nào đang đỏ?" | `tracking/wave-{N}/test-report.md` + `test-logs/<TC>.log` (nguyên nhân thật). **KHÔNG có sổ bug** — kết quả test chỉ nằm ở report; sửa xong chạy lại chốt test-execute, report tự xanh |
| "Skills cho `kind` nào?" | `scripts/build_prompt.py` — `PRIMARY_SKILLS_PER_KIND` + `SCAFFOLD_REF_SKILLS_PER_KIND` (kernel đọc, không phải doc) |
| "Skills cho ``kind`` nào ở đâu?" | ``.claude/skills/<skill-name>/SKILL.md`` (auto-load on-demand bởi Claude Code) |
| "Cấu hình local dev (docker-compose)?" | `docs/architecture/infra/docker-compose.yml` |

---

## SLASH COMMANDS

> **7 lệnh.** Xếp theo thứ tự chạy trong một vòng phát triển. Mỗi lệnh **tự suy đang đứng ở đâu** — không mode, không cờ phải nhớ. Gate chi tiết → `harness/PROTOCOL.md`; body lệnh → `.claude/commands/<name>.md`.

| Bước | Lệnh | Tác dụng |
|---|---|---|
| **1. Khám phá** | `/discover` | Giả thuyết → persona + **ma trận vai x hành động** → event storming → boundary + `PROJECT.md`. Không arg — tự suy: gate wave đang đứng **xanh thì tiến**, **đỏ thì ở lại** đào đúng chỗ thiếu. Arg `D0..D3` chỉ để ép đào thêm khi gate đã xanh. **Chỗ được hỏi nhiều nhất — không trần số câu.** Hết D3: agent rà chéo cả lớp → **DỪNG, bạn ĐỌC và đánh giá** → bạn duyệt = chữ ký (`status: APPROVED`) → mới sang Domain |
| **2. Tài liệu** | `/domain` | **Nốt nửa sau, một mạch 9 chốt**: Epic/Feature/BR/Journey (nghiệp vụ, plain VN) → bạn OK = **ký** → dịch sang bản kỹ thuật → ADR/HLD/API/data-model/events/tích hợp → **UX nếu có boundary web/mobile** → chia wave (WAVE-SEQUENCE + MATRIX + KG) → **rà chéo toàn bộ**. Dừng ở REVIEW. Gọi lại = chạy tiếp từ chốt đang đứng. KHÔNG hỏi lại user — suy từ tài liệu `/discover`; mơ hồ → `decide.py` |
| **3. Chốt** | `/approve-document` | Bạn **ĐỌC + đánh giá** toàn bộ tài liệu → duyệt = **KHOÁ SCOPE** (ký lớp design/contract). Đây là chỗ kết thúc phần tài liệu; mở cổng wave |
| **4. Chạy wave** | `/run-wave [<N>]` | **Một mạch 7 chốt**: dựng wave → code từng boundary → review tới sạch → dựng chạy thật → sinh test → chạy test → dogfood. Gate đỏ = **DỪNG đúng chốt đó**. Gọi lại = chạy tiếp từ chốt đang đứng. Còn bug thì tự sửa + re-test |
| | `/dogfood [<vai>]` | Chạy lại **một** lăng kính (lượt đầu đã nằm trong `/run-wave`) |
| **5. Khép vòng** | `/next-wave` | Đóng wave + **mở wave kế, KHÔNG reset gì**: snapshot toàn bộ tài liệu → `archive/wave-N/`, đóng gói FEAT/AC đã giao (`DELIVERED.md`), đánh dấu kết quả theo wave nên gate wave mới tự đỏ lại. Hết WAVE-SEQUENCE → teardown |
| **Mọi lúc** | `/status` | Đang ở đâu · chốt kế là gì · gate còn thiếu gì |

**Không còn là lệnh** — 4 thứ đổi từ cửa-người-gõ thành cơ chế agent tự chạy:

| Cũ | Giờ ở đâu |
|---|---|
| `/decide` | `py scripts/decide.py`, nhắc trong NON-NEGOTIABLES của mọi prompt spawn. Mơ hồ → chọn phương án **dẫn về một tài liệu cụ thể** → ghi (kèm cột *giả định*) → đi tiếp. Script **từ chối** dòng không dẫn được về artifact nào |
| `/log-bug` | **bỏ hẳn, không thay bằng gì.** TC đỏ nằm ở `test-report.md`; phát hiện dogfood nằm ở `dogfood-report.md` §2 kèm ô `Xử`. Sổ bug là bản sao thứ ba của cùng một sự thật |
| `/fix-bugs` | lượt sửa trong `/run-wave`: `build_prompt.py fix --tc TC-NNN` → sửa → chạy lại `test-execute`. Không chốt riêng, không sổ phải đóng bằng tay |
| `/apply-cr` | thay đổi = wave sau (`/domain` vốn đã là back-edge) |
| `/design` · `/plan` · `/review-document` | ba chốt bên trong `/domain` (thiết kế · chia wave · rà chéo) |


> **Menu `/` hiện cả SKILL, không chỉ lệnh.** `domain-po`, `test-plan`, `dogfood`… là skill
> của sub-agent — gõ chúng chỉ **nạp checklist** vào phiên, KHÔNG chạy chốt và KHÔNG chuyển
> state. Nhận ra bằng mô tả: skill mở đầu bằng `Skill của <agent> (chốt X trong /<lệnh>)`.
> **7 lệnh thật** là bảng ở trên.

Mỗi command tự document trong `.claude/commands/<name>.md` (sync từ `commands/<name>.md` qua `py scripts/sync_commands.py`).

---

## RUNTIME GUARANTEES (hooks — chi tiết: `harness/PROTOCOL.md` §Hooks + §Gate evidence)

> Hook đọc từ `gates.py` / `STATE-MACHINE.json` / `policies.py` — **KHÔNG đọc file này**. Bảng dưới chỉ là *awareness* (đủ để biết cái gì sẽ chặn bạn); rule đầy đủ + FM-ID → PROTOCOL.md.

| Hook | Bạn cần biết (chi tiết → PROTOCOL.md) |
|---|---|
| `SessionStart` · `UserPromptSubmit` · `Notification` | Inject header `[HARNESS stage=… \| next: …]` mỗi turn |
| `PreToolUse(Bash)` — gate | Deny `harness <cmd> complete` nếu sai `allowed_commands` hoặc fail gate — §Gate evidence |
| `PreToolUse(Write\|Edit)` — kernel | **Sub-agent KHÔNG sửa được `scripts/` `harness/` `commands/` `agents/` `.claude/`** — đó là thứ đang chấm nó (gate · chỉ thị · hook · luật). Gate đỏ thì sửa cho đạt, đừng sửa gate. MAIN sửa được (đó là việc phát triển khung) |
| `PreToolUse(Write\|Edit)` | Block kernel files + 3 proof file (chỉ `capture_infra_proof.py` sinh, FM-PROOF-FORGE) + doc phase-locked ngoài stage sở hữu + `services/**` khi dev-handoff-agent (#12) |
| `PreToolUse(Task)` | Block spawn command-agent bằng prompt tự viết (E-6: phải dùng `build_prompt.py`); Explore free |
| `PreToolUse(AskUserQuestion)` | Chặn hỏi user ngoài khâu khám phá. Cho qua ở `BOOTSTRAP`/`DISC_*` (đó LÀ chỗ để hỏi) và ở ba chốt KÝ khi **MAIN** chạy (`DOMAIN_AUTHORING` ký nghiệp vụ · `REVIEW` khoá scope · `MANUAL_TEST` UAT). **Sub-agent thì không, ở bất kỳ đâu ngoài khám phá** — nó phải suy từ tài liệu khám phá, mơ hồ thì `decide.py`, tắc thật thì `blockers.md` |
| `PreToolUse(Skill\|SlashCommand)` | Chặn CHỈ `SlashCommand` chạy harness cmd ∈ GATE_RULES (MAIN tự nối pipeline); `Skill` tool cho qua (sub-agent load convention); user **gõ tay** không ảnh hưởng |
| `SubagentStop` | Validate RETURN SCHEMA (7 field: completed/deferred/needs_review/files_changed/build/lint/test) |
| `Stop` | Build/lint/test **wave-scoped** khi sửa `services/` ở {DEV, REVIEW_DEV, TEST_EXECUTE}; đỏ → block (cache git-hash) |
| `PreCompact` | Pin STATE (stage+wave+boundary) vào summary |

> Fail-open: hook crash → allow. Mọi gate force-bypass (`force:true,reason`) → audit `tracking/decisions.md`. Config: `.claude/settings.json` · scripts `scripts/hooks/`.
>
> **Permission là hàng rào NGOÀI, hook là hàng rào TRONG — hai lớp độc lập.** Thứ tự xét `deny → ask → allow`:
> `deny` chặn thứ hook không nhìn thấy (secret `.env*`/`~/.ssh`/`~/.aws`, `sudo`, `rm -rf /`, force-push) ·
> `ask` dừng hỏi ở hành động hướng RA NGOÀI hoặc không thu hồi được (`git push`, `gh repo create`/`release`,
> `npm publish`, `docker compose down --volumes`) · `allow` mở rộng `Bash`/`Edit`/`Write` cho đỡ ma sát.
> `allow` rộng **KHÔNG** mở khoá được thứ hook chặn — protected file, phase-lock, owned_paths, gate vẫn deny như thường.

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
