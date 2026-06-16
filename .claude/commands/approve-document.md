---
name: approve-document
description: "User mark doc OK (approved=true). KHÔNG đổi state. Cho phép /start-wave"
argument-hint: "(no arguments)"
when_state: [REVIEW]
sets_stage: REVIEW
spawn:
  agent: null
  skills: []
gates: [{type: doc_review}, {type: flag, field: approved, expected: true}]
---

# /approve-document

## Mục đích

User explicit approve toàn bộ intake artifacts sau khi đã review (qua `/review-document` revision loop) và happy. Command này KHÔNG spawn sub-agent (instant action), chỉ set `approved=true` trong STATE.

Sau khi approved → có thể chạy `/start-wave` (gate check `approved=true`).

## Gate `doc_review` (ép sanity-check trước approve)

`scripts/gates.py check_doc_review` đọc `tracking/doc-review-findings.md` (do `/review-document` no-arg ghi):
- **Thiếu file** → doc-review sanity-check CHƯA chạy → **chặn** (chạy `/review-document` no-arg trước).
- Còn gap **BLOCKER/MAJOR** `status` open → **chặn** (vá qua revision loop hoặc lùi `/domain-start`).
- Mọi gap đóng / chỉ MINOR open → pass.

> Mirror `review-dev` `no_open_findings` (cho code) — nhưng cho TÀI LIỆU: bắt **thiếu năng lực nền (vd auth/login)** trước khi commit-to-build. Edge thật → `'{"approved":true,"force":true,"reason":"<lý do>"}'` (bypass + audit `tracking/decisions.md`).

## Input

Không argument.

```
/approve-document
```

## Workflow

```
1. Read harness/STATE.json → verify stage == REVIEW
2. Báo user:
   "Confirm approve toàn bộ artifacts (Discovery + DOMAIN + DESIGN + PLAN)?
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

- State KHÔNG đổi (REVIEW → REVIEW).
- Set `approved=true` trong STATE qua complete evidence.
- `/start-wave` gate check `approved=true` → pass.

## Forbidden

- Spawn sub-agent — command này là pure action.
- Sửa file — không sửa gì, chỉ set flag.
- Auto approve without user confirm — phải explicit "yes".

## Sau approve

Allowed commands ở REVIEW state:
- `/start-wave <N>` → transition REVIEW → WAVE_OPEN, materialize.
- `/review-document` vẫn allow (nếu user reconsider, revise thêm).
