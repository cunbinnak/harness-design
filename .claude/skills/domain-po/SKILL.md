---
name: domain-po
description: DOMAIN po-author — viết Epic + Feature + Journey (product, BDD AC) thẳng vào docs/architecture/{epics,feat,journeys}. Chia nhỏ product như ZIP DOMAIN. Spawn qua /domain-start <EPIC|FEATURE|JOURNEY>.
---

# Domain PO-Author Skill

## Khi load
`/domain-start EPIC|FEATURE|JOURNEY` — vai **Product Owner**. Author product chia nhỏ (Epic gom Feature; Journey = hành trình người dùng) **thẳng vào `docs/architecture/`** (single-repo, không docs/domain riêng, không translate). Chi tiết kỹ thuật (contract/endpoint/schema) để stage DESIGN bổ sung.

## Mode + output (giữ NGUYÊN cấu trúc template — gate glob đọc EP-*/FEAT-*)
| Mode | Output | Template |
|---|---|---|
| EPIC | `docs/architecture/epics/EP-<PREFIX>-NNN.md` | `docs/architecture/epics/TEMPLATE.epic.md` |
| FEATURE | `docs/architecture/feat/FEAT-<PREFIX>-NNN.md` | `docs/architecture/feat/TEMPLATE.feat.md` |
| JOURNEY | `docs/architecture/journeys/JOURNEY-<PREFIX>-NNN.md` | `docs/architecture/journeys/TEMPLATE.journey.md` |

## Boot sequence (targeted — đừng đọc sweeping)
1. STATE + `agents/domain-po-agent.md` (owned_paths/forbidden)
2. EPIC: `docs/discovery/{hypothesis-log,capability-map,persona-pool}.md`
3. FEATURE: epic cha `docs/architecture/epics/EP-*.md` + Journey liên quan `docs/architecture/journeys/JOURNEY-*.md` (flow → AC đúng) + BR liên quan `docs/architecture/business-rules/BR-*.md` + persona-pool
4. Template tương ứng mode

## Mode-specific
- **EPIC**: gom feature theo capability + outcome cho persona. `target_capability` (từ capability-map) + **`feature_refs` link ≥2 FEAT** (ZIP planning-rules: epic <2 feature → granularity sai, merge lại) + `priority` (P0-P3). **Tên EP KHÔNG chứa từ kỹ thuật** (API/Service/Consumer/Queue/Cache/Endpoint/Database/Adapter/Integration) — đặt theo business outcome theme. §Vision + §Success metrics **nghiệp vụ** (KHÔNG metric kỹ thuật p99) + §MVP scope + §Ngoài phạm vi.
- **FEATURE**: thuộc 1 epic (`epic_ref`) + `feat_type` (user_facing|platform — PLAN dùng chọn wave_strategy) + **`outcome_persona`** (persona chính) + **`demo_signature`** (1 câu chứng minh khi xong — anti-gaming, nguồn wave demo_target). ≥4 AC theo **BDD: Cho / Khi / Thì** (happy + validation + error + accessibility — stricter than ZIP floor 3, chủ đích enterprise). `business_rule_refs` link BR (thiếu BR → spawn `/domain-start BR` trước). `has_ui_touchpoint`. §Ngoài phạm vi (QC dựa vào) + §Câu hỏi Business Authority.
- **JOURNEY**: 3-7 step hành trình người dùng, mỗi step (hành động + kỳ vọng + cảm xúc). `persona_refs`; touchpoints nhất quán device persona. Nguồn: persona-pool (D1) + event-storming (D2).

## Quy tắc
- ID `EP-/FEAT-<PREFIX>-NNN`. Cross-ref bằng ID. status DRAFT → REVIEW → APPROVED (Business Authority duyệt).
- Author product-level: AC mô tả **hành vi nghiệp vụ + kết quả**; chi tiết kỹ thuật (API/contract/schema) KHÔNG ở đây — DESIGN (technical-design) bổ sung.
- KHÔNG sửa `docs/architecture/{hld,api,data-model,adr,...}` (DESIGN territory). KHÔNG tạo `knowledge-base/*.yaml`. KHÔNG tự đặt APPROVED.
- Question budget ~5: hỏi nghiệp vụ.

## Done
- Artifact đúng template + AC BDD + status APPROVED. Gate `/domain-end` (`domain_gate`): ≥1 epic + ≥1 feat + ≥1 BR ở docs/architecture/ → DESIGN.
