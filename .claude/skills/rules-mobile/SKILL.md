---
name: rules-mobile
description: Convention bắt buộc khi code mobile (Flutter/Dart hoặc tương đương). Hub data-layer theo design.
---

# Rules Mobile Skill

> **Primary skill** cho `kind=mobile` (invoke ngay khi spawn dev/fix/review).

## Khi load
Sub-agent `kind=mobile` — chốt code · sửa bug · review của `/run-wave`.

## Data layer — theo thiết kế dự án (xem integrations design)
- **Default — REST trực tiếp backend**: client (Dio/http) gọi contract `api-{backend}.md`; interceptor gắn auth + map error.
- **Optional — qua BFF/GraphQL**: CHỈ khi design có boundary `bff`. `flutter pub run build_runner build` refresh trước khi code; wire ops theo `integrations/INTEG-INT-{mobile}-to-{bff}.md`; KHÔNG invent op name.

## Quy ước bắt buộc
1. **Widget**: implement theo `ux-{boundary}.md`, Material 3 (hoặc design system đã chốt).
2. **Wire actions**: map đúng endpoint/op integration design; handle loading / error / success.
3. **Auth**: theo auth flow đã chốt (deep-link / token refresh).
4. **State**: Riverpod 2 (hoặc state mgmt đã chốt); scope provider per child.
5. **Offline queue**: mutation "queue if offline" cần idempotency strategy.
6. **NO business logic** — validate ở backend (hoặc BFF).
7. **Test**: flutter_test widget; coverage ≥ **60%**.

## Forbidden patterns

> Lỗi stack này hay dính. Dev né lúc viết; `review-mobile` đi **từng dòng** bảng này lúc soi — cột
> `Vì sao` thành `hậu quả thật` của finding, cột `Thay bằng` thành `suggested fix`.

| Cấm | Vì sao | Thay bằng |
|---|---|---|
| Token/dữ liệu nhạy cảm trong `SharedPreferences` | Máy root hoặc bản backup đọc được | Secure storage (Keychain/Keystore) |
| API key/secret trong code hoặc asset | Giải nén APK/IPA là thấy | Server giữ secret; key public thì giới hạn theo package/bundle id |
| Widget gọi API trực tiếp | Đổi API là sửa khắp nơi; không test được | Repository + provider |
| Mutation offline retry không có idempotency key | Mạng chập chờn là ghi hai lần | Key sinh lúc tạo mutation, gửi lại cùng key mỗi lần retry |
| Hiện `exception.toString()`/stack/message server lên UI | Lộ nội bộ; người dùng không biết làm gì | Map error code → thông báo theo `ux-{boundary}.md` |
| Deep link mở thẳng màn cần quyền, chỉ dựa vào giấu nút | Vai bị cấm vẫn vào được bằng link | Route guard trong app + server chặn API |
| Tham số deep link/intent không validate; WebView load URL từ ngoài, bật JS thừa | Mở màn với dữ liệu giả; XSS trong WebView | Whitelist host/path; tắt JS khi không cần |
| Log token/PII bằng `print`/`debugPrint` | Logcat/console đọc được | Logger có mask; tắt log ở release |
| Gọi HTTP thường, bật cleartext traffic | Nghe lén trên wifi công cộng | HTTPS; pinning cho API nhạy cảm nếu yêu cầu |
| Tính nghiệp vụ trong app | Bản app cũ ngoài kia tính theo luật cũ | Backend trả kết quả |
| Provider giữ dữ liệu user sống qua đăng xuất | Đăng nhập B vẫn thấy dữ liệu A | Scope provider; invalidate khi logout |
| Lưu dữ liệu sinh trắc học | Không thu hồi được khi lộ | Dùng API sinh trắc của OS, không lưu |

## Naming & structure
- **File**: `snake_case.dart`. **Class/Widget**: `PascalCase`. **Test**: `{module}_test.dart`.
- **Folder**: feature-first (`features/`, `shared/`, `core/`) hoặc theo design chốt.

## Done
- Build apk debug pass, `flutter analyze` pass, test ≥ 60%.
- No hardcoded FCM key / biometric data persisted; chỉ sửa file trong `owned_paths`.
