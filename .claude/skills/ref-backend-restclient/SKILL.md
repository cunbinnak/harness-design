---
name: ref-backend-restclient
description: Pattern gọi downstream HTTP cho backend — @HttpExchange interface + RestClient proxy factory, config per-client (base-url/timeout/retry/pool), error handler (4xx→BusinessException, 5xx/timeout→EXTERNAL_SERVICE_ERROR), header propagation (Authorization/X-Tenant-ID/X-Correlation-ID). Load khi boundary gọi external / cross-boundary qua HTTP.
---

# Reference: Backend RestClient (downstream HTTP)

> **Purpose:** gọi service external / cross-boundary qua HTTP an toàn, declarative. Load khi boundary có outbound HTTP (`rules-backend §External` trỏ tới).
> **Quan hệ:** `rules-backend` = WHAT (rule); file này = HOW (config + factory + error). Security/secret config chung → `ref-backend-config`.

## 1. Nguyên tắc
- Mỗi downstream = **1 `@HttpExchange` interface** + 1 RestClient proxy (base-url/timeout từ config).
- Inject **interface** vào service — KHÔNG inject `RestClient`/factory trực tiếp.
- KHÔNG `new RestTemplate()` thủ công; KHÔNG `WebClient` trừ khi HLD chỉ định reactive.

## 2. Config per-client (`@ConfigurationProperties` — không hardcode)
```java
@ConfigurationProperties(prefix = "integration")
@Getter @Setter
public class IntegrationClientProperties {
    private Map<String, ClientConfig> clients = new HashMap<>();
    @Getter @Setter
    public static class ClientConfig {
        private String baseUrl;
        private Duration connectTimeout = Duration.ofSeconds(2);
        private Duration readTimeout = Duration.ofSeconds(5);
        private int maxConnTotal = 100;
        private int maxConnPerRoute = 20;
        private int maxRetries = 2;
    }
}
```
```yaml
# application.yml — env placeholder, KHÔNG hardcode
integration:
  clients:
    payment:
      base-url: ${PAYMENT_BASE_URL}
      connect-timeout: 2s
      read-timeout: 5s
      max-retries: 2
```

## 3. `@HttpExchange` interface (declarative)
```java
@HttpExchange(url = "/v1", accept = "application/json", contentType = "application/json")
public interface PaymentClient {
    @PostExchange("/payments")
    PaymentResponse createPayment(@RequestBody CreatePaymentRequest req);

    @GetExchange("/payments/{id}")
    PaymentResponse getPayment(@PathVariable String id);
}
```

## 4. RestClient proxy factory + bean (Apache HttpClient5)
```java
@Configuration
@RequiredArgsConstructor
public class RestClientConfig {
    private final IntegrationClientProperties props;

    @Bean
    public PaymentClient paymentClient(RestClient.Builder builder,
                                       ClientHeaderInterceptor headers,
                                       ClientErrorHandler errors) {
        IntegrationClientProperties.ClientConfig c = props.getClients().get("payment");
        RestClient rc = builder
            .baseUrl(c.getBaseUrl())
            .requestInterceptor(headers)                       // propagate header (xem §6)
            .defaultStatusHandler(errors)                      // map lỗi → typed exception (xem §5)
            .requestFactory(requestFactory(c))                 // timeout/pool từ config (bên dưới)
            .build();
        return HttpServiceProxyFactory
            .builderFor(RestClientAdapter.create(rc))
            .build()
            .createClient(PaymentClient.class);
    }

    // Apache HttpClient5: connect/read timeout + connection pool — TẤT CẢ từ config, KHÔNG hardcode
    private ClientHttpRequestFactory requestFactory(IntegrationClientProperties.ClientConfig c) {
        ConnectionConfig connectionConfig = ConnectionConfig.custom()
            .setConnectTimeout(Timeout.of(c.getConnectTimeout()))
            .setSocketTimeout(Timeout.of(c.getReadTimeout()))
            .build();

        PoolingHttpClientConnectionManager connectionManager =
            PoolingHttpClientConnectionManagerBuilder.create()
                .setDefaultConnectionConfig(connectionConfig)
                .setMaxConnTotal(c.getMaxConnTotal())
                .setMaxConnPerRoute(c.getMaxConnPerRoute())
                .build();

        RequestConfig requestConfig = RequestConfig.custom()
            .setConnectionRequestTimeout(Timeout.of(c.getConnectTimeout()))
            .setResponseTimeout(Timeout.of(c.getReadTimeout()))
            .build();

        CloseableHttpClient httpClient = HttpClients.custom()
            .setConnectionManager(connectionManager)
            .setDefaultRequestConfig(requestConfig)
            .build();

        return new HttpComponentsClientHttpRequestFactory(httpClient);
    }
}
```
> Nhiều downstream → mỗi client 1 `@Bean` + lấy `ClientConfig` theo key (`props.getClients().get("{name}")`); factory dùng chung.

## 5. Error handler — map về typed exception (KHÔNG nuốt, KHÔNG null)
```java
@Component
@Slf4j
public class ClientErrorHandler implements ResponseErrorHandler {
    @Override public boolean hasError(ClientHttpResponse res) throws IOException {
        return res.getStatusCode().isError();
    }
    @Override public void handleError(ClientHttpResponse res) throws IOException {
        HttpStatusCode status = res.getStatusCode();
        log.warn("downstream error status={} traceId={}", status, MDC.get("traceId"));
        if (status.is4xxClientError()) {
            throw new BusinessException(ExternalErrorCode.EXTERNAL_BAD_REQUEST);
        }
        throw new BusinessException(ExternalErrorCode.EXTERNAL_SERVICE_ERROR);   // 5xx / timeout
    }
}
```
- 4xx → typed `BusinessException` (theo `ExternalErrorCode` enum); 5xx/timeout → `EXTERNAL_SERVICE_ERROR`.
- KHÔNG return `null`; KHÔNG nuốt lỗi — log correlation + rethrow typed. Retry/fallback theo `maxRetries`.

## 6. Header propagation (từ security context / MDC)
```java
@Component
public class ClientHeaderInterceptor implements ClientHttpRequestInterceptor {
    @Override public ClientHttpResponse intercept(HttpRequest req, byte[] body,
                                                  ClientHttpRequestExecution exec) throws IOException {
        req.getHeaders().add("Authorization", currentBearerToken());   // từ SecurityContext, KHÔNG hardcode
        req.getHeaders().add("X-Tenant-ID", currentTenantId());
        req.getHeaders().add("X-Correlation-ID", MDC.get("traceId"));
        return exec.execute(req, body);
    }
}
```

## Forbidden
- `new RestTemplate()` / inject `RestTemplate`/`RestClient` thủ công trong business method.
- `WebClient` trừ khi HLD chỉ định reactive.
- Hardcode base-url / timeout / pool / credential — phải qua `@ConfigurationProperties`.
- Return `null` khi lỗi — map về typed exception.
- Nuốt lỗi downstream (catch không log/rethrow).

## Done
- Mỗi downstream có `@HttpExchange` interface + RestClient proxy (timeout/pool config-driven); error map về typed exception; header propagate; KHÔNG `RestTemplate` thủ công.
