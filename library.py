"""Read-only knowledge library: prefab playbooks and design archives.

The library is shipped data, not user state.  Playbooks describe a starting
configuration (world, genre, play loop, tone, style, skill packs) that the
player can choose; archives are short design notes that explain how a world or
a mechanic came to be.  Nothing here writes a save — the normal session-zero
path does that.
"""

from __future__ import annotations

import json
import os
import re

from game_engine.rules import modes as mode_rules

def _asset_root(here: str) -> str:
    if os.path.isdir(os.path.join(here, "library")):
        return here
    parent = os.path.dirname(here)
    if os.path.isdir(os.path.join(parent, "library")):
        return parent
    return here


ROOT = _asset_root(os.path.dirname(os.path.abspath(__file__)))
LIBRARY_DIR = os.path.join(ROOT, "library")
PLAYBOOKS_DIR = os.path.join(LIBRARY_DIR, "playbooks")
ARCHIVES_DIR = os.path.join(LIBRARY_DIR, "archives")

MAX_PLAYBOOKS = 24
MAX_ARCHIVES = 16
MAX_BODY = 6000
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,39}$")


def _text(value, limit: int = 120, default: str = "") -> str:
    text = str(value if value is not None else "").strip()
    return (text[:limit] if text else default)


def _list(value, limit: int = 8) -> list[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple)):
        return []
    out = []
    for item in value:
        text = _text(item, 40)
        if text and text not in out:
            out.append(text)
    return out[:limit]


def _world(raw) -> dict:
    data = raw if isinstance(raw, dict) else {}
    kind = _text(data.get("kind"), 12)
    ident = _text(data.get("id"), 240)
    name = _text(data.get("name"), 60)
    if kind not in ("template", "setting") or not ident:
        return {}
    return {"kind": kind, "id": ident, "name": name}


def normalize_playbook(raw: dict) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("playbook 必须是对象")
    ident = _text(raw.get("id"), 40)
    if not ID_RE.match(ident):
        raise ValueError("playbook id 非法: %r" % ident)
    title = _text(raw.get("title"), 60)
    if not title:
        raise ValueError("playbook %s 缺少 title" % ident)
    world = _world(raw.get("world"))
    if not world:
        raise ValueError("playbook %s 缺少合法 world" % ident)
    genre = _text(raw.get("genre"), 20, "生存")
    play = _text(raw.get("play"), 20, "生存压力")
    difficulty = _text(raw.get("difficulty"), 8, "标准")
    mode_default = mode_rules.normalize(raw.get("mode") or difficulty)
    tone = _list(raw.get("tone"), 3) or ["克制"]
    skills = _list(raw.get("skills"), 8)
    return {
        "id": ident,
        "title": title,
        "summary": _text(raw.get("summary"), 180),
        "genre": genre,
        "play": play,
        "difficulty": difficulty,
        "mode_default": mode_default,
        "mode_label": mode_rules.MODE_SPECS[mode_default]["label"],
        "tone": tone,
        "role": _text(raw.get("role"), 12, "random"),
        "style": _text(raw.get("style"), 200),
        "world": world,
        "save_name": _text(raw.get("save_name"), 40, title),
        "skills": skills,
        "tags": _list(raw.get("tags"), 6),
        "order": int(raw.get("order") or 100),
    }


def _setting_bundle(world: dict) -> dict:
    """Read a setting bundle for its world-specific mode copy; never raise."""
    if world.get("kind") != "setting":
        return {}
    rel = os.path.normpath(str(world.get("id") or ""))
    if os.path.isabs(rel):
        return {}
    path = os.path.join(ROOT, rel)
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return {}


def _mode_specs(world: dict) -> list[dict]:
    bundle = _setting_bundle(world)
    return [
        mode_rules.summary(mode, bundle)
        for mode in mode_rules.MODE_IDS
    ]


def _world_exists(world: dict) -> bool:
    if world.get("kind") == "setting":
        rel = os.path.normpath(str(world.get("id") or ""))
        return (not os.path.isabs(rel)
                and os.path.isfile(os.path.join(ROOT, rel)))
    if world.get("kind") == "template":
        try:
            from game_engine import templates
            return str(world.get("id")) in templates.TEMPLATES
        except Exception:  # noqa: BLE001
            return False
    return False


def list_playbooks() -> list[dict]:
    try:
        names = sorted(n for n in os.listdir(PLAYBOOKS_DIR) if n.endswith(".json"))
    except OSError:
        return []
    rows = []
    for name in names[:MAX_PLAYBOOKS]:
        path = os.path.join(PLAYBOOKS_DIR, name)
        try:
            with open(path, encoding="utf-8") as fh:
                row = normalize_playbook(json.load(fh))
            if not _world_exists(row["world"]):
                continue
            row["mode_specs"] = _mode_specs(row["world"])
            rows.append(row)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
    rows.sort(key=lambda row: (row["order"], row["title"]))
    try:
        from game_engine import harness_config
        names = {item["id"]: item["name"] for item in harness_config.skill_catalog()}
    except Exception:  # noqa: BLE001 - a missing skill catalog should not blank the library
        names = {}
    for row in rows:
        row["skill_labels"] = [names.get(skill, skill) for skill in row["skills"]]
    return rows


def get_playbook(ident: str) -> dict:
    key = _text(ident, 40)
    for row in list_playbooks():
        if row["id"] == key:
            return row
    raise ValueError("预制玩法不存在: %r" % key)


def playbook_narrative(row: dict) -> dict:
    """The exact payload `/api/v1/new` accepts, with prefab provenance."""
    return {
        "genre": row["genre"],
        "play": row["play"],
        "role": row["role"],
        "tone": list(row["tone"]),
        "difficulty": row["difficulty"],
        "mode": row["mode_default"],
        "style": row["style"],
        "world_kind": row["world"]["kind"],
        "world_id": row["world"]["id"],
        "world_name": row["world"]["name"],
        "skill_ids": list(row["skills"]),
        "prefab": row["id"],
    }


def _archive_file(name: str) -> dict:
    path = os.path.join(ARCHIVES_DIR, name)
    try:
        with open(path, encoding="utf-8") as fh:
            body = fh.read(MAX_BODY)
    except OSError:
        return {}
    title = ""
    summary = ""
    tags = []
    for line in body.splitlines():
        stripped = line.strip()
        if not title and stripped.startswith("# "):
            title = stripped[2:].strip()[:60]
        elif not summary and stripped.startswith("> "):
            summary = stripped[2:].strip()[:180]
        elif stripped.startswith(("标签：", "Tags:")):
            raw = stripped.split("：", 1)[-1].split(":", 1)[-1]
            tags = _list([x.strip() for x in re.split(r"[,，、]", raw) if x.strip()], 6)
    if not title:
        title = os.path.splitext(name)[0]
    return {
        "id": os.path.splitext(name)[0],
        "title": title,
        "summary": summary,
        "tags": tags,
        "body": body,
        "path": "library/archives/" + name,
    }


def list_archives() -> list[dict]:
    try:
        names = sorted(n for n in os.listdir(ARCHIVES_DIR) if n.endswith(".md"))
    except OSError:
        return []
    rows = []
    for name in names[:MAX_ARCHIVES]:
        row = _archive_file(name)
        if row:
            rows.append(row)
    return rows


def payload() -> dict:
    playbooks = list_playbooks()
    archives = list_archives()
    return {
        "ok": True,
        "playbooks": playbooks,
        "archives": archives,
        "modes": mode_rules.catalog(),
        "counts": {"playbooks": len(playbooks), "archives": len(archives)},
        "root": LIBRARY_DIR,
    }
