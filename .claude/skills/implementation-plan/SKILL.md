---
name: implementation-plan
description: Intake step 4 (program-planner) — WAVE-SEQUENCE + wave-001 + materialize SERVICE-BOUNDARY-MATRIX + KG skeleton per boundary, theo thứ tự phụ thuộc.
---

# Implementation Plan Skill

## Khi load
`/intake-requirement` **step 4** — agent `program-planner-agent`, sau step 3.
Input: `PROJECT.md` + `FEAT-*.md` (AC/BR/boundaries) + design step 3 (ADR/HLD/API/data-model/integrations) + boundary decomposition (kind/stack).

## Deliverable của step 4 (đúng cái command verify)
1. **`docs/plans/WAVE-SEQUENCE.md`** — roadmap tổng: chia FEAT/boundary thành các wave theo thứ tự phụ thuộc; mỗi wave có goal + boundaries + features.
2. **`docs/plans/wave-001.md`** — chi tiết wave đầu: boundaries in scope, FEAT + AC count, thứ tự dev (foundation trước), cross-wave dependency, exit criteria.
3. **`harness/SERVICE-BOUNDARY-MATRIX.json`** — materialize từ decomposition: **≥ 1 boundary**, mỗi boundary `{boundary_id, kind, prefix, tech{language,framework,data_store}, wave, features[], depends_on, consumed_by}` (+ `owned_paths`/`repo_url` nếu có). `features[]` = FEAT-id boundary đảm nhận → là nguồn cho `STATE.wave_features` khi `/start-wave` (mỗi FEAT phải gắn đúng boundary + wave).
4. **KG skeleton per boundary** — `knowledge-base/{prefix}-{boundary}.knowledge-graph.yaml` (entities/business_rules/events placeholder để dev append sau).

> **MATRIX là kernel file** (PreToolUse chặn Write/Edit tay) — KHÔNG ghi bằng Write tool. Materialize qua script:
> ```bash
> py scripts/materialize_matrix.py <boundaries.json>     # hoặc --json '[...]' ; --mode merge ; --dry-run
> ```
> Script gate `stage ∈ {BOOTSTRAP, INTAKE}`, validate (kind hợp lệ, boundary_id unique, depends_on tồn tại) rồi ghi MATRIX + bump revision.

## Phương pháp
1. **Map FEAT → boundary**: từ `boundaries_suggested` (step 2) + decomposition (step 3).
2. **Thứ tự phụ thuộc**: boundary nền (auth/shared) trước; backend trước BFF/FE phụ thuộc nó; xác định `depends_on`.
3. **Chia wave**: nhóm boundary/feature có thể ship cùng nhau thành wave; wave-001 thường = foundation + 1–2 capability mỏng để chạy end-to-end sớm.
4. **Materialize MATRIX** qua `py scripts/materialize_matrix.py` (xem deliverable #3): mỗi boundary 1 entry (kind + stack từ step 3 + wave + depends_on).
5. **KG skeleton**: tạo file KG rỗng-có-cấu-trúc per boundary để dev/review append.

## Flow step 4 (theo command)
- Iterate với user: trình bày WAVE-SEQUENCE + wave-001 + MATRIX → "OK chưa? chỉnh gì?" → sửa. Lặp tới khi user confirm (không giới hạn số vòng).
- Sau user confirm: return RETURN SCHEMA với `user_confirmed: true`, `step: 4` (đây là step cuối → main agent chạy `harness intake-requirement complete '{step:4, all_steps_done:true}'`).

## Quality checklist
- [ ] WAVE-SEQUENCE chia wave theo thứ tự phụ thuộc rõ ràng (không có wave phụ thuộc ngược).
- [ ] wave-001 có boundaries + FEAT + thứ tự dev + exit criteria.
- [ ] MATRIX ≥ 1 boundary; mỗi boundary đủ kind + prefix + tech + wave + depends_on.
- [ ] KG skeleton tạo cho mọi boundary.
- [ ] Mọi FEAT đều được map vào ít nhất 1 wave (không sót).

## Done
- WAVE-SEQUENCE + wave-001 + MATRIX (≥1 boundary) + KG skeleton per boundary (khớp verify intake step 4); user đã confirm → intake complete (state INTAKE).
