"""载具阶位包（vessel ladder）——把“85 级载具”变成可运行的世界结构。

这一层解决的不是“显示一个 Lv 数字”，而是三件容易漂移的事：

  1. **品阶与细分阶是同一张表**：17 个大品阶 × 5 个细分阶 = 85 级；
     每一级都有长度、甲板格、仓库格、载重、艇体上限和速度。
  2. **当前阶位来自权威状态**：`game.meters` 里 key=base 的进度轨是唯一信源。
     面板、状态、存档都从这里派生，不再各自维护一个 `sheet["升级"]` 字符串。
  3. **跨品阶有门槛**：gate 是内容层写的条件；本模块只负责原样保留和展示，
     不把“有蓝图”自动当成“能升级”。

设定包形状（`settings/白鹿岛.setting.json`）::

    "vessel_ladder": {
      "grade_modifiers": {"I": 1.0, ...},
      "classes": [
        {"class": "普通充气救生筏", "grades": ["I", "II", "III", "IV", "V"],
         "length_m": [2.4, 2.8], "deck_slots": [0, 0],
         "storage_slots": [2, 3], "cargo_kg": [30, 40],
         "hull_max": [100, 110], "speed": "1-2km/h", "gate": "初始"}
      ]
    }

所有函数都是纯函数；`project()` 只在显式调用时写 state。
"""

from __future__ import annotations

MAX_CLASSES = 24
MAX_GRADES = 8
MAX_TIER = 200
DEFAULT_GRADES = ("I", "II", "III", "IV", "V")


def _num(value, default=0.0):
    try:
        if isinstance(value, bool):
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _text(value, limit=200, default=""):
    text = str(value or "").strip()
    return text[:limit] if text else default


def _pair(raw, key, default, lo=0.0, hi=999999.0):
    """读一个 [min, max] 数值对；顺序反了自动交换，越界夹紧。"""
    value = raw.get(key) if isinstance(raw, dict) else None
    if not isinstance(value, (list, tuple)) or len(value) < 2:
        value = default
    a = max(lo, min(hi, _num(value[0], default[0])))
    b = max(lo, min(hi, _num(value[1], default[1])))
    if a > b:
        a, b = b, a
    return [a, b]


def _pair_at(pair, fraction):
    if not pair:
        return 0
    fraction = max(0.0, min(1.0, float(fraction)))
    return pair[0] + (pair[1] - pair[0]) * fraction


def normalize(raw):
    """规范化整张载具梯；坏条目报 ValueError，空/缺省返回 {}。"""
    if not isinstance(raw, dict):
        return {}
    classes = []
    seen = set()
    for index, row in enumerate(raw.get("classes") or []):
        if len(classes) >= MAX_CLASSES:
            break
        if not isinstance(row, dict):
            raise ValueError("vessel_ladder.classes[%d] 必须是对象" % index)
        name = _text(row.get("class") or row.get("name"), 40)
        if not name:
            raise ValueError("vessel_ladder.classes[%d] 缺 class 名称" % index)
        if name in seen:
            raise ValueError("vessel_ladder 的 class 重复: %s" % name)
        seen.add(name)
        grades = row.get("grades") or list(DEFAULT_GRADES)
        if not isinstance(grades, (list, tuple)):
            raise ValueError("vessel_ladder.%s.grades 必须是数组" % name)
        grades = [_text(g, 16) for g in grades if _text(g, 16)]
        if not grades or len(grades) > MAX_GRADES:
            raise ValueError("vessel_ladder.%s.grades 数量必须是 1-%d" % (name, MAX_GRADES))
        if len(set(grades)) != len(grades):
            raise ValueError("vessel_ladder.%s.grades 有重复" % name)
        entry = {
            "class": name,
            "grades": grades,
            "length_m": _pair(row, "length_m", (2.4, 2.8), 0.5, 5000.0),
            "deck_slots": [int(round(v)) for v in _pair(row, "deck_slots", (0, 0), 0, 64)],
            "storage_slots": [int(round(v)) for v in _pair(row, "storage_slots", (0, 0), 0, 256)],
            "cargo_kg": [int(round(v)) for v in _pair(row, "cargo_kg", (0, 0), 0, 10 ** 7)],
            "hull_max": [int(round(v)) for v in _pair(row, "hull_max", (0, 0), 0, 10 ** 7)],
            "speed": _text(row.get("speed"), 60, "未标"),
            "gate": _text(row.get("gate"), 240, "未写门槛"),
        }
        classes.append(entry)
    if not classes:
        return {}
    tier_max = sum(len(row["grades"]) for row in classes)
    if tier_max > MAX_TIER:
        raise ValueError("vessel_ladder 总级数超过 %d" % MAX_TIER)

    modifiers = {}
    raw_mods = raw.get("grade_modifiers")
    if isinstance(raw_mods, dict):
        for key, val in list(raw_mods.items())[:MAX_GRADES]:
            try:
                modifiers[_text(key, 16)] = round(float(val), 3)
            except (TypeError, ValueError):
                continue
    return {
        "version": 1,
        "note": _text(raw.get("note"), 400, ""),
        "grade_modifiers": modifiers,
        "classes": classes,
        "tier_max": tier_max,
    }


def _tier_from_state(state):
    """当前载具阶位：`game.meters` key=base 优先，其次 `vessel.tier`，最后 1。"""
    tier = 0
    game = state.get("game") if isinstance(state, dict) else None
    if isinstance(game, dict):
        for row in game.get("meters") or []:
            if isinstance(row, dict) and str(row.get("key") or "") == "base":
                try:
                    tier = int(float(row.get("value", 1)))
                except (TypeError, ValueError):
                    tier = 0
                break
    if not tier:
        current = state.get("vessel") if isinstance(state, dict) else None
        if isinstance(current, dict):
            try:
                tier = int(current.get("tier", 1))
            except (TypeError, ValueError):
                tier = 0
    return max(1, tier or 1)


def status(state):
    """从载具梯与权威进度轨派生当前载具状态；没有阶梯返回 {}。"""
    ladder = state.get("vessel_ladder") if isinstance(state, dict) else None
    if not isinstance(ladder, dict) or not ladder.get("classes"):
        return {}
    classes = ladder["classes"]
    tier = min(int(ladder.get("tier_max", 1) or 1), _tier_from_state(state))

    offset = tier - 1
    class_index = 0
    for i, row in enumerate(classes):
        n = len(row.get("grades") or [])
        if offset < n:
            class_index = i
            grade_index = offset
            break
        offset -= n
    else:
        class_index = len(classes) - 1
        grade_index = len(classes[class_index].get("grades") or []) - 1

    row = classes[class_index]
    grades = row.get("grades") or ["I"]
    grade_index = max(0, min(len(grades) - 1, grade_index))
    frac = grade_index / float(len(grades) - 1) if len(grades) > 1 else 0.0
    next_row = classes[class_index + 1] if class_index + 1 < len(classes) else None
    return {
        "tier": tier,
        "tier_max": int(ladder.get("tier_max", tier) or tier),
        "class": row["class"],
        "grade": grades[grade_index],
        "class_index": class_index + 1,
        "class_count": len(classes),
        "grade_index": grade_index + 1,
        "grade_count": len(grades),
        "length_m": round(_pair_at(row.get("length_m"), frac), 2),
        "deck_slots": int(round(_pair_at(row.get("deck_slots"), frac))),
        "storage_slots": int(round(_pair_at(row.get("storage_slots"), frac))),
        "cargo_kg": int(round(_pair_at(row.get("cargo_kg"), frac))),
        "hull_max": int(round(_pair_at(row.get("hull_max"), frac))),
        "speed": row.get("speed", ""),
        "gate": row.get("gate", ""),
        "next_class": next_row.get("class") if next_row else None,
        "next_grade": (next_row.get("grades") or ["I"])[0] if next_row else None,
        "next_gate": next_row.get("gate") if next_row else None,
    }


def project(state, force_sheet=False):
    """把载具梯投影到 state：补 base 进度轨、刷新 `state["vessel"]`。

    不覆盖玩家自己写的 `game.sheet`，除非 `force_sheet=True`（建局/显式同步时）。
    这样旧存档里“R-1”这类玩家可见的编号不会被自动改写成无意义的阶位名。
    """
    if not isinstance(state, dict):
        return {}
    current = status(state)
    if not current:
        return {}
    ladder = state.get("vessel_ladder") or {}
    game = state.get("game")
    if isinstance(game, dict):
        meters = game.setdefault("meters", [])
        base = next((m for m in meters if isinstance(m, dict) and m.get("key") == "base"), None)
        if base is None:
            meters.append({"key": "base", "label": "载具阶位", "value": current["tier"],
                           "min": 1, "max": current["tier_max"]})
        else:
            base["max"] = max(int(base.get("max", 0) or 0), current["tier_max"])
            base["min"] = min(int(base.get("min", 1) or 1), 1)
            base["value"] = max(1, min(int(base["max"]), current["tier"]))
        if force_sheet:
            sheet = game.setdefault("sheet", {})
            if isinstance(sheet, dict):
                sheet["载具"] = "%s %s" % (current["class"], current["grade"])
                sheet["升级"] = "Lv%d/%d → %s" % (
                    current["tier"], current["tier_max"],
                    ("%s %s" % (current["next_class"], current["next_grade"]))
                    if current.get("next_class") else "已到顶")
                sheet["甲板"] = "%d格" % current["deck_slots"]
                sheet["舱内"] = "%d格" % current["storage_slots"]
                sheet["载重"] = "%dkg" % current["cargo_kg"]
                sheet["艇体品阶"] = "→".join(row["class"] for row in ladder.get("classes", []))
    state["vessel"] = current
    return current
