---
name: design
description: "Thiết kế kỹ thuật: ADR + HLD + API + data-model + events + tích hợp, và UX cho boundary có UI (tự suy từ kind, không cần cờ). Lặp refine; --end để chốt sang Plan."
argument-hint: "(không arg — refine)  ·  --end (chốt sang PLAN)"
when_state: [DESIGN, PLAN]
sets_stage: DESIGN
spawn:
  agent: "solution-architect-agent · ux-designer-agent (chỉ khi có boundary web/mobile)"
  skills: [technical-design, ux-design]
gates: [{type: design_gate}, {type: todo_resolved}, {type: contract_graph_parity}, {type: api_transport}]
---

# /design — thiết kế

Gộp `design` + `design-ux` + `design-end`. **Không có cờ `--ux`**: chạy UX hay không là hệ quả của sản phẩm có UI hay không, không phải thứ bạn phải nhớ gõ.

## Tự suy có làm UX không

```
đọc kind của từng boundary trong BOUNDARY-MAP
  kind ∈ {web, mobile}  → BẮT BUỘC lượt UX cho boundary đó
                          (SCREEN-MAP + mockup HTML + design-tokens.css)
  chỉ có backend/bff    → BỎ QUA lượt UX — và NÓI RÕ LÀ BỎ QUA,
                          không im lặng vắng mặt
```

Nói rõ là bỏ qua chứ không vắng mặt im lặng: *"đã kiểm, backend-only nên không cần UX"* khác hẳn *"chưa kiểm gì cả"*, và gate phải phân biệt được hai cái đó.

Kind lấy từ BOUNDARY-MAP — **suy**, không phải khai. Marker viết tay có thể nói ngược sự thật (ghi "không có UI" trong khi vẫn khai một web boundary); kind thì không.

## Hai lượt

| Lượt | Agent | Ra cái gì |
|---|---|---|
| Hệ thống / contract | `solution-architect-agent` | ADR (≥3) · HLD per boundary · API · data-model · events · INTEG (≥1) · docker-compose skeleton |
| UX — chỉ boundary có UI | `ux-designer-agent` | `ux/SCREEN-MAP.md` · `ux-{boundary}.md` · `mockups/{boundary}/*.html` · `design-tokens.css` |

Lặp được: gọi lại `/design` để refine tới khi vừa ý. **`--end` mới advance** — đó là quyết định của người; self-loop không tự biết bạn đã hài lòng chưa.

## Chạy

1. `py scripts/build_prompt.py design` → spawn solution-architect → `py scripts/harness.py design complete`
2. Mỗi FE boundary: `py scripts/build_prompt.py design-ux --boundary <b>` → spawn ux-designer → `py scripts/harness.py design-ux complete`
3. Vừa ý → `py scripts/harness.py design-end complete` (gate → PLAN)

## Gate khi chốt

`design_gate` per-boundary theo kind — backend → HLD + API; web/mobile → HLD + UX. Có web boundary → `ux/design-tokens.css` phải tồn tại (SoT một palette cho mọi FE, không boundary nào tự bịa màu). Cộng `todo_resolved` (field kỹ thuật translator để `TBD (DESIGN)` phải điền xong) · `contract_graph_parity` · `api_transport`.

## Lùi về đây từ PLAN

`/design` gọi được từ `PLAN` (back-edge) khi cần sửa doc design đã phase-lock. Sửa xong `--end` tiến lại (re-gate).

## Forbidden

- Code sản phẩm. Mockup HTML là tài liệu chốt giao diện, không phải nền code.
- Bịa cấu trúc / đặt tên / build tool ngoài skill + ADR.
- Sửa doc business (`docs/domain/`, epics/journeys/personas) — phase-lock chặn, lùi `/domain`.
