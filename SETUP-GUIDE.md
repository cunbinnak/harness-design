# Harness Setup Guide

## Prerequisites

```bash
pip install -r requirements-harness.txt
py scripts/harness.py state
```

At **BOOTSTRAP**, expect `workflow.allowed_next: ["intake-requirement"]`.

---

## How commands work

The harness advances **one workflow step at a time**. Each step is a **command id** (same name as slash commands under `commands/`).

| Action | Pattern |
|--------|---------|
| Check what is allowed | `py scripts/harness.py state` or `py scripts/harness.py can <command>` |
| Finish a step | `py scripts/harness.py <command> complete` |
| Finish with evidence | `py scripts/harness.py <command> complete '<json>'` |

Evidence is a JSON object on the CLI (see `harness/COMMAND-GATES.json` and `harness/HOOK-RULES.json` for required fields per command).

**Do not** edit `harness/STATE.json` by hand to skip steps. Hooks enforce `workflow.allowed_next` and block bypass attempts.

### Spawn prompts (agents)

```bash
py scripts/build_command_prompt.py <command> [--step N] [--input "..."] [--boundary <id>]
```

Intake uses `--step 1` … `4`. Dev commands use `--boundary` matching `agent-roster.md`.

---

## Workflow sequence

```text
intake-requirement → review-document → start-wave [→ register-boundary?]
  → start-dev → review-dev → dev-handoff
  → test-plan → test-execute
  → (fail) fix-bugs → retest
  → (pass) release → end-wave

apply-cr → intake-requirement (amendment) → review-document → start-dev | start-wave
```

Gate definitions: [`harness/COMMAND-GATES.json`](harness/COMMAND-GATES.json).

### Intake (4 internal steps)

Analyzes the **whole product** and produces a **full multi-wave plan**: `waves-roadmap.md` (timeline, wave count) plus **`docs/plans/waves/{each-wave}/wave.md`**. Intake may **ask clarifying questions** (scope, duration, number of waves) before `complete`.

`start-wave` opens **one** wave at a time. **`wave_id` accepts flexible input:** `2`, `02`, `wave-2` → normalized to `wave-002` (see `scripts/wave_ids.py`).

**Agent roster** column `waves_participating` — each boundary lists which waves it joins (materialized into `agents/*-agent.md`).

1. Requirement analyst — project catalog + FEAT drafts + open questions  
2. Business analyst — testable AC, business rules, suggested boundaries  
3. Solution architect — ADR, per-boundary design, integrations, FEAT→boundary map  
4. Program planner — multi-wave roadmap, wave-001 plan, agents + KG  

Then: `intake-requirement complete` (only when gates pass). Human gate: `review-document`.

### After `end-wave` (next wave, same project)

| Situation | Next step |
|-----------|-----------|
| Plan wave tiếp theo **đã có** từ intake, **không** đổi scope | `start-wave complete '{"wave_id": "2", "wave_title": "..."}'` — **không** cần intake lại |
| Có thay đổi nghiệp vụ / CR / timeline / boundary | [`apply-cr`](commands/apply-cr.md) → `intake-requirement` (`amendment` + `cr_id`) → `review-document` → `start-dev` hoặc `start-wave` |

`end-wave` sets `allowed_next: ["start-wave", "intake-requirement"]` and keeps `completed: ["end-wave"]` so `start-wave` is allowed without re-review (first wave still needs `review-document` after initial intake).

### Intake amendment (legacy-safe)

Re-intake with `intake_mode: "amendment"` uses lighter gates (`gates_amendment`). Agents must **patch** only affected docs — do not rewrite accepted ADR/FEAT wholesale.

### Change requests (CR)

File CR trong repo = **đã duyệt** (không gate approve).

```text
apply-cr → intake-requirement (amendment + cr_id) → review-document → start-dev | start-wave
```

1. Tạo `tracking/change-requests/CR-NNN-*.md` từ [TEMPLATE.cr.md](tracking/change-requests/TEMPLATE.cr.md)
2. `py scripts/build_command_prompt.py apply-cr --cr CR-001` → agent điền § Kế hoạch cập nhật
3. `py scripts/harness.py apply-cr complete '{"cr_id":"CR-001",...}'`
4. Intake 4 bước với `intake_mode: amendment` + `cr_id`
5. Ghi KG; tiếp dev hoặc wave mới

Agent discipline: rule luôn bật [`.cursor/rules/harness-agent-discipline.mdc`](.cursor/rules/harness-agent-discipline.mdc) + đọc/ghi `discipline.*` trong shared KG (xem `STATE.context.kg_discipline` sau `build_context`).

### IDE (Cursor / Claude)

1. Read `commands/COMMAND-FRAMEWORK.md` and the command file for the current step.
2. Run the agent from the built prompt.
3. Call `harness.py <command> complete` with evidence when artifacts are ready.
4. On gate failure, fix artifacts and retry — do not advance STATE manually.

Sync slash commands after editing `commands/`: `py scripts/sync_commands.py`.

---

## Gate checklist (summary)

| Command | Main artifacts / evidence |
|---------|---------------------------|
| `intake-requirement` | PROJECT, feat, ADR≥3, `ux/ux-{fe-id}.md` (materialize), plans, roster, agents, KG, integrations |
| `review-document` | `approved: true` |
| `start-wave` | handoff, matrix synced from roster |
| `start-dev` | `wave.md` §2, `features_in_flight`, `boundaries_in_flight` |
| `dev-handoff` | `coverage_pct`, `handoff_ready`, runnable `docker-compose.yml` |
| `test-plan` | `tracking/test-case-registry/**` |
| `test-execute` | registry + `test_result` |
| `fix-bugs` | `tracking/bugs/**` |
| `release` | prior test pass + `release_ok` |
| `end-wave` | `end_wave_ok` |
| `apply-cr` | CR file + § Kế hoạch cập nhật |

---

## Tracking

| Phase | Path |
|-------|------|
| Test plan / execute | `tracking/test-case-registry/**` |
| Failed tests | `tracking/bugs/**` (required for `fix-bugs`) |
| Reports (optional) | `tracking/test-reports/` |

---

## Hooks

- Config: [`harness/HOOK-RULES.json`](harness/HOOK-RULES.json)
- Implementation: [`scripts/hooks/README.md`](scripts/hooks/README.md) (không dùng `harness/hooks/` — đã gỡ)
- Cursor: [`.cursor/hooks.json`](.cursor/hooks.json) — `failClosed: true` → `scripts/hooks/ide_bridge.py`

| Hook | Khi nào |
|------|---------|
| `owned_paths` | Sửa file |
| `discipline_blockers` | `harness complete` — KG `discipline.blockers` phải rỗng |
| `discipline_kg_return` | Sub-agent kết thúc — bắt `kg_appended` nếu có thay đổi |
| `spawn_stage` | Spawn — đúng `STATE.stage` |
| `return_schema` + gates | Shell `harness.py … complete` |

Vi phạm → **HARNESS — KHÔNG ĐƯỢC PHÉP.** Không lách bằng sửa STATE tay.

---

## Key paths

| Path | Role |
|------|------|
| `harness/STATE.json` | Current stage + `workflow.allowed_next` |
| `harness/SERVICE-BOUNDARY-MATRIX.json` | Boundaries, owned paths, integrations |
| `commands/manifest.yaml` | Command registry |
| `scripts/harness.py` | CLI entrypoint |

See also: [`README.md`](README.md), [`harness/PROTOCOL.md`](harness/PROTOCOL.md).
