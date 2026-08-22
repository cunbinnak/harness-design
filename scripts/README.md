# Scripts — kernel Python

Bảng dưới là **danh sách đầy đủ**. Trước đây nó liệt kê 12/23 file — bản chép tay thiếu quá nửa
mà không ai thấy, vì thiếu thì không gây lỗi gì. Thêm script mới thì thêm dòng ở đây; quên thì
`doc_integrity` không bắt được, nhưng `selftest_all.py --list` sẽ lộ ra chỗ chênh.

## Bắt đầu một project mới

```bash
py scripts/bootstrap.py <mã-project> --name "Tên" --prefix cb
```

COPY bộ khung ra thư mục riêng, dọn artifact, đặt danh tính, `git init` sạch. **Bản khung giữ
nguyên** — không fork, không phải nhớ chạy reset, không mang lịch sử git của khung sang.

## Danh sách

| Script | Mục đích |
|---|---|
| `bootstrap.py` | Dựng project mới từ khung (copy → dọn → danh tính → kiểm → git init) |
| `harness.py` | CLI mỏng, gọi `state.py` |
| `state.py` | Quản STATE: load/save/validate/transition + in mục tự-xác-nhận |
| `gates.py` | Hàm gate thuần + `GATE_RULES` (nguồn duy nhất; `--list` để in) |
| `build_prompt.py` | Dựng prompt tự chứa cho sub-agent theo từng chốt |
| `next_wave.py` | Đóng wave / mở wave: snapshot, đánh dấu, re-arm, **KHÔNG reset** |
| `decide.py` | Ghi 1 quyết định vào `tracking/decisions.md` (từ chối dòng không dẫn về artifact) |
| `approve_document.py` | Stamp `APPROVED`/`ACTIVE` vào frontmatter lớp doc |
| `domain_approve.py` | Ký lớp nghiệp vụ `docs/domain/` |
| `discovery_gate.py` | Gate D0-D3 |
| `planning_lint.py` | Lint tài liệu kế hoạch |
| `wave_sequence_lint.py` | Lint `WAVE-SEQUENCE.md` |
| `materialize.py` | Sinh artifact per-boundary (dev/fix agent, KG) từ MATRIX |
| `materialize_matrix.py` | Ghi `SERVICE-BOUNDARY-MATRIX.json` |
| `capture_infra_proof.py` | Sinh proof hạ tầng/health — **chỉ script này được ghi**, ghi tay = FM-PROOF-FORGE |
| `capture_feature_state.py` | Derive `feature-state.md` từ registry + report |
| `doc_integrity.py` | Soi tài liệu trôi khỏi code (lệnh ma · gate ma · số lệnh sai · link chết · template mồ côi) |
| `selftest_all.py` | Chạy MỌI phép tự kiểm — **tự dò**, không chép danh sách |
| `smoke_test.py` | E2E state machine |
| `sync_commands.py` | Sync `commands/*.md` → `.claude/commands/` |
| `reset_for_new_project.py` | Dọn artifact TẠI CHỖ (bootstrap gọi lại; dùng trực tiếp khi bản làm việc đã bẩn) |
| `harness_lib.py` | Helper: `repo_root` · `load_json` · `save_json` · `utc_now_iso` |
| `hooks/dispatcher.py` | Một cửa vào cho 9 sự kiện hook |
| `hooks/policies.py` | Hàm kiểm thuần cho hook (phase-lock · protected · token drift) |

## Entry points

```bash
# CLI workflow
py scripts/harness.py state                          # current STATE summary
py scripts/harness.py can <command>                  # YES/NO check command allowed
py scripts/harness.py <command> complete '<evidence>'  # apply gate + transition

# Build prompts
py scripts/build_prompt.py <command> [options]       # stdout self-contained prompt
py scripts/build_prompt.py <command> --stats         # size breakdown
py scripts/build_prompt.py <command> --save path     # write to file + stdout

# Materialize MATRIX (stage PLAN — MATRIX bị hook chặn Write tay, dùng script này)
py scripts/materialize_matrix.py <boundaries.json>   # gate stage ∈ {BOOTSTRAP,PLAN}, validate, ghi MATRIX
py scripts/materialize_matrix.py --json '[...]' --mode merge   # update theo boundary_id
py scripts/materialize_matrix.py <f>.json --dry-run  # in ra, không ghi
py scripts/materialize_matrix.py --selftest

# Materialize per-boundary artifacts (sau khi có MATRIX)
py scripts/materialize.py                            # all boundaries in MATRIX
py scripts/materialize.py --wave 1                   # filter by wave
py scripts/materialize.py --boundary X --force       # specific boundary, overwrite
py scripts/materialize.py --dry-run                  # show what would write

# Sync commands → IDE
py scripts/sync_commands.py                          # → .claude/commands/
py scripts/sync_commands.py --cursor                 # also → .cursor/commands/

# Reset for new project
py scripts/reset_for_new_project.py                  # interactive (Phase 7+)

# Tests
py scripts/gates.py                                  # gates selftest
py scripts/state.py validate                         # STATE schema validate
py scripts/smoke_test.py                             # E2E state machine
```

## Hooks

```bash
# Hook dispatcher (called by Claude Code framework, not user)
py scripts/hooks/dispatcher.py --event <name>        # event handler

# Events: SessionStart, UserPromptSubmit, Notification, PreCompact,
#         PreToolUse, PostToolUse, SubagentStop, Stop, SessionEnd
```

Detail: [hooks/README.md](hooks/README.md).

## Relationship

```
harness.py  →  state.py  →  gates.py        (CLI flow)
                ↓
            STATE.json (write)

build_prompt.py  →  state.py + load MATRIX  →  stdout prompt
                                              ↓
                                        Agent tool spawn

materialize.py  →  MATRIX + templates  →  gen agents + KG files

hooks/dispatcher.py  →  policies.py + state.py  →  Claude Code response
```

## Liên quan

- [harness/PROTOCOL.md](../harness/PROTOCOL.md) — protocol detail
- [agents/](../agents/) — agent files spawned bởi build_prompt.py
- [commands/](../commands/) — slash command source
- [hooks/README.md](hooks/README.md) — hook implementation detail
