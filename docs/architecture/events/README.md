# Events

Async event contracts per boundary. Mỗi boundary có 1 file `{boundary}-events.md` mô tả mọi event boundary đó publish + consume.

## Cấu trúc

```
docs/architecture/events/
├── README.md
├── TEMPLATE.events.md
├── order-mgmt-events.md      (per backend boundary)
├── customer-mgmt-events.md
└── ...
```

## Khi nào tạo

Intake step 3 (solution-architect) tạo `{boundary}-events.md` cho mọi boundary có publish hoặc consume event.

Frontend boundaries (web/mobile) thường KHÔNG có events file (FE không publish event domain). BFF có thể có (vd subscription GraphQL).

## Format

Theo [TEMPLATE.events.md](TEMPLATE.events.md). Mỗi event có:
- Tên + topic name
- Schema version
- Trigger condition (khi nào publish)
- Payload structure
- Consumers (boundaries subscribe)
- Idempotency key
- Ordering guarantee
- Error handling (DLQ, retry policy)

## Workflow

- Intake step 3: solution-architect viết events spec per boundary.
- Dev: dev-agent implement publisher/consumer theo spec.
- Review: review agent verify code khớp spec.
- KG: events publish/consume append vào `knowledge-base/{prefix}-{boundary}.knowledge-graph.yaml` sections `events_published[]` + `events_consumed[]`.

## Versioning

- Topic name include version: `order.confirmed.v1`
- Schema changes: bump version (`v1` → `v2`), giữ v1 deprecated 1 wave.
- Producer publish cả v1 + v2 trong transition wave.

## Liên quan

- [agents/solution-architect-agent.md](../../../agents/solution-architect-agent.md)
- [docs/architecture/integrations/](../integrations/) (cross-boundary contracts)
- [knowledge-base/TEMPLATE.boundary-kg.yaml](../../../knowledge-base/TEMPLATE.boundary-kg.yaml) sections `events_published`, `events_consumed`
