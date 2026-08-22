---
type: design
artifact_kind: project
status: ACTIVE
version: 1
tier: T0
owner_authority: Architecture Authority
owner_role: "discovery:charter-author (derive ở D3, gộp aggregate D6)"
created_at: "{{DATE}}"
last_reviewed: "{{DATE}}"
service_prefix: "{{prefix}}"            # chốt ở D3 — dùng cho services/{prefix}-{boundary}/
---

# PROJECT — {{project_name}}

> Điền NGẮN GỌN: ưu tiên bảng/bullet, không văn xuôi thừa, không lặp. Doc này agent downstream đọc nhiều lần — tiết kiệm context.
> Tài liệu cấp cao nhất: gộp PRD + SYSTEM-ARCHITECTURE + TECHSTACK + ROADMAP (single-repo). Owner: `discovery:charter-author` (derive D3, gộp D6). Source-of-truth cho: vision, scope, NFR, security, metrics, glossary, stack, roadmap.
> Out of scope (file khác): per-boundary design → `hld/`; API → `api/`; schema → `data-model/`; UI → `ux/`; wave chi tiết → `../plans/`.

---

## 0. Bảng chốt — đề bài đã đủ chưa

> **Mọi dòng phải có câu trả lời.** Không áp dụng thì ghi `KHÔNG CÓ — <lý do>`; để trống nghĩa là **chưa ai hỏi**, không phải "không cần".
> Cột `Trả lời` viết ngắn + trỏ về mục chứa chi tiết (§n, hoặc file). Đây là bảng **kiểm soát**, không phải nơi chép lại nội dung.
> Đây là danh sách những thứ brief/tài liệu đầu vào gần như không bao giờ nói đủ — hỏi cho hết ở stage sở hữu, vì downstream không có chỗ nào hỏi lại.

| # | Phải chốt | Chốt ở | Trả lời (hoặc `KHÔNG CÓ — lý do`) | Nguồn |
|---|---|---|---|---|
| C1 | Pain point + **ai chịu** + tần suất/chi phí (có số) | DISC_D0 | {{...}} → §1 | {{hypothesis-log §problem}} |
| C2 | Persona + **năng lực được cấp / KHÔNG được làm** từng vai | DISC_D1 · DOMAIN | {{...}} → §2, `personas/` | {{...}} |
| C3 | **Danh sách vai (role) đóng** — đủ để lập ma trận vai × hành động | DOMAIN | {{...}} → §2 | {{...}} |
| C4 | Multi-tenant hay không; ranh giới cô lập là gì | DISC_D3 | {{...}} → §9 | {{...}} |
| C5 | Đăng nhập: provider, S2S hay user, vòng đời token | DESIGN | {{...}} → §7.2 + `adr/` | {{...}} |
| C6 | Phân quyền **enforce ở tầng nào** (không phải chỉ ẩn UI) | DESIGN | {{...}} → §9 | {{...}} |
| C7 | Định giá / hạn mức / quota | DOMAIN | {{...}} → §3 | {{...}} |
| C8 | Trạng thái rỗng + **error catalog chung** (mã lỗi, shape response) | DESIGN | {{...}} → `api/` | {{...}} |
| C9 | **Dữ liệu mẫu / seed** để chạy thử và test | DESIGN | {{...}} → `infra/` | {{...}} |
| C10 | Vòng đời dữ liệu: giữ bao lâu, xoá mềm hay cứng, ai được xoá | DESIGN | {{...}} → `data-model/` | {{...}} |
| C11 | Tích hợp ngoài: hệ nào, **ai giữ credential**, hỏng thì hệ thống làm gì | DESIGN | {{...}} → `integrations/` | {{...}} |
| C12 | Môi trường: mấy môi trường, deploy ở đâu | DISC_D3 | {{...}} → §5 | {{...}} |
| C13 | **NFR có SỐ**: p95, throughput, availability — không viết "nhanh" | DISC_D3 · DESIGN | {{...}} → §8 | {{...}} |
| C14 | i18n / múi giờ / tiền tệ / đơn vị đo | DOMAIN | {{...}} → §11 | {{...}} |
| C15 | Compliance / pháp lý / data residency | DISC_D3 | {{...}} → §9 | {{...}} |
| C16 | Tương thích ngược — surface đã giao ở wave trước *(từ wave 2)* | PLAN | {{...}} → BC-LEDGER | {{...}} |

**Lỗ hổng còn mở** → ghi vào §12. **§12 trống là đáng ngờ, không phải sạch** — tài liệu đầu vào gần như không bao giờ nói đủ về C5, C7, C8, C9, C13.

---

## 1. Tổng quan (PRD)

- **Tên / mã:** {{project_name}} / prefix `{{prefix}}`
- **One-liner:** {{làm gì, cho ai, giá trị gì}}
- **Vấn đề giải quyết:** {{pain point — trích hypothesis-log §problem}}
- **Vision (1 câu):** {{tương lai khi thành công}}

### 1.1 Hypotheses + risk (từ D0)

| Giả thuyết | Loại | Cách kiểm chứng | Trạng thái |
|---|---|---|---|
| {{H1: ...}} | hypothesis | {{metric / experiment}} | {{open/validated}} |
| {{A1: ...}} | anti-hypothesis | {{...}} | {{...}} |

---

## 2. Đối tượng (personas)

> Chỉ liệt kê + nhu cầu cốt lõi. Chi tiết → `personas/`; UI flow → `ux/`.

| Persona | Vai trò | Nhu cầu cốt lõi (job-to-be-done) |
|---|---|---|
| {{Cashier}} | {{người dùng chính}} | {{nhận order nhanh, ít thao tác}} |
| {{Manager}} | {{...}} | {{báo cáo real-time}} |

- **Bên liên quan (không trực tiếp dùng):** {{owner, kế toán, IT}}
- **Giả định môi trường:** {{cloud/on-prem; web/mobile; mạng/thiết bị}}

---

## 3. Phạm vi dự án

| In scope (làm) | Out of scope (KHÔNG làm — và vì sao) |
|---|---|
| {{...}} | {{... — lý do: hoãn / ngoài năng lực / không cốt lõi}} |

**Anti-capabilities (cố ý KHÔNG làm):** {{vd. "Không làm loyalty/CRM trong v1."}}

---

## 4. Mục tiêu & success metrics

- **Mục tiêu kinh doanh:** {{...}}
- **Điều kiện "done" cấp dự án:** {{khi nào coi là hoàn thành MVP/v1}}

| Metric | Baseline | Target | Đo bằng |
|---|---|---|---|
| {{Thời gian nhận 1 order}} | {{90s}} | {{< 30s}} | {{instrumentation}} |
| {{Tỷ lệ báo cáo đúng giờ}} | {{60%}} | {{> 95%}} | {{...}} |

---

## 5. Ràng buộc

- **Pháp lý / compliance:** {{hoá đơn điện tử, lưu trữ N năm, data residency}}
- **Kỹ thuật cứng:** {{stack bắt buộc, integration phải có, legacy phải tương thích}}
- **Vận hành:** {{timeline, team=1 người, budget, hạ tầng sẵn}}

---

## 6. System architecture (cấp dự án)

> Bức tranh boundary tổng thể. Chi tiết per-boundary → HLD; ownership/owned_paths/kind → MATRIX.

### 6.1 Boundary inventory

| Boundary | kind | Trách nhiệm | Phụ thuộc | Wave |
|---|---|---|---|---|
| `{{auth}}` | backend | {{xác thực + phân quyền}} | — | {{1}} |
| `{{order}}` | backend | {{quản lý order}} | `{{auth}}` | {{1}} |
| `{{bff-pos}}` | bff | {{aggregate cho POS app}} | `{{order, auth}}` | {{2}} |
| `{{pos-web}}` | web | {{giao diện thu ngân}} | `{{bff-pos}}` | {{2}} |

### 6.2 Topology (C4 — Container level)

```mermaid
flowchart TB
  subgraph clients[Clients]
    Web[{{pos-web}}]
    Mobile[{{manager-mobile}}]
  end
  subgraph bff[BFF]
    BFF[{{bff-pos}}]
  end
  subgraph backend[Backend]
    Auth[{{auth}}]
    Order[{{order}}]
  end
  subgraph infra[Stateful infra]
    DB[({{Postgres}})]
    Cache[({{Redis}})]
    Bus{{Kafka}}
  end
  Web --> BFF
  Mobile --> BFF
  BFF --> Auth
  BFF --> Order
  Order -->|event| Bus
  Order --> DB
  Auth --> DB
  Order --> Cache
```

### 6.3 Nguyên tắc thiết kế (project-wide invariants)

> Chi tiết + enforcement → `ARCHITECTURE-PRINCIPLES.md`.

- {{Boundary + kind — không fullstack (P1)}}
- {{Contract-first cross-boundary (P2)}}
- {{No business logic in frontend (I1)}}
- {{No cross-boundary FK — link by id, resolve app-layer}}
- {{Event-driven cho cross-boundary side-effect (nếu áp dụng)}}

---

## 7. Tech stack (TECHSTACK)

### 7.1 Per-kind stack

| kind | Language / runtime | Framework | Build | Test |
|---|---|---|---|---|
| backend | {{Java 21}} | {{Spring Boot 3.4}} | {{Gradle}} | {{JUnit5 + Testcontainers}} |
| bff | {{Node.js 22}} | {{Apollo Server}} | {{npm}} | {{Jest}} |
| web | {{TypeScript}} | {{React 19 + Vite}} | {{npm}} | {{Vitest + Playwright}} |
| mobile | {{Dart}} | {{Flutter 3}} | {{flutter}} | {{flutter test}} |

> Stack per boundary chốt ở DESIGN (ADR tech-stack). Bảng này là default; boundary có thể khác (ghi ở HLD + ADR).

### 7.2 Cross-cutting infra

| Hạng mục | Lựa chọn | Ghi chú |
|---|---|---|
| Primary DB | {{Postgres 16}} | schema-per-boundary |
| Cache / idempotency | {{Redis 7}} | keyspace-per-boundary |
| Message bus | {{Kafka / RabbitMQ}} | cross-boundary event |
| Auth | {{OAuth2 / JWT}} | `ADR-platform-auth` |
| Secrets | {{Vault / env-mount}} | không hardcode |
| Observability | {{OTel + JSON log}} | ADR observability |
| Local dev | docker-compose | `infra/docker-compose.yml` |

### 7.3 Rationale chọn stack

- {{vd. "Java 21 + Spring: team quen, ecosystem mạnh cho transactional service."}}

---

## 8. NFR (project-wide)

> Target cấp dự án — số cụ thể, đo được. Boundary refine chặt hơn ở HLD §7; KHÔNG lỏng hơn bảng này.

| Attribute | Target | Đo / verify |
|---|---|---|
| Performance | {{p95 < 200ms; p99 < 500ms}} | perf TC |
| Availability | {{99.5%}} | healthcheck + uptime |
| Scalability | {{1000 req/s @ {{N}} concurrent}} | load test |
| Durability | {{no data loss on single-node crash}} | resilience TC |
| Security | {{OWASP Top 10 clean; auth mọi endpoint}} | security review + TC |
| Test coverage | BE ≥ 80%, BFF ≥ 70%, web/mobile ≥ 60% | `dev-handoff` gate |
| Observability | {{JSON log + RED metric + trace}} | review |
| Maintainability | {{1 người vận hành — ưu tiên đơn giản}} | — |

---

## 9. Security & compliance

| Concern | Approach |
|---|---|
| AuthN / AuthZ | {{JWT + RBAC; deny-by-default}} |
| Multi-tenant isolation | {{tenant_id mọi query; không leak cross-tenant}} |
| Data at rest | {{encrypt PII column}} |
| Data in transit | {{TLS mọi hop}} |
| Secrets management | {{Vault; rotate định kỳ}} |
| Audit trail | {{log security-relevant ops}} |
| Compliance regime | {{hoá đơn điện tử, lưu trữ N năm, GDPR-like}} |
| PII inventory | {{field nào PII, ở boundary nào}} |

---

## 10. Roadmap (cấp dự án — wave level)

> Cao cấp theo capability → wave. Chi tiết → `../plans/WAVE-SEQUENCE.md` + `wave-{N}.md`.

| Wave | Theme / capability | Boundary đụng tới | Mục tiêu "done" |
|---|---|---|---|
| {{1}} | {{Core order + auth}} | `{{auth, order}}` | {{nhận order end-to-end}} |
| {{2}} | {{POS UI + BFF}} | `{{bff-pos, pos-web}}` | {{thu ngân dùng được}} |
| {{3}} | {{Reporting}} | `{{report, manager-mobile}}` | {{báo cáo real-time}} |

**Dependencies giữa wave:** {{vd. "Wave 2 cần Wave 1 (contract order); Wave 3 cần event Wave 1."}}

---

## 11. Glossary

| Thuật ngữ | Định nghĩa |
|---|---|
| {{Order}} | {{...}} |
| {{Tenant}} | {{...}} |
| {{Boundary}} | đơn vị giao hàng có `kind`; scaffold ra 1 service repo |

---

## 12. Open questions

| Câu hỏi | Ảnh hưởng | Owner | Hạn |
|---|---|---|---|
| [ ] {{...}} | {{...}} | {{@owner}} | {{Wave-N}} |

---

## 13. Liên kết

- Hypothesis (D0): `../discovery/hypothesis-log.md` · Capability (D1): `../discovery/capability-map.md` · Boundary (D3): `../discovery/BOUNDARY-MAP.md`
- Principles: `ARCHITECTURE-PRINCIPLES.md` · Taxonomy: `SEVERITY-TEST-TAXONOMY.md` · Epics/Features: `epics/` · `feat/`
- ADR: `adr/` · HLD: `hld/` · Plans: `../plans/WAVE-SEQUENCE.md` · Matrix: `../../harness/SERVICE-BOUNDARY-MATRIX.json`

---

## 14. Change log

| Date | Version | Author | Description |
|---|---|---|---|
| {{DATE}} | 1 | discovery:charter-author | Initial PROJECT (derive D3, gộp aggregate D6) |
