"""
叙事引擎 (Narrative Engine)

基于: 叙事学与游戏研究文献（Bartle 玩家类型 / 叙事传输 / 空间叙事 /
      涌现叙事），为 Agent 提供结构化叙事元数据
提供涌现故事的结构化元数据。Agent 用这些元数据生成文字描写。
"""

import math, random, json
from typing import List, Dict

def player_identity_vector(state: Dict) -> Dict:
    """玩家身份多维坐标 (Bartle 扩展 + MFT)"""
    events = state.get("event_log", [])
    
    achiever = killer = socializer = 0
    for ev in events:
        desc = ev.get("desc", "")
        if "击败" in desc or "杀" in desc:
            killer += 1
        if "购买" in desc or "获得" in desc:
            achiever += 1
        if "帮助" in desc or "声望" in desc:
            socializer += 1
    
    total = max(1, len(events))
    locations = set(ev.get("location", "") for ev in events)
    
    return {
        "achiever": min(100, achiever * 100 / total),
        "explorer": min(100, len(locations) * 25),
        "socializer": min(100, socializer * 100 / total),
        "killer": min(100, killer * 100 / total),
    }

def flow_channel_status(state: Dict) -> Dict:
    """基于最近战斗胜率判定心流/焦虑/无聊"""
    events = state.get("event_log", [])
    combat_events = [e for e in events if e.get("type") == "combat"]
    
    if len(combat_events) < 3:
        return {"state": "flow", "adjustment": 0.0, "confidence": "low"}
    
    recent = combat_events[-5:]
    wins = sum(1 for e in recent if "命中" in e.get("desc", "") and "被击败" not in e.get("desc", ""))
    win_rate = wins / len(recent)
    
    target = 0.65
    if abs(win_rate - target) < 0.15:
        return {"state": "flow", "adjustment": 0.0, "win_rate": round(win_rate, 2)}
    elif win_rate > target + 0.15:
        delta = min(0.3, (win_rate - target) * 0.5)
        return {"state": "boredom", "adjustment": round(delta, 3), "win_rate": round(win_rate, 2)}
    else:
        delta = max(-0.3, (win_rate - target) * 0.5)
        trigger_luck = win_rate < 0.3
        return {"state": "anxiety", "adjustment": round(delta, 3), "trigger_luck": trigger_luck, "win_rate": round(win_rate, 2)}

def narrative_event_weight(event_probability: float, base_importance: float = 1.0) -> float:
    """事件叙事权重 = 自信息量 I(E) = -log P(E)"""
    if event_probability <= 0:
        return float('inf')
    return -math.log(event_probability) * base_importance

def check_world_emergent_events(state: Dict) -> List[Dict]:
    """基于世界状态阈值检查涌现事件"""
    events = []
    tick = state.get("tick", 0)
    event_count = len(state.get("event_log", []))
    
    # 大劫预兆
    if event_count > 10 and tick > 20:
        events.append({
            "type": "calamity_omen",
            "desc": "天地灵气出现异常波动，天机紊乱",
            "probability": min(0.5, event_count / 50)
        })
    
    # 玩家名气扩散
    unique_relations = set()
    for k in state.get("relations", {}).keys():
        parts = k.split(":")
        for p in parts:
            if p != "player":
                unique_relations.add(p)
    
    if len(unique_relations) > 3:
        events.append({
            "type": "reputation_spread",
            "desc": f"你的名声已在{len(unique_relations)}个圈子传开",
            "probability": min(0.8, len(unique_relations) / 8)
        })
    
    # 业债爆发
    karma = state.get("karma_ledger", [])
    total = sum(e.get("amount", 0) for e in karma if not e.get("settled"))
    if total >= 300:  # 与 karma.py 的 extreme/catastrophe 阈值一致
        events.append({
            "type": "karma_collapse",
            "desc": "因果大清算即将降临...",
            "probability": min(0.9, total / 300)
        })
    
    return events

def update_player_moral_identity(state: Dict) -> Dict:
    """从事件日志累加最近行为的六维道德向量"""
    events = state.get("event_log", [])
    vec = {"care": 0, "fairness": 0, "loyalty": 0, "authority": 0, "sanctity": 0, "liberty": 0}
    
    moral_map = {
        "help_innocent": {"care": 2, "fairness": 1},
        "murder_innocent": {"care": -3, "fairness": -2, "sanctity": -1},
        "murder_evil": {"fairness": -1, "loyalty": 1},
        "betray": {"loyalty": -3, "fairness": -2},
        "theft": {"fairness": -2},
        "lie": {"fairness": -1},
        "oath_broken": {"loyalty": -3, "authority": -2, "sanctity": -2},
    }
    
    for ev in events:
        ev_str = json.dumps(ev, ensure_ascii=False) if isinstance(ev, dict) else str(ev)
        for k, deltas in moral_map.items():
            if k in ev_str or any(word in ev_str for word in [k, k.replace("_", " ")]):
                for dim, val in deltas.items():
                    vec[dim] = vec.get(dim, 0) + val
    
    return vec

def panarchy_phase_check(state: Dict) -> Dict:
    """世界 Panarchy 四相位判定"""
    from game_engine.rules.world_dynamics import panarchy_phase
    
    entities = state.get("entities", {})
    world_flags = state.get("world_flags", [])
    
    n_factions = len(set(e.get("faction", "") for e in entities.values()))
    capital = min(1.0, n_factions / 6)
    connectedness = min(1.0, len(world_flags) / 15)
    resilience = 0.5
    
    return panarchy_phase(capital, connectedness, resilience)
