# test-execute

**Agent:** [test-execute-agent.md](../agents/test-execute-agent.md)

```bash
python scripts/build_command_prompt.py test-execute
python scripts/harness.py test-execute complete '{"test_result": "pass"}'
```

Fail → `fix-bugs --boundary <id>`
