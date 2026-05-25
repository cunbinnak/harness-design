# Scripts harness

| Script | Mục đích |
|--------|----------|
| `harness.py` | CLI command workflow (chính) |
| `build_command_prompt.py` | Prompt theo command (boundary / intake step / skill); intake `--step N` ghi STATE |
| `intake_pipeline.py` | Tiến độ intake: `begin <1-4>`, `show` |
| `state_engine.py` | STATE, transition, register-boundary, spawn, complete-command |
| `workflow_engine.py` | complete-command / can-command |
| `gate_runner.py` | Kiểm tra COMMAND-GATES |
| `build_context.py` | Nạp STATE.context |
| `knowledge_writer.py` | Ghi KG |
| `sync_commands.py` | Sync slash → `.cursor` / `.claude` |
| `hooks/run_hook.py` | Chạy hook theo HOOK-RULES |

Entry: `python scripts/harness.py state`
