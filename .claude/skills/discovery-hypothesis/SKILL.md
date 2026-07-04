---
name: discovery-hypothesis
description: Discovery D0 (Business Authority) — mô tả ý tưởng project thành hypothesis-log (vision + problem statement + ≥3 hypothesis testable + ≥2 anti-hypothesis). Bức tranh tổng quan TRƯỚC khi vào capability/event-storming. Clone tối giản từ ADLC DISCOVERY D0.
---

# Discovery Hypothesis Skill (D0)

## Khi load
`/discovery-start D0` — agent `discovery-hypothesis-agent` (vai **Business Authority**): biến ý tưởng/brief project thành **bức tranh tổng quan dạng giả thuyết** để cả team đồng thuận vấn đề + đối tượng + cược gì, TRƯỚC khi đi vào capability (D1) / event-storming (D2) / boundary (D3).

Input: mô tả project user truyền (`$ARGUMENTS`). Không có → hỏi user "Ý tưởng/brief project là gì? Giải quyết vấn đề gì, cho ai?".

## Deliverable (đúng cái gate D0 verify)
**`docs/discovery/hypothesis-log.md`** theo `docs/discovery/TEMPLATE.hypothesis-log.md` — **giữ NGUYÊN heading** (gate match regex):
1. **§1 Vision narrative** — 1-2 đoạn: vấn đề gì, cho ai, vì sao bây giờ (non-empty thật, không placeholder).
2. **§2 Problem statement** — 2-3 đoạn: pain point + status quo + cost of inaction.
3. **§3 Hypotheses** — table `| H1 | ... |`, **≥3 row**: mỗi hypothesis có statement + expected outcome (measurable) + test method + status (TESTABLE).
4. **§4 Anti-hypotheses** — **≥2 item** list: cái KHÔNG cược / ngoài scope, để giữ scope honest.

> Gate D0 (`discovery_gate.py D0`): §1+§2 non-empty; ≥3 row `| H\d |`; ≥2 anti-hypothesis. Lệch heading → gate false-fail.

## Phương pháp
1. **Vision**: chốt 1 câu "what & why & for whom" rồi mở rộng 1-2 đoạn.
2. **Problem**: mô tả status quo + pain đo được + chi phí nếu không làm.
3. **Hypothesis**: mỗi cược lớn = 1 hypothesis có thể chứng minh/bác bỏ. Statement + signal đo được + cách test (experiment/interview/data). KHÔNG viết hypothesis không test được.
4. **Anti-hypothesis**: nêu rõ cái KHÔNG bet (chống scope creep + kỳ vọng sai).

## Flow
- Interactive với user (AskUserQuestion ≤5): hỏi info thiếu, KHÔNG bịa số liệu/nguồn.
- Iterate tới khi user confirm. Idempotent: re-run thì update file, không tạo file mới / blind-append.
- Sau confirm: return RETURN SCHEMA `wave: "D0"`, `user_confirmed: true`.

## Quality checklist
- [ ] §1 Vision + §2 Problem là nội dung thật (>20 ký tự, không chỉ `_TBD_`).
- [ ] ≥3 hypothesis testable (statement + outcome đo được + test method).
- [ ] ≥2 anti-hypothesis.
- [ ] Không bịa metric/nguồn.

## Done
- `docs/discovery/hypothesis-log.md` pass gate D0; user confirm → `/discovery-start D1` (tiến wave, gate D0 verify lúc đó).
