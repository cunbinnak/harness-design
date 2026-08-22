---
name: run-wave
description: "Chạy wave một mạch: dựng wave → code từng boundary → review tới sạch → dựng chạy thật → sinh test → chạy test → dogfood. Gate đỏ thì DỪNG đúng chốt đó. Gọi lại = chạy tiếp từ chốt đang đứng."
argument-hint: "<N>  (lần đầu mở wave N)  ·  không arg = chạy tiếp wave đang mở"
when_state: [REVIEW, WAVE_OPEN, DEV, REVIEW_DEV, DEV_HANDOFF, TEST_PLAN, TEST_EXECUTE, MANUAL_TEST]
spawn:
  agent: "theo từng chốt — start-wave-agent · dev-{prefix}-{boundary}-agent · review-{kind}-agent · dev-handoff-agent · test-plan-agent · test-execute-agent · dogfood-*-agent"
gates: "mỗi chốt giữ nguyên gate cũ của nó (xem bảng dưới)"
---

# /run-wave — hành lang một mạch

Gộp 7 chốt vốn là 7 lệnh rời. **Không bỏ chốt nào, không bỏ gate nào** — chỉ bỏ việc bạn phải gõ lệnh giữa các chốt đã xanh.

## Hành lang

| # | Chốt | `harness <id> complete` | Gate giữ nguyên |
|---|---|---|---|
| 1 | Dựng wave | `start-wave` | `wave_in_matrix` · `doc_review` · `doc_stamped` |
| 2 | Code từng boundary | `start-dev` (lặp mỗi boundary) | `in_state_list` |
| 3 | Review tới sạch | `review-dev` | **`challenge_passed`** · `all_boundaries_reviewed` · `code_compliance` |
| 4 | Dựng chạy thật | `dev-handoff` | `infra_proof` · `health_proof` · `web_styling` |
| 5 | Sinh test case | `test-plan` | `ui_test_present` · `registry_scope` · `contract_test_present` · `journey_e2e_present` |
| 6 | Chạy test | `test-execute` | `test_evidence` |
| 7 | Dogfood 6 vai | `dogfood` | `health_proof` · 2 đợt |

Xong chốt 7 → dừng ở `MANUAL_TEST`, chờ người: ký UAT rồi `/next-wave`.

## Luật của hành lang

1. **Chốt đỏ → DỪNG NGAY tại đó.** Báo user gate nào đỏ, thiếu gì, sửa ở đâu. **KHÔNG bỏ qua, KHÔNG force**, không nhảy sang chốt sau.
2. **Gọi lại `/run-wave` = chạy tiếp từ chốt đang đứng**, không chạy lại từ đầu. Chốt đang đứng suy từ `stage` trong STATE — không hỏi user.
3. **Còn bug open ở `MANUAL_TEST`** → hành lang tự sửa: spawn fix per bug (tuần tự) → `test-execute` lại → về `MANUAL_TEST`. Đây là chỗ `fix-bugs` cũ nằm.
4. **Mỗi sub-agent spawn bằng `py scripts/build_prompt.py <chốt> …`**, nguyên văn output. KHÔNG tự viết prompt.
5. Chốt 2 lặp **tuần tự** cho từng boundary trong `wave_boundaries`; xong hết mới sang chốt 3.
6. **Chốt 2 mở đầu bằng CHALLENGE**: trước dòng code đầu tiên, dev tự ra một câu hỏi khó dựa trên spec THẬT (mâu thuẫn giữa hai AC · ca biên HLD chưa chặn · ô `cấm` trong ma trận quyền · surface wave trước sắp đụng), trả lời **chỉ từ spec**, tự chấm PASS/FAIL. **FAIL = đọc lại, KHÔNG được code.** PASS → ghi `tracking/challenge-log.md`. review-dev bắt lỗi SAU khi code xong; challenge bắt chỗ *tưởng đã hiểu mà chưa*.

## Chạy

```bash
# lần đầu mở wave N (từ REVIEW, sau /approve-document)
py scripts/harness.py start-wave complete '{"wave_n": N}'

# rồi lần lượt từng chốt — mỗi chốt: build_prompt → spawn → harness complete
py scripts/build_prompt.py start-dev --boundary <b>
py scripts/harness.py start-dev complete '{"boundary": "<b>"}'
...
```

Không arg → đọc `stage` để biết đang ở chốt nào rồi đi tiếp. Có arg `<N>` mà wave chưa mở → bắt đầu từ chốt 1.

## Tôn trọng wave trước (wave ≥ 2)

`build_prompt.py` tự chèn vào prompt dev: `archive/wave-*/DELIVERED.md` — FEAT + AC các wave trước đã verify. Dev **chỉ được THÊM** vào surface đã giao (endpoint, shape, bảng/cột, khoá cache, event, format export); buộc phải phá → **DỪNG, ghi blocker, báo user**, không tự quyết.

## Forbidden

- Bỏ qua một chốt vì "chốt đó chắc xanh rồi" — gate là thứ trả lời câu đó, không phải phán đoán.
- `force: true` để đi tiếp. Force chỉ dùng khi user chỉ đạo tường minh, và ghi audit `tracking/decisions.md`.
- Teardown infra giữa hành lang — chốt 4 dựng lên để chốt 5-7 dùng.
- Sửa doc spec cho khớp code (phase-lock chặn).

## Crash / resume

Gõ lại `/run-wave`. Chốt đã xong không chạy lại (stage đã tiến); chốt dở chạy lại từ đầu chốt đó.
