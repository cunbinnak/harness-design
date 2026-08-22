"""
wave_sequence_lint.py — Validator cho docs/plans/WAVE-SEQUENCE.md §wave-NNN (G16).

Port từ ZIP `{{PROJECT-CODE}}-ADLC-DISCOVERY/scripts/wave-sequence-validate.py`, adapt single-repo:
- root marker `ADLC.md` → `harness/STATE.json`; path `Plan/WAVE-SEQUENCE.md` → `docs/plans/WAVE-SEQUENCE.md`.
- section `## §W{N}` → `### §wave-{NNN}` (layout harness §2 Per-wave entries — clone ZIP block YAML).
- BỎ contract-signing/`inherited_active` SIGNED check (plumbing multi-repo). Thay: `inherited_active`
  = đường dẫn doc trong `docs/architecture/` → check FILE TỒN TẠI (single-repo: contract = file).

Hard invariants (error → chặn plan): wave_class/wave_strategy enum · target_count_per_layer ≤ 3 ·
strategy layer-purity (horizontal-be cấm FE target; horizontal-fe cấm boundary target) · vertical →
mỗi FEAT có parent_epic. Warning (không chặn): rare combo rationale · paired_with reciprocal ·
exit_signal coherence · test_scope coherence.

CLI:
  py scripts/wave_sequence_lint.py            # lint tất cả wave
  py scripts/wave_sequence_lint.py --selftest # hermetic unit test
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

VALID_CLASSES = {"slice", "integration"}
VALID_STRATEGIES = {"vertical", "horizontal-be", "horizontal-fe"}
RARE_COMBOS = {("slice", "vertical"), ("integration", "horizontal-be"), ("integration", "horizontal-fe")}
TARGET_CAP_PER_LAYER = 3
EXPECTED_EXIT_SIGNAL = {
    "vertical": "demo_target",
    "horizontal-be": "bd_increment_milestone",
    "horizontal-fe": "ui_increment_milestone",
}


# ----------------------------------------------------------------- parsing

def list_waves(content: str) -> list[str]:
    """Mọi section `### §wave-NNN` (hoặc `## §wave-NNN`)."""
    return [m.group(1) for m in re.finditer(r"#{2,3}\s*§(wave-\d+)\b", content)]


def extract_wave_yaml(content: str, wave_id: str) -> str | None:
    """Section `### §{wave_id}` → YAML block đầu tiên (```yaml ... ```)."""
    pattern = rf"#{{2,3}}\s*§{re.escape(wave_id)}\b(.*?)(?=#{{2,3}}\s*§wave-\d+|\n##\s|\Z)"
    m = re.search(pattern, content, re.DOTALL)
    if not m:
        return None
    ym = re.search(r"```(?:yaml)?\n(.*?)```", m.group(1), re.DOTALL)
    return ym.group(1) if ym else None


def parse_yaml_block(block: str) -> dict[str, Any]:
    """PyYAML nếu có; fallback minimal parser (nested dict/list + multiline | + inline list)."""
    try:
        import yaml  # type: ignore
        return yaml.safe_load(block) or {}
    except Exception:
        pass
    out: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(0, out)]
    lines = block.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        indent = len(line) - len(line.lstrip())
        while len(stack) > 1 and stack[-1][0] > indent:
            stack.pop()
        parent = stack[-1][1]
        if stripped.startswith("- "):
            body = stripped[2:].strip()
            if isinstance(parent, list):
                if ":" in body:
                    item: dict[str, Any] = {}
                    k, _, v = body.partition(":")
                    item[k.strip()] = _parse_value(v.strip())
                    parent.append(item)
                    stack.append((indent + 2, item))
                else:
                    parent.append(_parse_value(body))
            i += 1
            continue
        if ":" in stripped:
            k, _, v = stripped.partition(":")
            k, v = k.strip(), v.strip()
            if not v:
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines) and lines[j].lstrip().startswith("- "):
                    nl: list[Any] = []
                    if isinstance(parent, dict):
                        parent[k] = nl
                    stack.append((indent + 2, nl))
                else:
                    nd: dict[str, Any] = {}
                    if isinstance(parent, dict):
                        parent[k] = nd
                    stack.append((indent + 2, nd))
            elif v == "|":
                collected: list[str] = []
                j = i + 1
                while j < len(lines):
                    if not lines[j].strip():
                        j += 1
                        continue
                    if len(lines[j]) - len(lines[j].lstrip()) <= indent:
                        break
                    collected.append(lines[j].strip())
                    j += 1
                if isinstance(parent, dict):
                    parent[k] = "\n".join(collected)
                i = j
                continue
            else:
                if isinstance(parent, dict):
                    parent[k] = _parse_value(v)
        i += 1
    return out


def _parse_value(v: str) -> Any:
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [] if not inner else [_parse_value(x.strip()) for x in inner.split(",")]
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
        return v[1:-1]
    if v in ("null", "~", ""):
        return None
    if v.isdigit():
        return int(v)
    return v


# ----------------------------------------------------------------- validate

def validate_wave(spec: dict, wave_id: str, root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    wave_class = str(spec.get("wave_class", "")).strip()
    wave_strategy = str(spec.get("wave_strategy", "")).strip()
    targets = spec.get("targets") or {}
    feats = spec.get("features_in_scope") or []
    contracts = spec.get("contracts") or {}

    if wave_class not in VALID_CLASSES:
        errors.append(f"{wave_id}: wave_class={wave_class!r} invalid (phải ∈ {sorted(VALID_CLASSES)})")
    if wave_strategy not in VALID_STRATEGIES:
        errors.append(f"{wave_id}: wave_strategy={wave_strategy!r} invalid (phải ∈ {sorted(VALID_STRATEGIES)})")

    # target cap per layer
    for layer in ("boundaries", "web_experiences", "mobile_experiences"):
        names = targets.get(layer) or []
        if not isinstance(names, list):
            errors.append(f"{wave_id}: targets.{layer} phải là list")
            continue
        if len(names) > TARGET_CAP_PER_LAYER:
            errors.append(f"{wave_id}: layer {layer} có {len(names)} target > cap {TARGET_CAP_PER_LAYER}")

    # strategy invariants
    if wave_strategy == "horizontal-be":
        if targets.get("web_experiences") or targets.get("mobile_experiences"):
            errors.append(f"{wave_id}: horizontal-be cấm FE target (web/mobile_experiences phải rỗng)")
        for f in feats:
            if not str(f.get("target", "")).startswith("boundaries/"):
                errors.append(f"{wave_id}: horizontal-be FEAT {f.get('feat_id','?')} target không thuộc boundaries/")
            if f.get("paired_with"):
                errors.append(f"{wave_id}: horizontal-be FEAT {f.get('feat_id','?')} có paired_with — cấm pair")
    elif wave_strategy == "horizontal-fe":
        if targets.get("boundaries"):
            errors.append(f"{wave_id}: horizontal-fe cấm boundary target (boundaries phải rỗng)")
        for f in feats:
            if str(f.get("target", "")).startswith("boundaries/"):
                errors.append(f"{wave_id}: horizontal-fe FEAT {f.get('feat_id','?')} target không được là boundaries/")
        # single-repo: inherited_active = doc path phải TỒN TẠI (thay contract-signing multi-repo)
        for c in (contracts.get("inherited_active") or []):
            if not (root / str(c)).is_file():
                errors.append(f"{wave_id}: inherited_active '{c}' không tồn tại (FE consume contract phải có file ở docs/architecture/)")
    elif wave_strategy == "vertical":
        for f in feats:
            if not f.get("parent_epic"):
                errors.append(f"{wave_id}: vertical FEAT {f.get('feat_id','?')} thiếu parent_epic")
        ids = {f.get("feat_id") for f in feats}
        for f in feats:
            p = f.get("paired_with")
            if p and p not in ids:
                warnings.append(f"{wave_id}: vertical FEAT {f.get('feat_id','?')} paired_with={p!r} không ở features_in_scope (có thể wave khác — verify)")

    # rare combo
    if (wave_class, wave_strategy) in RARE_COMBOS:
        if len(str(spec.get("rationale", "")).strip()) < 20:
            warnings.append(f"{wave_id}: rare combo ({wave_class},{wave_strategy}) — rationale phải giải thích rõ")

    # exit_signal coherence
    exit_type = (spec.get("exit_signal") or {}).get("type", "")
    exp = EXPECTED_EXIT_SIGNAL.get(wave_strategy)
    if exp and exit_type and exit_type != exp:
        warnings.append(f"{wave_id}: exit_signal.type={exit_type!r} != default {exp!r} cho strategy={wave_strategy}")

    # test_scope coherence
    ts = spec.get("test_scope") or {}
    required = ts.get("required") or []
    if wave_class == "slice":
        leaked = {"integration", "a11y", "e2e"} & set(required)
        if leaked:
            errors.append(f"{wave_id}: slice wave không required {sorted(leaked)} (chỉ integration wave)")
    elif wave_class == "integration":
        if "integration" not in required and "integration" not in (ts.get("conditional") or []):
            warnings.append(f"{wave_id}: integration wave thường có 'integration' trong test_scope")

    return errors, warnings


def run_lint(root: Path | None = None) -> tuple[bool, list[str]]:
    """Gate entry: (ok, errors). WARNING không chặn. File thiếu → ok (plan_gate lo)."""
    root = root or REPO_ROOT
    seq = root / "docs" / "plans" / "WAVE-SEQUENCE.md"
    if not seq.is_file():
        return True, []  # plan_gate file_exists đã chặn
    content = seq.read_text(encoding="utf-8", errors="ignore")
    waves = list_waves(content)
    if not waves:
        return False, ["WAVE-SEQUENCE.md không có §wave-NNN YAML block — không lint được strategy/target/cap"]
    all_errors: list[str] = []
    for wid in waves:
        block = extract_wave_yaml(content, wid)
        if block is None:
            all_errors.append(f"{wid}: thiếu YAML block trong section §{wid}")
            continue
        spec = parse_yaml_block(block)
        errs, _ = validate_wave(spec, wid, root)
        all_errors.extend(errs)
    return (not all_errors), all_errors


# ----------------------------------------------------------------- selftest

def _selftest() -> int:
    import tempfile, shutil, json as _json
    root = Path(tempfile.mkdtemp(prefix="wsl_"))
    try:
        (root / "harness").mkdir(parents=True, exist_ok=True)
        (root / "harness" / "STATE.json").write_text("{}", encoding="utf-8")
        plans = root / "docs" / "plans"
        plans.mkdir(parents=True, exist_ok=True)
        api = root / "docs" / "architecture" / "api"
        api.mkdir(parents=True, exist_ok=True)
        (api / "api-auth.md").write_text("# api-auth", encoding="utf-8")

        # (a) hợp lệ: vertical + horizontal-be + horizontal-fe (inherited file tồn tại)
        good = """\
## 2. Per-wave entries

### §wave-001
```yaml
wave_class: integration
wave_strategy: vertical
rationale: |
  Lat dau ship E2E - validate luong nghiep vu chinh som, pair BE+FE.
targets:
  boundaries: ["auth"]
  web_experiences: ["customer-app"]
  mobile_experiences: []
features_in_scope:
  - feat_id: FEAT-001
    target: boundaries/auth
    parent_epic: EP-001
    paired_with: FEAT-101
  - feat_id: FEAT-101
    target: web-experiences/customer-app
    parent_epic: EP-001
    paired_with: FEAT-001
exit_signal:
  type: demo_target
test_scope:
  required: [unit, component]
  conditional: [integration, e2e]
```

### §wave-003
```yaml
wave_class: slice
wave_strategy: horizontal-fe
rationale: short
targets:
  boundaries: []
  web_experiences: ["ops-portal"]
  mobile_experiences: []
features_in_scope:
  - feat_id: FEAT-301
    target: web-experiences/ops-portal
exit_signal:
  type: ui_increment_milestone
test_scope:
  required: [component, visual]
  conditional: [a11y]
contracts:
  inherited_active:
    - docs/architecture/api/api-auth.md
```
"""
        (plans / "WAVE-SEQUENCE.md").write_text(good, encoding="utf-8")
        ok, errs = run_lint(root)
        assert ok, f"valid case phải pass: {errs}"

        # (b) cap > 3 + horizontal-be có FE target + invalid enum
        bad = """\
### §wave-001
```yaml
wave_class: slice
wave_strategy: horizontal-be
targets:
  boundaries: ["a", "b", "c", "d"]
  web_experiences: ["x"]
  mobile_experiences: []
features_in_scope:
  - feat_id: FEAT-1
    target: web-experiences/x
    paired_with: FEAT-9
```

### §wave-002
```yaml
wave_class: bogus
wave_strategy: sideways
targets:
  boundaries: []
  web_experiences: []
  mobile_experiences: []
```
"""
        (plans / "WAVE-SEQUENCE.md").write_text(bad, encoding="utf-8")
        ok, errs = run_lint(root)
        joined = " | ".join(errs)
        assert not ok, "bad case phải fail"
        assert "cap 3" in joined and "horizontal-be cấm FE" in joined, joined
        assert "wave_class='bogus'" in joined and "wave_strategy='sideways'" in joined, joined

        # (c) horizontal-fe inherited_active file KHÔNG tồn tại → fail
        miss = """\
### §wave-001
```yaml
wave_class: slice
wave_strategy: horizontal-fe
targets:
  boundaries: []
  web_experiences: ["p"]
  mobile_experiences: []
features_in_scope:
  - feat_id: FEAT-1
    target: web-experiences/p
contracts:
  inherited_active:
    - docs/architecture/api/api-nonexistent.md
```
"""
        (plans / "WAVE-SEQUENCE.md").write_text(miss, encoding="utf-8")
        ok, errs = run_lint(root)
        assert not ok and "không tồn tại" in " ".join(errs), errs

        # (d) không có §wave block → fail
        (plans / "WAVE-SEQUENCE.md").write_text("# Wave Sequence\n\nno blocks here\n", encoding="utf-8")
        ok, errs = run_lint(root)
        assert not ok and "không có §wave" in " ".join(errs), errs

        # (e) file thiếu → ok (plan_gate lo)
        (plans / "WAVE-SEQUENCE.md").unlink()
        assert run_lint(root) == (True, [])
        _ = _json  # silence
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print("OK: wave_sequence_lint.py selftest passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Validate docs/plans/WAVE-SEQUENCE.md §wave-NNN (G16)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return _selftest()
    ok, errs = run_lint()
    if ok:
        print("OK: WAVE-SEQUENCE.md hợp lệ (wave-sequence-lint)")
        return 0
    print("FAIL wave-sequence-lint:")
    for e in errs:
        print(f"  - {e}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
