---
name: rules-bff
description: Convention bắt buộc khi code BFF (Apollo Server / GraphQL gateway). Hub — config inline.
---

# Rules BFF Skill

> **Primary skill** cho `kind=bff` (invoke ngay khi spawn dev/fix/review). BFF không có ref-skill riêng — config + pattern inline ở đây.

## Khi load
Sub-agent `kind=bff` — chốt code · sửa bug · review của `/run-wave`.

## Vai trò
BFF = GraphQL gateway: aggregate nhiều backend REST (`api-{backend}.md`) thành 1 graph cho FE. KHÔNG chứa business logic — chỉ orchestrate + shape data.

## Quy ước bắt buộc
1. **Schema GraphQL (SDL)**: additive — deprecate field cũ (`@deprecated`), KHÔNG remove/đổi type breaking. Relay-style `Connection` cho pagination.
2. **Resolver**: implement theo `integrations/INTEG-INT-{bff}-to-{backend}.md` (1 file/backend); gọi backend qua HTTP client, map response → GraphQL type.
3. **DataLoader**: BẮT BUỘC cho mọi field có N+1 risk (vd `order.customer`). Batch + cache per-request.
4. **Auth context**: extract JWT ở context factory → populate `userId / tenantId / roles[]` vào `GraphQLContext`; resolver đọc từ context, KHÔNG tự decode lại.
5. **Error mapping**: HTTP status backend → GraphQL error `extensions.code` (`UNAUTHENTICATED` / `FORBIDDEN` / `BAD_USER_INPUT` / `INTERNAL`).
6. **Cache**: Redis key cho sensitive data PHẢI include `userId`/`tenantId` (tránh leak cross-tenant).
7. **Test**: Vitest unit (resolver + mapper) + integration mock backend; coverage ≥ **70%**.
8. **KG** (`knowledge-base/{boundary}.knowledge-graph.yaml`): design (events/permissions/dependencies) **đã seed ở `/run-wave`**; append phần kinh nghiệm khi phát sinh — DataLoader/cache-key strategy → `learnings.patterns`; quyết định kỹ thuật → `decisions`. Dùng đúng sections của `TEMPLATE.knowledge-graph.yaml` (không tự đặt section mới).

## Forbidden patterns

> Lỗi stack này hay dính. Dev né lúc viết; `review-bff` đi **từng dòng** bảng này lúc soi — cột
> `Vì sao` thành `hậu quả thật` của finding, cột `Thay bằng` thành `suggested fix`.

| Cấm | Vì sao | Thay bằng |
|---|---|---|
| Nghiệp vụ (tính giá, eligibility) trong resolver | Logic nhân đôi với backend, sớm muộn lệch số | Backend tính, resolver chỉ orchestrate + shape |
| Resolver chạm thẳng DB/downstream không qua datasource | Không tái dùng, không test được | Resolver → datasource/service theo `INTEG-INT-*` |
| Field quan hệ không có DataLoader | N+1, sập dưới tải nhẹ | DataLoader batch |
| DataLoader/cache dùng chung toàn cục | Rò dữ liệu giữa các người dùng | Tạo mới mỗi request; key cache có `userId`/`tenantId` |
| Lấy `userId`/`tenantId`/role từ GraphQL args | Client tự khai là người khác | Context từ JWT |
| Decode JWT lại trong từng resolver | Lệch cách verify giữa các resolver | Context factory một lần |
| Bật introspection ở production | Công bố toàn bộ bề mặt tấn công | Tắt |
| Không giới hạn depth/complexity; list không phân trang | Một query đủ làm sập | depth + complexity limit; Relay `Connection` |
| Trả nguyên lỗi backend ra client | Lộ stack/thông tin nội bộ | Map `extensions.code` |
| Lỗi nghiệp vụ biết trước (hết hàng, trùng lịch) gộp chung `INTERNAL` | Client không phân biệt lỗi hệ thống với lỗi người dùng sửa được | Union/result type hoặc code nghiệp vụ riêng, theo `api-{bff}.md` |
| Remove/rename/đổi type field SDL | App đã phát hành gãy | `@deprecated` rồi mới bỏ |
| Viết SDL tay rồi tự đồng bộ với type | Chắc chắn lệch | Code-first hoặc codegen |
| Nối input vào URL/query downstream | Injection/SSRF đi xuyên gateway | Validate + encode tham số |

## Naming
- **Resolver file**: `{type}.resolver.ts`. **Loader**: `{entity}.loader.ts`. **Schema**: `{domain}.graphql`. **Test**: `*.spec.ts`.

## Done
- Build pass, typecheck pass, schema validate.
- DataLoader batching verified (no N+1), test ≥ 70%.
- File chỉ trong `owned_paths`; KG cập nhật.
