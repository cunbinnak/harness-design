---
name: boundary-charter
description: Discovery D3 (charter-author) — identify boundary từ event-storming → BOUNDARY-MAP + CHARTER per boundary, RỒI derive PROJECT.md (PRD) + chốt service_prefix (gộp vai trò aggregate D6). KHÔNG sinh FEAT (DOMAIN sở hữu). Clone từ ADLC agent-charter-author mode CHARTER-NEW.
---

# Boundary Charter Skill (D3)

## Khi load
`/discover D3` — agent `charter-author-agent` (Architecture Authority). Vai trò kép:
1. **Identify boundary** từ aggregates/domains ở D2 → `BOUNDARY-MAP.md` + `CHARTER.md` per boundary.
2. **Derive PROJECT.md** (PRD) → sang DOMAIN_AUTHORING.

> **KHÔNG sinh FEAT/Epic/BR ở D3**: DOMAIN (stage sau) sở hữu product — `/domain` author BUSINESS vào `docs/domain/` → ký → dịch sang eng `docs/architecture/` (một lệnh, ba bước). D3 chỉ charter + BOUNDARY-MAP + PROJECT.md.

Input: `hypothesis-log.md` + `capability-map.md` + `persona-pool.md` + `event-storming/ES-*.md`.

## Deliverable (đúng cái gate D3 verify)
1. **`docs/discovery/BOUNDARY-MAP.md`** theo template — **≥1 row non-placeholder** (backend boundary / web experience): boundary + mission + owned data + wave + status.
2. **`docs/discovery/boundaries/{boundary}/CHARTER.md`** theo `boundaries/TEMPLATE.CHARTER.md` cho mỗi boundary — **§1 Mission có content thật**; owned data (từ aggregates D2); capabilities exposed/consumed; epics/features high-level; NON-NEGOTIABLES.
3. **`docs/architecture/PROJECT.md`** (PRD) — derive từ hypothesis (vision/problem) + capability (scope) + event-storming: scope in/out + **NFR có số** + security/compliance + success metrics + glossary. (Gộp vai trò aggregate D6: bản tổng hợp project-level.)
4. **Chốt `service_prefix`** (kebab ngắn, vd `crm-hdpe`) → trả `service_prefix` trong RETURN SCHEMA.

> Gate D3 (`discovery_gate.py D3`): BOUNDARY-MAP ≥1 row; ≥1 CHARTER §1 Mission; PROJECT.md tồn tại. **KHÔNG check FEAT** (DOMAIN sở hữu). `service_prefix` enforce qua RETURN SCHEMA (SubagentStop), KHÔNG qua discovery_gate. Bỏ check ADR-D3/SYSTEM-TOPOLOGY (stack decision thuộc DESIGN/`technical-design`).

## Phương pháp (clone agent-charter-author CHARTER-NEW + derive)
1. **Boundary identification**: group aggregates (D2 §5) chia sẻ data/lifecycle → 1 boundary. Mỗi boundary owns data duy nhất (no overlap — verify qua BOUNDARY-MAP).
2. **Mission**: 1 câu "what & why" từ capability-map.
3. **Owned data / capabilities**: từ event-storming aggregates + capability-map.
4. **NON-NEGOTIABLES**: hỏi Architecture Authority (AskUserQuestion).
5. **Derive PROJECT.md**: tổng hợp hypothesis + capability + ES thành PRD đủ scope/NFR-số/security/metrics/glossary. KHÔNG bịa số NFR — hỏi user nếu chưa rõ.

## Quy tắc
- KHÔNG invent capability/boundary ngoài discovery — refer back D0-D2.
- 1 spawn có thể tạo nhiều boundary CHARTER (D3 identification), nhưng giữ data ownership không overlap.
- KHÔNG tạo `knowledge-base/*.yaml` (KG do implementation-plan/run-wave sau).
- Idempotent re-run.

## Sang DOMAIN authoring
Sau D3 + `/discover` (gate pass → DOMAIN_AUTHORING): PROJECT.md + charter boundaries đã có → user chạy `/domain` — tự suy thiếu gì viết nấy, lặp tới khi OK, rồi ký + dịch (gate ≥1 eng epic+feat+BR + translation_parity) → `/domain` (refine tới khi vừa ý, `--end` chốt) → `/domain` → `/approve-document` → `/run-wave 1`.

## Quality checklist
- [ ] BOUNDARY-MAP ≥1 row non-placeholder.
- [ ] Mỗi boundary có CHARTER §1 Mission thật + owned data không overlap.
- [ ] PROJECT.md có scope + NFR số + security/compliance + glossary.
- [ ] service_prefix chốt (kebab).
- [ ] KHÔNG sinh FEAT/Epic/BR (để DOMAIN).

## Chốt D3 — user ĐỌC và ĐÁNH GIÁ rồi mới ký

D3 là artifact cuối của Discovery, nên nó gánh thêm lượt **rà chéo toàn lớp** mà từng D-wave riêng lẻ không thấy: hypothesis ↔ capability ↔ persona ↔ ma trận quyền ↔ ES ↔ boundary ↔ PROJECT.md. Lệch chỗ nào sửa trước, đừng đẩy sang cho user phát hiện hộ.

Rồi **DỪNG LẠI**: trình danh sách file kèm *mỗi file nên soi gì*, nói rõ chỗ đã tự quyết (trỏ `tracking/decisions.md`) và chỗ mình không chắc nhất. **KHÔNG tự ký, KHÔNG chạy tiếp.**

User góp ý → sửa → rà lại → trình lại. User **duyệt** → `py scripts/approve_document.py --layer discovery` → complete.

Vì sao ký ở đây chứ không đợi REVIEW: domain + design + plan đều xây trên Discovery. Tìm ra lỗ ở `hypothesis-log` lúc đã dựng ba tầng lên trên nghĩa là tháo ngược cả ba.

## Done
- BOUNDARY-MAP + CHARTER + PROJECT.md pass gate D3; user confirm → `/discover` (không arg) → DOMAIN_AUTHORING.
