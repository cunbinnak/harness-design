---
name: run-wave
description: "Chạy wave một mạch 7 chốt: dựng → code → review → chạy thật → sinh test → chạy test → dogfood. Gate đỏ thì dừng đúng chốt đó."
argument-hint: "<N> (lần đầu mở wave N)  ·  không arg = chạy tiếp wave đang mở"
when_state: [REVIEW, WAVE_OPEN, DEV, REVIEW_DEV, DEV_HANDOFF, TEST_PLAN, TEST_EXECUTE, MANUAL_TEST]
spawn:
  agent: "start-wave-agent · dev-{prefix}-{boundary}-agent · review-{kind}-agent · dev-handoff-agent · test-plan-agent · test-execute-agent · dogfood-*-agent"
gates: "mỗi chốt giữ gate cũ của nó — py scripts/gates.py --list"
---

# /run-wave

Không arg → chạy tiếp từ chốt đang đứng (suy từ `stage`).

| # | Chốt | `harness <id> complete` |
|---|---|---|
| 1 | Dựng wave | `start-wave` |
| 2 | Code từng boundary (tuần tự) | `start-dev` |
| 3 | Review tới sạch — per-boundary **rồi** bug-hunt cả wave | `review-dev` |
| 4 | Dựng chạy thật | `dev-handoff` |
| 5 | Sinh test case | `test-plan` |
| 6 | Chạy test | `test-execute` |
| 7 | Dogfood 6 vai | `dogfood` |

> Gate từng chốt: `py scripts/gates.py --list` (SoT = `GATE_RULES`; đừng chép vào đây — bản chép trôi ngay lần đổi gate kế).

Xong chốt 7 → dừng ở `MANUAL_TEST`. Còn TC đỏ / dòng `sửa ngay` → hành lang tự sửa (spawn fix tuần tự → `test-execute` lại). Sạch + UAT ký → `/next-wave`.

## Luật

1. Chốt đỏ → **DỪNG tại đó**, báo gate nào đỏ, thiếu gì. KHÔNG bỏ qua, KHÔNG `force`.
2. Chốt 2 lặp **tuần tự** từng boundary; xong hết mới sang chốt 3.
2b. **Chốt 3 có HAI lượt.** Lượt 1: `review-{kind}-agent` từng boundary (đi từ code lên, hỏi *code này có vấn đề gì*). Lượt 2 sau khi mọi boundary sạch: `bug-hunter-agent` **một lần cho cả wave** (`build_prompt.py bug-hunt` — đi từ tài liệu xuống, hỏi *thứ đã hứa có ở đây không*). Bỏ lượt 2 thì **FEAT giao cho boundary A mà A không code sẽ im lặng biến mất**: không có code thì không có gì để review. Cùng sổ findings, cùng gate.
3. **Chốt 2 mở đầu bằng CHALLENGE**: một câu hỏi khó từ spec thật (mâu thuẫn hai AC · ca biên HLD §6.1 · ô `cấm` trong ma trận · surface `BC-LEDGER §1` sắp đụng), trả lời **chỉ từ spec**, tự chấm. **FAIL = không được code.** PASS → ghi `tracking/challenge-log.md`.
4. **Wave ≥2 — tôn trọng wave trước**: `archive/wave-*/DELIVERED.md` là hợp đồng. Chỉ được **THÊM** vào surface đã giao (endpoint · shape · cột · khoá cache · event · format export); buộc phải phá → **DỪNG, ghi blocker, báo user**, không tự quyết.
5. Spawn bằng `py scripts/build_prompt.py <chốt> …`, nguyên văn output.

## Forbidden

- Bỏ qua chốt vì "chắc xanh rồi" — gate là thứ trả lời câu đó.
- `force: true` khi user không chỉ đạo tường minh.
- Teardown infra giữa hành lang (chốt 4 dựng lên cho chốt 5-7 dùng).
- Sửa doc spec cho khớp code (phase-lock chặn).
