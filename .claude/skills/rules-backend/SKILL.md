---
name: rules-backend
description: Convention bắt buộc khi code backend boundary (Java 21 / Spring Boot). Hub — ref pattern/config + situational (kafka/redis/logging/restclient).
---

# Rules Backend Skill

> **Primary skill** cho `kind=backend` (invoke ngay khi spawn dev/fix/review). Rules = WHAT; HOW/code → ref skills.
> On-demand refs:
> - Cấu trúc thư mục + interface/impl + mapper config → `ref-backend-pattern` (Layered/Hexagonal theo **ADR backend-architecture** / HLD §4).
> - Config (application.yml, profiles, security, Gradle, Dockerfile…) → `ref-backend-config`.
> - Situational (theo boundary): Kafka → `ref-backend-kafka` · Redis → `ref-backend-redis` · logging → `ref-backend-logging` · downstream HTTP → `ref-backend-restclient`.

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
9. **KG** (`knowledge-base/{boundary}.knowledge-graph.yaml`): phần design (entities/business_rules/events/permissions) **đã seed ở `/start-wave`** từ docs — chỉ **update khi implement KHÁC design** (kèm sửa data-model cho khớp); **append phần kinh nghiệm** (learnings/gotchas/decisions/failure_modes) khi phát sinh. KHÔNG tái tạo lại design từ đầu.

## Entity (JPA — Java/Spring)
1. **KHÔNG `@Data` / `@EqualsAndHashCode` / `@ToString` (all-field) trên `@Entity`** — equals/hashCode all-field break trong `Set`/`Map` (hashCode đổi sau persist) + StackOverflow ở quan hệ bidirectional; toString all-field trigger lazy-load oan + log lộ dữ liệu.
2. **Dùng `@Getter @Setter @NoArgsConstructor @AllArgsConstructor`** — constructor do annotation sinh, KHÔNG tự viết. KHÔNG `@Data`.
3. KHÔNG cần tự viết `toString`/`equals`/`hashCode`; nếu thật sự cần override `equals`/`hashCode` → theo business/natural key (hoặc id sau persist + `@NaturalId`), KHÔNG all-field.
4. **Tên class = `{Resource}Entity`** (vd `OrderEntity`, `AppointmentEntity`) — KHÔNG để trần `Order`. Đặt ở package **`entities/`** (Layered) / `adapter/out/persistence/entities/` (Hexagonal) — KHÔNG để `model/`. (Service/repo/DTO/mapper/controller giữ `{Resource}`: `OrderService`/`OrderRepository`/`OrderResponse`, KHÔNG `OrderEntityService`.)

```java
// Nên
@Entity
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
class OrderEntity {
    @Id @GeneratedValue Long id;
    @Column(nullable = false) String code;
    @Column(nullable = false) Long customerId;   // liên kết qua id (no FK) — nhớ add index
}

// Tránh
@Data 
@Entity                                   // @Data trên @Entity
class OrderBad {
    @Id Long id;
    @OneToMany List<OrderLine> lines;            // association = FK, vi phạm no-FK
}
```

## Naming & package
- **File**: theo stack — `PascalCase.java` (Java) / `kebab-case.ts` (Node) / `snake_case.py` (Python).
- **Class**: `PascalCase` (`OrderService`). **Method**: `camelCase`/`snake_case` theo stack. **Constant**: `UPPER_SNAKE_CASE`.
- **1 class = 1 file (top-level)** — KHÔNG nested/inner class cho entity / DTO / service / repository / mapper / controller (tách file riêng). **Ngoại lệ duy nhất**: nested `static` class cho nhóm config `@ConfigurationProperties` (vd `ClientConfig` trong `IntegrationClientProperties`) — KHÔNG chứa business logic.
- **Package/module**: theo mô hình đã chốt — Layered (`controller`/`service`/`repository`/…) hoặc Hexagonal (`domain`/`application`/`adapter`). Cấu trúc đầy đủ + nơi đặt từng artifact xem `ref-backend-pattern`.
- **Test**: `{Unit}Test` / `test_{module}` theo runner.

## Java coding rules

### Convention sẵn có trước
- Trước khi tạo/sửa code: xem class tương tự trong cùng module.
- Theo package structure / naming / annotation / exception / response / mapper / test style **sẵn có**.
- KHÔNG tự thêm pattern mới nếu project đã có convention. Nhiều convention cùng tồn tại → theo cái gần module đích nhất.

### Khai báo kiểu & import
- KHÔNG dùng `var`; khai báo kiểu tường minh cho local var, field, param và return type.
- KHÔNG dùng Fully Qualified Class Name (FQCN) trong khai báo (biến/param/return/generic) — dùng `import` tường minh (vd `List`, `Optional`, không `java.util.List`). Ngoại lệ duy nhất: collision cùng simple name (`java.sql.Date` vs `java.util.Date`).
- KHÔNG wildcard import (`import java.util.*`) — luôn import từng class cụ thể.
- **Thứ tự import**: `java` → `jakarta` → `org.springframework` → third-party → base package nội bộ project (vd `com.{org}.{app}`).

### Timestamp types theo layer
- **Request DTO** → `OffsetDateTime` (client gửi kèm offset, ISO-8601).
- **Entity / Response DTO / Event payload** → `Instant` (UTC; entity ↔ `TIMESTAMPTZ`).
- **Date-only** → `LocalDate` (khi API/data docs quy định).
- **KHÔNG `LocalDateTime`** (mất timezone, bug daylight saving). Convert tại service: `request.startTime().toInstant()`.

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

### Layering & injection
- **Framework annotation đúng package**: `@Entity` ở `entities/` (Layered, **KHÔNG `model/`**) hoặc `adapter/out/persistence/entities/` (Hexagonal), `@Service` ở `service/impl`, `@Repository` ở `repository`/adapter, `@RestController` ở `controller`/`adapter.in.web`.
- **Controller**: map request + validation annotation + gọi **service (interface)** + map response. **KHÔNG gọi repository trực tiếp** — phải qua service layer.
- **Service interface/impl split bắt buộc**: `service/{Entity}Service.java` = interface (KHÔNG annotation); `service/impl/{Entity}ServiceImpl.java` = `@Service` impl chứa business logic + transaction boundary + business validation + orchestration + quyết định publish event. Controller/caller inject **interface** — KHÔNG inject `*ServiceImpl`.
- **Repository**: chỉ persistence/query. **Mapper**: chỉ convert Entity/DTO/Command/Event/Response; KHÔNG gọi service/repository/external client. **Config class**: chỉ define bean + bind config.
- KHÔNG đặt business logic trong Controller, Repository, Mapper, Entity listener, hay Config.
- **Dependency injection**: `@RequiredArgsConstructor` + `private final` (constructor injection). KHÔNG `@Autowired` field injection.

### DTO & API contract
- KHÔNG expose entity trực tiếp ra response; KHÔNG dùng entity làm request body. Dùng Request DTO + Response DTO ở biên API.
- **MapStruct** là default cho conversion DTO/entity/event payload; map tay chỉ khi 1-2 field trivial hoặc có logic custom MapStruct không biểu đạt rõ. KHÔNG nhét mapping field-to-field vào controller/service. Mapper là interface, KHÔNG impl tay. Config `@Mapper` + `MapperComponent` (custom converter) → `ref-backend-pattern §5`.
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
- **Truy vấn** (3 mức): (1) derived query / **JPQL** `@Query` cho query tĩnh, điều kiện cố định; (2) **Specification** (Criteria) cho **filter động / optional param / search nhiều điều kiện**; (3) `nativeQuery` chỉ khi JPQL/Specification không đáp ứng (last resort + `:tenantId` + comment + test isolation).
  - **JPQL ≠ native**: `@Query("SELECT t FROM Tenant t …")` (tên entity) là JPQL — hợp lệ. `nativeQuery = true` (SQL thô, tên bảng) mới là native.
  - **Anti-pattern (CẤM)**: nhồi optional filter vào 1 JPQL kiểu `(:status IS NULL OR t.status = :status) AND (:search IS NULL OR …)` → khó đọc, optimizer không tận index. Filter động/optional/search PHẢI dùng **Specification**.
- **Quan hệ bảng — KHÔNG khai báo foreign key constraint** (áp dụng mọi quan hệ, kể cả trong cùng boundary):
  - Liên kết bằng id column thường (vd `customer_id BIGINT`), KHÔNG `FOREIGN KEY ... REFERENCES`; migration không sinh FK.
  - Toàn vẹn tham chiếu + cascade enforce ở **application/service layer**, không ở DB.
  - BẮT BUỘC tự **add index** cho id column dùng để join/lookup (không có FK nên không tự index).
  - Lý do: mỗi boundary sở hữu DB riêng (polyrepo) → không thể FK cross-DB; tránh ràng buộc cứng gây khó scale/sharding và xoá/migrate.
- KHÔNG sửa migration đã apply — thêm file migration mới cho schema change.
- Column NOT NULL mới phải có default value hoặc strategy an toàn (thêm nullable → backfill → enforce NOT NULL).
- Add **index** cho field hay filter/join/sort/lookup.
- Tránh **N+1**; KHÔNG gọi repository lặp trong loop khi có thể bulk query.
- **ID strategy**: entity expose qua API/event → **UUID v4** PK; entity internal / junction / `outbox_event` → **BIGSERIAL** (`@GeneratedValue(IDENTITY)`, giảm index size).
- `saveAll()` chỉ batch thật khi có config (thiếu thì vẫn N INSERT riêng lẻ):
  ```yaml
  spring.jpa.properties.hibernate.jdbc.batch_size: 50
  spring.jpa.properties.hibernate.order_inserts: true
  spring.jpa.properties.hibernate.order_updates: true
  ```

### Event, job & idempotency
- Webhook / payment callback / message consumer / scheduled job / retry job / external callback PHẢI **idempotent**.
- KHÔNG xử lý trùng cùng `event id` / `transaction id` / `request id` / idempotency key.
- Event payload dùng DTO/schema class tường minh — KHÔNG raw `Map`, KHÔNG reuse entity làm payload.
- Scheduled job xử lý data lớn bằng pagination / batching / streaming.
- **Naming** (theo `docs/architecture/events/` convention): topic `{prefix}.{boundary}.{event-type}` · consumer group `{prefix}-{boundary}-{source}-consumer` · DLQ `{topic}-dlq` (giữ original event + failure_reason + retry_count).
- **Outbox**: lưu event cùng `@Transactional` với business data; recovery scheduler dùng `FOR UPDATE SKIP LOCKED` (tránh concurrent scheduler conflict). **Inbox**: insert `inbox_event(event_id PK)` + business logic trong cùng transaction; duplicate → `DataIntegrityViolationException` → acknowledge + skip (KHÔNG throw CONFLICT về client).
- Schema evolution **additive**; breaking → topic version mới. Code đầy đủ (producer/consumer/outbox/DLT) → `ref-backend-kafka`.

### External integration (downstream HTTP)
- External base URL / credential / timeout / retry / pool / feature flag phải configurable (không hardcode).
- Dùng **declarative HTTP client interface** (`@HttpExchange`) — KHÔNG `new RestTemplate()` thủ công trong business method; inject **interface**, không inject `RestClient` trực tiếp.
- **Error**: 4xx → typed `BusinessException`; 5xx / timeout → `EXTERNAL_SERVICE_ERROR`; KHÔNG return `null`; luôn có timeout + retry/fallback; propagate `Authorization` / `X-Tenant-ID` / `X-Correlation-ID`.
- Config + factory (Apache HttpClient5 timeout/pool) + error handler + header propagation đầy đủ → `ref-backend-restclient`.

### Logging & security
- KHÔNG log password / token / secret / OTP / Authorization header / refresh token / access token / PII nhạy cảm; KHÔNG log full request/response body.
- KHÔNG bypass authentication/authorization check.
- KHÔNG hardcode giá trị định danh / phân quyền (tenant, user, role, scope… tùy mô hình dự án) — lấy từ security context chuẩn của project.
- Internal endpoint dùng cơ chế internal auth đã duyệt (mTLS / internal JWT / gateway verification).

**Lombok — annotation cho phép / cấm:**

| Annotation | Đặt ở | Ghi chú |
|---|---|---|
| `@RequiredArgsConstructor`, `@Slf4j` | `@Service`/`@Component`/handler | constructor injection — đi cùng `private final` |
| `@Getter @Setter @NoArgsConstructor @AllArgsConstructor` | `@Entity` | **KHÔNG `@Data`** trên `@Entity` |
| `@Builder`, `@Value` | DTO / value object | OK |
| `@Data` trên `@Entity` | — | **CẤM** (equals/hashCode all-field hỏng) |

**SLF4J log level:** `ERROR` (failure escape handler) · `WARN` (degraded: retry/fallback/unexpected) · `INFO` (business milestone: entity created, flow done) · `DEBUG` (dev-only, never prod). KHÔNG log stacktrace ở `WARN` → dùng `log.error("msg", e)`.

**MDC** set ở request boundary (`traceId`/`tenantId`), clear ở `finally`/filter. Config structured log (JSON) chi tiết → `ref-backend-logging`.

### Code quality
- Method nhỏ, đọc được theo nghiệp vụ; tách logic/điều kiện phức tạp thành private method tên có nghĩa.
- Tránh if/else và loop lồng sâu. Stream API chỉ dùng khi tăng readability.
- KHÔNG duplicate business logic. KHÔNG trả null collection — trả empty collection.
- **Collection bất biến đúng mục đích**: `List.of()` / `Set.of()` / `Map.of()`, `Collections.unmodifiable*`, `Arrays.asList()` là **immutable** (riêng `Stream.toList()` cũng immutable — OK khi return read-only). Chỉ dùng cho constant / default rỗng / return read-only. Nếu collection sẽ `add/remove/put` về sau → khởi tạo mutable (`new ArrayList<>()` / `new HashMap<>()`), nếu không sẽ `UnsupportedOperationException` lúc runtime.
- KHÔNG thêm dependency mới nếu không cần — ưu tiên util sẵn có của project.

### Comment quality — agent-first
> Agent đọc code để phát triển tiếp; comment mang đủ business context để khỏi phải lần 10 file. KHÔNG mô tả WHAT (tên method/field đã nói).
- **PHẢI comment**:
  - `BR-{ID}`: khi enforce business rule cornerstone (vd vì sao `tenantId` phải boxed).
  - `ADR-{N}`: khi implement theo architectural decision.
  - `WHY`: khi lý do kỹ thuật không rõ từ code (vd vì sao `@Transactional(REQUIRES_NEW)` cho từng outbox event).
  - `FEAT-{N} AC-{M}`: khi method implement trực tiếp 1 AC.
- **KHÔNG comment**: mô tả WHAT (`// Get tenant by id`) · authorship/wave/date (git lưu) · comment đại trà vô giá trị (`// This service handles tenant operations`).

### Feature flags & backward compatibility
- **Feature flag** naming `FF_{BOUNDARY}_W{WAVE}_{FEATURE}`; default **DISABLED ở prod** (ENABLED ở staging); hỗ trợ gradual rollout; **kill switch instant** (tắt feature ngay khi có bug).
- **Backward compat / legacy**: KHÔNG break API contract đã published; KHÔNG rename/drop DB column đã deploy; KHÔNG sửa code runnable wave trước (chỉ additive); deprecated giữ ≥ 1 wave buffer; test wave trước PHẢI pass.

### Testing
- Thêm/cập nhật test khi đổi business logic; coverage ≥ **80%**. KHÔNG xoá test cũ trừ khi được yêu cầu rõ; test wave trước PHẢI pass (regression). KHÔNG `@Disabled` thiếu blocker ref.
- **Unit** (logic thuần: service/guard/validator/handler): `@ExtendWith(MockitoExtension.class)`, mock mọi dependency ngoài class test. KHÔNG DB/Redis/Kafka/HTTP, KHÔNG Spring context, **KHÔNG H2**.
- **Integration**: **TestContainers PostgreSQL** (DB thật) — **KHÔNG H2** (H2 thiếu JSONB, dialect khác ẩn migration/schema bug); Kafka container; REST qua MockMvc.
- **BẮT BUỘC ≥1 integration test BOOT Spring context trên Testcontainers Postgres + chạy MIGRATION + `ddl-auto: validate`** → Hibernate validate **entity ↔ schema** lúc boot: **sai tên cột / kiểu cột (vd `varchar(3)` ↔ `CHAR(3)`, `TIMESTAMPTZ` ↔ `Instant`) = test ĐỎ NGAY ở DEV** (không để lộ tới `/dev-handoff` lúc connect DB). Đây là chốt bắt schema-drift mà unit/mock + review tĩnh không thấy.
- Naming `should_{expected}_when_{condition}`. Cover: success / validation fail / not found / permission fail / tenant boundary / idempotency / edge.

## Coding checklist — verify trước khi báo done
- [ ] Coverage ≥ 80%; không `@Disabled` thiếu blocker ref; **không H2** trong test.
- [ ] **Gate `code_compliance` (dev-handoff)** sẽ HARD-FAIL nếu: thiếu `Dockerfile`; build file khai `com.h2database`; `application.{yml,properties}` có `jdbc:h2:` hoặc `ddl-auto: create-drop`; hoặc không có file config. → scaffold Dockerfile (multi-stage **Gradle `bootJar`→JRE** — default) + config Postgres + migration (Flyway/Liquibase) NGAY khi dev (không để handoff mới sửa).
- [ ] Không hardcode secret/URL/credential; configurable value externalize qua `@ConfigurationProperties` (không `private (static) final` literal); không rải `@Value` khi ≥ 2 props cùng prefix.
- [ ] Error code chỉ từ `api-{boundary}.md`; exception dùng enum/descriptor typed (không hardcode code/message tại throw site).
- [ ] **springdoc-openapi wired** (`/v3/api-docs` + `/swagger-ui`) khi scaffold, contract khớp `api-{boundary}.md`.
- [ ] Không `nativeQuery` nếu không cần; nếu có → `:tenantId` + comment + test isolation. Filter động/optional → **Specification** (không JPQL `(:x IS NULL OR …)`).
- [ ] DTO đúng `dto/request/` + `dto/response/`; conversion dùng **MapStruct** (mapper là interface, không impl tay).
- [ ] Service interface trong `service/`, impl trong `service/impl/`; inject **interface**; `@RequiredArgsConstructor` + `private final` (không `@Autowired`).
- [ ] Không FQCN inline / wildcard import; import order đúng.
- [ ] `Instant`/`OffsetDateTime`/`LocalDate` đúng layer (không `LocalDateTime`); id/tenant **boxed**; entity `@Getter @Setter @NoArgsConstructor @AllArgsConstructor` (không `@Data`).
- [ ] Quan hệ qua id (**no FK**) + index; migration `V{wave}_{seq}__` additive (không sửa migration đã apply).
- [ ] Outbox event commit cùng transaction business data; consumer idempotent.
- [ ] `tenant_id` filter trong MỌI repository query (nếu multi-tenant).
- [ ] Downstream HTTP qua `@HttpExchange` (không `new RestTemplate()`).
- [ ] Cấu trúc khớp `ref-backend-pattern` (kiến trúc HLD §4) + `hld-{boundary}.md`.

## Done
- Build pass, lint pass, test pass coverage ≥ 80%.
- File chỉ thay đổi trong `owned_paths` của boundary.
- Cấu trúc khớp `ref-backend-pattern` (mô hình theo ADR) + `hld-{boundary}.md`.
- KG cập nhật, không có `discipline.blockers`.
