"""设定包的领域目录：设施梯、模块梯、物品目录、潮汐规则、系统引导与能力选择。

这些内容过去只存在于 `settings/*.setting.json`，运行状态里没有对应字段：
面板只能看到手写 `game.sheet`，背包只能把 `vehicle_core` 这类 key 原样显示，
能力的“每人一次选择”也无法被 UI 或测试读到。本模块把它们规范化成
可落盘、可校验、可下发的结构。

原则：
  · 内容层负责写“有什么”；本模块只负责“结构合法、可重复载入、可展示”；
  · 没有对应字段的旧设定包返回空结构，不破坏任何现有世界；
  · 所有条目都有上限，避免一个设定包把状态撑爆。
"""

from __future__ import annotations

MAX_CATALOG = 32
MAX_LEVELS = 8
MAX_ITEMS = 512
MAX_TASKS = 40
MAX_OPTIONS = 16


def _text(value, limit=240, default=""):
    text = str(value or "").strip()
    return text[:limit] if text else default


def _level_list(raw):
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, (list, tuple)):
        return []
    out = []
    for value in raw:
        text = _text(value, 80)
        if text and text not in out:
            out.append(text)
        if len(out) >= MAX_LEVELS:
            break
    return out


def normalize_catalog(raw, kind="catalog"):
    """规范化设施/模块梯：每项 5 级（允许 1—8 级），key 唯一。"""
    if raw is None:
        return []
    if not isinstance(raw, (list, tuple)):
        raise ValueError("%s 必须是数组" % kind)
    out, seen = [], set()
    for index, row in enumerate(raw):
        if len(out) >= MAX_CATALOG:
            break
        if not isinstance(row, dict):
            raise ValueError("%s[%d] 必须是对象" % (kind, index))
        key = _text(row.get("key"), 32)
        if not key:
            raise ValueError("%s[%d] 缺 key" % (kind, index))
        if key in seen:
            raise ValueError("%s 的 key 重复: %s" % (kind, key))
        seen.add(key)
        name = _text(row.get("name"), 40, key)
        levels = _level_list(row.get("levels"))
        if not levels:
            raise ValueError("%s.%s 缺 levels" % (kind, key))
        entry = {
            "key": key,
            "name": name,
            "levels": levels,
            "effect": _text(row.get("effect"), 240, ""),
        }
        slot = _text(row.get("slot"), 40)
        if slot:
            entry["slot"] = slot
        out.append(entry)
    return out


def _task_rows(raw):
    if not isinstance(raw, (list, tuple)):
        return []
    out = []
    for index, row in enumerate(raw[:MAX_TASKS]):
        if not isinstance(row, dict):
            continue
        item_id = _text(row.get("id"), 32,
                        _text(row.get("module"), 32, "task%d" % (index + 1)))
        out.append({
            "id": item_id,
            "title": _text(row.get("title") or row.get("name") or row.get("module"), 80, item_id),
            "window": _text(row.get("window"), 60, ""),
            "risk": _text(row.get("risk"), 120, ""),
            "reward": _text(row.get("reward"), 120, ""),
            "cost": _text(row.get("cost"), 120, ""),
            "effect": _text(row.get("effect"), 240, ""),
            "note": _text(row.get("note"), 160, ""),
        })
    return out


def normalize_ability(raw):
    """规范化“每人一次初始能力选择”。

    允许 current 写 id 或 name；规范后同时保留 `current` 与 `current_id`，
    面板即可显示“已选哪个”，测试也能区分“没选”和“选了一个不存在的项”。
    """
    if not isinstance(raw, dict):
        return {}
    options = []
    seen = set()
    for index, row in enumerate(raw.get("options") or []):
        if len(options) >= MAX_OPTIONS:
            break
        if not isinstance(row, dict):
            continue
        option_id = _text(row.get("id"), 32, "ability%d" % (index + 1))
        if option_id in seen:
            continue
        seen.add(option_id)
        options.append({
            "id": option_id,
            "name": _text(row.get("name"), 40, option_id),
            "active": _text(row.get("active"), 240, ""),
            "passive": _text(row.get("passive"), 240, ""),
            "limit": _text(row.get("limit"), 240, ""),
        })
    current = _text(raw.get("current"), 40, "")
    current_id = ""
    if current:
        for option in options:
            if current in (option["id"], option["name"]):
                current_id = option["id"]
                break
    return {
        "scope": _text(raw.get("scope"), 240, ""),
        "current": current,
        "current_id": current_id,
        "slots": _text(raw.get("slots"), 40, ""),
        "reselect": _text(raw.get("reselect"), 240, ""),
        "options": options,
    }


def normalize_guidance(raw):
    """规范化系统引导：主线、每日任务、活动、能力预告、能力选择。"""
    if not isinstance(raw, dict):
        return {}
    result = {
        "mode": _text(raw.get("mode"), 80, ""),
        "main": _text(raw.get("main"), 400, ""),
        "recommendation": _text(raw.get("recommendation"), 400, ""),
        "daily_tasks": _task_rows(raw.get("daily_tasks")),
        "activities": _task_rows(raw.get("activities")),
        "ability_choices": _task_rows(raw.get("ability_choices")),
    }
    abilities = normalize_ability(raw.get("ability_selection"))
    if abilities:
        result["ability_selection"] = abilities
    return result


def normalize_tide(raw):
    """潮汐规则是内容层的解释文本；保留为稳定字段，供面板/提示词引用。"""
    if not isinstance(raw, dict):
        return {}
    out = {}
    for key, value in list(raw.items())[:20]:
        text = _text(value, 500)
        if text:
            out[_text(key, 40)] = text
    return out


def normalize_items(raw):
    """物品目录：接受 {key: {...}} 或 [{key, name, ...}]。"""
    if raw is None:
        return {}
    if isinstance(raw, dict):
        rows = []
        for key, value in raw.items():
            row = dict(value) if isinstance(value, dict) else {"name": value}
            row.setdefault("key", key)
            rows.append(row)
    elif isinstance(raw, (list, tuple)):
        rows = list(raw)
    else:
        raise ValueError("items 必须是对象或数组")
    out = {}
    for row in rows[:MAX_ITEMS]:
        if not isinstance(row, dict):
            continue
        key = _text(row.get("key"), 64)
        if not key:
            continue
        out[key] = {
            "key": key,
            "name": _text(row.get("name"), 80, key),
            "type": _text(row.get("type"), 40, ""),
            "desc": _text(row.get("desc"), 240, ""),
        }
    return out


def merge_market(items, market):
    """用市场行情的 name/type 补物品目录，避免新物品在背包里显示英文 key。"""
    out = dict(items or {})
    for location in market or []:
        if not isinstance(location, dict):
            continue
        for row in location.get("items") or []:
            if not isinstance(row, dict):
                continue
            key = _text(row.get("key"), 64)
            if not key or key in out:
                continue
            out[key] = {
                "key": key,
                "name": _text(row.get("name"), 80, key),
                "type": _text(row.get("type"), 40, ""),
                "desc": _text(row.get("desc"), 240, ""),
            }
    return out
