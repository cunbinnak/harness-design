---
name: domain-ba
description: "DOMAIN ba-author: viết BUSINESS Business-rule/Persona (plain VN) vào docs/domain/. Loop tới khi OK + hỏi 'Câu hỏi cho Author' ngay. KHÔNG approve/translate ở đây."
argument-hint: "<BR|PERSONA>  (vd: /domain-ba BR)"
when_state: [DOMAIN_AUTHORING, DESIGN]
sets_stage: DOMAIN_AUTHORING
spawn:
  agent: "domain-ba-agent"
  skills: [domain-ba]
gates: [{type: non_empty, field: mode}]
---

# /domain-ba

> **A1 — lớp BUSINESS.** ba-author viết Business-rule/Persona bằng **ngôn ngữ nghiệp vụ thuần** (no jargon) vào `docs/domain/{business-rules,personas}/`. Ký + dịch là bước RIÊNG sau.

## Flow (complete-before-spawn)
1. `py scripts/harness.py domain-ba complete '{"mode":"BR"}'` (transition/self-loop — STATE đúng stage để phase-lock cho agent ghi `docs/domain/`).
2. `py scripts/build_prompt.py domain-ba --mode BR` → **spawn domain-ba-agent bằng output này** (E-6).
3. Agent: author business doc → **hỏi NGAY "Câu hỏi cho Author"** → **loop tới khi OK** → `status: DRAFT`.

## Mode
`BR` · `PERSONA` (EPIC/FEATURE/JOURNEY dùng `/domain-po`).

## Back-edge
Gọi được **từ DESIGN** khi lùi sửa BR/Persona đã phase-lock.

## Sau khi viết xong cả bộ
`/domain-approve <id|all>` → `/domain-translate` → `/domain-end` → DESIGN.

## Forbidden
- Jargon kỹ thuật trong business doc (gate `domain_no_jargon` chặn lúc ký). Tự approve/translate. Spawn prompt tay (E-6).
