"""Per-world play modes: 爽文 / 适中 / 硬核.

The three modes are engine-level presets, not hand-written variants of every
setting. A setting may add a small ``modes`` block to name its own edge; the
numeric pressure stays here so all worlds remain comparable.

Design rule: 爽文 is a *mild* edge, never an infinite engine. It buys room to
recover from one bad decision; it does not remove hunger, weather, or death.
"""

from __future__ import annotations

import copy

MODE_IDS = ("power", "balanced", "hardcore")

MODE_SPECS = {
    "power": {
        "id": "power",
        "label": "爽文",
        "short": "工具齐全，力气够用",
        "description": "前两类主耗材 +50%，口粮钱 +50%，物价 -15%，库存 +2，压力钟 -1；失败通常留一口气。爽文给的是可清点的工具和搬货练出的身板：会用坏、会累、会被抢。",
        "world_intensity": "低",
        "play_style": "爽文推进",
        "system_strength": "无系统；可清点的工具与体力（会累/会坏/被抢）",
        "death_rule": "重伤留一口气，不直接抹掉角色",
        "resource_curve": "宽裕",
        "encounter_pressure": "低",
        "difficulty": "轻松",
        "hp_mult": 1.5,
        "mp_mult": 1.5,
        "gold_mult": 1.5,
        "clock_delta": -1,
        "price_mult": 0.85,
        "supply_delta": 2,
        "edge": "起始前两类主耗材 +50%，口粮钱 +50%，物价 -15%、库存 +2；所有加成都是可清点的物资和体力。",
        "narrative_rule": "给玩家留退路：失败先给代价和转机，不连续下死手；爽文加成只能落在可清点的物资、价格、库存、耐久和体力上，不提供任何超自然能力。",
    },
    "balanced": {
        "id": "balanced",
        "label": "适中",
        "short": "规则不偏向谁",
        "description": "资源、威胁和成长按设定走；有金手指的世界只给世界内信息或一次性小优势，不替玩家做决定。",
        "world_intensity": "中",
        "play_style": "均衡推进",
        "system_strength": "无系统，仅世界内信息",
        "death_rule": "按世界规则；重伤会留下长期后果",
        "resource_curve": "标准",
        "encounter_pressure": "中",
        "difficulty": "标准",
        "hp_mult": 1.0,
        "mp_mult": 1.0,
        "gold_mult": 1.0,
        "clock_delta": 0,
        "price_mult": 1.0,
        "supply_delta": 0,
        "edge": "没有额外金手指；能用的只有手里的东西、认识的人和愿意付出的代价。",
        "narrative_rule": "不送、不坑：每个收益都要有来处，每个代价都要能追溯。",
    },
    "hardcore": {
        "id": "hardcore",
        "label": "硬核",
        "short": "世界不欠你任何东西",
        "description": "起始资源更紧，压力钟更快，伤病、天气和敌人都不留情；死亡不可复活，错误会累积。",
        "world_intensity": "高",
        "play_style": "硬核推进",
        "system_strength": "无系统，无金手指",
        "death_rule": "死亡不可复活；伤势会发炎，错误会复利",
        "resource_curve": "紧缺",
        "encounter_pressure": "高",
        "difficulty": "硬核",
        "hp_mult": 0.75,
        "mp_mult": 0.75,
        "gold_mult": 0.5,
        "clock_delta": 1,
        "price_mult": 1.20,
        "supply_delta": -1,
        "edge": "无金手指。你只有一间漏风小屋和一具会累会冷会发炎的身体。",
        "narrative_rule": "不给免费提示、不暗中放水；每个选择都要付代价，死亡就是结局。",
    },
}

MODE_BY_LABEL = {spec["label"]: key for key, spec in MODE_SPECS.items()}
MODE_BY_DIFFICULTY = {"轻松": "power", "标准": "balanced", "硬核": "hardcore", "铁人": "hardcore"}


def normalize(value=None) -> str:
    """Accept id, Chinese label, or legacy difficulty; always return a valid id."""
    text = str(value or "").strip()
    if text in MODE_SPECS:
        return text
    if text in MODE_BY_LABEL:
        return MODE_BY_LABEL[text]
    if text in MODE_BY_DIFFICULTY:
        return MODE_BY_DIFFICULTY[text]
    return "balanced"


def catalog() -> list[dict]:
    """Frontend-facing catalog. No hidden tuning numbers."""
    rows = []
    for key in MODE_IDS:
        spec = MODE_SPECS[key]
        rows.append({
            "id": key,
            "label": spec["label"],
            "short": spec["short"],
            "description": spec["description"],
            "world_intensity": spec["world_intensity"],
            "play_style": spec["play_style"],
            "system_strength": spec["system_strength"],
            "death_rule": spec["death_rule"],
            "resource_curve": spec["resource_curve"],
            "encounter_pressure": spec["encounter_pressure"],
            "difficulty": spec["difficulty"],
        })
    return rows


def _world_overrides(bundle: dict, mode: str) -> dict:
    raw = (bundle or {}).get("modes")
    if not isinstance(raw, dict):
        return {}
    item = raw.get(mode)
    if not isinstance(item, dict):
        return {}
    allowed = {"edge", "description", "narrative_rule", "world_intensity",
               "system_strength", "death_rule", "start_items", "start_gold",
               "start_weapon", "attr_bonus", "label", "short"}
    return {k: copy.deepcopy(item[k]) for k in allowed if k in item}


def summary(mode=None, bundle=None) -> dict:
    key = normalize(mode)
    spec = dict(MODE_SPECS[key])
    override = _world_overrides(bundle or {}, key)
    spec.update(override)
    spec["id"] = key
    spec["label"] = spec.get("label") or MODE_SPECS[key]["label"]
    return spec


def apply(state: dict, bundle: dict | None = None, mode=None) -> dict:
    """Apply a mode to a freshly built state once.

    Guarded by ``state['mode']`` so ``apply_runtime_fields`` or a re-load never
    multiplies the bonuses a second time.
    """
    if not isinstance(state, dict):
        return summary(mode, bundle)
    if isinstance(state.get("mode"), dict) and state["mode"].get("id"):
        return state["mode"]

    key = normalize(mode)
    spec = summary(key, bundle)
    player = (state.get("entities") or {}).get("player")
    if isinstance(player, dict):
        base_hp = max(1, int(player.get("hp_max", 1) or 1))
        base_mp = max(0, int(player.get("mp_max", 0) or 0))
        player["hp_max"] = max(1, int(round(base_hp * spec.get("hp_mult", 1.0))))
        player["hp"] = min(int(player.get("hp", base_hp) or 0), player["hp_max"])
        if base_mp:
            player["mp_max"] = max(0, int(round(base_mp * spec.get("mp_mult", 1.0))))
            player["mp"] = min(int(player.get("mp", base_mp) or 0), player["mp_max"])
        player["gold"] = max(0, int(round(int(player.get("gold", 0) or 0) * spec.get("gold_mult", 1.0))))
        items = player.get("items")
        if isinstance(items, dict):
            if key == "power":
                # Extend what the player already has; never invent an item key
                # the world does not know how to price or describe.
                for item_key in list(items)[:2]:
                    try:
                        items[item_key] = int(items[item_key]) + max(1, int(items[item_key]) // 2)
                    except (TypeError, ValueError):
                        pass
            elif key == "hardcore":
                # 只削耗材，不把刀、手记这类工具一起抹掉：
                # 硬核的压迫感来自“水/火/药不够”，而不是让玩家开局一无所有。
                consumables = [k for k in items if k in (
                    "water", "biscuit", "bread", "food", "ration", "matches",
                    "candle", "bandage", "medicine", "salt")]
                for item_key in consumables[:2]:
                    try:
                        items[item_key] = max(0, int(items[item_key]) - 1)
                    except (TypeError, ValueError):
                        pass
                player["items"] = {k: v for k, v in items.items() if v > 0}
        extra = spec.get("start_items") if isinstance(spec.get("start_items"), dict) else {}
        if extra:
            bucket = player.setdefault("items", {})
            for item_key, qty in extra.items():
                try:
                    bucket[str(item_key)] = int(bucket.get(str(item_key), 0)) + max(0, int(qty))
                except (TypeError, ValueError):
                    continue
        if spec.get("start_gold"):
            try:
                player["gold"] = int(player.get("gold", 0)) + int(spec["start_gold"])
            except (TypeError, ValueError):
                pass
        attrs = player.get("attrs")
        bonus = spec.get("attr_bonus")
        if isinstance(attrs, dict) and isinstance(bonus, dict):
            for attr, delta in bonus.items():
                try:
                    attrs[str(attr)] = int(attrs.get(str(attr), 10) or 10) + int(delta)
                except (TypeError, ValueError):
                    continue
        weapon = spec.get("start_weapon")
        if isinstance(weapon, dict) and weapon.get("name"):
            player["weapon"] = copy.deepcopy(weapon)

    # Initial clock pressure: 爽文 starts one tick calmer, 硬核 one tick hotter.
    gameplay = state.get("gameplay")
    if isinstance(gameplay, dict):
        for clock in gameplay.get("clocks") or []:
            if not isinstance(clock, dict):
                continue
            try:
                segments = max(1, int(clock.get("segments", 6) or 6))
                filled = int(clock.get("filled", 0) or 0)
            except (TypeError, ValueError):
                continue
            filled += int(spec.get("clock_delta", 0) or 0)
            clock["filled"] = max(0, min(segments, filled))

    # Market temperature: a kinder world has more stock and softer prices.
    for items in (state.get("market") or {}).values():
        if not isinstance(items, dict):
            continue
        for item in items.values():
            if not isinstance(item, dict):
                continue
            try:
                price = max(1, int(item.get("price", 1) or 1))
                base = max(1, int(item.get("base_price", price) or price))
                mult = float(spec.get("price_mult", 1.0) or 1.0)
                item["price"] = max(1, int(round(price * mult)))
                item["base_price"] = max(1, int(round(base * mult)))
                item["supply"] = max(0, int(item.get("supply", 0) or 0)
                                     + int(spec.get("supply_delta", 0) or 0))
            except (TypeError, ValueError):
                continue

    flags = [str(f) for f in (state.get("world_flags") or [])
             if not str(f).startswith("mode:")
             and str(f) not in ("hardcore", "no_cheat", "no_respawn", "mild_cheat")]
    flags.append("mode:" + key)
    if key == "hardcore":
        flags.extend(["hardcore", "no_respawn", "no_cheat"])
    elif key == "power":
        flags.append("mild_cheat")
    state["world_flags"] = flags
    state["mode"] = {
        k: copy.deepcopy(spec.get(k)) for k in (
            "id", "label", "short", "description", "world_intensity",
            "play_style", "system_strength", "death_rule", "resource_curve",
            "encounter_pressure", "difficulty", "edge", "narrative_rule",
            "attr_bonus", "start_weapon"
        ) if k in spec
    }
    return state["mode"]
