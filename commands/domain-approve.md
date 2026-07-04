---
name: domain-approve
description: "KÝ business doc ở docs/domain/ (ký TRƯỚC, dịch SAU). Ký lẻ <id> hoặc toàn bộ (không arg = all). jargon-check + stamp status: APPROVED (script domain_approve.py — gate domain_stamped chặn complete chay)."
argument-hint: "[<EP-/FEAT-/BR-... id>]  (bỏ trống = all)"
when_state: [DOMAIN_AUTHORING]
sets_stage: DOMAIN_AUTHORING
spawn:
  agent: "none (instant action — script stamp)"
  skills: []
gates: [{type: domain_no_jargon}, {type: domain_stamped}]
---

# /domain-approve

> **Chủ-nghiệp-vụ KÝ** business doc đã viết xong (ký cái mình hiểu). Ký rồi mới `/domain-translate`. Ký **lẻ 1 doc** hoặc **toàn bộ** (không arg = `all`).

## Flow (instant action)
1. `py scripts/domain_approve.py <id|all>` — jargon-check `docs/domain/`; **sạch → stamp `status: APPROVED`** vào frontmatter; **còn jargon → REFUSE** (báo doc, sửa cho plain rồi ký lại). **BẮT BUỘC chạy script** — không stamp tay, không bỏ qua bước này.
2. PASS → `py scripts/harness.py domain-approve complete '{"target":"<id|all>"}'` (gate `domain_no_jargon` + **`domain_stamped`** — complete mà file trên disk chưa `status: APPROVED` sẽ bị CHẶN, chống "approve chay" khiến doc vẫn DRAFT) → ở lại DOMAIN_AUTHORING.

## Ví dụ
- `/domain-approve EP-clinic-001` — ký 1 doc.
- `/domain-approve` (không arg) — ký **tất cả**.

## Gate
- `domain_no_jargon`: doc business KHÔNG được chứa jargon kỹ thuật (code/SQL/API-path/class-name/HTTP-status) — giữ chủ-nghiệp-vụ đọc/ký được.
- `domain_stamped`: doc thuộc target phải ĐÃ có `status: APPROVED` trên disk lúc complete (chứng minh script stamp đã chạy). Override: `'{"target":"...","force":true,"reason":"..."}'`.

## Sau khi ký HẾT
`/domain-translate` (gate `domain_signed`: mọi business doc `status: APPROVED`) → dịch sang eng `docs/architecture/`.

## Forbidden
- Ký doc còn jargon (sửa plain trước). Stamp tay frontmatter (dùng script). Translate khi chưa ký hết.
