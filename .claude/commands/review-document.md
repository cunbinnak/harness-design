---
name: review-document
description: "Revision loop. User feed feedback, agent revise doc. Lặp đến khi user OK"
argument-hint: "\"<feedback>\" [--file path]  (vd: \"FEAT-002 AC quá mơ hồ\" --file docs/architecture/feat/FEAT-002.md)"
when_state: [REVIEW]
sets_stage: REVIEW
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

**Không argument** (sanity-check mode — gap/mâu thuẫn/độ-phủ):
```
/review-document
```
- Agent soi TOÀN BỘ doc (discovery + domain + design + plan) tìm **gap / mâu thuẫn / thiếu độ phủ năng lực** → ghi `tracking/doc-review-findings.md` (DR-NNN + severity).
- KHÔNG sửa doc nguồn.
- Gate `/approve-document` chặn nếu file còn gap **BLOCKER/MAJOR** open → ép vá trước khi start-wave.

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

- State KHÔNG đổi (REVIEW → REVIEW).
- Mỗi call xử lý feedback rồi revise doc (STATE.json chỉ giữ trạng thái hiện tại — không log feedback).
- User có thể chạy `/review-document` không giới hạn lần.

## Forbidden

- Set `approved=true` — đó là `/approve-document`.
- Sửa file ngoài `docs/architecture/`, `docs/plans/`, `harness/SERVICE-BOUNDARY-MATRIX.json`.
- Spawn sub-sub-agent (recurse).
- Skip verify sửa đúng — phải re-read file sau Edit.

## Sanity-check mode (no argument) — gap / mâu thuẫn / thiếu độ phủ

Khi user gọi `/review-document` không argument, agent soi TOÀN BỘ doc theo **5 lens** (chi tiết build_prompt §SANITY-CHECK TASK):
1. **Độ phủ năng lực (chính):** `capability-map` + nhu cầu persona + journey → mọi năng lực có FEAT phủ. Năng lực NỀN đương nhiên cần (auth/đăng nhập/cấp token, phân quyền, multi-tenant, xử-lý-lỗi) mà KHÔNG có FEAT → **BLOCKER** (bắt 'thiếu luồng login' trước khi vào build).
2. **Mâu thuẫn cross-doc** — FEAT vs BR · AC vs api/data-model · HLD vs PROJECT · MATRIX vs BOUNDARY-MAP.
3. **AC testable** — Cho/Khi/Thì đo được, có non-happy-path.
4. **Cross-ref integrity** — epic↔feat↔BR↔journey↔persona không dangling.
5. **Câu hỏi cho Author chưa chốt**.

Output → `tracking/doc-review-findings.md` (DR-NNN + severity + status; **LUÔN ghi kể cả 0 gap**). KHÔNG sửa doc nguồn.

> **Gate `doc_review` @ `/approve-document`:** thiếu file (review chưa chạy) hoặc còn gap BLOCKER/MAJOR open → **chặn approve**. Vá qua revision mode (`/review-document "<feedback>"`) hoặc lùi `/domain-po`·`/domain-ba` author bổ sung (→ `/domain-approve` → `/domain-translate`); set row `status=resolved`. Edge → `force:true,reason` (audit).

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
