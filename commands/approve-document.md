---
name: approve-document
description: "User mark doc OK (approved=true) + stamp status APPROVED/ACTIVE vào doc design/contract (approve_document.py). KHÔNG đổi state. Cho phép /run-wave"
argument-hint: "(no arguments)"
when_state: [REVIEW]
sets_stage: REVIEW
spawn:
  agent: null
  skills: []
gates: [{type: doc_review}, {type: doc_stamped}, {type: flag, field: approved, expected: true}]
---

# /approve-document

## Mục đích

User explicit approve toàn bộ intake artifacts sau khi đã review (qua `/review-document` revision loop) và happy. Command này KHÔNG spawn sub-agent (instant action): set `approved=true` trong STATE **và stamp trạng thái duyệt vào frontmatter doc** qua `py scripts/approve_document.py` — adr/hld/data-model/ux/integrations → `status: APPROVED`; api/events (contract) → `status: ACTIVE` (DEPRECATED giữ nguyên). Không chạy script = gate `doc_stamped` chặn (doc duyệt rồi mà vẫn hiện DRAFT = approve chay).

Sau khi approved → có thể chạy `/run-wave <N>` (gate check `approved=true`).

> Lifecycle status theo lớp: business `docs/domain` ký ở bước ký của `/domain` (`APPROVED`); eng product (epics/feat/BR) = `TRANSLATED→ENRICHED`; design/contract = stamp ở ĐÂY; plans giữ `PLANNED` (lifecycle wave: IN_PROGRESS/COMPLETED do wave chạy).

## Gate `doc_review` (ép sanity-check trước approve)

`scripts/gates.py check_doc_review` đọc `tracking/doc-review-findings.md` (do `/review-document` no-arg ghi):
- **Thiếu file** → doc-review sanity-check CHƯA chạy → **chặn** (chạy `/review-document` no-arg trước).
- Còn gap **BLOCKER/MAJOR** `status` open → **chặn** (vá qua revision loop hoặc lùi `/domain` → ký → dịch).
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
   
   Sau approve, /run-wave sẽ được phép. Gõ 'yes' để confirm, 'no' để cancel."
3. Đợi user reply.
4. Nếu user "yes":
   - Run: py scripts/approve_document.py        (stamp status APPROVED/ACTIVE vào doc design/contract)
   - Run: py scripts/harness.py approve-document complete '{"approved":true}'   (gate doc_stamped verify stamp)
   - Báo user: "Approved. Chạy /run-wave 1 để mở wave đầu tiên."
5. Nếu user "no":
   - Báo: "Cancelled. Tiếp tục /review-document nếu cần chỉnh."
```

## State semantics

- State KHÔNG đổi (REVIEW → REVIEW).
- Set `approved=true` trong STATE qua complete evidence.
- `/run-wave` gate check `approved=true` ở chốt dựng wave → pass.

## Forbidden

- Spawn sub-agent — command này là pure action.
- Stamp tay frontmatter — dùng `scripts/approve_document.py` (idempotent, re-run sau mỗi vòng revision).
- Auto approve without user confirm — phải explicit "yes".

## Sau approve

Allowed commands ở REVIEW state:
- `/run-wave <N>` → chốt 1 transition REVIEW → WAVE_OPEN, materialize.
- `/review-document` vẫn allow (nếu user reconsider, revise thêm).
