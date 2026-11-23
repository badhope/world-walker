"""Portable world packs: a snapshot that another player can actually resume.

A world pack is deliberately not a spoiler-free setting bundle.  It is the
current world *as played*: places discovered, clocks filled, NPCs met, history
written.  That makes it useful for backup and for handing a campaign to a
friend, and it keeps the import path honest: the snapshot is the same state
schema the engine already validates.

Keys, model endpoints and harness hooks never live in the state file, so the
pack cannot leak them by construction.
"""

from __future__ import annotations

import copy
import json
import os
from datetime import datetime, timezone

FORMAT = "world-walker.worldpack.v1"


def _text(value, default=""):
    text = str(value if value is not None else "").strip()
    return text or default


def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def build(state: dict, *, state_path: str = "", name: str = "") -> dict:
    """Return a JSON-serializable pack with the playable state snapshot."""
    if not isinstance(state, dict):
        raise ValueError("worldpack 需要状态对象")
    world = state.get("world_info") if isinstance(state.get("world_info"), dict) else {}
    playbook = state.get("playbook") if isinstance(state.get("playbook"), dict) else {}
    entities = state.get("entities") if isinstance(state.get("entities"), dict) else {}
    player = entities.get("player") if isinstance(entities.get("player"), dict) else {}
    snapshot = copy.deepcopy(state)
    return {
        "format": FORMAT,
        "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "name": _text(name, _text(world.get("name"), "未命名世界")),
        "world": {
            "name": _text(world.get("name"), "未命名世界"),
            "era": _text(world.get("era")),
            "tick": _int(state.get("tick"), 0),
            "mode": _text((state.get("mode") or {}).get("label")),
            "playbook": _text(playbook.get("title")),
            "protagonist": _text(player.get("name")),
        },
        "source": {"file": os.path.basename(_text(state_path))} if _text(state_path) else {},
        "contains_spoilers": True,
        "snapshot": snapshot,
    }


def validate(pack: dict) -> dict:
    if not isinstance(pack, dict):
        raise ValueError("世界包必须是 JSON 对象")
    if pack.get("format") != FORMAT:
        raise ValueError("不是 World Walker 世界包（format=%r）" % pack.get("format"))
    snapshot = pack.get("snapshot")
    if not isinstance(snapshot, dict):
        raise ValueError("世界包缺少 snapshot")
    if not isinstance(snapshot.get("world_info"), dict):
        raise ValueError("世界包 snapshot 缺少 world_info")
    return pack


def state_from_pack(pack: dict) -> dict:
    validate(pack)
    snapshot = copy.deepcopy(pack["snapshot"])
    # Import is a new local copy, never a remote author's live file path.
    snapshot.pop("imported_from", None)
    snapshot["imported_from"] = {
        "format": FORMAT,
        "name": _text(pack.get("name")),
        "exported_at": _text(pack.get("exported_at")),
    }
    return snapshot


def filename(pack: dict) -> str:
    stem = _text((pack.get("world") or {}).get("name"), "world-walker")
    stem = "".join(ch if ch.isalnum() or ch in "-_·" else "-" for ch in stem).strip("-")
    return "%s.worldpack.json" % (stem or "world-walker")


def dumps(pack: dict) -> bytes:
    return json.dumps(pack, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")
