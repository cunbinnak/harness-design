# Slash commands — 10 cửa vào

> Sync sang `.claude/commands/` bằng `py scripts/sync_commands.py`. Sửa ở **đây**, không sửa bản sync.

**Lớp vỏ 10 lệnh, ruột giữ nguyên.** Mỗi lệnh gọi một hoặc nhiều `harness <id> complete` nội bộ — state machine (`harness/STATE-MACHINE.json`) và `GATE_RULES` (`scripts/gates.py`) không đổi. Gộp lệnh bỏ việc *gõ* giữa các chốt, không bỏ chốt nào.

Mỗi lệnh **tự suy đang đứng ở đâu** từ `stage`. Không mode, không cờ phải nhớ.

## Vòng đời

| # | Lệnh | Từ stage | Tới stage | Gọi `harness` id nào |
|---|---|---|---|---|
| 1 | [discover](discover.md) | BOOTSTRAP · DISC_D0-D3 | DISC_D0-D3 · DOMAIN_AUTHORING | `discovery-start` (lặp D0→D3) · `discovery-end` |
| 2 | [domain](domain.md) | DOMAIN_AUTHORING · DESIGN | DOMAIN_AUTHORING · DESIGN | `domain-po` · `domain-ba` · `domain-approve` · `domain-translate` · `domain-end` |
| 3 | [design](design.md) | DESIGN · PLAN | DESIGN · PLAN | `design` · `design-ux` (chỉ khi có boundary web/mobile) · `design-end` |
| 4 | [plan](plan.md) | PLAN | REVIEW | `plan` |
| 5 | [review-document](review-document.md) | REVIEW | REVIEW | `review-document` |
| 6 | [approve-document](approve-document.md) | REVIEW | REVIEW | `approve-document` (không transition — mở cổng wave) |
| 7 | [run-wave](run-wave.md) | REVIEW → … → MANUAL_TEST | theo chốt | `start-wave` · `start-dev` · `review-dev` · `dev-handoff` · `test-plan` · `test-execute` · `dogfood` (+ vòng sửa bug) |
| 8 | [dogfood](dogfood.md) | MANUAL_TEST | MANUAL_TEST | `dogfood` — chỉ để **chạy lại** một lăng kính |
| 9 | [next-wave](next-wave.md) | MANUAL_TEST · DONE | WAVE_OPEN · BOOTSTRAP | `end-wave` → `next_wave.py --go` → `next-wave` · hết wave thì `done-wave` |
| 10 | [status](status.md) | mọi stage | — | không gọi gì, không tiêu gate |

**Back-edge** (lùi sửa doc đã phase-lock): `PLAN --/design--> DESIGN` · `DESIGN --/domain--> DOMAIN_AUTHORING` (sửa business → ký lại → dịch lại → tiến lại re-gate).

## Ba thứ đáng nhớ

**Hành lang `/run-wave`** — 7 chốt một mạch. Chốt đỏ thì **DỪNG đúng chốt đó**, báo thiếu gì; không bỏ qua, không `force`. Gọi lại = chạy tiếp từ chốt đang đứng.

**Vòng wave KHÔNG reset** — `/next-wave` snapshot toàn bộ tài liệu → `archive/wave-N/` + đóng gói FEAT/AC đã giao (`DELIVERED.md`), rồi mở wave kế. Kết quả cũ **không bị xoá mà bị đóng dấu wave**, nên gate wave mới tự đỏ lại.

**Wave sau tôn trọng wave trước** — ba lớp: challenge + "chỉ THÊM vào surface đã giao" lúc code · regression suite giữ xanh · `backward_compat` (soi hình dạng) + `dogfood_done` (soi luồng) lúc đóng wave.

## Không còn là lệnh

Bốn thứ đổi từ cửa-người-gõ thành cơ chế agent tự chạy:

| Cũ | Giờ ở đâu |
|---|---|
| `decide` | `py scripts/decide.py`, nhắc trong NON-NEGOTIABLES của mọi prompt spawn. Script từ chối dòng mà lý do không dẫn được về artifact nào |
| `log-bug` | skill `bug-logging` — auto từ test + dogfood; user báo trong chat thì MAIN ghi |
| `fix-bugs` | một chốt trong `/run-wave` |
| `apply-cr` | thay đổi sau ship = wave sau (`/domain` vốn đã là back-edge) |

## Đã gỡ trước đó

- `domain-start` — tách thành lớp business/eng + ký + dịch; nay cả bốn gộp lại trong `/domain`.
- `intake-requirement` — tách thành Discovery → Domain → Design → Plan → Review.
- `release` · `retest` — auto-transition / vòng lặp nội bộ, không cần lệnh.
- `register-boundary` — gộp vào chốt dựng wave.
- `show-state` — nay là `/status`.
