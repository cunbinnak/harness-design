---
name: plan
description: "Implementation plan (stage PLAN→REVIEW): spawn program-planner → WAVE-SEQUENCE + wave-{N} + materialize MATRIX + KG skeleton. Gate: WAVE-SEQUENCE + MATRIX + wave files + KG."
argument-hint: "(không cần arg)"
when_state: [PLAN]
sets_stage: REVIEW
spawn:
  agent: program-planner-agent
  skills: [implementation-plan]
gates: [{type: plan_gate}, {type: planning_lint}, {type: plan_integrity}, {type: matrix_coherence}, {type: api_transport}, {type: wave_sequence_lint}]
---

# /plan

> Implementation plan — tái dùng skill `implementation-plan` (intake step 4 cũ), giờ là stage riêng sau DESIGN.

## Workflow
1. Run `py scripts/build_prompt.py plan`.
2. Spawn program-planner-agent (skill `implementation-plan`).
3. Agent produce: `docs/plans/WAVE-SEQUENCE.md` + `wave-{N}.md` (mọi wave) + materialize MATRIX (`py scripts/materialize_matrix.py`, ALLOW_STAGES có PLAN) + KG skeleton per boundary.
4. Iterate với user tới khi confirm.
5. PASS gate → `py scripts/harness.py plan complete '{}'` → PLAN→REVIEW.
6. Override (user đồng ý): `complete '{"force":true,"reason":"<lý do>"}'` → ghi audit decisions.md.

## Gate
- `plan_gate`: `docs/plans/WAVE-SEQUENCE.md` + `harness/SERVICE-BOUNDARY-MATRIX.json` + ≥1 `docs/plans/wave-*.md` + ≥1 `knowledge-base/*.knowledge-graph.yaml`.
- `planning_lint` + `plan_integrity` + `matrix_coherence`: ref-integrity epic↔feat↔BR + FEAT-id backing + MATRIX phủ đủ boundary đúng kind.
- `api_transport` (G6): `docs/architecture/api/api-*.md` KHÔNG truyền tenant-id qua query string — phải `X-Tenant-ID` header/JWT claim (api template §2), nhất quán mọi endpoint (chống drift kiểu BUG-012 chỗ body chỗ query). Env/ngoại lệ → `force:true,reason`.
- `wave_sequence_lint` (G16): validate `docs/plans/WAVE-SEQUENCE.md` §wave-NNN YAML (port ZIP `wave-sequence-validate.py`): `wave_class`/`wave_strategy` enum · `target_count_per_layer ≤ 3` · strategy layer-purity (horizontal-be cấm FE target, horizontal-fe cấm boundary target) · vertical → FEAT có `parent_epic` · `inherited_active` trỏ file tồn tại. Warning (rare-combo/exit_signal/test_scope coherence) KHÔNG chặn. `force:true,reason` bypass.

## Sau PLAN (vào REVIEW)
Stage → REVIEW. `/review-document` (chỉnh nếu cần) → `/approve-document` → `/start-wave 1`.

## Forbidden
- Sửa design/product docs. Code trong services/. Tự đổi stage tay.
