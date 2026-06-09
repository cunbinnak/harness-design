---
name: bug-logging
description: Ghi bug vào 1 file bugs.md theo format gate parse được, để truy vết + chặn end-wave.
---

# Bug Logging Skill

## Khi load
`test-execute-agent` (bug `origin: auto`) và `/fix-bugs` chain (bug `origin: manual` từ MANUAL_TEST).

## Output: `tracking/wave-{N}/bugs.md` (1 FILE chung — **format BẢNG, mỗi bug = 1 HÀNG**)
Template: `tracking/_templates/TEMPLATE.bugs.md`. Log bug = **append 1 row** vào bảng.

Cột (gate `no_open_bugs` đọc cột `status` + `BUG`):

```markdown
| BUG | title | status | origin | sev | boundary | TC | AC | reproduce | expected | actual | error log | root cause | fix |
|-----|-------|--------|--------|-----|----------|----|----|-----------|----------|--------|-----------|------------|-----|
| BUG-007 | {tiêu đề} | open | auto | high | {boundary} | TC-XXX | FEAT-N:AC-M | `{lệnh}` | {kỳ vọng} | {thực tế} | `{excerpt}` (TC-XXX.log) | _(fix điền)_ | _(fix điền)_ |
```

- `BUG` id tăng dần `BUG-NNN`; `status`: `open|in_progress|fixed|closed|wontfix`; `origin`: `auto|manual|framework`; `sev`: `high|medium|low`.
- **error log** = excerpt stack/assertion fail, copy từ `test-logs/{TC}.log` — tín hiệu để fix định vị root cause, KHÔNG để fix đoán.
- Cell nhiều dòng → giữ ngắn 1 dòng (dùng `code` inline); chi tiết dài để trong `test-logs/`.

## Quy ước
1. `status` mở (`open`/`in_progress`) → gate `end-wave` (`no_open_bugs`) **chặn** soft-close.
2. `origin`: `auto` từ test-execute, `manual` từ UAT (MANUAL_TEST), `framework` từ review tooling (vd axe-core).
3. Sau fix: set ô `status` = `fixed` rồi `closed`; thêm regression `TC-R*` vào registry, ghi vào cột `fix`.
4. **Row `origin: auto` BẮT BUỘC đủ tín hiệu cho fix Mode A**: `TC` (detected_in) + `AC` (ac_violated, lấy từ `TC.ac` registry) + `error log` (excerpt `test-logs/{TC}.log`) + reproduce/expected/actual. Thiếu → fix phải đoán = sai.
5. Findings `/review-dev` **KHÔNG** log vào đây (ephemeral, fix ngay trong loop — Mode B).

## Done
- Mỗi bug 1 row có `BUG-NNN` + `status` (gate parse được) + đủ cột; row `auto` đủ TC/AC/error-log.
