---
name: apply-cr
description: "Change request amendment. Chỉ allow từ DONE state. Re-enter DOMAIN_AUTHORING (CR feature mới author được epic/feat/BR; CR kiến trúc → /domain-end qua thẳng)."
when_state: ['DONE']
sets_stage: DOMAIN_AUTHORING
spawn:
  agent: "apply-cr-agent"
  skills: []
gates: [{type: non_empty, field: cr_id}]
---

# /apply-cr

## Mục đích

Sau khi wave done, có scope change → tạo CR file → `/apply-cr` → STATE re-enter **DOMAIN_AUTHORING** (đầu pipeline authoring, sau discovery). apply-cr-agent phân tích impact CR; rồi:
- **CR thêm/đổi feature** (product): `/domain-po <EPIC|FEATURE|JOURNEY>` · `/domain-ba <BR|PERSONA>` author business mới (docs/domain) → `/domain-approve` (ký) → `/domain-translate` (dịch eng) → `/domain-end`.
- **CR chỉ đổi kiến trúc/contract** (không feature mới): `/domain-end` qua thẳng (epic/feat/BR cũ đã đủ gate) → DESIGN.
- Tiếp: `/design` → `/design-end` → `/plan` → `/review-document` → `/approve-document` → `/start-wave`.

> Re-enter DOMAIN (không phải DESIGN) để mở rộng feature sau ship mượt. CR cần **boundary MỚI** (chưa có trong BOUNDARY-MAP) → dùng đường `done-wave` → `/discovery-start D3` (charter boundary mới) thay vì apply-cr.

## Build prompt + spawn

```bash
# Tạo CR file trước: tracking/change-requests/CR-001-add-payment.md (theo TEMPLATE)
py scripts/build_prompt.py apply-cr --cr-id CR-001
py scripts/harness.py apply-cr complete '{"cr_id": "CR-001"}'
# STATE.stage -> DOMAIN_AUTHORING
```

## Sau khi vào DOMAIN_AUTHORING

CR feature → `/domain-po`·`/domain-ba` author business vùng CR → `/domain-approve` → `/domain-translate` → `/domain-end` → `/design` → `/design-end` → `/plan` → REVIEW → `/start-wave`. CR kiến trúc-only → `/domain-end` ngay → `/design`...
