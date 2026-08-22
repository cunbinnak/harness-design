---
name: domain
description: "Nốt nửa sau tài liệu, một mạch 9 chốt: nghiệp vụ → ký → dịch → thiết kế → UX → chia wave → rà chéo. Dừng ở REVIEW."
argument-hint: "(không arg — chạy tiếp từ chốt đang đứng)  ·  hoặc gợi ý phạm vi: \"đặt lịch\""
when_state: [DOMAIN_AUTHORING, DESIGN, PLAN, REVIEW]
spawn:
  agent: "domain-po-agent · domain-ba-agent · domain-translator-agent · solution-architect-agent · ux-designer-agent · program-planner-agent · review-document-agent"
  skills: [domain-po, domain-ba, domain-translator, technical-design, ux-design, implementation-plan, business-analysis]
gates: "mỗi chốt giữ gate cũ của nó — py scripts/gates.py --list"
---

# /domain

Không arg → chạy tiếp từ chốt đang đứng (suy từ `stage`).

| # | Chốt | `harness <id> complete` |
|---|---|---|
| 1 | Epic/Feature/BR/Journey — business, plain VN | `domain-po` · `domain-ba` (lặp) |
| 2 | Ký business | `domain-approve` |
| 3 | Dịch sang bản kỹ thuật | `domain-translate` |
| 4 | Đóng lớp nghiệp vụ | `domain-end` |
| 5 | ADR · HLD · API · data-model · events · tích hợp | `design` |
| 6 | UX — **chỉ khi kind có web/mobile**: DESIGN-SYSTEM **trước** → mockup → đi tiếp (user xem+chốt ở `/approve-document`) | `design-ux` |
| 7 | Đóng thiết kế | `design-end` |
| 8 | WAVE-SEQUENCE + wave-{N} + MATRIX + KG | `plan` |
| 9 | Rà chéo toàn bộ | `review-document` (no-arg) |

> Gate từng chốt: `py scripts/gates.py --list` (SoT = `GATE_RULES`; đừng chép vào đây — bản chép trôi ngay lần đổi gate kế).

Xong chốt 9 → dừng ở `REVIEW`, chờ `/approve-document`.

## Luật

1. Chốt đỏ → **DỪNG tại đó**, báo thiếu gì. KHÔNG bỏ qua, KHÔNG `force`.
2. **Chỉ chốt 1 được hỏi.** Từ chốt 3 gặp mơ hồ → `py scripts/decide.py` rồi đi tiếp.
3. Chốt 6 tự suy theo kind boundary; backend-only → bỏ qua **và nói rõ là bỏ qua**.
   Có UI: vẽ xong **đi tiếp**, KHÔNG dừng. Giao diện chỉ được user xem và chốt MỘT lần, ở
   `/approve-document` — chỗ họ vốn đang đọc cả bộ tài liệu. Chốt 6 chỉ để lại thứ đáng xem:
   đường dẫn mockup + màn nên xem trước, ghi vào `SCREEN-MAP.md` §Chốt. User chốt → ghi `Chốt bởi user: <ISO>` vào `SCREEN-MAP.md` (gate `mockup_signed` @`/approve-document` đòi dòng này).
4. Spawn bằng `py scripts/build_prompt.py <chốt> …`, nguyên văn output.

## Chốt 1 — tự suy viết gì

```
đọc capability-map + persona-pool + hypothesis-log  ×  docs/domain/ đang có gì
  capability chưa Epic phủ    → Epic
  Epic chưa đủ ≥2 Feature     → Feature
  Feature nhắc rule chưa có BR → BR
  persona chưa có Journey     → Journey
```

Hai chế độ hỏi như `/discover`. **Hỏi TRƯỚC khi viết.** Discovery chưa đủ để suy → STOP, báo user quay lại `/discover`.

Ba lớp: business `docs/domain/**` → **ký** (`status: APPROVED`) → dịch `docs/architecture/{epics,feat,business-rules}`. Ký trước, dịch sau.

## Chốt 9 — rà chéo

```
capability ↔ FEAT    mọi năng lực có ≥1 FEAT phủ? (bắt thiếu luồng nền: đăng nhập, phân quyền)
persona    ↔ FEAT    mọi persona có FEAT phục vụ?
ma trận    ↔ AC      mỗi ô `cấm` có ≥1 AC âm?
FEAT       ↔ BR      AC "lỗi nghiệp vụ" trỏ BR có thật?
FEAT       ↔ HLD/API mọi FEAT có boundary + contract?
HLD §6.1             ca biên còn ô trống nào?
wave plan  ↔ FEAT    mọi FEAT in-scope có wave? wave nào phụ thuộc thứ chưa giao?
```

Gap BLOCKER/MAJOR → ghi `doc-review-findings.md` rồi **vá trước**. Gate `doc_review` chặn approve nếu còn gap open.

## Forbidden

- Jargon ở `docs/domain/`: tên class/SQL/API-path/HTTP-status/endpoint.
- Dịch mà **sáng tác** — clone narrative, field kỹ thuật để `TBD (DESIGN)`, KHÔNG tự nghĩ AC/scope mới.
- Agent tự approve. `status: DRAFT` tới khi user OK.
- Code sản phẩm. Mockup HTML là tài liệu, không phải nền code.
