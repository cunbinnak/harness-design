---
type: charter
artifact_kind: boundary-charter
boundary: "{{boundary-name}}"
status: PROPOSED
version: 1
tier: T1
owner_authority: Architecture Authority + Business Authority
last_reviewed: "{{DATE}}"
---

# CHARTER — `{{boundary-name}}` (Backend Boundary)

> Điền NGẮN GỌN: ưu tiên bảng/bullet, không văn xuôi thừa, không lặp. Doc này agent downstream đọc nhiều lần — tiết kiệm context.

> Source-of-truth cho boundary này — conflict với HLD/ADR/code → CHARTER thắng. Authored ở D3 (charter-author) từ `ES-*.md §5 Aggregates`. Chỉ Architecture + Business modify (cross-boundary → chốt rà chéo của `/domain` + `/approve-document`).
> Gate D3: §1 Mission có content thật. Section khác có thể high-level ở D3, làm sâu ở DESIGN.
> Single-repo: FEAT ở `docs/architecture/feat/*` (DOMAIN) · contract draft ở DESIGN (`api,events,data-model`). KHÔNG có `contracts/` repo / signed-hash / multi-authority sign-off.

---

## 1. Mission

{{2-3 câu: boundary tồn tại để làm gì, trả lời business question nào, source-of-truth cho state nào, phục vụ flow/consumer nào.}}

_Ví dụ: "Quản lý vòng đời thanh toán: intent → capture → refund → reconcile. Source-of-truth cho transaction lifecycle. Phục vụ checkout + admin reconciliation."_

---

## 2. Owned data

> Entity/value object boundary sở hữu duy nhất (write authority). Không overlap — verify chéo `BOUNDARY-MAP.md §1`.

| Entity | Mô tả | Lifecycle |
|---|---|---|
| `{{Entity1}}` | {{1-line}} | {{created → … → archived}} |
| `{{Entity2}}` | {{1-line}} | {{…}} |

**KHÔNG sở hữu** (read-only qua contract ở DESIGN): `{{ExternalEntity}}` — read từ `{{other-boundary}}`.

---

## 3. Capabilities exposed

> Khả năng cung cấp cho hệ thống. Mỗi capability ↔ ≥1 FEAT (DOMAIN) + ≥1 contract (DESIGN). D3 list high-level + loại contract dự kiến; path chốt ở DESIGN.

| # | Capability | Loại (dự kiến) | Contract ref (DESIGN fill) | Consumers |
|---|---|---|---|---|
| 1 | {{vd "Issue refund"}} | api | `docs/architecture/api/api-{{boundary}}.md` | {{web / other-boundary}} |
| 2 | {{vd "Phát event X"}} | event | `docs/architecture/events/{{boundary}}-events.md` | {{subscribers}} |
| 3 | {{vd "Read-model Y"}} | data | `docs/architecture/data-model/data-model-{{boundary}}.md` | {{readers}} |

---

## 4. Capabilities consumed

> Boundary dựa vào ai. Mỗi dependency → 1 cross-boundary contract ở DESIGN.

| # | Consumed from | Via (dự kiến) | Why |
|---|---|---|---|
| 1 | `{{other-boundary}}` | {{read-model / api}} | {{reason}} |
| 2 | External `{{provider}}` | {{external api}} | {{reason}} |

---

## 5. Epics / Features (high-level)

> Chi tiết ở `docs/architecture/feat/*` (DOMAIN, sau D3). D3 chỉ list high-level.

| ID | Mô tả | Status |
|---|---|---|
| `EP-{{NNN}}` / `FEAT-{{NNN}}` | {{title}} | DRAFT |
| `FEAT-{{MMM}}` | {{title}} | DRAFT |

---

## 6. Business rules (high-level)

> Chi tiết per-rule ở `business-rules/BR-*.md` (DOMAIN). Đánh dấu CORNERSTONE = không bao giờ vi phạm.

| BR-ID | Tóm tắt | Severity |
|---|---|---|
| `BR-{{boundary}}-001` | {{1-line}} | CORNERSTONE |
| `BR-{{boundary}}-002` | {{1-line}} | NORMAL |

---

## 7. NON-NEGOTIABLES (boundary-specific)

> Specific cho boundary — KHÔNG copy-paste universal (xem `CLAUDE.md`). Vi phạm → chốt rà chéo của `/domain` + `/approve-document`.

1. {{vd "Mọi write qua transaction serializable isolation."}}
2. {{vd "Tenant ID trong WHERE clause mọi query."}}
3. {{vd "Idempotency key bắt buộc cho mọi mutation."}}

---

## 8. Owned paths (polyrepo)

> Code path boundary — service repo `services/{{prefix}}-{{boundary-name}}/`. `services/` gitignored (working dir tạm khi scaffold). owned_paths thực thi qua hook PreToolUse(Write|Edit) ở DEV; nguồn chính thức `harness/SERVICE-BOUNDARY-MATRIX.json` (materialize ở PLAN).

```
services/{{prefix}}-{{boundary-name}}/                  ← primary service code
services/{{prefix}}-{{boundary-name}}/db/migrations/     ← schema migrations
```

Cross-boundary write → chốt rà chéo của `/domain` + `/approve-document` TRƯỚC khi code.

---

## 9. Quality attributes (high-level)

> SLO / security / observability sơ bộ; làm sâu ở DESIGN (HLD §quality).

| Attribute | Target (sơ bộ) |
|---|---|
| Availability / SLO | {{vd "p99 < 300ms, 99.9% uptime"}} |
| Security | {{vd "OAuth2 resource server; tenant isolation"}} |
| Observability | {{vd "structured log + traceId"}} |
| Data retention | {{vd "giữ N năm; PII masked"}} |

---

## 10. Out-of-scope (boundary KHÔNG làm)

> Ranh giới tường minh — capability/dữ liệu ngoài boundary (link anti-capability nếu có).

- {{vd "Không báo cáo cross-store — thuộc reporting boundary."}}
- {{vd "Không sở hữu danh mục món — read từ catalog."}}

---

## 11. Lifecycle status

| Status | Trigger | Allowed actions |
|---|---|---|
| PROPOSED | Discovery (D3) | Charter authoring |
| DESIGNING | Charter approved → DESIGN | HLD + ADR + API/event/data-model draft |
| ACTIVE | Wave đầu include boundary | Full lifecycle (dev/test/review) |
| MAINTENANCE | Feature complete | FIX + minor enhancement |
| ARCHIVED | Decommissioned | Code deprecated; remove next wave |

Current: **{{STATUS}}**

---

## 12. Acceptance criteria (self-check ở D3)

- [ ] §1 Mission rõ — 1 câu "what & why".
- [ ] §2 Owned data không overlap (verify chéo `BOUNDARY-MAP.md`).
- [ ] §3 Capabilities có loại contract dự kiến · §4 Consumed có nguồn + lý do.
- [ ] §5 ≥1 epic/feature · §6 ≥1 cornerstone BR.
- [ ] §7 NON-NEGOTIABLES specific, không copy-paste universal.

---

## 13. References + hand-off (A→Z)

**Backward (nguồn):** `event-storming/ES-{{domain}}.md` (aggregate → owned data + capabilities) · `capability-map.md` · `BOUNDARY-MAP.md`.

**Sibling (cùng D3):** `docs/architecture/PROJECT.md` (PRD project-level — derive cùng lúc).

**Forward:**
- DOMAIN (`domain-po`·`domain-ba` → ký → `domain-translate`): `docs/domain/*` (business) → `docs/architecture/{epics,feat,business-rules,journeys}/*` (eng) từ §3/§5/§6.
- DESIGN (`design`): HLD/API/data-model/events `hld-{{boundary}}` · `api-{{boundary}}` · `data-model-{{boundary}}` · `{{boundary}}-events` — fill contract path §3/§4.
- PLAN (`plan`): `WAVE-SEQUENCE.md` + `SERVICE-BOUNDARY-MATRIX.json` (owned_paths §8) + KG `{{boundary}}.knowledge-graph.yaml`.
- DEV (`start-dev {{boundary}}`): scaffold `services/{{prefix}}-{{boundary-name}}/` theo §8.

---

## 14. Change Log

| Date | Version | Author | Description |
|---|---|---|---|
| {{DATE}} | 1 | charter-author (D3) | Initial charter (identification) |
