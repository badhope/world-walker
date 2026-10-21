"""
状态结构定义 (State Schema)

游戏状态是一个 JSON 对象,Agent 通过 read/write 与引擎交换。
引擎本身不持有状态——它每次调用都接收完整状态 JSON，返回更新后的完整状态 JSON。
这样 Agent 只需要在游戏开始时 load_state()，每回合通过 engine 结算后 save_state()。

状态结构:
{
  "tick": 123,                    # 回合数
  "entities": {
    "player": {
      "name": "玩家",
      "faction": "散修",
      "attrs": {"str": 12, "dex": 14, "int": 10, "con": 11, "cha": 9},
      "hp": 80, "hp_max": 80,     # 生命值
      "mp": 30, "mp_max": 30,     # 法力/内力
      "level": "练气三层",
      "gold": 500,
      "location": "bamboo_tea_booth"
    },
    "old_chen": { ... }
  },
  "relations": {
    "player:old_chen": {"affinity": 10, "respect": -5},
    ...
  },
  "market": {
    "bamboo_tea_booth": {
      "回灵丹": {"price": 50, "supply": 20, "base_price": 50},
      ...
    }
  },
  "karma_ledger": [
    {"from": "player", "to": "old_chen", "type": "赊欠", "amount": 50, "tick": 120, "settled": false}
  ],
  "world_flags": ["innkeeper_dead"],   # 触发过的世界事件
  "event_log": [...]                     # 最近 N 条事件
}
"""

import json, random

def new_game():
    """返回一个初始状态"""
    return {
        "tick": 0,
        "entities": {},
        "relations": {},
        "market": {},
        "karma_ledger": [],
        "world_flags": [],
        "event_log": []
    }

def load_state(path):
    """从路径加载状态 JSON"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def _archive_file(path, state):
    """按归档世代选择归档文件：`<path>.log.jsonl` 或 `<path>.log.<gen>.jsonl`。

    为什么按世代分文件：快照回退会让状态里的 archived_events 退到旧值，而归档是
    追加写的。若强行把共享文件截断到旧计数，会把"未来分支已经写下、但仍属用户
    历史"的事件物理删除（这是不可接受的数据丢失）。按世代隔离后，回退只需切回
    该世代的文件，任何分支的归档都完整保留。
    """
    gen = int(state.get("archive_generation", 0) or 0)
    return path + ".log.jsonl" if gen == 0 else "%s.log.%d.jsonl" % (path, gen)


def save_state(state, path):
    """保存状态 JSON 到路径。

    长局保护：写入前把超出保留量的旧事件归档到 `<path>.log.jsonl`（追加式），
    保留量见 state.config.event_log_keep（默认 200）。这样状态文件与上下文都不会被历史撑爆，
    旧事仍可按关键词用 recall 回捞。

    回退安全：归档按 archive_generation 分文件（见 _archive_file）。快照回退时
    状态的 generation 与 archived_events 一起退到旧值，因此只会切回旧世代文件，
    不会截断/删除任何已写下的归档。已有归档永久只增不减。
    """
    cfg = state.get("config") or {}
    keep = int(cfg.get("event_log_keep", 200))
    log = state.get("event_log") or []
    if len(log) > keep:
        overflow, state["event_log"] = log[:-keep], log[-keep:]
        if cfg.get("archive", True):
            with open(_archive_file(path, state), "a", encoding="utf-8") as f:
                for e in overflow:
                    f.write(json.dumps(e, ensure_ascii=False) + "\n")
        else:
            # 不落文件的归档不计入计数，否则计数与归档行数从第一天起就不一致
            pass
        if cfg.get("archive", True):
            state["archived_events"] = int(state.get("archived_events", 0)) + len(overflow)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def seed_rng(state) -> None:
    """按状态里的 rng_seed + rng_counter 重置全局随机源（带种子可复现）。

    同一 state、同一计数器、同一行动 → 同一结果；计数器随每次结算递增并落盘，
    保证同一回合内的多次行动不会复用同一段随机序列。CLI（engine.py）与
    MCP（mcp_server.py）共用本函数，两条入口的确定性语义一致。
    装有 numpy 时顺带重置其全局种子（可选，缺失则静默跳过）。
    """
    seed = state.get("rng_seed")
    if seed is None:
        return
    counter = int(state.get("rng_counter", 0)) + 1
    state["rng_counter"] = counter
    mixed = (int(seed) * 1000003 + int(state.get("tick", 0)) * 7919 + counter) % (2 ** 32)
    random.seed(mixed)
    try:
        import numpy as np
        np.random.seed(mixed)
    except ImportError:  # numpy 为可选依赖，缺失时仅跳过其全局种子重置
        pass

def entity_key(a, b):
    """生成关系键——保证对称性，始终按字母顺序"""
    return f"{min(a,b)}:{max(a,b)}"

def get_relation(state, a, b):
    """安全获取关系，不存在返回默认值（返回副本，避免原地修改污染）"""
    key = entity_key(a, b)
    r = state.get("relations", {}).get(key, {"affinity": 0, "respect": 0})
    return dict(r)

def _clamp(value, lo=-100, hi=100):
    """将值限制在 [lo, hi] 范围内"""
    return max(lo, min(hi, value))

def set_relation(state, a, b, affinity_delta=0, respect_delta=0):
    """更新关系值 (affinity/respect clamp 到 -100~100)"""
    key = entity_key(a, b)
    if "relations" not in state:
        state["relations"] = {}
    if key not in state["relations"]:
        state["relations"][key] = {"affinity": 0, "respect": 0}
    state["relations"][key]["affinity"] = _clamp(state["relations"][key]["affinity"] + affinity_delta)
    state["relations"][key]["respect"] = _clamp(state["relations"][key]["respect"] + respect_delta)

def add_karma(state, debtor, creditor, ktype, amount):
    """添加因果债记录"""
    entry = {
        "from": debtor,
        "to": creditor,
        "type": ktype,
        "amount": amount,
        "tick": state["tick"],
        "settled": False
    }
    ledger = state.setdefault("karma_ledger", [])
    ledger.append(entry)
    cap = int((state.get("config") or {}).get("karma_ledger_keep", 500))
    _prune_settled(state, ledger, cap)
    return entry

def _prune_settled(state, ledger, cap):
    """结算完毕的业债条目不再被任何读取器使用（get_unsettled_karma 已过滤），
    超保留量时从最旧的开始裁，防止长局无界增长。"""
    if len(ledger) <= cap:
        return
    settled = [i for i, e in enumerate(ledger) if e.get("settled")]
    for i in sorted(settled, reverse=True):
        if len(ledger) <= cap:
            break
        del ledger[i]

def get_unsettled_karma(state, entity):
    """获取某实体未偿还的因果债总额"""
    return sum(
        e["amount"] for e in state["karma_ledger"]
        if e["from"] == entity and not e["settled"]
    )

def log_event(state, etype, desc):
    """记录事件到日志"""
    log = state.get("event_log")
    if not isinstance(log, list):
        log = state["event_log"] = []
    log.append({
        "tick": state.get("tick", 0),
        "type": etype,
        "desc": desc
    })
    # 只追加；截断与归档统一在 save_state 里做（保证任何写入路径都不会漏归档）
