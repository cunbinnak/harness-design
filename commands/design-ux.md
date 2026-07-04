---
name: design-ux
description: "UX/UI design (stage DESIGN, self-loop): spawn ux-designer → ux-{boundary}.md + design-tokens.css cho FE boundary. Chạy lại để REFINE. Tách vai khỏi solution-architect (/design lo hệ thống/contract). Advance sang PLAN bằng /design-end."
argument-hint: "(không cần arg)"
when_state: [DESIGN, PLAN]
sets_stage: DESIGN
spawn:
  agent: ux-designer-agent
  skills: [ux-design]
gates: []
---

# /design-ux

> UX/UI design cho **FE boundary** (kind web/mobile) — agent chuyên môn `ux-designer-agent`, skill `ux-design`. Tách vai khỏi `/design` (solution-architect lo ADR/HLD/API/data-model/events/INTEG). **Self-loop**: chạy lại bao nhiêu lần tuỳ ý để refine; chỉ `/design-end` mới sang PLAN.
>
> **Thứ tự khuyến nghị:** `/design` trước (chốt boundary + `api-{be}.md`) → `/design-ux` (UX consume contract, không bịa endpoint) → lặp xen kẽ nếu cần → `/design-end`.
>
> **Back-edge:** gọi được **từ PLAN** (PLAN→DESIGN) khi cần lùi sửa ux-*.md / design-tokens.css đã phase-lock. Sửa xong `/design-end` re-gate.

## Workflow
1. Run `py scripts/build_prompt.py design-ux`.
2. Spawn ux-designer-agent (skill `ux-design`).
3. Agent produce: `docs/architecture/ux/design-tokens.css` (SoT token — 1 file dùng chung mọi web boundary) + per FE boundary `ux-{boundary}.md` (user flows per FEAT Must, wireframe + component states đầy đủ, API calls khớp `api-{be}.md`, §Visual polish, permission UI, responsive, a11y WCAG 2.1 AA). Iterate với user.
4. `py scripts/harness.py design-ux complete '{}'` = **self-loop DESIGN→DESIGN** (KHÔNG advance, KHÔNG gate).
5. Cả `/design` lẫn `/design-ux` đều vừa ý → `/design-end` (gate `design_gate`: web/mobile→hld+**ux** + **design-tokens.css khi có web boundary** + `todo_resolved`).

## Forbidden
- Sửa ADR/HLD/API/data-model/events/INTEG — đó là `/design`. Sửa product (epic/feat/BR) — đó là DOMAIN (po/ba → ký → translate). Code trong services/. Advance bằng `/design-ux` (phải dùng `/design-end`).
