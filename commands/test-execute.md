# test-execute

Chạy **auto** test (Type: auto trong test-cases.md) — smoke + integration + E2E auto.

**Agent:** [test-execute-agent.md](../agents/test-execute-agent.md) · **Role:** `test-execute`

## Luồng

```
docker-compose up --build -d  →  Smoke /health 200?
                                   ├ FAIL → docker down → fix-bugs
                                   └ PASS → Integration/E2E auto
                                              ↓
                                       test-results.md + bugs/
                                              ↓
                                       docker-compose down (BẮT BUỘC)
                                              ↓
                                  pass → release  |  fail → fix-bugs
```

## Output (per-wave folder)

| File | Nội dung |
|------|---------|
| `tracking/waves/{wave-id}/test-results.md` | Summary + chi tiết từng TC |
| `tracking/waves/{wave-id}/bugs/BUG-{n}-*.md` | Bug ticket (field `origin: auto`) |

**Field `origin: auto`** trong bug ticket → `retest` smart-route về `SPECIALIST_TESTING`.

## Chạy

```bash
py scripts/build_command_prompt.py test-execute
py scripts/harness.py test-execute complete '{"test_result": "pass"}'  # hoặc "fail"
```

## Sau fail

```bash
py scripts/build_command_prompt.py fix-bugs --boundary {boundary_id}
py scripts/harness.py fix-bugs complete '{"boundary_id": "{boundary_id}"}'
py scripts/harness.py retest complete '{"test_result": "pass"}'
```

**Lưu ý:** TC `Type: manual` trong test-cases.md → KHÔNG chạy ở đây. Chạy ở stage MANUAL_TEST (sau `end-wave`).
