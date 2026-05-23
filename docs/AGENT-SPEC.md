# Đặc tả file agent

## Một template duy nhất (boundary)

| File | Dùng khi |
|------|----------|
| `agents/_template.agent.md` | Materialize bộ 3 agent cho **mỗi boundary backend** + **FE** (`fe`) ở bước 4 intake |

```bash
py scripts/materialize_boundary_agents.py --boundaries order,product --wave wave-001
# → order, product, fe (3 file × mỗi boundary). Bỏ FE: --no-fe
```

| Layer | boundary_id mẫu | owned_paths (gợi ý) |
|-------|-----------------|---------------------|
| backend | `order`, `product` | `services/{id}/` |
| fe | `fe`, `frontend` | `apps/`, `packages/`, `services/fe/` |

## Intake & command — file agent cố định (không template riêng)

`/intake-requirement` gọi **từng specialist** theo bước:

```bash
py scripts/build_command_prompt.py intake-requirement --step 1 --input "..."
py scripts/build_command_prompt.py intake-requirement --step 2
# ...
```

| Bước | Agent file |
|------|------------|
| 1 | `requirement-analyst-agent.md` |
| 2 | `business-analyst-agent.md` |
| 3 | `solution-architect-agent.md` |
| 4 | `program-planner-agent.md` (+ materialize backend + FE) |

Command khác (`start-wave`, `test-execute`, …): một file `agents/{command}-agent.md` — spawn qua `build_command_prompt.py <command>`.

## Cấu trúc nội dung (mọi `*-agent.md`)

1. **Ai (Identity)** — bạn là ai, không phải ai  
2. **Nhiệm vụ (Mission)** — mục tiêu, phải làm, không được  
3. **Ngữ cảnh & phạm vi**  
4. **Đầu ra** — RETURN JSON (`harness/PROTOCOL.md`)

Evidence cho `harness.py complete` = **JSON truyền trên CLI**, không có thư mục riêng trong repo.
