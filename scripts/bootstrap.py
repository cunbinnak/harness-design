#!/usr/bin/env python3
"""bootstrap.py — dựng một project MỚI từ bộ khung này. Bản khung giữ nguyên, dùng lại được.

VÌ SAO CÓ FILE NÀY
    Trước đây cách bắt đầu project mới là: fork repo → tự chạy `reset_for_new_project.py --confirm`
    trong chính bản fork. Ba chỗ hụt:

      1. Bản khung bị dùng làm chỗ làm việc. Chạy thử một wave trong đó là nó bẩn, và lần sau
         fork ra đã mang sẵn vết của project trước — đúng thứ đã xảy ra (`archive/wave-001/`
         lọt vào repo khung, kiêm luôn cờ "wave 1 đã đóng" cho MỌI project fork sau).
      2. Lịch sử git của bộ khung đi theo. Project mới mở `git log` ra thấy 200 commit về
         chính cái khung, không phải về sản phẩm của nó.
      3. Phải NHỚ chạy reset. Quên là project mới khởi đầu với tài liệu của project khác.

    Đổi sang mô hình COPY-RA (như VIPER `bootstrap.py`): khung nằm im, mỗi project là một thư
    mục riêng, `git init` sạch. Bước dọn artifact vẫn dùng `reset_for_new_project.py` — gọi lại
    chứ không chép logic sang, để hai đường không lệch nhau.

LÀM GÌ
    1. Copy      → thư mục đích (bỏ .git, artifact wave, zip, file cá nhân, chính bootstrap này)
    2. Dọn       → gọi reset_for_new_project trong ĐÍCH: xoá tài liệu instance, đặt STATE
    3. Danh tính → STATE.project.{id,display_name,service_prefix} + CLAUDE.md §IDENTITY
    4. Kiểm      → file bắt buộc còn đủ · state hợp lệ · stage=BOOTSTRAP · không sót artifact
    5. git       → init + commit đầu trên nhánh main

Usage:
    py scripts/bootstrap.py <project-code> [--name "Tên"] [--prefix cb]
                            [--target PATH] [--dry-run]

Ví dụ:
    py scripts/bootstrap.py clinicbook --name "ClinicBook" --prefix cb

<project-code>: chữ thường + số + gạch nối. Mặc định --target là ../<project-code>

Exit: 0 ok · 1 sai tham số · 2 đích đã tồn tại · 3 kiểm tra thất bại
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent

# KHÔNG copy sang project mới.
SKIP_DIRS = {
    ".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", ".idea", ".cursor",
    "services",       # thư mục làm việc polyrepo, gitignored
    "archive",        # snapshot wave của project khác — copy sang là project mới sinh ra đã
                      # "đóng" sẵn wave 1 (thư mục này kiêm cờ đóng wave)
}
SKIP_FILES = {".DS_Store", "Thumbs.db"}
# Đường dẫn tương đối, khớp CHÍNH XÁC — không khớp theo tên file.
TEMPLATE_ONLY = {
    "scripts/bootstrap.py",        # project không sinh project khác
    "HARNESS-CHANGELOG.md",        # nhật ký của bộ khung, không phải của sản phẩm
    ".claude/settings.local.json", # permission cá nhân của máy này
}
SKIP_SUFFIXES = (".zip", ".pyc")

REQUIRED = [
    "CLAUDE.md", "AGENTS.md", "README.md", "SETUP-GUIDE.md",
    "harness/STATE.json", "harness/STATE-MACHINE.json",
    "harness/SERVICE-BOUNDARY-MATRIX.json", "harness/PROTOCOL.md",
    "scripts/harness.py", "scripts/state.py", "scripts/gates.py",
    "scripts/build_prompt.py", "scripts/next_wave.py", "scripts/decide.py",
    "scripts/doc_integrity.py", "scripts/selftest_all.py",
    ".claude/settings.json",
    "commands/discover.md", "commands/domain.md", "commands/approve-document.md",
    "commands/run-wave.md", "commands/dogfood.md", "commands/next-wave.md",
    "commands/status.md",
    "docs/architecture/TEMPLATE.project.md",
    "docs/discovery/TEMPLATE.hypothesis-log.md",
    "tracking/_templates/TEMPLATE.test-case-registry.md",
    "tracking/_templates/TEMPLATE.dogfood-report.md",
    "tracking/_templates/TEMPLATE.production-ready.md",
    "knowledge-base/TEMPLATE.knowledge-graph.yaml",
]

CODE_RE = re.compile(r"^[a-z][a-z0-9-]{1,38}[a-z0-9]$")


def die(msg: str, code: int) -> int:
    print(f"LỖI: {msg}", file=sys.stderr)
    return code


def iter_files(root: Path):
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if p.name in SKIP_FILES or p.suffix in SKIP_SUFFIXES:
            continue
        if rel.as_posix() in TEMPLATE_ONLY:
            continue
        yield p, rel


def copy_tree(target: Path) -> int:
    n = 0
    for src, rel in iter_files(SRC):
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        n += 1
    return n


def clean_artifacts(target: Path) -> str:
    """Gọi lại `reset_for_new_project.py` TRONG đích — không chép logic sang.

    Nó biết chính xác tài liệu nào là instance (PROJECT.md, FEAT-*, hld-*, wave-*…) và cái nào là
    khuôn phải giữ. Chép danh sách đó sang đây là đẻ ra bản sao thứ hai, rồi thêm một loại artifact
    là hai bên lệch.
    """
    r = subprocess.run(
        [sys.executable, "scripts/reset_for_new_project.py", "--confirm"],
        cwd=target, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or "").strip()[-600:])
    removed = sum(1 for l in (r.stdout or "").splitlines() if l.startswith("REMOVED"))
    return f"{removed} artifact"


def set_identity(target: Path, code: str, name: str, prefix: str | None) -> None:
    p = target / "harness" / "STATE.json"
    st = json.loads(p.read_text(encoding="utf-8"))
    st["project"] = {"id": code, "display_name": name, "service_prefix": prefix}
    st["stage"] = "BOOTSTRAP"
    p.write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # CLAUDE.md §IDENTITY: hai dòng đầu là danh tính project, phần còn lại do `/discover D3` derive.
    # Gỡ mọi trỏ tới HARNESS-CHANGELOG.md — file đó là nhật ký của BỘ KHUNG, không copy sang,
    # nên để nguyên link là mỗi project mới sinh ra đã có một link chết ngay ở router.
    for rel in ("CLAUDE.md", "README.md", "AGENTS.md", "SETUP-GUIDE.md"):
        f = target / rel
        if not f.is_file():
            continue
        body = f.read_text(encoding="utf-8")
        keep = [l for l in body.splitlines() if "HARNESS-CHANGELOG" not in l]
        if len(keep) != len(body.splitlines()):
            f.write_text("\n".join(keep) + "\n", encoding="utf-8")

    c = target / "CLAUDE.md"
    t = c.read_text(encoding="utf-8")
    t = re.sub(r"^\| Project \| .*$",
               f"| Project | **{name}** — _một dòng: giải quyết nỗi đau gì, cho ai. "
               f"`/discover D0` điền._ |", t, count=1, flags=re.M)
    c.write_text(t, encoding="utf-8")


def verify(target: Path) -> list[str]:
    bad = []
    for rel in REQUIRED:
        if not (target / rel).is_file():
            bad.append(f"thiếu {rel}")
    for leftover in ("archive", "services"):
        if (target / leftover).exists() and any((target / leftover).iterdir()):
            bad.append(f"{leftover}/ không rỗng — vết project cũ lọt sang")
    r = subprocess.run([sys.executable, "scripts/state.py", "validate"], cwd=target,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        bad.append("state.py validate đỏ: " + (r.stdout or r.stderr).strip()[:200])
    r = subprocess.run([sys.executable, "scripts/harness.py", "state"], cwd=target,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if "BOOTSTRAP" not in (r.stdout or ""):
        bad.append("stage không phải BOOTSTRAP sau khi dựng")
    return bad


def git_init(target: Path, code: str) -> str:
    def g(*a):
        return subprocess.run(["git", *a], cwd=target, capture_output=True, text=True)
    if g("rev-parse", "--git-dir").returncode == 0:
        return "đã có .git, bỏ qua"
    if g("init", "-b", "main").returncode != 0:
        g("init")
        g("checkout", "-b", "main")
    g("add", "-A")
    r = g("commit", "-m", f"khởi tạo {code} từ ADLC harness")
    return "init + commit đầu (main)" if r.returncode == 0 else f"init xong, commit lỗi: {r.stderr.strip()[:120]}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Dựng project mới từ bộ khung ADLC")
    ap.add_argument("code", help="mã project: chữ thường + số + gạch nối")
    ap.add_argument("--name", help="tên hiển thị (mặc định = code)")
    ap.add_argument("--prefix", help="service_prefix cho repo boundary (vd `cb` → cb-scheduling)")
    ap.add_argument("--target", help="thư mục đích (mặc định ../<code>)")
    ap.add_argument("--dry-run", action="store_true", help="in ra sẽ làm gì, không ghi")
    args = ap.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    if not CODE_RE.match(args.code):
        return die(f"mã project '{args.code}' không hợp lệ — chữ thường + số + gạch nối, 3-40 ký tự", 1)
    name = args.name or args.code
    target = Path(args.target).resolve() if args.target else (SRC.parent / args.code).resolve()
    if target == SRC:
        return die("đích trùng chính bộ khung — chọn thư mục khác", 1)

    n_files = sum(1 for _ in iter_files(SRC))
    print(f"Dựng project: {name}  ({args.code})")
    print(f"  khung  : {SRC}")
    print(f"  đích   : {target}")
    print(f"  copy   : {n_files} file (bỏ .git · archive · services · zip · changelog khung)")
    if args.dry_run:
        print("\nDRY RUN — không ghi gì.")
        return 0
    if target.exists() and any(target.iterdir()):
        return die(f"'{target}' đã tồn tại và không rỗng", 2)

    target.mkdir(parents=True, exist_ok=True)
    print(f"\n  ok  copy {copy_tree(target)} file")
    try:
        print(f"  ok  dọn {clean_artifacts(target)} (qua reset_for_new_project.py)")
    except RuntimeError as e:
        return die(f"dọn artifact thất bại:\n{e}", 3)
    set_identity(target, args.code, name, args.prefix)
    print(f"  ok  danh tính: project.id={args.code} · display_name={name!r} · prefix={args.prefix}")

    bad = verify(target)
    if bad:
        print("\nKIỂM TRA ĐỎ:", file=sys.stderr)
        for b in bad:
            print(f"  - {b}", file=sys.stderr)
        return 3
    print("  ok  kiểm tra: file bắt buộc đủ · STATE hợp lệ · stage=BOOTSTRAP · không sót vết cũ")
    print(f"  ok  git: {git_init(target, args.code)}")

    print(f"""
Xong. Bước kế:

  cd {target}
  pip install -r requirements-harness.txt
  py scripts/selftest_all.py        # xác nhận bộ khung lành
  claude
  /discover                         # pha khám phá — chỗ được hỏi nhiều nhất
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
