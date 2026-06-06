# Knowledge Base — per-boundary memory

KG (Knowledge Graph) per boundary. Agent đọc trước khi work, ghi sau khi xong. Domain memory dài hạn của boundary qua nhiều wave.

## Cấu trúc

```
knowledge-base/
├── README.md
├── TEMPLATE.boundary-kg.yaml         (skeleton — materialize fill)
├── {prefix}-{boundary}.knowledge-graph.yaml    (1 file per boundary)
└── ...
```

Mỗi boundary có 1 file KG riêng. File name: `{prefix}-{boundary}.knowledge-graph.yaml` (vd `crm-hdpe-order-mgmt.knowledge-graph.yaml`).

## Schema — 2 nhóm, vòng đời khác nhau

**Nhóm DESIGN (phái sinh từ docs)** — nguồn sự thật ở docs; KG là view cô đọng. **Seed 1 lần ở `/start-wave`** từ docs đã chốt (sau approve); re-sync khi docs đổi qua `/apply-cr`. Dev chỉ update nếu implement khác design (kèm sửa doc). KHÔNG gõ tay rải rác.

| Section | Nội dung | Seed từ (ở `/start-wave`) |
|---------|---------|--------|
| `metadata` | tech stack, purpose | MATRIX (materialize) |
| `entities[]` | aggregate roots, entities | `data-model-{boundary}.md` |
| `business_rules[]` | BR-NNN + cornerstone | `FEAT-*` của boundary |
| `events_published[]` / `events_consumed[]` | events phát/nhận | `events/{boundary}-events.md` |
| `dependencies` | outbound + inbound | `integrations/INTEG-*` |
| `integrations[]` | external systems | `integrations/INTEG-EXT-*` |
| `permissions` | RBAC + tenant | `hld-{boundary}.md` §7 |
| `workflows[]` | saga/temporal | `hld-{boundary}.md` §8 |

**Nhóm KINH NGHIỆM (sinh lúc làm)** — KG là nguồn sự thật duy nhất; **append/update khi phát sinh**.

| Section | Nội dung | Ai ghi (khi nào) |
|---------|---------|--------|
| `learnings` | gotchas + patterns | dev/review/test — **khi phát hiện** anti-pattern/bài học mới |
| `decisions[]` | quyết định kỹ thuật cục bộ | dev/fix — **khi quyết** (không lên ADR) |
| `discipline` | blockers + do_not_repeat | agent set khi gặp blocker / clear khi xong |
| `failure_modes[]` | FM-NNN + detection/mitigation | fix/test — **khi discover FM mới** |
| `execution_history[]` | wave participation status | end-wave update |

## Khi nào ghi / update

- **`/start-wave`** → seed nhóm DESIGN từ docs cuối (start-wave-agent). Nhóm kinh nghiệm để rỗng.
- **`/review-document`** (intake) → **KHÔNG đụng KG**, chỉ sửa doc; design seed sau ở start-wave từ docs cuối.
- **Dev** → append nhóm kinh nghiệm khi phát sinh; update design CHỈ khi implement lệch (kèm sửa data-model).
- **Review** → append `learnings` **chỉ khi** phát hiện cái mới; review sạch thì KHÔNG ghi.
- **Fix** → append `failure_modes` khi discover FM mới.
- **End-wave** → update `execution_history` (status=COMPLETED + deliverables).
- **`/apply-cr`** (sau DONE) → docs đổi → re-sync nhóm DESIGN.

## RETURN SCHEMA requires `kg_appended[]`

Mỗi sub-agent với `files_changed != []` PHẢI return `kg_appended` non-empty. Hook SubagentStop warn nếu thiếu.

```json
{
  "files_changed": ["services/.../OrderService.java"],
  "kg_appended": ["entity:OrderAggregate", "br:BR-ORDER-001", "decision:DEC-NNN"]
}
```

## Edit KG

Agent dùng Edit tool trực tiếp trên YAML:

```python
# Pseudo-code agent flow:
kg = read("knowledge-base/crm-hdpe-order-mgmt.knowledge-graph.yaml")
kg["entities"].append({"name": "OrderAggregate", "type": "aggregate_root", ...})
kg["business_rules"].append({"id": "BR-ORDER-001", ...})
write("knowledge-base/crm-hdpe-order-mgmt.knowledge-graph.yaml", kg)
```

(Không có script `knowledge_writer.py` riêng — direct edit qua Edit tool đủ.)

## Versioning

KG schema version: `version: 1` (current). Bump khi schema breaking change.

## Liên quan

- [TEMPLATE.boundary-kg.yaml](TEMPLATE.boundary-kg.yaml) — skeleton structure
- [agents/](../agents/) — agent files reference `kg_target` field
- [harness/PROTOCOL.md](../harness/PROTOCOL.md) — RETURN SCHEMA + kg_appended requirement
- [scripts/materialize.py](../scripts/materialize.py) — gen KG skeleton per boundary lúc start-wave
