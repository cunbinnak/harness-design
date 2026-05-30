---
name: review-document
description: "Revision loop. User feed feedback, agent revise doc. Lặp đến khi user OK"
argument-hint: "\"<feedback>\" [--file path]  (vd: \"FEAT-002 AC quá mơ hồ\" --file docs/architecture/feat/FEAT-002.md)"
when_state: [INTAKE]
sets_stage: INTAKE
spawn:
  agent: review-document-agent
  skills: [business-analysis]
gates: [{type: flag, field: feedback_processed, expected: true}]
---

# /review-document

## Mục đích

Loop revise tài liệu intake theo feedback của user. KHÔNG set approved (đó là `/approve-document`). Lặp lại không giới hạn cho đến khi user happy.

## Input

User truyền feedback sau slash command:

**Free text only:**
```
/review-document "PROJECT.md thiếu NFR security, FEAT-002 AC quá mơ hồ"
```

**Với target file:**
```
/review-document "Cần thêm endpoint POST /orders/{id}/cancel" --file docs/architecture/api/api-order-mgmt.md
```

**Không argument** (sanity check mode):
```
/review-document
```
- Agent đọc TẤT cả artifact intake, trả về issues list cho user xem.
- Không sửa file.
- User dùng kết quả để quyết định feedback gì.

## Workflow

```
1. Parse $ARGUMENTS:
   - Có "--file X" → focus revision vào file X
   - Free text → general feedback, agent self-routing

2. Run: py scripts/build_prompt.py review-document --feedback "$ARGUMENTS"

3. Spawn review-document-agent với prompt
   - Agent đọc feedback
   - Agent đọc file cần sửa (Read tool)
   - Agent edit file theo feedback (Edit tool)
   - Agent verify đã sửa đúng intent
   - Agent return summary "đã sửa X, Y, Z"

4. Báo user: "Đã revise theo feedback. File changed: [list]. Review lại, nếu cần chỉnh tiếp /review-document, nếu OK /approve-document."

5. Auto run: py scripts/harness.py review-document complete '{"feedback_processed":true}'
```

## State semantics

- State KHÔNG đổi (INTAKE → INTAKE).
- Mỗi call ghi 1 entry vào `workflow.history` với feedback summary.
- User có thể chạy `/review-document` không giới hạn lần.

## Forbidden

- Set `approved=true` — đó là `/approve-document`.
- Sửa file ngoài `docs/architecture/`, `docs/plans/`, `harness/SERVICE-BOUNDARY-MATRIX.json`.
- Spawn sub-sub-agent (recurse).
- Skip verify sửa đúng — phải re-read file sau Edit.

## Sanity check mode (no argument)

Khi user gọi `/review-document` không argument:
- Agent đóng vai reviewer, check toàn bộ intake artifacts theo checklist:
  - PROJECT.md scope + NFR + glossary
  - FEAT-*.md AC testable + BR rules
  - ADR ≥ 3 với rationale
  - HLD/API/data-model per boundary đầy đủ
  - WAVE-SEQUENCE + wave-001 có boundaries + features
  - MATRIX có metadata đủ
- Return list issues (KHÔNG sửa file).
- User dùng kết quả này để quyết định feedback gì cho call tiếp theo.

## Output

Báo user:
```
Revision done.
Files changed: [list]
Summary: [tóm tắt]

Review lại docs:
- Cần chỉnh tiếp: /review-document "<feedback>" [--file X]
- OK rồi: /approve-document
```
