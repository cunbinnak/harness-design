---
name: review-dev
description: "Wave-scoped: review TẤT CẢ service trong wave, mỗi cái theo kind. Mỗi boundary review-{kind}-agent tự loop fix tới pass."
when_state: ['DEV']
sets_stage: REVIEW_DEV
spawn:
  agent: "review-{kind}-agent (mỗi boundary trong wave, theo kind)"
  skills: review-{kind}
gates: []
---

# /review-dev

## Mục đích

Review **toàn bộ service trong wave** (sau khi đã `/start-dev` xong từng boundary). Mỗi boundary được review bằng `review-{kind}-agent` đúng kind của nó (backend → review-backend, web → review-web, …). Mỗi agent tự loop review → spawn fix → re-review tới pass. **Pass khi MỌI boundary pass.**

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
# → spawn review-{kind}-agent ; agent tự loop fix tới pass
```

Gom kết quả, rồi complete:

```bash
py scripts/harness.py review-dev complete '{"review_results":[
  {"boundary":"order","kind":"backend","review_result":"pass","coverage_pct":85},
  {"boundary":"product","kind":"backend","review_result":"pass","coverage_pct":82},
  {"boundary":"web","kind":"web","review_result":"pass","coverage_pct":61}
]}'
```

## Agent internal loop (mỗi boundary)

```
1. Review code services/{prefix}-{boundary}/ theo skill review-{kind}
2. Issue (coverage < ngưỡng kind, lint, convention, BLOCKER) → spawn fix-{prefix}-{boundary}-agent
3. Fix → re-review → loop tới pass
4. Return {boundary, kind, review_result: pass, coverage_pct}
```

## Quy tắc

- **Tuần tự, không song song** — xong boundary này mới sang boundary kế (dễ trace, fix-loop không đụng nhau).
- Boundary nào không pass được → **STOP**, báo user, KHÔNG complete.
- `review_results` lưu vào STATE; gate `/dev-handoff` verify lại: mọi `wave_boundaries` đều pass + coverage đạt ngưỡng kind (BE80 / BFF70 / web60 / mobile60).
- Boundary chưa từng `/start-dev` (không có code) → review fail → gate chặn (ép dev đủ trước khi handoff).
