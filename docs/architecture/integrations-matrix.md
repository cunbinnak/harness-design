# Integrations matrix

> Architect (intake bước 3) điền. Đồng bộ sang `harness/SERVICE-BOUNDARY-MATRIX.json` → `integrations[]` khi `start-wave`.

## Gọi đồng bộ (sync)

| from_boundary | to_boundary | kind | contract | notes |
|---------------|-------------|------|----------|-------|
| fe-web | customer | http | docs/architecture/api/api-customer.md | SPA → API |
| sales | customer | http | docs/architecture/api/api-customer.md | read customer ref |

## Sự kiện (async) — tùy chọn

| producer | consumer | topic/event | schema |
|----------|----------|-------------|--------|
| | | | |

## Quy tắc

1. **FE → BE:** mỗi hàng `from` là boundary `layer: fe`, `to` là backend phục vụ.
2. **BE → BE:** tránh circular; ưu tiên API sync trước event.
3. Mọi hàng phải có `contract` trỏ file API hoặc event schema.
