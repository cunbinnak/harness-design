---
name: ref-backend-redis
description: Pattern Redis cho backend — config đầy đủ (Lettuce connection + RedisTemplate<String,Object> serializer JSON), RedisService interface + impl đầy đủ function (value/hash/list/set/zset/key/counter/lock), TTL từ config, cache-aside. Load khi boundary dùng Redis.
---

# Reference: Backend Redis (Spring Data Redis)

> **Audience:** `dev:backend`, `fix:backend`, `review:backend` — load on-demand khi boundary dùng Redis.
> **Quan hệ:** convention bắt buộc → `rules-backend`; config nâng cao (cluster/sentinel) → `ref-backend-config`.
> **Nguyên tắc:** truy cập Redis qua **interface `RedisService`** + impl (`RedisServiceImpl`) ở `infrastructure/` (Layered) hoặc `adapter/out/cache` (Hexagonal). KHÔNG rải `RedisTemplate` trong service/controller.

## 1. Config — connection + serializer

`application.yml`:
```yaml
spring:
  data:
    redis:
      host: ${REDIS_HOST:localhost}
      port: ${REDIS_PORT:6379}
      password: ${REDIS_PASSWORD:}
      timeout: 2s
      lettuce:
        pool: { max-active: 16, max-idle: 8, min-idle: 2 }

app:
  cache:
    key-prefix: ${CACHE_PREFIX:order}            # prefix theo boundary
    default-ttl: 10m
    ttl: { order-detail: 10m, order-list: 5m }   # TTL khai ở yml, KHÔNG hardcode trong code
```

```java
@ConfigurationProperties(prefix = "app.cache")
public record CacheProperties(String keyPrefix, Duration defaultTtl, Map<String, Duration> ttl) {
    public Duration ttlOf(String cache) { return ttl.getOrDefault(cache, defaultTtl); }
}

@Configuration
@EnableConfigurationProperties(CacheProperties.class)
class RedisConfig {

    // 1) Connection (Lettuce) — host/port/password đọc từ spring.data.redis (RedisProperties)
    @Bean
    LettuceConnectionFactory redisConnectionFactory(RedisProperties p) {
        RedisStandaloneConfiguration cfg = new RedisStandaloneConfiguration(p.getHost(), p.getPort());
        if (StringUtils.hasText(p.getPassword())) cfg.setPassword(p.getPassword());
        return new LettuceConnectionFactory(cfg);
    }

    // 2) ObjectMapper cho Redis — bật type info để get() trả về ĐÚNG class khi value là Object
    private ObjectMapper redisObjectMapper() {
        ObjectMapper om = new ObjectMapper();
        om.registerModule(new JavaTimeModule());                       // Instant / LocalDateTime
        om.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
        om.activateDefaultTyping(                                       // lưu kèm @class -> đọc lại đúng kiểu
            om.getPolymorphicTypeValidator(),
            ObjectMapper.DefaultTyping.NON_FINAL, JsonTypeInfo.As.PROPERTY);
        return om;
    }

    // 3) Template cho Object — key = String, value = JSON (serialize Object TỰ ĐỘNG, không serialize tay)
    @Bean
    RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory cf) {
        RedisTemplate<String, Object> tpl = new RedisTemplate<>();
        tpl.setConnectionFactory(cf);
        StringRedisSerializer keySer = new StringRedisSerializer();
        GenericJackson2JsonRedisSerializer valSer = new GenericJackson2JsonRedisSerializer(redisObjectMapper());
        tpl.setKeySerializer(keySer);
        tpl.setHashKeySerializer(keySer);
        tpl.setValueSerializer(valSer);
        tpl.setHashValueSerializer(valSer);
        tpl.afterPropertiesSet();
        return tpl;
    }
    // StringRedisTemplate (counter/lock raw string) — Spring Boot tự cấu hình sẵn, inject thẳng.
}
```

> **Serialize Object:** lưu Object qua `RedisTemplate<String,Object>` → `GenericJackson2JsonRedisSerializer` tự serialize sang JSON và lưu kèm `@class`, nên `get(key, Type)` đọc lại đúng kiểu (chỉ cần cast). **Counter/lock** dùng `StringRedisTemplate` (thao tác số/chuỗi raw, không qua JSON serializer).

## 2. RedisService — interface (đầy đủ function)

```java
public interface RedisService {

    // ===== Value (Object → JSON) =====
    void set(String key, Object value);
    void setWithTTL(String key, Object value, Duration ttl);
    boolean setIfAbsent(String key, Object value, Duration ttl);        // SET NX PX
    <T> Optional<T> get(String key, Class<T> type);
    <T> T getOrLoad(String key, Class<T> type, Duration ttl, Supplier<T> loader);  // cache-aside

    // ===== Counter (raw) =====
    long increment(String key, long delta);
    long decrement(String key, long delta);

    // ===== Key =====
    boolean exists(String key);
    void delete(String key);
    void deleteByPattern(String pattern);                               // SCAN, không KEYS
    boolean expire(String key, Duration ttl);
    Duration getExpire(String key);
    Duration ttlOf(String cacheName);                                   // TTL từ CacheProperties

    // ===== Hash =====
    void hset(String key, String field, Object value);
    <T> Optional<T> hget(String key, String field, Class<T> type);
    <T> Map<String, T> hgetAll(String key, Class<T> type);
    void hdelete(String key, String... fields);

    // ===== List =====
    void rpush(String key, Object value);
    void lpush(String key, Object value);
    <T> Optional<T> lpop(String key, Class<T> type);
    <T> List<T> lrange(String key, long start, long end, Class<T> type);

    // ===== Set =====
    void sadd(String key, Object... values);
    <T> Set<T> smembers(String key, Class<T> type);
    boolean sismember(String key, Object value);

    // ===== Sorted Set =====
    void zadd(String key, Object value, double score);
    <T> List<T> zrange(String key, long start, long end, Class<T> type);

    // ===== Distributed lock =====
    boolean tryLock(String key, Duration ttl);                          // SET NX PX
    void unlock(String key);
    <T> T withLock(String key, Duration ttl, Supplier<T> action);       // lock -> action -> finally unlock
}
```

## 3. RedisServiceImpl — impl

```java
@Service
class RedisServiceImpl implements RedisService {

    private final RedisTemplate<String, Object> redis;     // Object → JSON (serializer ở RedisConfig)
    private final StringRedisTemplate stringRedis;         // counter / lock (raw)
    private final CacheProperties props;

    RedisServiceImpl(RedisTemplate<String, Object> redis, StringRedisTemplate stringRedis, CacheProperties props) {
        this.redis = redis; this.stringRedis = stringRedis; this.props = props;
    }

    // ---- Value (serialize Object tự động) ----
    public void set(String key, Object value) { redis.opsForValue().set(key, value); }
    public void setWithTTL(String key, Object value, Duration ttl) { redis.opsForValue().set(key, value, ttl); }
    public boolean setIfAbsent(String key, Object value, Duration ttl) {
        return Boolean.TRUE.equals(redis.opsForValue().setIfAbsent(key, value, ttl));
    }
    public <T> Optional<T> get(String key, Class<T> type) {
        Object raw = redis.opsForValue().get(key);
        return raw == null ? Optional.empty() : Optional.of(type.cast(raw));
    }
    public <T> T getOrLoad(String key, Class<T> type, Duration ttl, Supplier<T> loader) {
        Optional<T> cached = get(key, type);
        if (cached.isPresent()) return cached.get();
        T value = loader.get();
        if (value != null) setWithTTL(key, value, ttl);
        return value;
    }

    // ---- Counter (StringRedisTemplate) ----
    public long increment(String key, long delta) { Long v = stringRedis.opsForValue().increment(key, delta); return v == null ? 0 : v; }
    public long decrement(String key, long delta) { Long v = stringRedis.opsForValue().decrement(key, delta); return v == null ? 0 : v; }

    // ---- Key ----
    public boolean exists(String key) { return Boolean.TRUE.equals(redis.hasKey(key)); }
    public void delete(String key) { redis.delete(key); }
    public void deleteByPattern(String pattern) {
        ScanOptions opts = ScanOptions.scanOptions().match(pattern).count(100).build();
        try (Cursor<String> c = redis.scan(opts)) { c.forEachRemaining(redis::delete); }
    }
    public boolean expire(String key, Duration ttl) { return Boolean.TRUE.equals(redis.expire(key, ttl)); }
    public Duration getExpire(String key) {
        Long s = redis.getExpire(key, TimeUnit.SECONDS);
        return s == null || s < 0 ? Duration.ZERO : Duration.ofSeconds(s);
    }
    public Duration ttlOf(String cacheName) { return props.ttlOf(cacheName); }

    // ---- Hash ----
    public void hset(String key, String field, Object value) { redis.opsForHash().put(key, field, value); }
    public <T> Optional<T> hget(String key, String field, Class<T> type) {
        Object raw = redis.opsForHash().get(key, field);
        return raw == null ? Optional.empty() : Optional.of(type.cast(raw));
    }
    public <T> Map<String, T> hgetAll(String key, Class<T> type) {
        Map<Object, Object> raw = redis.opsForHash().entries(key);
        Map<String, T> out = new HashMap<>();
        raw.forEach((k, v) -> out.put((String) k, type.cast(v)));
        return out;
    }
    public void hdelete(String key, String... fields) { redis.opsForHash().delete(key, (Object[]) fields); }

    // ---- List ----
    public void rpush(String key, Object value) { redis.opsForList().rightPush(key, value); }
    public void lpush(String key, Object value) { redis.opsForList().leftPush(key, value); }
    public <T> Optional<T> lpop(String key, Class<T> type) {
        Object raw = redis.opsForList().leftPop(key);
        return raw == null ? Optional.empty() : Optional.of(type.cast(raw));
    }
    public <T> List<T> lrange(String key, long start, long end, Class<T> type) {
        List<Object> raw = redis.opsForList().range(key, start, end);
        return raw == null ? List.of() : raw.stream().map(type::cast).toList();
    }

    // ---- Set ----
    public void sadd(String key, Object... values) { redis.opsForSet().add(key, values); }
    public <T> Set<T> smembers(String key, Class<T> type) {
        Set<Object> raw = redis.opsForSet().members(key);
        return raw == null ? Set.of() : raw.stream().map(type::cast).collect(Collectors.toSet());
    }
    public boolean sismember(String key, Object value) { return Boolean.TRUE.equals(redis.opsForSet().isMember(key, value)); }

    // ---- Sorted Set ----
    public void zadd(String key, Object value, double score) { redis.opsForZSet().add(key, value, score); }
    public <T> List<T> zrange(String key, long start, long end, Class<T> type) {
        Set<Object> raw = redis.opsForZSet().range(key, start, end);
        return raw == null ? List.of() : raw.stream().map(type::cast).toList();
    }

    // ---- Lock (StringRedisTemplate, raw) ----
    public boolean tryLock(String key, Duration ttl) {
        return Boolean.TRUE.equals(stringRedis.opsForValue().setIfAbsent(key, "1", ttl));   // SET NX PX
    }
    public void unlock(String key) { stringRedis.delete(key); }
    public <T> T withLock(String key, Duration ttl, Supplier<T> action) {
        if (!tryLock(key, ttl)) throw new BusinessException(OrderErrorCode.LOCK_NOT_ACQUIRED);
        try { return action.get(); } finally { unlock(key); }
    }
}
```

> Lock production-grade (auto-renew/lease) nên dùng **Redisson** `RLock`; `SET NX PX` ở trên đủ cho lock đơn giản — chi tiết Redisson → `ref-backend-config`.

## 4. Key & TTL — lấy từ config
- **TTL** khai ở `application.yml` (`app.cache.ttl.*`), đọc qua `ttlOf("order-detail")` — KHÔNG hardcode `Duration.ofMinutes(...)`.
- **Prefix** từ `CacheProperties.keyPrefix` (theo boundary). Build key tùy boundary; nhiều key thì gom 1 helper `CacheKeys` (nhận prefix từ `CacheProperties`).
- Data nhạy cảm/theo người dùng: key PHẢI include `tenantId`/`userId`. Đổi schema cache → tăng `version` trong key.

## 5. Cách dùng

```java
// cache-aside (read) — TTL từ config; Object serialize/deserialize tự động
OrderResponse dto = redis.getOrLoad(key, OrderResponse.class, redis.ttlOf("order-detail"),
    () -> mapper.toResponse(repository.findById(id)
            .orElseThrow(() -> new BusinessException(OrderErrorCode.NOT_FOUND))));

// set Object có TTL
redis.setWithTTL("session:" + token, session, Duration.ofMinutes(30));

// invalidate sau khi update DB
repository.save(order);
redis.delete(key);                      // hoặc redis.deleteByPattern(prefix + ":list:*")

// rate-limit bằng counter (raw)
long hits = redis.increment("rate:" + userId, 1);
if (hits == 1) redis.expire("rate:" + userId, Duration.ofMinutes(1));
if (hits > 100) throw new BusinessException(OrderErrorCode.RATE_LIMITED);

// distributed lock — chống double-process
redis.withLock("lock:payment:" + orderId, Duration.ofSeconds(10), () -> {
    paymentService.capture(orderId);
    return null;
});
```

## Anti-patterns (review flag)
- Inject `RedisTemplate`/`opsForValue()` trực tiếp vào service/controller (phải qua `RedisService`).
- Hardcode TTL/prefix trong code thay vì `application.yml`.
- Cache không TTL; key data nhạy cảm thiếu `tenantId`/`userId`.
- Quên invalidate sau update DB → stale data.
- Dùng `KEYS *` (block Redis) thay vì `SCAN`.
- Distributed lock không TTL / không unlock.

## Done
- Truy cập Redis qua `RedisService`; serialize Object qua serializer ở config; TTL/prefix từ config; cache-aside + invalidation đúng; lock có TTL; không leak cross-tenant.
