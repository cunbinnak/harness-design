---
name: domain-end
description: "Đóng DOMAIN authoring: verify gate (≥1 epic + ≥1 feat + ≥1 BR ở docs/architecture/) → DESIGN. Override: force+reason."
argument-hint: "(không cần arg)"
when_state: [DOMAIN_AUTHORING]
sets_stage: DESIGN
spawn:
  agent: "none (instant action — verify gate + transition)"
  skills: []
gates: [{type: domain_gate}, {type: planning_lint}, {type: translation_parity}]
---

# /domain-end

> Đóng DOMAIN authoring. Verify gate trên disk → transition DOMAIN_AUTHORING → DESIGN.

## Workflow
1. Run `py scripts/build_prompt.py domain-end`.
2. Gate (`domain_gate`): ≥1 `docs/architecture/epics/EP-*.md` + ≥1 `docs/architecture/feat/FEAT-*.md` + ≥1 `docs/architecture/business-rules/BR-*.md`. Kèm `planning_lint` (field bắt buộc + ref-integrity) và **`translation_parity`**: mỗi business doc ĐÃ KÝ (docs/domain/) phải có eng doc tương ứng (khớp frontmatter `source`/`domain_source_id`/stem) — translate bỏ sót = chặn; eng doc lớp product (epics/feat/BR) không có `source: docs/domain/...` = MỒ CÔI (tự author né vòng ký) = chặn.
3. PASS → `py scripts/harness.py domain-end complete '{}'` → DOMAIN_AUTHORING → DESIGN.
4. FAIL → KHÔNG complete; author thêm (`/domain-po <EPIC|FEATURE|JOURNEY>` · `/domain-ba <BR|PERSONA>` → `/domain-approve` → `/domain-translate`) rồi `/domain-end` lại.
5. Override (user đồng ý): `complete '{"force":true,"reason":"<lý do>"}'` → ghi audit `tracking/decisions.md`.

## Sau DOMAIN (vào DESIGN)
Product (epic/feat/BR) đã có ở `docs/architecture/`. Stage → DESIGN.
Chạy `/design` (technical-design: ADR/HLD/API/data-model/UX/events/integrations) → `/plan` (WAVE-SEQUENCE+MATRIX+KG) → REVIEW → /approve-document → /start-wave 1.

## Forbidden
- `force` không `reason`. Complete khi gate fail (trừ force có chủ đích). Sửa stage tay.
