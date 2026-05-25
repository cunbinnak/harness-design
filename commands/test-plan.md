# test-plan

Tạo **một file test cases** tổng hợp cho wave (cả auto + manual).

**Agent:** [test-plan-agent.md](../agents/test-plan-agent.md) · **Role:** `test-plan`

## Output

```
tracking/waves/{wave-id}/test-cases.md
```

**Một file duy nhất per wave**, mỗi TC có cột `Type: auto | manual`:
- Smoke tests (auto)
- Integration tests per FEAT:AC (auto)
- E2E tests (auto cho automation + manual cho UX)
- Manual UAT tests (stakeholder verify)
- Regression tests (auto, từ bug wave trước)

## Phân chia file theo stage

| File | Stage | Tạo bởi |
|------|-------|---------|
| `test-cases.md` | SPECIALIST_TESTING | test-plan |
| `test-results.md` | SPECIALIST_TESTING | test-execute (auto only) |
| `manual-test-log.md` | MANUAL_TEST | end-wave (skeleton) + stakeholder (điền) |
| `bugs/BUG-*.md` | bất cứ stage test nào | test-execute (origin: auto) hoặc stakeholder (origin: manual) |

## Input cần đọc (DOCS IN SCOPE auto-inject)

`handoff/{wave-id}.md` · `docs/architecture/feat/**` · `docs/architecture/api/**` · `docs/architecture/ux/**`

## Chạy

```bash
py scripts/build_command_prompt.py test-plan
py scripts/harness.py test-plan complete
```

Gate: `tracking/waves/*/test-cases.md` có ít nhất 1 file.
