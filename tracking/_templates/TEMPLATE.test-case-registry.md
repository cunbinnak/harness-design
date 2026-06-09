# Test Case Registry — wave-{N}

> Wave: wave-{N} ({wave-title}) · Features: FEAT-001, FEAT-002, … · Boundaries: {boundary-list} · Created by: test-plan-agent
>
> **Mỗi TC = 1 HÀNG.** `type`: `auto` (test-execute chạy) | `manual` (UAT/QA). `pri`: P0 (blocker) | P1 (must) | P2 (nice).
> `AC` = `FEAT-N:AC-M` (mọi TC trace ≥ 1 AC, trừ smoke infra). `note` = framework (playwright) / verifier (stakeholder/QA) / `ref_bug` (regression).
> Steps/Expected giữ ngắn 1 cell (chi tiết dài → UAT script riêng). test-execute parse cột `type=auto` để chạy.

| TC | group | type | boundary | feature | AC | pri | pre-condition | steps | expected | note |
|----|-------|------|----------|---------|----|-----|---------------|-------|----------|------|
| TC-S01 | smoke | auto | all | infra | N/A | P0 | compose up, services healthy | `curl /health` | 200 `{status:ok}` | |
| TC-S02 | smoke | auto | auth | FEAT-001 | AC-1 | P0 | auth up + seed user | POST `/v1/auth/login` | 200 + `access_token` | |
| TC-I01 | integration | auto | {boundary} | FEAT-{N} | AC-1 | P1 | token (TC-S02), tenant in DB | POST `/v1/{res}` → GET `/{id}` | 201 + id; GET same entity | |
| TC-I02 | integration | auto | {boundary} | FEAT-{N} | AC-2 | P1 | — | POST thiếu required field | 400 `VALIDATION_ERROR` | |
| TC-I03 | integration | auto | {boundary} | FEAT-{N} | AC-3 | P0 | — | POST không Authorization header | 401 `UNAUTHORIZED` | |
| TC-I04 | integration | auto | {boundary} | FEAT-{N} | AC-x | P1 | tenant khác | GET resource của tenant khác | 403/404 (no cross-tenant leak) | tenant isolation |
| TC-E01 | e2e | auto | fe-{name} | FEAT-{N} | AC-M | P1 | login | login → /resource → create → submit → verify list | item visible + screenshot | playwright |
| TC-E02 | e2e | manual | fe-{name} | FEAT-{N} | AC-M | P2 | — | open detail → print → preview | PDF render đúng layout | |
| TC-M01 | uat | manual | cross-cutting | FEAT-{N} | AC-M | P1 | stakeholder role | execute business flow (UAT script) | stakeholder confirm OK | verifier=stakeholder |
| TC-M02 | uat | manual | {boundary} | FEAT-{N} | AC-M | P2 | — | input boundary value (max/min) | handle gracefully, no crash | verifier=QA |
| TC-R01 | regression | auto | {boundary} | regression | — | P0 | — | re-run bug scenario | không tái phát | ref_bug=BUG-{NNN} |

## Coverage matrix (AC → TC)

| FEAT:AC | TCs covering | auto | manual |
|---------|--------------|------|--------|
| FEAT-001:AC-1 | TC-S02, TC-I01 | 2 | 0 |
| FEAT-001:AC-2 | TC-I02 | 1 | 0 |
| FEAT-001:AC-3 | TC-I03 | 1 | 0 |
| FEAT-002:AC-1 | TC-E01, TC-M01 | 1 | 1 |
| … | … | … | … |

**Total**: {N} TC ({auto} auto, {manual} manual). AC coverage: 100% (mọi AC `Must` ≥ 1 TC — không AC mồ côi).
