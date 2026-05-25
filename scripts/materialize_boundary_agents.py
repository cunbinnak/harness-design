#!/usr/bin/env python3
"""Materialize dev boundary agents (dev + fix + review) from roster.

Mỗi boundary_id trong roster (kể cả FE: fe-web, fe-admin) → bộ 3 agent.
Không tự thêm `fe` — khai báo rõ trong agent-roster.md.

Usage:
  py scripts/materialize_boundary_agents.py --wave wave-001 --boundaries order,fe-web
  py scripts/materialize_boundary_agents.py --from-roster docs/plans/project/agent-roster.md
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from harness_lib import repo_root
from materialize_wave_plans import parse_wave_ids_from_roadmap
from wave_ids import normalize_wave_id

FE_BOUNDARY_IDS = frozenset({"fe", "frontend"})
FE_LAYERS = frozenset({"fe", "frontend", "front-end"})

ROLE_META = {
    "dev": {
        "prefix": "",
        "role_label": "Development",
        "primary_command": "start-dev",
        "spawn_stage": "IMPLEMENTATION",
        "skill_primary": "implementation",
        "identity": "kỹ sư triển khai boundary `{bid}`",
        "display": "{bid} Development Agent",
        "mission": "Triển khai code đúng FEAT và wave-plan trong owned_paths.",
        "forbidden": (
            "- Self-review thay `review-{bid}-agent`.\n"
            "- Sửa bug thay `fix-{bid}-agent`.\n"
            "- Test/release hoặc đăng ký matrix."
        ),
    },
    "fix": {
        "prefix": "fix-",
        "role_label": "Bug fix",
        "primary_command": "fix-bugs",
        "spawn_stage": "FIX_MANUAL_BUGS",
        "skill_primary": "implementation",
        "identity": "kỹ sư sửa bug boundary `{bid}`",
        "display": "fix-{bid} Bug Fix Agent",
        "mission": "Sửa lỗi trong owned_paths; ghi `tracking/waves/{wave-id}/bugs/`.",
        "forbidden": "- Feature mới ngoài bug scope.\n- test-execute / release.",
    },
    "review": {
        "prefix": "review-",
        "role_label": "Self-review",
        "primary_command": "review-dev",
        "spawn_stage": "SELF_REVIEW",
        "skill_primary": "self-review",
        "identity": "reviewer code boundary `{bid}`",
        "display": "review-{bid} Self-Review Agent",
        "mission": "Rà soát chất lượng code trước handoff QA.",
        "forbidden": "- Triển khai feature mới.\n- Chạy test-plan/execute.",
    },
}

# Map (layer, role) → key in harness/AGENT-DISCIPLINE.json[agent_roles]
REGISTRY_ROLE_KEY = {
    ("backend", "dev"): "dev:backend",
    ("backend", "fix"): "fix:backend",
    ("backend", "review"): "review:backend",
    ("fe", "dev"): "dev:frontend",
    ("fe", "fix"): "fix:frontend",
    ("fe", "review"): "review:frontend",
}


# Per-layer content blocks injected via {{layer_block}} placeholder.
# Avoids all-in-one template noise — BE agent sees only BE rules, FE agent sees only FE rules.
LAYER_BLOCKS = {
    "backend": """## Skills áp dụng (Backend)

| Skill | Khi nào dùng |
|-------|--------------|
| [`{{skill_primary}}`](../skills/{{skill_primary}}/SKILL.md) | Mọi task BE — quy trình implement |
| [`backend-conventions`](../skills/backend-conventions/SKILL.md) | Code style + coding standards BE |
| [`ref-back-end-pattern`](../skills/ref-back-end-pattern/SKILL.md) | Cấu trúc thư mục + layered architecture (api/domain/infra) |
| [`ref-back-end-config`](../skills/ref-back-end-config/SKILL.md) | Mẫu config YAML/env, docker-compose entry, secrets management |
| [`tech-stack`](../skills/tech-stack/SKILL.md) | Framework / lib chuẩn của project |
| [`self-review`](../skills/self-review/SKILL.md) | Chỉ khi role là `review:backend` |

**KHÔNG load** `frontend-conventions`, `frontend-implementation`, `ref-front-end-*` — ngoài layer.

---

## Rule Backend cứng

| # | Rule | Tham chiếu |
|---|------|-----------|
| BE-1 | Mọi endpoint (trừ `/health`) phải validate JWT Bearer | ADR-003 |
| BE-2 | Parse + validate DTO ở api layer — trả 400 trước khi vào domain | api-{{boundary_id}}.md |
| BE-3 | HTTP status code chuẩn: 200/201/204/400/401/403/404/409/500 | api-{{boundary_id}}.md |
| BE-4 | Error format JSON `{"error":"CODE","message":"..."}` nhất quán | api-{{boundary_id}}.md |
| BE-5 | Multi-table write **phải trong transaction** | data-model + ADR-002 |
| BE-6 | Domain service KHÔNG được import infra trực tiếp — qua port/interface | ref-back-end-pattern |
| BE-7 | KHÔNG hardcode secret — dùng env (`config/`) | ref-back-end-config |
| BE-8 | Outbound call có timeout + retry policy | HLD §5 |
| BE-9 | Migration forward-only, nullable trước backfill trước enforce | data-model |
| BE-10 | Log structured JSON (request_id, user_id, latency) | PROJECT NFR |

**Coverage ngưỡng:** ≥ 80% (pytest/junit/jest BE).

---

## Test commands (Backend)

```bash
cd services/{{boundary_id}}
# Python:
pytest --cov=. --cov-report=term-missing 2>&1 | tee /tmp/coverage.txt
# Node BE:
npm test -- --coverage 2>&1 | tee /tmp/coverage.txt
# Java:
mvn test jacoco:report 2>&1 | tee /tmp/coverage.txt

# Lint
ruff check . || flake8 . || npm run lint || mvn checkstyle:check
```

---

## Nếu là Review Agent (`review-{{boundary_id}}-agent`)

> Áp dụng chỉ khi `agent_id` prefix `review-`.

**Mục tiêu review BE:**
1. **Correctness** — BR khớp FEAT AC, Rule BE-1..10
2. **Coverage** — ≥ 80%
3. **Quality** — lint pass, no magic constants, error handling đủ
4. **Security** — input validate, JWT check, no hardcoded secret

**Bắt buộc fix khi:** coverage < 80%, test fail, security ≥ medium, Rule BE-1..10 violation.

Spawn fix-agent khi cần:
```bash
py scripts/build_command_prompt.py fix-bugs --boundary {{boundary_id}}
```

**RETURN review:**
```json
{
  "completed": ["review-{{boundary_id}}"],
  "build": "pass",
  "lint": "pass",
  "test": "pass",
  "coverage_pct": 85,
  "review_status": "approved | approved_with_notes | needs_fix",
  "issues_found": [],
  "kg_appended": ["review-decision-xxx"]
}
```""",
    "fe": """## Skills áp dụng (Frontend)

| Skill | Khi nào dùng |
|-------|--------------|
| [`{{skill_primary}}`](../skills/{{skill_primary}}/SKILL.md) | Mọi task FE — quy trình implement UI |
| [`frontend-conventions`](../skills/frontend-conventions/SKILL.md) | Code style, component pattern, state management |
| [`ref-front-end-pattern`](../skills/ref-front-end-pattern/SKILL.md) | Cấu trúc thư mục FE (src/pages/components/hooks/services/stores) |
| [`ref-front-end-config`](../skills/ref-front-end-config/SKILL.md) | Mẫu config FE (package.json scripts, .env, Vite/Webpack, Dockerfile FE) |
| [`tech-stack`](../skills/tech-stack/SKILL.md) | Framework FE chuẩn (React/Vue/Angular...) |
| [`self-review`](../skills/self-review/SKILL.md) | Chỉ khi role là `review:frontend` |

**KHÔNG load** `backend-conventions`, `implementation` (BE-focused), `ref-back-end-*` — ngoài layer.

---

## Rule Frontend cứng

| # | Rule | Tham chiếu |
|---|------|-----------|
| FE-1 | Form validate **CẢ client + server** — không tin client | ux validation |
| FE-2 | Mọi data fetch có **loading / empty / error state** | ux UI states |
| FE-3 | Protected route có **auth guard** — redirect `/login?redirect={current}` | ux routing |
| FE-4 | Component reusable: props rõ ràng, KHÔNG hardcode value/string | ref-front-end-pattern |
| FE-5 | A11y WCAG 2.1 AA: `label`/`aria-*`, focus visible, contrast ≥ 4.5:1 | ux a11y checklist |
| FE-6 | Responsive: desktop ≥1024, tablet 768-1023, mobile <768 | ux responsive |
| FE-7 | API call qua service layer (`src/services/`), KHÔNG fetch trong component | ref-front-end-pattern |
| FE-8 | Token storage: httpOnly cookie hoặc memory (không localStorage cho JWT) | ADR-003 |
| FE-9 | Error toast/dialog format nhất quán Design System | ADR-004 |
| FE-10 | Lazy load route + code split cho bundle nặng | NFR performance |

**Coverage ngưỡng:** ≥ 60% (jest/vitest/cypress).

---

## Test commands (Frontend)

```bash
cd services/{{boundary_id}}
npm test -- --coverage --watchAll=false 2>&1 | tee /tmp/coverage.txt
# hoặc: yarn test --coverage

# Lint
npm run lint
# A11y (nếu có axe-core)
npm run a11y || npx jest --testPathPattern=a11y

# E2E (nếu có)
npx cypress run --headless
```

---

## Nếu là Review Agent (`review-{{boundary_id}}-agent`)

> Áp dụng chỉ khi `agent_id` prefix `review-`.

**Mục tiêu review FE:**
1. **UX correctness** — khớp wireframe `ux-{{boundary_id}}.md`
2. **Coverage** — ≥ 60%
3. **A11y** — WCAG 2.1 AA checklist
4. **Quality** — lint pass, component reusable, no inline style chaos
5. **Security** — XSS prevention (escape user input), token storage đúng (FE-8)

**Bắt buộc fix khi:** coverage < 60%, test fail, A11y A/AA violation, Rule FE-1..10 violation, XSS/security medium+.

Spawn fix-agent khi cần:
```bash
py scripts/build_command_prompt.py fix-bugs --boundary {{boundary_id}}
```

**RETURN review:**
```json
{
  "completed": ["review-{{boundary_id}}"],
  "build": "pass",
  "lint": "pass",
  "test": "pass",
  "coverage_pct": 65,
  "coverage_fe_pct": 65,
  "review_status": "approved | approved_with_notes | needs_fix",
  "issues_found": [],
  "kg_appended": ["review-decision-xxx"]
}
```""",
}

COVERAGE_THRESHOLD = {
    "backend": "80",
    "fe": "60",
}


LAYER_META = {
    "backend": {
        "layer": "backend",
        "layer_label": "Backend / service",
        "owned_paths_hint": "`services/{bid}/` và paths trong SERVICE-BOUNDARY-MATRIX",
        "role_meta": ROLE_META,
    },
    "fe": {
        "layer": "fe",
        "layer_label": "Frontend",
        "owned_paths_hint": "app surface + `docs/architecture/ux/ux-{bid}.md` (theo matrix)",
        "role_meta": {
            **ROLE_META,
            "dev": {
                **ROLE_META["dev"],
                "skill_primary": "frontend-implementation",
                "identity": "kỹ sư frontend boundary `{bid}` (phục vụ: {serves})",
                "display": "{bid} Frontend Agent — serves {serves}",
                "mission": "Triển khai UI/FE cho backend: {serves}. Contract API theo integrations-matrix.",
            },
            "fix": {
                **ROLE_META["fix"],
                "skill_primary": "frontend-implementation",
                "identity": "kỹ sư sửa bug FE boundary `{bid}`",
                "display": "fix-{bid} Frontend Bug Fix Agent",
                "mission": "Sửa lỗi UI/FE trong owned_paths; ghi `tracking/waves/{wave-id}/bugs/`.",
            },
            "review": {
                **ROLE_META["review"],
                "skill_primary": "self-review",
                "identity": "reviewer FE boundary `{bid}`",
                "display": "review-{bid} Frontend Self-Review Agent",
                "mission": "Rà soát chất lượng FE trước handoff QA.",
            },
        },
    },
}


@dataclass
class RosterRow:
    boundary_id: str
    layer: str
    waves: list[str]
    serves_boundaries: list[str]
    fe_surface: str
    display_name: str


def _all_waves_from_roadmap() -> list[str]:
    p = repo_root() / "docs/plans/project/waves-roadmap.md"
    if p.is_file():
        return parse_wave_ids_from_roadmap(p)
    return ["wave-001"]


def parse_waves_field(raw: str, all_waves: list[str] | None = None) -> list[str]:
    all_waves = all_waves or _all_waves_from_roadmap()
    s = (raw or "").strip()
    if not s or s in ("—", "-", "n/a", "N/A"):
        return list(all_waves)
    if s.lower() == "all":
        return list(all_waves)
    out: list[str] = []
    for part in re.split(r"[,;]", s):
        part = part.strip()
        if part:
            out.append(normalize_wave_id(part))
    return sorted(set(out))


def waves_yaml_block(waves: list[str], scope: str) -> str:
    lines = ["waves:"]
    for w in waves:
        lines.append(f"  - id: {w}")
        lines.append(f'    scope: "{scope}"')
    return "\n".join(lines)


def waves_table_md(waves: list[str], scope: str, mission: str) -> str:
    hdr = "| Wave | Phạm vi | Vai trò boundary |\n|------|---------|------------------|\n"
    rows = "\n".join(f"| `{w}` | {scope} | {mission} |" for w in waves)
    return hdr + rows


def waves_list_human(waves: list[str]) -> str:
    return ", ".join(f"`{w}`" for w in waves) if waves else "—"


def layer_for_boundary(boundary_id: str, layer_col: str | None = None) -> str:
    if layer_col and layer_col.strip().lower() in FE_LAYERS:
        return "fe"
    if boundary_id in FE_BOUNDARY_IDS:
        return "fe"
    return "backend"


def _template() -> str:
    return (repo_root() / "agents" / "_template.agent.md").read_text(encoding="utf-8")


def parse_roster_row(path: Path) -> list[RosterRow]:
    text = path.read_text(encoding="utf-8")
    rows: list[RosterRow] = []
    for line in text.splitlines():
        if "|" not in line or "---" in line or "boundary_id" in line.lower():
            continue
        cols = [c.strip() for c in line.split("|") if c.strip()]
        if not cols or not re.match(r"^[a-z][a-z0-9_-]*$", cols[0]):
            continue
        bid = cols[0]
        layer_col = cols[1] if len(cols) > 1 else ""
        waves_raw = cols[2] if len(cols) > 2 else ""
        serves_raw = cols[3] if len(cols) > 3 else ""
        fe_surface = cols[4] if len(cols) > 4 else ""
        if serves_raw in ("—", "-", "n/a", "N/A"):
            serves_raw = ""
        all_w = _all_waves_from_roadmap()
        serves = [
            s.strip()
            for s in serves_raw.replace(";", ",").split(",")
            if s.strip() and s.strip() not in ("—", "-")
        ]
        lyr = layer_for_boundary(bid, layer_col)
        rows.append(
            RosterRow(
                boundary_id=bid,
                layer=lyr,
                waves=parse_waves_field(waves_raw, all_w),
                serves_boundaries=serves,
                fe_surface=fe_surface or ("web-app" if lyr == "fe" else ""),
                display_name=bid.replace("-", " ").title(),
            )
        )
    return rows


def parse_roster(path: Path) -> tuple[str, list[str]]:
    rows = parse_roster_row(path)
    wave = "wave-001"
    m = re.search(r"wave-\d{3}", path.read_text(encoding="utf-8"), re.I)
    if m:
        wave = m.group(0).lower()
    if rows:
        return wave, [r.boundary_id for r in rows]
    text = path.read_text(encoding="utf-8")
    boundaries: list[str] = []
    for line in text.splitlines():
        if "|" not in line or "---" in line or "boundary_id" in line:
            continue
        cols = [c.strip() for c in line.split("|") if c.strip()]
        if cols and re.match(r"^[a-z][a-z0-9_-]*$", cols[0]):
            boundaries.append(cols[0])
    return wave, sorted(set(boundaries))


def _fill(
    template: str,
    *,
    row: RosterRow,
    role_key: str,
    wave: str,
    wave_scope: str,
) -> str:
    layer_key = row.layer
    layer = LAYER_META[layer_key]
    meta = layer["role_meta"][role_key]
    serves = ", ".join(row.serves_boundaries) if row.serves_boundaries else "—"
    owned = layer["owned_paths_hint"].format(bid=row.boundary_id)
    serves_yaml = str(row.serves_boundaries) if row.serves_boundaries else "[]"
    convention = "frontend-conventions" if row.layer == "fe" else "backend-conventions"
    mission = meta["mission"].format(bid=row.boundary_id, serves=serves)
    wlist = row.waves or [normalize_wave_id(wave)]
    # Inject layer_block FIRST so inner placeholders ({{boundary_id}}, {{skill_primary}}) get resolved by subsequent .replace() calls
    return (
        template.replace("{{layer_block}}", LAYER_BLOCKS.get(row.layer, LAYER_BLOCKS["backend"]))
        .replace("{{boundary_id}}", row.boundary_id)
        .replace("{{layer}}", layer["layer"])
        .replace("{{layer_label}}", layer["layer_label"])
        .replace("{{owned_paths_hint}}", owned)
        .replace("{{prefix}}", meta["prefix"])
        .replace("{{role}}", role_key)
        .replace("{{role_key}}", REGISTRY_ROLE_KEY.get((row.layer, role_key), role_key))
        .replace("{{role_label}}", meta["role_label"])
        .replace("{{primary_command}}", meta["primary_command"])
        .replace("{{spawn_stage}}", meta["spawn_stage"])
        .replace("# {{waves_yaml}}", waves_yaml_block(wlist, wave_scope))
        .replace("{{waves_list_human}}", waves_list_human(wlist))
        .replace("{{waves_table_md}}", waves_table_md(wlist, wave_scope, mission))
        .replace("{{role_mission}}", mission)
        .replace("{{identity_one_liner}}", meta["identity"].format(bid=row.boundary_id, serves=serves))
        .replace("{{agent_display_name}}", meta["display"].format(bid=row.boundary_id, serves=serves))
        .replace("{{role_forbidden}}", meta["forbidden"].format(bid=row.boundary_id))
        .replace("{{skill_primary}}", meta["skill_primary"])
        .replace("{{serves_boundaries_yaml}}", serves_yaml)
        .replace("{{fe_surface}}", row.fe_surface or "—")
        .replace("{{display_name}}", row.display_name)
        .replace("{{convention_skill}}", convention)
        .replace("{{pattern_skill}}", "ref-back-end-pattern" if row.layer == "backend" else "ref-front-end-pattern")
        .replace("{{config_skill}}", "ref-back-end-config" if row.layer == "backend" else "ref-front-end-config")
        .replace("{{coverage_threshold}}", COVERAGE_THRESHOLD.get(row.layer, "80"))
    )


def materialize(
    boundaries: list[str],
    wave: str,
    *,
    roster_rows: list[RosterRow] | None = None,
    wave_scope: str = "Theo wave-plan",
    dry_run: bool = False,
    force: bool = False,
) -> list[str]:
    root = repo_root()
    template = _template()
    created: list[str] = []

    row_by_id = {r.boundary_id: r for r in (roster_rows or [])}
    for bid in boundaries:
        bid = bid.strip()
        if not bid:
            continue
        row = row_by_id.get(bid)
        if not row:
            row = RosterRow(
                boundary_id=bid,
                layer=layer_for_boundary(bid),
                waves=[normalize_wave_id(wave)],
                serves_boundaries=[],
                fe_surface="web-app" if layer_for_boundary(bid) == "fe" else "",
                display_name=bid.replace("-", " ").title(),
            )
        for role_key in ("dev", "fix", "review"):
            meta = LAYER_META[row.layer]["role_meta"][role_key]
            name = f"{meta['prefix']}{bid}-agent.md"
            path = root / "agents" / name
            content = _fill(
                template,
                row=row,
                role_key=role_key,
                wave=wave,
                wave_scope=wave_scope,
            )
            rel = str(path.relative_to(root))
            if dry_run:
                created.append(rel)
                continue
            if path.is_file() and not force:
                continue
            path.write_text(content, encoding="utf-8")
            created.append(rel)
    return created


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wave", default="wave-001")
    ap.add_argument("--wave-scope", default="Theo wave-plan")
    ap.add_argument("--boundaries", help="comma-separated boundary ids")
    ap.add_argument("--from-roster", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    roster_rows: list[RosterRow] | None = None
    if args.from_roster:
        p = args.from_roster if args.from_roster.is_absolute() else repo_root() / args.from_roster
        wave, boundaries = parse_roster(p)
        roster_rows = parse_roster_row(p)
    elif args.boundaries:
        wave = args.wave.replace("_", "-")
        boundaries = [b.strip() for b in args.boundaries.split(",") if b.strip()]
    else:
        ap.error("need --boundaries or --from-roster")

    created = materialize(
        boundaries,
        wave,
        roster_rows=roster_rows,
        wave_scope=args.wave_scope,
        dry_run=args.dry_run,
        force=args.force,
    )
    for p in created:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
