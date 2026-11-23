"""Small, deterministic summaries of what a turn changed.

The panel used to show the new numbers but not the movement.  A player could
see HP 30/45 after a fight and still have to remember whether it was 45/45 a
minute ago.  This module compares two engine states and returns only the
changes a person can act on: resources, items, clocks, location, flags and the
scene.  It never guesses and never writes.

The summary is deliberately JSON-only and bounded so it can travel through a
turn record, an action-log line or an HTTP response without inflating saves.
"""

from __future__ import annotations

from typing import Any

MAX_CHANGES = 12
MAX_LABEL = 24

_KIND_ORDER = {
    "resource": 0,
    "clock": 1,
    "item": 2,
    "weapon": 3,
    "location": 4,
    "scene": 5,
    "flag": 6,
    "relation": 7,
}


def _dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _number(value: Any):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    return None


def _text(value: Any) -> str:
    return str(value if value is not None else "").strip()


def _label(value: Any, fallback: str = "") -> str:
    text = _text(value)
    return text[:MAX_LABEL] if text else fallback


def _player(state: dict) -> dict:
    return _dict(_dict(state.get("entities")).get("player"))


def _catalog(state: dict) -> dict:
    return _dict(state.get("item_catalog"))


def _item_name(*states: dict, key: str) -> str:
    for state in states:
        row = _dict(_catalog(state).get(key))
        name = _label(row.get("name") or row.get("label"))
        if name:
            return name
    return key


def _entity_label(state: dict, entity_id: str) -> str:
    ent = _dict(_dict(state.get("entities")).get(entity_id))
    return _label(ent.get("name"), entity_id)


def _change(key: str, label: str, before: Any, after: Any, kind: str, *,
            delta: Any = None, tone: str = "") -> dict:
    row = {
        "key": key,
        "label": _label(label, key),
        "before": before,
        "after": after,
        "kind": kind,
    }
    if delta is not None:
        row["delta"] = delta
    row["tone"] = tone or ("up" if isinstance(delta, (int, float)) and delta > 0
                           else "down" if isinstance(delta, (int, float)) and delta < 0
                           else "neutral")
    return row


def _num_delta(before: Any, after: Any):
    b, a = _number(before), _number(after)
    if b is None or a is None or b == a:
        return None
    return a - b


def _resource_changes(before: dict, after: dict, changes: list[dict]) -> None:
    bp, ap = _player(before), _player(after)
    for key, label in (("hp", "气血"), ("mp", "内力"), ("gold", "钱财")):
        if key not in bp and key not in ap:
            continue
        delta = _num_delta(bp.get(key), ap.get(key))
        if delta is None:
            continue
        changes.append(_change(key, label, bp.get(key), ap.get(key), "resource",
                               delta=delta))
    # Attributes are usually static, but a level-up or a curse can move them.
    battrs, aattrs = _dict(bp.get("attrs")), _dict(ap.get("attrs"))
    for key in sorted(set(battrs) | set(aattrs)):
        delta = _num_delta(battrs.get(key), aattrs.get(key))
        if delta is not None:
            changes.append(_change("attr:%s" % key, key, battrs.get(key),
                                   aattrs.get(key), "resource", delta=delta))


def _item_changes(before: dict, after: dict, changes: list[dict]) -> None:
    bitems = _dict(_player(before).get("items"))
    aitems = _dict(_player(after).get("items"))
    for key in sorted(set(bitems) | set(aitems)):
        bvalue = bitems.get(key, 0)
        avalue = aitems.get(key, 0)
        delta = _num_delta(bvalue, avalue)
        if delta is not None:
            changes.append(_change("item:%s" % key, _item_name(after, before, key=key),
                                   bvalue, avalue, "item", delta=delta))


def _weapon_changes(before: dict, after: dict, changes: list[dict]) -> None:
    bw = _dict(_player(before).get("weapon"))
    aw = _dict(_player(after).get("weapon"))
    if not bw and not aw:
        return
    bdur, adur = bw.get("durability"), aw.get("durability")
    if _num_delta(bdur, adur) is not None:
        changes.append(_change("weapon:durability", "%s 耐久" % _label(aw.get("name"), "武器"),
                               bdur, adur, "weapon", delta=_num_delta(bdur, adur)))
    bname, aname = _text(bw.get("name")), _text(aw.get("name"))
    if bname and aname and bname != aname:
        changes.append(_change("weapon:name", "武器", bname, aname, "weapon"))


def _clock_changes(before: dict, after: dict, changes: list[dict]) -> None:
    def rows(state):
        return _list(_dict(state.get("gameplay")).get("clocks"))

    bmap = {_text(row.get("name")): row for row in rows(before) if isinstance(row, dict)}
    amap = {_text(row.get("name")): row for row in rows(after) if isinstance(row, dict)}
    for name in sorted(set(bmap) | set(amap)):
        b, a = bmap.get(name, {}), amap.get(name, {})
        delta = _num_delta(b.get("filled"), a.get("filled"))
        if delta is None:
            continue
        max_b = b.get("segments")
        max_a = a.get("segments")
        before_text = "%s/%s" % (b.get("filled", 0), max_b if max_b is not None else "?")
        after_text = "%s/%s" % (a.get("filled", 0), max_a if max_a is not None else "?")
        changes.append(_change("clock:%s" % name, name, before_text, after_text,
                               "clock", delta=delta))


def _location_scene_changes(before: dict, after: dict, changes: list[dict]) -> None:
    bloc = _text(_player(before).get("location"))
    aloc = _text(_player(after).get("location"))
    if bloc != aloc:
        changes.append(_change("location", "所在", bloc or "未知", aloc or "未知", "location"))
    bscene = _dict(before.get("scene"))
    ascene = _dict(after.get("scene"))
    btitle, atitle = _text(bscene.get("title")), _text(ascene.get("title"))
    if atitle and btitle != atitle:
        changes.append(_change("scene", "场景", btitle or "开场", atitle, "scene"))


def _flag_changes(before: dict, after: dict, changes: list[dict]) -> None:
    bflags = {_text(x) for x in _list(before.get("world_flags")) if _text(x)}
    aflags = {_text(x) for x in _list(after.get("world_flags")) if _text(x)}
    added = sorted(aflags - bflags)
    removed = sorted(bflags - aflags)
    for flag in added:
        changes.append(_change("flag:%s" % flag, flag, "无", "已记下", "flag", tone="up"))
    for flag in removed:
        changes.append(_change("flag:%s" % flag, flag, "已记下", "无", "flag", tone="down"))


def _relation_changes(before: dict, after: dict, changes: list[dict]) -> None:
    brel = _dict(before.get("relations"))
    arel = _dict(after.get("relations"))
    for key in sorted(set(brel) | set(arel)):
        b, a = _dict(brel.get(key)), _dict(arel.get(key))
        for field, label in (("affinity", "好感"), ("respect", "敬重")):
            delta = _num_delta(b.get(field), a.get(field))
            if delta is not None:
                left, _, right = key.partition(":")
                if left == "player":
                    who = _entity_label(after, right)
                elif right == "player":
                    who = _entity_label(after, left)
                else:
                    who = "%s↔%s" % (_entity_label(after, left), _entity_label(after, right))
                changes.append(_change("relation:%s:%s" % (key, field),
                                       "%s %s" % (who, label), b.get(field),
                                       a.get(field), "relation", delta=delta))


def summarize(before: Any, after: Any) -> dict:
    """Return a bounded, player-facing diff between two state dicts."""
    b = _dict(before)
    a = _dict(after)
    changes: list[dict] = []
    if b:
        _resource_changes(b, a, changes)
        _item_changes(b, a, changes)
        _weapon_changes(b, a, changes)
        _clock_changes(b, a, changes)
        _location_scene_changes(b, a, changes)
        _flag_changes(b, a, changes)
        _relation_changes(b, a, changes)

    tick_before = _number(b.get("tick"))
    tick_after = _number(a.get("tick"))
    tick_delta = None
    if tick_before is not None and tick_after is not None and tick_before != tick_after:
        tick_delta = tick_after - tick_before
    if tick_delta is not None and not changes:
        changes.append(_change("tick", "时间", tick_before, tick_after, "resource",
                               delta=tick_delta))

    changes.sort(key=lambda row: (_KIND_ORDER.get(row.get("kind"), 99),
                                  -abs(row.get("delta") or 0)
                                  if isinstance(row.get("delta"), (int, float)) else 0,
                                  row.get("label") or ""))
    total = len(changes)
    return {
        "tick_from": tick_before,
        "tick_to": tick_after,
        "changes": changes[:MAX_CHANGES],
        "total": total,
        "truncated": max(0, total - MAX_CHANGES),
        "empty": not changes,
    }


def format_line(summary: Any) -> str:
    """One-line Chinese summary, used in logs and the MCP action record."""
    if not isinstance(summary, dict) or summary.get("empty"):
        return ""
    parts = []
    for row in summary.get("changes") or []:
        if not isinstance(row, dict):
            continue
        label = _text(row.get("label"))
        before, after = row.get("before"), row.get("after")
        if row.get("kind") == "clock":
            parts.append("%s %s→%s" % (label, before, after))
            continue
        delta = row.get("delta")
        if isinstance(delta, (int, float)):
            sign = "+" if delta > 0 else ""
            parts.append("%s %s%s" % (label, sign, delta))
        elif before != after:
            parts.append("%s %s→%s" % (label, before, after))
    return "；".join(parts[:8])
