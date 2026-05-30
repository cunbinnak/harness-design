# ADLC Design Harness — CLAUDE.md

> **Router file.** Đọc top-to-bottom mỗi session. Tier-A only — chi tiết → routing table.

---

## NON-NEGOTIABLES

1. **Đọc `harness/STATE.json` trước mọi tool call** (hoặc xem header `[STATE: ...]` đã được hook `UserPromptSubmit` inject).
2. **Edit chỉ trong `owned_paths`** của `active_boundary`. PreToolUse hook block; đừng cố lách.
3. **Stage transition CHỈ qua slash command** (`/start-wave`, `/dev-handoff`, `/end-wave`, …). KHÔNG sửa `stage` trong STATE.json bằng tay.
4. **Quyết định non-trivial → artifact ngay** (ADR / FEAT / CR / KG). Không để chỉ tồn tại trong chat.
5. **Cross-boundary change** phải qua `/apply-cr` + `/review-document` approve trước khi code.
6. **Không bypass test** (`--no-verify`, skip), không hardcode secrets, không modify intake-locked docs sau `/review-document` đã approve.

> Vi phạm sẽ bị hook block. Refusal message tham chiếu `harness/PROTOCOL.md` § Failure Modes (FM-ID).

---

## IDENTITY

| Field | Value |
|---|---|
| Project | **ADLC Design Harness** — bộ khung orchestrator cho workflow ADLC (Architecture-Driven Lifecycle), kết hợp agent + người theo chuẩn harness |
| Repo type | **Design repo** — chứa harness kernel + docs + plans + agents + skills + commands + tracking + knowledge-base. KHÔNG chứa code service. |
| Strategy | **Polyrepo** — mỗi boundary scaffolded ở `/start-dev` là 1 repo riêng (`{prefix}-{boundary}`). Service repos sống ngoài, link qua `SERVICE-BOUNDARY-MATRIX.json` field `repo_url`. |
| Kernel stack | Python 3.14 (state engine + hooks + materialize + build_prompt) |
| Service stack | Per-boundary, set trong intake step 3 (technical-design). Vd: Java 21 + Spring Boot 3.4, Node.js 22 + Apollo, React 19 + Vite, Flutter 3, … |
| Scale | 10 states · 13 commands · N waves · M boundaries (set dynamic từ intake step 4) |
| `services/` trong repo này | **gitignored** — chỉ working dir tạm khi sub-agent scaffold (push lên repo riêng, không track ở đây) |

> Khi fork harness này cho project mới: `/intake-requirement` sẽ rewrite IDENTITY (project name, prefix, scale) qua artifacts ở `docs/architecture/PROJECT.md`.

---

## ROUTING (load on demand)

| Câu hỏi | File / Command |
|---|---|
| "Tôi đang ở stage nào?" | `py scripts/harness.py state` |
| "Command nào được phép gọi tiếp?" | `state` output `allowed_commands[]` |
| "Quy trình state X?" | `harness/PROTOCOL.md` § `<state>` |
| "Gate của command Y?" | `commands/<Y>.md` frontmatter `gates:` |
| "Failure mode đã biết?" | `harness/PROTOCOL.md` § FM-* + `grep knowledge-base/` |
| "Project này làm gì? Stack? Scope?" | `docs/architecture/PROJECT.md` |
| "Feature X yêu cầu gì?" | `docs/architecture/feat/FEAT-X-*.md` |
| "Boundary design ra sao?" | `docs/architecture/hld/hld-{boundary}.md` |
| "API contract boundary?" | `docs/architecture/api/api-{boundary}.md` |
| "Schema boundary?" | `docs/architecture/data-model/data-model-{boundary}.md` |
| "UX / wireframe boundary?" | `docs/architecture/ux/ux-{boundary}.md` |
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
# Core flow (11)
/intake-requirement                       Flat orchestration: main spawn 4 sub-agents tuần tự (req → biz → arch → plan)
/review-document "<feedback>" [--file X]  Revision loop. User feed feedback, agent revise doc. Lặp đến khi user OK
/approve-document                         User mark doc OK (approved=true). KHÔNG đổi state. Cho phép /start-wave
/start-wave <N>                           Mở wave, materialize boundaries + agents + KG (gate: approved=true)
/start-dev <boundary>                     Vào DEV, spawn dev sub-agent boundary (auto detect kind)
/review-dev                               Self-review code + coverage. Internal loop fix+review
/dev-handoff                              Verify gates (coverage≥80, infra) → TEST
/test-plan                                Sinh test-case-registry.md
/test-execute                             Build local + run auto test. Internal fix loop. Pass → auto-transition MANUAL_TEST
/end-wave                                 Soft close, infra UP → DONE (UAT signed)
/done-wave                                Hard close, teardown → BOOTSTRAP

# Branch (1)
/fix-bugs <bug-id>                        Fix manual UAT bug. Chain spawn fix + review sub-agent

# Side (1)
/apply-cr <CR-ID>                         Change request → intake amendment (chỉ từ DONE state)
```

Mỗi command tự document trong `.claude/commands/<name>.md` (sync từ `commands/<name>.md` qua `py scripts/sync_commands.py`).

---

## RUNTIME GUARANTEES (do hooks cung cấp)

- `SessionStart` hook in STATE summary + non-negotiables.
- `UserPromptSubmit` hook inject `[STATE: stage={stage} wave={wave} boundary={b} allowed={cmds}]` mỗi turn.
- `PreToolUse(Bash)` hook check `harness <X> complete`: allowed_commands (theo STATE-MACHINE) + gate (gates.py).
- `PreToolUse(Write|Edit)` hook block edit `harness/STATE.json`, `harness/STATE-MACHINE.json`, `.claude/settings.json`.
- `PreToolUse(Task)` hook KHÔNG block theo stage. Explore agent free. Chỉ inject reminder boundary cho dev-spawn.
- `PostToolUse(Bash)` hook append checkpoint vào `STATE.workflow.history`.
- `SubagentStop` hook validate RETURN SCHEMA + kg_appended.
- `Stop` hook chạy build/lint/test scoped theo `kind` của `active_boundary` khi `stage` ∈ [DEV, TEST] VÀ turn có sửa file trong `services/{prefix-boundary}/`. Đỏ → block stop kèm 40 dòng output cuối; xanh → allow. Cache theo git hash, không rerun nếu code không đổi.
- `PreCompact` hook pin STATE + active wave + 3 quyết định gần nhất vào summary.

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

