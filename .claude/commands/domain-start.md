---
name: domain-start
description: "DOMAIN (clone ADLC, chia nhỏ product): author Epic/Feature/Journey (po) + Business-rule/Persona (ba) THẲNG vào docs/architecture/. Spawn agent theo mode."
argument-hint: "<EPIC|FEATURE|JOURNEY|BR|PERSONA>  (vd: /domain-start FEATURE)"
when_state: [DOMAIN_AUTHORING]
sets_stage: DOMAIN_AUTHORING
spawn:
  agent: "domain-po-agent (EPIC/FEATURE/JOURNEY) | domain-ba-agent (BR/PERSONA)"
  skills: [domain-po, domain-ba]
gates: [{type: non_empty, field: mode}]
---

# /domain-start

> **Clone ADLC DOMAIN** (chia nhỏ product), adapt single-repo: author **thẳng vào `docs/architecture/`** (KHÔNG docs/domain riêng, KHÔNG translate — đó là plumbing multi-repo). Vào DOMAIN từ DISC_D3 qua `/discovery-end D3`.

## Mục đích
Spawn agent author product chia nhỏ theo mode (self-loop trong DOMAIN_AUTHORING).

| Mode | Agent / skill | Output |
|---|---|---|
| EPIC | domain-po-agent / `domain-po` | `docs/architecture/epics/EP-*.md` |
| FEATURE | domain-po-agent / `domain-po` | `docs/architecture/feat/FEAT-*.md` (AC BDD) |
| JOURNEY | domain-po-agent / `domain-po` | `docs/architecture/journeys/JOURNEY-*.md` |
| BR | domain-ba-agent / `domain-ba` | `docs/architecture/business-rules/BR-*.md` (≥2 ví dụ) |
| PERSONA | domain-ba-agent / `domain-ba` | `docs/architecture/personas/PERSONA-*.md` |

> Wireframe = UX = `docs/architecture/ux/` (DESIGN lo) — KHÔNG phải mode DOMAIN.

## Workflow
1. Parse `$1` = mode (EPIC|FEATURE|JOURNEY|BR|PERSONA).
2. Run `py scripts/build_prompt.py domain-start --mode $1`.
3. Spawn agent (skill tự load + đọc boot sequence + agent spec `agents/domain-{po|ba}-agent.md`).
4. Author product-level (AC BDD / business rule), status DRAFT → user duyệt → APPROVED.
5. Self-loop: gọi `/domain-start <mode>` lặp để author thêm Epic/Feature/Journey/BR/Persona.

## State semantics
- DISC_D3 → DOMAIN_AUTHORING qua `/discovery-end D3` (gate D3). 
- DOMAIN_AUTHORING + domain-start → self (author thêm). Sang DESIGN qua `/domain-end` (gate).

## Forbidden
- Author ngoài owned_paths (po: epics/feat; ba: business-rules). Sửa design docs (hld/api/...) — DESIGN.
- Chi tiết kỹ thuật (contract/endpoint/schema) trong AC — để DESIGN. Tạo `knowledge-base/*.yaml`. Set APPROVED tự ý.

## Sau khi agent confirm
"Mode $1 xong. Author thêm: `/domain-start <EPIC|FEATURE|JOURNEY|BR|PERSONA>`. Đủ (≥1 epic + ≥1 feat + ≥1 BR) → `/domain-end` (gate → DESIGN)."
