---
name: next-wave
description: "Đóng wave hiện tại + mở wave kế. KHÔNG RESET GÌ — snapshot toàn bộ tài liệu, đóng gói FEAT/AC đã giao, đánh dấu kết quả theo wave. Hết WAVE-SEQUENCE thì teardown."
argument-hint: "(không arg)"
when_state: [MANUAL_TEST, DONE]
spawn:
  agent: "end-wave-agent (đóng mềm) · done-wave-agent (teardown khi hết wave)"
gates: [{type: flag, field: uat_signed, expected: true}, {type: test_passed}, {type: no_open_bugs}, {type: features_complete}, {type: dogfood_done}]
---

# /next-wave — khép vòng

Gộp `end-wave` + `done-wave`. Phân nhánh theo **stage**, không theo cờ bạn gõ.

## Vì sao không reset

Reset là mất trí nhớ giữa các wave: wave sau không biết wave trước đã giao gì, nên không tôn trọng được nó. Tài liệu sống tiến hoá liên tục, **không file nào bị xoá**. Hàng rào chống "gate wave mới xanh sẵn nhờ vết wave cũ" chuyển sang hai cơ chế khác:

| | |
|---|---|
| **Đánh dấu** | `test_result` / `review_results` mang dấu wave lúc GHI, gate đối chiếu lúc ĐỌC. Wave mới → tự đỏ lại. **Không bị xoá — bị đối chiếu.** Thiếu dấu → fail-closed |
| **Snapshot** | COPY toàn bộ `docs/` + `knowledge-base/` + `tracking/wave-N/` + STATE/MATRIX/decisions → `archive/wave-N/`. Chép cả ĐẶC TẢ chứ không chỉ thực thi: wave sau lùi `/domain` sửa FEAT thì bản wave cũ vẫn nguyên để đối chiếu |

## Chạy

```bash
py scripts/harness.py end-wave complete '{"uat_signed": true}'   # gate 5 mục → DONE
py scripts/next_wave.py                                          # xem trước
py scripts/next_wave.py --go                                     # snapshot + mở wave kế
py scripts/harness.py next-wave complete '{"wave_n": <N+1>}'     # → WAVE_OPEN
```

Hết WAVE-SEQUENCE → `next_wave.py` báo là hết và **không mở gì**; lúc đó teardown:

```bash
py scripts/harness.py done-wave complete '{"teardown_ok": true}'  # → BOOTSTRAP
```

## `next_wave.py --go` làm gì

| Việc | Vì sao |
|---|---|
| **Cờ đã đóng** — `archive/wave-N/` tồn tại → TỪ CHỐI | Sự tồn tại của thư mục **là** cờ. Đóng hai lần sẽ ghi đè snapshot và mất vết wave đó |
| **Snapshot** — copy hết, không chọn lọc | "Chép doc nào" là loại phán đoán sẽ mục: hôm nay đủ, thêm một loại artifact là sót. ~0.5MB/wave nên chọn lọc chẳng đổi lại được gì |
| **`DELIVERED.md`** — FEAT + AC đã verify, TC nào verify | **Hợp đồng wave sau phải giữ.** Máy derive từ registry + report, KHÔNG phải agent khai |
| **capability-map** — `Wave giao` khớp N → `đã giao` | Trả lời "còn bao nhiêu năng lực chưa giao" từ MỘT file. Khớp theo SỐ nên cắt lát `1 (scaffold), 3 (đầy đủ)` vẫn đúng |
| **Re-arm sổ tương thích ngược** — bỏ tick ĐÚNG §3 | Wave nào rà wave đó. **§1 sổ hợp đồng KHÔNG bị đụng** — surface wave 1 giao vẫn là hợp đồng ở wave 9. Giới hạn đúng §3 chứ không quét cả file: một checkbox ghi chú ở §1/§4 bị bỏ tick oan sẽ chặn đóng wave mà không chỗ nào re-arm lại |
| **Mở wave kế** — chỉ dời con trỏ + boundary/feature từ MATRIX | Không đụng decisions · bugs cũ · knowledge-base · `docs/` |

## Ai đọc `archive/`

| Đọc gì | Ai | Khi nào |
|---|---|---|
| `DELIVERED.md` | prompt dev (`/run-wave` chốt 2) | **TRƯỚC khi sửa dòng nào** của code đã có — chỉ được THÊM vào surface đã giao |
| `DELIVERED.md` | `dogfood-rushed-agent` | lượt regression, wave ≥2 |
| `archive/<wave>/docs/` | khi cần đối chiếu | FEAT bị sửa ở wave sau → bản gốc ở đây |

## Forbidden

- Đóng wave khi gate đỏ. Năm gate ở `end-wave` là điều kiện giao hàng, không phải gợi ý.
- Sửa tay `archive/**`. Đó là hồ sơ; sửa thì nó thành lời kể.
- Xoá `archive/wave-N/` — mất nó là mất cờ "đã đóng", `next_wave.py --go` chạy lại được lần hai.
- Reset tài liệu để "wave mới cho sạch". Sạch ở đây nghĩa là mất trí nhớ.
