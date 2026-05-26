"""Append decisions, learnings, backlog to knowledge-graph YAML."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from harness_lib import load_kg, save_kg, utc_now_iso


def _next_dec_id(decisions: list) -> str:
    n = 1
    for d in decisions:
        if isinstance(d, dict) and d.get("id", "").startswith("DEC-"):
            try:
                n = max(n, int(d["id"].split("-", 1)[1]) + 1)
            except ValueError:
                pass
    return f"DEC-{n:03d}"


def append_decision(graph_path: str, payload: dict[str, Any], *, updated_by: str = "script") -> str:
    data = load_kg(graph_path)
    decisions = data.setdefault("decisions", [])
    dec_id = payload.get("id") or _next_dec_id(decisions)
    entry = {
        "id": dec_id,
        "made_at": payload.get("made_at") or utc_now_iso(),
        "context": payload.get("context", ""),
        "decision": payload.get("decision", ""),
        "rationale": payload.get("rationale", ""),
        "alternatives_rejected": payload.get("alternatives_rejected", []),
        "status": payload.get("status", "active"),
        "supersedes": payload.get("supersedes"),
    }
    decisions.append(entry)
    data.setdefault("meta", {})["updated_by"] = updated_by
    save_kg(graph_path, data)
    return dec_id


def append_learning(
    graph_path: str,
    kind: str,
    text: str,
    *,
    updated_by: str = "script",
) -> None:
    data = load_kg(graph_path)
    learn = data.setdefault("learnings", {"gotchas": [], "patterns": []})
    key = "gotchas" if kind == "gotcha" else "patterns"
    if text not in learn.setdefault(key, []):
        learn[key].append(text)
    data.setdefault("meta", {})["updated_by"] = updated_by
    save_kg(graph_path, data)


def append_do_not_repeat(
    graph_path: str,
    text: str,
    *,
    updated_by: str = "script",
) -> None:
    data = load_kg(graph_path)
    disc = data.setdefault("discipline", {"do_not_repeat": [], "blockers": []})
    items = disc.setdefault("do_not_repeat", [])
    if text not in items:
        items.append(text)
    learn = data.setdefault("learnings", {"gotchas": [], "patterns": []})
    if text not in learn.setdefault("gotchas", []):
        learn["gotchas"].append(text)
    data.setdefault("meta", {})["updated_by"] = updated_by
    save_kg(graph_path, data)


def append_blocker(
    graph_path: str,
    text: str,
    *,
    updated_by: str = "script",
) -> None:
    data = load_kg(graph_path)
    disc = data.setdefault("discipline", {"do_not_repeat": [], "blockers": []})
    items = disc.setdefault("blockers", [])
    if text not in items:
        items.append(text)
    data.setdefault("meta", {})["updated_by"] = updated_by
    save_kg(graph_path, data)


def append_in_progress(
    graph_path: str,
    task_id: str,
    *,
    updated_by: str = "script",
) -> None:
    data = load_kg(graph_path)
    impl = data.setdefault("implementation", {})
    items = impl.setdefault("in_progress", [])
    if task_id not in items:
        items.append(task_id)
    data.setdefault("meta", {})["updated_by"] = updated_by
    save_kg(graph_path, data)


def append_completed(
    graph_path: str,
    task_id: str,
    *,
    updated_by: str = "script",
) -> None:
    data = load_kg(graph_path)
    impl = data.setdefault("implementation", {})
    prog = impl.setdefault("in_progress", [])
    if task_id in prog:
        prog.remove(task_id)
    done = impl.setdefault("completed", [])
    if task_id not in done:
        done.append(task_id)
    data.setdefault("meta", {})["updated_by"] = updated_by
    save_kg(graph_path, data)


def append_entity(graph_path: str, payload: dict[str, Any], *, updated_by: str = "script") -> None:
    """Add entity to domain.entities. Payload: {name, description?, attributes?, owner_boundary?}"""
    data = load_kg(graph_path)
    domain = data.setdefault("domain", {"entities": [], "relationships": []})
    entities = domain.setdefault("entities", [])
    name = payload.get("name")
    if not name:
        raise ValueError("entity requires 'name' field")
    if any(isinstance(e, dict) and e.get("name") == name for e in entities):
        return
    entities.append({
        "name": name,
        "description": payload.get("description", ""),
        "attributes": payload.get("attributes", []),
        "owner_boundary": payload.get("owner_boundary"),
    })
    data.setdefault("meta", {})["updated_by"] = updated_by
    save_kg(graph_path, data)


def append_relationship(graph_path: str, payload: dict[str, Any], *, updated_by: str = "script") -> None:
    """Add relationship. Payload: {from, to, kind (1-1|1-N|N-N|references), description?}"""
    data = load_kg(graph_path)
    domain = data.setdefault("domain", {"entities": [], "relationships": []})
    rels = domain.setdefault("relationships", [])
    fr, to, kind = payload.get("from"), payload.get("to"), payload.get("kind")
    if not (fr and to and kind):
        raise ValueError("relationship requires from, to, kind fields")
    key = (fr, to, kind)
    if any(isinstance(r, dict) and (r.get("from"), r.get("to"), r.get("kind")) == key for r in rels):
        return
    rels.append({"from": fr, "to": to, "kind": kind, "description": payload.get("description", "")})
    data.setdefault("meta", {})["updated_by"] = updated_by
    save_kg(graph_path, data)


def append_backlog(graph_path: str, task_id: str, description: str = "", *, updated_by: str = "script") -> None:
    """Add task to implementation.backlog (chưa start)."""
    data = load_kg(graph_path)
    impl = data.setdefault("implementation", {})
    items = impl.setdefault("backlog", [])
    if any((b.get("id") if isinstance(b, dict) else b) == task_id for b in items):
        return
    items.append({"id": task_id, "description": description} if description else task_id)
    data.setdefault("meta", {})["updated_by"] = updated_by
    save_kg(graph_path, data)


def append_integration(graph_path: str, direction: str, payload: dict[str, Any], *, updated_by: str = "script") -> None:
    """direction: depends_on | exposes. Payload: {boundary, contract, kind?}"""
    data = load_kg(graph_path)
    integ = data.setdefault("integrations", {"depends_on": [], "exposes": []})
    if direction not in ("depends_on", "exposes"):
        raise ValueError("direction must be depends_on or exposes")
    items = integ.setdefault(direction, [])
    boundary = payload.get("boundary")
    if not boundary:
        raise ValueError("integration requires 'boundary' field")
    if any(isinstance(i, dict) and i.get("boundary") == boundary for i in items):
        return
    items.append({
        "boundary": boundary,
        "contract": payload.get("contract", ""),
        "kind": payload.get("kind", "http"),
    })
    data.setdefault("meta", {})["updated_by"] = updated_by
    save_kg(graph_path, data)


def main() -> None:
    if len(sys.argv) < 4:
        print(
            "Usage:\n"
            "  knowledge_writer.py decision <graph.yaml> '<json>'\n"
            "  knowledge_writer.py learning <graph.yaml> gotcha|pattern '<text>'\n"
            "  knowledge_writer.py do-not-repeat <graph.yaml> '<text>'\n"
            "  knowledge_writer.py blocker <graph.yaml> '<text>'\n"
            "  knowledge_writer.py in-progress <graph.yaml> '<task_id>'\n"
            "  knowledge_writer.py completed <graph.yaml> '<task_id>'\n"
            "  knowledge_writer.py backlog <graph.yaml> '<task_id>' ['<description>']\n"
            "  knowledge_writer.py entity <graph.yaml> '<json>'\n"
            "  knowledge_writer.py relationship <graph.yaml> '<json>'\n"
            "  knowledge_writer.py integration <graph.yaml> depends_on|exposes '<json>'",
            file=sys.stderr,
        )
        sys.exit(64)
    cmd, path, arg = sys.argv[1], sys.argv[2], sys.argv[3]
    try:
        if cmd == "decision":
            payload = json.loads(arg)
            dec_id = append_decision(path, payload)
            print(f"appended decision {dec_id}")
        elif cmd == "learning":
            kind = arg
            text = sys.argv[4] if len(sys.argv) > 4 else ""
            if not text:
                print("ERROR: learning text required", file=sys.stderr)
                sys.exit(1)
            append_learning(path, kind, text)
            print(f"appended {kind}")
        elif cmd == "do-not-repeat":
            text = arg
            append_do_not_repeat(path, text)
            print("appended do_not_repeat")
        elif cmd == "blocker":
            text = arg
            append_blocker(path, text)
            print("appended blocker")
        elif cmd == "in-progress":
            append_in_progress(path, arg)
            print(f"in_progress: {arg}")
        elif cmd == "completed":
            append_completed(path, arg)
            print(f"completed: {arg}")
        elif cmd == "backlog":
            desc = sys.argv[4] if len(sys.argv) > 4 else ""
            append_backlog(path, arg, desc)
            print(f"backlog: {arg}")
        elif cmd == "entity":
            payload = json.loads(arg)
            append_entity(path, payload)
            print(f"entity: {payload.get('name')}")
        elif cmd == "relationship":
            payload = json.loads(arg)
            append_relationship(path, payload)
            print(f"relationship: {payload.get('from')} -> {payload.get('to')}")
        elif cmd == "integration":
            direction = arg
            json_str = sys.argv[4] if len(sys.argv) > 4 else "{}"
            payload = json.loads(json_str)
            append_integration(path, direction, payload)
            print(f"integration {direction}: {payload.get('boundary')}")
        else:
            print(f"unknown cmd: {cmd}", file=sys.stderr)
            sys.exit(64)
    except (RuntimeError, json.JSONDecodeError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
