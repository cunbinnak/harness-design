#!/usr/bin/env python3
"""selftest_all.py — chạy MỌI phép tự kiểm của harness, tự dò chứ không chép danh sách.

VÌ SAO CÓ FILE NÀY
    Danh sách script phải chạy vốn nằm trong đầu người gõ và trong `README`. Cả hai đều trôi:
    đo được 10 script có `--selftest` mà bộ đang chạy chỉ đụng 7 — `capture_feature_state`,
    `capture_infra_proof`, `materialize_matrix` có phép kiểm chạy được nhưng **không ai gọi**,
    tức là hỏng cũng không ai biết.

    Cùng một bài với `gates.py --list`: thứ chép tay là bản sao thứ hai của sự thật, và bản sao
    thì trôi ngay lần thêm file kế tiếp. Nên ở đây **dò**: script nào khai `--selftest` trong
    argparse thì chạy nó. Thêm script mới có selftest → tự được gọi, không phải nhớ sửa chỗ nào.

    Ba phép không theo khuôn `--selftest` được gọi tên riêng (`state.py validate`,
    `smoke_test.py`, `doc_integrity.py`, `policies.py`) — chúng là entry point khác kiểu, không
    phải ngoại lệ bị bỏ quên.

Usage:
  py scripts/selftest_all.py            # chạy hết
  py scripts/selftest_all.py --list     # chỉ liệt kê sẽ chạy gì

Exit: 0 tất cả xanh · 1 có cái đỏ
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

# Phép kiểm KHÔNG theo khuôn `--selftest`. Gọi tên riêng vì entry point khác kiểu, không phải vì
# quên — thêm vào đây thì cũng phải nói được vì sao nó không dùng `--selftest`.
EXTRA: tuple[tuple[str, list[str]], ...] = (
    ("state.py validate", ["state.py", "validate"]),          # validate STATE vs STATE-MACHINE
    ("smoke_test.py", ["smoke_test.py"]),                     # E2E state machine, tự chạy khi gọi
    ("doc_integrity.py", ["doc_integrity.py"]),               # soi tài liệu trôi, không có cờ
    ("hooks/policies.py", ["hooks/policies.py"]),             # selftest chạy khi import as main
)


def discover() -> list[Path]:
    """Script khai `--selftest` trong argparse — dò, không chép danh sách."""
    out = []
    for p in sorted(SCRIPTS.rglob("*.py")):
        if "__pycache__" in p.parts or p.name == Path(__file__).name:
            continue
        try:
            if "--selftest" in p.read_text(encoding="utf-8", errors="ignore"):
                out.append(p)
        except OSError:
            continue
    return out


def escapees() -> list[str]:
    """Script CÓ hàm `_selftest` mà KHÔNG khai `--selftest` → dò không thấy, hỏng cũng không ai biết.

    `gates.py` từng lọt đúng khe này: nó chạy selftest MẶC ĐỊNH nên trong file không có chuỗi
    `--selftest`, và file lớn nhất repo nằm ngoài mọi lượt kiểm. **Một luật dò im lặng bỏ sót còn
    tệ hơn danh sách chép tay** — danh sách ít ra còn nhìn thấy là thiếu.
    """
    named = {args[0] for _, args in EXTRA}       # đã gọi tên riêng thì không phải lọt lưới
    out = []
    for p in sorted(SCRIPTS.rglob("*.py")):
        rel = p.relative_to(SCRIPTS).as_posix()
        if "__pycache__" in p.parts or p.name == Path(__file__).name or rel in named:
            continue
        try:
            s = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "def _selftest" in s and "--selftest" not in s:
            out.append(rel)
    return out


def run(label: str, args: list[str]) -> bool:
    r = subprocess.run([sys.executable, *args], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok = r.returncode == 0
    print(f"  {'PASS' if ok else 'FAIL'}  {label}")
    if not ok:
        tail = (r.stderr or r.stdout or "").strip().splitlines()[-6:]
        for line in tail:
            print(f"        {line[:120]}")
    return ok


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    found = discover()
    jobs: list[tuple[str, list[str]]] = [
        (p.relative_to(SCRIPTS).as_posix(),
         [str(p.relative_to(ROOT)).replace("\\", "/"), "--selftest"]) for p in found
    ]
    jobs += [(label, [f"scripts/{a}" if not a.startswith("scripts/") else a for a in args][:1]
              + args[1:]) for label, args in EXTRA]

    if "--list" in sys.argv:
        print(f"{len(jobs)} phép kiểm:")
        for label, _ in jobs:
            print(f"  {label}")
        return 0

    lost = escapees()
    if lost:
        print("LỌT LƯỚI: có `_selftest` mà không khai `--selftest`, dò không thấy:")
        for x in lost:
            print(f"  {x}")
        print("  Thêm cờ `--selftest` vào script đó, hoặc gọi tên riêng ở EXTRA.")
        print()

    print(f"Chạy {len(jobs)} phép kiểm ({len(found)} dò được + {len(EXTRA)} gọi tên riêng)\n")
    results = [run(label, args) for label, args in jobs]
    bad = results.count(False) + len(lost)
    print(f"\n  ---- {results.count(True)} đạt · {bad} hỏng")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
