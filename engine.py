#!/usr/bin/env python3
"""
规则引擎 - 统一 CLI 入口
"""

import json, sys, argparse, os

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_SCRIPT_DIR)
sys.path.insert(0, _PARENT_DIR)

# 引擎内部统一用 `import game_engine.*`，过去要求仓库目录名必须叫 game_engine。
# 这里注册包别名，使任意克隆目录名 / pip 安装方式都能导入。
if "game_engine" not in sys.modules:
    import importlib.util
    _spec = importlib.util.spec_from_file_location(
        "game_engine", os.path.join(_SCRIPT_DIR, "__init__.py"),
        submodule_search_locations=[_SCRIPT_DIR])
    _pkg = importlib.util.module_from_spec(_spec)
    _pkg.__path__ = [_SCRIPT_DIR]
    sys.modules["game_engine"] = _pkg

from game_engine.state_schema import load_state, save_state, log_event, seed_rng
from game_engine.rules.combat import resolve_combat
from game_engine.rules.economy import resolve_trade, tick_market
from game_engine.rules.social import resolve_social_event
from game_engine.rules.karma import resolve_karma, get_karma_consequence

from game_engine.rules.cognition import daily_cognitive_budget, should_use_system2
from game_engine.rules.world_dynamics import event_information
from game_engine.rules.social_extended import merit_quality
from game_engine.rules.narrative_engine import (
    flow_channel_status, player_identity_vector, check_world_emergent_events,
    update_player_moral_identity, panarchy_phase_check
)

def main():
    parser = argparse.ArgumentParser(description="规则引擎")
    sub = parser.add_subparsers(dest="action")
    
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--state", required=True)
    
    # combat
    p = sub.add_parser("combat", parents=[parent])
    p.add_argument("--attacker", required=True)
    p.add_argument("--defender", required=True)
    p.add_argument("--action_type", default="attack")
    p.add_argument("--skill", default=None)
    
    # trade
    p = sub.add_parser("trade", parents=[parent])
    p.add_argument("--location", required=True)
    p.add_argument("--item", required=True)
    p.add_argument("--quantity", type=int, default=1)
    p.add_argument("--direction", choices=["buy","sell"], required=True)
    p.add_argument("--entity", default="player")
    
    # social
    p = sub.add_parser("social", parents=[parent])
    p.add_argument("--actor", required=True)
    p.add_argument("--target", required=True)
    p.add_argument("--event", required=True)
    p.add_argument("--intensity", type=float, default=1.0)
    
    # karma
    p = sub.add_parser("karma", parents=[parent])
    p.add_argument("--actor", required=True)
    p.add_argument("--victim", default=None)
    p.add_argument("--karma_type", required=True)
    
    # tick
    sub.add_parser("tick", parents=[parent])
    
    # new commands
    sub.add_parser("flow", parents=[parent])
    sub.add_parser("identity", parents=[parent])
    sub.add_parser("narrative", parents=[parent])
    sub.add_parser("world_state", parents=[parent])
    sub.add_parser("panarchy", parents=[parent])
    sub.add_parser("moral_update", parents=[parent])
    
    p = sub.add_parser("cognition", parents=[parent])
    p.add_argument("--entity", default="player")
    
    p = sub.add_parser("merit", parents=[parent])
    p.add_argument("--aid", type=float, default=0.5)
    p.add_argument("--sincerity", type=float, default=0.5)
    
    p = sub.add_parser("info_weight", parents=[parent])
    p.add_argument("--probability", type=float, required=True)
    
    args = parser.parse_args()
    if not args.action:
        parser.print_help()
        sys.exit(1)
    
    state = load_state(args.state)
    seed_rng(state)   # 与 MCP 共用：同一 state + 同一行动 → 同一结果
    result = {"action": args.action}
    dirty = False      # 只有变更状态的分支才落盘；只读命令不得改写状态文件

    if args.action == "combat":
        skill = json.loads(args.skill) if args.skill else None
        r = resolve_combat(state, args.attacker, args.defender, args.action_type, skill)
        result.update(r)
        for e in r.get("events", []): log_event(state, "combat", e)
        dirty = True

    elif args.action == "trade":
        r = resolve_trade(state, args.location, args.item, args.quantity, args.direction=="buy", args.entity)
        result.update(r)
        for e in r.get("events", []): log_event(state, "trade", e)
        dirty = True

    elif args.action == "social":
        r = resolve_social_event(state, args.actor, args.target, args.event, args.intensity)
        result.update(r)
        for e in r.get("events", []): log_event(state, "social", e)
        dirty = True

    elif args.action == "karma":
        r = resolve_karma(state, args.actor, args.victim, args.karma_type)
        result.update(r)
        for e in r.get("events", []): log_event(state, "karma", e)
        cons = get_karma_consequence(state, args.actor)
        if cons["triggered"]:
            result["karma_consequence"] = cons
        dirty = True

    elif args.action == "tick":
        tick_market(state)
        state["tick"] += 1
        log_event(state, "tick", f"回合{state['tick']}结束")
        result["events"] = [f"回合{state['tick']}结束"]
        dirty = True
    
    elif args.action == "flow":
        r = flow_channel_status(state)
        result.update(r)
    
    elif args.action == "identity":
        identity = player_identity_vector(state)
        result["identity"] = identity
    
    elif args.action == "narrative":
        events = check_world_emergent_events(state)
        result["emergent_events"] = events
        phase = panarchy_phase_check(state)
        result["panarchy_phase"] = phase
    
    elif args.action == "world_state":
        result["tick"] = state.get("tick", 0)
        result["entity_count"] = len(state.get("entities", {}))
        result["relation_count"] = len(state.get("relations", {}))
        result["karma_entries"] = len(state.get("karma_ledger", []))
        result["world_flags"] = state.get("world_flags", [])
    
    elif args.action == "panarchy":
        result.update(panarchy_phase_check(state))
    
    elif args.action == "moral_update":
        result["moral_vector"] = update_player_moral_identity(state)
    
    elif args.action == "cognition":
        ent = state["entities"].get(args.entity, {})
        attrs = ent.get("attrs", {})
        # 境界等级由悟性推导，与 mcp_server.status 一致（此前硬传 0，任何实体都得到同一个预算）
        realm_level = int(attrs.get("int", 10) // 5)
        budget = daily_cognitive_budget(realm_level, "正常")
        result = {
            "entity": args.entity,
            "realm_level": realm_level,
            "cognitive_budget": budget,
            "system2_likely": should_use_system2(budget, 0.7),
        }
    
    elif args.action == "merit":
        result = {"merit_value": merit_quality(args.aid, args.sincerity)}
    
    elif args.action == "info_weight":
        result = {"info_weight": event_information(args.probability)}
    
    if dirty:
        save_state(state, args.state)
    result["_tick"] = state["tick"]
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
