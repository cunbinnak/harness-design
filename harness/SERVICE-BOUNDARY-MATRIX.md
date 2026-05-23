# SERVICE-BOUNDARY-MATRIX.json

**Nguồn sự thật** cho: boundary nào tồn tại, agent nào sở hữu, path nào được sửa, KG nào đọc.

## Khi nào được điền?

| Trạng thái | `boundaries` |
|------------|--------------|
| BOOTSTRAP | `[]` |
| Sau **start-wave** (`run_sync_matrix`) | Một row per `boundary_id` + `integrations[]` từ `integrations-matrix.md` |
| **register-boundary** | Thêm row lẻ (boundary mới ngoài roster) |

**Không** điền lúc intake — chưa mở wave. Điền khi **`start-wave` complete** (script `sync_matrix_from_roster.py`).

## Schema mỗi boundary

```json
{
  "boundary_id": "order",
  "display_name": "Order",
  "kind": "backend",
  "agent": "agents/order-agent.md",
  "knowledge_graph": "knowledge-base/order.knowledge-graph.yaml",
  "materialized_path": "services/order/",
  "owned_paths": [
    "services/order/**",
    "docs/architecture/hld/hld-order.md",
    "docs/architecture/api/api-order.md",
    "docs/architecture/data-model/data-model-order.md"
  ]
}
```

**FE** (`kind: fe`): thêm `apps/**`, `packages/**`, `docs/architecture/ux/ux-fe.md`, …

## `integrations`

Cặp boundary gọi nhau (sau architect bước 3 có thể bổ sung tay hoặc script tương lai):

```json
{
  "from": "fe",
  "to": "order",
  "contract": "docs/architecture/api/api-order.md"
}
```

## Lệnh liên quan

```bash
py scripts/harness.py start-wave complete
py scripts/harness.py register-boundary catalog-api --materialize
```

Đồng bộ từ roster: `py scripts/sync_matrix_from_roster.py`
