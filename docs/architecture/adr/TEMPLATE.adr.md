---
type: design
artifact_kind: adr
adr_id: "ADR-{{boundary}}-{{NNN}}"
target_boundary: "{{boundary}}"
# FE boundary (web/mobile): vẫn dùng target_boundary. Cross-cutting toàn dự án: namespace chung (vd ADR-platform-001)
related_feat: "FEAT-XXX-NNN"          # FEAT thúc đẩy decision (khuyến nghị)
related_boundary: ""                   # khi ADR cross-boundary
related_br: ""                          # BR mà decision hiện thực (nếu có)
status: "PROPOSED | ACCEPTED | DEPRECATED | SUPERSEDED-BY-{{ADR-ID}}"
decision_class: "T1 | T2 | T3"          # T1=multi-boundary/khó đảo ngược; T2=boundary-local; T3=reversible/local
version: 1
tier: T2
owner_authority: Architecture Authority
created_at: "{{DATE}}"
last_reviewed: "{{DATE}}"
review_due: "{{DATE or 'n/a'}}"          # khi nào re-validate
supersedes: "{{ADR-ID or 'none'}}"
superseded_by: "{{ADR-ID or 'none'}}"
---

# ADR-{{boundary}}-{{NNN}} — {{Title}}

> Điền NGẮN GỌN: ưu tiên bảng/bullet, không văn xuôi thừa, không lặp. Doc này agent downstream đọc nhiều lần — tiết kiệm context.
> One decision per file. Supersede = tạo ADR mới + flip status cái cũ, KHÔNG xoá. Quy mô theo decision_class: T1 đầy đủ; T3 rút gọn §Rollout/§Failure nếu reversible.

---

## Status

**{{PROPOSED | ACCEPTED | DEPRECATED | SUPERSEDED}}** — {{date}}

- PROPOSED: chờ Architecture Authority review. ACCEPTED: code mới PHẢI tuân; code cũ migrate per §Rollout. DEPRECATED: không áp dụng code mới, chưa có thay thế. SUPERSEDED: ghi `superseded_by`.

If SUPERSEDED: supersedes `ADR-{{boundary}}-{{previous}}`, superseded by `ADR-{{boundary}}-{{next}}`.

---

## Context

{{2-4 câu: vấn đề là gì, để người/agent 6 tháng sau hiểu vì sao quyết định tồn tại mà không cần hỏi.}}

**Forces / drivers** (mỗi lực kéo khác hướng — lý do quyết định khó):

| Lực kéo | Loại | Mô tả |
|---|---|---|
| {{Performance p99 < 200ms}} | Technical | {{...}} |
| {{Single-person ops}} | Operational | {{...}} |
| {{Compliance / data residency}} | Regulatory | {{...}} |

**Constraints (cứng):** {{vd. stack đã chốt Java 21 + Spring Boot 3.4; tương thích contract api-{{boundary}}.md}}
**Assumptions (sai thì re-open ADR):** {{vd. throughput đỉnh ≤ 1000 req/s trong 12 tháng}}
**Why now:** {{vd. Wave-N cần code boundary này; trễ sẽ chặn dev}}

---

## Decision

{{1-3 câu phát biểu dứt khoát: "Sử dụng X", "KHÔNG dùng Y", "Bắt buộc Z".}}

**Scope:** Áp dụng: {{vd. mọi aggregate trong boundary}} · KHÔNG áp dụng: {{vd. legacy table x giữ đến Wave-M}}

---

## Alternatives considered

> Liệt kê MỌI option nghiêm túc đã cân nhắc (≥2, gồm option được chọn). `planning_lint.py` đếm data-row bảng này (cần ≥2 non-placeholder).

| Alternative | Pros | Cons | Reason not chosen |
|---|---|---|---|
| {{Option-A}} | {{...}} | {{...}} | {{lý do loại}} |
| {{Option-B}} | {{...}} | {{...}} | {{lý do loại}} |
| {{Chosen}} | {{...}} | {{...}} | **CHOSEN** — {{lý do thắng}} |

## Decision drivers (scoring — tuỳ chọn)

> Dùng khi tradeoff không hiển nhiên. Bảng riêng để `planning_lint` chỉ đếm bảng Alternatives ở trên.

| Tiêu chí (trọng số) | {{Option-A}} | {{Option-B}} | {{Chosen}} |
|---|---|---|---|
| {{Simplicity (×3)}} | {{2}} | {{3}} | {{5}} |
| {{Operability (×3)}} | {{2}} | {{4}} | {{5}} |
| **Tổng có trọng số** | {{...}} | {{...}} | **{{cao nhất}}** |

---

## Consequences

- **Positive:** {{...}}
- **Negative / tradeoff (chấp nhận — ghi để đời sau biết "đã biết mà vẫn chọn"):** {{...}}
- **Neutral:** {{...}}

**Risks + mitigation:**

| Risk | Likelihood | Impact | Mitigation | Trigger re-open ADR |
|---|---|---|---|---|
| {{UUID v7 không sortable đủ cho range query}} | {{Low}} | {{Med}} | {{thêm created_at index}} | {{p99 query > 200ms}} |

---

## Implementation impact

| Area | Impact | Cascade |
|---|---|---|
| Data model | {{...}} | `data-model/data-model-{{boundary}}.md` §1 |
| HLD | {{...}} | `hld/hld-{{boundary}}.md §{{section}}` |
| Code | {{...}} | `services/{{prefix}}-{{boundary}}/**` — mới tuân, cũ migrate per §Rollout |
| API contract | {{Yes/No}} | If yes: `api/api-{{boundary}}.md` + re-validate consumer ở REVIEW |
| Events | {{Yes/No}} | If yes: `events/{{boundary}}-events.md` |
| Tests | {{...}} | TC mới + regression cho path migrate |
| Migration | {{Required/None}} | §Rollout |
| Knowledge graph | {{...}} | `knowledge-base/{{boundary}}.knowledge-graph.yaml` thêm decision node |

---

## Rollout

> Bắt buộc nếu cần migration. Bỏ qua nếu decision_class=T3 thuần forward.

**Strategy:** {{Big-bang / Strangler-fig / Dual-write + backfill / Feature-flag}}

1. Wave {{N}}: {{vd. thêm cột nullable, dual-write}}
2. Wave {{N+1}}: {{backfill, đọc cột mới}}
3. Wave {{N+2}}: {{drop đường cũ}}

**Backward compat khi migrate:** {{giữ hệ thống chạy khi cả 2 đường tồn tại}}
**Rollback nếu fail:** {{vd. feature-flag off, giữ cột cũ}}
Deprecation old approach: hoàn tất by Wave {{M}}.

---

## Validation / verification

| Cách verify | Khi nào | Pass criteria |
|---|---|---|
| {{Lint rule / ArchUnit}} | CI mỗi build | {{không còn auto-increment ID}} |
| {{Load test}} | `/test-execute` | {{p99 < 200ms}} |
| {{Review checklist}} | `/review-dev` | {{contract khớp}} |

---

## DECISION-REF usage

Commit message: `# DECISION-REF: ADR-{{boundary}}-{{NNN}}`. Đảm bảo `tracking/decisions.md` có row (wave, boundary, agent, ref). Trace: code → decisions.md → ADR này (Architecture-Principles P4).

---

## References

- BR: `business-rules/BR-{{boundary}}-{{NNN}}.md` · HLD: `hld/hld-{{boundary}}.md §{{section}}` · API: `api/api-{{boundary}}.md`
- Related ADRs: `adr/ADR-{{boundary}}-{{other}}.md` · Principle: `ARCHITECTURE-PRINCIPLES.md §{{Pn}}` · External: {{URL/RFC nếu có}}

---

## Change log

| Date | Status | Author | Note |
|---|---|---|---|
| {{DATE}} | PROPOSED | {{Author}} | Initial draft |
| {{DATE}} | ACCEPTED | Architecture Authority | After review |
