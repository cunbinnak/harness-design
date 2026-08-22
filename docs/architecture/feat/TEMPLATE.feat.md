---
type: domain-artifact
artifact_kind: feature-intent
id: "FEAT-{{PREFIX}}-{{NNN}}"
status: "DRAFT | REVIEW | APPROVED"
version: 1
tier: T2
owner_authority: business
owner: "{{người chịu trách nhiệm feature — single-person: chính bạn}}"
priority: "P0 | P1 | P2 | P3"
epic_ref: "EP-{{PREFIX}}-{{NNN}}"   # 1 epic cha (gate planning_lint, trỏ file thật)
feat_type: "user_facing | platform"   # user_facing=có UI demo; platform=backend-only (gate planning_lint)
business_rule_refs: ["BR-{{PREFIX}}-{{NNN}}"]   # BR phải tuân thủ (gate planning_lint, trỏ file thật)
journey_refs: ["JOURNEY-{{PREFIX}}-{{NNN}}"]   # journey feature hiện thực
persona_refs: ["PERSONA-{{PREFIX}}-{{NNN}}"]
outcome_persona: "PERSONA-{{PREFIX}}-{{NNN}}"   # persona CHÍNH nhận outcome
demo_signature: "{{1 câu: demo gì để CHỨNG MINH feature đạt (anti-gaming) — nguồn cho wave demo_target}}"
target_boundary_hint: "{{boundary name (kind backend/web/mobile) hoặc TBD}}"
has_ui_touchpoint: true
consumes_contracts: []   # TODO engineer — DESIGN điền contract FEAT tiêu thụ (api/INTEG id); gate todo_resolved đòi hết TBD/TODO trước design-end
source: "docs/domain/feat/FEAT-{{PREFIX}}-{{NNN}}.md"   # file business nguồn (translator điền — gate translation_parity @domain-end đối chiếu 1-1)
domain_source_id: "FEAT-{{PREFIX}}-{{NNN}}"
last_reviewed: "{{YYYY-MM-DD}}"
---

> **LỚP ENGINEERING** — bản dịch từ business (`source` ở trên) do `domain-translate` sinh, KHÔNG author tay (gate `translation_parity` chặn eng mồ côi). Sửa NGHIỆP VỤ → lùi `domain-po` sửa bản business → re-ký → re-dịch. Điền NGẮN GỌN: ưu tiên bảng/bullet — agent downstream đọc nhiều lần.

> AC giữ BDD Cho/Khi/Thì thuần HÀNH VI (test map vào hành vi, không map class/endpoint — spec sống lâu hơn implementation; heading `### AC-n` để gate `ac_coverage` parse). Khác bản business ở FRONTMATTER máy-đọc: `feat_type`/`priority`/refs (planning_lint gate) + `consumes_contracts` (TODO engineer → DESIGN điền) + `source`/`domain_source_id` (trace về bản đã ký) + §5 AC→BR + §7 demo evidence.

# FEAT-{{PREFIX}}-{{NNN}} — {{Tên tính năng}}

## 1. Mục tiêu nghiệp vụ

{{1-2 câu: giải quyết vấn đề gì cho persona, gắn outcome epic cha.}}

## 2. Persona dùng tính năng

> Persona chính trùng `outcome_persona`. Phân biệt người THAO TÁC vs người NHẬN kết quả.

| Persona | Vai trò |
|---|---|
| {{PERSONA-XXX-001 — Merchant Admin}} | {{Người chính — tạo yêu cầu}} |
| {{PERSONA-XXX-002 — Manager}} | {{Approver nếu vượt ngưỡng (tuỳ chọn)}} |

## 3. User story

**Là** {{persona}}, **tôi muốn** {{khả năng}}, **để** {{outcome nghiệp vụ}}.

## 4. Tiêu chí chấp nhận (Acceptance Criteria)

> Mỗi AC: **Cho** (bối cảnh) / **Khi** (hành động) / **Thì** (kết quả quan sát được). Độc lập testable, QC seed 1:1. Phủ tối thiểu các archetype áp dụng được; thêm AC nếu thiếu archetype.

| Archetype | Bắt buộc khi |
|---|---|
| Happy path | Luôn |
| Validation đầu vào | Có nhập liệu |
| Lỗi nghiệp vụ | Có BR / điều kiện chặn |
| Phân quyền | Quyền phụ thuộc vai trò |
| A11y + responsive | has_ui_touchpoint=true |
| Trạng thái rỗng/tải/lỗi tải | UI có dữ liệu động |

### AC-1: {{Happy path — tên ngắn}}

**Cho** {{persona, quyền, trạng thái dữ liệu}}
**Khi** {{hành động persona}}
**Thì** {{kết quả quan sát được + thay đổi trạng thái nghiệp vụ}}

### AC-2: {{Validation đầu vào — tên ngắn}}

**Cho** {{persona đang nhập liệu}}
**Khi** {{nhập giá trị không hợp lệ — vd vượt số dư, xem [BR-{{PREFIX}}-001](../business-rules/BR-{{PREFIX}}-001.md)}}
**Thì** {{từ chối, báo lý do rõ tại đúng chỗ, không đổi dữ liệu}}

### AC-3: {{Lỗi nghiệp vụ — tên ngắn}}

**Cho** {{đầu vào hợp lệ}}
**Khi** {{điều kiện chặn nghiệp vụ — vd yêu cầu song song, trạng thái không cho thao tác}}
**Thì** {{thông báo nghiệp vụ rõ + hướng dẫn tiếp; KHÔNG "HTTP 409"}}

### AC-4: {{Happy path mở rộng / kết quả phụ — tên ngắn}}

**Cho** {{...}}
**Khi** {{persona hoàn tất hành động chính}}
**Thì** hệ thống:
- {{Cập nhật trạng thái nghiệp vụ}}
- {{Đưa sang màn hình/kết quả tiếp}}
- {{Gửi xác nhận tới các bên liên quan}}

### AC-5: {{A11y — chỉ khi has_ui_touchpoint}}

**Cho** {{persona dùng bàn phím / trình đọc màn hình}}
**Khi** {{thao tác qua màn hình}}
**Thì** {{tab order hợp lý, mọi trường có nhãn, lỗi đọc được bằng screen reader}}

### AC-6: {{Responsive — chỉ khi has_ui_touchpoint}}

**Cho** {{persona dùng điện thoại / tablet / máy tính}}
**Khi** {{màn hình hiển thị}}
**Thì** {{bố cục hợp thiết bị, không cuộn ngang, không che nội dung}}

<!-- Thêm AC theo archetype còn thiếu. Mỗi AC testable + tầng nghiệp vụ. -->

## 5. Bảng ánh xạ AC → BR (traceability)

> Mỗi BR liên quan ≥1 AC kiểm chứng; mỗi AC "lỗi nghiệp vụ" trỏ về BR nguồn.

| AC | Archetype | BR liên quan | Ghi chú |
|---|---|---|---|
| AC-1 | Happy path | — | {{...}} |
| AC-2 | Validation | [BR-{{PREFIX}}-001](../business-rules/BR-{{PREFIX}}-001.md) | {{...}} |
| AC-3 | Lỗi nghiệp vụ | [BR-{{PREFIX}}-002](../business-rules/BR-{{PREFIX}}-002.md) | {{...}} |

## 6. Quy tắc liên quan

> Mọi BR ở đây phải có trong frontmatter `business_rule_refs` và trỏ file THẬT.

| Business Rule | Vai trò trong feature |
|---|---|
| [BR-{{PREFIX}}-001](../business-rules/BR-{{PREFIX}}-001.md) | {{Số tiền hoàn ≤ số dư còn lại}} |
| [BR-{{PREFIX}}-002](../business-rules/BR-{{PREFIX}}-002.md) | {{Đơn đã chargeback không cho hoàn thủ công}} |

## 6.1 Ca biên hành vi — đã quyết

> **Bảng TRA, không phải văn xuôi.** Khác `HLD §6.1` (ca biên kỹ thuật/dữ liệu: khoá lạc quan,
> idempotency key, cache cũ): chỗ này là **ca biên HÀNH VI mà người dùng thật gặp** — và AC hạnh
> phúc gần như không bao giờ nói tới.
>
> **Mọi dòng phải có câu trả lời.** Không áp dụng → `n/a — <lý do>`. Để trống nghĩa là **chưa ai
> quyết**, và lúc code sẽ có người quyết thay bạn.
>
> Dòng nào cần chặn ở server thì phải sinh **≥1 AC âm** ở §4 — nếu không, nó chỉ là ý định.

| # | Tình huống | Người dùng thấy gì | Có AC nào phủ? |
|---|---|---|---|
| B1 | Bấm/gửi hai lần liên tiếp | {{một kết quả, không nhân đôi}} | {{AC-n / cần thêm}} |
| B2 | Bỏ dở giữa chừng rồi quay lại | {{dữ liệu đang nhập còn / mất — nói rõ}} | {{...}} |
| B3 | Không có quyền nhưng gọi thẳng | {{bị chặn ở server, thông báo nói được PHẢI LÀM GÌ}} | {{...}} |
| B4 | Dữ liệu rỗng (lần đầu dùng) | {{hiện gì, hướng dẫn bước tiếp theo}} | {{...}} |
| B5 | Hệ phụ thuộc lỗi / mất mạng giữa chừng | {{báo lỗi tử tế + cách thử lại, KHÔNG nuốt im lặng}} | {{...}} |
| B6 | Dữ liệu rất nhiều / chuỗi rất dài | {{phân trang, cắt, không vỡ}} | {{...}} |

> `/dogfood` chạy đúng các tình huống này bằng 6 lăng kính persona; `B3` lấy ca thử từ ma trận
> vai × hành động (`persona-pool.md`).

## 7. Bằng chứng demo (anti-gaming)

> Cụ thể hoá `demo_signature` thành kịch bản quan sát được — nguồn cho wave `demo_target`. CHỨNG MINH outcome, không chỉ "code chạy".

- Kịch bản: {{persona làm A → B → C; người xem thấy X}}
- Dữ liệu mẫu cần có: {{...}}
- Coi là "đạt": {{tiêu chí quan sát được}}

## 8. Ngoài phạm vi (QC dựa vào để biết KHÔNG test gì)

> BẮT BUỘC. Mỗi mục nói rõ thuộc feature/epic/phase nào.

- {{Hoàn tiền tự động theo lịch — feature riêng}}
- {{Workflow duyệt nhiều cấp — feature riêng}}
- {{Tích hợp kế toán bên thứ ba — phase sau}}

## 9. TODO engineer / Open questions kỹ thuật (DESIGN trả — gate `todo_resolved`)

> Câu hỏi NGHIỆP VỤ đã chốt trước khi ký ở lớp business (docs/domain). Ở đây chỉ còn nợ KỸ THUẬT translator để lại — DESIGN phải điền hết trước `design-end`.

- [ ] {{consumes_contracts: FEAT này gọi contract nào? (api-{{boundary}} / INTEG-INT-*)}}
- [ ] {{Lỗi nghiệp vụ AC-3 map error code nào trong Domain error catalog? (api §4.2)}}
- [ ] {{Màn hình nào ở ux-{{boundary}}.md hiện thực AC có UI? (design-ux)}}

## 10. References

- Epic cha: `docs/architecture/epics/EP-{{PREFIX}}-{{NNN}}.md`
- Journey: `docs/architecture/journeys/JOURNEY-{{PREFIX}}-{{NNN}}.md`
- Personas: `docs/architecture/personas/PERSONA-{{PREFIX}}-{{NNN}}.md`
- Business rules: `docs/architecture/business-rules/BR-{{PREFIX}}-*.md`
- Business nguồn (bản ĐÃ KÝ): `docs/domain/feat/FEAT-{{PREFIX}}-{{NNN}}.md`
- UX (nếu có UI, do design-ux): `docs/architecture/ux/ux-{{boundary}}.md`

## 11. Change log

| Date | Version | Status | Author | Thay đổi |
|---|---|---|---|---|
| {{YYYY-MM-DD}} | 1 | TRANSLATED | domain-translator | Dịch từ bản business đã ký (source) — TODO-engineer chờ DESIGN |
| {{YYYY-MM-DD}} | 1 | ENRICHED | solution-architect | DESIGN điền consumes_contracts/error-code map (gate todo_resolved sạch) |
