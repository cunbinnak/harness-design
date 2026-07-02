---
name: plan
description: "Implementation plan (stage PLAN→REVIEW): spawn program-planner → WAVE-SEQUENCE + wave-{N} + materialize MATRIX + KG skeleton. Gate: WAVE-SEQUENCE + MATRIX + wave files + KG."
argument-hint: "(không cần arg)"
when_state: [PLAN]
sets_stage: REVIEW
spawn:
  agent: program-planner-agent
  skills: [implementation-plan]
gates: [{type: plan_gate}, {type: planning_lint}, {type: plan_integrity}, {type: matrix_coherence}, {type: api_transport}, {type: wave_sequence_lint}, {type: contract_graph_parity}]
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
- `planning_lint` + `plan_integrity` + `matrix_coherence`: ref-integrity epic↔feat↔BR + FEAT-id backing + **FEAT mồ côi** (mọi FEAT-*.md phải nằm trong `features[]` của ≥1 boundary — file không boundary nào nhận sẽ KHÔNG BAO GIỜ được build/test; opt-out `status: deferred|dropped`) + MATRIX phủ đủ boundary đúng kind.
- `contract_graph_parity`: đồ thị contract (api-*.md frontmatter `consumers[]` + `INTEG-INT-*.md` consumer/producer + events subscribers) phải KHỚP MATRIX `depends_on`/`consumed_by` cả 2 chiều — id không tồn tại / cạnh contract không có trong MATRIX / cạnh MATRIX không được contract doc nào ghi nhận → chặn (3 nguồn khai 1 sự thật, không để lệch).
- `api_transport`: `docs/architecture/api/api-*.md` KHÔNG truyền tenant-id qua query string — phải `X-Tenant-ID` header/JWT claim (api template §2), nhất quán mọi endpoint (chống drift kiểu BUG-012 chỗ body chỗ query). Env/ngoại lệ → `force:true,reason`.
- `wave_sequence_lint`: validate `docs/plans/WAVE-SEQUENCE.md` §wave-NNN YAML (port ZIP `wave-sequence-validate.py`): `wave_class`/`wave_strategy` enum · `target_count_per_layer ≤ 3` · strategy layer-purity (horizontal-be cấm FE target, horizontal-fe cấm boundary target) · vertical → FEAT có `parent_epic` · `inherited_active` trỏ file tồn tại. Warning (rare-combo/exit_signal/test_scope coherence) KHÔNG chặn. `force:true,reason` bypass.

## Sau PLAN (vào REVIEW)
Stage → REVIEW. `/review-document` (chỉnh nếu cần) → `/approve-document` → `/start-wave 1`.

## Forbidden
- Sửa design/product docs. Code trong services/. Tự đổi stage tay.
