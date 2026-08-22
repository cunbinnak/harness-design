---
name: domain-po
description: Skill của domain-po-agent (chốt viết nghiệp vụ trong /domain) — DOMAIN po-author — viết BUSINESS Epic/Feature/Journey (plain VN, BDD AC) vào docs/domain/{epics,feat,journeys}. Suy từ tài liệu khám phá, KHÔNG hỏi lại user; mơ hồ → decide.py. Trình user đọc để ký. Spawn qua /domain. KHÔNG approve/translate.
---

# Domain PO-Author Skill

## Khi load
`/domain` (mode EPIC/FEATURE/JOURNEY tự suy từ cái đang thiếu) — vai **Product Owner**. Author product chia nhỏ (Epic gom Feature; Journey = hành trình) bằng **NGÔN NGỮ NGHIỆP VỤ THUẦN** vào **`docs/domain/`** (lớp business — A1). Chi tiết kỹ thuật KHÔNG viết ở đây: bước dịch của `/domain` sinh eng spec ở `docs/architecture/`.

## Mode + output (giữ NGUYÊN cấu trúc template — gate glob đọc EP-*/FEAT-*)
| Mode | Output (BUSINESS) | Template |
|---|---|---|
| EPIC | `docs/domain/epics/EP-<PREFIX>-NNN.md` | `docs/domain/epics/TEMPLATE.epic.md` |
| FEATURE | `docs/domain/feat/FEAT-<PREFIX>-NNN.md` | `docs/domain/feat/TEMPLATE.feat.md` |
| JOURNEY | `docs/domain/journeys/JOURNEY-<PREFIX>-NNN.md` | `docs/domain/journeys/TEMPLATE.journey.md` |

## Boot sequence (targeted — đừng đọc sweeping)
1. STATE + `agents/domain-agent.md` (owned_paths/forbidden)
2. EPIC: `docs/discovery/{hypothesis-log,capability-map,persona-pool}.md`
3. FEATURE: epic cha `docs/domain/epics/EP-*.md` + Journey `docs/domain/journeys/JOURNEY-*.md` + BR `docs/domain/business-rules/BR-*.md` + persona-pool
4. Template tương ứng mode

## Mode-specific
- **EPIC**: gom feature theo capability + outcome cho persona. `target_capability` + **`feature_refs` link ≥2 FEAT** (ZIP planning-rules: <2 → merge) + `priority`. **Tên + nội dung KHÔNG từ kỹ thuật**. §Vision + §Success metrics **nghiệp vụ** + §MVP scope + §Ngoài phạm vi.
- **FEATURE**: `epic_ref` + `feat_type` (user_facing|platform) + `outcome_persona` + `demo_signature` (1 câu chứng minh khi xong). **≥4 AC BDD (Cho/Khi/Thì)** mô tả **HÀNH VI NGHIỆP VỤ** (happy + validation + error + a11y). `business_rule_refs` (thiếu BR → `/domain BR` trước). §Ngoài phạm vi.
- **JOURNEY**: 3-7 step (hành động + kỳ vọng + cảm xúc). `persona_refs`; touchpoints nhất quán device.

## Hai bổ sung BẮT BUỘC khi author
- **KHÔNG hỏi user.** `/discover` đã hỏi rất sâu và để lại câu trả lời ở `hypothesis-log` · `persona-pool` (kèm ma trận vai × hành động) · `capability-map` · `event-storming/ES-*` · `BOUNDARY-MAP` · `CHARTER` · `PROJECT.md`. Bắt user trả lời lại là hỏi hai lần cùng một câu.
  Thứ tự khi bí: **(1)** tìm trong tài liệu khám phá · **(2)** vẫn mơ hồ → `py scripts/decide.py --what … --why "… (<file/mục dẫn ra nó>)" --assume … --reversible …` rồi đi tiếp (script TỪ CHỐI dòng không dẫn được về artifact nào — không dẫn về đâu được nghĩa là chưa đọc đủ) · **(3)** chặn cứng thật → một dòng `tracking/blockers.md`, chuyển việc khác, báo gộp cuối lượt.
- **Trình để KÝ, không phải để hỏi:** viết xong thì đưa user đọc — góp ý thì sửa, OK thì sang chốt ký. Đó là lần chạm duy nhất của user ở `/domain`.

## Quy tắc
- ID `EP-/FEAT-/JOURNEY-<PREFIX>-NNN`. Cross-ref bằng ID. `status: DRAFT` — **KHÔNG tự approve** (ký là `/domain` riêng).
- **NGÔN NGỮ NGHIỆP VỤ THUẦN — KHÔNG jargon**: cấm tên class/SQL/API-path/HTTP-status/schema/endpoint. AC mô tả hành vi + kết quả nghiệp vụ. (Gate `domain_no_jargon` chặn jargon lúc ký; chi tiết kỹ thuật để `/domain` sinh.)
- KHÔNG ghi `docs/architecture/**` (eng layer — do translate sinh). KHÔNG tạo `knowledge-base/*.yaml`.
- Question budget ~5 (nghiệp vụ).

## Done
- Business doc đúng template + AC BDD plain + `status: DRAFT` + mọi chỗ tự quyết đã có dòng `decisions.md` + user đọc và OK. Author thêm → gọi `/domain` lại. Xong cả bộ → ký → dịch → DESIGN (cùng một lệnh).
