---
name: rules-backend
description: Convention bắt buộc khi code backend boundary (Java/Spring hoặc tương đương). Hub — ref pattern + config.
---

# Rules Backend Skill

> **Primary skill** cho `kind=backend` (invoke ngay khi spawn dev/fix/review).
> On-demand refs:
> - Kiến trúc + cấu trúc thư mục → `ref-backend-pattern` (Layered/DDD theo **ADR backend-architecture**).
> - File cấu hình (application.yml, security, kafka, secrets…) → `ref-backend-config`.

## Khi load
Sub-agent `kind=backend` ở `/start-dev`, `/fix-bugs`, `/review-dev`.

## Quy ước bắt buộc
1. **Kiến trúc**: theo loại đã chốt trong **ADR backend-architecture** (Layered hoặc DDD tactical) — cấu trúc thư mục + layer responsibilities xem `ref-backend-pattern`.
2. **Multi-tenancy**: mọi entity, query MUST filter `tenant_id` từ auth context (nếu project multi-tenant).
3. **API**: contract khớp `docs/architecture/api/api-{boundary}.md`; KHÔNG đổi breaking không qua ADR.
4. **DB**: migration versioned, additive (không sửa migration đã apply); schema khớp `data-model-{boundary}.md`.
5. **Event**: publish/consume theo `docs/architecture/events/{boundary}-events.md` envelope chuẩn.
6. **Cross-boundary**: KHÔNG import code từ `services/{prefix}-{other}/`; gọi qua HTTP/event theo `docs/architecture/integrations/INTEG-*.md`.
7. **Config**: secrets qua env; không hardcode (chi tiết `ref-backend-config`).
8. **Test**: unit (domain/application) + integration (api + DB testcontainer); coverage ≥ **80%**.
9. **KG**: append entity/event/decision vào `knowledge-base/{prefix}-{boundary}.knowledge-graph.yaml` sau khi xong.

## Entity (JPA — Java/Spring)
1. **KHÔNG dùng `@Data` / `@EqualsAndHashCode` / `@ToString` (all-field) trên `@Entity`.** Lý do:
   - `equals`/`hashCode` trên mọi field break khi entity nằm trong `Set`/`Map` (hashCode đổi sau persist) và gây StackOverflow ở quan hệ bidirectional.
   - `toString` all-field trigger lazy-load oan và log lộ dữ liệu.
2. **Dùng getter/setter tường minh** (hoặc `@Getter`/`@Setter` field-level riêng lẻ — KHÔNG `@Data`).
3. **`equals`/`hashCode`**: dựa trên business/natural key ổn định (hoặc id sau persist + `@NaturalId`), KHÔNG dùng toàn bộ field.
4. **`toString`**: chỉ field scalar (id, code…), KHÔNG include collection/association.
5. Constructor: `protected` no-arg cho JPA + constructor có tham số để khởi tạo hợp lệ (giữ invariant).

```java
// Tránh
@Entity @Data
class Order { @Id Long id; @OneToMany List<OrderLine> lines; }

// Nên
@Entity
@Getter @Setter
class Order {
    @Id @GeneratedValue Long id;
    @Column(nullable = false) String code;
    @OneToMany(mappedBy = "order") List<OrderLine> lines = new ArrayList<>();
    protected Order() {}                       // JPA
    public Order(String code) { this.code = code; }
    @Override public boolean equals(Object o) { /* theo code (natural key) */ }
    @Override public int hashCode() { return Objects.hash(code); }
    @Override public String toString() { return "Order{id=%d, code=%s}".formatted(id, code); }
}
```

## Naming & package
- **File**: theo stack — `PascalCase.java` (Java) / `kebab-case.ts` (Node) / `snake_case.py` (Python).
- **Class**: `PascalCase` (`OrderService`). **Method**: `camelCase`/`snake_case` theo stack. **Constant**: `UPPER_SNAKE_CASE`.
- **Package/module**: theo mô hình đã chốt — Layered (`controller`/`service`/`repository`/…) hoặc Hexagonal (`domain`/`application`/`adapter`). Cấu trúc đầy đủ + nơi đặt từng artifact xem `ref-backend-pattern`.
- **Test**: `{Unit}Test` / `test_{module}` theo runner.

## Java coding rules

### Convention sẵn có trước
- Trước khi tạo/sửa code: xem class tương tự trong cùng module.
- Theo package structure / naming / annotation / exception / response / mapper / test style **sẵn có**.
- KHÔNG tự thêm pattern mới nếu project đã có convention. Nhiều convention cùng tồn tại → theo cái gần module đích nhất.

### Khai báo kiểu
- KHÔNG dùng `var`; khai báo kiểu tường minh cho local var, field, param và return type.
- KHÔNG dùng Fully Qualified Class Name (FQCN) trong khai báo (biến/param/return/generic) — dùng `import` tường minh (vd `List`, `Optional`, không `java.util.List`).
- KHÔNG wildcard import (`import java.util.*`).

### Constant & config — phân loại hard-coded value
KHÔNG hardcode magic string/number, role/claim/header/topic/queue name, timeout, retry, endpoint URL, feature flag trong business logic. Trước khi thêm/refactor bất kỳ giá trị hard-code, **phân loại** rồi đặt đúng chỗ:

| Loại giá trị | Ví dụ | Đặt ở đâu |
|---|---|---|
| Kỹ thuật/domain ổn định | regex, default page size, date format, cache key prefix | constants class theo domain |
| Theo môi trường | base URL, port, pool size, feature flag | `application.yml` (+ env placeholder) |
| Nhạy cảm (secret) | DB password, API key, JWT secret, OTP salt | env var / Vault / K8s Secret / Secret Manager |
| Trạng thái/loại nghiệp vụ | `OrderStatus`, `PaymentMethod`, `Role` | `enum` |
| Message cho user | validation message, error text | message resource / i18n (`messages.properties`) |

Nguyên tắc:
- KHÔNG bao giờ hardcode secret — kể cả trong test, YAML commit, constants class, hay ví dụ trong tài liệu.
- KHÔNG dùng một `Constants.java` khổng lồ làm bãi rác — tách constants class theo domain/nhóm (vd `OrderConstants`, `SecurityHeaders`); class `final`, constructor `private`.
- Config nhóm liên quan → `@ConfigurationProperties(prefix = "...")` thay vì rải `@Value` khắp nơi.
- YAML dùng env placeholder tường minh, KHÔNG hardcode giá trị môi trường — vd `${PAYMENT_BASE_URL}`, `${DB_PASSWORD}` (có thể kèm default `${PORT:8080}`).

```java
// Constants class theo domain (KHÔNG dồn hết vào 1 Constants.java)
public final class OrderConstants {
    public static final int MAX_LINES = 100;
    public static final String CODE_PREFIX = "ORD-";
    private OrderConstants() {}
}

// Config nhóm qua @ConfigurationProperties (type-safe, validate được)
@ConfigurationProperties(prefix = "payment")
public record PaymentProperties(String baseUrl, Duration timeout) {}
```
```yaml
# application.yml — env placeholder tường minh
payment:
  base-url: ${PAYMENT_BASE_URL}
  timeout: ${PAYMENT_TIMEOUT:5s}
```

### Layering
- **Controller**: chỉ map request, validation annotation, gọi service, map response.
- **Service**: business logic + transaction boundary + business validation + orchestration + quyết định publish event.
- **Repository**: chỉ persistence/query.
- **Mapper**: chỉ convert Entity/DTO/Command/Event/Response; KHÔNG gọi service/repository/external client.
- **Config class**: chỉ define bean + bind config.
- KHÔNG đặt business logic trong Controller, Repository, Mapper, Entity listener, hay Config class.

### DTO & API contract
- KHÔNG expose entity trực tiếp ra response; KHÔNG dùng entity làm request body. Dùng Request DTO + Response DTO ở biên API.
- KHÔNG đổi path / HTTP method / request field / response field / enum value / error code / event payload / DB column / topic name — trừ khi được yêu cầu rõ.
- Giữ **backward compatibility** khi thêm/sửa hành vi API.
- List API phải **paginate** khi data có thể tăng.

### Exception
- Lỗi nghiệp vụ: dùng custom exception (vd `BusinessException`), KHÔNG dùng `RuntimeException` / `Exception` / `IllegalArgumentException`.
- Error code quản lý tập trung bằng **enum** theo domain — vd `throw new BusinessException(OrderErrorCode.NOT_FOUND);`.
- **Global exception handler** (`@RestControllerAdvice`) map exception → response thống nhất; KHÔNG try/catch map lỗi rải rác trong controller.
- KHÔNG gọi `Optional.get()` trực tiếp — dùng `orElseThrow(() -> new BusinessException(OrderErrorCode.NOT_FOUND))`.

### Validation
- Input cơ bản: Bean Validation annotation. Business rule: validate ở service layer. KHÔNG rải null/empty check lặp lại khắp business code.
- KHÔNG tin các giá trị định danh / phân quyền / ownership do client gửi nếu theo thiết kế dự án chúng phải đến từ authenticated context — lấy từ security context, KHÔNG từ request body/param.
- Validate quyền truy cập data (ownership / phạm vi được phép) trước khi đọc/sửa, theo mô hình phân quyền của dự án.
- Validate **state transition** hợp lệ trước khi đổi business status.

### Transaction & consistency
- `@Transactional` chỉ đặt trên method service layer (trừ khi convention project khác). Method read-only: `@Transactional(readOnly = true)` khi phù hợp.
- KHÔNG gọi external API chậm bên trong DB transaction (trừ khi bắt buộc).
- KHÔNG publish event phụ thuộc DB-state trước khi commit — ưu tiên **after-commit publishing** (vd `@TransactionalEventListener(AFTER_COMMIT)`).

### Persistence & migration
- **Truy vấn**: ưu tiên **JPQL**; query động/nhiều điều kiện dùng **Specification** (Criteria API); `nativeQuery` chỉ dùng khi JPQL/Specification không đáp ứng được (last resort).
- **Quan hệ bảng — KHÔNG khai báo foreign key constraint** (áp dụng mọi quan hệ, kể cả trong cùng boundary):
  - Liên kết bằng id column thường (vd `customer_id BIGINT`), KHÔNG `FOREIGN KEY ... REFERENCES`; migration không sinh FK.
  - Toàn vẹn tham chiếu + cascade enforce ở **application/service layer**, không ở DB.
  - BẮT BUỘC tự **add index** cho id column dùng để join/lookup (không có FK nên không tự index).
  - Lý do: mỗi boundary sở hữu DB riêng (polyrepo) → không thể FK cross-DB; tránh ràng buộc cứng gây khó scale/sharding và xoá/migrate.
- KHÔNG sửa migration đã apply — thêm file migration mới cho schema change.
- Column NOT NULL mới phải có default value hoặc strategy an toàn (thêm nullable → backfill → enforce NOT NULL).
- Add **index** cho field hay filter/join/sort/lookup.
- Tránh **N+1**; KHÔNG gọi repository lặp trong loop khi có thể bulk query.

### Event, job & idempotency
- Webhook / payment callback / message consumer / scheduled job / retry job / external callback PHẢI **idempotent**.
- KHÔNG xử lý trùng cùng `event id` / `transaction id` / `request id` / idempotency key.
- Event payload dùng DTO/schema class tường minh — KHÔNG raw `Map` (trừ khi convention sẵn có).
- Scheduled job xử lý data lớn bằng pagination / batching / streaming.

### External integration
- External base URL / credential / timeout / retry / feature flag phải configurable (không hardcode).
- KHÔNG khởi tạo HTTP client thủ công trong business method — dùng client theo cơ chế project đã duyệt.
- Luôn handle timeout / error response / retry theo convention project.

### Logging & security
- KHÔNG log password / token / secret / OTP / Authorization header / refresh token / access token / PII nhạy cảm.
- KHÔNG bypass authentication/authorization check.
- KHÔNG hardcode giá trị định danh / phân quyền (tenant, user, role, scope… tùy mô hình dự án) — lấy từ security context chuẩn của project.
- Internal endpoint dùng cơ chế internal auth đã duyệt (mTLS / internal JWT / gateway verification).

### Code quality
- Method nhỏ, đọc được theo nghiệp vụ; tách logic/điều kiện phức tạp thành private method tên có nghĩa.
- Tránh if/else và loop lồng sâu. Stream API chỉ dùng khi tăng readability.
- KHÔNG duplicate business logic. KHÔNG trả null collection — trả empty collection.
- KHÔNG thêm dependency mới nếu không cần — ưu tiên util sẵn có của project.

### Testing
- Thêm/cập nhật test khi đổi business logic. Mock external system trong unit test.
- Cover: success, validation fail, not found, permission fail, edge case quan trọng.
- KHÔNG xoá test cũ trừ khi được yêu cầu rõ.

## Done
- Build pass, lint pass, test pass coverage ≥ 80%.
- File chỉ thay đổi trong `owned_paths` của boundary.
- Cấu trúc khớp `ref-backend-pattern` (mô hình theo ADR) + `hld-{boundary}.md`.
- KG cập nhật, không có `discipline.blockers`.
