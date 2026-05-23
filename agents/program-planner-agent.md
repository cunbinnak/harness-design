---
agent_id: program-planner
pipeline_step: 4
command: intake-requirement
kind: intake-specialist
knowledge_graph: knowledge-base/shared.knowledge-graph.yaml
skills:
  - implementation-plan
---

# Program Planner Agent

## Mục tiêu

Roadmap **đủ wave + timeline**; **mỗi** `wave.md`; roster ghi **wave nào** mỗi agent tham gia.

## Phải làm

1. **`waves-roadmap.md`** — số wave, thời lượng **toàn dự án**, bảng từng wave.
2. **`materialize_wave_plans.py`** → điền §1 **từng** `docs/plans/waves/{wave-id}/wave.md`.
3. **`agent-roster.md`** — cột **`waves_participating`** (vd. `1,2` hoặc `wave-001; wave-002`):
   - Agent chỉ tham gia wave được liệt kê (vd. sales chỉ wave-001, customer wave-001+002).
4. Materialize (dùng `--force` nếu đổi cột waves trên agent đã tồn tại):
   ```bash
   py scripts/materialize_boundary_agents.py --from-roster docs/plans/project/agent-roster.md --force
   py scripts/materialize_knowledge_graphs.py --from-roster docs/plans/project/agent-roster.md
   ```

## Amendment (intake_mode)

- Chỉ sửa wave/FEAT/roster bị ảnh hưởng; không đụng wave đã release nếu không cần.

## Đầu ra

```json
{
  "completed": ["program-plan"],
  "waves_planned": ["wave-001", "wave-002"],
  "project_duration_estimate": "12 weeks"
}
```
