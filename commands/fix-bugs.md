# fix-bugs — STRICT REPRODUCE → FIX → VERIFY cycle

Sửa bug — spawn `agents/fix-{boundary}-agent.md` (role `fix:backend` hoặc `fix:frontend`).

## CỐT LÕI: 3-step cycle (KHÔNG fix đại)

Mỗi bug PHẢI qua 3 bước, có proof từng bước:

```
1. REPRODUCE — chạy failing TC, xác nhận bug tồn tại
2. FIX       — sửa code (chỉ owned_paths)
3. VERIFY    — chạy lại TC, xác nhận pass + regression boundary
```

**KHÔNG được skip bước 1 hay bước 3.** Hook gate check artifacts:
- `tracking/waves/{wave-id}/bugs/BUG-XXX.md` phải có `reproduced_at` + `fixed_at` + `verified_at` timestamps
- Status flow: `open → reproduced → fixed → verified`

## Pre-condition

- Stage: `BUG_LOGGING` (sau test-execute fail) hoặc `MANUAL_TEST` (sau UAT fail)
- Bug ticket tồn tại trong `tracking/waves/{wave-id}/bugs/`
- `requires_previous_any`: `test-execute`, `retest`, `end-wave`

## Slash

```bash
py scripts/build_command_prompt.py fix-bugs --boundary order
```

DOCS IN SCOPE auto-inject (role `fix:backend` hoặc `fix:frontend`):
- `tracking/waves/{wave-id}/bugs/**` (bug tickets — đọc ALL open bugs cho boundary)
- `tracking/waves/{wave-id}/test-logs/**` (log từ test-execute — biết TC nào fail thế nào)
- `services/{boundary}/**` (source code cần sửa)
- `docs/architecture/hld/hld-{boundary}.md` (BE) hoặc `ux-{boundary}.md` (FE)
- `docs/architecture/api/api-{boundary}.md`
- `knowledge-base/{boundary}.knowledge-graph.yaml`

## Quy trình bắt buộc trong agent

### Step 1 — REPRODUCE (xác nhận bug)

```bash
# Đọc bug ticket
BUG_ID="BUG-001"
TC_ID=$(grep "related_tc:" tracking/waves/{wave-id}/bugs/$BUG_ID-*.md | head -1 | awk '{print $2}')

# Chạy lại TC failing — đảm bảo bug có thực
cd docs/architecture/infra && docker-compose up -d && cd -
sleep 10

# Re-run failing TC (giống test-execute)
RESP=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8080/v1/orders \
    -H "Authorization: Bearer $TOKEN" -d '{"description":"no name"}')
HTTP=$(echo "$RESP" | tail -1)

# Verify bug exists
if [ "$HTTP" = "500" ]; then
    echo "REPRODUCED: bug tồn tại (HTTP 500 thay vì 400 expected)"
    # Update bug ticket: status=reproduced, reproduced_at=<timestamp>
    sed -i "s/^status: open/status: reproduced/" tracking/waves/{wave-id}/bugs/$BUG_ID-*.md
    sed -i "/^status: reproduced/a reproduced_at: $(date -Iseconds)" tracking/waves/{wave-id}/bugs/$BUG_ID-*.md
else
    echo "BUG NOT REPRODUCED — recheck TC hoặc bug đã tự fix?"
    exit 1   # KHÔNG fix vu vơ
fi
```

**Nếu KHÔNG reproduce được:** STOP. Document lý do trong bug ticket (`status: not_reproduced`), không fix code.

### Step 2 — FIX (sửa source code)

```bash
# Identify root cause (read source + bug evidence)
# Vd: services/order/api/order-handler.py thiếu validate request body trước domain

# Sửa code trong owned_paths
# ... edit files ...

# Lint local
cd services/order && ruff check . && cd -

# Unit test local
cd services/order && pytest tests/unit -v && cd -
```

### Step 3 — VERIFY (xác nhận fix + regression)

```bash
# 3.1 Run failing TC again — phải PASS
RESP=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8080/v1/orders \
    -H "Authorization: Bearer $TOKEN" -d '{"description":"no name"}')
HTTP=$(echo "$RESP" | tail -1)
[ "$HTTP" = "400" ] && echo "FIX VERIFIED ($HTTP)" || { echo "FIX FAILED — bug vẫn còn"; exit 1; }

# 3.2 Run regression — toàn bộ TC của boundary có thể bị ảnh hưởng
cd services/order && pytest tests/integration -v && cd -

# 3.3 Update bug ticket status
sed -i "s/^status: reproduced/status: fixed/" tracking/waves/{wave-id}/bugs/$BUG_ID-*.md
sed -i "/^status: fixed/a fixed_at: $(date -Iseconds)" tracking/waves/{wave-id}/bugs/$BUG_ID-*.md

# 3.4 Save verification log
mkdir -p tracking/waves/{wave-id}/bugs/verification
cat > tracking/waves/{wave-id}/bugs/verification/$BUG_ID-verify.log << EOF
Timestamp: $(date -Iseconds)
TC: $TC_ID
Before fix HTTP: 500
After fix HTTP: $HTTP
Regression tests: all pass
Files changed: services/order/api/order-handler.py, services/order/dto/order-request.py
EOF
```

### Step 4 — Ghi KG đầy đủ

```bash
# Decision về cách fix
py scripts/knowledge_writer.py decision knowledge-base/order.knowledge-graph.yaml \
  '{"context":"BUG-001 fix","decision":"Validate DTO ở api layer trước khi pass vào domain","rationale":"Catch error sớm, đúng Rule BE-2"}'

# Do-not-repeat
py scripts/knowledge_writer.py do-not-repeat knowledge-base/order.knowledge-graph.yaml \
  "Validate DTO ở api layer trước domain (BUG-001 wave-001)"

# Pattern fix
py scripts/knowledge_writer.py learning knowledge-base/order.knowledge-graph.yaml pattern \
  "Pydantic validate trong DTO class + Depends() trong handler"

# Completed
py scripts/knowledge_writer.py completed knowledge-base/order.knowledge-graph.yaml \
  "fix-BUG-001"
```

### Step 5 — Complete

```bash
py scripts/harness.py fix-bugs complete '{"boundary_id": "order"}'
```

→ stage = `FIX_MANUAL_BUGS`, allowed_next = `["retest"]`.

## Sau fix-bugs

Bug ticket status = `fixed` (chưa `verified` — retest mới verify).

`/retest` đọc bug ticket frontmatter:
- `origin: auto` → branch `pass_auto` → SPECIALIST_TESTING
- `origin: manual` → branch `pass_manual` → MANUAL_TEST

retest sẽ set `status: verified` + `verified_at` nếu pass.

## Gate hook (verify proof)

`gate_runner.check_command("fix-bugs")` check:
- `tracking/waves/*/bugs/**` exists
- Bug ticket có field `reproduced_at` (không skip step 1)
- `tracking/waves/*/bugs/verification/*.log` tồn tại (proof step 3)
- Files changed trong owned_paths

Nếu thiếu proof → gate fail, `complete` reject.

## KHÔNG được

- **Fix mà không reproduce** — không có proof bug tồn tại.
- **Fix mà không verify** — không re-run TC.
- **Skip regression** — fix 1 chỗ break 1 chỗ khác.
- **Update status trực tiếp** không qua reproduce-fix-verify cycle.
- Fix file ngoài owned_paths boundary.
