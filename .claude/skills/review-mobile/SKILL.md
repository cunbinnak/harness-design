---
name: review-mobile
description: Self-review mobile: analyze, offline strategy, no hardcoded keys.
---

# Review Mobile Skill

## Khi load
`review-mobile-agent` sau `/review-dev` cho mobile boundary.

## Checklist
1. **Coverage**: ≥ 60%.
2. **flutter analyze** pass.
3. **Codegen up-to-date**.
4. **No hardcoded FCM/biometric**.
5. **Offline queue idempotency** đầy đủ cho marked mutation.
6. **No business logic**.
7. **Owned paths**.

## Output
RETURN SCHEMA.
