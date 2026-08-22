---
name: dogfood
description: "Dùng thử hệ ĐANG CHẠY bằng 6 lăng kính persona, hai đợt theo trạng thái DB — thay cho MANUAL_TEST thủ công. Ghi bug origin=manual, KHÔNG fix."
argument-hint: "(không arg)  ·  hoặc <edge|newbie|picky|rushed|breaker|mobile> để chạy lại một vai"
when_state: [MANUAL_TEST]
sets_stage: MANUAL_TEST
spawn:
  agent: "dogfood-{lens}-agent (6 vai, 2 đợt x 3 vai)"
  skills: [dogfood, bug-logging]
gates: [{type: health_proof}]
---

# /dogfood — "tự dùng trước khi bảo là xong"

Stage MANUAL_TEST, sau chốt chạy test của `/run-wave`. **Không đổi stage** — chạy lại được bao nhiêu lần tuỳ ý.

## Vì sao có lệnh này

Chốt chạy test của `/run-wave` chỉ chạy **test-case đã viết**, nên nó chỉ tìm được thứ ai đó đã nghĩ ra trước. MANUAL_TEST sinh ra để bù đúng khoảng đó — chỗ con người ngồi chọc vào hệ và thấy thứ không ai viết TC cho. Lệnh này tự động hoá đúng việc ngồi chọc đó, không thay thế nó.

Thứ dogfood tìm được mà registry không: cảnh rỗng không nói gì · lỗi bị nuốt im lặng · bấm hai lần ra hai bản ghi · vai A chạm được dữ liệu vai B · nút chính tràn khỏi màn hình nhỏ.

## Điều kiện vào (gate `health_proof`)

Hệ phải **đang chạy thật** — `tracking/wave-{N}/health-proof.json` do `capture_infra_proof.py` sinh. Hệ chết → STOP, chạy lại `/run-wave` (chốt dựng chạy thật). **Không dogfood ảo**: một lượt dogfood trên hệ không chạy còn tệ hơn không chạy lượt nào, vì nó để lại vết "đã kiểm".

Cần thêm, thiếu thì STOP: `docs/discovery/persona-pool.md` có **ma trận vai × hành động** (danh sách phép thử của vai `breaker`) + bảng **gán 6 vai ↔ persona + đợt**. Cả hai là output gate D1 nên bình thường đã có.

## Workflow

1. Đọc `health-proof.json` lấy URL/endpoint thật — **không đoán**.
2. Đọc `persona-pool.md`: persona, ma trận quyền, bảng gán vai ↔ đợt. Không có bảng gán → mặc định mọi vai đóng persona chính.
3. **Đợt 1 (DB SẠCH)** — spawn 3 vai trong MỘT lượt: `edge` · `newbie` · `picky`.
4. **Đợi đủ 3 vai trả kết quả**, rồi **seed lại** dữ liệu mẫu.
5. **Đợt 2 (DB CÓ DỮ LIỆU)** — spawn 3 vai trong MỘT lượt: `rushed` · `breaker` · `mobile`.
6. Gộp phát hiện → soi **dấu hiệu dogfood giả** (skill `dogfood`) → vai nào dính thì cho chạy lại vai đó.
7. Ghi bug vào `tracking/wave-{N}/bugs.md` qua skill `bug-logging`, `origin=manual`.
8. Báo user tổng hợp. Có bug → `/run-wave` (tự sửa + re-test). Sạch → `/next-wave`.

Có arg (`/dogfood breaker`) → chỉ chạy lại vai đó, bỏ qua chia đợt.

## Vì sao chia hai đợt

Không phải để dàn tải. **Các vai dùng chung một hệ và một DB**: `breaker` đổ dữ liệu bậy và `rushed` tạo bản ghi trùng ngay giữa lúc `newbie` đang nhìn màn, nên người này thấy cảnh của người kia. Nặng nhất là **trạng thái rỗng — thứ `edge` coi là quan trọng nhất — chết ngay khi bất kỳ vai nào tạo bản ghi đầu tiên**.

Ba ràng buộc cứng: tối đa **3 vai một đợt** · **không mở đợt 2 khi đợt 1 chưa xong** · **giữa hai đợt phải seed lại**.

## Mỗi vai phải nhận gì

| # | Nội dung | Thiếu thì |
|---|---|---|
| 1 | URL/endpoint thật từ health-proof | vai không thử được |
| 2 | **Persona được giao** — chân dung + năng lực + luồng chính | vai thử như "người dùng nói chung" |
| 3 | Luồng lõi + AC của wave | không biết đúng/sai theo gì |
| 4 | `breaker`: ma trận đầy đủ + tài khoản từng vai | không có danh sách phép thử |
| 5 | `picky`: màn liên quan + `design-tokens.css` | không có gì để đối chiếu |

## Bằng chứng bộ ba — không có thì không tính

```
Tôi đã làm    : <thao tác chính xác — URL, dữ liệu đã gõ, nút đã bấm>
Tôi thấy      : <thứ hiện ra / mã lỗi / response thật>
Tôi mong đợi  : <thứ lẽ ra phải xảy ra + dẫn về AC/FEAT/ô ma trận>
```

Thiếu vế đầu = suy từ code chứ chưa chạy. Vế cuối không dẫn được về tài liệu = ý kiến cá nhân, không phải bug.

## Forbidden

- **KHÔNG fix** — ghi bug rồi dừng. Fix ở chốt sửa bug của `/run-wave` để nhân quả rõ ràng.
- **KHÔNG sửa `test-case-registry.md`** cho khớp thứ vừa thấy.
- **KHÔNG sửa doc spec** — phase-lock chặn; sửa spec cho khớp code là đúng anti-pattern harness sinh ra để chống.
- **KHÔNG teardown infra** — giữ UP cho lượt sửa bug + re-test. Teardown khi hết WAVE-SEQUENCE (`/next-wave`).
- Vai dogfood **KHÔNG hỏi user** — trả phát hiện + đề xuất, quyền quyết ở phiên chính.

## Crash / resume

Re-run `/dogfood` (hoặc `/dogfood <vai>`). Bug đã ghi không ghi lại — `bug-logging` đối chiếu trước khi append.
