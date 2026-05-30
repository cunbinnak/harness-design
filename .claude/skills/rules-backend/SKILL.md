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

## Interface + impl
1. **Service & repository khai báo qua interface trước, impl riêng** — caller phụ thuộc abstraction, KHÔNG phụ thuộc impl cụ thể.
2. **Port (repository/gateway interface)** đặt ở `domain/ports/`; **impl (adapter)** ở `infrastructure/` (DIP — domain không biết JPA/HTTP).
3. **Application service**: interface (`OrderService`) + impl (`OrderServiceImpl`); controller inject interface.
4. **Constructor injection** (`final` field) — KHÔNG `@Autowired` trên field/setter.
5. Naming: `XxxService` đi với `XxxServiceImpl`; port `XxxRepository` (trong `domain/ports/`) đi với adapter `XxxRepositoryAdapter`/`JpaXxxRepository` (trong `infrastructure/`).

```java
// domain/ports/OrderRepository.java   (interface — domain định nghĩa)
public interface OrderRepository { Optional<Order> findByCode(String code); Order save(Order o); }

// infrastructure/JpaOrderRepository.java   (impl — adapter)
@Repository
class JpaOrderRepository implements OrderRepository { /* dùng Spring Data / EntityManager */ }

// application/OrderServiceImpl.java   (constructor injection)
@Service
class OrderServiceImpl implements OrderService {
    private final OrderRepository repo;
    OrderServiceImpl(OrderRepository repo) { this.repo = repo; }   // KHÔNG @Autowired field
}
```

## Naming & package
- **File**: theo stack — `PascalCase.java` (Java) / `kebab-case.ts` (Node) / `snake_case.py` (Python).
- **Class**: `PascalCase` (`OrderService`). **Method**: `camelCase`/`snake_case` theo stack. **Constant**: `UPPER_SNAKE_CASE`.
- **Package/module**: theo layer của mô hình kiến trúc (`api`/`application`/`domain`/`infrastructure`) — xem `ref-backend-pattern`.
- **Test**: `{Unit}Test` / `test_{module}` theo runner.

## Done
- Build pass, lint pass, test pass coverage ≥ 80%.
- File chỉ thay đổi trong `owned_paths` của boundary.
- Cấu trúc khớp `ref-backend-pattern` (mô hình theo ADR) + `hld-{boundary}.md`.
- KG cập nhật, không có `discipline.blockers`.
