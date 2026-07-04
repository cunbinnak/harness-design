---
name: dev-handoff
description: "Dựng wave services chạy THẬT (docker up + content-validated proof) cho test agent."
when_state: ['REVIEW_DEV']
sets_stage: DEV_HANDOFF
spawn:
  agent: "dev-handoff-agent"
  skills: [infra-local-dev]
gates: [{type: all_boundaries_reviewed}, {type: infra_proof}, {type: health_proof}, {type: code_compliance}, {type: web_styling}, {type: api_contract_proof}]
---

# /dev-handoff

## Mục đích

Đưa **MỌI wave service lên chạy THẬT** để test agent dùng được local. dev-handoff = **INFRA-ONLY**: chỉ sửa `docs/architecture/infra/docker-compose.yml`; **`services/{boundary}/**` (Dockerfile/src/config/migration) là READ-ONLY** — lỗi code làm container chết → STOP + fix-agent, KHÔNG tự vá (hook chặn dev-handoff-agent sửa `services/`).

1. Mỗi wave boundary PHẢI có **Dockerfile** (do **dev scaffold** — gate `code_compliance`; backend multi-stage Gradle `bootJar`→JRE). **dev-handoff KHÔNG tạo/sửa Dockerfile** (đó là deliverable boundary). Thiếu/sai → STOP + `fix-{boundary}-agent`.
2. Reconcile **`docs/architecture/infra/docker-compose.yml`** (infra dùng chung — file DUY NHẤT dev-handoff được sửa): env khớp cái app đọc (vd `SPRING_DATASOURCE_URL`), bỏ `depends_on` service chưa có ở wave, web `VITE_*` qua **build arg**.
3. `docker compose up -d --build <wave services>` → đợi healthy.
4. **MAIN chạy `py scripts/capture_infra_proof.py`** → `tracking/wave-{N}/docker-ps.json` (infra_proof) + `health-proof.json` (curl /health/ready) + `api-proof.json` (fetch OpenAPI runtime `/v3/api-docs` mỗi backend — gate `api_contract_proof`). Service chưa UP → exit !=0.
5. **Service chưa healthy → `docker compose logs <svc>` chẩn ROOT-CAUSE → phân loại:** (a) lỗi **compose/env** → sửa docker-compose.yml + up lại; (b) lỗi **code/migration/config/Dockerfile trong `services/{boundary}/`** (vd tên cột/kiểu cột migration sai, thiếu HealthController, healthcheck dùng curl mà image không có) → **STOP, KHÔNG tự sửa**, báo MAIN spawn **`fix-{boundary}-agent` (Mode B)** kèm root-cause → fix → re-run `/dev-handoff`. (Lỗi schema lẽ ra đã bị bắt ở DEV qua integration-test Testcontainers `ddl-auto: validate` — xem rules/review-backend.)

## Gates

### `all_boundaries_reviewed` (wave-scoped)
Đọc `STATE.review_results` (set bởi `/review-dev`): **MỌI** boundary trong wave phải `review_result=pass` + `coverage_pct` đạt ngưỡng theo `kind`:

| kind | ngưỡng |
|---|---|
| backend | 80% |
| bff | 70% |
| web / mobile | 60% |

> **Coverage KHÔNG tin số tự khai:** service đã scaffold → harness **derive từ coverage report thật** (jacoco XML `build/reports/jacoco/**` / `coverage/coverage-summary.json` / `coverage/lcov.info`) — có report thì số đo THẮNG số khai; scaffold rồi mà không có report → fail (chạy test kèm coverage rồi `/review-dev` lại). Chưa scaffold → fallback số khai (hermetic).
>
> `review-dev` đã ép kèm `review_results` (gate `non_empty`) nên STATE không rỗng. **force-bypass:** `dev-handoff` `force:true,reason` bypass được gate này (đồng bộ họ force-bypass, audit decisions.md) — lưới an toàn env/edge.

### `infra_proof` (content-validated — KHÔNG chỉ file tồn tại)
`scripts/gates.py check_infra_proof` parse `tracking/wave-{N}/docker-ps.json` → **MỌI** boundary trong `wave_boundaries` phải có container `State=running` (và `Health != unhealthy`). Compose `Service` field == `boundary_id`.

> Vì sao 2 lớp: trước đây gate chỉ check `proof.is_file()` → up tạm Postgres/Redis rồi capture file là PASS dù service chính chưa lên. Giờ content-validated → service PHẢI chạy thật mới qua handoff. Env không có Docker → `force:true,reason` (audit `decisions.md`).

> `infra_proof` lặp lại ở `/test-plan` (re-verify service vẫn UP khi sang test).

### `health_proof` (app-readiness — HARNESS đo, không agent tự khai)
`scripts/gates.py check_health_proof` parse `tracking/wave-{N}/health-proof.json` (do `capture_infra_proof.py` curl `/health/ready` từng wave service): **MỌI** boundary phải có 1 probe ok (http 2xx/3xx). Khác `infra_proof` (chỉ container `State=running` từ file agent ghi) — `State=running` chưa chứng minh app đã UP (Spring còn `503` lúc khởi động; compose không khai healthcheck → `Health=''` vẫn lọt). Lớp này chứng minh app **thực sự trả lời**. Env không Docker → `force:true,reason` (audit).

### `code_compliance` (content-validated — backend, đối xứng web_styling)
`scripts/gates.py check_code_compliance`: mỗi **backend** boundary đã scaffold phải (a) có `Dockerfile`; (b) build file KHÔNG khai H2 (`com.h2database`); (c) `application.{yml,yaml,properties}` (kể cả profile) KHÔNG `jdbc:h2:` và KHÔNG `ddl-auto: create-drop`; (d) có **base `application.yml`** + **≥1 file profile `application-<dev|sit|prod>.{yml,properties}`** (theo `ref-backend-config`: mỗi env 1 file, không chỉ base + env var — chống config thiếu profile). Bắt chuỗi defect "test xanh nhờ H2" + "dev done ≠ runnable" (thiếu Dockerfile) + "config thiếu profile". Env-block → `force:true,reason` (audit).

### `web_styling` (content-validated — chặn FE unstyled + lệch design token)
`scripts/gates.py check_web_styling`: mỗi web boundary trong wave:
1. dùng `className=` mà KHÔNG có cơ chế styling nào (0 file `.css/.scss`, không tailwind, không CSS-in-JS) → **FAIL** (FE unstyled, render không màu/layout).
2. Style bằng **plain CSS** (không tailwind/CSS-in-JS) mà KHÔNG dùng design token `var(--...)` → **FAIL** (hardcode hex/px, lệch `docs/architecture/ux/design-tokens.css`). Tailwind/CSS-in-JS có cơ chế token riêng → miễn.
3. Dùng `var(--...)` mà token KHÔNG được **định nghĩa/import** trong bundle (không copy `design-tokens.css` vào src, không `@import`, không `:root{--...}`) → **FAIL** (var resolve rỗng → UI vẫn unstyled dù "dùng token").

Bắt đúng defect "FE thiếu CSS / bịa style rời design system" — lỗi mà test (query role/text) + review tĩnh đều mù. Env-block → `force:true,reason` (audit). Reviewer cũng verify (skill `review-web` §6 Design fidelity = BLOCKER).

### `api_contract_proof` (contract ↔ implementation — HARNESS đo)
`scripts/gates.py check_api_contract_proof`: mỗi **backend** boundary trong wave có `api-{b}.md` với endpoint REST khai (`Method · Path`) → endpoint đó PHẢI tồn tại trong runtime OpenAPI (`tracking/wave-{N}/api-proof.json`, do `capture_infra_proof.py` fetch `/v3/api-docs`). Path param normalize (`{id}` vs `{appointmentId}` vẫn khớp). Bắt **contract drift** (endpoint thiếu/rename) TRƯỚC khi test — gốc BUG-006. Boundary không có api doc / không endpoint REST (GraphQL) → miễn. Backend phải bật springdoc (xem `ref-backend-config`). Env-block → `force:true,reason` (audit).

## Build prompt + spawn

```bash
py scripts/build_prompt.py dev-handoff --boundary order-management
# Sau khi đã up + capture docker-ps.json:
py scripts/harness.py dev-handoff complete '{"coverage_pct": 85, "review_result": "pass", "docker_compose_ok": true, "connectivity_ok": true}'
```

