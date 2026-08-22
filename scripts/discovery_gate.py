"""
discovery_gate.py — Exit gate cho mỗi DISCOVERY sub-wave D0-D3 (cloned từ ZIP discovery-gate.py).

Scope harness: clone tối giản D0-D2 + charter (D3). Bỏ D3.5/D4/D5/D6/D7 (plumbing multi-repo).

Usage:
  py scripts/discovery_gate.py <D-wave>   # D0 | D1 | D2 | D3
  py scripts/discovery_gate.py --all

Exit codes:
  0 — gate pass (đủ artifact để transition sang D{N+1})
  1 — gate fail (artifact missing / dưới minimum count)
  2 — usage error (D-wave invalid)

Strictness: BẰNG CHỨNG, không phải hình dạng. Trước đây gate chỉ đếm ">20 ký tự sau khi bỏ
placeholder" — một đoạn văn xuôi trừu tượng ("người dùng hay gặp khó khăn khi nhập đơn") thừa sức
qua, nên gate xanh mà buổi khai thác vẫn hời hợt. Nay §2/§3 của D0 đòi dòng `Bằng chứng:` không rỗng
(câu chuyện thật / con số / hiện vật) và §6 đòi bảng lỗ hổng — thứ chỉ có nếu thật sự đã hỏi.

Path harness: docs/discovery/* (ZIP dùng _discovery/*). Root = repo root (parent của scripts/).

Dùng bởi gates.py: kind=discovery_advance (discovery-start tiến wave → gate wave đang rời) +
kind=discovery_wave (discovery-end chốt D3 → check_gate('D3')); fail → block transition.

Self-test: py scripts/discovery_gate.py --selftest
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parent.parent
DISC = "docs/discovery"

# Placeholder chưa điền, hai kiểu template dùng: `_TBD_`/`_PLAN_` và `{{…}}`.
PLACEHOLDER_RE = re.compile(r"_[A-Z]+_|\{\{[^}]*\}\}")
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


# ---------- Helpers ----------

def file_exists(rel: str) -> bool:
    return (REPO_ROOT / rel).exists()


def file_nonempty(rel: str) -> bool:
    p = REPO_ROOT / rel
    return p.exists() and p.stat().st_size > 0


def read(rel: str) -> str:
    p = REPO_ROOT / rel
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="ignore")


def read_live(rel: str) -> str:
    """Nội dung THẬT — đã bỏ khối <!-- -->.

    Template để dòng MẪU trong comment cho người điền dễ bắt chước. Không bỏ chúng ra thì mọi phép
    đếm đều tính cả ví dụ, và gate xanh khi chưa ai viết gì. Mọi phép đếm dưới đây phải đi qua hàm
    này — thêm phép đếm mới mà đọc read() thẳng là mở lại đúng lỗ vừa vá.
    """
    return COMMENT_RE.sub("", read(rel))


def has_placeholder(text: str) -> bool:
    return bool(PLACEHOLDER_RE.search(text or ""))


def count_lines_matching(rel: str, pattern: str) -> int:
    text = read_live(rel)
    if not text:
        return 0
    rx = re.compile(pattern, re.MULTILINE)
    return len(rx.findall(text))


def section_body(rel: str, header_pattern: str) -> str:
    """Thân một section (từ header tới `## ` kế tiếp), đã bỏ comment."""
    text = read_live(rel)
    if not text:
        return ""
    rx = re.compile(rf"^{header_pattern}.*?$(.*?)(?=^##\s|\Z)", re.MULTILINE | re.DOTALL)
    m = rx.search(text)
    return m.group(1) if m else ""


def section_nonempty(rel: str, header_pattern: str) -> bool:
    """Section có content thật (không chỉ placeholder)."""
    body = PLACEHOLDER_RE.sub("", section_body(rel, header_pattern))
    return len(body.strip()) > 20               # ≥20 chars content thật


def count_evidence(rel: str, header_pattern: str) -> tuple[int, int]:
    """(số dòng `Bằng chứng:` có nội dung thật, tổng số dòng `Bằng chứng:`) trong một section.

    Vì sao đếm hai vế: người điền hay để lại dòng nhãn rỗng cho đủ hình thức. Đếm cả hai thì thông
    báo lỗi nói được "3 dòng nhưng chỉ 1 có nội dung" — chính xác hơn hẳn "thiếu bằng chứng".
    """
    total = real = 0
    for line in section_body(rel, header_pattern).splitlines():
        m = re.match(r"^\s*(?:[-*]\s*)?(?:\*\*)?Bằng chứng(?:\*\*)?\s*:\s*(.*)$", line)
        if not m:
            continue
        total += 1
        val = PLACEHOLDER_RE.sub("", m.group(1)).strip()
        if len(val) >= 15:   # ngắn hơn thế là nhãn cho có, không phải chuyện/số/hiện vật
            real += 1
    return real, total


def table_rows(body: str, *, drop_placeholder: bool = True) -> list[list[str]]:
    """Dòng dữ liệu thật của mọi bảng trong `body` → list các ô.

    Bỏ dòng phân cách và dòng tiêu đề. `drop_placeholder` loại dòng còn `{{…}}`/`_TBD_` — dòng MẪU
    của template. Trước đây phép đếm chỉ loại `_TBD_` nên 5 dòng mẫu `{{TBD}}` của
    TEMPLATE.capability-map đủ làm gate D1 XANH trên file chưa ai điền.
    """
    out: list[list[str]] = []
    seen_header = False
    for line in body.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            seen_header = False
            continue
        if re.match(r"^\|[\s\-:|]+\|?\s*$", s):     # separator → dòng trước là header
            seen_header = True
            continue
        if not seen_header:
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if drop_placeholder and any(has_placeholder(c) for c in cells):
            continue
        if not any(c for c in cells):
            continue
        out.append(cells)
    return out


def subdirs_with_file(parent: str, filename: str) -> list[str]:
    """Subdir dưới parent/ có chứa filename. Loại _TEMPLATE."""
    p = REPO_ROOT / parent
    if not p.exists():
        return []
    return sorted(
        d.name for d in p.iterdir()
        if d.is_dir() and d.name != "_TEMPLATE" and (d / filename).exists()
    )


def _count_non_placeholder_table_rows(rel: str, section_header_regex: str) -> int:
    """Đếm row table dưới section, loại header/separator/_TBD_."""
    text = read(rel)
    if not text:
        return 0
    m = re.search(rf"^{section_header_regex}.*?$(.*?)(?=^##\s|\Z)", text, re.MULTILINE | re.DOTALL)
    if not m:
        return 0
    count = 0
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:|]+\|?\s*$", line):  # separator
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        non_empty = [c for c in cells if c and c != "_TBD_" and not c.startswith("_") and "{{" not in c]
        if non_empty:
            count += 1
    return count


# ---------- Per-wave gate (port từ ZIP gate_d0/d1/d2; d3 adapt single-repo) ----------

def err(msg: str, hint: str = "") -> str:
    """Một lỗi gate = CÁI GÌ sai + SỬA Ở ĐÂU.

    Kênh `hint` tách khỏi `msg` (port từ Report.note của VIPER): thông báo chỉ nói "thiếu bằng chứng"
    thì người đọc phải đi tra luật ở chỗ khác, và lần sau lại vấp y hệt. Hint đi kèm ngay tại chỗ.
    """
    return f"{msg}\n      → {hint}" if hint else msg


def _count_bullets(body: str) -> int:
    return len([
        l for l in body.splitlines()
        if (re.match(r"^\s*[-*]\s+\S", l) or re.match(r"^\s*\d+\.\s+\S", l))
        and not has_placeholder(l)
    ])


def gate_d0() -> tuple[bool, list[str]]:
    """D0: hypothesis-log.md — vision + problem CÓ BẰNG CHỨNG + ≥3 hypothesis + ≥2 anti + lỗ hổng.

    Bằng chứng là chỗ phân biệt buổi khai thác thật với buổi hỏi cho có. Phép đếm cũ (">20 ký tự")
    không phân biệt được, nên nó bị thay chứ không được nới.
    """
    errors: list[str] = []
    rel = f"{DISC}/hypothesis-log.md"
    if not file_nonempty(rel):
        errors.append(err(f"MISSING: {rel} (cần file + non-empty)",
                          "chép từ docs/discovery/TEMPLATE.hypothesis-log.md rồi điền"))
        return False, errors

    if not section_nonempty(rel, "## 1\\. Vision narrative"):
        errors.append(err(f"{rel} §1 Vision narrative trống hoặc chỉ placeholder",
                          "1-2 đoạn: giải quyết vấn đề gì, cho ai, vì sao BÂY GIỜ"))
    if not section_nonempty(rel, "## 2\\. Problem statement"):
        errors.append(err(f"{rel} §2 Problem statement trống hoặc chỉ placeholder",
                          "mỗi pain: status quo + cost of inaction"))

    # Bằng chứng §2 — mỗi pain point một dòng, nội dung thật.
    ev_real, ev_total = count_evidence(rel, "## 2\\. Problem statement")
    if ev_real < 1:
        errors.append(err(
            f"{rel} §2: {ev_real}/{ev_total} dòng `Bằng chứng:` có nội dung thật (cần ≥1)",
            "câu chuyện thật đã xảy ra (ai/khi nào/mất gì) · con số (mấy lần/tuần, "
            "tốn bao nhiêu) · hiện vật (file Excel, ảnh sổ, tin nhắn đang dùng). "
            "Diễn đạt lại câu trả lời cho mượt hơn KHÔNG phải bằng chứng"))
    elif ev_real < ev_total:
        errors.append(err(
            f"{rel} §2: có {ev_total} dòng `Bằng chứng:` nhưng chỉ {ev_real} dòng có nội dung",
            "pain point nào cũng phải có bằng chứng — dòng nhãn rỗng là nợ, không phải xong"))

    # §3 Hypotheses — đếm row THẬT (dòng mẫu còn {{…}} không tính) + đòi cột Bằng chứng.
    h_body = section_body(rel, "## 3\\. Hypotheses")
    h_rows = [c for c in table_rows(h_body) if c and re.match(r"^H\d+$", c[0])]
    if len(h_rows) < 3:
        errors.append(err(
            f"{rel} §3 Hypotheses chỉ có {len(h_rows)} row đã điền (yêu cầu ≥3)",
            "row còn `{{…}}` không tính — mỗi giả thuyết phải falsifiable + có tín hiệu đo được"))
    else:
        header = next((l for l in h_body.splitlines()
                       if l.strip().startswith("|") and "Bằng chứng" in l), None)
        if header is None:
            errors.append(err(f"{rel} §3 thiếu cột `Bằng chứng` trong bảng hypotheses",
                              "chép lại header bảng từ TEMPLATE.hypothesis-log.md"))
        else:
            cols = [c.strip() for c in header.strip().strip("|").split("|")]
            idx = next(i for i, c in enumerate(cols) if "Bằng chứng" in c)
            weak = [r[0] for r in h_rows if len(r) <= idx or len(r[idx].strip()) < 10]
            if weak:
                errors.append(err(
                    f"{rel} §3 hypothesis chưa có bằng chứng: {', '.join(weak)}",
                    "cột Bằng chứng trống = giả thuyết suy ra từ suy luận, không từ thực tế "
                    "Authority kể. Hỏi lại: 'vì sao anh tin điều này — đã thấy nó ở đâu?'"))

    anti_count = _count_bullets(section_body(rel, "## 4\\."))
    if anti_count < 2:
        errors.append(err(f"{rel} §4 Anti-hypotheses chỉ có {anti_count} item (yêu cầu ≥2)",
                          "nêu tường minh cái KHÔNG cược — đây là hàng rào chặn scope-creep về sau"))

    # §6 Lỗ hổng — bảng trống nghĩa là chưa đào, không phải "đã phủ hết".
    gap_body = section_body(rel, "## 6\\.")
    if not gap_body.strip():
        errors.append(err(f"{rel} thiếu mục `## 6. Lỗ hổng & cách xử`",
                          "chép mục này từ TEMPLATE.hypothesis-log.md"))
    elif not table_rows(gap_body):
        errors.append(err(
            f"{rel} §6 Lỗ hổng & cách xử chưa có dòng nào",
            "chưa buổi khai thác nào phủ hết mọi thứ ngay lần đầu — bảng trống là dấu hiệu "
            "chưa đào, không phải đã đủ. Mỗi lỗ ghi: đã tìm ở đâu · cách xử · vết "
            "(§ nào, hoặc dòng tracking/decisions.md nào)"))

    return len(errors) == 0, errors


def gate_d1() -> tuple[bool, list[str]]:
    """D1: persona-pool (persona + MA TRẬN quyền không ô trống + gán vai dogfood) + capability-map.

    Ma trận vai × hành động là artifact DUY NHẤT trong cả vòng đời khai được "ai KHÔNG được làm gì".
    Thiếu nó thì: phân quyền lúc code là agent tự đoán · test không sinh được ca âm · dogfood không
    có gì để phá. Vì vậy nó là gate, không phải mục khuyến nghị.
    """
    errors: list[str] = []

    persona = f"{DISC}/persona-pool.md"
    if not file_nonempty(persona):
        errors.append(err(f"MISSING: {persona}",
                          "chép từ docs/discovery/TEMPLATE.persona-pool.md"))
    else:
        persona_count = count_lines_matching(persona, r"^##\s+P\d+\s*[—-]")
        if persona_count < 1:
            errors.append(err(f"{persona} không có persona nào (yêu cầu ≥1 dạng '## P1 — Name')",
                              "mỗi persona = 1 VAI TRÒ vận hành, không phải một cá nhân"))

        anti_p_count = _count_bullets(section_body(persona, r"##\s+Anti-personas"))
        if anti_p_count < 2:
            errors.append(err(f"{persona} §Anti-personas chỉ có {anti_p_count} item (yêu cầu ≥2)",
                              "nêu rõ nhóm KHÔNG thiết kế cho — giữ scope honest"))

        errors.extend(_check_permission_matrix(persona))

    cap = f"{DISC}/capability-map.md"
    if not file_nonempty(cap):
        errors.append(err(f"MISSING: {cap}", "chép từ docs/discovery/TEMPLATE.capability-map.md"))
    else:
        cap_rows = table_rows(section_body(cap, "## 1\\."))
        if len(cap_rows) < 5:
            errors.append(err(
                f"{cap} §1 Persona × Capability chỉ có {len(cap_rows)} capability row đã điền (yêu cầu ≥5)",
                "dòng còn `{{…}}`/`_TBD_` là dòng MẪU của template, không tính. "
                "Capability = động từ + đối tượng ('place order'), không phải tên màn hình"))

        domain_rows = table_rows(section_body(cap, "## 3\\."))
        if not domain_rows:
            errors.append(err(
                f"{cap} §3 Candidate domains chưa có domain nào (yêu cầu ≥1)",
                "tên kebab-case — D2 sẽ đòi đúng một file ES-<domain>.md cho mỗi dòng ở đây"))

    return len(errors) == 0, errors


MATRIX_HEADER = r"##\s+Ma trận vai × hành động"
_MATRIX_OK = re.compile(r"^(có|cấm|n/?a)\b", re.IGNORECASE)


def _check_permission_matrix(persona: str) -> list[str]:
    """Ma trận vai × hành động: có mặt · ≥1 hành động · KHÔNG ô trống.

    Ô trống KHÁC ô `cấm`: trống nghĩa là chưa ai quyết, và chỗ chưa ai quyết ở D1 thành chỗ code tự
    đoán ở DEV. Đó là lý do gate bắt ô trống chứ không chỉ bắt sự tồn tại của bảng.
    """
    out: list[str] = []
    body = section_body(persona, MATRIX_HEADER)
    if not body.strip():
        return [err(f"{persona} thiếu mục `## Ma trận vai × hành động`",
                    "chép mục này từ TEMPLATE.persona-pool.md — mỗi hành động một dòng, "
                    "mỗi vai một cột, cộng cột `chưa đăng nhập`")]

    rows = table_rows(body)
    if not rows:
        return [err(f"{persona} ma trận vai × hành động chưa có hành động nào đã điền",
                    "hành động viết bằng ngôn ngữ nghiệp vụ ('Huỷ đơn của người khác'), "
                    "không phải endpoint. Mỗi ô điền `có` hoặc `cấm`")]

    blank: list[str] = []
    bad: list[str] = []
    for cells in rows:
        action = cells[0] if cells else "?"
        for c in cells[1:]:
            if not c.strip():
                blank.append(action)
                break
            if not _MATRIX_OK.match(c.strip()):
                bad.append(f"{action} → {c!r}")
                break
    if blank:
        out.append(err(
            f"{persona} ma trận còn ô TRỐNG ở hành động: {', '.join(sorted(set(blank))[:5])}",
            "ô trống = chưa ai quyết, và chỗ chưa ai quyết ở D1 sẽ thành chỗ code tự đoán ở DEV. "
            "Không chắc thì hỏi user — đây vẫn là chỗ được hỏi; vẫn không rõ thì chọn `cấm` "
            "(chặt an toàn hơn mở) + 1 dòng tracking/decisions.md"))
    if bad:
        out.append(err(
            f"{persona} ma trận có ô không đọc được: {', '.join(bad[:3])}",
            "mỗi ô bắt đầu bằng `có` / `cấm` / `n/a`; điều kiện ghi kèm sau: "
            "`có (chỉ bản ghi của mình)`. KHÔNG dùng icon — convention no-icon toàn repo"))

    if not any(re.match(r"^cấm", c.strip(), re.IGNORECASE)
               for cells in rows for c in cells[1:]):
        out.append(err(
            f"{persona} ma trận không có ô `cấm` nào",
            "hệ thống nào cũng có ranh giới — không có ô cấm nghĩa là chưa nghĩ tới phân quyền, "
            "và test sẽ không sinh được ca âm nào"))
    return out


def gate_d2() -> tuple[bool, list[str]]:
    """D2: ≥1 ES file per candidate domain (D1 §3), mỗi file §1 Events ≥10."""
    errors: list[str] = []

    cap = f"{DISC}/capability-map.md"
    if not file_nonempty(cap):
        errors.append(f"MISSING: {cap} (D1 chưa xong)")
        return False, errors

    # Dùng CHUNG table_rows với gate D1: dòng mẫu còn `{{…}}` không được thành domain giả, không thì
    # D2 đi đòi một file ES-kebab-case.md không bao giờ tồn tại.
    domains: list[str] = []
    for cells in table_rows(section_body(cap, "## 3\\.")):
        name = re.sub(r"[^a-z0-9-]", "-", cells[0].lower()).strip("-")
        if name:
            domains.append(name)

    if not domains:
        errors.append(err(
            f"{cap} §3 không list candidate domain nào — không xác định được expected ES files",
            "quay lại D1 điền §3 (kebab-case); mỗi dòng ở đó là một file ES bắt buộc ở D2"))
        return False, errors

    es_dir = REPO_ROOT / DISC / "event-storming"
    es_files = list(es_dir.glob("ES-*.md")) if es_dir.exists() else []
    es_names = {f.stem for f in es_files}

    for domain in domains:
        expected = f"ES-{domain}"
        if expected not in es_names:
            errors.append(f"MISSING: {DISC}/event-storming/{expected}.md (cho domain '{domain}' từ capability-map §3)")
            continue
        es_text = read(f"{DISC}/event-storming/{expected}.md")
        m_ev = re.search(r"^##?\s*1\.\s*Events.*?$(.*?)(?=^##\s|\Z)", es_text, re.MULTILINE | re.DOTALL)
        if m_ev:
            event_count = len([l for l in m_ev.group(1).splitlines() if re.match(r"^\s*[-*\d]+\.?\s+\w", l)])
        else:
            event_count = 0
        if event_count < 10:
            errors.append(f"{DISC}/event-storming/{expected}.md §1 Events chỉ có {event_count} event (yêu cầu ≥10)")

    return len(errors) == 0, errors


def gate_d3() -> tuple[bool, list[str]]:
    """D3 (adapt single-repo): BOUNDARY-MAP ≥1 row + ≥1 CHARTER Mission + derive PROJECT.md.

    Bỏ check ADR-D3/SYSTEM-TOPOLOGY (stack decision thuộc technical-design/DESIGN sau).
    D3 derive PROJECT.md (PRD) → DOMAIN_AUTHORING. **KHÔNG sinh FEAT** ở đây: DOMAIN sở hữu
    product — po/ba author BUSINESS vào docs/domain/ → ký (domain-approve) → domain-translate
    dịch sang eng docs/architecture/{epics,feat,business-rules}/.
    """
    errors: list[str] = []

    bmap = f"{DISC}/BOUNDARY-MAP.md"
    if not file_nonempty(bmap):
        errors.append(f"MISSING: {bmap}")
    else:
        total_real_rows = 0
        for section in (r"## 1\.", r"## 2\.", r"## 3\."):
            total_real_rows += _count_non_placeholder_table_rows(bmap, section)
        if total_real_rows < 1:
            errors.append(f"{bmap} không có row non-placeholder nào (yêu cầu ≥1 boundary). Hiện chỉ _TBD_.")

    # ≥1 target có CHARTER.md (non-_TEMPLATE) + §1 Mission có content
    boundaries = subdirs_with_file(f"{DISC}/boundaries", "CHARTER.md")
    if not boundaries:
        errors.append(f"Chưa có target nào với CHARTER.md trong {DISC}/boundaries/<x>/ (yêu cầu ≥1 non-_TEMPLATE)")
    else:
        for b in boundaries:
            charter = f"{DISC}/boundaries/{b}/CHARTER.md"
            if not section_nonempty(charter, "## 1\\. Mission"):
                errors.append(f"{charter} §1 Mission trống hoặc chỉ placeholder")

    # D3 derive PROJECT.md (PRD) → bridge sang DOMAIN authoring
    if not file_nonempty("docs/architecture/PROJECT.md"):
        errors.append("MISSING: docs/architecture/PROJECT.md (D3 charter-author derive PRD từ hypothesis+capability+ES)")

    return len(errors) == 0, errors


# ---------- Dispatch ----------

GATES: dict[str, Callable[[], tuple[bool, list[str]]]] = {
    "D0": gate_d0,
    "D1": gate_d1,
    "D2": gate_d2,
    "D3": gate_d3,
}

# Map stage harness → gate của stage đang rời (outgoing).
STAGE_TO_GATE = {
    "DISC_D0": "D0",
    "DISC_D1": "D1",
    "DISC_D2": "D2",
    "DISC_D3": "D3",
}


def check_gate(wave: str) -> tuple[bool, list[str]]:
    """Run gate cho wave. Trả (passed, errors). Dùng bởi gates.py."""
    wave = wave.upper()
    if wave not in GATES:
        return False, [f"unknown wave {wave!r}. Valid: {sorted(GATES.keys())}"]
    return GATES[wave]()


def _print_result(wave: str, passed: bool, errors: list[str]) -> int:
    if passed:
        print(f"OK: {wave} exit gate PASS")
        return 0
    print(f"FAIL: {wave} exit gate:", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    print(
        f"\nResolution: produce artifact thiếu (xem plan §Flow). "
        f"Hoặc override: state.py complete discovery-end với --force (ghi tracking/decisions.md).",
        file=sys.stderr,
    )
    return 1


# ---------- Self-test ----------

def _selftest() -> int:
    """Kiểm chính gate: mỗi phép kiểm phải ĐỎ ĐÚNG LÝ DO, không chỉ đỏ.

    Vì sao assert theo lý do chứ không theo exit code: gate đỏ vì "file không tồn tại" và gate đỏ vì
    "thiếu bằng chứng" là hai chuyện khác hẳn nhau, nhưng cả hai đều exit 1. Test chỉ nhìn exit code
    sẽ xanh kể cả khi phép kiểm mình vừa viết không bao giờ chạy tới.
    """
    import tempfile
    global REPO_ROOT
    saved = REPO_ROOT
    failures: list[str] = []

    def check(label: str, cond: bool, detail: str = "") -> None:
        if cond:
            print(f"  ok   {label}")
        else:
            failures.append(label)
            print(f"  FAIL {label}" + (f"\n       {detail}" if detail else ""))

    def reasons(wave: str) -> str:
        return "\n".join(check_gate(wave)[1])

    tmpl_h = (saved / "docs/discovery/TEMPLATE.hypothesis-log.md").read_text(encoding="utf-8")
    tmpl_p = (saved / "docs/discovery/TEMPLATE.persona-pool.md").read_text(encoding="utf-8")
    tmpl_c = (saved / "docs/discovery/TEMPLATE.capability-map.md").read_text(encoding="utf-8")

    try:
        with tempfile.TemporaryDirectory() as td:
            REPO_ROOT = Path(td)
            d = REPO_ROOT / DISC
            d.mkdir(parents=True)

            # --- Chưa có file gì: đỏ vì MISSING, không phải vì thứ khác ---
            check("D0 chưa có file → MISSING", "MISSING" in reasons("D0"))

            # --- Template thô (chưa ai điền) PHẢI ĐỎ. Đây là hồi quy cho lỗ đã vá:
            #     5 dòng mẫu `{{TBD}}` của capability-map từng đủ làm gate D1 xanh. ---
            (d / "hypothesis-log.md").write_text(tmpl_h, encoding="utf-8")
            (d / "persona-pool.md").write_text(tmpl_p, encoding="utf-8")
            (d / "capability-map.md").write_text(tmpl_c, encoding="utf-8")
            r0, r1 = reasons("D0"), reasons("D1")
            check("D0 template thô → đỏ", not check_gate("D0")[0])
            check("D1 template thô → đỏ", not check_gate("D1")[0])
            check("D1 template thô → đỏ vì capability toàn dòng MẪU (không phải vì lý do khác)",
                  "capability row đã điền" in r1, r1)

            # --- Bằng chứng: văn xuôi dài KHÔNG thay được bằng chứng ---
            waffle = ("## 1. Vision narrative\n" + "Sản phẩm giúp người dùng làm việc hiệu quả hơn rất nhiều. " * 4
                      + "\n\n## 2. Problem statement\n"
                      + "**Pain point 1 — nhập liệu.** Người dùng hay gặp khó khăn khi nhập đơn và điều này gây ra nhiều vấn đề.\n"
                      + "\n## 3. Hypotheses\n\n| ID | Statement | Bằng chứng |\n|---|---|---|\n"
                      + "| H1 | a | b |\n| H2 | c | d |\n| H3 | e | f |\n"
                      + "\n## 4. Anti\n- x\n- y\n\n## 6. Lỗ hổng\n\n| # | a |\n|---|---|\n| G1 | z |\n")
            (d / "hypothesis-log.md").write_text(waffle, encoding="utf-8")
            check("D0 văn xuôi trừu tượng, không bằng chứng → đỏ đúng chỗ §2",
                  "`Bằng chứng:`" in reasons("D0"), reasons("D0"))

            # --- Comment KHÔNG được tính là nội dung (read_live) ---
            hidden = waffle.replace("## 6. Lỗ hổng\n\n| # | a |\n|---|---|\n| G1 | z |\n",
                                    "## 6. Lỗ hổng\n\n<!--\n| # | a |\n|---|---|\n| G1 | z |\n-->\n")
            (d / "hypothesis-log.md").write_text(hidden, encoding="utf-8")
            check("D0 lỗ hổng bọc trong <!-- --> → vẫn đỏ (read_live bỏ comment)",
                  "Lỗ hổng" in reasons("D0"), reasons("D0"))

            # --- Ma trận quyền: thiếu / ô trống / toàn `có` đều phải đỏ, mỗi cái một lý do ---
            base_p = ("## P1 — Thu ngân\n\n| Field | Value |\n|---|---|\n| Role | x |\n\n"
                      "## Anti-personas\n- a\n- b\n")
            (d / "persona-pool.md").write_text(base_p, encoding="utf-8")
            check("D1 thiếu ma trận → đỏ vì thiếu MỤC ma trận",
                  "thiếu mục `## Ma trận vai × hành động`" in reasons("D1"), reasons("D1"))

            mtx = "\n## Ma trận vai × hành động\n\n| Hành động | P1 | chưa đăng nhập |\n|---|---|---|\n"
            (d / "persona-pool.md").write_text(base_p + mtx + "| Tạo đơn | có |  |\n", encoding="utf-8")
            check("D1 ma trận có Ô TRỐNG → đỏ vì ô trống",
                  "ô TRỐNG" in reasons("D1"), reasons("D1"))

            (d / "persona-pool.md").write_text(base_p + mtx + "| Tạo đơn | có | có |\n", encoding="utf-8")
            check("D1 ma trận toàn `có` → đỏ vì không có ô cấm",
                  "không có ô `cấm` nào" in reasons("D1"), reasons("D1"))

            (d / "persona-pool.md").write_text(base_p + mtx + "| Tạo đơn | có | cấm |\n", encoding="utf-8")
            check("D1 ma trận hợp lệ → hết lỗi ma trận",
                  "Ma trận" not in reasons("D1") and "ma trận" not in reasons("D1"), reasons("D1"))

            # --- Icon KHÔNG được nhận thay cho `có`/`cấm` (convention no-icon) ---
            (d / "persona-pool.md").write_text(base_p + mtx + "| Tạo đơn | ✓ | ✗ |\n", encoding="utf-8")
            check("D1 ma trận dùng icon → đỏ vì ô không đọc được",
                  "không đọc được" in reasons("D1"), reasons("D1"))
    finally:
        REPO_ROOT = saved

    print()
    if failures:
        print(f"FAIL: discovery_gate selftest — {len(failures)} phép kiểm hỏng", file=sys.stderr)
        return 1
    print("OK: discovery_gate selftest passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(prog="discovery_gate.py", description="DISCOVERY exit gate D0-D3")
    ap.add_argument("wave", nargs="?", help="D0 | D1 | D2 | D3")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--selftest", action="store_true",
                    help="kiểm chính gate: mỗi phép kiểm phải đỏ ĐÚNG LÝ DO")
    args = ap.parse_args(argv)

    if args.selftest:
        return _selftest()

    if args.all:
        rc = 0
        for w in ("D0", "D1", "D2", "D3"):
            passed, errors = check_gate(w)
            if _print_result(w, passed, errors) != 0:
                rc = 1
        return rc
    if not args.wave:
        ap.print_help(sys.stderr)
        return 2
    passed, errors = check_gate(args.wave)
    if args.wave.upper() not in GATES:
        print(f"ERROR: unknown wave {args.wave!r}", file=sys.stderr)
        return 2
    return _print_result(args.wave.upper(), passed, errors)


if __name__ == "__main__":
    sys.exit(main())
