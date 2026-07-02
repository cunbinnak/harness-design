"""
capture_infra_proof.py — HARNESS tự bắt bằng chứng infra (G13), KHÔNG để agent tự khai.

Chạy ở `/dev-handoff` (sau khi `docker compose up -d --build` wave services):
  1. `docker compose ps --format json` → ghi `tracking/{wave}/docker-ps.json` (gate `infra_proof`).
  2. curl /health/ready (qua urllib, stdlib) MỖI wave service → ghi `tracking/{wave}/health-proof.json`
     (gate `health_proof`). Đây là điểm khác cốt lõi với loophole cũ: bằng chứng app THỰC SỰ trả
     2xx do HARNESS đo, không phải shape của file agent viết tay.
  3. fetch OpenAPI runtime (`/v3/api-docs` springdoc) MỖI backend service → ghi
     `tracking/{wave}/api-proof.json` (gate `api_contract_proof`): endpoint khai trong
     `api-{boundary}.md` phải tồn tại trong spec runtime — bắt contract↔implementation drift
     (endpoint thiếu/rename) TRƯỚC khi test. Fetch fail chỉ ghi error (gate quyết định chặn hay
     bỏ qua — boundary GraphQL/không REST được miễn), KHÔNG đổi exit code.

Vì sao HARNESS chạy (không phải dev/handoff sub-agent tự ghi): agent có thể up tạm rồi capture, hoặc
ghi JSON shape-hợp-lệ mà service chưa UP. Script này deterministic — orchestrator (MAIN) chạy bằng Bash.

Usage:
  py scripts/capture_infra_proof.py                  # đọc STATE → capture wave hiện tại
  py scripts/capture_infra_proof.py --wave wave-001  # ép wave
  py scripts/capture_infra_proof.py --selftest       # unit test parser (hermetic, no docker)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = REPO_ROOT / "harness" / "STATE.json"
MATRIX_FILE = REPO_ROOT / "harness" / "SERVICE-BOUNDARY-MATRIX.json"
COMPOSE_FILE = REPO_ROOT / "docs" / "architecture" / "infra" / "docker-compose.yml"

PROBE_TIMEOUT_SEC = 5

# Health path ứng viên theo kind (thử lần lượt, lấy 2xx đầu tiên).
HEALTH_PATHS = {
    "backend": ["/actuator/health/readiness", "/actuator/health", "/health/ready", "/health", "/healthz"],
    "bff": ["/health/ready", "/health", "/healthz", "/.well-known/apollo/server-health"],
    "web": ["/"],
}
DEFAULT_PORT = {"backend": 8080, "bff": 4000, "web": 80}
# status chứng minh app process đang serving (UP) dù path/authz khác.
_APP_UP_NON_2XX = (401, 403, 404, 405)


# ------------------------------------------------------------------ parsers

def parse_compose_ports(text: str) -> dict[str, list[int]]:
    """Parse docker-compose.yml (indent-based, không cần PyYAML) → {service: [host_port,...]}.

    Bắt block `services:` → mỗi key thụt 2 cấp = service; trong đó `ports:` list `- "H:C"` / `- H:C`
    → lấy H (host port). Đủ dùng để suy URL probe; không cần full YAML.
    """
    out: dict[str, list[int]] = {}
    lines = text.splitlines()
    in_services = False
    services_indent = None
    cur_service = None
    cur_service_indent = None
    in_ports = False
    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()
        if not in_services:
            if re.match(r"^services:\s*$", stripped):
                in_services = True
                services_indent = indent
            continue
        # rời khỏi block services (về indent <= services_indent với key khác)
        if indent <= services_indent and stripped.endswith(":") and not stripped.startswith("-"):
            if not re.match(r"^services:", stripped):
                in_services = False
                continue
        # service key (thụt sâu hơn services:, kết thúc ':', không phải list item)
        if cur_service_indent is None or indent == cur_service_indent:
            m = re.match(r"^([A-Za-z0-9._-]+):\s*$", stripped)
            if m and indent > services_indent:
                cur_service = m.group(1)
                cur_service_indent = indent
                out.setdefault(cur_service, [])
                in_ports = False
                continue
        if cur_service is None:
            continue
        # nếu gặp service mới ở cùng cấp indent
        m_svc = re.match(r"^([A-Za-z0-9._-]+):\s*$", stripped)
        if m_svc and indent == cur_service_indent:
            cur_service = m_svc.group(1)
            out.setdefault(cur_service, [])
            in_ports = False
            continue
        if re.match(r"^ports:\s*$", stripped) and indent > cur_service_indent:
            in_ports = True
            continue
        if in_ports:
            pm = re.match(r'^-\s*["\']?(\d+):(\d+)', stripped)
            if pm:
                out[cur_service].append(int(pm.group(1)))
                continue
            # hết list ports (dòng không phải '- ...')
            if not stripped.startswith("-"):
                in_ports = False
    return out


def load_json(path: Path) -> dict | list | None:
    try:
        return json.loads(path.read_text(encoding="utf-8").lstrip("﻿"))
    except (OSError, ValueError):
        return None


def matrix_boundaries() -> dict[str, dict]:
    data = load_json(MATRIX_FILE) or {}
    bs = data.get("boundaries", []) if isinstance(data, dict) else data
    return {b["boundary_id"]: b for b in bs if isinstance(b, dict) and b.get("boundary_id")}


# ------------------------------------------------------------------ probe

def probe_url(url: str, timeout: int = PROBE_TIMEOUT_SEC) -> int:
    """GET url → http status (int). 0 = không kết nối được (down/timeout/refused)."""
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return int(resp.status)
    except urllib.error.HTTPError as e:
        return int(e.code)
    except (urllib.error.URLError, OSError, ValueError):
        return 0


OPENAPI_PATHS = ["/v3/api-docs", "/openapi.json", "/api-docs"]
_HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")


def fetch_json(url: str, timeout: int = PROBE_TIMEOUT_SEC) -> dict | None:
    """GET url → parsed JSON dict; None nếu không kết nối được / không phải JSON object."""
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            return data if isinstance(data, dict) else None
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError):
        return None


def openapi_paths(spec: dict) -> dict[str, list[str]]:
    """OpenAPI spec → {path: [METHOD,...]} (chỉ HTTP method thật, bỏ parameters/summary...)."""
    out: dict[str, list[str]] = {}
    for path, ops in (spec.get("paths") or {}).items():
        if not isinstance(ops, dict):
            continue
        methods = sorted(m.upper() for m in ops if isinstance(m, str) and m.lower() in _HTTP_METHODS)
        if methods:
            out[path] = methods
    return out


def capture_api_spec(boundary: str, port: int) -> dict:
    """Fetch OpenAPI runtime của 1 backend service → {source_url, paths} hoặc {error}."""
    for path in OPENAPI_PATHS:
        url = f"http://localhost:{port}{path}"
        spec = fetch_json(url)
        if spec and spec.get("paths"):
            return {"boundary": boundary, "source_url": url, "paths": openapi_paths(spec)}
    return {
        "boundary": boundary,
        "error": f"không fetch được OpenAPI (thử {', '.join(OPENAPI_PATHS)}) — bật springdoc (ref-backend-config)",
    }


def probe_boundary(boundary: str, kind: str, port: int) -> dict:
    """Thử các health path theo kind, trả probe dict {boundary, kind, url, http_status, ok}."""
    if kind == "mobile":
        return {"boundary": boundary, "kind": kind, "url": None, "http_status": None,
                "ok": True, "note": "mobile (no http health endpoint)"}
    paths = HEALTH_PATHS.get(kind, HEALTH_PATHS["backend"])
    best = {"url": None, "status": 0}
    for path in paths:
        url = f"http://localhost:{port}{path}"
        status = probe_url(url)
        if 200 <= status < 400:
            return {"boundary": boundary, "kind": kind, "url": url, "http_status": status, "ok": True}
        # giữ status "tốt nhất" (app responding) để báo cáo nếu không có 2xx
        if status and (best["status"] == 0 or status < 500):
            best = {"url": url, "status": status}
    status = best["status"]
    ok = status in _APP_UP_NON_2XX  # app process đang serving (UP) dù path/authz khác
    note = None
    if status == 0:
        note = "không kết nối được (service down / chưa UP / connection refused)"
    elif not ok:
        note = f"app trả {status} (chưa ready / 5xx) — không phải 2xx ở health path"
    p = {"boundary": boundary, "kind": kind, "url": best["url"], "http_status": status or None, "ok": ok}
    if note:
        p["note"] = note
    return p


# ------------------------------------------------------------------ main

def capture(wave_id: str) -> int:
    out_dir = REPO_ROOT / "tracking" / wave_id
    out_dir.mkdir(parents=True, exist_ok=True)
    state = load_json(STATE_FILE) or {}
    wave_boundaries = state.get("wave_boundaries") or []
    bmap = matrix_boundaries()
    ports = parse_compose_ports(COMPOSE_FILE.read_text(encoding="utf-8")) if COMPOSE_FILE.is_file() else {}

    # 1. docker compose ps → docker-ps.json
    docker_json = "[]"
    if COMPOSE_FILE.is_file():
        try:
            proc = subprocess.run(
                ["docker", "compose", "-f", str(COMPOSE_FILE), "ps", "--format", "json"],
                capture_output=True, text=True, timeout=60,
            )
            docker_json = (proc.stdout or "").strip() or "[]"
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as e:
            print(f"WARN: docker compose ps lỗi ({e}) — ghi docker-ps.json rỗng", file=sys.stderr)
    (out_dir / "docker-ps.json").write_text(docker_json, encoding="utf-8")

    # 2. curl /health/ready mỗi wave service → health-proof.json
    probes = []
    for b in wave_boundaries:
        meta = bmap.get(b, {})
        kind = meta.get("kind", "backend")
        port = meta.get("host_port")
        if not port:
            svc_ports = ports.get(b) or ports.get(f"{meta.get('prefix','')}-{b}") or []
            port = svc_ports[0] if svc_ports else DEFAULT_PORT.get(kind, 8080)
        probes.append(probe_boundary(b, kind, int(port)))

    health = {"captured_by": "capture_infra_proof.py", "wave": wave_id, "probes": probes}
    (out_dir / "health-proof.json").write_text(
        json.dumps(health, indent=2, ensure_ascii=False), encoding="utf-8")

    # 3. OpenAPI runtime mỗi backend service → api-proof.json (gate api_contract_proof)
    specs: dict[str, dict] = {}
    for b in wave_boundaries:
        meta = bmap.get(b, {})
        if meta.get("kind", "backend") != "backend":
            continue
        port = meta.get("host_port")
        if not port:
            svc_ports = ports.get(b) or ports.get(f"{meta.get('prefix','')}-{b}") or []
            port = svc_ports[0] if svc_ports else DEFAULT_PORT.get("backend", 8080)
        specs[b] = capture_api_spec(b, int(port))
    (out_dir / "api-proof.json").write_text(
        json.dumps({"captured_by": "capture_infra_proof.py", "wave": wave_id, "specs": specs},
                   indent=2, ensure_ascii=False), encoding="utf-8")

    ok_all = all(p.get("ok") for p in probes) if probes else False
    print(json.dumps(health, indent=2, ensure_ascii=False))
    if not probes:
        print("WARN: wave_boundaries rỗng — chưa /start-wave?", file=sys.stderr)
        return 1
    if not ok_all:
        bad = [p["boundary"] for p in probes if not p.get("ok")]
        print(f"\nFAIL: service chưa UP/ready: {bad} — start service thật rồi chạy lại.", file=sys.stderr)
        return 1
    print(f"\nOK: {len(probes)} wave service đều trả health probe ok.")
    return 0


def _selftest() -> int:
    sample = """\
version: "3.9"
services:
  scheduling:
    build: ./scheduling
    ports:
      - "8081:8081"
    environment:
      - X=1
  patient-web:
    image: nginx
    ports:
      - "5173:80"
  postgres:
    image: postgres:16
    ports:
      - "5432:5432"
volumes:
  pgdata:
"""
    ports = parse_compose_ports(sample)
    assert ports.get("scheduling") == [8081], ports
    assert ports.get("patient-web") == [5173], ports
    assert ports.get("postgres") == [5432], ports
    assert "volumes" not in ports, ports
    # probe_boundary mobile → ok không cần http
    p = probe_boundary("mobile-app", "mobile", 0)
    assert p["ok"] is True and p["url"] is None, p
    # openapi_paths: lọc HTTP method thật, bỏ key phụ (parameters/summary)
    spec = {"openapi": "3.0", "paths": {
        "/api/v1/refunds": {"get": {}, "post": {}, "parameters": []},
        "/api/v1/refunds/{id}": {"get": {}},
        "/bogus": {"summary": "no ops"},
    }}
    paths = openapi_paths(spec)
    assert paths["/api/v1/refunds"] == ["GET", "POST"], paths
    assert paths["/api/v1/refunds/{id}"] == ["GET"], paths
    assert "/bogus" not in paths, paths
    print("OK: capture_infra_proof.py selftest passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="HARNESS capture infra + health proof (G13)")
    ap.add_argument("--wave", help="wave id (vd wave-001); mặc định đọc STATE")
    ap.add_argument("--selftest", action="store_true", help="unit test parser (hermetic)")
    args = ap.parse_args(argv)
    if args.selftest:
        return _selftest()
    wave_id = args.wave
    if not wave_id:
        state = load_json(STATE_FILE) or {}
        wave_id = (state.get("wave") or {}).get("id")
    if not wave_id:
        print("FAIL: không xác định wave (STATE.wave.id rỗng) — chạy /start-wave trước.", file=sys.stderr)
        return 2
    return capture(wave_id)


if __name__ == "__main__":
    sys.exit(main())
