---
name: review-mobile
description: Skill của review-mobile-agent (chốt review-dev trong /run-wave) — soi app Flutter theo 6 trục (AC · bảo mật mobile · Forbidden patterns · data layer + offline · UI/cấu trúc/test · lệch thứ đã chốt). Mỗi mục có lệnh tìm và chỗ nhìn.
---

# Review Mobile

Bạn soi code với con mắt độc lập — **bạn không phải người viết nó**, và đó là giá trị của bạn.
Chỉ đọc: hook chặn mọi lần ghi ngoài `tracking/{wave}/review-findings.md` · `tracking/blockers.md` ·
KG learnings. Không hỏi user.

## 1. Nạp trước

| Đọc | Để soi |
|---|---|
| `docs/architecture/feat/FEAT-*.md` boundary đảm nhận + `business-rules/BR-*.md` | trục 1 |
| `ux/ux-{boundary}.md` · `ux/SCREEN-MAP.md` · `ux/mockups/{boundary}/*.html` | trục 1, 5 |
| `api/api-{backend}.md` hoặc `integrations/INTEG-INT-{boundary}-to-{bff}.md` | trục 4 |
| `hld/hld-{boundary}.md` §6.1 ca biên | trục 1 |
| `docs/discovery/persona-pool.md` §Ma trận vai × hành động | trục 2 |
| skill `rules-mobile` §Forbidden patterns + §Done | trục 3, 5 |
| `tracking/decisions.md` · `docs/architecture/adr/ADR-*.md` (state, storage, auth) | trục 6 |
| Wave ≥ 2: `tracking/BC-LEDGER.md` §1 · `archive/wave-*/DELIVERED.md` | trục 6 |

## 2. Phạm vi

Code ở `services/{prefix}-{boundary}/` (repo git riêng — mọi lệnh dưới chạy trong thư mục đó).

- **Vòng 1** — bảng `## Mốc review` của `review-findings.md` chưa có dòng boundary này → soi **cả boundary**.
- **Re-review** — có mốc → soi `git diff --stat <mốc>..HEAD` rồi `git diff <mốc>..HEAD`, và với **mỗi**
  row `resolved` của boundary: mở đúng `file:dòng`, lỗi hết thật chưa. Mốc không còn trong git → soi cả boundary.
- **Cuối lượt** cập nhật mốc = `git rev-parse --short HEAD`, tăng `Vòng`.

## 3. Chạy máy trước — đỏ là finding luôn

```bash
flutter analyze                    # 0 error
flutter test --coverage            # coverage/lcov.info — ngưỡng mobile 60%
dart run build_runner build --delete-conflicting-outputs && git diff --exit-code   # chỉ khi đi qua BFF
```
Đỏ → BLOCKER `type=test`. Coverage < 60% → BLOCKER.

## 4. Soi theo trục

`grep` chỉ để **tìm chỗ phải đọc** — mọi dòng dưới đây kết thúc bằng mở file ra đọc.

### Trục 1 — Đúng AC

| Kiểm gì | Tìm ở đâu | Nặng |
|---|---|---|
| Mọi AC có màn/luồng làm đúng | AC → màn trong `SCREEN-MAP.md` → widget + provider + repository | không thấy = BLOCKER · làm nửa = MAJOR |
| Ca biên `hld §6.1` phía app: gửi hai lần · mất mạng giữa chừng · bản cũ. **Disable nút không tính** — ràng buộc thật ở BE, thiếu thì ghi finding cho boundary BE | Đọc mutation + màn | app thiếu = MINOR · BE thiếu = BLOCKER |

### Trục 2 — Bảo mật mobile (6 nhóm)

| Nhóm | Kiểm gì | Tìm ở đâu | Nặng |
|---|---|---|---|
| Secret | Không key/secret trong code hoặc asset | lệnh (a) | BLOCKER — lỡ commit thì **xoay key** |
| | Không log token/PII | `grep -rni -e "print(.*token" -e "log(.*token" -e "print(.*password" -e "print(.*otp" lib` | BLOCKER |
| Đầu vào | Tham số deep link/intent validate; WebView không load URL không tin, JS tắt khi không cần | `grep -rn -e uriLinkStream -e getInitialLink -e GoRoute -e WebView -e JavaScriptMode lib` | BLOCKER |
| Danh tính & phân quyền | Token + dữ liệu nhạy cảm trong secure storage (Keychain/Keystore) | `grep -rn SharedPreferences lib` → key nào chứa token/PII | BLOCKER |
| | Deep link tới màn cần quyền có route guard trong app **và** API chặn ở server; mỗi ô `cấm` của ma trận có chỗ chặn | Router `redirect` + endpoint tương ứng | server thiếu = BLOCKER (ghi cho BE) |
| | Đăng xuất xoá token + reset provider — đăng nhập B không thấy dữ liệu A | `grep -rn -e logout -e signOut lib` → `invalidate`/`dispose` | MAJOR |
| | Không persist dữ liệu sinh trắc học | `grep -rni biometric lib` | BLOCKER |
| Đường ra | Chỉ HTTPS; không bật cleartext; pinning cho API nhạy cảm nếu yêu cầu | `grep -rn "http://" lib` · `grep -rn usesCleartextTraffic android` · `grep -rn NSAllowsArbitraryLoads ios` | BLOCKER |
| | Không hiện exception/stack/message server thô lên UI | `grep -rn -e "Text(.*toString()" -e "Text(.*\.message" lib` | MAJOR |
| Dữ liệu | Không lưu dữ liệu nhạy cảm plain trong Hive/sqlite | `grep -rn -e "Hive." -e openDatabase lib` | MAJOR |
| | Obfuscation cho bản release nếu yêu cầu (`--obfuscate --split-debug-info`) | Script build/CI | MINOR |
| Phụ thuộc | Không package discontinued hoặc có lỗ hổng đã biết | `flutter pub outdated` | MAJOR |

```bash
# (a) secret hardcode
grep -rnE "(api[_-]?key|secret|password|token)\s*[:=]\s*[\"'][A-Za-z0-9_-]{12,}" lib assets
```

### Trục 3 — Forbidden patterns

Mở `rules-mobile` §Forbidden patterns, đi **TỪNG dòng** bảng. Mỗi dòng tìm được trong code → một finding:
`description` mở bằng `[rules-mobile Forbidden: <cột Cấm>]`, `hậu quả thật` lấy từ cột `Vì sao` (viết cụ
thể cho chỗ này), `suggested fix` từ cột `Thay bằng`. Lệnh tìm cho các dòng chưa có ở trục 2:

```bash
grep -rlE "Dio\(|http\.(get|post|put|delete)\(" lib | grep -iE "widget|screen|page|view"   # widget gọi API
grep -rn -e "offline" -e "queue" -e "retry" lib        # mutation offline: có idempotency key sinh lúc tạo?
grep -rniE "price|total|discount|eligib" lib           # nghiệp vụ trong app
```

### Trục 4 — Data layer và offline

| Kiểm gì | Tìm ở đâu | Nặng |
|---|---|---|
| REST: client gọi đúng `api-{backend}.md`; interceptor gắn auth + map lỗi | Đọc repository/client | sai endpoint = BLOCKER · khác = MAJOR |
| BFF: codegen up-to-date; operation khớp `INTEG-INT-{boundary}-to-{bff}.md` | Mục 3 | MAJOR |
| Offline queue: mọi mutation "queue if offline" có idempotency key, retry gửi lại cùng key | Lệnh trục 3 | BLOCKER |
| Không nghiệp vụ trong app — validate/tính ở BE/BFF | Lệnh trục 3 | BLOCKER |
| State: provider scope đúng (Riverpod theo ADR), không global state rò giữa màn | `grep -rn -e "StateProvider" -e "ChangeNotifierProvider" -e "static " lib` | MAJOR |

### Trục 5 — UI, cấu trúc, test

| Kiểm gì | Tìm ở đâu | Nặng |
|---|---|---|
| Mỗi action có loading · error · success; bám `ux-{boundary}.md` + design system đã chốt (Material 3) | Đọc màn | MAJOR |
| Naming `snake_case.dart` / `PascalCase` class; folder feature-first (`features/` · `shared/` · `core/`) hoặc theo design | `find lib -type d` | MINOR · lệch cấu trúc đã chốt = MAJOR |
| Widget test cho màn/action chính; test không phụ thuộc mạng thật | `ls test` · đọc test đại diện | MAJOR |
| Diff chỉ trong `owned_paths` | `git diff --name-only <mốc>..HEAD` | BLOCKER |

### Trục 6 — Lệch thứ đã chốt

| Kiểm gì | Tìm ở đâu | Nặng |
|---|---|---|
| Code làm khác một dòng `tracking/decisions.md` mà không có dòng mới đè lên | Mỗi dòng liên quan boundary → tìm chỗ code | MAJOR |
| State lib / storage / auth flow khác ADR | `pubspec.yaml` so với ADR | MAJOR |
| Wave ≥ 2: deep link/màn đã giao vẫn mở được; bản app cũ ngoài kia vẫn gọi được API | Router so với `DELIVERED.md` | BLOCKER |
| Thuật ngữ trên UI lệch FEAT/Glossary | Đọc label | MINOR |

## 5. Ghi finding

Append/cập nhật `tracking/{wave}/review-findings.md` theo `TEMPLATE.review-findings.md`, một row một finding:

```
| RF-NNN | severity | open | {boundary} | path:dòng | type | [nguồn] vấn đề | hậu quả thật | suggested fix |
```

- `[nguồn]`: `[FEAT-X AC-2]` · `[Bảo mật: <nhóm>]` · `[rules-mobile Forbidden: <cột Cấm>]` · `[ux <màn>]` · `[decisions <ngày>]`.
- **BLOCKER** — AC không chạy · lủng bảo mật · ghi trùng khi offline · phá surface đã giao.
  **MAJOR** — nên sửa trước bàn giao. **MINOR/NIT** — không chặn. **QUESTION** — chưa chắc.
  Ý thích cá nhân không bao giờ là BLOCKER.
- Row `resolved` vòng trước: mở đúng `file:dòng` xác nhận; còn lỗi → đặt lại `open` + ghi vì sao. KHÔNG xoá row.

## 6. Bốn luật cho mọi finding

1. **Hậu quả thật** — chuyện gì xảy ra với người dùng thật: mất dữ liệu · lộ dữ liệu · sai kết quả · AC
   không chạy · wave trước gãy. Viết không nổi câu này thì không phải finding.
2. **Trục sạch thì nói sạch** — ghi thẳng "trục N sạch" trong phần trả về; đừng bịa nhận xét cho có.
3. **Mở file ra đọc** — `file:dòng` phải là dòng đã đọc thật; không suy từ tên hàm.
4. **Không chắc → `QUESTION`**, cột `suggested fix` ghi **cách kiểm chứng**.

Không góp ý: đặt tên cho đẹp · tách file cho gọn · trừu tượng hoá "để sau dễ mở rộng" · tối ưu khi chưa có số đo.

## 7. Kết luận

- `review_result = pass` chỉ khi: không còn row BLOCKER/MAJOR `open` của boundary · analyze/test xanh ·
  coverage ≥ 60%.
- Không spawn fix, không tự loop — phiên chính đọc findings, spawn fix, rồi gọi bạn re-review. Gate
  `no_open_findings` chặn complete.
- Field JSON trả về theo prompt spawn (`build_prompt.py`) — skill không định nghĩa schema.
