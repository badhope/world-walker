"""Read-only story replay and share text.

The panel already renders a live feed, but a player who wants to remember what
happened three nights ago had to scroll.  This module turns the persisted
`turns` (and, for older saves, `prose`) into a chronological timeline that can
be shown in a replay drawer or exported as a Markdown battle report.

It is deliberately independent of the model and of the panel HTTP layer: tests
can feed a state dict and assert the order, the player/narrator roles and the
turn delta without starting a server.
"""

from __future__ import annotations

from datetime import datetime, timezone

MAX_TIMELINE = 240


def _dict(value):
    return value if isinstance(value, dict) else {}


def _text(value):
    return str(value if value is not None else "").strip()


def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _turn_items(state: dict) -> list[dict]:
    rows = state.get("turns") if isinstance(state.get("turns"), list) else []
    out = []
    for turn in rows[-MAX_TIMELINE:]:
        if not isinstance(turn, dict):
            continue
        role = _text(turn.get("role"))
        text = _text(turn.get("text"))
        if role not in ("player", "assistant") or not text:
            continue
        out.append({
            "id": _text(turn.get("id")),
            "kind": "player" if role == "player" else "narrator",
            "tick": _int(turn.get("tick"), 0),
            "text": text,
            "tools": [str(t) for t in (turn.get("tools") or [])][:8],
            "delta": turn.get("delta") if isinstance(turn.get("delta"), dict) else None,
            "ts": _text(turn.get("ts")),
            "_order": 1 if role == "player" else 2,
        })
    return out


def _prose_items(state: dict, turn_items: list[dict]) -> list[dict]:
    prose = state.get("prose") if isinstance(state.get("prose"), list) else []
    seen = {_text(row.get("text"))[:90] for row in turn_items if row.get("text")}
    first_turn_tick = min((row["tick"] for row in turn_items), default=None)
    out = []
    for index, entry in enumerate(prose):
        if not isinstance(entry, dict):
            continue
        text = _text(entry.get("text"))
        fingerprint = text[:90]
        if not text or fingerprint in seen:
            continue
        tick = _int(entry.get("tick"), 0)
        if turn_items and first_turn_tick is not None and tick > first_turn_tick:
            continue
        seen.add(fingerprint)
        out.append({
            "id": "prose-%s-%s" % (tick, index),
            "kind": "narrator",
            "tick": tick,
            "text": text,
            "tools": [],
            "delta": None,
            "ts": "",
            "_order": 0,
        })
    return out


def _opening_item(state: dict, rows: list[dict]) -> dict | None:
    """The cold open is part of the story, but older saves stored it only as prose."""
    world = state.get("world_info") if isinstance(state.get("world_info"), dict) else {}
    raw = world.get("prologue")
    if isinstance(raw, list):
        text = "\n\n".join(_text(part) for part in raw if _text(part))
    else:
        text = _text(raw)
    if not text:
        return None
    known = "\n".join(_text(row.get("text")) for row in rows)
    probe = text[:36]
    if probe and probe in known:
        return None
    return {
        "id": "opening",
        "kind": "narrator",
        "tick": 0,
        "text": text,
        "tools": [],
        "delta": None,
        "ts": "",
        "opening": True,
        "_order": -1,
    }


def timeline(state: dict) -> list[dict]:
    """Chronological player/narrator rows, oldest first, bounded to 240."""
    turns = _turn_items(state)
    prose = _prose_items(state, turns)
    rows = prose + turns
    opening = _opening_item(state, rows)
    if opening:
        rows.append(opening)
    rows.sort(key=lambda row: (row.get("tick", 0), row.get("_order", 0), row.get("id", "")))
    for row in rows:
        row.pop("_order", None)
    return rows[-MAX_TIMELINE:]


def payload(state: dict, state_path: str = "") -> dict:
    world = _dict(state.get("world_info"))
    rows = timeline(state)
    turns = [row for row in rows if row.get("kind") == "player"]
    narrations = [row for row in rows if row.get("kind") == "narrator"]
    return {
        "ok": True,
        "format": "world-walker.replay.v1",
        "world": {
            "name": _text(world.get("name")),
            "era": _text(world.get("era")),
            "tick": _int(state.get("tick"), 0),
            "mode": _text(_dict(state.get("mode")).get("label")),
        },
        "state_path": state_path,
        "timeline": rows,
        "counts": {
            "player": len(turns),
            "narrator": len(narrations),
            "total": len(rows),
        },
        "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def _delta_line(delta) -> str:
    if not isinstance(delta, dict) or delta.get("empty"):
        return ""
    parts = []
    for row in (delta.get("changes") or [])[:8]:
        if not isinstance(row, dict):
            continue
        label, before, after = _text(row.get("label")), row.get("before"), row.get("after")
        if row.get("kind") == "clock":
            parts.append("%s %s→%s" % (label, before, after))
            continue
        value = row.get("delta")
        if isinstance(value, (int, float)):
            parts.append("%s %s%s" % (label, "+" if value > 0 else "", value))
        elif before != after:
            parts.append("%s %s→%s" % (label, before, after))
    return " · ".join(parts)


def markdown(state: dict, name: str = "") -> str:
    """A portable battle report; no model keys, no hidden state, no JSON."""
    world = _dict(state.get("world_info"))
    title = name or _text(world.get("name")) or "World Walker 战报"
    rows = timeline(state)
    lines = [
        "# %s" % title,
        "",
        "> %s · 第 %s 回合 · %s" % (
            _text(world.get("era")) or "未记录年代",
            _int(state.get("tick"), 0),
            _text(_dict(state.get("mode")).get("label")) or "标准模式"),
        "",
    ]
    player = _dict(_dict(state.get("entities")).get("player"))
    if player:
        lines.extend([
            "**%s** · %s · 气血 %s/%s" % (
                _text(player.get("name")) or "无名者",
                _text(player.get("level")) or "凡人",
                player.get("hp", 0), player.get("hp_max", 0)),
            "",
        ])
    if not rows:
        lines.append("_这一局还没有留下正文。_")
        return "\n".join(lines) + "\n"

    for row in rows:
        if row.get("kind") == "player":
            lines.extend(["> **你**", ">", "> %s" % row["text"], ""])
            continue
        lines.extend([row["text"], ""])
        delta = _delta_line(row.get("delta"))
        if delta:
            lines.extend(["`结算：%s`" % delta, ""])
    lines.extend(["---", "", "由 World Walker 导出。规则、存档与战报同源。"])
    return "\n".join(lines) + "\n"
