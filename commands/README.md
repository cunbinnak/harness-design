# Commands

Nguồn sự thật: [`harness/COMMAND-GATES.json`](../harness/COMMAND-GATES.json) · Luồng tổng quan: [`COMMAND-FRAMEWORK.md`](COMMAND-FRAMEWORK.md) · Chi tiết: [`SETUP-GUIDE.md`](../SETUP-GUIDE.md)

| # | Command | Ghi chú |
|---|---------|---------|
| 1 | [intake-requirement](intake-requirement.md) | BOOTSTRAP — 4 bước pipeline |
| 2 | [review-document](review-document.md) | Duyệt plan |
| 3 | [start-wave](start-wave.md) | Mở wave + sync matrix |
| 4 | [register-boundary](register-boundary.md) | Tùy chọn — boundary ngoài roster |
| 5 | [start-dev](start-dev.md) | Dev theo boundary (`wave.md` §2 + evidence) |
| 6 | [review-dev](review-dev.md) | Self-review code |
| 7 | [dev-handoff](dev-handoff.md) | Dev → QA |
| 8 | [test-plan](test-plan.md) | Test cases |
| 9 | [test-execute](test-execute.md) | Chạy test → pass/fail |
| 10 | [fix-bugs](fix-bugs.md) | Nhánh khi test fail |
| 11 | [retest](retest.md) | Sau fix |
| 12 | [release](release.md) | RC |
| 13 | [end-wave](end-wave.md) | Đóng wave |
| — | [apply-cr](apply-cr.md) | CR → intake amendment (song song dev) |

Sau sửa file trong `commands/`: `py scripts/sync_commands.py`
