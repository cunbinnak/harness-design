---
name: dev-handoff
description: "Dựng wave services chạy THẬT (docker up + content-validated proof) cho test agent."
when_state: ['REVIEW_DEV']
sets_stage: DEV_HANDOFF
spawn:
  agent: "dev-handoff-agent"
  skills: [infra-local-dev]
gates: [{type: all_boundaries_reviewed}, {type: infra_proof}, {type: health_proof}, {type: code_compliance}, {type: web_styling}]
---

# /dev-handoff

## Mục đích

Đưa **MỌI wave service lên chạy THẬT** để test agent dùng được local. Việc cần làm (agent dev-handoff):

1. Mỗi wave boundary có **Dockerfile** (backend: multi-stage maven→JRE; web: node build→nginx). Thiếu → tạo.
2. Reconcile `docs/architecture/infra/docker-compose.yml` cho wave hiện tại: env khớp cái app THỰC SỰ đọc (vd `SPRING_DATASOURCE_URL`), bỏ `depends_on` các service chưa có code ở wave này (vd kafka/boundary wave sau), web truyền `VITE_*` qua **build arg** (Vite inline lúc build, KHÔNG phải runtime env).
3. `docker compose up -d --build <wave services>` → đợi healthy.
4. **MAIN chạy `py scripts/capture_infra_proof.py`** (HARNESS đo, KHÔNG agent tự ghi) → sinh `tracking/wave-{N}/docker-ps.json` (infra_proof) + `tracking/wave-{N}/health-proof.json` (health_proof: curl /health/ready mỗi wave service). Service chưa UP → script exit !=0 → STOP, sửa rồi chạy lại.

## Gates

### `all_boundaries_reviewed` (wave-scoped)
Đọc `STATE.review_results` (set bởi `/review-dev`): **MỌI** boundary trong wave phải `review_result=pass` + `coverage_pct` đạt ngưỡng theo `kind`:

| kind | ngưỡng |
|---|---|
| backend | 80% |
| bff | 70% |
| web / mobile | 60% |

### `infra_proof` (content-validated — KHÔNG chỉ file tồn tại)
`scripts/gates.py check_infra_proof` parse `tracking/wave-{N}/docker-ps.json` → **MỌI** boundary trong `wave_boundaries` phải có container `State=running` (và `Health != unhealthy`). Compose `Service` field == `boundary_id`.

> Vì sao 2 lớp: trước đây gate chỉ check `proof.is_file()` → up tạm Postgres/Redis rồi capture file là PASS dù service chính chưa lên. Giờ content-validated → service PHẢI chạy thật mới qua handoff. Env không có Docker → `force:true,reason` (audit `decisions.md`).

> `infra_proof` lặp lại ở `/test-plan` (re-verify service vẫn UP khi sang test).

### `health_proof` (app-readiness — HARNESS đo, không agent tự khai)
`scripts/gates.py check_health_proof` parse `tracking/wave-{N}/health-proof.json` (do `capture_infra_proof.py` curl `/health/ready` từng wave service): **MỌI** boundary phải có 1 probe ok (http 2xx/3xx). Khác `infra_proof` (chỉ container `State=running` từ file agent ghi) — `State=running` chưa chứng minh app đã UP (Spring còn `503` lúc khởi động; compose không khai healthcheck → `Health=''` vẫn lọt). Lớp này chứng minh app **thực sự trả lời**. Env không Docker → `force:true,reason` (audit).

### `code_compliance` (content-validated — backend, đối xứng web_styling)
`scripts/gates.py check_code_compliance`: mỗi **backend** boundary đã scaffold phải (a) có `Dockerfile`; (b) build file KHÔNG khai H2 (`com.h2database`); (c) `application.{yml,yaml,properties}` (kể cả profile) KHÔNG `jdbc:h2:` và KHÔNG `ddl-auto: create-drop`; (d) có ≥1 file config. Bắt đúng chuỗi defect "test xanh nhờ H2" che bug prod (flyway-postgres thiếu, TIMESTAMP vs TIMESTAMPTZ) + "dev done ≠ runnable" (thiếu Dockerfile). Env-block → `force:true,reason` (audit).

### `web_styling` (content-validated — chặn FE unstyled + lệch design token)
`scripts/gates.py check_web_styling`: mỗi web boundary trong wave:
1. dùng `className=` mà KHÔNG có cơ chế styling nào (0 file `.css/.scss`, không tailwind, không CSS-in-JS) → **FAIL** (FE unstyled, render không màu/layout).
2. **(G15)** style bằng **plain CSS** (không tailwind/CSS-in-JS) mà KHÔNG dùng design token `var(--...)` → **FAIL** (hardcode hex/px, lệch `docs/architecture/ux/design-tokens.css`). Tailwind/CSS-in-JS có cơ chế token riêng → miễn.

Bắt đúng defect "FE thiếu CSS / bịa style rời design system" — lỗi mà test (query role/text) + review tĩnh đều mù. Env-block → `force:true,reason` (audit). Reviewer cũng verify (skill `review-web` §6 Design fidelity = BLOCKER).

## Build prompt + spawn

```bash
py scripts/build_prompt.py dev-handoff --boundary order-management
# Sau khi đã up + capture docker-ps.json:
py scripts/harness.py dev-handoff complete '{"coverage_pct": 85, "review_result": "pass", "docker_compose_ok": true, "connectivity_ok": true}'
```

