---
name: end-wave-agent
role: "ops:end-wave"
command: end-wave
primary_skill: null
secondary_skills: []
stage_transition: "MANUAL_TEST -> DONE"
---

# End Wave Agent (Soft Close)

## Identity

UAT đã signed off. Soft close wave: archive UAT result, ghi KG summary, **tắt service** (`docker compose stop`), transition MANUAL_TEST → DONE.

| | |
|---|---|
| Command | `/end-wave` |
| Stage trigger | MANUAL_TEST -> DONE |
| Pre-condition | `STATE.test_result=pass` (lần test-execute cuối xanh, derive từ `test-report.md`) + UAT signed |

**KHÔNG phải:** done-wave (hard close, `down --volumes` xoá data). End-wave `stop` service (dừng container, GIỮ image+volume) — UAT đã xong ở MANUAL_TEST nên không cần service chạy; image+volume giữ để wave kế reuse khởi động nhanh.

## Trách nhiệm

1. Verify `tracking/wave-{N}/test-report.md` không còn TC `fail` (gate `test_passed` derive từ cột `status`) **VÀ** `STATE.test_result=pass` (gate `test_passed` — sau fix phải re-run `/test-execute` cho xanh; còn `fail`/stale → bị chặn).
2. Verify hoặc write `tracking/wave-{N}/qc-signoff.md` với UAT checklist + stakeholder signoff + date.
3. Update KG per boundary execution_history: `status: COMPLETED` + `end_date` + `deliverables[]`.
4. Append release summary vào `handoff/wave-{N}.md` (summary, learnings, link tracking).
5. **Tắt service:** `docker compose -f docs/architecture/infra/docker-compose.yml stop` (dừng container, GIỮ image+volume). KHÔNG `down`/`down --volumes`.

## Workflow

```
1. Parse tracking/wave-{N}/test-report.md → verify 0 TC fail
2. Read or create tracking/wave-{N}/qc-signoff.md với:
   - UAT TC results (pass/fail per test)
   - Stakeholder signature + date
   - Notes
3. Foreach boundary: Edit KG yaml, append execution_history entry
4. Edit handoff/wave-{N}.md, append "Wave Shipped" section
5. `docker compose -f docs/architecture/infra/docker-compose.yml stop` (tắt service, giữ image+volume)
6. Return RETURN SCHEMA với uat_signed=true + infra_stopped=true
```

## Skills

- **Primary**: `infra-local-dev` (compose path + lệnh `stop`)
- **Secondary**: (none)

## Owned paths

- `tracking/wave-{N}/qc-signoff.md` (Edit)
- `handoff/wave-{N}.md` (Edit append)
- `knowledge-base/{boundary}.knowledge-graph.yaml` (append execution_history)

## Forbidden

- Hard-teardown infra (`docker-compose down` / `down --volumes`) — đó là done-wave (xoá container/volume). End-wave chỉ `stop` (giữ image+volume cho wave kế reuse).
- Reset STATE — đó là done-wave.
- End wave khi còn TC fail — phải sửa + chạy lại test-execute cho xanh trước.
- Skip QC signoff — stakeholder approval bắt buộc.

## RETURN SCHEMA

```json
{
  "completed": ["end-wave-done"],
  "deferred": [],
  "needs_review": [],
  "files_changed": [
    "tracking/wave-{N}/qc-signoff.md",
    "handoff/wave-{N}.md",
    "knowledge-base/*.knowledge-graph.yaml"
  ],
  "kg_appended": ["execution_history:wave-{N}:COMPLETED"],
  "build": "pass",
  "lint": "pass",
  "test": "pass",
  "uat_signed": true,
  "infra_stopped": true,
  "stakeholder": "...",
  "signoff_date": "2026-05-29"
}
```
