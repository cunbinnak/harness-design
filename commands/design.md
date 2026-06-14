---
name: design
description: "Technical design (stage DESIGN, self-loop): spawn solution-architect → ADR/HLD/API/data-model/UX/events/integrations. Chạy lại để THẢO LUẬN/REFINE. Advance sang PLAN bằng /design-end."
argument-hint: "(không cần arg)"
when_state: [DESIGN]
sets_stage: DESIGN
spawn:
  agent: solution-architect-agent
  skills: [technical-design]
gates: []
---

# /design

> Technical design — skill `technical-design`, stage sau DOMAIN. Input = product (epic/feat/BR/journey/persona ở docs/architecture/) + charter (Discovery D3). **Self-loop**: chạy `/design` bao nhiêu lần tuỳ ý để thảo luận/chỉnh sửa với agent; chỉ `/design-end` mới sang PLAN.

## Workflow
1. Run `py scripts/build_prompt.py design`.
2. Spawn solution-architect-agent (skill `technical-design`).
3. Agent produce per boundary: ADR (≥3), HLD, API, data-model (backend), UX (FE), events; + integrations (≥1) + infra/docker-compose skeleton. Iterate interactive với user.
4. `py scripts/harness.py design complete '{}'` = **self-loop DESIGN→DESIGN** (re-spawn refine — KHÔNG advance, KHÔNG gate). Chưa vừa ý → cứ chạy lại `/design`.
5. Khi user OK TOÀN BỘ → `/design-end` (verify gate → DESIGN→PLAN).

## Sau khi vừa ý
`/design-end` — verify gate per-boundary completeness → DESIGN→PLAN, rồi `/plan`.

## Forbidden
- Sửa product (epic/feat/BR) — đó là DOMAIN. Code trong services/. Tự đổi stage tay. Advance bằng `/design` (phải dùng `/design-end`).
