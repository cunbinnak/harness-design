# FAILURE MODES

Đăng ký lỗi / hành vi sai đã biết. Tham chiếu từ RETURN SCHEMA `failure_modes_logged`.

| ID | Mô tả | boundary_id | Phát hiện | Mitigation |
|----|--------|-------------|-----------|------------|
| FM-001 | Agent sửa ngoài owned_paths | * | Hook / review diff | Chặn edit; chỉ path trong matrix |
| FM-002 | Thiếu INTEG / contract khi implement | * | Spawn pre-check | Dừng; bổ sung docs/architecture trước |
| FM-003 | Trùng decision không supersede | * | KB audit | Ghi `status: superseded` + `supersedes` |
| FM-012 | Spawn return không phải JSON / thiếu field RETURN SCHEMA | * | Orchestrator parse | Reject; yêu cầu subagent retry JSON only |

> Thêm hàng khi có incident hoặc test fail. Ghi song song vào `knowledge-base/shared.knowledge-graph.yaml` learnings nếu cần.
