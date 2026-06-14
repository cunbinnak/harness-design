---
name: review-dev
description: "Wave-scoped: review TẤT CẢ service trong wave, mỗi cái theo kind. Review ghi findings; MAIN spawn fix Mode B → re-review tới open_findings==0."
when_state: ['DEV']
sets_stage: REVIEW_DEV
spawn:
  agent: "review-{kind}-agent (mỗi boundary trong wave, theo kind)"
  skills: review-{kind}
gates: [{type: no_open_findings}]
---

# /review-dev

## Mục đích

Review **toàn bộ service trong wave** (sau khi đã `/start-dev` xong từng boundary). Mỗi boundary được review bằng `review-{kind}-agent` đúng kind của nó (backend → review-backend, web → review-web, …). Review-agent **chỉ đánh giá + ghi findings**, KHÔNG tự spawn fix (sub-agent không nest spawn). **MAIN** đọc findings → spawn fix Mode B → re-review tới sạch. **Pass khi MỌI boundary `open_findings==0`.**

## Vị trí trong flow

```
WAVE_OPEN
  → /start-dev order     → DEV   (dev order)
  → /start-dev product   → DEV   (dev product)     # DEV cho phép start-dev tiếp
  → /start-dev web       → DEV   (dev web)
  → /review-dev          → REVIEW_DEV               # review CẢ wave, mỗi cái theo kind
  → /dev-handoff         → DEV_HANDOFF              # gate: mọi boundary pass + coverage theo kind
```

## Build prompt + spawn (wave-scoped)

```bash
# Không --boundary → orchestrator prompt: liệt kê wave_boundaries + kind, hướng dẫn review tuần tự
py scripts/build_prompt.py review-dev
```

Main loop làm theo orchestrator: với MỖI boundary trong `wave_boundaries` (tuần tự):

```bash
py scripts/build_prompt.py review-dev --boundary <b>   # prompt review 1 boundary, kind tự suy từ MATRIX
# → spawn review-{kind}-agent ; review ghi findings → MAIN spawn fix → re-review
```

Gom kết quả, rồi complete:

```bash
py scripts/harness.py review-dev complete '{"review_results":[
  {"boundary":"order","kind":"backend","review_result":"pass","coverage_pct":85},
  {"boundary":"product","kind":"backend","review_result":"pass","coverage_pct":82},
  {"boundary":"web","kind":"web","review_result":"pass","coverage_pct":61}
]}'
```

## MAIN orchestrate vòng review→fix (mỗi boundary)

> review-agent là sub-agent → KHÔNG nest spawn fix. **MAIN điều phối** spawn fix.

```
loop tới open_findings==0 (cap ~5 vòng):
  1. MAIN spawn review-{kind}-agent
       → review ghi tracking/{wave}/review-findings.md (mỗi issue 1 row RF-NNN)
       → return {review_result, open_findings, coverage_pct}
  2. open_findings>0 → MAIN đọc row status=open của boundary → spawn fix-{prefix}-{boundary}-agent (Mode B):
       prompt = FEAT/AC + findings (file/type/suggested_fix)
       → fix sửa code, set row status=resolved → return
  3. quay lại 1 (re-review)
MAIN ghi {boundary, kind, review_result: pass, coverage_pct}
```

## Quy tắc

- **Tuần tự, không song song** — xong boundary này mới sang boundary kế (dễ trace, fix-loop không đụng nhau).
- **MAIN spawn cả review lẫn fix** — review-agent read-only, KHÔNG tự spawn (sub-agent không nest spawn).
- Boundary nào fix mãi không sạch → **STOP**, báo user, KHÔNG complete.
- **Gate `no_open_findings` chặn `/review-dev complete`** nếu `review-findings.md` còn row BLOCKER/MAJOR `status=open` → ép fix sạch trước khi rời REVIEW_DEV.
- `review_results` lưu vào STATE; gate `/dev-handoff` verify thêm: mọi `wave_boundaries` đều pass + coverage đạt ngưỡng kind (BE80 / BFF70 / web60 / mobile60).
- Boundary chưa từng `/start-dev` (không có code) → review fail → gate chặn (ép dev đủ trước khi handoff).
