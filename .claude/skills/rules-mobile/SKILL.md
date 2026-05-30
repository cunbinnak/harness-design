---
name: rules-mobile
description: Convention bắt buộc khi code mobile (Flutter/Dart).
---

# Rules Mobile Skill

## Khi load
Sub-agent kind=mobile ở /start-dev, /fix-bugs cho boundary mobile.

## Quy ước bắt buộc
1. **Codegen**: `flutter pub run build_runner build` refresh trước khi code.
2. **Widget**: implement theo UX spec, Material 3.
3. **GraphQL ops**: wire theo INTEG-MOB mapping; KHÔNG invent op name.
4. **Auth**: qua bff-auth deep-link.
5. **State**: Riverpod 2; scope provider per child.
6. **Offline queue**: mutations marked "queue if offline" cần idempotency strategy.
7. **NO business logic** — validate ở BFF/backend.
8. **Test**: flutter_test widget; coverage ≥ 60%.

## Done
- Build apk debug pass, analyze pass, test pass.
- No hardcoded FCM key/biometric data persisted.
