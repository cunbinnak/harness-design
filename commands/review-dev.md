# review-dev

Self-review code theo boundary — spawn `review-{boundary}-agent.md`.

**Slash:** `/review-dev <boundary_id>`

## Luồng

```
review-dev
    │
    ▼
review-{boundary}-agent
    ├── chạy tests + coverage
    ├── coverage BE ≥ 80% && FE ≥ 60% ?
    │       ├── YES → report approved → harness complete
    │       └── NO  → spawn fix-{boundary}-agent → fix → re-run tests → approve
    └── code quality, security check
```

## Ngưỡng bắt buộc

| Metric | Ngưỡng | Hành động nếu thiếu |
|--------|--------|---------------------|
| BE coverage | ≥ 80% | Spawn `fix-{boundary}-agent`, không approve |
| FE coverage | ≥ 60% | Spawn `fix-{boundary}-agent`, không approve |
| Unit test pass | 100% | Fix trước khi approve |
| Security (≥ medium) | 0 issues | Fix trước khi approve |

## Chạy

```bash
# Build prompt cho boundary cụ thể
py scripts/build_command_prompt.py review-dev --boundary order

# Complete (sau khi review-{boundary}-agent approved)
py scripts/harness.py review-dev complete
# hoặc với boundary_id (khi nhiều boundary)
py scripts/harness.py review-dev complete '{"boundary_id": "order"}'
```

## Agent

`agents/review-{boundary_id}-agent.md` (materialized từ `_template.agent.md`)

Xem section **"Nếu bạn là Review Agent"** trong template agent để biết luồng chi tiết.

## Sau review-dev

- Approved → `dev-handoff`
- Issues fixed → `review-dev` lại (nếu cần) hoặc `dev-handoff` ngay
