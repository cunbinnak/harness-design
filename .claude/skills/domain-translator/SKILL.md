---
name: domain-translator
description: DỊCH business doc (docs/domain/, đã ký) → engineering artifact (docs/architecture/). Clone ZIP agent-domain-translator. DỊCH KHÔNG SÁNG TÁC — clone narrative + map sang format eng + thêm field engineer dạng TODO; KHÔNG tự nghĩ AC/scope mới. Spawn qua /domain.
---

# Domain Translator Skill (clone ZIP `agent-domain-translator`, adapt single-repo)

## Khi load
`/domain` (stage DOMAIN_AUTHORING) — chỉ chạy sau khi **mọi business doc đã KÝ** (gate `domain_signed`). Cầu nối **business → engineering**, single-repo: nguồn `docs/domain/` (business, plain VN, no jargon) → đích `docs/architecture/` (eng).

> **Bạn là translator — KHÔNG sáng tác.** Chỉ DỊCH business artifact sang format eng (kèm field engineer cần: `consumes_contracts: []`, `enforcement_location: TBD (DESIGN)`, …). **KHÔNG inject content mới** (không tự nghĩ AC/scope không có ở business). Thiếu chi tiết kỹ thuật → để **TODO engineer** (DESIGN điền), KHÔNG tự bịa.

## Modes (giữ ID, mỗi business doc → eng doc cùng ID)
| Mode | Source (business) | → Eng target | Eng template |
|---|---|---|---|
| MAP-EPIC | `docs/domain/epics/EP-*.md` | `docs/architecture/epics/EP-*.md` | `docs/architecture/epics/TEMPLATE.epic.md` |
| MAP-FEAT | `docs/domain/feat/FEAT-*.md` | `docs/architecture/feat/FEAT-*.md` | `docs/architecture/feat/TEMPLATE.feat.md` |
| MAP-BR | `docs/domain/business-rules/BR-*.md` | `docs/architecture/business-rules/BR-*.md` | `docs/architecture/business-rules/TEMPLATE.business-rule.md` |
| MAP-PERSONA | `docs/domain/personas/PERSONA-*.md` | `docs/architecture/personas/PERSONA-*.md` | `docs/architecture/personas/TEMPLATE.persona.md` |
| MAP-JOURNEY | `docs/domain/journeys/JOURNEY-*.md` | `docs/architecture/journeys/JOURNEY-*.md` | `docs/architecture/journeys/TEMPLATE.journey.md` |

> Single-repo: ghi THẲNG `docs/architecture/` (KHÔNG `_aggregated/specs-drafts/`, KHÔNG sync-to-specs/SPECS-repo — đó là plumbing multi-repo đã bỏ). KHÔNG UX-SEED (wireframe=UX=DESIGN).

## Boot sequence (targeted, < 20 KB)
1. STATE + verify gate `domain_signed`.
2. Source business doc(s) `docs/domain/**` (đã `status: APPROVED`).
3. Eng template tương ứng `docs/architecture/<kind>/TEMPLATE.*.md` (read-only — hiểu structure).
4. `tracking/translation-log.md` (tránh dịch trùng).

## Transformation rules (clone ZIP §4)
- **Frontmatter**: clone từ business source + thêm field eng + `source: docs/domain/<file>` + `domain_source_id: <id>` + `translated_at`. Strip field business-only.
- **Body**: clone narrative business; map AC **Cho/Khi/Thì plain VN → format eng** (engineer thêm reference contract/endpoint ở DESIGN). Thêm **TODO block** cho field kỹ thuật: FEAT `consumes_contracts: [] # TODO engineer`; BR `enforcement_location: TBD (DESIGN)` + `scope: TBD`; PERSONA clone gần nguyên + field eng (`tier`).
- **FEAT FE** (`has_ui_touchpoint=true`): thêm `consumes_backend_feats` cross-link nếu có.
- Giữ NGUYÊN id (FEAT-x business → FEAT-x eng).

## Workflow
1. Verify mọi business doc `status: APPROVED` (gate `domain_signed`) — chưa đủ → STOP, về `/domain`.
2. Foreach business doc → dịch sang eng artifact tương ứng (clone + add TODO-engineer + source). KHÔNG sáng tác.
3. Mơ hồ / thiếu thông tin nghiệp vụ để dịch đúng → **AskUserQuestion (≤3)**, KHÔNG tự quyết scope.
4. Append row `tracking/translation-log.md`: `| date | TR-<n> | <source-id> | <target-paths> | translator-v1 | <decisions> |`.
5. `py scripts/harness.py domain-translate complete '{}'`. Return RETURN SCHEMA `files_changed` (eng docs).

## NEVER
- Sáng tác content (AC/scope không có ở business). Translator dịch, KHÔNG author.
- Tự ĐIỀN chi tiết kỹ thuật (contract/endpoint/schema) — để TODO engineer, DESIGN điền.
- Dịch khi business doc chưa ký (`approved!=true`). Sửa business doc `docs/domain/` (read-only ở bước này).
- Bỏ field `source` (engineer cần biết origin).

## Done
- Mỗi business doc đã ký có eng doc tương ứng `docs/architecture/` (giữ id + `source` + `domain_source_id` + TODO-engineer). translation-log có row.
- **Gate `translation_parity` (@/domain) đối chiếu 1-1 bằng máy:** business đã ký thiếu eng doc = bỏ sót (chặn); eng doc epics/feat/BR không có `source: docs/domain/...` = mồ côi (chặn) — dịch ĐỦ 100%, không bỏ sót. Gate `/domain` (`domain_gate`) → DESIGN.
