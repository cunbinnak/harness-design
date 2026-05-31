---
name: ref-backend-logging
description: Pattern logging backend — config (JSON structured + level theo profile), SLF4J usage, MDC correlation (traceId/tenantId), masking dữ liệu nhạy cảm, exception logging tập trung. Load khi cần chuẩn hóa log.
---

# Reference: Backend Logging

> **Audience:** `dev:backend`, `fix:backend`, `review:backend` — load on-demand khi setup/chuẩn hóa logging.
> **Quan hệ:** convention bắt buộc → `rules-backend` (§Logging & security); observability/tracing nâng cao → `ref-backend-config`.
> **Nguyên tắc:** structured log (JSON) ở môi trường thật; correlation qua MDC (`traceId`); KHÔNG log dữ liệu nhạy cảm; log exception 1 chỗ với context.

## 1. Config — appender theo profile + level

`logback-spring.xml`:
```xml
<configuration>
  <!-- local: console người đọc -->
  <springProfile name="local">
    <appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
      <encoder><pattern>%d{HH:mm:ss} %-5level [%X{traceId}] %logger{36} - %msg%n</pattern></encoder>
    </appender>
    <root level="INFO"><appender-ref ref="CONSOLE"/></root>
  </springProfile>

  <!-- dev/staging/prod: JSON structured (logstash encoder) -->
  <springProfile name="dev,staging,prod">
    <appender name="JSON" class="ch.qos.logback.core.ConsoleAppender">
      <encoder class="net.logstash.logback.encoder.LogstashEncoder">
        <includeMdcKeyName>traceId</includeMdcKeyName>
        <includeMdcKeyName>tenantId</includeMdcKeyName>
        <includeMdcKeyName>userId</includeMdcKeyName>
      </encoder>
    </appender>
    <root level="INFO"><appender-ref ref="JSON"/></root>
  </springProfile>
</configuration>
```

`application.yml` — level theo package (không hardcode trong code):
```yaml
logging:
  level:
    root: INFO
    com.example.order: DEBUG
    org.springframework.web: WARN
    org.hibernate.SQL: ${SQL_LOG_LEVEL:WARN}
```

## 2. Logger usage (SLF4J)

```java
public class OrderService {
    private static final Logger log = LoggerFactory.getLogger(OrderService.class);

    void create(...) {
        log.info("order created id={} tenant={}", orderId, tenantId);   // parameterized, KHÔNG concat chuỗi
        log.debug("order payload size={}", lines.size());               // chi tiết dev -> DEBUG
    }
}
```
- **Levels:** `ERROR` (cần can thiệp) · `WARN` (bất thường có thể chịu được) · `INFO` (mốc nghiệp vụ) · `DEBUG` (chi tiết dev).
- Dùng placeholder `{}`, KHÔNG `"... " + var` (tránh tạo chuỗi khi level tắt).
- KHÔNG `System.out.println` / `printStackTrace()`.

## 3. MDC correlation (traceId / tenantId / userId)

```java
// gắn traceId mỗi request, clear sau khi xong
@Component
class CorrelationIdFilter extends OncePerRequestFilter {
    static final String TRACE_ID = "traceId";
    static final String HEADER = "X-Request-Id";

    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain)
            throws ServletException, IOException {
        String traceId = Optional.ofNullable(req.getHeader(HEADER)).orElse(UUID.randomUUID().toString());
        MDC.put(TRACE_ID, traceId);
        res.setHeader(HEADER, traceId);
        try {
            chain.doFilter(req, res);
        } finally {
            MDC.clear();   // BẮT BUỘC clear — tránh leak context sang request/thread khác (thread pool)
        }
    }
}
```
- Sau khi resolve security context: `MDC.put("tenantId", ctx.tenantId())`, `MDC.put("userId", ctx.userId())`.
- Async / @KafkaListener / @Scheduled: tự set MDC (vd `traceId` từ event header) + clear ở `finally`.

## 4. Masking dữ liệu nhạy cảm

```java
log.info("login user={} ip={}", userId, ip);     // OK
// log.info("auth token={}", token);             // CẤM: token/password/secret/OTP/Authorization/PII
log.info("notify email={}", Masks.email(email)); // mask khi buộc phải log: a***@x.com
```
- KHÔNG log: password, token, refresh/access token, secret, OTP, Authorization header, PII (số CMND, thẻ…).
- Cần log định danh → mask (email/phone/card) qua util chung.

## 5. Exception logging (tập trung, không lặp)
- Log exception **1 lần ở boundary** (`GlobalExceptionHandler`) với context (`traceId` đã ở MDC) — KHÔNG `log + rethrow` ở mỗi tầng.
- Lỗi nghiệp vụ kỳ vọng (`BusinessException`) → `WARN`/`INFO` (không cần stacktrace dài).
- Lỗi hệ thống ngoài dự kiến → `ERROR` + stacktrace (exception là tham số CUỐI, không nhét vào `{}`).

```java
@RestControllerAdvice
class GlobalExceptionHandler {
    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(BusinessException.class)
    ResponseEntity<ErrorResponse> handleBusiness(BusinessException e) {
        log.warn("business error code={}", e.errorCode().code());            // không stacktrace
        return ResponseEntity.status(e.errorCode().httpStatus()).body(/* ErrorResponse */ null);
    }

    @ExceptionHandler(Exception.class)
    ResponseEntity<ErrorResponse> handleUnexpected(Exception e) {
        log.error("unexpected error", e);                                    // exception cuối -> stacktrace
        return ResponseEntity.status(500).body(/* ErrorResponse code=INTERNAL_ERROR */ null);
    }
}
```

## Anti-patterns (review flag)
- `System.out.println` / `e.printStackTrace()` thay cho logger.
- Concat chuỗi (`"id=" + id`) thay vì placeholder `{}`.
- Log password/token/secret/OTP/PII (kể cả trong DEBUG).
- `log.error` + rethrow ở nhiều tầng → log trùng 1 lỗi nhiều lần.
- Quên `MDC.clear()` → traceId/tenant leak sang request khác (thread pool).
- Đặt level cứng trong code thay vì `application.yml`.

## Done
- Structured JSON ở môi trường thật; mọi log có `traceId` (MDC); không lộ dữ liệu nhạy cảm; exception log tập trung ở boundary; level theo config.
