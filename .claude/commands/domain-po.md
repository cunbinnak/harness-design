---
name: domain-po
description: "DOMAIN po-author: viết BUSINESS Epic/Feature/Journey (plain VN) vào docs/domain/. Loop tới khi OK + hỏi 'Câu hỏi cho Author' ngay. KHÔNG approve/translate ở đây."
argument-hint: "<EPIC|FEATURE|JOURNEY>  (vd: /domain-po EPIC)"
when_state: [DOMAIN_AUTHORING, DESIGN]
sets_stage: DOMAIN_AUTHORING
spawn:
  agent: "domain-po-agent"
  skills: [domain-po]
gates: [{type: non_empty, field: mode}]
---

# /domain-po

> **A1 — lớp BUSINESS.** po-author viết Epic/Feature/Journey bằng **ngôn ngữ nghiệp vụ thuần** (no jargon) vào `docs/domain/{epics,feat,journeys}/`. Ký (`/domain-approve`) + dịch sang eng (`/domain-translate`) là bước RIÊNG sau.

## Flow (complete-before-spawn)
1. `py scripts/harness.py domain-po complete '{"mode":"EPIC"}'` (transition/self-loop DOMAIN_AUTHORING — STATE đúng stage để phase-lock cho agent ghi `docs/domain/`).
2. `py scripts/build_prompt.py domain-po --mode EPIC` → **spawn domain-po-agent bằng output này** (E-6: KHÔNG tự viết prompt tay).
3. Agent: author business doc → **hỏi NGAY "Câu hỏi cho Author"** (AskUserQuestion) → **loop draft↔user tới khi OK** → `status: DRAFT` (KHÔNG approve).

## Mode
`EPIC` · `FEATURE` · `JOURNEY` (BR/PERSONA dùng `/domain-ba`). Author thêm → gọi lại lệnh.

## Back-edge
Gọi được **từ DESIGN** (DESIGN→DOMAIN_AUTHORING) khi lùi sửa product đã phase-lock; sửa xong `/domain-end` re-gate.

## Sau khi viết xong cả bộ
`/domain-approve <id|all>` (ký) → `/domain-translate` (dịch eng) → `/domain-end` → DESIGN.

## Forbidden
- Jargon kỹ thuật (class/SQL/API/HTTP-status/schema) trong business doc — gate `domain_no_jargon` chặn lúc ký.
- Tự approve/translate. Ghi `docs/architecture/` (đó là eng layer do translate sinh). Spawn bằng prompt tay (E-6).
