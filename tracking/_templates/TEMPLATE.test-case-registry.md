# Test Case Registry — wave-{N}

> Wave: wave-{N} ({wave-title}) · Features: FEAT-001, FEAT-002, … · Boundaries: {boundary-list} · Created by: test-plan-agent
>
> **Mỗi TC = 1 HÀNG.** **Registry tích luỹ qua wave** — TC wave trước GIỮ NGUYÊN; wave mới reuse (note `reuse W{prev}`) hoặc thêm. Trước khi thêm TC mới: DEDUPE-check (cùng `feature`+`group`, steps tương tự) → reuse > create.
> `type`: `auto` (test-execute chạy) | `manual` (UAT/QA). `group` = test_type bản chất. `pri`: P0 (blocker) | P1 (must) | P2 (nice).
> `AC` = `FEAT-N:AC-M` (mọi TC trace ≥1 AC, trừ smoke infra). `BR` = `BR-N` nếu TC enforce 1 business rule (optional). `tags` ≥1 `@FEAT-<id>` + ≥1 suite tag.
> Steps/Expected/test-data giữ ngắn 1 cell (chi tiết dài → UAT script / automation riêng). test-execute parse cột `type=auto` để chạy.
> Khi `/apply-cr` đổi AC: TC bị ảnh hưởng → `note: STALE` (re-author) hoặc `note: remap W{cr}` (refine nhỏ). Coverage matrix re-verify sau remap.
> Quy tắc gán `pri` + `group`(test_type) enum + tag taxonomy: xem `docs/architecture/SEVERITY-TEST-TAXONOMY.md` §3-§5.
> **Deferred:** AC/feature đã hoãn ở `## Deferred to later waves` của `wave-{N}.md` → TC đánh tag `@deferred` + `note: deferred wave-N` → test-execute `skip(deferred)`, không log bug, không tính fail. Tag chỉ hiệu lực khi wave plan khai báo (chống né test).

| TC | group | type | boundary | feature | AC | BR | pri | pre-condition | test-data | steps | expected | tags | note |
|----|-------|------|----------|---------|----|----|-----|---------------|-----------|-------|----------|------|------|
| TC-S01 | smoke | auto | all | infra | N/A | — | P0 | compose up, services healthy | — | `curl /health` | 200 `{status:ok}` | @smoke | |
| TC-S02 | smoke | auto | auth | FEAT-001 | AC-1 | — | P0 | auth up + seed user | valid creds | POST `/v1/auth/login` | 200 + `access_token` | @smoke @FEAT-001 @critical-path | |
| TC-I01 | integration | auto | {boundary} | FEAT-{N} | AC-1 | — | P1 | token (TC-S02), tenant in DB | valid body | POST `/v1/{res}` → GET `/{id}` | 201 + id; GET same entity | @FEAT-{N} @happy-path @boundary:{b} | |
| TC-I02 | integration | auto | {boundary} | FEAT-{N} | AC-2 | BR-{N} | P1 | — | missing required field | POST thiếu required field | 400 `VALIDATION_ERROR` | @FEAT-{N} @edge-case @BR-{N} | |
| TC-I03 | security | auto | {boundary} | FEAT-{N} | AC-3 | — | P0 | — | no token | POST không Authorization header | 401 `UNAUTHORIZED` | @FEAT-{N} @edge-case | |
| TC-I04 | security | auto | {boundary} | FEAT-{N} | AC-x | BR-{N} | P0 | tenant khác | tenant-B id | GET resource của tenant khác | 403/404 (no cross-tenant leak) | @FEAT-{N} @edge-case @boundary:{b} | tenant isolation |
| TC-E01 | e2e | auto | fe-{name} | FEAT-{N} | AC-M | — | P1 | login | seed list | login → /resource → create → submit → verify list | item visible + screenshot | @FEAT-{N} @critical-path @platform:web | playwright |
| TC-E02 | e2e | manual | fe-{name} | FEAT-{N} | AC-M | — | P2 | — | sample doc | open detail → print → preview | PDF render đúng layout | @FEAT-{N} @manual | |
| TC-M01 | uat | manual | cross-cutting | FEAT-{N} | AC-M | — | P1 | stakeholder role | business data | execute business flow (UAT script) | stakeholder confirm OK | @FEAT-{N} @manual | verifier=stakeholder |
| TC-M02 | uat | manual | {boundary} | FEAT-{N} | AC-M | — | P2 | — | max/min value | input boundary value (max/min) | handle gracefully, no crash | @FEAT-{N} @edge-case @manual | verifier=QA |
| TC-R01 | regression | auto | {boundary} | regression | — | — | P0 | — | bug repro data | re-run bug scenario | không tái phát | @regression | ref_bug=BUG-{NNN} |
| TC-D01 | security | auto | {boundary} | FEAT-{N} | AC-x | — | P2 | — | no/invalid token | endpoint cần auth (auth hoãn wave sau) | 401 (khi auth bật) | @FEAT-{N} @deferred | deferred wave-2 (auth out-of-scope wave này) |

## Coverage matrix (AC → TC) — chứng minh traceability 2 chiều

| FEAT:AC | required? | TCs covering | auto | manual |
|---------|-----------|--------------|------|--------|
| FEAT-001:AC-1 | Must | TC-S02, TC-I01 | 2 | 0 |
| FEAT-001:AC-2 | Must | TC-I02 | 1 | 0 |
| FEAT-001:AC-3 | Must | TC-I03 | 1 | 0 |
| FEAT-002:AC-1 | Must | TC-E01, TC-M01 | 1 | 1 |
| … | … | … | … | … |

**Total**: {N} TC ({auto} auto, {manual} manual). AC coverage: 100% (mọi AC `Must` ≥1 TC — không AC mồ côi; mọi TC trace đúng AC — không TC mồ côi).
