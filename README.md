# ADLC Design Harness

Bộ khung điều phối cho workflow ADLC (Architecture-Driven Lifecycle): agent làm, người chốt, state
machine giữ thứ tự. **Polyrepo** — repo này chỉ chứa tài liệu + kernel; mỗi boundary được scaffold
ở chốt code của `/run-wave` là một repo riêng.

## Bắt đầu

```bash
pip install -r requirements-harness.txt
py scripts/harness.py state             # STATE hiện tại (mặc định BOOTSTRAP)
```

Fork cho project mới:

```bash
py scripts/reset_for_new_project.py     # dọn artifact của project cũ
py scripts/harness.py state             # xác nhận stage=BOOTSTRAP
```

## 7 lệnh

Xếp theo thứ tự chạy trong một vòng. **Mỗi lệnh tự suy đang đứng ở đâu** — không mode, không cờ
phải nhớ. Gọi lại một lệnh = chạy tiếp từ chốt đang đứng.

| | Lệnh | Làm gì |
|---|---|---|
| 1 | `/discover [D0..D3]` | Giả thuyết → persona + ma trận vai × hành động → event storming → boundary + `PROJECT.md`. Chỗ được hỏi nhiều nhất. Hết D3 bạn đọc và duyệt = chữ ký |
| 2 | `/domain` | Nốt nửa sau, một mạch: Epic/Feature/BR/Journey plain VN → bạn ký → dịch sang bản kỹ thuật → ADR/HLD/API/data-model/events/tích hợp → UX nếu có boundary web/mobile → chia wave → rà chéo |
| 3 | `/approve-document` | Bạn đọc + đánh giá toàn bộ → duyệt = **KHOÁ SCOPE**. Hết phần tài liệu, mở cổng wave |
| 4 | `/run-wave [<N>]` | Một mạch: dựng wave → code từng boundary → review tới sạch → dựng chạy thật → sinh test → chạy test → dogfood. Gate đỏ = dừng đúng chốt đó |
| | `/dogfood [<vai>]` | Chạy lại **một** lăng kính (lượt đầu đã nằm trong `/run-wave`) |
| 5 | `/next-wave` | Đóng wave + mở wave kế, **KHÔNG reset**: snapshot toàn bộ tài liệu → `archive/wave-N/`, đóng gói FEAT/AC đã giao, đánh dấu kết quả theo wave |
| | `/status` | Đang ở đâu · chốt kế là gì · gate còn thiếu gì |

Bảy lệnh chạy qua **25 chốt** (`harness <chốt> complete`) trên **17 state / 39 transition**. Chốt là
đơn vị gate — `dev-handoff`, `test-plan`, `end-wave`… là chốt, không phải lệnh người gõ.

```bash
py scripts/build_prompt.py <chốt> [opts]        # dựng prompt tự chứa cho sub-agent
py scripts/harness.py <chốt> complete '<json>'  # chạy gate + chuyển state
py scripts/gates.py --list                      # gate của từng chốt (nguồn duy nhất)
```

KHÔNG sửa `harness/STATE.json` bằng tay — hook chặn.

## Cấu trúc

```
.
├── CLAUDE.md                       Router — đọc top-to-bottom mỗi session
├── AGENTS.md                       Entry doc cross-IDE (chuẩn agents.md)
├── SETUP-GUIDE.md                  Setup + workflow chi tiết
├── .claude/
│   ├── settings.json              9 hook event + 3 lớp permission (deny → ask → allow)
│   ├── commands/                  7 lệnh (sync từ commands/)
│   └── skills/                    33 skill, nạp theo nhu cầu
├── harness/
│   ├── STATE.json                 Stage hiện tại (không giữ lịch sử)
│   ├── STATE-MACHINE.json         17 state · 39 transition
│   ├── SERVICE-BOUNDARY-MATRIX.json   Boundary + owned_paths + repo_url
│   └── PROTOCOL.md                Giao thức orchestrator ↔ sub-agent
├── agents/                         30 agent (singleton + template materialize theo boundary)
├── commands/                       Nguồn của 7 lệnh
├── scripts/
│   ├── harness.py                 CLI mỏng
│   ├── state.py                   Quản STATE
│   ├── gates.py                   Hàm gate thuần + GATE_RULES (nguồn duy nhất)
│   ├── build_prompt.py            Dựng prompt tự chứa
│   ├── next_wave.py               Đóng wave / mở wave — snapshot, KHÔNG reset
│   ├── decide.py                  Ghi quyết định khi gặp mơ hồ (agent tự gọi)
│   ├── doc_integrity.py           Chống tài liệu trôi khỏi code
│   ├── smoke_test.py              E2E state machine
│   └── hooks/{dispatcher,policies}.py
├── docs/
│   ├── discovery/                 hypothesis-log · persona-pool · capability-map · event-storming · BOUNDARY-MAP · CHARTER
│   ├── domain/                    Lớp BUSINESS plain VN (PO/BA ký)
│   ├── architecture/              PROJECT · epic/feat/BR (bản kỹ thuật) · ADR · HLD · API · data-model · UX · events · tích hợp · infra
│   └── plans/                     WAVE-SEQUENCE.md + wave-{N}.md
├── tracking/
│   ├── _templates/                10 khuôn
│   ├── BC-LEDGER.md               Sổ hợp đồng surface — tích luỹ vĩnh viễn
│   ├── PRODUCTION-READY.md        Sẵn sàng vận hành — 4 nhóm
│   ├── challenge-log.md           Chất vấn spec trước khi code
│   ├── decisions.md               Quyết định tự quyết lúc gặp mơ hồ
│   └── wave-{N}/                  Test case · report · signoff
├── knowledge-base/                 {boundary}.knowledge-graph.yaml
├── archive/wave-{N}/               Snapshot khi đóng wave (cờ "wave đã đóng")
└── services/                       Thư mục làm việc polyrepo (gitignored)
```

## Tài liệu

| File | Mục đích |
|---|---|
| [CLAUDE.md](CLAUDE.md) | Router cho Claude Code |
| [AGENTS.md](AGENTS.md) | Entry doc cross-IDE |
| [SETUP-GUIDE.md](SETUP-GUIDE.md) | Setup + workflow chi tiết |
| [harness/PROTOCOL.md](harness/PROTOCOL.md) | Giao thức orchestrator ↔ sub-agent, failure mode |
| [commands/README.md](commands/README.md) | Lệnh ↔ chốt |
| [agents/README.md](agents/README.md) | Danh mục agent |
| [tracking/README.md](tracking/README.md) | Format tracking theo wave |
| [knowledge-base/README.md](knowledge-base/README.md) | Cấu trúc KG |
| [HARNESS-CHANGELOG.md](HARNESS-CHANGELOG.md) | Nhật ký thay đổi bộ khung (append-only) |

## Kiểm tra sau khi cài

```bash
py scripts/gates.py --selftest    # gate
py scripts/state.py validate      # STATE schema
py scripts/smoke_test.py          # E2E state machine
py scripts/doc_integrity.py       # tài liệu có trôi khỏi code không
```

Bốn cái xanh → cài đặt OK.
