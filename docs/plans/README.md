# docs/plans — Cấu trúc (đề xuất A, file wave gộp)

```text
docs/plans/
  README.md
  project/                          # cấp dự án
    waves-roadmap.md
    agent-roster.md
  waves/
    wave-001/
      wave.md                       # plan + assignment trong một file
    wave-002/
      wave.md
  _templates/
    waves-roadmap.md
    agent-roster.md
    wave.md
```

| File | Ai tạo | Nội dung |
|------|--------|----------|
| `project/waves-roadmap.md` | Intake bước 4 | Bao nhiêu wave, FEAT theo wave |
| `project/agent-roster.md` | Intake bước 4 | Boundary → 3 agent paths |
| `waves/{wave-id}/wave.md` | Intake: §1 Plan · prepare-dev: §2 Assignment | **Gộp** — tránh tách `plan` / `assignment` ra nhiều file |

## Vì sao gộp `wave.md`?

- Một wave = một nơi đọc (plan + ai làm gì).
- `prepare-dev` chỉ **bổ sung section 2** trong cùng file, không tạo `wave-001-assignment.md` riêng.

## Legacy (không dùng nữa)

- `docs/plans/waves-roadmap.md` (phẳng)
- `docs/plans/project-agent-roster.md`
- `docs/plans/wave-001-plan.md`, `wave-001-assignment.md`

Script `load_wave_roster.py` ưu tiên path mới, fallback path cũ nếu còn file.
