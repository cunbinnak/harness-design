"""
capture_feature_state.py — HARNESS ghi feature-state.md (L05/L07/L08), KHÔNG để agent tự khai.

Derive trạng thái mỗi FEAT in-scope wave từ bằng chứng (FEAT `### AC-n` + test-case-registry TC↔AC +
test-report TC pass) rồi ghi `tracking/{wave}/feature-state.md` — bảng máy-đọc + người-đọc.

Vì sao HARNESS ghi (không phải agent): giống proof-file infra/health — nguồn sự thật là phép derive
(gates.derive_feature_states), file chỉ là VIEW. Agent ghi tay = fake tiến độ → PreToolUse chặn
(policies.is_proof_file: feature-state.md).

Là **clock-in artifact** (L05): session mới đọc file này biết ngay feat nào `passing`/`active`/
`not_started` — không phải dò lại từ đầu. MAIN chạy sau /test-execute (khi có report), hoặc bất cứ
lúc nào ở DEV+ để xem tiến độ (chưa test → mọi feat not_started, vẫn là baseline hữu ích).

Usage:
  py scripts/capture_feature_state.py                  # đọc STATE → ghi wave hiện tại
  py scripts/capture_feature_state.py --wave wave-001  # ép wave
  py scripts/capture_feature_state.py --selftest       # smoke (hermetic)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import gates  # noqa: E402  (reuse derive_feature_states + render_feature_state_md)

REPO_ROOT = SCRIPTS.parent
STATE_FILE = REPO_ROOT / "harness" / "STATE.json"


def capture(wave_id: str, root: Path | None = None) -> int:
    root = root or REPO_ROOT
    try:
        state = json.loads((root / "harness" / "STATE.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    # ép wave_id vào state để derive dùng đúng wave
    state = dict(state)
    state["wave"] = {**(state.get("wave") or {}), "id": wave_id}
    rows = gates.derive_feature_states(state, root)
    if not rows:
        print(f"WARN: wave {wave_id} không có wave_features (chưa /start-wave?) — không ghi.", file=sys.stderr)
        return 1
    out_dir = root / "tracking" / wave_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "feature-state.md").write_text(gates.render_feature_state_md(state, root), encoding="utf-8")
    passing = sum(1 for r in rows if r["state"] == "passing")
    scoped = sum(1 for r in rows if r["state"] not in ("deferred", "no-file"))
    print(f"OK: tracking/{wave_id}/feature-state.md — {passing}/{scoped} feat in-scope passing.")
    for r in rows:
        print(f"  {r['feat']:<18} {r['state']:<12} AC {r['ac_pass']}/{r['ac_total']}")
    return 0


def _selftest() -> int:
    import shutil
    import tempfile
    d = Path(tempfile.mkdtemp(prefix="capfs_"))
    try:
        (d / "harness").mkdir()
        (d / "docs" / "architecture" / "feat").mkdir(parents=True)
        w = d / "tracking" / "wave-001"
        w.mkdir(parents=True)
        (d / "harness" / "STATE.json").write_text(
            json.dumps({"wave": {"id": "wave-001"}, "wave_features": ["FEAT-1"]}), encoding="utf-8")
        (d / "docs" / "architecture" / "feat" / "FEAT-1.md").write_text(
            "# F\n### AC-1: x\n### AC-2: y\n", encoding="utf-8")
        (w / "test-case-registry.md").write_text(
            "| TC | feature | AC |\n|--|--|--|\n| TC-1 | FEAT-1 | FEAT-1:AC-1 |\n| TC-2 | FEAT-1 | FEAT-1:AC-2 |\n",
            encoding="utf-8")
        (w / "test-report.md").write_text(
            "| TC | Result |\n|--|--|\n| TC-1 | PASS |\n| TC-2 | PASS |\n", encoding="utf-8")
        assert capture("wave-001", root=d) == 0
        txt = (w / "feature-state.md").read_text(encoding="utf-8")
        assert "1/1 feat in-scope `passing`" in txt and "FEAT-1 | passing" in txt, txt
        print("OK: capture_feature_state.py selftest passed")
        return 0
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="HARNESS ghi feature-state.md (derive, L05/L07/L08)")
    ap.add_argument("--wave", help="wave id (vd wave-001); mặc định đọc STATE")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return _selftest()
    wave_id = args.wave
    if not wave_id:
        try:
            wave_id = (json.loads(STATE_FILE.read_text(encoding="utf-8")).get("wave") or {}).get("id")
        except (OSError, ValueError):
            wave_id = None
    if not wave_id:
        print("FAIL: không xác định wave (STATE.wave.id rỗng) — /start-wave trước.", file=sys.stderr)
        return 2
    return capture(wave_id)


if __name__ == "__main__":
    sys.exit(main())
