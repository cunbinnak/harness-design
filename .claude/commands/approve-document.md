---
name: approve-document
description: "User mark doc OK (approved=true). KHÔNG đổi state. Cho phép /start-wave"
argument-hint: "(no arguments)"
when_state: [INTAKE]
sets_stage: INTAKE
spawn:
  agent: null
  skills: []
gates: [{type: flag, field: approved, expected: true}]
---

# /approve-document

## Mục đích

User explicit approve toàn bộ intake artifacts sau khi đã review (qua `/review-document` revision loop) và happy. Command này KHÔNG spawn sub-agent (instant action), chỉ set `approved=true` trong STATE.

Sau khi approved → có thể chạy `/start-wave` (gate check `approved=true`).

## Input

Không argument.

```
/approve-document
```

## Workflow

```
1. Read harness/STATE.json → verify stage == INTAKE
2. Báo user:
   "Confirm approve toàn bộ intake artifacts?
   - PROJECT.md
   - FEAT-*.md (N files)
   - ADR + HLD + API + data-model + UX + events + integrations
   - WAVE-SEQUENCE.md + wave-001.md
   - SERVICE-BOUNDARY-MATRIX.json
   
   Sau approve, /start-wave sẽ được phép. Gõ 'yes' để confirm, 'no' để cancel."
3. Đợi user reply.
4. Nếu user "yes":
   - Run: py scripts/harness.py approve-document complete '{"approved":true}'
   - Báo user: "Approved. Run /start-wave 1 để mở wave đầu tiên."
5. Nếu user "no":
   - Báo: "Cancelled. Tiếp tục /review-document nếu cần chỉnh."
```

## State semantics

- State KHÔNG đổi (INTAKE → INTAKE).
- Set `approved=true` trong STATE qua complete evidence.
- `/start-wave` gate sẽ check `approved=true` trong workflow.history → pass.

## Forbidden

- Spawn sub-agent — command này là pure action.
- Sửa file — không sửa gì, chỉ set flag.
- Auto approve without user confirm — phải explicit "yes".

## Sau approve

Allowed commands ở INTAKE state:
- `/start-wave <N>` → transition INTAKE → WAVE_OPEN, materialize.
- `/review-document` vẫn allow (nếu user reconsider).
- `/intake-requirement` vẫn allow (re-run mode amendment hoặc full).
