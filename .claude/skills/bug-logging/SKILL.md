---
name: bug-logging
description: Ghi nhận bug có cấu trúc để truy vết.
---

# Bug Logging Skill

## Hoạt động

1. Tạo file bug trong `tracking/waves/{wave-id}/bugs/BUG-{n}-{short-name}.md` — dùng [`tracking/_templates/TEMPLATE.bug.md`](../../tracking/_templates/TEMPLATE.bug.md).
2. Field `origin: auto | manual` quyết định smart routing của `retest`.
3. Liên kết tới failure mode / FEAT:AC nếu có.

## Done

- Bug có bước tái hiện, mức độ nghiêm trọng, và owner.
