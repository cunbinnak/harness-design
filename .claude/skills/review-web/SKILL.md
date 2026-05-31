---
name: review-web
description: Self-review web frontend — a11y, no biz logic, data layer khớp design, security (XSS/token/secret), coverage, owned_paths.
---

# Review Web Skill

> Checklist source-of-truth cho `review-web-agent` ở `/review-dev`. Fail → spawn fix → re-review → loop tới pass.

## Lệnh chạy
```bash
npm run -s test -- --coverage     # Vitest + RTL
npm run -s typecheck
npm run -s lint
npx axe-core (hoặc CI a11y job)   # a11y scan
git diff --name-only main...HEAD
```

## Checklist (PASS/FAIL/NA)
1. **Build + typecheck + lint** xanh; test ≥ **60%**.
2. **a11y**: axe-core 0 critical (contrast, label, role, focus order).
3. **Data layer khớp design**:
   - REST (default): client gọi đúng endpoint `api-{backend}.md`; type khớp DTO; có interceptor auth.
   - BFF (nếu design có bff): codegen up-to-date (`npm run codegen` no diff); op name khớp `integrations/INTEG-INT-{web}-to-{bff}.md`.
4. **No business logic** trong FE: price/score/eligibility lấy từ BE/BFF, không tự tính.
5. **State handling**: mọi async có loading / error / success (không UI treo khi fail).
6. **Design fidelity**: page khớp `ux-{boundary}.md` (SCR-XXX).
7. **Security (FE)**:
   - **XSS**: không `dangerouslySetInnerHTML` với data chưa sanitize; không render HTML thô từ input/API.
   - **Token**: không lưu access/refresh token vào `localStorage` (XSS-exfil) — ưu tiên httpOnly cookie / in-memory; không log token.
   - **Auth UI ≠ enforcement**: ẩn/disable theo role chỉ là UX; BE vẫn enforce (không tin client).
   - **No secret in bundle**: không nhúng API secret/private key vào env public/bundle.
   - **Open redirect / link**: URL redirect từ input validate; external link `rel="noopener"`.
   - Dependency không có CVE nghiêm trọng đã biết.
8. **Owned paths** ⊆ boundary.

## Anti-patterns cần flag
- `components/` gọi API trực tiếp (phải qua `hooks/` → `api/`).
- Tính tiền/giảm giá ở FE.
- Hardcode role string thay vì đọc `roles[]` từ JWT.
- Bỏ trạng thái error (chỉ render khi success).
- `dangerouslySetInnerHTML` / render HTML từ API chưa sanitize; token trong `localStorage`.

## Output
RETURN SCHEMA: `review_result`, `coverage_pct`, `checklist_summary`, `needs_review[]`, `fix_loops_triggered`.
