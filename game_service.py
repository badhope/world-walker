"""Player-facing facade over the MCP primitives.

The MCP server keeps its fine-grained tools for hosts and tests.  The player
runtime, the HTTP API and the new shell talk to this facade instead: one method
per player concept, explicit action strings, no accidental god-objects.
"""

from __future__ import annotations

import inspect
import json
import os

from game_engine import model_config


def _jsonable(value):
    try:
        json.dumps(value, ensure_ascii=False, allow_nan=False)
        return value
    except (TypeError, ValueError):
        return json.loads(json.dumps(value, ensure_ascii=False, default=str))


class GameService:
    def __init__(self, state_path: str):
        self.state_path = os.path.abspath(state_path)

    # -- low level -----------------------------------------------------
    def _call(self, tool_name: str, /, **kwargs) -> dict:
        import game_engine.mcp_server as server
        fn = getattr(server, tool_name, None)
        if fn is None:
            return {"ok": False, "error": "未知工具：%s" % tool_name}
        try:
            sig = inspect.signature(fn)
            accepted = {p.name for p in sig.parameters.values()
                        if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)}
            filtered = {k: v for k, v in kwargs.items() if k in accepted and v is not None}
            server.set_active_path(self.state_path)
            result = fn(**filtered)
            if isinstance(result, dict):
                result = _jsonable(result)
                result.setdefault("ok", True)
                return result
            return {"ok": True, "data": _jsonable(result)}
        except TypeError as exc:
            return {"ok": False, "error": "参数不对：%s" % str(exc)[:180]}
        except Exception as exc:  # noqa: BLE001 - tool errors become model-readable results
            return {"ok": False, "error": model_config.redact(str(exc))[:240]}

    # -- lifecycle -----------------------------------------------------
    def new_game(self, *, name: str = "", setting_path: str = "", template: str = "",
                 seed: int | None = None, player_name: str = "") -> dict:
        if template:
            return self._call("template_start", template=template, name=name, player_name=player_name)
        if setting_path:
            if not name:
                name = os.path.basename(setting_path).split(".")[0] or "新的一局"
            return self._call("session_new", name=name, setting_path=setting_path, seed=seed)
        return {"ok": False, "error": "需要 setting_path 或 template 之一"}

    def open_game(self, *, path: str = "", name: str = "") -> dict:
        if name:
            return self._call("session_switch", name=name)
        if path:
            return self._call("world_open", state_path=path)
        return {"ok": False, "error": "需要 path 或 name 之一"}

    def saves(self, *, action: str = "list", **kwargs) -> dict:
        if action == "list":
            return self._call("session_list", include_trash=kwargs.get("include_trash", False))
        if action == "manage":
            return self._call("session_manage", action=kwargs.get("manage_action", "trash"),
                              name=kwargs.get("name", ""))
        if action == "import":
            return self._call("session_import", path=kwargs.get("path", ""),
                              name=kwargs.get("name", ""),
                              overwrite=kwargs.get("overwrite", False))
        return {"ok": False, "error": "saves.action 只能是 list/manage/import"}

    def snapshot(self, *, action: str = "create", **kwargs) -> dict:
        if action == "create":
            return self._call("snapshot", label=kwargs.get("label", ""))
        if action == "restore":
            return self._call("restore", snapshot_path=kwargs.get("snapshot_path", ""))
        if action == "list":
            return self._call("session_snapshot", label=kwargs.get("label", ""), list_only=True)
        return {"ok": False, "error": "snapshot.action 只能是 create/restore/list"}

    # -- read / progress / story ---------------------------------------
    def inspect(self, *, view: str = "status", **kwargs) -> dict:
        if view == "state":
            return self._call("read_state")
        if view == "world":
            return self._call("world_state")
        if view == "progress":
            return {"ok": True, "playbook": self._call("playbook_info"),
                    "quests": self._call("quest_status", include_dormant=kwargs.get("include_dormant", False))}
        if view == "memory":
            return self._call("recap", recent=kwargs.get("recent", 12))
        return self._call("status")

    def progress(self, *, action: str = "status", **kwargs) -> dict:
        if action == "status":
            return {"ok": True, "playbook": self._call("playbook_info"),
                    "quests": self._call("quest_status", include_dormant=kwargs.get("include_dormant", False))}
        if action == "advance":
            return self._call("quest_advance", quest=kwargs.get("quest", ""),
                              stage=kwargs.get("stage", ""), note=kwargs.get("note", ""))
        if action == "failure":
            return self._call("failure_tick", amount=kwargs.get("amount", 1),
                              reason=kwargs.get("reason", ""))
        return {"ok": False, "error": "progress.action 只能是 status/advance/failure"}

    def story(self, *, action: str = "publish", **kwargs) -> dict:
        if action == "publish":
            return self._call("publish_prose", text=kwargs.get("text", ""),
                              location=kwargs.get("location", ""))
        if action == "narrative":
            return self._call("narrative")
        return {"ok": False, "error": "story.action 只能是 publish/narrative"}

    def memory(self, *, action: str = "recap", **kwargs) -> dict:
        if action == "recap":
            return self._call("recap", recent=kwargs.get("recent", 12),
                              budget_chars=kwargs.get("budget_chars", 0))
        if action == "search":
            return self._call("recall", query=kwargs.get("query", ""), limit=kwargs.get("limit", 8))
        if action == "summary":
            return self._call("write_summary", text=kwargs.get("text", ""))
        if action == "remember":
            return self._call("context_remember", text=kwargs.get("text", ""),
                              kind=kwargs.get("kind", "fact"), keys=kwargs.get("keys"),
                              subject=kwargs.get("subject", ""), source=kwargs.get("source", ""),
                              confidence=kwargs.get("confidence", 1.0), ttl=kwargs.get("ttl", 0),
                              importance=kwargs.get("importance"), supersede=kwargs.get("supersede", False),
                              witnesses=kwargs.get("witnesses"), public=kwargs.get("public", False))
        if action == "known":
            return self._call("context_known", character=kwargs.get("character", "player"),
                              limit=kwargs.get("limit", 12))
        if action == "tell":
            return self._call("context_tell", fact_id=kwargs.get("fact_id", ""),
                              to=kwargs.get("to", ""), how=kwargs.get("how", "told"))
        if action == "search_facts":
            return self._call("context_search", query=kwargs.get("query", ""), keys=kwargs.get("keys"),
                              kind=kwargs.get("kind", ""), status=kwargs.get("status", "open"),
                              limit=kwargs.get("limit", 12), ranked=kwargs.get("ranked", True))
        if action == "forget":
            return self._call("context_forget", fact_id=kwargs.get("fact_id", ""),
                              keys=kwargs.get("keys"), kind=kwargs.get("kind", ""),
                              status=kwargs.get("status", ""))
        return {"ok": False, "error": "memory.action 不在支持范围"}

    def knowledge(self, *, action: str = "search", **kwargs) -> dict:
        return self._call("knowledge", action=action, **kwargs)

    def context(self, *, action: str = "pack", **kwargs) -> dict:
        if action == "pack":
            return self._call("context_pack", scene_text=kwargs.get("scene_text", ""),
                              recent=kwargs.get("recent", 8), budget_chars=kwargs.get("budget_chars", 0))
        if action == "narrate":
            return self._call("narration_context", scene_text=kwargs.get("scene_text", ""),
                              recent=kwargs.get("recent", 12))
        if action == "lookup":
            return self._call("lore_lookup", text=kwargs.get("text", ""))
        if action == "import":
            return self._call("import_lorebook", path=kwargs.get("path", ""))
        return {"ok": False, "error": "context.action 只能是 pack/narrate/lookup/import"}

    def canon(self, *, action: str = "brief", **kwargs) -> dict:
        if action == "brief":
            return self._call("canon_brief", scene_text=kwargs.get("scene_text", ""),
                              limit=kwargs.get("limit", 14))
        if action == "check":
            return self._call("canon_check", facts=kwargs.get("facts") or [],
                              status=kwargs.get("status", "revealed"),
                              allow_override=kwargs.get("allow_override", False))
        if action == "commit":
            return self._call("canon_commit", facts=kwargs.get("facts") or [],
                              status=kwargs.get("status", "revealed"),
                              source=kwargs.get("source", "play"),
                              allow_override=kwargs.get("allow_override", False),
                              reason=kwargs.get("reason", ""))
        if action == "init":
            return self._call("canon_init", bible=kwargs.get("bible") or {})
        return {"ok": False, "error": "canon.action 只能是 brief/check/commit/init"}

    # -- sheet / systems / worlds --------------------------------------
    def characters(self, *, action: str, **kwargs) -> dict:
        if action == "read":
            return self._call("character_card_read", path=kwargs.get("path", ""))
        if action == "add":
            return self._call("add_character", path=kwargs.get("path", ""),
                              entity_id=kwargs.get("entity_id", ""), attrs=kwargs.get("attrs"),
                              hp=kwargs.get("hp", 100), gold=kwargs.get("gold", 0),
                              location=kwargs.get("location", ""), level=kwargs.get("level", "凡人"))
        if action == "spawn":
            return self._call("spawn_npc", id=kwargs.get("id") or kwargs.get("entity_id") or "",
                              name=kwargs.get("name", ""), faction=kwargs.get("faction", ""),
                              attrs=kwargs.get("attrs"), level=kwargs.get("level", "凡人"),
                              hp=kwargs.get("hp", 60), gold=kwargs.get("gold", 0),
                              location=kwargs.get("location", ""), desc=kwargs.get("desc", ""),
                              personality=kwargs.get("personality", ""),
                              activity=kwargs.get("activity", ""), intent=kwargs.get("intent", ""),
                              mood=kwargs.get("mood", ""), routine=kwargs.get("routine", ""),
                              status=kwargs.get("status", ""), agenda=kwargs.get("agenda", ""),
                              aliases=kwargs.get("aliases"))
        return {"ok": False, "error": "characters.action 只能是 read/add/spawn"}

    def sheet(self, *, action: str = "profile", **kwargs) -> dict:
        if action == "profile":
            return self._call("game_profile", profile=kwargs.get("profile"))
        if action == "adjust":
            return self._call("game_adjust", key=kwargs.get("key", ""),
                              kind=kwargs.get("kind", "resources"), delta=kwargs.get("delta"),
                              value=kwargs.get("value"))
        if action == "tag":
            return self._call("game_tag", tag=kwargs.get("tag", ""), remove=kwargs.get("remove", False))
        if action == "sheet":
            return self._call("game_sheet", fields=kwargs.get("fields") or {},
                              remove=kwargs.get("remove", False))
        return {"ok": False, "error": "sheet.action 只能是 profile/adjust/tag/sheet"}

    def systems(self, *, action: str = "status", **kwargs) -> dict:
        if action == "schema":
            return self._call("system_schema")
        if action == "define":
            return self._call("system_define", system=kwargs.get("system") or {},
                              replace=kwargs.get("replace", True))
        if action == "run":
            return self._call("system_run", system_id=kwargs.get("system_id", ""),
                              action=kwargs.get("run_action", "status"), params=kwargs.get("params"))
        if action == "status":
            return self._call("system_status", system_id=kwargs.get("system_id", ""))
        if action == "remove":
            return self._call("system_remove", system_id=kwargs.get("system_id", ""))
        return {"ok": False, "error": "systems.action 只能是 schema/define/run/status/remove"}

    def worlds(self, *, action: str = "list", **kwargs) -> dict:
        if action == "schema":
            return self._call("world_schema")
        if action == "list":
            return self._call("templates_list")
        if action == "info":
            return self._call("template_info", template=kwargs.get("template", ""))
        if action == "apply":
            return self._call("template_apply", template=kwargs.get("template", ""),
                              overrides=kwargs.get("overrides"), name=kwargs.get("name", ""),
                              player_name=kwargs.get("player_name", ""))
        return {"ok": False, "error": "worlds.action 只能是 schema/list/info/apply"}

    def calc(self, *, action: str = "models", **kwargs) -> dict:
        if action == "models":
            return self._call("model_list")
        if action == "model":
            return self._call("model", name=kwargs.get("name", ""), params=kwargs.get("params") or {})
        if action == "merit":
            return self._call("merit", aid=kwargs.get("aid", 0.5),
                              sincerity=kwargs.get("sincerity", 0.5))
        if action == "weight":
            return self._call("narrative_weight", probability=kwargs.get("probability", 0.5))
        return {"ok": False, "error": "calc.action 只能是 models/model/merit/weight"}

    def panel(self, *, action: str = "pending", **kwargs) -> dict:
        if action == "pending":
            return self._call("pending_actions", limit=kwargs.get("limit", 20),
                              mark_done=kwargs.get("mark_done", False))
        if action == "open":
            return self._call("open_panel", port=kwargs.get("port", 8765))
        if action == "close":
            return self._call("close_panel")
        return {"ok": False, "error": "panel.action 只能是 pending/open/close"}

    # -- direct player actions -----------------------------------------
    def combat(self, **kwargs) -> dict:
        return self._call("combat", attacker=kwargs.get("attacker", "player"),
                          defender=kwargs.get("defender", ""),
                          action_type=kwargs.get("action_type", "attack"),
                          skill=kwargs.get("skill"))

    def combat_preview(self, **kwargs) -> dict:
        return self._call("combat_preview", attacker=kwargs.get("attacker", "player"),
                          defender=kwargs.get("defender", ""),
                          action_type=kwargs.get("action_type", "attack"))

    def trade(self, **kwargs) -> dict:
        return self._call("trade", location=kwargs.get("location", ""),
                          item=kwargs.get("item", ""), direction=kwargs.get("direction", "buy"),
                          quantity=kwargs.get("quantity", 1), entity=kwargs.get("entity", "player"))

    def social(self, **kwargs) -> dict:
        return self._call("social", actor=kwargs.get("actor", "player"),
                          target=kwargs.get("target", ""), event=kwargs.get("event", ""),
                          intensity=kwargs.get("intensity", 1.0))

    def karma(self, **kwargs) -> dict:
        return self._call("karma", actor=kwargs.get("actor", "player"),
                          karma_type=kwargs.get("karma_type", ""), victim=kwargs.get("victim"))

    def tick(self) -> dict:
        return self._call("tick")

    def advance(self, **kwargs) -> dict:
        return self._call("advance", next_level=kwargs.get("next_level", ""),
                          insight=kwargs.get("insight", 0.0))

    def travel(self, **kwargs) -> dict:
        return self._call("travel", location=kwargs.get("location", ""),
                          note=kwargs.get("note", ""), desc=kwargs.get("desc", ""))

    def use_item(self, **kwargs) -> dict:
        return self._call("use_item", item=kwargs.get("item", ""),
                          quantity=kwargs.get("quantity", 1), location=kwargs.get("location", ""))

    def roll(self, **kwargs) -> dict:
        return self._call("roll", attribute=kwargs.get("attribute", ""),
                          difficulty=kwargs.get("difficulty", 10), dice=kwargs.get("dice", "d20"),
                          mode=kwargs.get("mode", "add"), modifiers=kwargs.get("modifiers"),
                          actor=kwargs.get("actor", "player"), opposed_by=kwargs.get("opposed_by", ""),
                          pool_size=kwargs.get("pool_size", 0), reason=kwargs.get("reason", ""))

    def configure(self, **kwargs) -> dict:
        return self._call("configure", **kwargs)
