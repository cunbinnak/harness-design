---
name: review-mobile
description: Self-review mobile — analyze, data layer khớp design, offline idempotency, security (secure storage/transport/deeplink), no hardcoded keys, coverage.
---

# Review Mobile Skill

> Checklist source-of-truth cho `review-mobile-agent` ở `/review-dev`. Fail → spawn fix → re-review → loop tới pass.

## Lệnh chạy
```bash
flutter analyze                   # static analysis
flutter test --coverage          # widget test + coverage
git diff --name-only main...HEAD
```

## Checklist (PASS/FAIL/NA)
1. **Build + analyze** xanh (`flutter analyze` 0 error); test ≥ **60%**.
2. **Data layer khớp design**:
   - REST (default): client (Dio/http) gọi đúng `api-{backend}.md`; interceptor auth.
   - BFF (nếu có): codegen up-to-date (`build_runner`); op khớp `integrations/INTEG-INT-{mobile}-to-{bff}.md`.
3. **Offline queue**: mọi mutation "queue if offline" có idempotency strategy (key/dedup) — FAIL nếu retry gây double-write.
4. **No business logic** — validate ở BE/BFF.
5. **No hardcoded secrets**: FCM key, biometric data không persist/hardcode.
6. **State**: provider scope đúng (Riverpod), không global state rò rỉ giữa screen.
7. **Security (mobile)**:
   - **Token storage**: access/refresh token + dữ liệu nhạy cảm vào secure storage (Keychain/Keystore), KHÔNG `SharedPreferences` plain.
   - **Transport**: chỉ HTTPS; cert pinning cho API nhạy cảm (nếu yêu cầu).
   - **Deeplink / WebView**: validate input từ deeplink/intent; WebView không load URL không tin, tắt JS nếu không cần.
   - **No secret in bundle**: không hardcode API key/secret trong code/asset; bật obfuscation nếu yêu cầu.
   - **Logging**: không in token/PII ra log.
8. **Owned paths** ⊆ boundary.

## Anti-patterns cần flag
- Mutation offline retry không idempotent → tạo bản ghi trùng.
- Lưu token/biometric vào SharedPreferences plain (phải secure storage).
- Widget gọi API trực tiếp thay vì qua repository/provider.
- WebView load URL không tin / nhận deeplink không validate; hardcode API key trong asset.

## Output
RETURN SCHEMA: `review_result`, `coverage_pct`, `checklist_summary`, `needs_review[]`, `fix_loops_triggered`.
