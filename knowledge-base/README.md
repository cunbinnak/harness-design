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

## Schema

Mỗi KG có sections:

| Section | Nội dung | Ai ghi |
|---------|---------|--------|
| `metadata` | tech stack, purpose, integration refs | solution-architect (intake step 3) |
| `entities[]` | aggregate roots, entities, value objects | dev agent khi code |
| `business_rules[]` | BR-NNN với cornerstone flag | business-analyst (step 2) + dev |
| `events_published[]` | events boundary phát ra | solution-architect + dev |
| `events_consumed[]` | events boundary nhận về | solution-architect + dev |
| `dependencies` | outbound + inbound API calls | solution-architect + review |
| `integrations[]` | external systems (DB, cache, broker) | solution-architect |
| `permissions` | RBAC + multi-tenancy | solution-architect |
| `workflows[]` | long-running orchestration (Temporal/saga) | solution-architect |
| `learnings` | gotchas + patterns phát hiện | review agent |
| `failure_modes[]` | FM-NNN với detection + mitigation | fix agent, test agent |
| `execution_history[]` | wave participation status | program-planner + end-wave |

## Khi nào ghi

Append vào KG **sau khi sub-agent xong work**:

- Dev sub-agent → append entities, BR, events_published khi implement code.
- Review sub-agent → append learnings (gotchas) khi phát hiện anti-pattern.
- Fix sub-agent → append failure_modes khi fix bug discovered new FM.
- Test execute → append learnings, failure_modes khi test discover behavior.
- End-wave → append execution_history entry: status=COMPLETED + deliverables.

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
