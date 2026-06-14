---
name: discovery-end
description: "Đóng 1 Discovery wave: verify exit gate (discovery_gate.py) → transition wave kế. D3 → DOMAIN_AUTHORING. Override: force + reason."
argument-hint: "<D0|D1|D2|D3>  (vd: /discovery-end D0)"
when_state: [DISC_D0, DISC_D1, DISC_D2, DISC_D3]
sets_stage: DISC_D1
spawn:
  agent: "none (instant action — verify gate + transition)"
  skills: []
gates: [{type: discovery_wave}]
---

# /discovery-end

> Đóng wave Discovery hiện tại. Verify gate trên disk (`scripts/discovery_gate.py`) → transition. Đây là điểm enforce: thiếu artifact → block.

## Mục đích
Verify exit gate của wave đang ở (gate lấy theo `state.stage`) rồi transition:
- DISC_D0 → DISC_D1, DISC_D1 → DISC_D2, DISC_D2 → DISC_D3.
- **DISC_D3 → DOMAIN_AUTHORING** (author Epic/Feature/BR vào docs/architecture/).

## Input
`$ARGUMENTS` = D-wave đang đóng (D0..D3). Có thể bỏ — gate tự lấy theo stage hiện tại.

## Workflow
1. Run: `py scripts/build_prompt.py discovery-end --disc-wave $1` (xem hướng dẫn).
2. Chạy `py scripts/discovery_gate.py <wave>` để xem gate pass/fail (đọc message nếu fail).
3. **Gate PASS** → `py scripts/harness.py discovery-end complete '{"wave":"<wave>"}'` → transition wave kế.
   - D3 thêm `service_prefix` từ charter: `'{"wave":"D3","service_prefix":"<kebab>"}'`.
4. **Gate FAIL** → KHÔNG complete. Báo user artifact thiếu; quay lại `/discovery-start <wave>` bổ sung rồi `/discovery-end` lại.
5. **Override** (chỉ khi user đồng ý bỏ qua gate): `py scripts/harness.py discovery-end complete '{"wave":"<wave>","force":true,"reason":"<lý do>"}'` → skip gate + ghi audit `tracking/decisions.md`.

## State semantics
- Transition DISC_D{N} → DISC_D{N+1} (N<3) hoặc DISC_D3 → DOMAIN_AUTHORING.
- Gate `discovery_wave` lấy wave theo `state.stage` (faithful: gate của stage đang rời), fallback `evidence.wave`.

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
