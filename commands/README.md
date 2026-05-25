# Commands

Nguồn sự thật: [`harness/COMMAND-GATES.json`](../harness/COMMAND-GATES.json) · Luồng tổng quan: [`COMMAND-FRAMEWORK.md`](COMMAND-FRAMEWORK.md) · Setup: [`SETUP-GUIDE.md`](../SETUP-GUIDE.md)

## Wave flow (chuẩn)

| # | Command | Stage sau | Ghi chú |
|---|---------|-----------|---------|
| 1 | [intake-requirement](intake-requirement.md) | IMPLEMENTATION_PLAN | BOOTSTRAP — 4 step pipeline |
| 2 | [review-document](review-document.md) | IMPLEMENTATION_PLAN | Duyệt plan |
| 3 | [start-wave](start-wave.md) | IMPLEMENTATION_PLAN | Mở wave + sync matrix từ roster |
| 4 | [start-dev](start-dev.md) | IMPLEMENTATION | Dev theo boundary |
| 5 | [review-dev](review-dev.md) | SELF_REVIEW | Self-review code + coverage |
| 6 | [dev-handoff](dev-handoff.md) | SPECIALIST_TESTING | Dev → QA (BE≥80%, FE≥60%) |
| 7 | [test-plan](test-plan.md) | SPECIALIST_TESTING | `tracking/waves/{wave}/test-cases.md` |
| 8 | [test-execute](test-execute.md) | RELEASE_CANDIDATE (pass) / BUG_LOGGING (fail) | Auto test only |
| 9 | [release](release.md) | DONE | `tracking/waves/{wave}/release-notes.md` |
| 10 | [end-wave](end-wave.md) | **MANUAL_TEST** | Soft close — giữ infra, ship UAT |
| 11 | [done-wave](done-wave.md) | BOOTSTRAP | Hard close — teardown + reset |

## Fail / nhánh phụ

| # | Command | Khi nào | Stage |
|---|---------|---------|-------|
| 12 | [fix-bugs](fix-bugs.md) | Auto fail (`test-execute`) hoặc manual fail (`MANUAL_TEST`) | FIX_MANUAL_BUGS |
| 13 | [retest](retest.md) | Sau fix — smart route auto/manual | SPECIALIST_TESTING hoặc MANUAL_TEST |

## Side commands

| # | Command | Khi nào |
|---|---------|---------|
| 14 | [apply-cr](apply-cr.md) | Thay đổi scope → intake amendment |
| 15 | [register-boundary](register-boundary.md) | Boundary ngoài roster (rare) |
| 16 | [show-state](show-state.md) | Inspect STATE.json |

## Quy tắc

- Sau sửa file trong `commands/`: chạy `py scripts/sync_commands.py` (propagate sang `.claude/`, `.cursor/`)
- Mỗi command 2 lệnh: `build_command_prompt.py <cmd>` (spawn) + `harness.py <cmd> complete` (gate + transition)
- Check `harness.py state` để xem `workflow.allowed_next` — KHÔNG sửa STATE tay
