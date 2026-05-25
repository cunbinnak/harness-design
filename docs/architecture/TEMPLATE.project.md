# PROJECT — {project_name}

> **Purpose:** Mô tả dự án ở cấp cao nhất — vision, scope, KPI, NFR, constraints.
> **Owner:** `intake:requirement-analyst` (bước 1) → `intake:business-analyst` (bước 2 refine).
> **Audience:** Mọi agent intake/review, dev (đọc làm bối cảnh), stakeholder.
> **Out of scope:** Per-boundary design (→ [`hld/`](hld/)), API (→ [`api/`](api/)), UI (→ [`ux/`](ux/)), wave plan (→ [`../plans/`](../plans/)).

---

## Tổng quan

- **Tên / mã dự án:**
- **One-liner:** (sản phẩm làm gì cho ai)
- **Vấn đề giải quyết:**

## Đối tượng

- **Người dùng chính:** (persona — chỉ liệt kê, chi tiết UI ở [`ux/`](ux/))
- **Bên liên quan:**
- **Giả định môi trường:** (cloud, on-prem, mobile/web...)

## Phạm vi dự án

| In scope | Out of scope |
|----------|--------------|
| | |

## Mục tiêu & KPI

- **Mục tiêu kinh doanh:**
- **KPI / điều kiện done cấp dự án:**

## Ràng buộc

- **Pháp lý / compliance:**
- **Kỹ thuật cứng:** (tech stack bắt buộc, integration phải có...)
- **Vận hành:** (timeline, team size, budget)

## NFR (project-wide)

> Targets cấp dự án. Boundary có thể refine trong HLD §NFR nếu cần stricter.

| Attribute | Target |
|-----------|--------|
| Performance | (vd. p95 latency < 200ms) |
| Availability | (vd. 99.5%) |
| Security | (vd. OWASP Top 10) |
| Test Coverage | BE ≥ 80%, FE ≥ 60% |
| Scalability | (vd. {N} req/s @ {users}) |
| Observability | (vd. structured JSON logs) |

## Nguyên tắc thiết kế

- (vd. API-first, bounded context, event-driven nếu áp dụng)

## Glossary

| Thuật ngữ | Định nghĩa |
|-----------|------------|
| | |

## Open questions

- [ ] (câu hỏi) → @owner → deadline

## Liên kết

- FEAT: [`feat/FEAT-*.md`](feat/)
- ADR: [`adr/ADR-*.md`](adr/)
- Plans: [`../plans/project/waves-roadmap.md`](../plans/project/waves-roadmap.md)
- Shared KG: [`../../knowledge-base/shared.knowledge-graph.yaml`](../../knowledge-base/shared.knowledge-graph.yaml)
