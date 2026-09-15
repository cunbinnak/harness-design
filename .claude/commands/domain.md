---
name: domain
description: "Nốt nửa sau tài liệu, một mạch 9 chốt: nghiệp vụ → ký → dịch → thiết kế → UX → chia wave → rà chéo. Dừng ở REVIEW."
argument-hint: "(không arg — chạy tiếp từ chốt đang đứng)  ·  hoặc gợi ý phạm vi: \"đặt lịch\""
when_state: [DOMAIN_AUTHORING, DESIGN, PLAN, REVIEW, WAVE_OPEN, DONE]
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
2. **KHÔNG hỏi user ở bất kỳ chốt nào.** `/discover` đã hỏi rất sâu và câu trả lời nằm ở
   `hypothesis-log` · `persona-pool` (ma trận vai × hành động) · `capability-map` ·
   `event-storming/ES-*` · `BOUNDARY-MAP` · `CHARTER` · `PROJECT.md`. Bắt user trả lời lại là
   hỏi hai lần cùng một câu.
   Bí thì theo thứ tự: **(1)** tìm trong tài liệu khám phá → **(2)** `py scripts/decide.py`
   (script từ chối dòng không dẫn được về artifact — không dẫn về đâu được nghĩa là chưa đọc đủ)
   → **(3)** chặn cứng thật thì một dòng `tracking/blockers.md`, chuyển việc khác, báo gộp cuối.
   User chỉ CHẠM hai lần trong cả hành lang: **đọc bản nghiệp vụ để ký** (chốt 2) và **xem giao
   diện** ở `/approve-document`. Cả hai đều là ĐỌC + DUYỆT, không phải trả lời câu hỏi.
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

## Gọi sau khi đã chạy wave — bổ sung + chia lại

Kế hoạch không cố định từ đầu. Chạy xong một wave mà lộ chỗ thiếu tài liệu thì **không sửa tại chỗ,
không dừng wave đang chạy**: đợi `/next-wave` lưu wave vào `archive/`, rồi gọi `/domain`.

| Đang ở | Nghĩa | Vào chốt |
|---|---|---|
| `WAVE_OPEN` | còn wave trong kế hoạch, chưa code wave kế | 1 |
| `DONE` | hết WAVE-SEQUENCE mà còn việc → thêm wave | 1 (gate `replan_entry`: wave vừa xong phải đã có archive) |

Chỗ thiếu cần **năng lực · vai · event · boundary mới** (chưa có trong tài liệu khám phá) → `/discover
D1|D2|D3` trước — đó là quyết định phạm vi, cần hỏi user. Lúc vào, dấu ký nghiệp vụ + thiết kế bị hạ
về DRAFT: phần sửa phải được ký lại thật ở chốt 2 và `/approve-document`.

Đi đủ 9 chốt như lượt đầu, chỉ khác ở hai chỗ:

- **Chốt 1** viết phần bù. Nguồn: dòng `wave sau` ở `tracking/wave-*/dogfood-report.md` ·
  `tracking/blockers.md` · chỗ thiếu người vận hành báo. Sửa thứ đã giao → FEAT mới, hoặc thêm AC vào
  FEAT cũ; không sửa lặng lẽ AC đã giao.
- **Chốt 8** chia lại: **phần bù chen vào ngay wave kế, tính năng đã xếp lùi dần ra sau**, tràn thì
  sinh wave mới. Không dồn phần bù ra cuối — các wave ở giữa sẽ xây trên nền đang thiếu. Wave đã đóng
  không đổi. Gate `replan_integrity` kiểm (skill `implementation-plan` §Chia lại).

Xong chốt 9 → `/approve-document` lại (gate `replan_approved` chặn `start-wave` tới khi duyệt) →
`/run-wave` chạy wave kế theo kế hoạch mới.

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
