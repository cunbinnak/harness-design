---
name: apply-cr
description: "Change request amendment. Chỉ allow từ DONE state. Re-trigger intake."
when_state: ['DONE']
sets_stage: INTAKE
spawn:
  agent: "apply-cr-agent"
  skills: []
gates: [{type: non_empty, field: cr_id}]
---

# /apply-cr

## Mục đích

Sau khi wave done, nếu có scope change -> tạo CR file -> chạy `/apply-cr` -> re-trigger intake amendment để phân tích lại impact.

## Build prompt + spawn

```bash
# Tạo CR file trước
# tracking/change-requests/CR-001-add-payment.md (theo TEMPLATE)
py scripts/build_prompt.py apply-cr --cr-id CR-001
py scripts/harness.py apply-cr complete '{"cr_id": "CR-001"}'
# STATE.stage -> INTAKE (amendment mode)
```

## Sau khi vào INTAKE

Chạy lại `/intake-requirement` với evidence `{"intake_mode": "amendment", "cr_id": "CR-001"}` để 4 step pipeline phân tích CR.

