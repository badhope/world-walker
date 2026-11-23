"""Character-card projection shared by MCP, the panel and exports.

SillyTavern's V2 card is the interchange format most players already have.
The engine stores live NPC state in its own entity shape, so exporting means
projecting that shape into a card *without* losing activity fields: those go
into `extensions.world_walker` where other tools will not mistake them for
prompt text.
"""

from __future__ import annotations

from typing import Any


def _text(value: Any) -> str:
    return str(value if value is not None else "").strip()


def entity_card(ent: dict) -> dict:
    """Project an engine entity into a portable chara_card_v2 document."""
    data = ent if isinstance(ent, dict) else {}
    name = _text(data.get("name"))
    card = {
        "spec": "chara_card_v2",
        "spec_version": "2.0",
        "data": {
            "name": name,
            "description": _text(data.get("desc")),
            "personality": _text(data.get("personality")),
            "scenario": "",
            "first_mes": "",
            "mes_example": _text(data.get("speech")),
            "creator_notes": "World Walker 现场生成的角色卡",
            "system_prompt": "",
            "post_history_instructions": "",
            "alternate_greetings": [],
            "tags": ["world-walker", "auto-generated"],
            "creator": "world-walker",
            "character_version": "1",
            "extensions": {"world_walker": {
                "activity": _text(data.get("activity")),
                "intent": _text(data.get("intent")),
                "mood": _text(data.get("mood")),
                "routine": _text(data.get("routine")),
                "status": _text(data.get("status")),
                "agenda": _text(data.get("agenda")),
                "aliases": list(data.get("aliases") or []) if isinstance(data.get("aliases"), list) else [],
                "location": _text(data.get("location")),
                "last_seen_tick": data.get("last_seen_tick"),
            }},
        },
    }
    return card


def _card_data(card: Any) -> dict:
    """Accept a V2 envelope or the inner data object."""
    if not isinstance(card, dict):
        raise ValueError("角色卡必须是 JSON 对象")
    data = card.get("data") if isinstance(card.get("data"), dict) else card
    if not isinstance(data, dict) or not _text(data.get("name")):
        raise ValueError("角色卡缺少 data.name")
    return data


def add_to_state(state: dict, card: Any, entity_id: str, *, attrs: dict | None = None,
                 hp: int = 100, gold: int = 0, location: str = "", level: str = "凡人") -> dict:
    """Add a card as an NPC to an in-memory state; caller owns the transaction.

    This is the dependency-free half of `mcp_server.add_character`: the panel
    can import a JSON card without installing the optional MCP SDK.
    """
    from game_engine import settings_loader
    from game_engine.state_schema import bump, log_event

    data = _card_data(card)
    entity_id = _text(entity_id)
    if not entity_id:
        raise ValueError("entity_id 不能为空")
    entities = state.setdefault("entities", {})
    if entity_id in entities:
        raise ValueError("实体已存在: %s（换个 entity_id 或先 remove）" % entity_id)
    ent = settings_loader.normalize_entity(entity_id, {
        "name": _text(data.get("name")),
        "attrs": attrs or {},
        "hp": hp, "hp_max": hp,
        "gold": gold,
        "location": location or (entities.get("player") or {}).get("location", ""),
        "level": level,
        "desc": _text(data.get("description")),
        "personality": _text(data.get("personality")),
        "speech": _text(data.get("mes_example")),
        "card_json": {"spec": "chara_card_v2", "spec_version": "2.0", "data": data},
    })
    entities[entity_id] = ent
    book = (data.get("character_book") or {}).get("entries") or []
    if isinstance(book, dict):
        book = list(book.values())
    added = 0
    for row in book:
        normalized = settings_loader.normalize_lore_entry(row)
        if normalized:
            state.setdefault("lore", []).append(normalized)
            added += 1
    codex = state.setdefault("codex", {})
    people = codex.setdefault("people", [])
    if ent["name"] not in people:
        people.append(ent["name"])
        if len(people) > 200:
            del people[0]
        bump(state, "people")
    log_event(state, "system", "角色卡「%s」入局（%s），世界书 +%d 条" % (
        ent["name"], entity_id, added))
    return {"entity_id": entity_id, "name": ent["name"], "lore_added": added,
            "entities": len(entities)}
