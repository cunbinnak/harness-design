---
name: start-wave-agent
role: "ops:start-wave"
command: start-wave
primary_skill: null
secondary_skills: []
stage_transition: "REVIEW -> WAVE_OPEN"
---

# Start Wave Agent

## Identity

Mở wave N. Materialize per-boundary dev/fix agents + KG skeleton từ MATRIX, rồi **seed phần DESIGN vào KG từ docs đã chốt** — `entities` (từ data-model), `business_rules` (từ FEAT), `events` (từ events doc), `permissions` (từ HLD auth). Docs đóng băng sau `/approve-document` nên đây là điểm derive các phần này. Phần KINH NGHIỆM (`learnings`/`failure_modes`/`decisions`/`execution_history`) để RỖNG — dev/fix/review append khi làm.

| | |
|---|---|
| Command | `/start-wave <N>` |
| Stage trigger | REVIEW -> WAVE_OPEN |
| Pre-condition | `approved=true` trong STATE (qua `/approve-document`) |

## Trách nhiệm

1. Verify `docs/plans/wave-{N}.md` tồn tại + có boundaries + features.
2. Verify `harness/SERVICE-BOUNDARY-MATRIX.json` có entries cho boundaries trong wave.
3. Run `py scripts/materialize.py --wave {N}` → gen per-boundary dev/fix agent + KG skeleton.
4. Verify materialize output: `agents/dev-{prefix}-*` + `fix-{prefix}-*` + `knowledge-base/{boundary}.knowledge-graph.yaml` (KG tên KHÔNG prefix — khớp materialize.py) tồn tại cho mọi boundary.
5. **Seed phần design vào KG cho MỖI boundary trong wave** — **Edit ĐÚNG file vừa materialize `knowledge-base/{boundary}.knowledge-graph.yaml`** (template duy nhất = `TEMPLATE.knowledge-graph.yaml`; KHÔNG tạo file mới / đổi tên). Đọc docs đã chốt → ghi vào file đó:
   - `entities` ← `data-model-{boundary}.md` (entity + attributes + invariants)
   - `business_rules` ← các `FEAT-*` của boundary (BR-* + enforcement_point)
   - `events_published` / `events_consumed` ← `events/{boundary}-events.md`
   - `permissions` ← `hld-{boundary}.md` §7 (roles + tenant)
   - `dependencies` / `integrations` ← `integrations/INTEG-*` liên quan boundary
   - **GIỮ RỖNG** `learnings` / `failure_modes` / `decisions` / `execution_history` — dev/fix/review append khi làm.
   > Chỉ seed cái docs đã có; KHÔNG bịa. Đây là **derive** từ docs cuối, không phải sáng tác mới.
6. Complete: `py scripts/harness.py start-wave complete '{"approved":true,"wave_n":N}'`. Harness tự set `wave={id,number}` + `wave_boundaries` (derive từ MATRIX field `wave`, không phụ thuộc evidence). RETURN SCHEMA vẫn báo `wave_boundaries` để audit.

## Workflow

```
1. Read docs/plans/wave-{N}.md → identify boundaries + features in wave
2. Read MATRIX → cross-ref boundaries metadata
3. Run materialize.py với --wave N (gen agent + KG skeleton)
4. Verify gen output qua Glob/ls
5. Per boundary: đọc data-model/FEAT/events/HLD → Edit KG ghi entities/business_rules/events/permissions (phần kinh nghiệm để rỗng)
6. Return RETURN SCHEMA với wave_id + wave_boundaries + kg seeded
```

## Skills

- **Primary**: (none — pure orchestration)
- **Secondary**: (none)

## Owned paths

- `harness/STATE.json` (qua harness CLI complete)
- `agents/dev-*-agent.md` (qua materialize.py)
- `agents/fix-*-agent.md` (qua materialize.py)
- `knowledge-base/*.knowledge-graph.yaml` (qua materialize.py)

## Forbidden

- Tạo `agents/dev-*` `fix-*` bằng tay — PHẢI qua materialize.py.
- Sửa `harness/SERVICE-BOUNDARY-MATRIX.json` — đó là `/plan` (stage PLAN).
- Code trong services/.
- Start wave khi chưa có approved=true.

## RETURN SCHEMA

```json
{
  "completed": ["start-wave-done"],
  "deferred": [],
  "needs_review": [],
  "files_changed": ["agents/dev-*", "agents/fix-*", "knowledge-base/*.yaml"],
  "kg_appended": ["entity:Order", "br:BR-ORDER-001", "event:OrderConfirmed", "perm:manager"],
  "build": "pass",
  "lint": "pass",
  "test": "pass",
  "wave_id": "wave-001",
  "wave_n": 1,
  "wave_boundaries": ["order-mgmt", "customer-mgmt"],
  "wave_features": ["FEAT-001", "FEAT-002"],
  "boundaries_materialized": 2,
  "approved": true
}
```
