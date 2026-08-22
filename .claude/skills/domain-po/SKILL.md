---
name: domain-po
description: DOMAIN po-author — viết BUSINESS Epic/Feature/Journey (plain VN, BDD AC) vào docs/domain/{epics,feat,journeys}. Loop tới khi user OK + hỏi "Câu hỏi cho Author" ngay sau khi viết. Spawn qua /domain. KHÔNG approve/translate.
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
4. Template tương ứng mode (có mục **"Câu hỏi cho Author"**)

## Mode-specific
- **EPIC**: gom feature theo capability + outcome cho persona. `target_capability` + **`feature_refs` link ≥2 FEAT** (ZIP planning-rules: <2 → merge) + `priority`. **Tên + nội dung KHÔNG từ kỹ thuật**. §Vision + §Success metrics **nghiệp vụ** + §MVP scope + §Ngoài phạm vi.
- **FEATURE**: `epic_ref` + `feat_type` (user_facing|platform) + `outcome_persona` + `demo_signature` (1 câu chứng minh khi xong). **≥4 AC BDD (Cho/Khi/Thì)** mô tả **HÀNH VI NGHIỆP VỤ** (happy + validation + error + a11y). `business_rule_refs` (thiếu BR → `/domain BR` trước). §Ngoài phạm vi.
- **JOURNEY**: 3-7 step (hành động + kỳ vọng + cảm xúc). `persona_refs`; touchpoints nhất quán device.

## Hai bổ sung BẮT BUỘC khi author
- **Hỏi NGAY sau khi viết:** viết xong draft → đọc mục **"Câu hỏi cho Author"** trong template → dùng **AskUserQuestion hỏi TỪNG câu mở đó NGAY** → fold câu trả lời vào doc. KHÔNG để câu hỏi treo.
- **Loop tới khi OK:** vòng *draft → trình user → user góp ý → sửa* — CHỈ dừng khi user xác nhận OK. KHÔNG one-shot.

## Quy tắc
- ID `EP-/FEAT-/JOURNEY-<PREFIX>-NNN`. Cross-ref bằng ID. `status: DRAFT` — **KHÔNG tự approve** (ký là `/domain` riêng).
- **NGÔN NGỮ NGHIỆP VỤ THUẦN — KHÔNG jargon**: cấm tên class/SQL/API-path/HTTP-status/schema/endpoint. AC mô tả hành vi + kết quả nghiệp vụ. (Gate `domain_no_jargon` chặn jargon lúc ký; chi tiết kỹ thuật để `/domain` sinh.)
- KHÔNG ghi `docs/architecture/**` (eng layer — do translate sinh). KHÔNG tạo `knowledge-base/*.yaml`.
- Question budget ~5 (nghiệp vụ).

## Done
- Business doc đúng template + AC BDD plain + `status: DRAFT` + đã hỏi "Câu hỏi cho Author" + user OK. Author thêm → gọi `/domain` lại. Xong cả bộ → ký → dịch → DESIGN (cùng một lệnh).
