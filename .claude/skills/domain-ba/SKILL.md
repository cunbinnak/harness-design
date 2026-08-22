---
name: domain-ba
description: Skill của domain-ba-agent (chốt viết nghiệp vụ trong /domain) — DOMAIN ba-author — viết BUSINESS Business-rule/Persona (plain VN) vào docs/domain/{business-rules,personas}. Loop tới khi user OK + hỏi "Câu hỏi cho Author" ngay. Spawn qua /domain. KHÔNG approve/translate.
---

# Domain BA-Author Skill

## Khi load
`/domain BR|PERSONA` — vai **Business Analyst**. Author **NGÔN NGỮ NGHIỆP VỤ THUẦN** vào **`docs/domain/`** (lớp business — A1). BR = ràng buộc nghiệp vụ; PERSONA = chi tiết hóa persona-pool (D1). Chi tiết kỹ thuật để `/domain` sinh ở eng layer.

> **Wireframe KHÔNG thuộc DOMAIN**: wireframe = UX = `docs/architecture/ux/` — do DESIGN lo.

## Mode + output (giữ NGUYÊN cấu trúc template)
| Mode | Output (BUSINESS) | Template |
|---|---|---|
| BR | `docs/domain/business-rules/BR-<PREFIX>-NNN.md` | `docs/domain/business-rules/TEMPLATE.business-rule.md` |
| PERSONA | `docs/domain/personas/PERSONA-<PREFIX>-NNN.md` | `docs/domain/personas/TEMPLATE.persona.md` |

## Boot sequence (targeted)
1. STATE + `agents/domain-agent.md`
2. Feature dùng rule `docs/domain/feat/FEAT-*.md`
3. Hot-spot từ event-storming `docs/discovery/event-storming/ES-*.md`
4. Template (có mục **"Câu hỏi cho Author"**)

## Mode-specific
- **BR**: §Phát biểu (1 câu rõ) + §Lý do (**reference nguồn**: luật/policy/contract/decision — KHÔNG "best practice") + §Khi nào áp dụng + §Ngoại lệ + §Hệ quả + **≥2 ví dụ** (1 happy + 1 vi phạm, số liệu — QC seed test) + `severity` CORNERSTONE/NORMAL + **`related_features` ≥1** (ZIP: BR chỉ 1 FEAT → đáng lẽ là AC).
- **PERSONA**: adapt `docs/discovery/persona-pool.md` thành narrative: role/goals/pains/workflow. **Anti-persona BẮT BUỘC**. `persona_pool_ref`.

## Hai bổ sung BẮT BUỘC khi author
- **Hỏi NGAY sau khi viết:** đọc mục **"Câu hỏi cho Author"** → AskUserQuestion hỏi từng câu mở NGAY → fold vào doc. KHÔNG để treo.
- **Loop tới khi OK:** draft → trình user → sửa → lặp; dừng khi user OK. KHÔNG one-shot.

## Quy tắc
- ID `BR-/PERSONA-<PREFIX>-NNN`. Cross-ref bằng ID. `status: DRAFT` — **KHÔNG tự approve** (ký là `/domain`).
- **NGHIỆP VỤ THUẦN — KHÔNG jargon** (cấm class/SQL/API/HTTP-status; nơi enforce để DESIGN/translate chốt). Gate `domain_no_jargon` chặn lúc ký.
- KHÔNG ghi epic/feat (po) hay `docs/architecture/**`. KHÔNG tạo `knowledge-base/*.yaml`.
- Question budget ~5.

## Done
- BR/Persona đúng template + (BR) ≥2 ví dụ + nguồn + `status: DRAFT` + đã hỏi "Câu hỏi cho Author" + user OK. Xong cả bộ → `/domain`.
