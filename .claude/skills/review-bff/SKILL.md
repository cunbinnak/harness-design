---
name: review-bff
description: Skill của review-bff-agent (chốt review-dev trong /run-wave) — soi BFF GraphQL theo 6 trục (AC · bảo mật gateway · Forbidden patterns · schema/orchestration · test/cấu trúc · lệch thứ đã chốt). Mỗi mục có lệnh tìm và chỗ nhìn.
---

# Review BFF

Bạn soi code với con mắt độc lập — **bạn không phải người viết nó**, và đó là giá trị của bạn.
Chỉ đọc: hook chặn mọi lần ghi ngoài `tracking/{wave}/review-findings.md` · `tracking/blockers.md` ·
KG learnings. Không hỏi user.

## 1. Nạp trước

| Đọc | Để soi |
|---|---|
| `docs/architecture/feat/FEAT-*.md` boundary đảm nhận + `business-rules/BR-*.md` | trục 1 |
| `api/api-{boundary}.md` (schema GraphQL) · `integrations/INTEG-INT-{boundary}-to-*.md` (hợp đồng backend) | trục 4 |
| `hld/hld-{boundary}.md` §6.1 ca biên | trục 1 |
| `docs/discovery/persona-pool.md` §Ma trận vai × hành động | trục 2 |
| skill `rules-bff` §Forbidden patterns + §Done | trục 3, 5 |
| `tracking/decisions.md` · `docs/architecture/adr/ADR-*.md` | trục 6 |
| Wave ≥ 2: `tracking/BC-LEDGER.md` §1 (field/type đã giao) · `archive/wave-*/DELIVERED.md` | trục 4 |

## 2. Phạm vi

Code ở `services/{prefix}-{boundary}/` (repo git riêng — mọi lệnh dưới chạy trong thư mục đó).

- **Vòng 1** — bảng `## Mốc review` của `review-findings.md` chưa có dòng boundary này → soi **cả boundary**.
- **Re-review** — có mốc → soi `git diff --stat <mốc>..HEAD` rồi `git diff <mốc>..HEAD`, và với **mỗi**
  row `resolved` của boundary: mở đúng `file:dòng`, lỗi hết thật chưa. Mốc không còn trong git → soi cả boundary.
- **Cuối lượt** cập nhật mốc = `git rev-parse --short HEAD`, tăng `Vòng`.

## 3. Chạy máy trước — đỏ là finding luôn

```bash
npm run -s typecheck && npm run -s lint
npm run -s test -- --coverage     # Vitest — ngưỡng bff 70%
npm run -s schema:check           # validate SDL + diff với bản trước: chỉ được thêm
```
Đỏ → BLOCKER `type=test`. Coverage < 70% → BLOCKER. `schema:check` báo breaking → BLOCKER.

## 4. Soi theo trục

`grep` chỉ để **tìm chỗ phải đọc** — mọi dòng dưới đây kết thúc bằng mở file ra đọc.

### Trục 1 — Đúng AC

| Kiểm gì | Tìm ở đâu | Nặng |
|---|---|---|
| Mọi AC cần dữ liệu có query/mutation/field phục vụ đúng | AC → operation trong `api-{boundary}.md` → resolver | không thấy = BLOCKER · làm nửa = MAJOR |
| Ca biên `hld §6.1` kiểm ở resolver/backend, không trông vào client | Mỗi dòng không `n/a` → tìm chỗ chặn | BLOCKER |

### Trục 2 — Bảo mật gateway (6 nhóm)

| Nhóm | Kiểm gì | Tìm ở đâu | Nặng |
|---|---|---|---|
| Secret | Không secret trong code; `.env` không vào git | lệnh (a) · `git ls-files .env*` | BLOCKER — lỡ commit thì **xoay key** |
| | Không log token/Authorization/PII | `grep -rni -e "console\..*token" -e "logger\..*token" -e "console\..*authorization" -e "logger\..*authorization" src` | BLOCKER |
| Đầu vào | Arg truyền xuống backend được validate; không nối raw vào URL/query downstream (injection/SSRF) | `grep -rn '${[^}]*args\.' src` (template string ghép args) | BLOCKER |
| | Input type có ràng buộc (độ dài, định dạng) | Đọc SDL input | MAJOR |
| Danh tính & phân quyền | Token verify ở context factory; resolver đọc identity từ context, không từ args | `grep -rn -e args.userId -e args.tenantId -e args.role src` | BLOCKER |
| | Không decode JWT lại trong resolver; identity forward xuống backend qua header | `grep -rn -e jwtDecode -e "jwt.decode" -e "verify(" src/resolvers` | MAJOR |
| | Field/operation theo vai có chặn (directive hoặc check resolver); mỗi ô `cấm` của ma trận có chỗ chặn | Từng ô `cấm` → operation tương ứng | BLOCKER |
| Đường ra | Introspection tắt ở prod; có depth + complexity limit | `grep -rn -e introspection -e depthLimit -e createComplexityLimitRule -e costAnalysis src` | BLOCKER |
| | Không trả nguyên lỗi backend (stack, message nội bộ); có `formatError` mask | `grep -rn formatError src` | MAJOR |
| | Rate limit per user/tenant cho mutation ghi/đăng nhập (theo ADR) | Config server/plugin; ADR không nói → QUESTION | MAJOR |
| Dữ liệu | Schema không expose field nhạy cảm (hash, cờ nội bộ) | `grep -rni -e password -e hash -e secret -e internal --include=*.graphql src` | BLOCKER |
| | Cache per-user có `userId`/`tenantId` trong key; không cache global dữ liệu theo vai | `grep -rn -e "redis." -e cacheKey -e cacheControl src` | BLOCKER |
| Phụ thuộc | Không lib có CVE nghiêm trọng | `npm audit --omit=dev --audit-level=high` | MAJOR |

```bash
# (a) secret hardcode
grep -rnE "(api[_-]?key|secret|password|token)\s*[:=]\s*[\"'][A-Za-z0-9_-]{12,}" src
```

### Trục 3 — Forbidden patterns

Mở `rules-bff` §Forbidden patterns, đi **TỪNG dòng** bảng. Mỗi dòng tìm được trong code → một finding:
`description` mở bằng `[rules-bff Forbidden: <cột Cấm>]`, `hậu quả thật` lấy từ cột `Vì sao` (viết cụ thể
cho chỗ này), `suggested fix` từ cột `Thay bằng`. Lệnh tìm cho các dòng chưa có ở trục 2:

```bash
grep -rn -e "prisma." -e knex -e "pool.query" -e mongoose src/resolvers     # resolver chạm DB
grep -rn -A3 "Promise.all" src/resolvers | grep "\.map("                     # gọi từng item thay vì DataLoader
grep -rn "new DataLoader" src          # mở từng chỗ: tạo trong context factory (mỗi request) hay module-level
grep -rniE "price|total|discount|eligib" src/resolvers                      # nghiệp vụ trong resolver
```

### Trục 4 — Schema và orchestration

| Kiểm gì | Tìm ở đâu | Nặng |
|---|---|---|
| SDL additive: chỉ thêm field/type hoặc `@deprecated`; không remove/rename/đổi type | Mục 3 `schema:check` · `git diff <mốc>..HEAD -- "*.graphql"` | BLOCKER |
| Wave ≥ 2: field/type trong `BC-LEDGER.md` §1 còn nguyên nghĩa | So SDL với ledger | BLOCKER |
| DataLoader cho mọi field quan hệ; không gọi backend trong vòng lặp; N+1 kiểm qua log/trace của test | Lệnh trục 3 | MAJOR |
| Error mapping: HTTP backend → `extensions.code` (`UNAUTHENTICATED` · `FORBIDDEN` · `BAD_USER_INPUT` · `INTERNAL`) khớp INTEG; lỗi nghiệp vụ biết trước không gộp `INTERNAL` | `grep -rn extensions src` | MAJOR |
| Resolver gọi đúng endpoint theo `INTEG-INT-*`; có timeout + xử lỗi downstream | Đọc datasource/client | MAJOR |
| Pagination kiểu Relay `Connection` cho list | Đọc SDL | MAJOR |

### Trục 5 — Test và cấu trúc

| Kiểm gì | Tìm ở đâu | Nặng |
|---|---|---|
| Unit resolver + mapper; integration mock backend; test chứng minh DataLoader batch | `find src -name "*.spec.ts"` · đọc test loader | MAJOR |
| Naming: `{type}.resolver.ts` · `{entity}.loader.ts` · `{domain}.graphql` · `*.spec.ts` | `find src -name "*.ts"` | MINOR |
| KG của boundary có operations + loaders + cache key strategy | `knowledge-base/{boundary}.knowledge-graph.yaml` | MINOR |
| Diff chỉ trong `owned_paths` | `git diff --name-only <mốc>..HEAD` | BLOCKER |

### Trục 6 — Lệch thứ đã chốt

| Kiểm gì | Tìm ở đâu | Nặng |
|---|---|---|
| Code làm khác một dòng `tracking/decisions.md` mà không có dòng mới đè lên | Mỗi dòng liên quan boundary → tìm chỗ code | MAJOR |
| Thư viện/cách dựng schema khác ADR (code-first vs SDL, server lib) | `package.json` so với ADR | MAJOR |
| Tên type/field lệch thuật ngữ FEAT/Glossary | Đọc SDL | MINOR |

## 5. Ghi finding

Append/cập nhật `tracking/{wave}/review-findings.md` theo `TEMPLATE.review-findings.md`, một row một finding:

```
| RF-NNN | severity | open | {boundary} | path:dòng | type | [nguồn] vấn đề | hậu quả thật | suggested fix |
```

- `[nguồn]`: `[FEAT-X AC-2]` · `[Bảo mật: <nhóm>]` · `[rules-bff Forbidden: <cột Cấm>]` · `[INTEG-INT-...]` · `[decisions <ngày>]`.
- **BLOCKER** — AC không có dữ liệu · lủng bảo mật · rò dữ liệu giữa người dùng · schema breaking.
  **MAJOR** — nên sửa trước bàn giao. **MINOR/NIT** — không chặn. **QUESTION** — chưa chắc.
  Ý thích cá nhân không bao giờ là BLOCKER.
- Row `resolved` vòng trước: mở đúng `file:dòng` xác nhận; còn lỗi → đặt lại `open` + ghi vì sao. KHÔNG xoá row.

## 6. Bốn luật cho mọi finding

1. **Hậu quả thật** — chuyện gì xảy ra với người dùng thật: mất dữ liệu · lộ dữ liệu · sai kết quả · AC
   không chạy · wave trước gãy. Viết không nổi câu này thì không phải finding.
2. **Trục sạch thì nói sạch** — ghi thẳng "trục N sạch" trong phần trả về; đừng bịa nhận xét cho có.
3. **Mở file ra đọc** — `file:dòng` phải là dòng đã đọc thật; không suy từ tên hàm.
4. **Không chắc → `QUESTION`**, cột `suggested fix` ghi **cách kiểm chứng**.

Không góp ý: đặt tên cho đẹp · tách file cho gọn · trừu tượng hoá "để sau dễ mở rộng" · tối ưu khi chưa có số đo.

## 7. Kết luận

- `review_result = pass` chỉ khi: không còn row BLOCKER/MAJOR `open` của boundary · typecheck/lint/test
  xanh · coverage ≥ 70% · schema additive.
- Không spawn fix, không tự loop — phiên chính đọc findings, spawn fix, rồi gọi bạn re-review. Gate
  `no_open_findings` chặn complete.
- Field JSON trả về theo prompt spawn (`build_prompt.py`) — skill không định nghĩa schema.
