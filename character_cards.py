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
