---
name: domain-ba
description: Skill của domain-ba-agent (chốt viết nghiệp vụ trong /domain) — DOMAIN ba-author — viết BUSINESS Business-rule/Persona (plain VN) vào docs/domain/{business-rules,personas}. Suy từ tài liệu khám phá, KHÔNG hỏi lại user; mơ hồ → decide.py. Trình user đọc để ký. Spawn qua /domain. KHÔNG approve/translate.
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
4. Template

## Mode-specific
- **BR**: §Phát biểu (1 câu rõ) + §Lý do (**reference nguồn**: luật/policy/contract/decision — KHÔNG "best practice") + §Khi nào áp dụng + §Ngoại lệ + §Hệ quả + **≥2 ví dụ** (1 happy + 1 vi phạm, số liệu — QC seed test) + `severity` CORNERSTONE/NORMAL + **`related_features` ≥1** (ZIP: BR chỉ 1 FEAT → đáng lẽ là AC).
- **PERSONA**: adapt `docs/discovery/persona-pool.md` thành narrative: role/goals/pains/workflow. **Anti-persona BẮT BUỘC**. `persona_pool_ref`.

## Hai bổ sung BẮT BUỘC khi author
- **KHÔNG hỏi user.** `/discover` đã hỏi rất sâu và để lại câu trả lời ở `hypothesis-log` · `persona-pool` (kèm ma trận vai × hành động) · `capability-map` · `event-storming/ES-*` · `BOUNDARY-MAP` · `CHARTER` · `PROJECT.md`. Bắt user trả lời lại là hỏi hai lần cùng một câu.
  Thứ tự khi bí: **(1)** tìm trong tài liệu khám phá · **(2)** vẫn mơ hồ → `py scripts/decide.py --what … --why "… (<file/mục dẫn ra nó>)" --assume … --reversible …` rồi đi tiếp (script TỪ CHỐI dòng không dẫn được về artifact nào — không dẫn về đâu được nghĩa là chưa đọc đủ) · **(3)** chặn cứng thật → một dòng `tracking/blockers.md`, chuyển việc khác, báo gộp cuối lượt.
- **Trình để KÝ, không phải để hỏi:** viết xong thì đưa user đọc — góp ý thì sửa, OK thì sang chốt ký. Đó là lần chạm duy nhất của user ở `/domain`.

## Quy tắc
- ID `BR-/PERSONA-<PREFIX>-NNN`. Cross-ref bằng ID. `status: DRAFT` — **KHÔNG tự approve** (ký là `/domain`).
- **NGHIỆP VỤ THUẦN — KHÔNG jargon** (cấm class/SQL/API/HTTP-status; nơi enforce để DESIGN/translate chốt). Gate `domain_no_jargon` chặn lúc ký.
- KHÔNG ghi epic/feat (po) hay `docs/architecture/**`. KHÔNG tạo `knowledge-base/*.yaml`.
- Question budget ~5.

## Done
- BR/Persona đúng template + (BR) ≥2 ví dụ + nguồn + `status: DRAFT` + mọi chỗ tự quyết đã có dòng `decisions.md` + user OK. Xong cả bộ → `/domain`.
