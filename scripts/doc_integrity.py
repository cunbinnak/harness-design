#!/usr/bin/env python3
"""doc_integrity.py — chống tài liệu TRÔI khỏi code.

VÌ SAO CÓ FILE NÀY
    Tài liệu trôi tệ hơn tài liệu thiếu: người đọc TIN nó. Phiên gộp lệnh 26→7 để lại 130 tham
    chiếu chết trong skill/command/router, một bảng gate chép tay thiếu 6 gate, và một gate viết
    xong mà chưa nối dispatch — không selftest nào bắt được vì tất cả đều nằm trong văn xuôi.

    File này biến các phép soi đó thành lệnh chạy được. Sửa lệnh/gate xong thì chạy nó TRƯỚC khi
    nói là xong.

Usage: py scripts/doc_integrity.py
Exit: 0 sạch · 1 có chỗ trôi
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

# QUÉT RỘNG có chủ ý. Bản trước chỉ soi router + lệnh + skill + agent, nên `docs/**` và
# `tracking/_templates/**` nằm ngoài tầm — và 20 chỗ `apply-cr` sống trong đó qua nhiều lượt quét
# báo sạch. Template là thứ project mới CHÉP RA DÙNG: lệnh ma ở đó lan sang mọi project sau.
SURFACES = ["CLAUDE.md", "README.md", "SETUP-GUIDE.md", "AGENTS.md",
            "harness", "commands", ".claude/skills", "agents",
            "docs", "tracking", "knowledge-base", "handoff",
            # scripts không phải tài liệu người đọc, nhưng chuỗi trong đó ĐƯỢC NHỒI vào prompt của
            # sub-agent (build_prompt) và vào thông báo chặn của hook (policies) — lệnh ma ở đây
            # tệ hơn ở README: agent đọc rồi tin là có lệnh đó để gọi.
            "scripts"]
# Câu khai SỐ LƯỢNG lệnh. Bắt hẹp — chỉ ba dạng người thật viết — vì đây là chỗ dễ báo oan nhất
# (tài liệu đầy "7 chốt", "17 state", "2 lớp doc"). Báo oan một lần là công cụ bị tắt.
COUNT_CLAIM = re.compile(
    r"\*\*(\d+)\s+lệnh[.\s]*\*\*"               # **7 lệnh**  ·  **10 lệnh.**
    r"|\*\*(\d+)\s+commands?\*\*"               # **7 commands**
    r"|\b(\d+)\s+slash\s+commands?\b"           # 19 slash commands
    r"|\((\d+)\s+commands?,",                   # (24 commands, 17 states)
    re.IGNORECASE)
# Chỉ soi tên lệnh ĐÃ XOÁ — không cố đoán "mọi slash command", vì tài liệu đầy path
# (`/health`, `/gradlew`, `/app`) và đoán rộng thì báo oan; công cụ báo oan sẽ bị tắt.
RETIRED = (
    "discovery-start", "discovery-end", "domain-po", "domain-ba", "domain-approve",
    "domain-translate", "domain-end", "design", "design-ux", "design-end", "plan",
    "review-document", "start-wave", "start-dev", "review-dev", "dev-handoff",
    "test-plan", "test-execute", "log-bug", "fix-bugs", "end-wave", "done-wave",
    "apply-cr", "decide", "validate",
)
# Lookbehind CHỈ loại `\w` và `-` (chặn `docs/design`, `x-/plan`). KHÔNG loại backtick:
# `/apply-cr` trong nháy ngược là cách viết PHỔ BIẾN NHẤT của lệnh trong tài liệu, loại nó ra làm
# công cụ mù đúng chỗ cần soi nhất — đo được 20 chỗ `apply-cr` sống sót qua ba lượt quét chỉ vì
# một ký tự backtick đứng trước.
SLASH = re.compile(r"(?<![\w-])/(" + "|".join(sorted(RETIRED, key=len, reverse=True)) + r")\b")
# Cột đầu có thể gộp nhiều tên (`| `/design` · `/plan` · `/review-document` | … |`).
MIGRATION_ROW = re.compile(r"^\s*\|\s*`/[a-z-]+`(?:\s*[·,]\s*`/[a-z-]+`)*\s*\|")
GATEISH = re.compile(r"`([a-z_]{4,})`")
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
GATE_SUFFIX = ("_proof", "_gate", "_present", "_passed", "_compat", "_decided",
               "_scope", "_stamped", "_jargon", "_parity", "_styling", "_compliance",
               "_coherence", "_transport")
# Field của RETURN SCHEMA / evidence — trông giống tên gate nhưng không phải.
NOT_GATES = {"open_findings", "files_changed", "needs_review", "test_result", "review_result"}


SELF = Path(__file__).name


def _files(py: bool = True) -> list[Path]:
    """File cần soi. `py=False` → chỉ .md.

    File .py bị soi HẸP HƠN .md: chỉ tìm lệnh ma, không tìm tên gate hay link. Lý do: `gates.py` là
    NƠI ĐỊNH NGHĨA gate, còn chuỗi trong code đầy `path`/regex trông giống tên gate — soi rộng ở đó
    chỉ đẻ dương tính giả, mà công cụ báo oan thì bị tắt.

    Bỏ qua chính file này: nó buộc phải chứa cả danh sách RETIRED, soi vào là tự báo mình.
    """
    out: list[Path] = []
    for s in SURFACES:
        p = ROOT / s
        if p.is_file():
            out.append(p)
        elif p.is_dir():
            out += [f for f in p.rglob("*.md") if "__pycache__" not in f.parts]
            if py:
                out += [f for f in p.rglob("*.py")
                        if "__pycache__" not in f.parts and f.name != SELF]
    return out


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    import gates

    commands = {p.stem for p in (ROOT / "commands").glob("*.md") if p.stem != "README"}
    harness_ids = set(gates.GATE_RULES)
    # HAI tập tách bạch — gộp làm một là tự đẻ dương tính giả:
    #   gate_kinds : dùng cho phép kiểm DISPATCH (chỉ `kind` mới cần nhánh dispatch)
    #   doc_allow  : dùng cho phép kiểm TÀI LIỆU (kind + evidence field + field RETURN SCHEMA —
    #                `uat_signed`, `open_findings`… trông giống tên gate nhưng không phải)
    gate_kinds = {r["kind"] for rs in gates.GATE_RULES.values() for r in rs}
    doc_allow = gate_kinds | NOT_GATES | {
        r["field"] for rs in gates.GATE_RULES.values() for r in rs if "field" in r}
    src = (ROOT / "scripts" / "gates.py").read_text(encoding="utf-8")
    dispatched = set(re.findall(r'if kind == "(\w+)"', src))
    defined = set(re.findall(r"^def (check_\w+)", src, re.M))

    problems: list[str] = []

    # 1. slash command nhắc trong tài liệu nhưng KHÔNG có file lệnh
    for f in _files():
        rel = f.relative_to(ROOT).as_posix()
        text = f.read_text(encoding="utf-8", errors="ignore")
        for n, line in enumerate(text.splitlines(), 1):
            # Dòng bảng migration: tên lệnh cũ đứng ở CỘT ĐẦU (`| `/x` | giờ ở đâu |`) —
            # ở đó nó là CHỦ NGỮ chứ không phải lời khuyên dùng lệnh đó.
            if ("không còn là lệnh" in line.lower() or "Cũ | Giờ ở đâu" in line
                    or MIGRATION_ROW.match(line)):
                continue
            for name in SLASH.findall(line):
                problems.append(f"[lệnh ma] {rel}:{n} → /{name} (đã gộp/xoá)")

    # 2. tên gate nhắc trong tài liệu nhưng không có trong GATE_RULES (CHỈ .md)
    for f in _files(py=False):
        rel = f.relative_to(ROOT).as_posix()
        text = f.read_text(encoding="utf-8", errors="ignore")
        for n, line in enumerate(text.splitlines(), 1):
            for tok in GATEISH.findall(line):
                kind = tok[len("check_"):] if tok.startswith("check_") else tok
                if kind.endswith(GATE_SUFFIX) and kind not in doc_allow:
                    problems.append(f"[gate ma] {rel}:{n} → {tok}")

    # 3. gate khai trong GATE_RULES mà không có nhánh dispatch (và ngược lại)
    for k in sorted(gate_kinds - dispatched):
        problems.append(f"[gate không dispatch] {k}")
    # 4. hàm check_* viết mà không ai gọi → code chết trông như gate sống
    for fn in sorted(defined):
        if len(re.findall(rf"\b{fn}\(", src)) <= 1:
            problems.append(f"[gate chết] {fn} — viết mà không ai gọi")

    # 5. con số "N lệnh" khai trong văn xuôi ≠ số file lệnh thật
    #    Gộp lệnh 26→7 để lại "10 lệnh" ở CLAUDE.md và "24 commands"/"19 slash commands" ở
    #    README — không phép kiểm nào thấy, vì con số nằm trong câu văn chứ không phải trong
    #    danh sách. Người đọc TIN con số đó rồi đi tìm 10 lệnh.
    for f in _files():
        rel = f.relative_to(ROOT).as_posix()
        for n, line in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            for m in COUNT_CLAIM.finditer(line):
                claimed = int(next(g for g in m.groups() if g))
                if claimed != len(commands):
                    problems.append(f"[số lệnh sai] {rel}:{n} → khai {claimed}, "
                                    f"thật có {len(commands)}")

    # 6. link markdown trỏ tới file KHÔNG tồn tại
    #    `agents/README.md` còn trỏ `apply-cr-agent.md` sau khi agent đó bị xoá — link chết là
    #    dạng trôi khó thấy nhất: người đọc bấm vào mới biết, agent thì đọc thấy tên rồi tin là có.
    for f in _files(py=False):
        rel = f.relative_to(ROOT).as_posix()
        text = f.read_text(encoding="utf-8", errors="ignore")
        for n, line in enumerate(text.splitlines(), 1):
            for target in LINK_RE.findall(line):
                if target.startswith(("http", "#", "mailto:")):
                    continue
                t = target.split("#")[0].strip()
                if not t or "{" in t or "<" in t or "*" in t:
                    continue  # placeholder trong template, không phải link thật
                if not (f.parent / t).exists():
                    problems.append(f"[link chết] {rel}:{n} → {t}")

    # 7. Skill TRÙNG TÊN CHỐT mà mô tả không nói ai sở hữu.
    #    Claude Code liệt kê skill trong menu `/`, nên `domain-po` hiện lên y hệt một slash command
    #    — người dùng gõ `/domain-po` tưởng đang chạy chốt, thực ra chỉ nạp checklist vào phiên
    #    chính. Không đổi được tên (build_prompt + agent trỏ vào), nên bắt MÔ TẢ phải tự khai:
    #    dòng đầu tiên người đọc thấy trong menu phải nói ngay nó là skill của agent nào.
    for sk in sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md")):
        name = sk.parent.name
        if name not in harness_ids and name.replace("translator", "translate") not in harness_ids:
            continue
        head = sk.read_text(encoding="utf-8", errors="ignore")[:900]
        if "Skill của" not in head:
            problems.append(
                f"[skill trùng tên chốt] {name} — mô tả không khai chủ sở hữu; thêm tiền tố "
                '"Skill của <agent> (chốt X trong /<lệnh>) — " để menu `/` không đọc nhầm là lệnh')

    # 8. TEMPLATE mồ côi — không tài liệu/script nào nhắc tên nó
    #    Template không ai gọi là chỗ trốn kỹ nhất của rác: nó không gây lỗi, không ai xoá, và
    #    lần sau có người chép nhầm bản đã chết. (`TEMPLATE.local-dev.md` nằm im như vậy 3 tháng.)
    tpl_names = {p.name for p in ROOT.rglob("TEMPLATE.*")
                 if ".git" not in p.parts and "archive" not in p.parts}
    corpus = []
    for p in ROOT.rglob("*"):
        if not p.is_file() or ".git" in p.parts or "archive" in p.parts:
            continue
        if p.suffix not in (".md", ".py", ".json", ".yaml", ".yml"):
            continue
        if p.name in tpl_names:
            continue                       # template không tự chứng minh mình còn sống
        if p.name == "HARNESS-CHANGELOG.md":
            continue                       # changelog là LỊCH SỬ, không phải tham chiếu sống:
                                           # "từng có" không chứng minh "đang dùng"
        try:
            corpus.append(p.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            pass
    joined = "\n".join(corpus)
    for name in sorted(tpl_names):
        if name in joined:
            continue
        # Dạng gộp `TEMPLATE.service-repo-{CLAUDE.md,settings.json,gitignore}` — khớp tên nguyên
        # văn không thấy. Nhận cả tiền tố tới dấu `-` cuối, đứng ngay trước `{`.
        pre = name.rsplit("-", 1)[0] + "-"
        if "-" in name and (pre + "{") in joined:
            continue
        problems.append(f"[template mồ côi] {name} — không chỗ nào nhắc tên; xoá hoặc nối vào flow")

    # 8. command file trên đĩa nhưng chưa sync sang .claude/commands
    synced = {p.stem for p in (ROOT / ".claude" / "commands").glob("*.md")}
    for c in sorted(commands - synced):
        problems.append(f"[chưa sync] commands/{c}.md — chạy py scripts/sync_commands.py")

    if problems:
        # In theo NHÓM, và luôn in đủ bảng tổng. Cắt phẳng ở 40 dòng thì phần bị cắt đọc như
        # "hết rồi" — đúng cái bẫy im-lặng-mà-tưởng-đã-phủ.
        import collections
        by_file: dict[str, list[str]] = collections.defaultdict(list)
        for p in problems:
            m = re.search(r"\] ([^:\s]+)", p)
            by_file[m.group(1) if m else "(chung)"].append(p)
        print(f"TRÔI: {len(problems)} chỗ, {len(by_file)} file\n", file=sys.stderr)
        for rel, items in sorted(by_file.items(), key=lambda kv: -len(kv[1])):
            print(f"  {rel}  ({len(items)})", file=sys.stderr)
            for p in items[:6]:
                print("      " + p[p.index("]") + 2:], file=sys.stderr)
            if len(items) > 6:
                print(f"      … {len(items) - 6} chỗ nữa trong file này", file=sys.stderr)
        return 1
    print(f"OK: doc_integrity — {len(commands)} lệnh · {len(gate_kinds)} gate, không chỗ nào trôi")
    return 0


if __name__ == "__main__":
    sys.exit(main())
