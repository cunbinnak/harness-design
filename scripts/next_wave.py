#!/usr/bin/env python3
"""next_wave.py — đóng wave N, mở wave N+1. KHÔNG RESET GÌ.

VÌ SAO CÓ FILE NÀY
    Trước đây đóng wave đi qua `done-wave` → reset STATE về BOOTSTRAP. Reset là mất trí nhớ giữa các
    wave: wave sau không biết wave trước đã giao gì, nên không "tôn trọng" được nó. Đổi sang mô hình
    vòng: tài liệu sống tiến hoá liên tục, KHÔNG file nào bị xoá — và hàng rào chống "gate wave mới
    xanh sẵn nhờ vết wave cũ" chuyển sang hai cơ chế:

      ĐÁNH DẤU   kết quả mang dấu wave lúc GHI (`test_result_wave`, `review_results_wave` ở
                 state.apply_effects), gate đối chiếu lúc ĐỌC (gates.results_stale). Fail-closed khi
                 thiếu dấu. → wave N+1 không thừa hưởng `pass` của wave N.
      SNAPSHOT   COPY **toàn bộ tài liệu + thực thi** của wave sang `archive/wave-N/`: `docs/**`
                 (đặc tả), `knowledge-base/`, `tracking/wave-N/` (thực thi), STATE + MATRIX +
                 decisions. Bản COPY chứ không phải tóm tắt agent viết — tóm tắt là lời kể, không
                 dùng làm hợp đồng được. Chép cả ĐẶC TẢ chứ không chỉ thực thi: wave sau lùi
                 `/domain` sửa FEAT thì bản wave cũ vẫn còn nguyên để đối chiếu.

    Sự TỒN TẠI của `archive/wave-N/` kiêm luôn **cờ "wave N đã đóng"** — chạy lần hai bị từ
    chối. Trước đây chỗ này chỉ có `teardown_ok`, một flag agent tự khai trong evidence.

LÀM GÌ
    1. Cờ đóng      → có archive/wave-N/ rồi thì TỪ CHỐI (đã đóng, đừng đóng lại)
    2. Snapshot     → copy docs/ + knowledge-base/ + tracking/wave-N/ + STATE/MATRIX/decisions
                      → archive/wave-N/   (chỉ copy, bản sống giữ nguyên)
    3. Capability   → capability-map §1: `Wave giao` khớp N → Trạng thái `đã giao`
    4. Mở wave kế   → wave.id/number + wave_boundaries + wave_features từ MATRIX
                      KHÔNG đụng: test_result/review_results (dấu wave lo) · decisions · bugs cũ ·
                      knowledge-base · mọi thứ trong docs/
    5. Hết wave     → báo là hết, KHÔNG tự mở

Usage:
  py scripts/next_wave.py            # xem trước, không ghi gì
  py scripts/next_wave.py --go
  py scripts/next_wave.py --selftest

Exit codes: 0 ok · 1 điều kiện chưa đạt · 2 sai tham số
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = "archive"
CAP_MAP = "docs/discovery/capability-map.md"


def _state_path() -> Path:
    return REPO_ROOT / "harness" / "STATE.json"


def load_state() -> dict:
    return json.loads(_state_path().read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    _state_path().write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def wave_num(state: dict) -> int | None:
    return (state.get("wave") or {}).get("number")


def archive_dir(n: int) -> Path:
    return REPO_ROOT / ARCHIVE / f"wave-{n:03d}"


def _matrix_boundaries() -> list[dict]:
    p = REPO_ROOT / "harness" / "SERVICE-BOUNDARY-MATRIX.json"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if isinstance(data, dict):
        return data.get("boundaries") or []
    return data if isinstance(data, list) else []


def boundaries_for(n: int) -> list[str]:
    out: list[str] = []
    for b in _matrix_boundaries():
        if b.get("wave") == n or n in (b.get("waves") or []):
            bid = b.get("id") or b.get("boundary")
            if bid and bid not in out:
                out.append(bid)
    return out


def features_for(n: int) -> list[str]:
    out: list[str] = []
    for b in _matrix_boundaries():
        if b.get("wave") == n or n in (b.get("waves") or []):
            for f in (b.get("features") or []):
                if f not in out:
                    out.append(f)
    return out


# Cái gì được đóng gói khi đóng wave. CHÉP HẾT, không chọn lọc — có chủ ý:
#
#   Chép `tracking/wave-N/` thôi là đóng gói phần THỰC THI mà bỏ phần ĐẶC TẢ. Lỗ nó để lại: wave 3
#   lùi `/domain` sửa `FEAT-A-001`, thì DELIVERED.md của wave 1 vẫn ghi "2/2 AC verified" nhưng AC
#   đã khác — lượt regression đi lại AC MỚI, không phải thứ wave 1 thật sự giao. Gói mà thiếu đặc
#   tả chỉ là cái nhãn.
#
#   "Chép doc nào" là đúng loại phán đoán sẽ mục: hôm nay đủ, thêm một loại artifact là sót. Cây
#   tài liệu ~0.5MB/wave nên chọn lọc không đổi lại được gì. Luật đơn giản, không drift.
SNAPSHOT_TREES = ("docs", "knowledge-base")
SNAPSHOT_FILES = ("harness/STATE.json", "harness/SERVICE-BOUNDARY-MATRIX.json",
                  "tracking/decisions.md")


def snapshot(n: int) -> tuple[int, Path]:
    """Đóng gói TOÀN BỘ tài liệu + thực thi của wave N → archive/wave-N/. Trả (số file, đích).

    Copy chứ không move: bản sống ở lại, lượt sửa và người đọc vẫn dùng đường cũ.
    Copy chứ không tóm tắt: wave sau cần bản gốc để biết wave trước hứa gì, không cần lời kể.
    """
    dst = archive_dir(n)
    dst.mkdir(parents=True, exist_ok=True)

    wave_src = REPO_ROOT / "tracking" / f"wave-{n:03d}"
    if wave_src.is_dir():
        shutil.copytree(wave_src, dst / "tracking" / wave_src.name)
    for tree in SNAPSHOT_TREES:
        src = REPO_ROOT / tree
        if src.is_dir():
            shutil.copytree(src, dst / tree)
    for rel in SNAPSHOT_FILES:
        src = REPO_ROOT / rel
        if src.is_file():
            out = dst / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, out)
    return sum(1 for p in dst.rglob("*") if p.is_file()), dst


def render_delivered(state: dict, n: int) -> tuple[str, int]:
    """Đóng gói FEAT/AC wave N đã giao → nội dung DELIVERED.md + số FEAT.

    ĐÂY LÀ HỢP ĐỒNG WAVE SAU PHẢI TÔN TRỌNG. Không có nó thì "wave sau không được làm gãy wave
    trước" là lời dặn: wave N+1 phải tự đi đọc plan + registry + report của mọi wave cũ mới biết
    cái gì từng chạy được — và sẽ không ai đọc.

    Máy DERIVE (`gates.derive_feature_states`: registry TC↔AC + report kết quả), KHÔNG phải agent tự
    khai. Agent khai "đã giao xong" thì file này chỉ ghi lại được lời khai.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import gates
    rows = gates.derive_feature_states(state, REPO_ROOT)
    done = [r for r in rows if r.get("state") == "passing"]
    other = [r for r in rows if r.get("state") not in ("passing", "deferred")]
    defer = [r for r in rows if r.get("state") == "deferred"]

    out = [
        f"# Wave {n} — đã giao",
        "",
        "> Sinh bằng máy khi đóng wave (derive từ `test-case-registry.md` + `test-report.md`),",
        "> KHÔNG phải agent tự khai. Đừng sửa tay — sửa thì nó thành lời kể.",
        ">",
        "> **Hợp đồng cho các wave sau:** mọi thứ trong bảng dưới phải GIỮ CHẠY ĐƯỢC.",
        "> `/dogfood` từ wave 2 trở đi đi lại đúng các luồng này (lượt regression); gãy vì code wave",
        "> mới là phát hiện nặng ngang gãy luồng lõi, không phải chuyện để lại sau.",
        "",
        f"Boundary: {', '.join(state.get('wave_boundaries') or []) or '—'}",
        "",
        "| FEAT | AC verified | TC đã verify | Trạng thái |",
        "|---|---|---|---|",
    ]
    for r in done + other:
        tcs = r.get("tcs") or []
        tc_txt = ", ".join(sorted(tcs)[:6]) + ("…" if len(tcs) > 6 else "") if tcs else "—"
        out.append(f"| {r.get('feat')} | {r.get('ac_pass')}/{r.get('ac_total')} | {tc_txt} "
                   f"| {r.get('state')} |")
    if not (done or other):
        out.append("| — | | | *(không FEAT nào in-scope)* |")
    if defer:
        out += ["", "**Hoãn sang wave sau** (khai deferred ở wave plan — KHÔNG phải hợp đồng):", ""]
        out += [f"- {r.get('feat')}" for r in defer]
    out.append("")
    return "\n".join(out), len(done) + len(other)


def mark_capabilities_delivered(n: int) -> int:
    """capability-map §1: dòng có `Wave giao` nhắc wave N → Trạng thái `đã giao`.

    Đây là thứ làm capability-map thành bảng SỐNG thay vì chết sau D1: trả lời được "còn bao nhiêu
    năng lực chưa giao" từ MỘT file, không phải đọc lại mọi wave.
    """
    p = REPO_ROOT / CAP_MAP
    if not p.is_file():
        return 0
    lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
    header: list[str] = []
    i_wave = i_stat = -1
    changed = 0
    for idx, raw in enumerate(lines):
        s = raw.strip()
        if not s.startswith("|"):
            header, i_wave, i_stat = [], -1, -1
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            low = [h.lower() for h in header]
            i_wave = next((k for k, h in enumerate(low) if "wave giao" in h), -1)
            i_stat = next((k for k, h in enumerate(low) if "trạng thái" in h), -1)
            continue
        if i_wave < 0 or i_stat < 0:
            header = cells
            continue
        if len(cells) <= max(i_wave, i_stat):
            continue
        # `1` · `1 (scaffold), 3 (đầy đủ)` — cắt lát được, nên khớp SỐ chứ không khớp chuỗi.
        if str(n) not in re.findall(r"\d+", cells[i_wave]):
            continue
        if cells[i_stat] == "đã giao":
            continue
        cells[i_stat] = "đã giao"
        lines[idx] = "| " + " | ".join(cells) + " |\n"
        changed += 1
    if changed:
        p.write_text("".join(lines), encoding="utf-8")
    return changed


BC_LEDGER = "tracking/BC-LEDGER.md"
PROD_READY = "tracking/PRODUCTION-READY.md"
PER_WAVE = "(mỗi wave)"


def rearm_marked(rel: str, marker: str) -> int:
    """Bỏ tick những dòng mang `marker` (vd `(mỗi wave)`). Trả số dòng đã bỏ tick.

    Chỉ đụng dòng CÓ marker — mục hạ tầng (HTTPS, backup, pipeline) không mang marker nên giữ tick:
    "đã kiểm cho code cũ" không tự thành "đã kiểm cho code mới", nhưng HTTPS thì không phải dựng lại
    mỗi wave.
    """
    p = REPO_ROOT / rel
    if not p.is_file():
        return 0
    out, n = [], 0
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.startswith("- [x]") and marker in line:
            line = "- [ ]" + line[5:]
            n += 1
        out.append(line)
    if n:
        p.write_text("\n".join(out) + "\n", encoding="utf-8")
    return n


def carry_open_findings(n: int) -> list[str]:
    """Mang phát hiện `chưa xử` của wave n sang report của wave n+1. Trả list mã đã mang.

    VÌ SAO — `dogfood-report.md` nằm trong `tracking/wave-N/`, đóng wave là nó vào `archive/` rồi
    không ai đọc nữa. Thứ ghi "chưa xử, sẽ làm" lặng lẽ biến mất đúng lúc đáng ra phải nhắc.

    Mang sang với ô `Xử` BỎ TRỐNG, không giữ nguyên `chưa xử`: gate `dogfood_done` của wave mới
    sẽ đỏ tới khi có người quyết LẠI. Giữ nguyên chữ "chưa xử" thì nó tự hoãn vô hạn — hai wave
    liền mang cùng một dòng nghĩa là nó không phải "chưa xử", nó là "wave sau" hoặc "không làm".
    """
    src = REPO_ROOT / "tracking" / f"wave-{n:03d}" / "dogfood-report.md"
    if not src.is_file():
        return []
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import gates

    rows = gates._parse_md_table_rows(gates.read_live(src), ("xử",))
    carried = [r for r in rows
               if (r.get("xử") or "").strip().lower().startswith("chưa xử")
               and (r.get("#") or "").strip() and "{{" not in (r.get("#") or "")]
    if not carried:
        return []

    dst_dir = REPO_ROOT / "tracking" / f"wave-{n + 1:03d}"
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / "dogfood-report.md"
    head = "" if dst.is_file() else (
        f"---\ntype: dogfood-report\nwave: \"wave-{n + 1:03d}\"\n---\n\n"
        f"# Dogfood — wave-{n + 1:03d}\n\n"
        "> Khuôn đầy đủ: `tracking/_templates/TEMPLATE.dogfood-report.md`. Lượt dogfood của wave này\n"
        "> **APPEND** vào bảng dưới, KHÔNG ghi đè file.\n")
    block = [
        "", f"## Mang sang từ wave {n}", "",
        f"> {len(carried)} phát hiện wave {n} ghi `chưa xử`. Ô `Xử` để TRỐNG có chủ ý — phải quyết",
        "> LẠI ở wave này (sửa ngay / wave sau), không được để nguyên chữ 'chưa xử' mà hoãn tiếp.",
        "", "| # | Lăng kính | FEAT/AC | Thao tác đã làm | Thấy gì trên màn hình | Xử | Ở đâu |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in carried:
        block.append("| {} | {} | {} | {} | {} |  | {} |".format(
            (r.get("#") or "").strip(), (r.get("lăng kính") or "").strip(),
            (r.get("feat/ac") or "").strip(), (r.get("thao tác đã làm") or "").strip(),
            (r.get("thấy gì trên màn hình") or "").strip(),
            f"mang sang từ wave {n}"))
    with dst.open("a", encoding="utf-8") as fh:
        fh.write(head + "\n".join(block) + "\n")
    return [(r.get("#") or "").strip() for r in carried]


def open_blockers() -> list[str]:
    """Dòng blocker còn `mở` trong tracking/blockers.md. Trả mô tả ngắn từng dòng.

    Sổ blocker KHÔNG bị reset khi mở wave (cùng lựa chọn với VIPER: `STATE.md` không reset nên
    bảng Blocker tự đi theo vòng). Đếm và **nhắc, không chặn** — một blocker treo qua wave là thứ
    đáng biết TRƯỚC khi cam kết scope wave mới, nhưng quyết định vẫn là của người.
    """
    f = REPO_ROOT / "tracking" / "blockers.md"
    if not f.is_file():
        return []
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import gates

    out = []
    for r in gates._parse_md_table_rows(gates.read_live(f), ("blocker", "trạng thái")):
        if (r.get("trạng thái") or "").strip().lower() != "mở":
            continue
        desc = (r.get("blocker") or "").strip()
        if desc and "{{" not in desc:
            out.append(f"{(r.get('wave') or '?').strip()}: {desc[:70]}")
    return out


def mark_decisions(next_n: int) -> bool:
    """Ghi mốc `(wave-N)` vào cuối decisions.md. Trả True nếu đã ghi.

    VÌ SAO — sổ quyết định là append-only và KHÔNG bị reset (đúng như wave trước). Không có mốc thì
    hai quyết định ghi ở wave 1 làm gate `decisions_min` xanh cho mọi wave về sau: sổ đầy mà wave 5
    chưa từng ghi dòng nào vẫn qua. Mốc biến "đếm cả sổ" thành "đếm dưới mốc cuối" — hàng rào
    đếm-theo-wave, cùng họ với dấu wave ở test_result và `Vòng mở` của VIPER.
    """
    f = REPO_ROOT / "tracking" / "decisions.md"
    if not f.is_file():
        return False
    wave = f"wave-{next_n:03d}"
    line = (f"| — | — | — MỐC — | quyết định của {wave} nằm DƯỚI dòng này "
            f"(gate `decisions_min` chỉ đếm dưới mốc cuối) | — | — | — |")
    body = f.read_text(encoding="utf-8")
    if line in body:
        return False
    with f.open("a", encoding="utf-8") as fh:
        fh.write(("" if body.endswith("\n") else "\n") + line + "\n")
    return True


def unplanned_deferrals(n: int) -> list[str]:
    """Dòng dogfood `wave sau` của wave n mà WAVE-SEQUENCE.md chưa nhắc tới. Trả list mã.

    VÌ SAO TÁCH ĐÔI — chỗ GHI và chỗ NHẬN không cùng một lúc mở:
      ghi   `tracking/wave-N/dogfood-report.md`  (không khoá, /dogfood ghi được ngay lúc thấy)
      nhận  `docs/plans/WAVE-SEQUENCE.md`        (phase-lock: chỉ mở ở PLAN/REVIEW)

    Bắt /dogfood ghi thẳng vào WAVE-SEQUENCE là ra luật không tuân thủ nổi — hook chặn ở
    MANUAL_TEST. Nên đối chiếu ở đây, lúc mở wave, và **cảnh báo chứ không chặn**: từ chối một
    phát hiện vẫn là quyền của người, nhưng từ chối trong im lặng thì wave sau không biết mình
    đứng trên nền gì. Muốn nhận thật thì lùi `/domain` (chốt chia-wave) — khoá mở ở đó.
    """
    src = REPO_ROOT / "tracking" / f"wave-{n:03d}" / "dogfood-report.md"
    seq = REPO_ROOT / "docs" / "plans" / "WAVE-SEQUENCE.md"
    if not src.is_file():
        return []
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import gates

    plan_txt = gates.read_live(seq) if seq.is_file() else ""
    out = []
    for r in gates._parse_md_table_rows(gates.read_live(src), ("xử",)):
        rid = (r.get("#") or "").strip()
        if not rid or "{{" in rid:
            continue
        if (r.get("xử") or "").strip().lower().startswith("wave sau") and rid not in plan_txt:
            out.append(rid)
    return out


def rearm_bc_ledger() -> int:
    """Bỏ tick ĐÚNG §3 của sổ tương thích ngược → wave nào rà wave đó. Trả số dòng đã bỏ tick.

    **§1 sổ hợp đồng KHÔNG BAO GIỜ bị đụng** — nó là registry sống, tích luỹ vĩnh viễn: surface
    wave 1 giao vẫn là hợp đồng ở wave 9. Chỉ mục RÀ (§3) mới re-arm.

    Giới hạn đúng §3 chứ không quét cả file: một checkbox ghi chú ở §1/§4 bị bỏ tick oan sẽ chặn
    đóng wave mà không chỗ nào re-arm lại nó (đây là lỗi VIPER từng vấp — selftest của họ có hẳn
    assert 'dòng tick ngoài §3 giữ nguyên').
    """
    p = REPO_ROOT / BC_LEDGER
    if not p.is_file():
        return 0
    out, inside, n = [], False, 0
    for line in p.read_text(encoding="utf-8").splitlines():
        if re.match(r"## 3(?!\d)", line):
            inside = True
        elif inside and line.startswith("## "):
            inside = False
        if inside and line.startswith("- [x]"):
            line = "- [ ]" + line[5:]
            n += 1
        out.append(line)
    if n:
        p.write_text("\n".join(out) + "\n", encoding="utf-8")
    return n


def checks(state: dict) -> tuple[list[str], int | None]:
    errs: list[str] = []
    n = wave_num(state)
    if n is None:
        errs.append("STATE chưa mở wave nào (wave.number = null) — không có gì để đóng")
        return errs, None
    if archive_dir(n).exists():
        errs.append(
            f"{ARCHIVE}/wave-{n:03d}/ đã tồn tại — wave {n} ĐÃ ĐÓNG rồi.\n"
            "    Sự tồn tại của thư mục này là cờ 'đã đóng' (chống đóng hai lần). "
            "Đóng lại sẽ ghi đè snapshot và mất vết wave đó."
        )
    return errs, n


def plan(n: int) -> tuple[list[str], bool]:
    nxt = n + 1
    bs = boundaries_for(nxt)
    return bs, bool(bs)


def do_go(state: dict, n: int) -> int:
    n_files, dst = snapshot(n)
    print(f"  ok  snapshot: copy {n_files} file → {dst.relative_to(REPO_ROOT).as_posix()}/ "
          "(bản sống giữ nguyên; thư mục này = cờ 'wave đã đóng')")

    body, n_feat = render_delivered(state, n)
    (dst / "DELIVERED.md").write_text(body, encoding="utf-8")
    print(f"  ok  đóng gói {n_feat} FEAT + AC đã verify → {dst.name}/DELIVERED.md "
          "(hợp đồng wave sau phải giữ chạy được)")

    n_cap = mark_capabilities_delivered(n)
    if n_cap:
        print(f"  ok  capability-map: {n_cap} năng lực → 'đã giao'")

    n_bc = rearm_bc_ledger()
    if n_bc:
        print(f"  ok  sổ tương thích ngược: bỏ tick {n_bc} mục §3 — wave mới rà lại "
              "(§1 sổ hợp đồng GIỮ NGUYÊN, tích luỹ vĩnh viễn)")

    blk = open_blockers()
    if blk:
        print(f"  !!  còn {len(blk)} blocker đang MỞ, mang sang wave {n + 1}:")
        for b in blk[:5]:
            print(f"        {b}")
        print("      Sổ blocker không bị reset. Gỡ hoặc đóng trước khi cam kết scope wave "
              "mới — không chặn, nhưng cam kết trên nền còn tắc thì wave mới tắc theo.")

    if mark_decisions(n + 1):
        print(f"  ok  decisions: ghi mốc wave {n + 1} — gate `decisions_min` chỉ đếm "
              "dưới mốc cuối, quyết định wave cũ không xanh hộ wave mới")

    unplanned = unplanned_deferrals(n)
    if unplanned:
        print(f"  !!  dogfood: {len(unplanned)} phát hiện đẩy `wave sau` mà WAVE-SEQUENCE.md "
              f"CHƯA nhắc tới ({', '.join(unplanned[:6])}).")
        print("      Đẩy sang wave sau mà không có chỗ nhận thì là bỏ đi, chỉ gọi tên khác thôi.")
        print("      Muốn nhận thật → lùi `/domain` (chốt chia-wave) thêm vào WAVE-SEQUENCE; "
              "`docs/plans/**` chỉ mở khoá ở đó.")
        print("      Không chặn — từ chối là quyền của bạn, nhưng từ chối trong im lặng thì "
              "wave sau không biết mình đứng trên nền gì.")

    carried = carry_open_findings(n)
    if carried:
        print(f"  ok  dogfood: mang {len(carried)} phát hiện `chưa xử` sang wave {n + 1} "
              f"({', '.join(carried[:6])}) — ô `Xử` để trống, phải quyết LẠI. "
              "Không mang thì thứ ghi 'sẽ làm' biến mất cùng lúc wave đóng")

    n_pr = rearm_marked(PROD_READY, PER_WAVE)
    if n_pr:
        print(f"  ok  sẵn sàng vận hành: bỏ tick {n_pr} mục '{PER_WAVE}' — đầu vào mới cần "
              "validate mới, hành động mới cần thử phân quyền mới (hạ tầng giữ tick)")

    bs, has_next = plan(n)
    if not has_next:
        print(f"\n  Hết WAVE-SEQUENCE — wave {n} là wave cuối. KHÔNG tự mở wave mới.")
        print("  Còn phát hiện `wave sau` chưa được nhận → lùi `/domain` (chốt chia-wave) "
              "để thêm vào WAVE-SEQUENCE.md.")
        return 0

    nxt = n + 1
    state["wave"] = {"id": f"wave-{nxt:03d}", "number": nxt}
    state["wave_boundaries"] = bs
    state["wave_features"] = features_for(nxt)
    state["active_boundary"] = None
    save_state(state)

    print(f"  ok  mở wave {nxt}: boundary={bs} · feature={len(state['wave_features'])}")
    print(f"""
Wave {nxt} đã mở — KHÔNG file nào bị reset, vết wave {n} nằm nguyên tại chỗ.

  Giữ nguyên : tracking/wave-{n:03d}/ (bản sống) · decisions.md · knowledge-base/ · toàn bộ docs/
  Đỏ lại     : test_result + review_results mang dấu wave-{n:03d} → gate wave {nxt} không tính
               (không phải bị xoá — bị ĐỐI CHIẾU; chạy lại cho wave {nxt} là xanh)
  Tôn trọng  : luồng lõi wave ≤{n} phải giữ chạy được — dogfood đọc
               {ARCHIVE}/wave-*/DELIVERED.md cho lượt regression

  Tiếp: /run-wave""")
    return 0


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(prog="next_wave.py",
                                 description="Đóng wave N, mở wave N+1 — không reset gì")
    ap.add_argument("--go", action="store_true", help="thực thi (mặc định chỉ xem trước)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return _selftest()

    state = load_state()
    n = wave_num(state)
    print(f"=== đóng wave {n}, mở wave {(n + 1) if n else '?'} ==="
          + ("" if args.go else "  (xem trước, chưa ghi gì)"))
    errs, n = checks(state)
    if errs:
        for e in errs:
            print(f"  x  {e}", file=sys.stderr)
        return 1
    assert n is not None
    if not args.go:
        bs, has_next = plan(n)
        print(f"""  ok  điều kiện đủ. Chạy với --go sẽ (KHÔNG reset gì):
      copy tracking/wave-{n:03d}/ → {ARCHIVE}/wave-{n:03d}/   (cờ 'đã đóng')
      capability-map: năng lực của wave {n} → 'đã giao'
      {'mở wave ' + str(n + 1) + ': boundary=' + str(bs) if has_next else 'hết WAVE-SEQUENCE — không mở wave mới'}""")
        return 0
    return do_go(state, n)


def _selftest() -> int:
    """Assert cái quan trọng nhất: sau khi mở wave mới, GATE PHẢI ĐỎ LẠI.

    Không có assert này thì mọi thứ ở trên chỉ là lời hứa — đúng bài học từ selftest test_repeat của
    VIPER, nơi ba dòng assert 'gate V/E/P1 ĐỎ lại sau khi mở vòng' mới là mục đích của cả cơ chế
    snapshot + đánh dấu.
    """
    import tempfile
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import gates
    global REPO_ROOT
    saved = REPO_ROOT
    fails: list[str] = []

    def check(label: str, cond: bool, detail: str = "") -> None:
        print(f"  {'ok  ' if cond else 'FAIL'} {label}" + ("" if cond else f"\n       {detail}"))
        if not cond:
            fails.append(label)

    try:
        with tempfile.TemporaryDirectory() as td:
            REPO_ROOT = Path(td)
            (REPO_ROOT / "tracking" / "wave-001").mkdir(parents=True)
            (REPO_ROOT / "tracking" / "wave-001" / "test-report.md").write_text("x", encoding="utf-8")
            (REPO_ROOT / "tracking" / "wave-001" / "test-report.md").write_text("y", encoding="utf-8")

            st = {"wave": {"id": "wave-001", "number": 1},
                  "wave_boundaries": ["payment"],
                  "test_result": "pass", "test_result_wave": "wave-001",
                  "review_results": [{"boundary": "payment", "review_result": "pass",
                                      "coverage_pct": 95}],
                  "review_results_wave": "wave-001"}

            check("wave 1: gate xanh với kết quả của chính nó",
                  gates.check_test_passed(st)[0] and
                  gates.check_all_boundaries_reviewed(st, {}, root=REPO_ROOT)[0])

            # ĐẶC TẢ phải được chép cùng thực thi — đây là chỗ suýt sót: chép mỗi tracking/ thì
            # wave sau lùi sửa FEAT là bản wave cũ mất, DELIVERED.md thành cái nhãn không đối chiếu được.
            (REPO_ROOT / "docs" / "architecture" / "feat").mkdir(parents=True)
            (REPO_ROOT / "docs/architecture/feat/FEAT-A-001.md").write_text(
                "### AC-1\n### AC-2\n", encoding="utf-8")
            n_files, dst = snapshot(1)
            check("snapshot chép cả THỰC THI lẫn ĐẶC TẢ (bản sống còn nguyên)",
                  (dst / "tracking/wave-001/test-report.md").is_file()
                  and (dst / "docs/architecture/feat/FEAT-A-001.md").is_file()
                  and (REPO_ROOT / "tracking/wave-001/test-report.md").is_file()
                  and (REPO_ROOT / "docs/architecture/feat/FEAT-A-001.md").is_file(),
                  f"n_files={n_files}, có: {[p.name for p in dst.rglob('*') if p.is_file()]}")

            # Lùi sửa FEAT sau khi đóng wave → bản wave cũ trong archive KHÔNG đổi theo.
            (REPO_ROOT / "docs/architecture/feat/FEAT-A-001.md").write_text(
                "### AC-1\n### AC-2\n### AC-3-them-o-wave-sau\n", encoding="utf-8")
            check("sửa FEAT ở wave sau KHÔNG đụng bản đã đóng gói",
                  "AC-3" not in (dst / "docs/architecture/feat/FEAT-A-001.md").read_text(
                      encoding="utf-8"))

            errs, _ = checks(st)
            check("cờ 'đã đóng': đóng lần hai bị TỪ CHỐI",
                  any("ĐÃ ĐÓNG" in e for e in errs), str(errs))

            # Đóng gói FEAT/AC: derive từ registry+report, KHÔNG phải agent khai.
            (REPO_ROOT / "tracking/wave-001/test-case-registry.md").write_text(
                "| TC | Feature | AC | type |\n|---|---|---|---|\n"
                "| TC-01 | FEAT-A-001 | AC-1 | auto |\n"
                "| TC-02 | FEAT-A-001 | AC-2 | auto |\n", encoding="utf-8")
            (REPO_ROOT / "tracking/wave-001/test-report.md").write_text(
                "| TC | Result |\n|---|---|\n| TC-01 | pass |\n| TC-02 | pass |\n",
                encoding="utf-8")
            st_f = dict(st); st_f["wave_features"] = ["FEAT-A-001"]
            body, n_feat = render_delivered(st_f, 1)
            check("DELIVERED.md đóng gói được FEAT của wave",
                  n_feat == 1 and "FEAT-A-001" in body, body[:300])
            check("DELIVERED.md nêu rõ là hợp đồng wave sau phải giữ",
                  "GIỮ CHẠY ĐƯỢC" in body and "regression" in body)

            # Mở wave 2 kiểu KHÔNG RESET — chỉ đổi con trỏ wave, giữ nguyên mọi kết quả cũ.
            st2 = dict(st)
            st2["wave"] = {"id": "wave-002", "number": 2}
            ok_t, msg_t = gates.check_test_passed(st2)
            ok_r, msg_r = gates.check_all_boundaries_reviewed(st2, {}, root=REPO_ROOT)
            check("wave 2: test_passed ĐỎ LẠI (không thừa hưởng wave 1)",
                  not ok_t and "wave-001" in msg_t, msg_t)
            check("wave 2: all_boundaries_reviewed ĐỎ LẠI",
                  not ok_r and "wave-001" in msg_r, msg_r)

            st3 = dict(st2); st3["test_result_wave"] = "wave-002"
            check("wave 2: chạy lại test cho wave này → xanh",
                  gates.check_test_passed(st3)[0])

            st4 = {k: v for k, v in st.items() if not k.endswith("_wave")}
            check("STATE thiếu dấu wave → FAIL-CLOSED (không cho qua)",
                  not gates.check_test_passed(st4)[0])

            # capability-map: cắt lát `1 (scaffold), 3 (đầy đủ)` phải khớp theo SỐ
            cap = REPO_ROOT / CAP_MAP
            cap.parent.mkdir(parents=True, exist_ok=True)
            cap.write_text(
                "## 1. x\n\n| # | Capability | Wave giao | Trạng thái |\n|---|---|---|---|\n"
                "| C1 | a | 1 | chưa giao |\n"
                "| C2 | b | 1 (scaffold), 3 (đầy đủ) | chưa giao |\n"
                "| C3 | c | 2 | chưa giao |\n", encoding="utf-8")
            n_cap = mark_capabilities_delivered(1)
            body = cap.read_text(encoding="utf-8")
            check("capability-map: đánh dấu đúng 2 dòng của wave 1 (kể cả dòng cắt lát)",
                  n_cap == 2, f"changed={n_cap}")
            check("capability-map: dòng wave 3 KHÔNG bị đụng",
                  "| C3 | c | 2 | chưa giao |" in body, body)

            # Sổ tương thích ngược: §3 re-arm, §1 sổ hợp đồng TÍCH LUỸ vĩnh viễn.
            bc = REPO_ROOT / BC_LEDGER
            bc.write_text(
                "## 1. Sổ hợp đồng\n\n- [x] surface wave 1 đã ghi\n\n"
                "## 3. Checklist rà mỗi wave\n\n- [x] API\n- [x] DB\n\n"
                "## 4. Bỏ qua\n\n- [x] ghi chú ngoài §3\n", encoding="utf-8")
            n_bc = rearm_bc_ledger()
            after = bc.read_text(encoding="utf-8")
            check("BC §3: bỏ tick đúng 2 mục rà", n_bc == 2, f"n={n_bc}")
            check("BC §1 sổ hợp đồng GIỮ NGUYÊN (tích luỹ vĩnh viễn)",
                  "- [x] surface wave 1 đã ghi" in after, after)
            check("BC: tick NGOÀI §3 giữ nguyên (re-arm không quét cả file)",
                  "- [x] ghi chú ngoài §3" in after, after)

            # Sẵn sàng vận hành: mục "(mỗi wave)" re-arm, hạ tầng giữ tick.
            pr = REPO_ROOT / PROD_READY
            pr.write_text(
                "## Nhóm 1\n\n- [x] **Validate đầu vào** `(mỗi wave)` — abc\n"
                "- [x] **HTTPS** `(sau môi trường thật)`\n- [x] **Backup** — hạ tầng\n",
                encoding="utf-8")
            n_pr = rearm_marked(PROD_READY, PER_WAVE)
            after_pr = pr.read_text(encoding="utf-8")
            check("sẵn-sàng: bỏ tick đúng 1 mục '(mỗi wave)'", n_pr == 1, f"n={n_pr}")
            check("sẵn-sàng: hạ tầng GIỮ tick (HTTPS dựng một lần, không dựng lại mỗi wave)",
                  "- [x] **HTTPS**" in after_pr and "- [x] **Backup**" in after_pr, after_pr)
            check("sẵn-sàng: thiếu file thì im lặng, không nổ",
                  rearm_marked("tracking/KHONG-CO.md", PER_WAVE) == 0)
    finally:
        REPO_ROOT = saved

    print()
    if fails:
        print(f"FAIL: next_wave selftest — {len(fails)} hỏng", file=sys.stderr)
        return 1
    print("OK: next_wave selftest passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
