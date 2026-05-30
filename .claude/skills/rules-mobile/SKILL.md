---
name: rules-mobile
description: Convention bắt buộc khi code mobile (Flutter/Dart hoặc tương đương). Hub data-layer theo design.
---

# Rules Mobile Skill

> **Primary skill** cho `kind=mobile` (invoke ngay khi spawn dev/fix/review).

## Khi load
Sub-agent `kind=mobile` ở `/start-dev`, `/fix-bugs`, `/review-dev`.

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

## Naming & structure
- **File**: `snake_case.dart`. **Class/Widget**: `PascalCase`. **Test**: `{module}_test.dart`.
- **Folder**: feature-first (`features/`, `shared/`, `core/`) hoặc theo design chốt.

## Done
- Build apk debug pass, `flutter analyze` pass, test ≥ 60%.
- No hardcoded FCM key / biometric data persisted; chỉ sửa file trong `owned_paths`.
