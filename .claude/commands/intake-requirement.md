---
name: intake-requirement
description: "Flat orchestration: Claude main spawn 4 sub-agents tuần tự (req → biz → arch → plan)"
argument-hint: "\"<mô tả project>\" (vd: \"CRM cho công ty bán nhựa HDPE multi-tenant\")"
when_state: [BOOTSTRAP, INTAKE]
sets_stage: INTAKE
spawn:
  agent: "Claude main (no orchestrator agent) → 4 specialist sub-agents sequentially"
  skills: [requirement-analysis, business-analysis, technical-design, implementation-plan]
gates: [{type: int_min, field: step, min: 1}]
---

# /intake-requirement

> **TUẦN TỰ — không skip, không reorder.** Mỗi bước verify file trước khi proceed bước kế.

## Mục đích

Phân tích yêu cầu project end-to-end qua 4 step. Claude main đóng vai orchestrator, spawn 4 specialist sub-agent tuần tự trong cùng 1 turn. Output: full doc set (PROJECT + FEAT + ADR + HLD + API + data-model + UX + events + integrations + plans + MATRIX).

## Mode detection (Claude main thực hiện)

```
1. Read docs/architecture/PROJECT.md exists?
   - NO  → mode = "full"
   - YES → check evidence for cr_id
       - cr_id present → mode = "amendment"
       - else → mode = "full" (re-run)
```

## Input

User truyền **mô tả project** sau slash command:
```
/intake-requirement "CRM cho công ty bán nhựa HDPE multi-tenant, 3 module: customer-mgmt, order-mgmt, payment"
```

Phần `"..."` sau `/intake-requirement` được pass vào `$ARGUMENTS`. Bước 1 sử dụng `$ARGUMENTS` làm input cho specialist.

Nếu user gọi `/intake-requirement` không argument:
- Mode = full lần đầu → ask user: "Mô tả project? (vd: CRM cho công ty XYZ với N module ...)"
- Mode = amendment → đọc CR file lấy change_summary làm input

## Bước 1: Requirement analysis

1. Run: `py scripts/build_prompt.py intake-requirement --step 1 --input "$ARGUMENTS"`
2. Spawn sub-agent qua Agent tool với prompt từ stdout.
3. Đợi sub-agent return.
4. Verify: `docs/architecture/PROJECT.md` tồn tại, có scope + NFR + glossary.
5. Verify: `docs/architecture/feat/FEAT-*.md` ≥ 1 file.
6. Sub-agent return có lỗi → **STOP**, báo user, KHÔNG tiếp tục bước 2.

## Bước 2: Business analysis

Chỉ thực hiện sau khi Bước 1 PASS verify.

1. Run: `py scripts/build_prompt.py intake-requirement --step 2`
2. Spawn sub-agent.
3. Verify: FEAT-*.md có AC testable, có BR-*, có `boundaries_suggested`.
4. Lỗi → STOP.

## Bước 3: Technical design

Chỉ thực hiện sau Bước 2.

1. Run: `py scripts/build_prompt.py intake-requirement --step 3`
2. Spawn sub-agent.
3. Verify:
   - `docs/architecture/adr/ADR-*.md` ≥ 3 file
   - `docs/architecture/hld/hld-*.md` per boundary
   - `docs/architecture/api/api-*.md` per boundary
   - `docs/architecture/data-model/data-model-*.md` per backend boundary
   - `docs/architecture/ux/ux-*.md` per FE boundary
   - `docs/architecture/events/*-events.md` per event-producing boundary
   - `docs/architecture/integrations/INTEG-*.md` ≥ 1
4. Lỗi → STOP.

## Bước 4: Implementation plan

Chỉ thực hiện sau Bước 3.

1. Run: `py scripts/build_prompt.py intake-requirement --step 4`
2. Spawn sub-agent.
3. Verify:
   - `docs/plans/WAVE-SEQUENCE.md` tồn tại
   - `docs/plans/wave-001.md` tồn tại
   - `harness/SERVICE-BOUNDARY-MATRIX.json` có boundaries ≥ 1
4. Lỗi → STOP.

## Sau khi cả 4 bước done

1. Báo user:
   ```
   Intake 4-step pipeline done.
   
   Artifacts generated:
   - PROJECT.md
   - FEAT-*.md (N files)
   - ADR-*.md (N files)
   - HLD/API/data-model/UX/events/integrations per boundary
   - WAVE-SEQUENCE.md + wave-001.md
   - SERVICE-BOUNDARY-MATRIX.json
   
   Next steps:
   - Review docs. Nếu cần chỉnh: /review-document "<feedback>" [--file path]
   - Nếu OK luôn: /approve-document
   ```

2. Auto run: `py scripts/harness.py intake-requirement complete '{"step":4, "all_steps_done":true}'`

## Crash / resume

Nếu Claude main crash giữa chừng (vd sau bước 2):
- Re-run `/intake-requirement`
- Mode detect = full, đọc workflow.history
- Skip các bước đã có evidence trong history
- Tiếp tục từ bước chưa xong

## Amendment mode

Khi mode=amendment (sau `/apply-cr`):
- Đọc CR file để biết section nào cần sửa
- Bước nào không bị CR ảnh hưởng → skip
- Chỉ chạy specialist nào cần update artifact

## Sub-agent reminder pattern

Mỗi specialist sub-agent kết thúc với reminder ở cuối message:
> "Step N done. Bạn review file [list]. Nếu OK chạy `/review-document` hoặc `/approve-document`. Có sửa thì feedback qua `/review-document`."
