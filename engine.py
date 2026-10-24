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
    # 真正执行 __init__.py：包级元数据（__version__ 等）在里面；只建对象不执行会拿不到。
    _spec.loader.exec_module(_pkg)

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
from game_engine.rules.world_evolution import evolve as evolve_world, world_summary

def _build_parser():
    """14 条子命令的声明集中在一处；每条只描述参数，不承载业务。"""
    parser = argparse.ArgumentParser(description="规则引擎")
    sub = parser.add_subparsers(dest="action")
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--state", required=True)

    p = sub.add_parser("combat", parents=[parent])
    p.add_argument("--attacker", required=True)
    p.add_argument("--defender", required=True)
    p.add_argument("--action_type", default="attack")
    p.add_argument("--skill", default=None)

    p = sub.add_parser("trade", parents=[parent])
    p.add_argument("--location", required=True)
    p.add_argument("--item", required=True)
    p.add_argument("--quantity", type=int, default=1)
    p.add_argument("--direction", choices=["buy", "sell"], required=True)
    p.add_argument("--entity", default="player")

    p = sub.add_parser("social", parents=[parent])
    p.add_argument("--actor", required=True)
    p.add_argument("--target", required=True)
    p.add_argument("--event", required=True)
    p.add_argument("--intensity", type=float, default=1.0)

    p = sub.add_parser("karma", parents=[parent])
    p.add_argument("--actor", required=True)
    p.add_argument("--victim", default=None)
    p.add_argument("--karma_type", required=True)

    for name in ("tick", "flow", "identity", "narrative", "world_state",
                 "panarchy", "moral_update"):
        sub.add_parser(name, parents=[parent])

    p = sub.add_parser("cognition", parents=[parent])
    p.add_argument("--entity", default="player")

    p = sub.add_parser("merit", parents=[parent])
    p.add_argument("--aid", type=float, default=0.5)
    p.add_argument("--sincerity", type=float, default=0.5)

    p = sub.add_parser("info_weight", parents=[parent])
    p.add_argument("--probability", type=float, required=True)
    return parser


def _do_combat(state, args, result):
    skill = json.loads(args.skill) if args.skill else None
    r = resolve_combat(state, args.attacker, args.defender, args.action_type, skill)
    result.update(r)
    for e in r.get("events", []):
        log_event(state, "combat", e)
    return True


def _do_trade(state, args, result):
    r = resolve_trade(state, args.location, args.item, args.quantity,
                      args.direction == "buy", args.entity)
    result.update(r)
    for e in r.get("events", []):
        log_event(state, "trade", e)
    return True


def _do_social(state, args, result):
    r = resolve_social_event(state, args.actor, args.target, args.event, args.intensity)
    result.update(r)
    for e in r.get("events", []):
        log_event(state, "social", e)
    return True


def _do_karma(state, args, result):
    r = resolve_karma(state, args.actor, args.victim, args.karma_type)
    result.update(r)
    for e in r.get("events", []):
        log_event(state, "karma", e)
    cons = get_karma_consequence(state, args.actor)
    if cons["triggered"]:
        result["karma_consequence"] = cons
    return True


def _do_tick(state, args, result):
    """与 MCP 的 tick 工具同一语义：市场 + **世界演化** + tick+1。

    旧 CLI 只推市价与计数，导致同一存档走 CLI 与走 MCP 会得到两个不同的世界
    （违反 INV-E4/E6，也让"世界自己会动"在 CLI 通道上不成立）。
    """
    tick_market(state)
    state["tick"] += 1
    world = evolve_world(state)
    for desc in world.get("events", []):
        log_event(state, "world", str(desc))
    log_event(state, "tick", "回合%d结束" % state["tick"])
    result.update({
        "events": ["回合%d结束" % state["tick"]] + [str(e) for e in world.get("events", [])],
        "panarchy_phase": world.get("phase"),
        "capital": world.get("capital"),
        "connectedness": world.get("connectedness"),
        "factions": world.get("factions"),
        "rumors": world.get("rumors"),
        "market_index": world.get("market_index"),
    })
    return True


def _do_flow(state, args, result):
    result.update(flow_channel_status(state))
    return False


def _do_identity(state, args, result):
    result["identity"] = player_identity_vector(state)
    return False


def _do_narrative(state, args, result):
    result["emergent_events"] = check_world_emergent_events(state)
    result["panarchy_phase"] = panarchy_phase_check(state)
    return False


def _do_world_state(state, args, result):
    # 与 MCP world_state 同构：势力/相位/谣言/风气/物价指数（不是只有几个计数）。
    result.update(world_summary(state))
    result.update({
        "tick": state.get("tick", 0),
        "entity_count": len(state.get("entities", {})),
        "relation_count": len(state.get("relations", {})),
        "karma_entries": len(state.get("karma_ledger", [])),
        "world_flags": state.get("world_flags", []),
    })
    return False


def _do_panarchy(state, args, result):
    result.update(panarchy_phase_check(state))
    return False


def _do_moral_update(state, args, result):
    result["moral_vector"] = update_player_moral_identity(state)
    return False


def _do_cognition(state, args, result):
    ent = state["entities"].get(args.entity, {})
    attrs = ent.get("attrs", {})
    # 境界等级由悟性推导，与 mcp_server.status 一致（此前硬传 0，任何实体得到同一预算）
    realm_level = int(attrs.get("int", 10) // 5)
    budget = daily_cognitive_budget(realm_level, "正常")
    result.update({
        "entity": args.entity,
        "realm_level": realm_level,
        "cognitive_budget": budget,
        "system2_likely": should_use_system2(budget, 0.7),
    })
    return False


def _do_merit(state, args, result):
    result["merit_value"] = merit_quality(args.aid, args.sincerity)
    return False


def _do_info_weight(state, args, result):
    result["info_weight"] = event_information(args.probability)
    return False


# 命令 → 处理函数。返回 True 表示"改了状态，需要落盘"。
COMMANDS = {
    "combat": _do_combat,
    "trade": _do_trade,
    "social": _do_social,
    "karma": _do_karma,
    "tick": _do_tick,
    "flow": _do_flow,
    "identity": _do_identity,
    "narrative": _do_narrative,
    "world_state": _do_world_state,
    "panarchy": _do_panarchy,
    "moral_update": _do_moral_update,
    "cognition": _do_cognition,
    "merit": _do_merit,
    "info_weight": _do_info_weight,
}


def main():
    parser = _build_parser()
    args = parser.parse_args()
    if not args.action:
        parser.print_help()
        sys.exit(1)

    handler = COMMANDS.get(args.action)
    if handler is None:  # pragma: no cover - argparse 已限制可选值
        parser.error("未知命令: %s" % args.action)

    state = load_state(args.state)
    seed_rng(state)   # 与 MCP 共用：同一 state + 同一行动 → 同一结果
    result = {"action": args.action}
    dirty = handler(state, args, result)   # 只有写命令返回 True；只读命令不得改写状态文件
    if dirty:
        save_state(state, args.state)
    result["_tick"] = state["tick"]
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
