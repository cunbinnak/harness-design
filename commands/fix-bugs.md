# fix-bugs

Sửa bug — spawn `fix-{boundary}-agent.md`.

```bash
python scripts/build_command_prompt.py fix-bugs --boundary order
python scripts/harness.py fix-bugs complete
```

Pre: `test-execute` fail. Artifact: `tracking/bugs/**`
