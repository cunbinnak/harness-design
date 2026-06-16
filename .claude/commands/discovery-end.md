---
name: discovery-end
description: "CHỐT Discovery (1 lần, không arg): verify gate D3 (discovery_gate.py) → DOMAIN_AUTHORING. Override: force + reason."
argument-hint: "(không cần arg — chỉ chốt ở DISC_D3)"
when_state: [DISC_D3]
sets_stage: DOMAIN_AUTHORING
spawn:
  agent: "none (instant action — verify gate + transition)"
  skills: []
gates: [{type: discovery_wave}]
---

# /discovery-end

> **Chốt toàn bộ Discovery** (chỉ gọi 1 lần, ở DISC_D3). Verify gate D3 trên disk → DOMAIN_AUTHORING. Điểm enforce cuối: thiếu charter/BOUNDARY-MAP/PROJECT.md → block.
>
> Tiến qua D0→D1→D2→D3 KHÔNG dùng lệnh này nữa — dùng `/discovery-start D{N+1}` (xem `/discovery-start`).

## Mục đích
Verify exit gate D3 (charter + BOUNDARY-MAP + PROJECT.md + service_prefix) rồi transition **DISC_D3 → DOMAIN_AUTHORING** (author Epic/Feature/BR vào docs/architecture/).

## Workflow
1. Chạy `py scripts/discovery_gate.py D3` để xem gate pass/fail (đọc message nếu fail).
2. **Gate PASS** → `py scripts/harness.py discovery-end complete '{"service_prefix":"<kebab>"}'` → DOMAIN_AUTHORING.
3. **Gate FAIL** → KHÔNG complete. Báo user artifact D3 còn thiếu; quay lại `/discovery-start D3` bổ sung rồi `/discovery-end` lại.
4. **Override** (chỉ khi user đồng ý bỏ qua gate): `'{"service_prefix":"<kebab>","force":true,"reason":"<lý do>"}'` → skip gate + ghi audit `tracking/decisions.md`.

## State semantics
- Chỉ 1 transition: DISC_D3 → DOMAIN_AUTHORING. Gate `discovery_wave` lấy wave theo `state.stage` (= D3).

## Sau D3 (vào DOMAIN_AUTHORING)
Báo user:
```
Discovery xong (D0-D3). Stage = DOMAIN_AUTHORING.
PROJECT.md + charter boundaries đã có → author product:
  /domain-start <EPIC|FEATURE|JOURNEY|BR|PERSONA>  (self-loop) → /domain-end
→ /design → /plan → /approve-document → /start-wave 1
```

## Forbidden
- `force` mà không có `reason` (audit trống).
- Complete khi gate fail (trừ force có chủ đích + user đồng ý).
- Sửa stage tay trong STATE.json.
