---
name: domain
description: "Viết NỐT nửa sau tài liệu: FEAT/AC/BR → thiết kế (ADR/HLD/API/data-model/UX) → chia wave → rà chéo toàn bộ. Chạy một mạch, dừng ở REVIEW chờ bạn duyệt. Không mode, không cờ."
argument-hint: "(không arg — chạy tiếp từ stage đang đứng)  ·  hoặc gợi ý phạm vi: \"đặt lịch\""
when_state: [DOMAIN_AUTHORING, DESIGN, PLAN, REVIEW]
spawn:
  agent: "domain-po-agent · domain-ba-agent · domain-translator-agent · solution-architect-agent · ux-designer-agent · program-planner-agent · review-document-agent"
  skills: [domain-po, domain-ba, domain-translator, technical-design, ux-design, implementation-plan, business-analysis]
gates: "mỗi chốt giữ nguyên gate cũ của nó (xem bảng dưới)"
---

# /domain — nốt nửa sau tài liệu

`/discover` cho nửa đầu (persona + ma trận quyền · capability · boundary · PROJECT). Lệnh này viết **nốt phần còn lại** rồi dừng ở `REVIEW` chờ bạn duyệt — `/approve-document` là chỗ **kết thúc**, tương đương khoá scope.

## Hành lang

| # | Chốt | `harness <id> complete` | Gate giữ nguyên |
|---|---|---|---|
| 1 | Epic / Feature / BR / Journey (business, plain VN) | `domain-po` · `domain-ba` (lặp) | `domain_no_jargon` |
| 2 | Ký business | `domain-approve` | `domain_stamped` |
| 3 | Dịch sang bản kỹ thuật | `domain-translate` | `domain_signed` · `translation_parity` |
| 4 | Đóng lớp nghiệp vụ | `domain-end` | `domain_gate` |
| 5 | Thiết kế: ADR · HLD · API · data-model · events · tích hợp | `design` | — |
| 6 | UX — **chỉ khi có boundary web/mobile** | `design-ux` | — |
| 7 | Đóng thiết kế | `design-end` | `design_gate` · **`edge_cases_decided`** · `todo_resolved` · `contract_graph_parity` · `api_transport` |
| 8 | Chia wave: WAVE-SEQUENCE + wave-{N} + MATRIX + KG | `plan` | `plan_gate` · `planning_lint` · `plan_integrity` · `matrix_coherence` · `wave_sequence_lint` |
| 9 | **Rà chéo toàn bộ** | `review-document` (no-arg) | ghi `tracking/doc-review-findings.md` |

Xong chốt 9 → dừng ở `REVIEW`. Bạn đọc, duyệt bằng `/approve-document`.

## Luật của hành lang

1. **Chốt đỏ → DỪNG NGAY tại đó.** Báo gate nào đỏ, thiếu gì. KHÔNG bỏ qua, KHÔNG `force`.
2. **Gọi lại `/domain` = chạy tiếp từ chốt đang đứng** (suy từ `stage`, không hỏi).
3. **Chỉ chốt 1 được hỏi.** Từ chốt 3 trở đi gặp mơ hồ → `py scripts/decide.py` rồi đi tiếp, KHÔNG dừng hỏi. Thứ cần hỏi lẽ ra đã hỏi ở `/discover` và chốt 1.
4. Chốt 6 **tự suy**: kind boundary có `web`/`mobile` thì chạy, backend-only thì bỏ qua **và nói rõ là bỏ qua** — không im lặng vắng mặt.
5. Mỗi sub-agent spawn bằng `py scripts/build_prompt.py <chốt> …`, nguyên văn output.

## Chốt 1 — chỗ DUY NHẤT của lệnh này được hỏi

Tự suy viết gì, không cần mode:

```
đọc docs/discovery/{capability-map, persona-pool, hypothesis-log} + docs/domain/ đang có gì
  capability chưa Epic nào phủ      → viết Epic
  Epic chưa đủ ≥2 Feature           → viết Feature
  Feature nhắc rule chưa có BR      → viết BR
  persona chưa có Journey           → viết Journey
```

Hai chế độ hỏi như `/discover`: mục **khám phá** (luồng nghiệp vụ, ca biên, ai làm gì khi nào) hỏi bằng **hội thoại mở**, KHÔNG `AskUserQuestion`; mục **quyết định** (chọn giữa hai cách xử đã đếm được) mới dùng `AskUserQuestion` kèm đánh đổi.

**Hỏi TRƯỚC khi viết.** Draft đã thành hình thì câu trả lời sau đó chỉ còn là sửa vặt — người ta ngại phủ nhận thứ đã viết ra.

Không suy được (Discovery chưa đủ) → **STOP, báo user quay lại `/discover`**. Đừng bịa Epic từ hư không.

## Ba lớp, đúng thứ tự

| Lớp | Ở đâu | Ai làm |
|---|---|---|
| **Business** — plain VN, không jargon | `docs/domain/**` | `domain-po-agent` · `domain-ba-agent` |
| **Chữ ký** — `status: APPROVED` | cùng file | bạn OK → `py scripts/domain_approve.py` |
| **Engineering** — bản dịch cho kỹ sư | `docs/architecture/{epics,feat,business-rules}` | `domain-translator-agent` |

**Ký TRƯỚC, dịch SAU.** Dịch bản chưa ký là dịch thứ còn đổi.

## Chốt 9 — rà chéo, thứ từng chốt riêng lẻ không thấy

```
capability ↔ FEAT       mọi năng lực có ≥1 FEAT phủ? (bắt thiếu luồng nền: đăng nhập, phân quyền)
persona    ↔ FEAT       mọi persona có FEAT phục vụ?
ma trận    ↔ AC         mỗi ô `cấm` có ≥1 AC âm?
FEAT       ↔ BR         AC "lỗi nghiệp vụ" trỏ về BR có thật?
FEAT       ↔ HLD/API    mọi FEAT có boundary + contract?
HLD §6.1                ca biên còn ô trống nào?
wave plan  ↔ FEAT       mọi FEAT in-scope có wave? wave nào phụ thuộc thứ chưa giao?
"Câu hỏi cho Author"    còn câu nào treo?
```

Gap **BLOCKER/MAJOR** → ghi `tracking/doc-review-findings.md`, **vá trước**, đừng đẩy sang cho bạn phát hiện hộ. Gate `doc_review` @ `/approve-document` chặn nếu còn gap open.

## Lùi về đây

`/domain` gọi được từ `DESIGN`/`PLAN`/`REVIEW` (back-edge) khi cần sửa doc đã phase-lock. Sửa business xong phải **ký lại + dịch lại**, rồi chạy tiếp các chốt sau (re-gate).

## Forbidden

- Bỏ qua chốt vì "chắc xanh rồi" — gate là thứ trả lời câu đó.
- **Jargon ở `docs/domain/`**: cấm tên class/SQL/API-path/HTTP-status/endpoint. Gate `domain_no_jargon` chặn lúc ký.
- **Dịch mà SÁNG TÁC**: translator clone narrative + map sang format eng + để field kỹ thuật `TBD (DESIGN)`. KHÔNG tự nghĩ AC/scope mới. Gate `translation_parity` đối chiếu.
- Agent **tự approve**. `status: DRAFT` tới khi bạn OK.
- Code sản phẩm. Mockup HTML là tài liệu chốt giao diện, không phải nền code.
