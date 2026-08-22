#!/usr/bin/env python3
"""decide.py — append 1 dòng vào tracking/decisions.md. Sổ quyết định, không phải nhật ký.

VÌ SAO CÓ FILE NÀY
    Agent gặp mơ hồ có ba đường: đoán im lặng (tệ nhất — không ai biết để soi), dừng hỏi (tốn một
    lần ngắt, và ở nửa sau tự động thì sub-agent không hỏi được ai), hoặc TỰ QUYẾT CÓ VẾT. File này
    làm đường thứ ba rẻ hơn hai đường kia.

    Trước đây tracking/decisions.md chỉ là sổ audit 3 cột cho force-bypass gate. Nó vẫn là thế, cộng
    thêm vai trò chính: mọi quyết định không hiển nhiên của cả vòng đời đổ về đây.

HAI CỘT LÀM NÊN GIÁ TRỊ CỦA SỔ
    --why  phải DẪN VỀ MỘT TÀI LIỆU (FEAT-…, BR-…, ADR-…, hld-…, PROJECT.md §…). Quyết định không
           dẫn được về tài liệu nào là quyết định bịa — và đó chính là thứ cần bị chặn, không phải
           thứ cần được ghi lại cho đẹp. Script từ chối nếu thiếu.
    --assume  điều đang tin là đúng mà CHƯA kiểm chứng. Đây là cột quan trọng nhất: nó chỉ đúng chỗ
           người review cần soi. Quyết định không mang giả định nào thì thường là quyết định hiển
           nhiên — mà hiển nhiên thì không cần ghi (xem --help mục "Khi nào KHÔNG ghi").

Usage:
  py scripts/decide.py --what "..." --why "... (FEAT-X-001 §3)" --assume "..." --reversible yes
  py scripts/decide.py --what "..." --why "..." --assume "..." --reversible hard --note "..."

Exit codes: 0 ghi xong · 1 thiếu vế bắt buộc (không ghi gì) · 2 sai tham số
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER = "tracking/decisions.md"

HEADER = (
    "# Decisions log\n\n"
    "> **Append-only.** Không sửa dòng cũ; quyết định mới đè quyết định cũ thì thêm dòng mới,\n"
    "> ghi `thay cho: <ngày>` ở cột Ghi chú.\n"
    ">\n"
    "> Sổ này là thứ **thay thế cho việc đoán im lặng**. Gặp mơ hồ → chọn phương án hợp lý nhất\n"
    "> **theo một tài liệu cụ thể** → ghi một dòng ở đây → đi tiếp.\n"
    ">\n"
    "> **Khi nào phải ghi:** mô hình dữ liệu, cách xử ca biên, phân quyền, đánh đổi hiệu năng,\n"
    "> chọn thư viện chính, cách hiểu một AC mơ hồ — bất cứ thứ gì mà ba ngày sau nhìn lại sẽ hỏi\n"
    "> \"sao lúc đó làm thế?\".\n"
    ">\n"
    "> **Khi nào KHÔNG ghi:** đặt tên biến, chia file, thư viện tiện ích nhỏ đổi lúc nào cũng được.\n"
    "> Ghi mọi thứ thì sổ thành nhật ký, không ai đọc, và mất luôn tác dụng.\n\n"
    "| Ngày | Stage · Wave | Quyết định | Lý do (dẫn về tài liệu) | Giả định đang mang | Đảo ngược được? | Ghi chú |\n"
    "|---|---|---|---|---|---|---|\n"
)

# Ref tài liệu chấp nhận được: ID artifact của harness, tên file .md, hoặc trích mục `§n`.
DOC_REF_RE = re.compile(
    r"\b(FEAT|EP|BR|ADR|CR|DR|JOURNEY|PS|CAP|TC|BUG|H)-[A-Za-z0-9-]+"
    r"|\b[A-Za-z0-9._-]+\.(md|ya?ml|json|css|html)\b"
    r"|§\s*\d"
    r"|\bhypothesis-log\b|\bcapability-map\b|\bpersona-pool\b|\bBOUNDARY-MAP\b|\bCHARTER\b",
    re.IGNORECASE,
)

REVERSIBLE = {
    "yes": "Có",
    "hard": "Khó",
    "no": "Không",
}


def _state() -> dict:
    try:
        return json.loads((REPO_ROOT / "harness" / "STATE.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _cell(s: str) -> str:
    """Một ô bảng markdown — `|` và xuống dòng phá bảng, và bảng vỡ thì phép đếm theo wave mù."""
    return " ".join((s or "").replace("|", "/").split())


def append(what: str, why: str, assume: str, reversible: str, note: str = "") -> str:
    st = _state()
    stage = st.get("stage") or "-"
    wave = (st.get("wave") or {}).get("id") or "-"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    path = REPO_ROOT / LEDGER
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        path.write_text(HEADER, encoding="utf-8")
    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
        path.write_text(text, encoding="utf-8")

    row = (f"| {ts} | {stage} · {wave} | {_cell(what)} | {_cell(why)} | "
           f"{_cell(assume)} | {REVERSIBLE.get(reversible, reversible)} | {_cell(note)} |\n")
    with path.open("a", encoding="utf-8") as f:
        f.write(row)
    return row


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(
        prog="decide.py",
        description="Ghi 1 quyết định vào tracking/decisions.md",
        epilog="Không dẫn được về tài liệu nào → chưa đủ căn cứ để tự quyết. Đọc lại spec, "
               "hoặc hỏi user nếu đang ở stage còn được hỏi.",
    )
    ap.add_argument("--what", required=True, help="quyết định, CỤ THỂ và làm được ('Xoá mềm cho đơn hàng')")
    ap.add_argument("--why", required=True, help="lý do — PHẢI dẫn về tài liệu (FEAT-…/ADR-…/hld-….md §3)")
    ap.add_argument("--assume", required=True, help="điều đang tin là đúng mà chưa kiểm chứng")
    ap.add_argument("--reversible", required=True, choices=sorted(REVERSIBLE),
                    help="yes = đổi lúc nào cũng được · hard = đổi được nhưng tốn (nói rõ ở --note) · no")
    ap.add_argument("--note", default="", help="ghi chú thêm; 'thay cho: <ngày>' nếu đè quyết định cũ")
    args = ap.parse_args(argv)

    errs: list[str] = []
    if len(args.what.strip()) < 10:
        errs.append("--what quá ngắn — viết quyết định cụ thể, làm được "
                    "('Xoá mềm cho đơn hàng', không phải 'cải thiện cách xoá')")
    if not DOC_REF_RE.search(args.why):
        errs.append(
            "--why không dẫn về tài liệu nào. Quyết định phải bám một artifact có thật: "
            "FEAT-…/BR-…/ADR-…/CR-… · tên file (hld-x.md, PROJECT.md) · hoặc trích mục (§3).\n"
            "  Không dẫn được về đâu = chưa đủ căn cứ để tự quyết: đọc lại spec, "
            "hoặc hỏi user nếu stage hiện tại còn được hỏi.")
    if len(args.assume.strip()) < 10:
        errs.append("--assume quá ngắn — đây là cột người review soi đầu tiên. "
                    "Thật sự không mang giả định nào thì quyết định đó hiển nhiên, không cần ghi.")
    if args.reversible == "hard" and not args.note.strip():
        errs.append("--reversible hard thì --note phải nói KHÓ Ở ĐÂU "
                    "(vd 'phải migrate dữ liệu người dùng đang có')")
    if errs:
        print("KHÔNG ghi — thiếu vế bắt buộc:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 1

    row = append(args.what, args.why, args.assume, args.reversible, args.note)
    print(f"OK: ghi vào {LEDGER}")
    print(row.rstrip())
    return 0


def _selftest() -> int:
    """Kiểm chính script: phải TỪ CHỐI đúng lý do, không chỉ từ chối."""
    import io
    import tempfile
    global REPO_ROOT
    saved = REPO_ROOT
    fails = []

    def run(args: list[str]) -> tuple[int, str]:
        buf = io.StringIO()
        old = sys.stderr
        sys.stderr = buf
        try:
            rc = main(args)
        except SystemExit as e:      # argparse
            rc = int(e.code or 0)
        finally:
            sys.stderr = old
        return rc, buf.getvalue()

    def check(label: str, cond: bool, detail: str = "") -> None:
        print(f"  {'ok  ' if cond else 'FAIL'} {label}" + ("" if cond else f"\n       {detail}"))
        if not cond:
            fails.append(label)

    ok = ["--what", "Xoá mềm cho đơn hàng thay vì xoá cứng",
          "--why", "AC-4 của FEAT-ORD-002 đòi huỷ nhầm phải khôi phục được",
          "--assume", "Lượng bản ghi nhỏ, không lo phình bảng trong wave này",
          "--reversible", "yes"]
    try:
        with tempfile.TemporaryDirectory() as td:
            REPO_ROOT = Path(td)
            rc, e = run(ok)
            check("dòng hợp lệ → ghi được", rc == 0, e)
            check("file có header + 1 dòng",
                  (REPO_ROOT / LEDGER).read_text(encoding="utf-8").count("\n| 2") == 1)

            bad_why = [a if a != "AC-4 của FEAT-ORD-002 đòi huỷ nhầm phải khôi phục được"
                       else "thấy làm thế hợp lý hơn" for a in ok]
            rc, e = run(bad_why)
            check("lý do không dẫn tài liệu → từ chối ĐÚNG lý do",
                  rc == 1 and "không dẫn về tài liệu" in e, e)

            rc, e = run(ok[:-1] + ["hard"])
            check("reversible=hard thiếu --note → từ chối đúng lý do",
                  rc == 1 and "KHÓ Ở ĐÂU" in e, e)

            rc, e = run(["--what", "abc", "--why", "FEAT-X-001", "--assume", "giả định đủ dài ở đây",
                         "--reversible", "yes"])
            check("--what quá ngắn → từ chối", rc == 1 and "--what quá ngắn" in e, e)

            rc, e = run(["--what", "Quyết định đủ dài để hợp lệ", "--why", "FEAT-X-001 §2",
                         "--assume", "ngắn", "--reversible", "yes"])
            check("--assume quá ngắn → từ chối", rc == 1 and "--assume quá ngắn" in e, e)

            n_before = (REPO_ROOT / LEDGER).read_text(encoding="utf-8").count("\n| 2")
            check("mọi lần từ chối đều KHÔNG ghi gì", n_before == 1)

            rc, _ = run(["--what", "Ô có dấu | gạch đứng trong nội dung", "--why", "hld-x.md §5",
                         "--assume", "bảng không được phép vỡ vì phép đếm theo wave đọc nó",
                         "--reversible", "yes"])
            last = (REPO_ROOT / LEDGER).read_text(encoding="utf-8").strip().splitlines()[-1]
            check("ô chứa `|` được làm sạch → bảng không vỡ", last.count("|") == 8, last)
    finally:
        REPO_ROOT = saved

    print()
    if fails:
        print(f"FAIL: decide.py selftest — {len(fails)} hỏng", file=sys.stderr)
        return 1
    print("OK: decide.py selftest passed")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    sys.exit(main())
