---
name: ref-backend-pattern
description: Cấu trúc backend boundary — Layered (classic Spring 3-tier) hoặc Hexagonal (Ports & Adapters) theo ADR. Layout artifact, layer responsibilities, interface/impl, response & error shape, forbidden patterns.
---

# Reference: Backend Structure (Layered | Hexagonal)

> **Purpose:** Layout chuẩn 1 backend boundary để dev/fix/review scaffold đồng nhất.
> **Audience:** `dev:backend`, `fix:backend`, `review:backend` — load on-demand từ `rules-backend`.
> **Quan hệ:** `rules-backend` là convention bắt buộc và trỏ sang file này cho cấu trúc; file này KHÔNG lặp lại rule, chỉ mô tả nơi đặt từng artifact (thuật ngữ khớp `rules-backend §Layering`).
> **Tách bạch:** cấu trúc = file này · config chi tiết (application.yml, security, kafka…) = `ref-backend-config`.
> **Tuning:** mô hình + layer/package của boundary **đã chốt ở HLD §4** (theo ADR backend-architecture). File này KHÔNG quyết lại — chỉ cung cấp layout chuẩn cho mô hình mà HLD đã chốt. Cây thư mục dưới là khung tối thiểu — package tùy chọn (`event/`, `scheduler/`, `util/`…) chỉ thêm khi boundary cần.
> **Cache/Redis:** có ref skill riêng (pattern interface + impl adapter), KHÔNG mô tả ở file này.

## 1. Chọn mô hình (chốt ở HLD §4, theo ADR backend-architecture)

| Mô hình | Khi dùng | Luồng |
|---|---|---|
| **Layered** (classic Spring) | CRUD, domain ít phức tạp — mặc định | `controller → service → repository` |
| **Hexagonal** (Ports & Adapters) | Nghiệp vụ phức tạp, cần tách domain khỏi framework, nhiều inbound/outbound | `adapter.in → application (use case) → domain`; outbound qua port, `adapter.out` impl |

Một boundary = một repo polyrepo, root `services/{prefix}-{boundary}/` (prefix = `project.service_prefix`).

## 2. Layout — Layered (classic Spring 3-tier)

```
services/{prefix}-{boundary}/src/main/java/.../{boundary}/
├── controller/
│   └── {Resource}Controller.java           # map request/response, validation annotation, gọi service
├── service/
│   ├── {Resource}Service.java              # interface use case
│   └── impl/{Resource}ServiceImpl.java     # @Service, @Transactional, business logic, constructor injection
├── repository/
│   └── {Resource}Repository.java           # Spring Data JPA interface (JPQL/Specification, no nativeQuery)
├── model/                                  # (hoặc entity/)
│   └── {Resource}.java                     # @Entity: no @Data, no FK (liên kết qua id column)
├── dto/
│   ├── request/{Resource}Request.java      # request DTO + Bean Validation
│   └── response/{Resource}Response.java    # response DTO (KHÔNG expose entity)
├── mapper/{Resource}Mapper.java            # convert DTO ↔ entity (không gọi service/repository/client)
├── event/                                  # Kafka — thêm khi boundary phát/nhận event
│   ├── producer/{Resource}EventPublisher.java  # publish after-commit (@TransactionalEventListener AFTER_COMMIT)
│   ├── consumer/{Topic}Consumer.java           # @KafkaListener — idempotent (dedup theo event/message id)
│   └── payload/{Resource}Event.java            # event schema/DTO (không raw Map); topic name lấy từ config
├── enums/                                  # business enum
│   ├── {Resource}Status.java               # enum trạng thái nghiệp vụ
│   └── {Resource}ErrorCode.java            # enum mã lỗi per-domain
├── constant/                               # constants class theo domain (final + private ctor)
│   └── {Domain}Constants.java
├── exception/
│   ├── ErrorCode.java                      # interface (code, message, httpStatus) — enum per-domain implements
│   ├── BusinessException.java              # base business exception (nhận ErrorCode)
│   └── GlobalExceptionHandler.java         # @RestControllerAdvice: map exception → response envelope
├── config/                                 # CHỈ @Configuration bean + @ConfigurationProperties
│   ├── {Domain}Properties.java             # @ConfigurationProperties (config nhóm)
│   └── {Web,Security,…}Config.java         # @Configuration bean (chi tiết → ref-backend-config)
├── scheduler/                              # job định kỳ (@Scheduled) — thêm khi boundary cần (data lớn: paginate/batch)
└── util/                                   # helper thuần (formatter, validator, date) — thêm khi dự án cần

resources/db/migration/                     # migration versioned, no FK
tests/{unit,integration}                    # unit: service mock repo · integration: controller + DB thật
```

## 3. Layout — Hexagonal (Ports & Adapters)

```
services/{prefix}-{boundary}/src/main/java/.../{boundary}/
├── domain/
│   ├── model/                  # Domain model: aggregate, entity, value object (pure, no framework)
│   ├── enums/                  # business enum + {Resource}ErrorCode (mã lỗi)
│   ├── service/                # Domain service thuần (nếu có)
│   └── exception/              # ErrorCode (interface) + BusinessException  (GlobalExceptionHandler ở adapter/in/web)
├── application/
│   ├── port/
│   │   ├── in/                 # Inbound port = use case interface (vd CreateOrderUseCase)
│   │   └── out/                # Outbound port = repository/gateway interface (vd LoadOrderPort, SaveOrderPort)
│   └── service/                # Use case impl (application service), @Transactional, impl inbound port
├── adapter/
│   ├── in/
│   │   ├── web/                 # Inbound adapter (REST): Controller + dto/{request,response} + mapper + GlobalExceptionHandler
│   │   ├── messaging/           # Inbound adapter (Kafka consumer): {Topic}Consumer — idempotent
│   │   └── scheduler/           # Inbound adapter (job định kỳ @Scheduled) — thêm khi cần
│   └── out/
│       ├── persistence/         # Outbound adapter: JPA entity + repository, impl outbound port
│       ├── client/              # Outbound adapter: external HTTP client, impl outbound port
│       └── messaging/           # Outbound adapter (Kafka producer): {Resource}EventPublisher — publish after-commit
├── constant/                   # constants class theo domain
├── config/                     # @ConfigurationProperties + @Configuration bean + DI wiring
└── util/                       # helper thuần — thêm khi dự án cần

resources/db/migration/         # migration versioned, no FK
tests/{unit,integration}
```

## 4. Trách nhiệm từng thành phần

**Layered:**

| Thành phần | Trách nhiệm |
|---|---|
| `controller/` | Map request/response, validation annotation, gọi service. KHÔNG business logic. |
| `service/` (+`impl/`) | Business logic, transaction boundary, business validation, orchestration, quyết định publish event. |
| `repository/` | Persistence/query (Spring Data, JPQL/Specification). |
| `model/` | JPA entity (no @Data, no FK). |
| `dto/request` · `dto/response` | Schema vào/ra ở biên API. |
| `mapper/` | Convert DTO ↔ entity. KHÔNG gọi service/repository/client. |
| `event/` | Kafka: producer (publish after-commit) + consumer (idempotent) + payload DTO. Topic name từ config. |
| `enums/` | Business enum (status/type) + `{Resource}ErrorCode` (implements `ErrorCode`). |
| `constant/` | Constants class theo domain (`final`, private constructor). |
| `exception/` | `ErrorCode` interface + `BusinessException` + `GlobalExceptionHandler` (khung §6). |
| `config/` | `@ConfigurationProperties` + `@Configuration` bean. |
| `util/` | Helper thuần, không state, không phụ thuộc layer khác. |
| `scheduler/` | Job định kỳ (`@Scheduled`) — thêm khi cần; data lớn phải paginate/batch. |

**Hexagonal:**

| Thành phần | Trách nhiệm |
|---|---|
| `domain/` | Model + enum + business rule + exception, thuần — KHÔNG phụ thuộc framework/adapter. |
| `application/port/in` · `port/out` | Hợp đồng (interface) vào/ra của use case. |
| `application/service` | Use case impl: orchestrate domain qua outbound port, transaction boundary. |
| `adapter/in/web` · `in/messaging` | Inbound adapter: REST controller (+ dto + mapper + GlobalExceptionHandler) / Kafka consumer (idempotent). |
| `adapter/out/persistence` · `out/client` · `out/messaging` | Outbound adapter: impl outbound port (DB / HTTP / Kafka producer). |

## 5. Interface + impl
- **Service / use case**: interface + impl tách riêng; caller phụ thuộc interface.
  - Layered: `service/{Resource}Service` + `service/impl/{Resource}ServiceImpl`.
  - Hexagonal: inbound port `application/port/in/{X}UseCase` impl ở `application/service/{X}Service`.
- **Repository**:
  - Layered: Spring Data interface `{Resource}Repository extends JpaRepository<…>` — auto-impl (custom query phức tạp → `{Resource}RepositoryCustom` + impl đi kèm).
  - Hexagonal: outbound port `application/port/out/{X}Port` impl bởi adapter `adapter/out/persistence/{X}PersistenceAdapter` (DIP).
- **Injection**: constructor (`final` field), KHÔNG `@Autowired` trên field/setter.

```java
// service/{Resource}Service.java + service/impl/{Resource}ServiceImpl.java  (Layered)
public interface OrderService { OrderResponse create(OrderRequest req); }

@Service
class OrderServiceImpl implements OrderService {
    private final OrderRepository repository;
    private final OrderMapper mapper;
    OrderServiceImpl(OrderRepository repository, OrderMapper mapper) {   // constructor injection
        this.repository = repository; this.mapper = mapper;
    }
}

// repository/OrderRepository.java  (Spring Data — auto-impl, JPQL khi cần)
public interface OrderRepository extends JpaRepository<Order, Long> {
    Optional<Order> findByCode(String code);
}
```

## 6. Response & error shape (common)
Envelope response nhất quán toàn boundary — contract cụ thể chốt ở `api-{boundary}.md` (§Common error format), pattern này mô tả khung chung.

1. **Success**: bọc trong `data` + `meta` (timestamp/traceId). KHÔNG trả entity trần.
2. **Error**: `error.code` (mã nghiệp vụ ổn định, từ ErrorCode enum) + `message` + optional `details[]`. Body lỗi cùng envelope.
3. **Pagination**: list lớn trả `content[]` + `page{number,size,totalElements,totalPages}` (hoặc cursor) — KHÔNG trả mảng trần.
4. **HTTP status** đúng semantic (200/201/204/400/401/403/404/409/422/500).
5. **GlobalExceptionHandler** (`@RestControllerAdvice`) là nơi duy nhất map exception → envelope.

```json
// success
{ "data": { "id": 42, "code": "ORD-001" }, "meta": { "timestamp": "..." } }
// error
{ "error": { "code": "ORDER_NOT_FOUND", "message": "Order không tồn tại", "details": [] },
  "meta": { "timestamp": "...", "traceId": "..." } }
// page
{ "data": { "content": [ ... ], "page": { "number": 0, "size": 20, "totalElements": 137, "totalPages": 7 } } }
```

### Khung generic dùng sẵn (copy theo)

```java
// exception/ErrorCode.java — interface; mỗi domain khai 1 enum implements
public interface ErrorCode { String code(); String message(); HttpStatus httpStatus(); }

// enums/OrderErrorCode.java
public enum OrderErrorCode implements ErrorCode {
    NOT_FOUND("ORDER_NOT_FOUND", "Order không tồn tại", HttpStatus.NOT_FOUND);
    private final String code; private final String message; private final HttpStatus status;
    OrderErrorCode(String c, String m, HttpStatus s) { this.code = c; this.message = m; this.status = s; }
    public String code() { return code; } public String message() { return message; } public HttpStatus httpStatus() { return status; }
}

// exception/BusinessException.java — throw new BusinessException(OrderErrorCode.NOT_FOUND);
public class BusinessException extends RuntimeException {
    private final transient ErrorCode errorCode;
    public BusinessException(ErrorCode ec) { super(ec.message()); this.errorCode = ec; }
    public ErrorCode errorCode() { return errorCode; }
}

// common response envelope
public record Meta(Instant timestamp, String traceId) {
    public static Meta now() { return new Meta(Instant.now(), MDC.get("traceId")); }
}
public record ApiResponse<T>(T data, Meta meta) {
    public static <T> ApiResponse<T> ok(T data) { return new ApiResponse<>(data, Meta.now()); }
}
public record PageResponse<T>(List<T> content, PageMeta page) {
    public record PageMeta(int number, int size, long totalElements, int totalPages) {}
}
public record ErrorResponse(ErrorBody error, Meta meta) {
    public record ErrorBody(String code, String message, List<String> details) {}
}

// exception/GlobalExceptionHandler.java — nơi DUY NHẤT map exception → ErrorResponse
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ErrorResponse> handle(BusinessException e) {
        ErrorCode ec = e.errorCode();
        var body = new ErrorResponse(new ErrorResponse.ErrorBody(ec.code(), ec.message(), List.of()), Meta.now());
        return ResponseEntity.status(ec.httpStatus()).body(body);
    }
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(MethodArgumentNotValidException e) {
        // → HTTP 400, code "VALIDATION_ERROR", details = danh sách field error
        ...
    }
    // fallback: @ExceptionHandler(Exception.class) → HTTP 500, code "INTERNAL_ERROR" (KHÔNG lộ stacktrace)
}
```

## 7. Forbidden patterns
- Business logic trong `controller/` (Layered) hoặc `adapter/in` (Hexagonal) — chỉ map + delegate.
- `controller/` gọi `repository/` trực tiếp — phải qua `service/`.
- Business logic trong `repository/` hoặc `mapper/`.
- `mapper/` gọi service/repository/external client.
- Hexagonal: `domain/` hoặc `application/` import `adapter/` — chỉ giao tiếp qua port.
- Expose entity ra API hoặc dùng entity làm request body.
- Import code từ `services/{prefix}-{other}/` — cross-boundary chỉ qua HTTP/event theo `docs/architecture/integrations/INTEG-*.md`.

## 8. Done
- Cấu trúc khớp mô hình chốt trong ADR backend-architecture + `hld-{boundary}.md`.
- API khớp `api-{boundary}.md`; schema khớp `data-model-{boundary}.md`.
- Build chạy được (`./mvnw` / `./gradlew`).
