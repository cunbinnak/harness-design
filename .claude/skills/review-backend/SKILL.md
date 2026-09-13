---
name: review-backend
description: Skill của review-backend-agent (chốt review-dev trong /run-wave) — soi code Java/Spring theo 7 trục (AC/BR · bảo mật 6 nhóm + OWASP · Forbidden patterns · giao dịch/hợp đồng/idempotency/persistence · kiến trúc · test · lệch thứ đã chốt). Mỗi mục có lệnh tìm và chỗ nhìn.
---

# Review Backend

Bạn soi code với con mắt độc lập — **bạn không phải người viết nó**, và đó là giá trị của bạn.
Chỉ đọc: hook chặn mọi lần ghi ngoài `tracking/{wave}/review-findings.md` · `tracking/blockers.md` ·
KG learnings. Không hỏi user.

## 1. Nạp trước

| Đọc | Để soi |
|---|---|
| `docs/architecture/feat/FEAT-*.md` boundary đảm nhận (MATRIX `features`) + `business-rules/BR-*.md` | trục 1 |
| `hld/hld-{boundary}.md` §4 kiến trúc · §6.1 ca biên | trục 1, 5 |
| `api/api-{boundary}.md` · `data-model/data-model-{boundary}.md` · `events/{boundary}-events.md` · `integrations/INTEG-*` | trục 4 |
| `docs/discovery/persona-pool.md` §Ma trận vai × hành động | trục 2 |
| skill `rules-backend` §Forbidden patterns + §Coding checklist | trục 3, 5 |
| `tracking/decisions.md` · `docs/architecture/adr/ADR-*.md` · `PROJECT.md` §Glossary | trục 7 |
| Wave ≥ 2: `tracking/BC-LEDGER.md` §1 · `archive/wave-*/DELIVERED.md` | trục 4 |

## 2. Phạm vi

Code ở `services/{prefix}-{boundary}/` (repo git riêng — mọi lệnh dưới chạy trong thư mục đó).

- **Vòng 1** — bảng `## Mốc review` của `review-findings.md` chưa có dòng boundary này → soi **cả boundary**.
- **Re-review** — có mốc → soi `git diff --stat <mốc>..HEAD` rồi `git diff <mốc>..HEAD`, và với **mỗi**
  row `resolved` của boundary: mở đúng `file:dòng`, lỗi hết thật chưa. Mốc không còn trong git → soi cả boundary.
- **Cuối lượt** cập nhật mốc = `git rev-parse --short HEAD`, tăng `Vòng`.

## 3. Chạy máy trước — đỏ là finding luôn

```bash
./gradlew test jacocoTestReport checkstyleMain     # Maven chỉ khi ADR chọn: mvn -q test jacoco:report
# coverage: build/reports/jacoco/test/jacocoTestReport.xml, counter LINE — ngưỡng backend 80%
```
Build/test đỏ → BLOCKER `type=test`, dẫn tên test + dòng lỗi. Coverage < 80% → BLOCKER.

## 4. Soi theo trục

`grep` chỉ để **tìm chỗ phải đọc** — mọi dòng dưới đây kết thúc bằng mở file ra đọc. Viết tắt:
`J` = `--include=*.java src/main`.

### Trục 1 — Đúng AC và BR

| Kiểm gì | Tìm ở đâu | Nặng |
|---|---|---|
| Mọi AC có code, gồm nhánh không-happy | Liệt kê AC trong FEAT → `grep -rn "AC-" J` (rules bắt comment `FEAT-N AC-M`); không có comment thì lần từ endpoint trong `api-{boundary}.md` xuống service | không thấy = BLOCKER · làm nửa = MAJOR |
| Mọi BR enforce ở service/domain, chạy **trước** khi ghi | `grep -rn "BR-" J` → mở chỗ check | BLOCKER |
| Ca xấu: không tồn tại · inactive · status đã final · request lặp · không sở hữu · tenant khác | Mở từng method service có ghi dữ liệu | MAJOR |
| Chuyển trạng thái hợp lệ; default đúng; không side effect ngoài ý | `grep -rn "setStatus(" J` → trước đó có kiểm trạng thái nguồn không | MAJOR |
| Ca biên `hld §6.1` (gửi hai lần · sửa đồng thời · xoá · sai thứ tự · hỏng nửa chừng · bản cũ · rỗng · thu hồi quyền) | Mỗi dòng không `n/a` → ràng buộc DB (`grep -rniE "unique" src/main/resources/db`), `@Version`, hoặc check ở service. Không tìm thấy = chưa xử | BLOCKER |

### Trục 2 — Bảo mật (6 nhóm)

| Nhóm | Kiểm gì | Tìm ở đâu | Nặng |
|---|---|---|---|
| Secret | Không secret trong code / yml / test | Lệnh (a) dưới bảng | BLOCKER — `suggested fix` ghi **xoay key**, không chỉ xoá commit |
| | Không log password/token/OTP/Authorization/PII/full body | `grep -rni -e "log\..*password" -e "log\..*token" -e "log\..*otp" -e "log\..*authorization" J` | token/password = BLOCKER · PII = MAJOR |
| Đầu vào | DTO có Bean Validation, controller có `@Valid` | `grep -rn "@RequestBody" J` → dòng nào thiếu `@Valid` | MAJOR |
| | Injection: không nối input vào JPQL/native; cột sort whitelist | `grep -rn -e createQuery -e createNativeQuery -e "nativeQuery = true" -e "Sort.by(" J` → tìm `+` ghép chuỗi, tên cột lấy từ request | BLOCKER |
| | Mass assignment: không bind body vào `@Entity`; mapper request→entity không map `id`/`role`/`tenantId`/`status`/`price` | `grep -rnE "@RequestBody +\w+Entity" J` + đọc `*Mapper` | BLOCKER |
| | Upload: giới hạn size, kiểm loại thật, tên do server sinh, lưu ngoài web root | `grep -rn "MultipartFile" J` · `grep -rn "max-file-size" src/main/resources` | MAJOR · path theo tên client = BLOCKER |
| | Deserialization, XXE, SSRF | `grep -rn -e ObjectInputStream -e activateDefaultTyping -e DocumentBuilderFactory -e SAXParserFactory -e XMLInputFactory -e "URI.create(" -e "new URL(" J` → parser tắt external entity? URL dựng từ input có allowlist? | BLOCKER |
| Danh tính & phân quyền | Không endpoint public ngoài ý | `grep -rn "permitAll" J` → mỗi path phải public theo `api-{boundary}.md` | BLOCKER |
| | Identity từ security context, không từ client | `grep -rn -e userId -e tenantId -e ownerId --include=*Request.java src/main` · `grep -rn -e "@RequestParam.*Id" -e "@PathVariable.*tenantId" -e "@RequestHeader.*tenantId" J` | BLOCKER |
| | Lấy bản ghi theo id kèm chủ sở hữu/tenant | `grep -rn -e "findById(" -e "getById(" -e "getReferenceById(" -e "findOne(" J` → trước khi trả/ghi có so owner/tenant với security context? | BLOCKER |
| | Mỗi ô `cấm` của ma trận vai × hành động có chỗ chặn **ở server** | Từng ô `cấm` liên quan boundary → tìm `@PreAuthorize`/check role ở endpoint hoặc service. Ẩn nút ở FE KHÔNG tính | BLOCKER |
| | Admin/internal endpoint: role rõ; internal dùng cơ chế đã duyệt (mTLS/internal JWT/gateway); token hết hạn, đăng xuất được | `SecurityConfig` + ADR auth | MAJOR |
| | Password BCrypt/Argon2; token/nonce `SecureRandom`; không tự chế crypto | `grep -rn -e MessageDigest -e MD5 -e SHA1 -e "SHA-1" -e "new Random(" J` | BLOCKER |
| Đường ra | Không lộ stack trace/SQL/message nội bộ | `grep -rn -e include-stacktrace -e include-message src/main/resources` · `grep -rn "getMessage()" --include=*Handler*.java src/main` | MAJOR |
| | CORS không `*` khi có credential; CSRF bật nếu cookie session; security headers | `grep -rn -e allowedOrigins -e allowedOriginPatterns -e "@CrossOrigin" -e csrf J` | BLOCKER |
| | Actuator/endpoint nhạy cảm không public | `grep -rn -A3 "exposure" src/main/resources` → `include: "*"` không auth = finding | MAJOR |
| | Rate limit: đăng nhập · đăng ký · quên mật khẩu · gửi OTP/email/SMS | `grep -rni -e login -e signin -e register -e signup -e otp -e forgot --include=*Controller.java src/main` → có rate limiter (theo ADR)? ADR không nói → QUESTION kèm cách kiểm | MAJOR |
| Dữ liệu | Response không thừa field nhạy cảm (hash, cờ nội bộ, dữ liệu người khác) | Mở từng `*Response` so với `api-{boundary}.md` | MAJOR |
| | Chỉ thu dữ liệu AC cần; PII mã hoá at-rest khi HLD yêu cầu; chỉ qua TLS | Cột trong migration so với AC — cột cá nhân không AC nào dùng = finding | MINOR · thiếu mã hoá khi yêu cầu = MAJOR |
| Phụ thuộc | Không lib có CVE nghiêm trọng; không thêm lib vì một hàm | Có plugin thì `./gradlew dependencyCheckAnalyze`; không có → đọc dependency mới trong `git diff <mốc>..HEAD -- build.gradle*` | MAJOR |

```bash
# (a) secret — dòng có ${...} là placeholder, bỏ qua
grep -rnE "(password|secret|api[_-]?key|token)\s*[:=]\s*[\"']?[A-Za-z0-9_/+=-]{8,}" src \
  --include=*.java --include=*.yml --include=*.yaml --include=*.properties | grep -v '\${'
```

### Trục 3 — Forbidden patterns

Mở `rules-backend` §Forbidden patterns, đi **TỪNG dòng** bảng. Mỗi dòng tìm được trong code → một
finding: `description` mở bằng `[rules-backend Forbidden: <cột Cấm>]`, `hậu quả thật` lấy từ cột
`Vì sao` (viết cụ thể cho chỗ này), `suggested fix` từ cột `Thay bằng`. Lệnh tìm cho các dòng chưa có ở trục 2:

```bash
grep -rnE "ddl-auto: *(update|create)" src/main/resources          # ddl-auto
git log --diff-filter=M --name-only --format= -- src/main/resources/db  # migration bị sửa: file có từ wave trước = BLOCKER
grep -rln "@Transactional" --include=*Controller.java src/main       # transaction ở controller
grep -rn "Repository" --include=*Controller.java src/main            # controller gọi repository
grep -rnE "catch *\([^)]*\) *\{ *\}" --include=*.java src/main       # catch rỗng
grep -rn -A4 "catch *(" --include=*Controller.java src/main | grep -E "ok\(|HttpStatus\.OK"   # catch rồi trả 200
grep -rn ").get()" --include=*.java src/main                         # Optional.get() trần
grep -rn -e "FetchType.LAZY" -e "@OneToMany" -e "@ManyToOne" --include=*.java src/main   # lazy: mapper có đọc sau khi service trả về?
grep -rn "findAll()" --include=*.java src/main                       # list không phân trang
grep -rln "@Data" --include=*Entity.java src/main                    # @Data trên entity
grep -rn -e "new RestTemplate" -e "WebClient.create" --include=*.java src/main
grep -rni -e h2database -e "jdbc:h2" build.gradle* src               # H2
```

### Trục 4 — Giao dịch, hợp đồng, idempotency, persistence, tích hợp

| Kiểm gì | Tìm ở đâu | Nặng |
|---|---|---|
| `@Transactional` ở service, phạm vi hẹp; chỉ đọc thì `readOnly = true` | `grep -rn "@Transactional" J` | MAJOR |
| Không gọi HTTP/downstream chậm trong transaction | Mở từng method `@Transactional`, tìm `*Client.` / `restClient` / `.send(` | MAJOR |
| Event/cache/index phụ thuộc DB đi **sau commit** hoặc qua outbox | `grep -rn -e "kafkaTemplate.send" -e "publishEvent(" -e "opsForValue()" J` → nằm trong transaction mà không `AFTER_COMMIT`/outbox | BLOCKER |
| Ghi nhiều bảng cần atomic nằm cùng transaction | Đọc service ghi ≥ 2 bảng | BLOCKER |
| Khớp `api-{boundary}.md`: path · method · field · enum · error code · HTTP status · pagination · sort/filter | So từng `@*Mapping` với spec | breaking không có yêu cầu = BLOCKER |
| Wave ≥ 2: surface trong `BC-LEDGER.md` §1 chỉ được THÊM, không đổi/xoá | `git diff <mốc wave trước>..HEAD` trên controller · DTO · migration · topic | BLOCKER |
| Request/Response là DTO, không Entity; list có phân trang; GET không đổi state | `grep -rn "Entity" --include=*Controller.java src/main` · đọc `@GetMapping` | BLOCKER · phân trang = MAJOR |
| Webhook · callback · consumer · job · retry · import · sync idempotent — dedup theo eventId/transactionId/idempotency key | `grep -rn -e "@KafkaListener" -e "@RabbitListener" -e "@Scheduled" -e webhook -e callback J` → mỗi chỗ tìm bảng inbox/unique key | luồng tiền/critical = BLOCKER · còn lại MAJOR |
| Event: payload DTO (không `Map`/entity) · topic/retry từ config · có eventId + correlationId · retry + DLQ · không giả định thứ tự · envelope khớp `events/{boundary}-events.md` (`ref-backend-kafka`) | Đọc producer/consumer | MAJOR |
| Không N+1 / repository trong vòng lặp / query không giới hạn; projection khi đủ, không eager thừa | `grep -rn -A4 -e "for (" -e ".forEach(" --include=*ServiceImpl.java src/main` → có gọi repository bên trong | MAJOR · không giới hạn trên bảng lớn = BLOCKER |
| Index cho cột filter/sort/join (không FK nên không tự có index) | So `findBy*`/`WHERE` với `CREATE INDEX` trong migration | MAJOR |
| Migration: file mới, NOT NULL mới có default/rollout an toàn, không FK | `grep -rni -e "foreign key" -e "references " src/main/resources/db` | MAJOR |
| Entity ↔ migration khớp tên/kiểu/nullable (`varchar(n)`↔`CHAR(n)`, `TIMESTAMPTZ`↔`Instant`) | Đọc song song entity và migration | BLOCKER |
| Không hardcode URL/timeout/retry/batch/topic/role/header; đúng chỗ: constant theo domain · yml · secret store · enum · i18n | `grep -rn -e "\"http://" -e "\"https://" -e "Duration.of" J` | MAJOR |
| Downstream: `@HttpExchange` · timeout + retry/fallback · 4xx→`BusinessException`, 5xx/timeout→`EXTERNAL_SERVICE_ERROR` · không return null · truyền Authorization/X-Tenant-ID/X-Correlation-ID · base URL/credential/flag cấu hình được (`ref-backend-restclient`) | Đọc `*Client` | MAJOR |
| Cache (`ref-backend-redis`): qua service interface, key có convention + TTL, invalidate sau ghi, không cache dữ liệu nhạy cảm, lock có timeout + release | `grep -rn -e RedisTemplate -e "@Cacheable" -e "@CacheEvict" -e RLock J` | MAJOR |
| Job: idempotent, lock khi nhiều instance, batching/phân trang, log tổng kết (start/end/duration/processed/success/failure), cấu hình ra ngoài | `grep -rn "@Scheduled" J` → có `@SchedulerLock`? | MAJOR |

### Trục 5 — Kiến trúc và quy ước

ArchUnit gác layer/package/cycle (`gradle test` chạy nó). Bạn soi thứ nó không bắt được.

| Kiểm gì | Tìm ở đâu | Nặng |
|---|---|---|
| `ArchitectureTest.java` tồn tại, rule khớp layout HLD §4 | `find src/test -name ArchitectureTest.java` → đọc rule | thiếu/rỗng = BLOCKER |
| Cấu trúc khớp HLD §4 + cây `ref-backend-pattern`: Layered HOẶC Hexagonal, không trộn, không package tự đặt | `find src/main/java -type d` so với cây trong skill | BLOCKER |
| Class đúng package; `@Entity` ở `entities/` (Hexagonal: `adapter/out/persistence/entities/`), tên `{Resource}Entity` | `grep -rl "@Entity" J` | MAJOR |
| Không package rỗng, không scaffold mẫu | `find src/main -type d -empty` · `find src -name "Example*" -o -name "Demo*" -o -name "Sample*" -o -name "HelloController*"` | thừa = MAJOR · mẫu lẫn code thật = BLOCKER |
| Đúng tầng: controller map + validate + gọi service interface · nghiệp vụ + transaction ở service · query ở repository · convert ở mapper · không nghiệp vụ trong controller/repository/mapper/config/migration | Đọc controller + mapper | MAJOR |
| Bean Validation cho input; nghiệp vụ + chuyển trạng thái validate ở service | Đọc DTO + service | MAJOR |
| Lỗi không lọt 500: exception map qua `GlobalExceptionHandler` → error code typed; input null/rỗng → 400 typed; catch phải log + ném lại/map | Lệnh trục 3 (catch, `.get()`) | BLOCKER |
| `rules-backend` §Coding checklist — đi từng dòng: interface/impl, inject interface · `@RequiredArgsConstructor` + `private final` · MapStruct · `Instant` đúng tầng · id/tenant boxed · Specification thay JPQL `(:x IS NULL OR …)`, không `nativeQuery` vô cớ · error code từ enum · `@ConfigurationProperties` · không FQCN/wildcard import · theo convention sẵn có, không tự thêm pattern | `grep -rn -e "@Autowired" -e "LoggerFactory.getLogger" -e "ServiceImpl " J` | MAJOR · FQCN = MINOR |
| Logging (`ref-backend-logging`): `@Slf4j`, JSON structured, MDC traceId/tenantId, mask PII, level đúng, log lỗi đủ ngữ cảnh, async/job có correlation | `grep -rn "MDC" J` | MAJOR |
| Config (`ref-backend-config`): `application.yml` + `application-{dev,sit,prod}.yml`; Dockerfile multi-stage `bootJar` | `ls src/main/resources/application*.yml Dockerfile` | MAJOR |
| Dễ bảo trì: method gọn, không lồng sâu, không nhân đôi logic nghiệp vụ, không dependency vô cớ | Chỉ ghi khi nói được hậu quả thật | MINOR |

### Trục 6 — Test

| Kiểm gì | Tìm ở đâu | Nặng |
|---|---|---|
| Ca đủ: success · validation fail · not found · permission denied · tenant khác · chuyển trạng thái sai · trùng/idempotency · external fail · publish event · rollback · biên | Đối chiếu `src/test` với AC + `hld §6.1` | MAJOR |
| Unit: given-when-then, tên `should_x_when_y`, assert hành vi + error code (không assert chi tiết cài đặt), mock đúng ranh giới (không mock class đang test), deterministic (Clock/seed), branch coverage có nghĩa | Đọc 2–3 test đại diện | MAJOR |
| Integration trên Testcontainers Postgres (không H2); contract API status + envelope; tenant isolation | `grep -rl -e PostgreSQLContainer -e "@Testcontainers" src/test` | MAJOR |
| **Schema drift**: ≥ 1 test boot Spring context + chạy migration + `ddl-auto: validate` | `grep -rn "ddl-auto" src/test/resources src/main/resources` + test `@SpringBootTest` dùng container | BLOCKER |
| Đổi logic có test mới; không xoá test có nghĩa; không test rỗng / chỉ `assertDoesNotThrow`; không `@Disabled` thiếu lý do | `grep -rn -e assertDoesNotThrow -e "@Disabled" src/test` · `git diff --stat <mốc>..HEAD -- src/test` | MAJOR |
| Diff chỉ trong `owned_paths` | `git diff --name-only <mốc>..HEAD` | BLOCKER |

### Trục 7 — Lệch thứ đã chốt

| Kiểm gì | Tìm ở đâu | Nặng |
|---|---|---|
| Code làm khác một dòng `tracking/decisions.md` mà không có dòng mới đè lên | Mỗi dòng liên quan boundary → tìm chỗ code tương ứng | MAJOR |
| Thư viện/kiểu kiến trúc khác ADR | Dependencies trong `build.gradle*` so với ADR tech-stack | MAJOR |
| Thuật ngữ lệch: FEAT/Glossary gọi "lịch hẹn" mà code chỗ `booking` chỗ `schedule` | `grep` tên class/bảng | MINOR |
| TODO/FIXME chặn một AC; code chết để dạng comment | `grep -rn -e TODO -e FIXME -e HACK J` | chặn AC = MAJOR |

## 5. Ghi finding

Append/cập nhật `tracking/{wave}/review-findings.md` theo `TEMPLATE.review-findings.md`, một row một finding:

```
| RF-NNN | severity | open | {boundary} | path:dòng | type | [nguồn] vấn đề | hậu quả thật | suggested fix |
```

- `[nguồn]`: `[FEAT-X AC-2]` · `[BR-...]` · `[Bảo mật: <nhóm>]` · `[rules-backend Forbidden: <cột Cấm>]` · `[hld §6.1 <ca>]` · `[decisions <ngày>]`.
- **BLOCKER** — sai nghiệp vụ · lủng bảo mật/tenant · hỏng dữ liệu/transaction · phá hợp đồng không có yêu
  cầu · thiếu idempotency ở luồng tiền · secret · sửa migration đã chạy · query không giới hạn.
  **MAJOR** — nên sửa trước bàn giao. **MINOR/NIT** — không chặn. **QUESTION** — chưa chắc.
  Ý thích cá nhân không bao giờ là BLOCKER.
- Row `resolved` vòng trước: mở đúng `file:dòng` xác nhận; còn lỗi → đặt lại `open` + ghi vì sao. KHÔNG xoá row.
- Ít thời gian thì theo thứ tự: AC/BR → bảo mật & tenant → giao dịch/dữ liệu → hợp đồng → idempotency →
  hiệu năng query → config/secret → test → dễ đọc.

## 6. Bốn luật cho mọi finding

1. **Hậu quả thật** — chuyện gì xảy ra với người dùng thật: mất dữ liệu · lộ dữ liệu · sai kết quả · AC
   không chạy · wave trước gãy. Viết không nổi câu này thì không phải finding.
2. **Trục sạch thì nói sạch** — ghi thẳng "trục N sạch" trong phần trả về; đừng bịa nhận xét cho có.
3. **Mở file ra đọc** — `file:dòng` phải là dòng đã đọc thật; không suy từ tên hàm.
4. **Không chắc → `QUESTION`**, cột `suggested fix` ghi **cách kiểm chứng** (vd "gọi API bằng token A với
   id bản ghi của B, xem có trả 200 không").

Không góp ý: đặt tên cho đẹp · tách file cho gọn · trừu tượng hoá "để sau dễ mở rộng" · tối ưu khi chưa có số đo.

## 7. Kết luận

- `review_result = pass` chỉ khi: không còn row BLOCKER/MAJOR `open` của boundary · build/test xanh · coverage ≥ 80%.
- Không spawn fix, không tự loop — phiên chính đọc findings, spawn fix, rồi gọi bạn re-review. Gate
  `no_open_findings` chặn complete.
- Field JSON trả về theo prompt spawn (`build_prompt.py`) — skill không định nghĩa schema.
