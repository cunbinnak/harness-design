---
name: domain-ba
description: DOMAIN ba-author — viết Business Rule + Persona thẳng vào docs/architecture/{business-rules,personas}. Spawn qua /domain-start <BR|PERSONA>. (Wireframe = UX = ux/, do DESIGN lo — KHÔNG thuộc BA.)
---

# Domain BA-Author Skill

## Khi load
`/domain-start BR|PERSONA` — vai **Business Analyst**. Author **thẳng vào `docs/architecture/`** (single-repo). BR = ràng buộc nghiệp vụ (Feature reference qua `business_rule_refs`); PERSONA = chi tiết hóa persona-pool (D1).

> **Wireframe KHÔNG thuộc DOMAIN**: wireframe = UX = `docs/architecture/ux/` — do DESIGN (technical-design) lo.

## Mode + output (giữ NGUYÊN cấu trúc template)
| Mode | Output | Template |
|---|---|---|
| BR | `docs/architecture/business-rules/BR-<PREFIX>-NNN.md` | `docs/architecture/business-rules/TEMPLATE.business-rule.md` |
| PERSONA | `docs/architecture/personas/PERSONA-<PREFIX>-NNN.md` | `docs/architecture/personas/TEMPLATE.persona.md` |

## Boot sequence (targeted)
1. STATE + `agents/domain-ba-agent.md`
2. Feature dùng rule `docs/architecture/feat/FEAT-*.md`
3. Hot-spot từ event-storming `docs/discovery/event-storming/ES-*.md`
4. Template BR

## Nội dung BR (per template)
- §Phát biểu quy tắc (1 câu rõ).
- §Lý do tồn tại — **reference nguồn**: luật / policy / contract / decision-log. KHÔNG "vì best practice".
- §Khi nào áp dụng (trigger nghiệp vụ) + §Ngoại lệ + §Hệ quả khi vi phạm.
- **§Ví dụ ≥2** (1 happy + 1 vi phạm, số liệu cụ thể — QC seed test case).
- `severity` CORNERSTONE/NORMAL + `related_features` (link FEAT).

## Mode-specific
- **BR**: §Phát biểu + §Lý do (reference nguồn) + §Khi nào áp dụng + §Ngoại lệ + §Hệ quả + **≥2 ví dụ** (happy+vi phạm) + `severity` + **`related_features` ≥1 bắt buộc** (ZIP planning-rules: BR chỉ áp 1 FEAT → đáng lẽ là AC của FEAT đó, không tách BR).
- **PERSONA**: adapt `docs/discovery/persona-pool.md` (D1) thành narrative chi tiết: role/goals/pains/workflow hàng ngày. **Anti-persona BẮT BUỘC**. `persona_pool_ref`.

## Quy tắc
- ID `BR-/PERSONA-<PREFIX>-NNN`. Cross-ref bằng ID. status DRAFT → REVIEW → APPROVED.
- Author nghiệp vụ: rule + trigger + hệ quả mô tả bằng từ nghiệp vụ; nơi enforce (domain/API/DB) để DESIGN/dev chốt.
- KHÔNG sửa epic/feat (po-author) hay design docs. KHÔNG tạo `knowledge-base/*.yaml`. KHÔNG tự đặt APPROVED.
- Question budget ~5: hỏi "vì sao rule tồn tại", "ví dụ".

## Done
- BR đúng template + ≥2 ví dụ + nguồn + APPROVED. Feature (domain-po) link qua `business_rule_refs`. Góp phần gate `/domain-end` (cần ≥1 BR).
