"""The player-facing view model.

One payload for the whole shell, shaped by what a player needs to see:
the story, the character, the goal, the people, the world.  It intentionally
does not expose the old 38-field dashboard or developer diagnostics.
"""

from __future__ import annotations

import os

from game_engine import model_config, panel
from game_engine.state_schema import load_state


def _turns(state: dict) -> list:
    rows = state.get("turns") if isinstance(state.get("turns"), list) else []
    return [r for r in rows if isinstance(r, dict)]


def _feed(vm: dict, state: dict) -> list:
    turns = _turns(state)
    items = []
    if turns:
        for turn in turns[-80:]:
            role = str(turn.get("role") or "")
            text = str(turn.get("text") or "").strip()
            if role not in ("player", "assistant") or not text:
                continue
            items.append({
                "id": str(turn.get("id") or ""),
                "role": "player" if role == "player" else "narrator",
                "tick": int(turn.get("tick", 0) or 0),
                "text": text,
                "tools": [str(t) for t in (turn.get("tools") or [])][:8],
                "status": str(turn.get("status") or ""),
                "_order": 0 if role == "player" else 1,
            })
    else:
        prose = ((vm.get("prose") or {}).get("items") or [])
        seen = set()
        for entry in prose:
            text = str(entry.get("text") or "").strip()
            # Old saves append dashboard-ish recaps to the prose. Drop that
            # suffix for the player feed; the structured rail already carries it.
            for marker in ("刚才发生的事还压在心上", "世界的相位落在"):
                if marker in text:
                    text = text.split(marker)[0].rstrip("。 ，, ")
            # Old saves often contain near-identical scene recaps; keep the
            # feed readable instead of repeating the same paragraph seven times.
            fingerprint = text[:90]
            if text and fingerprint not in seen:
                seen.add(fingerprint)
                items.append({
                    "id": "prose-%s" % entry.get("tick", 0),
                    "role": "narrator",
                    "tick": int(entry.get("tick", 0) or 0),
                    "text": text,
                    "tools": [],
                    "status": "ok",
                    "_order": 1,
                })

    checks = ((vm.get("game") or {}).get("checks") or [])
    for row in checks:
        level = str(row.get("level_label") or row.get("level") or "")
        if not level:
            continue
        items.append({
            "id": "check-%s-%s" % (row.get("tick", 0), row.get("dice", "")),
            "role": "check",
            "tick": int(row.get("tick", 0) or 0),
            "text": "%s · %s %s vs %s（%s）" % (
                row.get("actor") or "玩家", row.get("attribute") or "判定",
                row.get("dice") or "", row.get("difficulty", 0), level),
            "tools": [],
            "status": "ok",
            "_order": 2,
        })

    items.sort(key=lambda row: (row["tick"], row["_order"], row["id"]))
    for row in items:
        row.pop("_order", None)
    return items[-80:]


def _places(state: dict) -> list:
    raw = state.get("places") if isinstance(state.get("places"), dict) else {}
    rows = []
    for name, info in sorted(raw.items()):
        if not isinstance(info, dict):
            info = {"desc": str(info or "")}
        rows.append({
            "name": str(name),
            "desc": str(info.get("desc") or ""),
            "last_prose": str(info.get("last_prose") or ""),
            "last_tick": int(info.get("last_tick", info.get("tick", 0)) or 0),
        })
    return rows


def build_player_view(state_path: str) -> dict:
    state = load_state(state_path)
    vm = panel.view_model(state_path)
    world = vm.get("world") or {}
    player = vm.get("player") or {}
    game = vm.get("game") or {}
    world_state = vm.get("world_state") or {}
    quests = vm.get("quests") or {}

    model = model_config.public_config()
    return {
        "ok": True,
        "world": {
            "name": str(world.get("name") or "未命名世界"),
            "era": str(world.get("era") or ""),
            "location_desc": str(world.get("location_desc") or ""),
            "tick": int(vm.get("tick", 0) or 0),
            "updated_at": str(vm.get("updated_at") or ""),
            "phase": world_state.get("phase"),
        },
        "scene": vm.get("scene") or {},
        "player": {
            "name": player.get("name") or "玩家",
            "level": player.get("level") or "",
            "location": player.get("location") or "",
            "hp": player.get("hp", 0),
            "hp_max": player.get("hp_max", 1),
            "mp": player.get("mp", 0),
            "mp_max": player.get("mp_max", 0),
            "gold": player.get("gold", 0),
            "currency": player.get("currency") or "钱财",
            "attrs": player.get("attrs") or {},
            "inventory": player.get("inventory") or [],
            "karma": player.get("karma"),
            "moral": vm.get("moral") or {},
        },
        "feed": _feed(vm, state),
        "rail": {
            "character": {
                "player": player,
                "game": game.get("profile") or {},
                "checks": game.get("checks") or [],
                "systems": (vm.get("systems") or {}).get("rows") or [],
                "insights": vm.get("insights") or {},
            },
            "quests": {
                "playbook": vm.get("playbook") or {},
                "rows": quests.get("rows") or [],
                "total": quests.get("total", 0),
                "next_moves": vm.get("next_moves") or [],
                "milestones": vm.get("milestones") or [],
            },
            "relations": {
                "present": vm.get("present") or [],
                "others": vm.get("others") or [],
                "relations": vm.get("relations") or [],
            },
            "world": {
                "summary": world_state,
                "flags": vm.get("flags") or [],
                "market": vm.get("market") or [],
                "places": _places(state),
                "lore_total": vm.get("lore_total", 0),
            },
        },
        "world_overlay": {
            "codex": vm.get("codex") or {},
            "lorebook": vm.get("lorebook") or {},
            "events": vm.get("events") or [],
            "market": vm.get("market") or [],
            "milestones": vm.get("milestones") or [],
            "places": _places(state),
            "world_state": world_state,
            "flags": vm.get("flags") or [],
            "summaries": vm.get("summaries", 0),
            "archived_events": vm.get("archived_events", 0),
        },
        "model": model,
        "meta": {
            "turn_count": len(_turns(state)),
            "state_path": os.path.abspath(state_path),
            "read_only": True,
        },
    }
