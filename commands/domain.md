---
name: domain
description: "Viết tài liệu nghiệp vụ: TỰ SUY thiếu gì viết nấy (Epic → Feature → BR → Journey/Persona) → trình bạn duyệt → ký → dịch sang bản kỹ thuật → sang Design. Không cần mode."
argument-hint: "(không arg — tự suy)  ·  hoặc gợi ý phạm vi: \"đặt lịch\""
when_state: [DOMAIN_AUTHORING, DESIGN]
sets_stage: DOMAIN_AUTHORING
spawn:
  agent: "domain-po-agent · domain-ba-agent · domain-translator-agent"
  skills: [domain-po, domain-ba, domain-translator, business-analysis]
gates: [{type: domain_gate}, {type: domain_signed}, {type: domain_stamped}, {type: domain_no_jargon}, {type: translation_parity}]
---

# /domain — tài liệu nghiệp vụ

Gộp 5 lệnh cũ. **Không có mode** — thiếu gì thì viết nấy, suy từ Discovery đã chốt.

## Tự suy viết gì

```
đọc  docs/discovery/{capability-map, persona-pool, hypothesis-log}.md
     + docs/domain/ đang có gì
     ↓
capability chưa Epic nào phủ        → viết Epic
Epic chưa đủ ≥2 Feature             → viết Feature
Feature nhắc rule chưa có BR        → viết BR
persona chưa có Journey             → viết Journey
     ↓  (thứ tự này là phụ thuộc, không phải sở thích:
        Feature cần Epic cha, BR cần Feature dẫn nó)
trình user → sửa → LẶP tới khi user OK
     ↓
user OK = CHỮ KÝ → ký (status APPROVED) → dịch sang docs/architecture/ → DESIGN
```

Không suy được (Discovery chưa đủ) → **STOP, báo user quay lại `/discover`**. Đừng bịa Epic từ hư không.

## Hỏi thế nào

Đây vẫn là chỗ **được hỏi**, và hỏi nhiều là đúng. Hai chế độ như Discovery:

| Loại | Cách hỏi |
|---|---|
| **Khám phá** — luồng nghiệp vụ, ca biên, ai làm gì khi nào | hội thoại **mở**. KHÔNG `AskUserQuestion` — option mớm lời |
| **Quyết định** — chọn giữa hai cách xử đã đếm được | `AskUserQuestion` + đánh đổi |

**Hỏi TRƯỚC khi viết**, không viết xong rồi mới hỏi. Draft viết ra rồi thì câu trả lời sau đó chỉ còn là sửa vặt — người ta ngại phủ nhận thứ đã thành hình.

## Ba tầng, đúng thứ tự

| Tầng | Ở đâu | Ai làm |
|---|---|---|
| **Business** — plain VN, không jargon | `docs/domain/{epics,feat,business-rules,journeys,personas}/` | `domain-po-agent` (Epic/Feature/Journey) · `domain-ba-agent` (BR/Persona) |
| **Chữ ký** — `status: APPROVED` | cùng file | bạn OK → `py scripts/domain_approve.py` stamp |
| **Engineering** — bản dịch cho kỹ sư | `docs/architecture/{epics,feat,business-rules}/` | `domain-translator-agent` |

**Ký TRƯỚC, dịch SAU.** Dịch bản chưa ký là dịch thứ còn đổi.

## Chạy

```bash
py scripts/build_prompt.py domain-po --mode <EPIC|FEATURE|JOURNEY>   # hoặc domain-ba --mode <BR|PERSONA>
py scripts/harness.py domain-po complete '{...}'
# ... lặp tới khi đủ + user OK
py scripts/domain_approve.py <id|all>
py scripts/harness.py domain-approve complete '{...}'
py scripts/build_prompt.py domain-translate
py scripts/harness.py domain-translate complete '{...}'
py scripts/harness.py domain-end complete '{...}'          # → DESIGN
```

## Luật

- **NGÔN NGỮ NGHIỆP VỤ THUẦN** ở `docs/domain/`: cấm tên class/SQL/API-path/HTTP-status/schema/endpoint. Gate `domain_no_jargon` chặn lúc ký.
- **Dịch KHÔNG sáng tác**: translator clone narrative + map sang format eng + để field kỹ thuật dạng `TBD (DESIGN)`. KHÔNG tự nghĩ AC/scope mới. Gate `translation_parity` đối chiếu.
- **`status: DRAFT` tới khi bạn OK.** Agent KHÔNG tự approve.
- Feature: **≥4 AC dạng BDD** (Cho/Khi/Thì) mô tả hành vi nghiệp vụ — happy + validation + error + a11y.
- Epic: **≥2 Feature** (ít hơn thì gộp vào Epic khác).

## Lùi về đây từ DESIGN

`/domain` gọi được từ `DESIGN` (back-edge) khi cần sửa narrative/AC — doc business bị phase-lock ở DESIGN. Sửa xong phải **ký lại + dịch lại**, rồi `/design` tiến lại (re-gate).

## Done

Gate `domain_gate` (≥1 epic + ≥1 feat + ≥1 BR ở `docs/architecture/`) xanh → `DESIGN`.
