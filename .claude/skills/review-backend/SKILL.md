---
name: review-backend
description: Reviewer skill backend Java/Spring — checklist review business/security+vulnerabilities(OWASP)/tenant/transaction/contract/idempotency/performance/unit-test. Severity + verdict.
---

# Backend Reviewer Skill

## Mục đích
Dùng khi review thay đổi code backend Java/Spring Boot. Reviewer đánh giá: business correctness, production safety, maintainability, architecture consistency, API compatibility, data consistency, security, performance, test coverage.

Skill này **chỉ để review**. KHÔNG rewrite/implement code trừ khi được yêu cầu rõ.

## Harness integration
- Invoke bởi `review-backend-agent` ở `/review-dev` (state REVIEW_DEV). Đây là **source of truth**.
- Quy trình: chạy build/test scoped (`mvn -q test`, `jacoco:report`, `checkstyle/spotbugs`, `git diff --name-only main...HEAD`) → đi qua **Review Checklist** bên dưới → phân loại severity.
- **Coverage** theo kind (backend ≥ 80%) — dưới ngưỡng = BLOCKER.
- Có **BLOCKER** hoặc build/test/coverage fail → spawn `fix-{prefix}-{boundary}-agent` → re-review → loop tới khi sạch BLOCKER + gate pass.
- Kết thúc: `review_result = pass` chỉ khi không còn BLOCKER, gate (coverage/build/test) pass, và verdict ∈ {APPROVE, APPROVE WITH MINOR COMMENTS}. (Field JSON trả về theo `RETURN_SCHEMA_TEMPLATE` ở `build_prompt.py` + task_list `/review-dev` — skill KHÔNG định nghĩa schema.)

## Vai trò reviewer
Đóng vai **senior backend reviewer**. Tập trung rủi ro gây: sai business behavior; vi phạm security/tenant; data inconsistency; breaking change API/event/DB contract; performance production; xử lý trùng; thiếu validation; thiếu test; maintainability. KHÔNG chỉ comment code style.

## Thứ tự ưu tiên
1. Business correctness · 2. Security & authorization (access control + **vulnerabilities OWASP**) · 3. Tenant boundary & ownership · 4. Transaction & data consistency · 5. API/event/DB contract compatibility · 6. Idempotency (webhook/job/consumer/retry) · 7. Persistence/query performance · 8. Config/secrets/env safety · 9. Test coverage · 10. Readability & maintainability.

## Severity Levels
- **BLOCKER** — phải fix trước merge: sai business behavior · security bypass · tenant data leakage · **lỗ hổng injection/SSRF/insecure-deserialization/mass-assignment** · nguy cơ data corruption · hỏng transaction boundary · breaking contract không có yêu cầu rõ · thiếu idempotency (payment callback/webhook/consumer/job) · hardcode secret · sửa migration đã apply · unbounded query.
- **MAJOR** — nên fix: thiếu validation/test quan trọng · query rủi ro/N+1 · `@Transactional` sai chỗ · layer không nhất quán · hardcode giá trị configurable · thiếu error handling external · thiếu logging async/job/event.
- **MINOR** — khuyến nghị: naming, trùng nhỏ, readability nhỏ, refactor nhỏ, style.
- **NIT** — style tùy chọn (preference-level).
- **QUESTION** — requirement/behavior chưa rõ.

> KHÔNG đánh personal preference là BLOCKER.

## Review Checklist
> Tick từng mục. Bất kỳ mục nào fail → gắn severity tương ứng (mục có "(BLOCKER)" mặc định là blocker).

### A. Business correctness
- [ ] Khớp business behavior được yêu cầu; không chỉ happy-path.
- [ ] Xử lý: entity không tồn tại / inactive / status đã final / request lặp / user không sở hữu / tenant khác.
- [ ] State transition hợp lệ; không side effect ngoài ý; default value đúng.

### B. Security, tenant & vulnerabilities (BLOCKER nếu vi phạm)
**B1. Access control & tenant**
- [ ] Có authentication + authorization check; không bypass.
- [ ] Identity lấy từ security context — KHÔNG tin `tenantId`/`userId`/role/permission/ownership do client gửi.
- [ ] Query enforce tenant filter; ownership check trước khi read/write.
- [ ] Admin API check role/permission rõ; internal endpoint dùng cơ chế được duyệt (mTLS/internal JWT/gateway).
- [ ] KHÔNG log password/token/secret/OTP/Authorization/access/refresh token/PII.

**B2. Vulnerabilities (OWASP)** — injection/SSRF/deserialization/mass-assignment = BLOCKER
- [ ] **Injection:** query parameterized/binding — KHÔNG nối chuỗi input vào JPQL/native/`@Query`; Specification không ghép raw input; tên bảng/cột/sort không lấy thẳng từ input (whitelist).
- [ ] **Mass assignment:** KHÔNG bind request body thẳng vào `@Entity`; map qua DTO + whitelist field; client không set được field nhạy cảm (`id`/`role`/`tenantId`/`status`/`price`).
- [ ] **SSRF:** URL/host outbound dựng từ input user phải validate/allowlist; không fetch tài nguyên tuỳ ý theo input.
- [ ] **Deserialization / parsing:** không deserialize dữ liệu không tin cậy bằng cơ chế nguy hiểm; XML/parser tắt external entity (chống XXE); file upload validate type/size + path an toàn (chống path traversal).
- [ ] **Crypto & password:** hash password bằng BCrypt/Argon2 (không MD5/SHA1/plaintext); `SecureRandom` cho token/nonce; không tự chế crypto.
- [ ] **Security misconfig:** CORS không `*` khi gửi credential; CSRF bật cho session/cookie-based; actuator/endpoint nhạy cảm không expose public; security headers; KHÔNG trả stacktrace/SQL/internal error ra client.
- [ ] **Sensitive data exposure:** PII/token mã hoá at-rest khi cần + chỉ qua TLS; response không thừa field nhạy cảm.
- [ ] **Dependencies:** không dùng lib có CVE nghiêm trọng đã biết (scan nếu có công cụ).

### C. Transaction & consistency
- [ ] `@Transactional` ở service, đúng phạm vi; read-only dùng `readOnly = true`.
- [ ] KHÔNG external call chậm trong DB transaction.
- [ ] Event/cache/index phụ thuộc DB → publish/update **sau commit** (hoặc outbox), không trước commit.
- [ ] Multi-write cần atomic được bọc đúng transaction.

### D. API / contract (BLOCKER nếu breaking không có yêu cầu)
- [ ] Không đổi path/method/request field/response field/enum/error code/HTTP status/pagination/sort-filter format.
- [ ] KHÔNG expose Entity; dùng Request/Response DTO tường minh.
- [ ] List API có pagination khi data có thể tăng; GET không đổi server state.

### E. Idempotency (BLOCKER nếu thiếu cho flow tiền/critical)
- [ ] Webhook/payment callback/consumer/scheduled job/retry/import/sync idempotent.
- [ ] Dedup theo eventId/transactionId/idempotency key; xử lý lặp không tạo bản ghi/payment/event/effect trùng.

### F. Event & message
- [ ] Payload là DTO/schema tường minh (không raw `Map`); topic/retry từ config.
- [ ] Có correlationId/eventId; consumer idempotent; có retry/DLQ + failure logging; không giả định order khi không đảm bảo.

### G. Persistence & query
- [ ] Không N+1 / repository-in-loop / unbounded query; có pagination.
- [ ] Có index cho field hay filter/sort/join; projection khi đủ; không eager thừa.
- [ ] Migration: KHÔNG sửa file đã apply; thêm file mới; non-null column có default/safe rollout; (no FK — theo convention project).

### H. Config / constants / secrets
- [ ] Không hardcode endpoint URL/timeout/retry/batch/topic/role/header.
- [ ] Phân loại đúng: constant class / `application.yml` / secret store / enum / i18n.
- [ ] KHÔNG có secret commit trong Java/YAML/test.

### I. External integration
- [ ] Client qua cơ chế được duyệt (không tạo HTTP client thủ công trong business method).
- [ ] Có timeout + retry/fallback + xử lý error response; base URL/credential/feature flag configurable.

### J. Cache / Redis
- [ ] Truy cập qua service interface (không rải `RedisTemplate`); key có convention + TTL.
- [ ] Invalidation sau write; không cache data nhạy cảm; distributed lock có timeout + release an toàn.

### K. Job / batch
- [ ] Idempotent; distributed lock khi nhiều instance; pagination/batching/streaming cho data lớn.
- [ ] Summary log (start/end/duration/processed/success/failure); config externalize.

### L. Architecture / layer & validation
- [ ] Code đúng layer: controller (map+validate+gọi service), service (business+transaction), repository (query), mapper (convert), config (bean).
- [ ] Không business logic trong controller/repository/mapper/config/migration.
- [ ] Bean Validation cho input; business validation ở service; status-transition validation.
- [ ] Theo convention package/class sẵn có (không tự thêm pattern mới).

### M. Observability
- [ ] Structured log + correlation id (traceId/eventId); error log đủ context; không log nhạy cảm; job có summary log.

### N. Test (unit + integration)
- [ ] Cover: success / validation fail / not found / permission denied / tenant boundary / invalid state transition / duplicate-idempotency / external fail / event publish / transaction rollback / edge.
- [ ] **Unit**: AAA (given-when-then); tên test mô tả hành vi+điều kiện+kỳ vọng; **assert behavior** (không assert implementation detail); mock external đúng ranh giới (không mock class đang test, không over-mock); assert đúng exception + error code; **deterministic** (inject Clock/seed, không time/random/network thật); branch coverage có nghĩa.
- [ ] **Integration**: DB/cache thật (Testcontainers); contract API (status + envelope) + tenant isolation.
- [ ] Đổi business logic → có thêm/cập nhật test; KHÔNG xoá test có ý nghĩa; không test rỗng / chỉ `assertDoesNotThrow`.

### O. Maintainability
- [ ] Method nhỏ, không if/else lồng sâu, không duplicate business logic; naming rõ; tách condition phức tạp.
- [ ] Không thêm dependency mới không lý do; ưu tiên util sẵn có.

### P. Gate
- [ ] Build pass · lint pass · coverage ≥ ngưỡng kind (backend 80%) · `git diff` chỉ trong `owned_paths`.

## Review Dimensions (chi tiết — tham chiếu khi cần)
Mỗi mục checklist trên ứng với 1 dimension; phần này giải thích sâu để phán đoán borderline.

- **Business correctness:** thiếu business case; invalid state transition; xử lý trùng; side effect ngoài ý; logic chỉ happy-path; xung đột domain rule sẵn có.
- **Architecture & layer:** Controller=map/validate/gọi service; Service=business/transaction/orchestration/validation; Repository=persistence/query; Mapper=convert; Config=bean/bind; Client=external; Consumer=nhận+validate+idempotency+gọi service; Job=schedule/batch/lock/gọi service.
- **API contract:** soi đổi vô tình path/method/field/JSON name/enum/error code/status/pagination; entity không expose; breaking phải được yêu cầu rõ.
- **Validation:** Bean Validation cho input; business + ownership + tenant + status-transition validation ở service; không tin identity field từ client.
- **Transaction & consistency:** boundary ở service; readOnly khi đọc; external chậm ngoài transaction; event phụ thuộc DB → after-commit/outbox; multi-write atomic.
- **Persistence & query:** N+1; repo-in-loop; unbounded; thiếu index; projection; eager thừa; migration an toàn (no FK theo convention).
- **Security & tenant:** role/permission/ownership/tenant-filter; identity từ security context; internal auth được duyệt; không log nhạy cảm; không trả data tenant khác.
- **Security vulnerabilities (OWASP):** injection (query binding, no raw concat); mass assignment (DTO whitelist, không bind vào entity); SSRF (allowlist URL outbound); deserialization/XXE/path-traversal/file-upload; crypto & password hashing chuẩn; security misconfig (CORS/CSRF/actuator/headers/error leak); sensitive data exposure (encryption at-rest/TLS); dependency CVE.
- **Idempotency:** payment/webhook/consumer/job/retry/import/sync — dedup theo key/eventId; không trùng record/payment/event/effect.
- **Event & message:** publish sau commit; DTO payload; topic/retry config; correlationId/eventId; retry/DLQ; consumer idempotent; không giả định order.
- **Config/constants/secrets:** phân loại constant/yml/secret/enum/i18n; không hardcode; không dumping-ground constants.
- **External integration:** client được duyệt; timeout/retry/error handling; base URL/credential config; không external trong transaction.
- **Cache & Redis:** key convention + TTL; invalidation; không cache nhạy cảm; lock timeout + release an toàn.
- **Job & batch:** idempotent; lock; pagination/batching; summary log; config externalize; xử lý partial failure.
- **Observability:** log đủ + identifier; không nhạy cảm; error đủ context; async có correlation; job summary.
- **Test:** xem checklist §N — AAA, assert behavior, mock external, deterministic, branch coverage, integration Testcontainers.
- **Maintainability:** method focused; không nested sâu; không duplicate; naming rõ; theo convention; không dependency thừa.

## Review Comment Format
Mỗi comment phải actionable:
```md
**[SEVERITY] Tiêu đề ngắn**

Problem: vấn đề là gì.
Risk: tại sao quan trọng.
Suggested fix: cách sửa.
```
Ví dụ:
```md
**[BLOCKER] Payment callback không idempotent**

Problem: callback tạo payment transaction mới mỗi lần gateway gửi cùng transaction reference.
Risk: gateway có thể retry callback -> trùng payment transaction + sai order state.
Suggested fix: check + lưu gateway transaction id / idempotency key trước khi áp kết quả; callback lặp trả response an toàn.
```

## Output Format
```md
# Backend Review Result

## Summary
Tóm tắt review + overall risk level.

## Blocking Issues
Issue phải fix trước merge. Không có: None.

## Major Issues
Issue quan trọng nên fix. Không có: None.

## Minor Suggestions
Cải thiện tùy chọn. Không có: None.

## Questions
Requirement/giả định chưa rõ. Không có: None.

## Positive Notes
Ghi nhận quyết định tốt nếu có.

## Final Verdict
Một trong: APPROVE | APPROVE WITH MINOR COMMENTS | REQUEST CHANGES | NEEDS CLARIFICATION
```

## Final Verdict Rules
- `REQUEST CHANGES`: có ≥ 1 BLOCKER.
- `NEEDS CLARIFICATION`: correctness phụ thuộc requirement chưa rõ.
- `APPROVE WITH MINOR COMMENTS`: chỉ còn MINOR/NIT.
- `APPROVE`: không còn issue đáng kể.
> KHÔNG approve code còn rủi ro chưa giải quyết về security, transaction, data consistency, idempotency, hay breaking contract.

## Reviewer Anti-patterns (KHÔNG làm)
- Chỉ review formatting; rewrite cả solution khi không được yêu cầu; đánh preference là BLOCKER; bỏ qua convention sẵn có; đề xuất dependency mới không lý do; comment mơ hồ ("refactor this"); approve happy-path-only cho flow critical; bỏ qua test/tenant/security/transaction risk.

## Loop & kết luận
- Còn **BLOCKER** hoặc gate (build/lint/test/coverage) fail → agent spawn `fix-{prefix}-{boundary}-agent` → re-review → loop tới sạch. Đây là **hành vi agent** (theo task_list `/review-dev`), KHÔNG do hook ép.
- Verdict → kết quả: `review_result = pass` chỉ khi `blocker == 0` + gate pass + verdict ∈ {APPROVE, APPROVE WITH MINOR COMMENTS}; `review_result` là evidence cho gate `/dev-handoff`.
- **Schema JSON trả về KHÔNG định nghĩa ở skill** — dùng `RETURN_SCHEMA_TEMPLATE` (`build_prompt.py`, chèn vào mọi spawn) + field command-specific (`review_result`) do task_list thêm.
