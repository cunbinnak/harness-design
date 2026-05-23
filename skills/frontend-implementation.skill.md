---
name: frontend-implementation
description: Triển khai UI/FE theo FEAT, HLD và contract API backend.
---

# Frontend Implementation Skill

## Khi dùng

Giai đoạn build UI trong `apps/`, `packages/` hoặc `services/fe/` (theo matrix).

## Hoạt động

1. Đọc `docs/architecture/ux/ux-fe.md` (luồng, màn hình, trạng thái).
2. Khớp API/contract từ HLD và boundary backend.
3. Component/state theo convention dự án; test UI/e2e nếu có.
4. Không sửa logic domain trong `services/{backend}/`.

## Done

- UI đáp ứng AC FEAT; build/lint/test FE pass theo RETURN SCHEMA.
