# Orchestrator (Claude / Cursor / CLI)

**Hướng dẫn:** [`HUONG-DAN-SETUP.md`](HUONG-DAN-SETUP.md)

```bash
python scripts/harness.py intake-requirement complete
python scripts/harness.py review-document complete '{"approved": true}'
python scripts/harness.py state
```

Gates: `harness/COMMAND-GATES.json` · Hooks: `scripts/hooks/run_hook.py`
