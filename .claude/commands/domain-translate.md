---
name: domain-translate
description: "DỊCH business doc (docs/domain/, đã ký) → engineering spec (docs/architecture/). Spawn domain-translator. Gate: mọi business doc đã ký (domain_signed)."
argument-hint: "(không cần arg)"
when_state: [DOMAIN_AUTHORING]
sets_stage: DOMAIN_AUTHORING
spawn:
  agent: "domain-translator-agent"
  skills: [domain-translator]
gates: [{type: domain_signed}]
---

# /domain-translate

> **Cầu nối business → engineering.** Đọc `docs/domain/` (đã KÝ) → sinh eng spec ở `docs/architecture/{epics,feat,business-rules,journeys,personas}/` (BDD AC chuẩn + field/enum/error code + ref-id). GIỮ nguyên Ý nghiệp vụ, THÊM độ chính xác kỹ thuật. KHÔNG bịa scope mới.

## Flow (complete-before-spawn)
1. `py scripts/harness.py domain-translate complete` **chỉ chạy SAU khi dịch xong** — nhưng STATE giữ DOMAIN_AUTHORING (self-loop), gate `domain_signed` verify mọi business doc `status: APPROVED` TRƯỚC.
2. `py scripts/build_prompt.py domain-translate` → **spawn domain-translator-agent bằng output này** (E-6).
3. Agent: foreach business doc → dịch sang eng artifact tương ứng (giữ id, frontmatter `source: docs/domain/<file>`); mơ hồ → hỏi user (≤5 câu), KHÔNG tự quyết scope.
4. `py scripts/harness.py domain-translate complete '{}'`.

## Gate `domain_signed`
MỌI business doc ở `docs/domain/` phải `status: APPROVED` trong frontmatter (ký TRƯỚC, dịch SAU — stamp do `scripts/domain_approve.py`). Còn doc chưa ký → chặn, về `/domain-approve`. Override: `'{"force":true,"reason":"..."}'`.

## Sau khi dịch
`/domain-end` (gate `domain_gate`: eng epic+feat+BR ở `docs/architecture/` tồn tại) → DESIGN.

## Forbidden
- Dịch khi chưa ký hết. Bịa scope/feature không có ở business doc. Sửa business doc (đó là docs/domain). Spawn prompt tay (E-6).
