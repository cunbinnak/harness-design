# Hướng dẫn dựng harness

Bộ khung điều phối workflow ADLC. Tài liệu này nói **cách chạy**; cái gì nằm ở đâu → [README.md](README.md),
luật bắt buộc → [CLAUDE.md](CLAUDE.md), giao thức + failure mode → [harness/PROTOCOL.md](harness/PROTOCOL.md).

## Cần có trước

- Python 3.14+
- Docker (dựng hạ tầng lúc dev/test)
- Git
- IDE: VSCode hoặc Cursor

```bash
pip install -r requirements-harness.txt
py scripts/harness.py state          # STATE hiện tại (mặc định BOOTSTRAP)
```

## Fork cho project mới

```bash
git clone <fork-url> && cd <project>
py scripts/reset_for_new_project.py    # dọn artifact của project cũ
py scripts/harness.py state            # phải thấy stage: BOOTSTRAP
```

`reset_for_new_project.py` dọn cả `archive/wave-*/` — thư mục đó kiêm **cờ "wave đã đóng"**, để sót
thì wave 1 của project mới bị coi là đã đóng và không đóng lại được.

## Vòng chạy hằng ngày

Bảy lệnh, gõ theo thứ tự. Mỗi lệnh tự suy đang đứng ở chốt nào; gọi lại = chạy tiếp.

```
/discover          → giả thuyết · persona + ma trận vai × hành động · event storming · boundary
                     (bạn đọc + duyệt = chữ ký)
/domain            → nghiệp vụ plain VN → bạn ký → dịch kỹ thuật → ADR/HLD/API/data-model/events
                     → UX nếu có web/mobile → chia wave → rà chéo
/approve-document  → bạn đọc + đánh giá toàn bộ → duyệt = KHOÁ SCOPE
/run-wave [<N>]    → dựng wave · code · review · dựng chạy thật · sinh test · chạy test · dogfood
/dogfood [<vai>]   → chạy lại một lăng kính
/next-wave         → đóng wave + mở wave kế (snapshot, KHÔNG reset)
/status            → đang ở đâu · chốt kế · gate còn thiếu gì
```

Bên dưới, mỗi lệnh chạy qua nhiều **chốt**. Hai lệnh của một chốt:

```bash
py scripts/build_prompt.py <chốt> [opts]        # dựng prompt tự chứa cho sub-agent
py scripts/harness.py <chốt> complete '<json>'  # chạy gate + chuyển state
```

Xem trạng thái trước khi đi tiếp:

```bash
py scripts/harness.py state
py scripts/harness.py can <chốt>     # chốt này có được phép chạy không
py scripts/gates.py --list           # gate của TỪNG chốt — nguồn duy nhất, đừng chép ra chỗ khác
```

KHÔNG sửa `harness/STATE.json` bằng tay — hook chặn.

## Khi gate đỏ

Gate đỏ **không phải lỗi cần lách**. Thông báo nói thiếu gì và ở file nào; sửa file đó rồi chạy lại
đúng chốt ấy. Ba việc KHÔNG được làm:

- sửa `STATE.json` cho qua
- `force: true` để đi tiếp (mọi lần force đều bị ghi vào `tracking/decisions.md`)
- bỏ qua chốt đỏ rồi chạy chốt sau

Muốn sửa tài liệu đã qua stage sở hữu → **lùi** về lệnh sở hữu nó (`/domain` gọi được từ
DESIGN/PLAN/REVIEW), sửa, rồi tiến lại để gate chạy lại. Sau khi wave đã ship → đổi ở **wave sau**.

## Hook

Cấu hình: `.claude/settings.json` — 9 sự kiện, tất cả đi qua `scripts/hooks/dispatcher.py`.

| Sự kiện | Làm gì |
|---|---|
| SessionStart · UserPromptSubmit · Notification | Nhồi header `[HARNESS stage=… \| next: …]`, reset cờ mỗi lượt |
| PreToolUse(Bash) | Chạy gate khi thấy `harness <chốt> complete`; đỏ thì chặn |
| PreToolUse(Write\|Edit\|MultiEdit\|NotebookEdit) | Chặn file kernel · 3 file proof · doc phase-locked ngoài stage sở hữu · `services/**` sai vai |
| PreToolUse(Task) | Chặn spawn agent bằng prompt tự viết (phải dùng `build_prompt.py`) |
| PreToolUse(Skill\|SlashCommand) | Chặn MAIN tự nối pipeline bằng SlashCommand |
| PostToolUse(Bash) | no-op |
| SubagentStop | Kiểm RETURN SCHEMA |
| Stop | Build/lint/test wave-scoped khi có sửa `services/`; đỏ thì chặn |
| PreCompact | Ghim STATE vào bản tóm tắt |

Hook crash → cho qua (fail-open). Permission là hàng rào NGOÀI, hook là hàng rào TRONG — `allow` rộng
KHÔNG mở khoá được thứ hook chặn.

## Kiểm tra sức khoẻ bộ khung

```bash
py scripts/gates.py --selftest      # gate
py scripts/state.py validate        # STATE khớp schema
py scripts/smoke_test.py            # E2E state machine
py scripts/doc_integrity.py         # tài liệu có trôi khỏi code không
py scripts/next_wave.py --selftest  # đóng/mở wave
```

## Gỡ rối

**`state.py validate` đỏ** — `harness/STATE.json` lệch schema của `STATE-MACHINE.json[version]`.

**Hook chặn lệnh** — đọc thông báo, nó nói lý do cụ thể. Đừng sửa `STATE.json`; sửa cái thiếu.

**Sub-agent trả về không phải JSON** — xem mục RETURN SCHEMA trong file agent; `SubagentStop` cảnh báo
chứ không chặn.

**Skill không nạp** — đường dẫn phải là `.claude/skills/<tên>/SKILL.md`, `name:` trong frontmatter phải
khớp tên thư mục; nạp lại session.

**Tài liệu nói một đằng, code một nẻo** — chạy `py scripts/doc_integrity.py`. Nó bắt: lệnh đã xoá còn
nhắc trong doc · tên gate không tồn tại · gate khai mà không dispatch · gate viết mà không ai gọi ·
con số "N lệnh" khai sai · command chưa sync.
