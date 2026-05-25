# Wave {wave-id}

> **Purpose:** Plan + assignment cho 1 wave — FEAT nào làm, boundary nào đảm nhiệm, timeline.
> **Owner:** §1 `intake:program-planner` (intake bước 4) · §2 `start-wave` agent (trước start-dev).
> **Audience:** `start-wave`, `start-dev` agents; reviewer.
> **Out of scope:**
> - FEAT spec → [`../../architecture/feat/`](../../architecture/feat/)
> - HLD per boundary → [`../../architecture/hld/`](../../architecture/hld/)
> - Test plan → `tracking/waves/{wave-id}/test-cases.md`
> - Handoff doc → `handoff/{wave-id}.md`

---

## §1. Plan (intake bước 4)

> Điền bởi `program-planner` lúc intake. KHÔNG đụng sau khi `start-wave complete`.

### Meta

- **Wave id:** {wave-id}
- **Title:** {tên wave — vd "MVP", "Phase 2 - Reporting"}
- **Thời lượng ước lượng:** (vd 4 tuần)
- **Mục tiêu deliverable:** (1-2 câu)
- **Phụ thuộc wave trước:** (wave-00X hoặc —)

### FEAT trong wave này

| FEAT | Mục tiêu ngắn | Boundary dự kiến | Ưu tiên |
|------|--------------|------------------|---------|
| FEAT-001 | (1 câu) | order, fe-web | Must |
| FEAT-002 | | customer | Must |
| FEAT-003 | | analytics | Should |

### UX deliverable (FE boundaries)

| Boundary | Hình thức | File / link |
|----------|-----------|-------------|
| fe-web | markdown ASCII wireframe | `docs/architecture/ux/ux-fe-web.md` |
| fe-admin | figma + markdown | `docs/architecture/ux/ux-fe-admin.md` + link figma |

### Order of implementation

> Thứ tự logic để dev không bị block. Ghi rõ "FEAT-X cần xong trước FEAT-Y vì..."

1. FEAT-001 (customer model trước — FEAT-002 phụ thuộc)
2. FEAT-002
3. FEAT-003 (parallel với FEAT-002 sau khi customer xong)

---

## §2. Assignment (trước `start-dev complete`)

> Điền/cập nhật bởi `start-wave-agent` sau khi load roster. Đây là input cho `start-dev`.

### Bảng giao việc

| FEAT | boundary_id | dev agent | AC scope |
|------|-------------|-----------|---------|
| FEAT-001 | order | order-agent | AC-1, AC-2, AC-3 |
| FEAT-001 | fe-web | fe-web-agent | AC-4 (UI) |
| FEAT-002 | customer | customer-agent | All AC |
| FEAT-003 | analytics | analytics-agent | AC-1, AC-2 |

### Evidence cho `start-dev complete`

```json
{
  "features_in_flight": ["FEAT-001", "FEAT-002"],
  "boundaries_in_flight": ["order", "customer", "fe-web"]
}
```

(Chạy `start-dev complete` lần đầu cho boundary đầu tiên — các boundary còn lại spawn dev agent riêng.)

### Context đã load (tham khảo, harness auto-fill khi `start-wave`)

- `STATE.features_in_flight` ← từ FEAT list §1
- `STATE.boundaries_in_flight` ← từ assignment §2
- `STATE.workflow.wave_dev_agents` ← list agent files theo boundary

---

## §3. Progress notes (optional, free-form)

| Date | Note |
|------|------|
| | |
