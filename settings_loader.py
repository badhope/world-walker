"""
设定包装载 (settings_loader) —— 纯标准库

为什么单独成模块：把"一个 JSON 设定包 → 一份可运行的游戏状态"这件事从 MCP 层里拿出来。

- MCP 的 `load_setting` / `world_init` 需要 pydantic 做入参 schema，因此必须有 mcp 依赖；
- 但**校验设定包**、**验证四套世界观**不需要 MCP，也不该因为没有 mcp 就跳过。

把这条路径抽出来后：
  · `mcp_server.world_init` 与 `settings_loader.build_state` 共用同一套规范化逻辑，
    不会出现"MCP 建局"与"测试建局"两套字段处理而悄悄漂移；
  · `scripts/verify_settings.py` 可以在零依赖环境（CI 的 core 作业）里跑。

所有函数都是纯函数（除非显式接收 state 并原地更新），不读写文件、不依赖时间。
"""

from game_engine.state_schema import entity_key, log_event

ATTR_KEYS = ("str", "dex", "int", "con", "cha")
DEFAULT_SEED = 20261014
PLACE_DESC_CAP = 1200


def normalize_entity(entity_id: str, raw: dict) -> dict:
    """把设定包里的一个角色规范成引擎实体。

    规则与 MCP 的 EntityIn 保持一致：五维缺省 10 且必须是数字，hp 缺省等于 hp_max，
    items 只保留正数，描述类文字截断到 1200 字（防止一个设定包把状态撑爆）。
    """
    if not isinstance(raw, dict) or not raw.get("name"):
        raise ValueError("实体 %s 缺少 name" % entity_id)
    attrs = dict(raw.get("attrs") or {})
    for key in ATTR_KEYS:
        val = attrs.get(key, 10)
        if not isinstance(val, (int, float)):
            raise ValueError("实体 %s 的属性 %s 必须是数字" % (entity_id, key))
        attrs[key] = int(val)

    hp_max = int(raw.get("hp_max", 100))
    mp_max = int(raw.get("mp_max", 0))
    ent = {
        "name": str(raw["name"]),
        "faction": str(raw.get("faction", "")),
        "attrs": attrs,
        "hp": int(raw.get("hp", hp_max)),
        "hp_max": hp_max,
        "mp": int(raw.get("mp", mp_max)),
        "mp_max": mp_max,
        "level": str(raw.get("level", "凡人")),
        "gold": int(raw.get("gold", 0)),
        "location": str(raw.get("location", "")),
    }
    for extra in ("desc", "personality", "speech"):
        if raw.get(extra):
            ent[extra] = str(raw[extra])[:PLACE_DESC_CAP]
    if raw.get("skills"):
        ent["skills"] = list(raw["skills"])
    if raw.get("morality"):
        ent["morality"] = list(raw["morality"])[:6]
    if raw.get("roam"):
        ent["roam"] = True

    items = raw.get("items")
    if items:
        cleaned = {}
        for key, val in dict(items).items():
            try:
                n = int(val)
            except (TypeError, ValueError):
                continue
            if n > 0:
                cleaned[str(key)] = n
        if cleaned:
            ent["items"] = cleaned
    return ent


def normalize_market(market: list) -> dict:
    """[{location, items:[{key,...}]}] → {location: {key: item}}。"""
    out = {}
    for loc in market or []:
        if not isinstance(loc, dict) or not loc.get("location"):
            raise ValueError("market 每项都必须有 location")
        items = {}
        for item in loc.get("items") or []:
            if not isinstance(item, dict) or not item.get("key"):
                raise ValueError("market.items 每项都必须有 key")
            key = str(item["key"])
            price = int(item.get("price", 50))
            items[key] = {
                "name": str(item.get("name", key)),
                "price": price,
                "supply": int(item.get("supply", 20)),
                "base_price": int(item.get("base_price", price)),
                "type": str(item.get("type", "")),
                "desc": str(item.get("desc", "")),
            }
        out[str(loc["location"])] = items
    return out


def normalize_relations(relations: list, entity_ids) -> dict:
    """[{a,b,affinity,respect}] → {'a:b': {...}}；引用了不存在的实体直接报错。"""
    out = {}
    for rel in relations or []:
        if not isinstance(rel, dict):
            raise ValueError("relations 每项必须是对象")
        a, b = str(rel.get("a", "")), str(rel.get("b", ""))
        for eid in (a, b):
            if eid not in entity_ids:
                raise ValueError("关系引用了不存在的实体: %s" % eid)
        out[entity_key(a, b)] = {"affinity": int(rel.get("affinity", 0)),
                                 "respect": int(rel.get("respect", 0))}
    return out


def build_state(bundle: dict, seed: int | None = None) -> dict:
    """设定包 → 初始状态（不落盘、不写文件）。

    `bundle` 形状见 settings/README.md：world / player / entities / market /
    relations / world_flags / ui / seed。所有校验错误都是 ValueError，带人能读懂的原因。
    """
    if not isinstance(bundle, dict):
        raise ValueError("设定包必须是 JSON 对象")
    world = bundle.get("world")
    player = bundle.get("player")
    if not isinstance(world, dict) or not world.get("name"):
        raise ValueError("设定包缺 world.name")
    if not isinstance(player, dict) or not player.get("name"):
        raise ValueError("设定包缺 player.name")

    entities = {"player": normalize_entity("player", player)}
    for npc in bundle.get("entities") or []:
        if not isinstance(npc, dict):
            raise ValueError("entities 每项必须是对象")
        eid = str(npc.get("id") or "").strip()
        if not eid:
            raise ValueError("entities 里每个 NPC 都必须有 id")
        if eid == "player":
            raise ValueError("entities 里不要重复定义 player")
        if eid in entities:
            raise ValueError("实体 id 重复: %s" % eid)
        entities[eid] = normalize_entity(eid, npc)

    state = {
        "tick": 0,
        "rng_seed": int(seed if seed is not None else bundle.get("seed", DEFAULT_SEED)),
        "entities": entities,
        "relations": normalize_relations(bundle.get("relations") or [], set(entities)),
        "market": normalize_market(bundle.get("market") or []),
        "karma_ledger": [],
        "world_flags": [str(f) for f in (bundle.get("world_flags") or [])],
        "ui": dict(bundle.get("ui") or {}),
        "event_log": [],
        "world_info": {
            "name": str(world["name"]),
            "era": str(world.get("era", "")),
            "location_desc": str(world.get("location_desc", "")),
        },
    }
    return state


def search_place(bundle: dict, name: str) -> dict:
    """取设定包里某地点的描写（兼容 {name:{desc}} 与 {name:"文字"} 两种写法）。"""
    places = bundle.get("places") or {}
    info = places.get(name)
    if isinstance(info, dict):
        return {"desc": str(info.get("desc", ""))[:PLACE_DESC_CAP], "tick": 0}
    if isinstance(info, str):
        return {"desc": info[:PLACE_DESC_CAP], "tick": 0}
    return {}


def apply_runtime_fields(state: dict, bundle: dict) -> int:
    """把"建局之外的运行时字段"写进状态，返回导入的世界书条目数。

    字段：currency / terms / level_tiers / places / lore。
    这里**不**做落盘——调用方（MCP 的 load_setting）负责 save_state。
    """
    if bundle.get("currency"):
        state["currency"] = str(bundle["currency"])
    terms = bundle.get("terms")
    if isinstance(terms, dict) and terms:
        state.setdefault("ui", {})["terms"] = {str(k): str(v) for k, v in terms.items()}
    tiers = bundle.get("level_tiers")
    if isinstance(tiers, list) and tiers:
        state.setdefault("config", {})["level_tiers"] = [str(t) for t in tiers]
    places = bundle.get("places")
    if isinstance(places, dict):
        bucket = state.setdefault("places", {})
        for name in places:
            info = search_place(bundle, str(name))
            if info:
                info["tick"] = int(state.get("tick", 0) or 0)
                bucket[str(name)] = info

    lore_n = 0
    for entry in bundle.get("lore") or []:
        norm = normalize_lore_entry(entry)
        if norm:
            state.setdefault("lore", []).append(norm)
            lore_n += 1
    if lore_n:
        log_event(state, "system", "设定包「%s」载入：世界书 %d 条"
                  % (bundle.get("name", ""), lore_n))
    return lore_n


def normalize_lore_entry(entry: dict):
    """规范化世界书条目；同时吃角色卡 character_book 与 SillyTavern world-info 两套字段名。"""
    if not isinstance(entry, dict):
        return None
    keys = entry.get("keys", entry.get("key")) or []
    if isinstance(keys, str):
        keys = [keys]
    secondary = entry.get("secondary_keys", entry.get("keysecondary")) or []
    if isinstance(secondary, str):
        secondary = [secondary]
    content = str(entry.get("content") or "").strip()
    keys = [str(k).strip() for k in keys if str(k).strip()]
    if not keys or not content:
        return None
    if "enabled" in entry:
        enabled = bool(entry["enabled"])
    else:
        enabled = not bool(entry.get("disable", False))
    return {
        "keys": keys,
        "secondary_keys": [str(k).strip() for k in secondary if str(k).strip()],
        "content": content,
        "comment": str(entry.get("comment") or entry.get("name") or ""),
        "selective": bool(entry.get("selective", False)),
        "constant": bool(entry.get("constant", False)),
        "case_sensitive": bool(entry.get("case_sensitive", False)),
        "order": int(entry.get("insertion_order", entry.get("order", 100)) or 0),
        "enabled": enabled,
    }

