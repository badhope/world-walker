"""
战斗结算规则 (Combat)

输入: state + attacker_id + defender_id + action_type
输出: combat_result dict (结构化战斗结果, 不含文字描写)

伤害公式: 基础伤害 × 攻击方str系数 × 防守方破防率 × 浮动(0.8~1.2)
暴击: dex差 > 3 时概率暴击 (1.5倍)
击杀: hp归零 → dead=true

两条**会改变结果的输入**（旧实现里它们只是面板上的装饰）：
- 世界相位（`state["panarchy"]["phase"]`）：Ω 动乱期命中更难、伤害更飘
- 心流（`flow_channel_status`）：无聊→命中下降（挑战不足），焦虑→命中上升（压力激发）
"""

import random


def _combat_modifiers(state):
    """返回 (命中倍率, 伤害倍率)。缺失/异常一律回退 1.0，不影响结算可用性。"""
    hit_mult = 1.0
    dmg_mult = 1.0
    try:
        from game_engine.rules.narrative_engine import flow_channel_status
        flow = flow_channel_status(state)
        adj = float(flow.get("adjustment", 0.0) or 0.0)
        # 无聊（adjustment>0）时命中下降；焦虑（<0）时命中上升（背水一战）
        hit_mult *= max(0.75, min(1.25, 1.0 - adj * 0.5))
    except Exception:  # nosec B110; aqg: top-level boundary —— 心流是辅助输入，坏了不许影响战斗
        pass
    try:
        phase = str((state.get("panarchy") or {}).get("phase") or "")
        if phase == "Ω":
            hit_mult *= 0.90
            dmg_mult *= 1.25
        elif phase == "α":
            hit_mult *= 0.95
            dmg_mult *= 1.10
        elif phase == "K":
            dmg_mult *= 0.95
    except Exception:  # nosec B110; aqg: top-level boundary —— 相位缺失时按无修正处理
        pass
    return hit_mult, dmg_mult


def resolve_combat(state, attacker_id, defender_id, action="attack", skill=None):
    """
    确定性战斗结算
    
    参数:
        state: 完整游戏状态
        attacker_id: 攻击方 entity id
        defender_id: 防守方 entity id
        action: "attack" / "heavy" / "flee"
        skill: 技能/功法 id (可选)
    
    返回: {
        "attacker": "player",
        "defender": "old_chen",
        "hit": true,
        "damage": 23,
        "crit": false,
        "defender_hp_after": 7,
        "defender_dead": false,
        "events": ["player命中old_chen造成23点伤害"]
    }
    """
    atk_ent = state["entities"].get(attacker_id)
    def_ent = state["entities"].get(defender_id)
    
    if not atk_ent or not def_ent:
        return {"error": "entity not found", "hit": False, "damage": 0}
    
    result = {
        "attacker": attacker_id,
        "defender": defender_id,
        "hit": False,
        "damage": 0,
        "crit": False,
        "defender_hp_after": def_ent.get("hp", 0),
        "defender_dead": False,
        "events": []
    }
    
    atk_attrs = atk_ent.get("attrs", {})
    def_attrs = def_ent.get("attrs", {})

    # 死目标守卫：气血已归零的实体不再参与结算。
    # 否则可以对尸体继续攻击、继续造成伤害、继续触发 defender_dead，
    # 进而重复记"击杀"里程碑（玩家可感知的行为错误，不只是数据瑕疵）。
    if int(def_ent.get("hp", 0) or 0) <= 0:
        result["events"].append(f"{def_ent.get('name', defender_id)}已经没有还手之力")
        result["target_already_dead"] = True
        return result
    
    # 计算命中（含等级差与相位/心流修正）
    atk_power = atk_attrs.get("str", 10) + atk_attrs.get("dex", 10) * 0.5
    def_power = def_attrs.get("str", 10) + def_attrs.get("dex", 10) * 0.7
    atk_tier_bonus = def_tier_bonus = 0.0
    try:
        from game_engine.rules.progression import tier_bonus
        atk_tier_bonus = tier_bonus(state, atk_ent)
        def_tier_bonus = tier_bonus(state, def_ent)
        atk_power += atk_tier_bonus
        def_power += def_tier_bonus
    except Exception:  # nosec B110; aqg: top-level boundary —— 阶梯配置坏了退回纯属性判定
        pass

    hit_mult, dmg_mult = _combat_modifiers(state)
    hit_chance = max(0.1, min(0.95, 0.5 + (atk_power - def_power) * 0.05))
    hit_chance = max(0.05, min(0.98, hit_chance * hit_mult))

    # 重击更难命中 (必须在命中判定前应用)
    if action == "heavy":
        hit_chance = max(0.1, hit_chance * 0.7)

    if random.random() > hit_chance:  # nosec B311 —— 游戏骰子，非密码学用途
        result["events"].append(f"{atk_ent['name']}的攻击被{def_ent['name']}闪避")
        result["outcome"] = "loss" if attacker_id == "player" else "win"
        return result

    result["hit"] = True

    # 计算伤害
    base_damage = atk_attrs.get("str", 10) * 1.5 + atk_tier_bonus * 1.5

    # action 加成
    if action == "heavy":
        base_damage *= 1.8
    elif action == "flee":
        result["events"].append(f"{atk_ent['name']}尝试逃跑")
        flee_chance = atk_attrs.get("dex", 10) / (atk_attrs.get("dex", 10) + def_attrs.get("dex", 10))
        if random.random() < flee_chance:  # nosec B311 —— 游戏骰子，非密码学用途
            result["events"].append("逃跑成功!")
            result["fled"] = True
        else:
            result["events"].append("逃跑失败!")
            result["fled"] = False
        return result
    
    # 技能/功法加成 (世界观无关——"功法"可以是内力/法力/科技, 只是名字不同)
    skill_bonus = 1.0
    if skill:
        # skill 格式: {"name": "寒冰箭", "power": 2.0, "mp_cost": 10}
        skill_bonus = skill.get("power", 1.5)
        mp_cost = skill.get("mp_cost", 0)
        if atk_ent.get("mp", 0) >= mp_cost:
            atk_ent["mp"] -= mp_cost
            base_damage *= skill_bonus
            result["events"].append(f"{atk_ent['name']}施展{skill['name']}!")
        else:
            result["events"].append(f"内力不足，无法施展{skill['name']}，改用普通攻击")
    
    # 防御减免
    defense = def_attrs.get("con", 10) * 0.3
    damage = max(1, base_damage - defense)
    damage *= dmg_mult
    
    # 浮动 0.8 ~ 1.2
    damage *= random.uniform(0.8, 1.2)  # nosec B311 —— 游戏骰子，非密码学用途
    
    # 暴击判定
    dex_diff = atk_attrs.get("dex", 10) - def_attrs.get("dex", 10)
    crit_chance = max(0, min(0.3, dex_diff * 0.05))
    if random.random() < crit_chance:  # nosec B311 —— 游戏骰子，非密码学用途
        damage *= 1.5
        result["crit"] = True
    
    damage = max(1, int(damage))
    result["damage"] = damage
    
    # 扣除血量
    def_ent["hp"] = max(0, def_ent.get("hp", 0) - damage)
    result["defender_hp_after"] = def_ent["hp"]
    # 结构化胜负：flow_channel_status 直接读它，不再用中文关键词猜
    if attacker_id == "player":
        result["outcome"] = "win"
    elif defender_id == "player":
        result["outcome"] = "loss"
    else:
        result["outcome"] = "draw"
    
    # 记录事件
    hit_desc = "暴击!" if result["crit"] else "命中"
    result["events"].append(
        f"{atk_ent['name']}{hit_desc}{def_ent['name']}，造成{damage}点伤害 "
        f"(剩余{def_ent['hp']}/{def_ent.get('hp_max', 100)})"
    )
    
    # 检查击杀
    if def_ent["hp"] <= 0:
        # 战利品：击败目标后接管其随身钱财。没有这条，玩家打怪毫无经济回报，
        # 只能坐吃山空（实测 600 回合后 gold=0、买不起药、长期残血）。
        loot = int(def_ent.get("gold", 0) or 0)
        if defender_id != "player" and loot > 0:
            atk_ent["gold"] = int(atk_ent.get("gold", 0) or 0) + loot
            def_ent["gold"] = 0
            result["loot_gold"] = loot
            result["events"].append(f"{atk_ent.get('name', attacker_id)}从{def_ent.get('name', defender_id)}身上取得{loot}钱财")
        if defender_id == "player":
            # 玩家永不真正死亡：气血保底 1，代价是濒死（掉钱 / 心伤 / 留痕）
            _apply_near_death(state, def_ent, result)
        else:
            result["defender_dead"] = True
            result["events"].append(f"{def_ent['name']}被击败了")
    
    return result


def _apply_near_death(state, player, result):
    """濒死保护：玩家的气血归零改判为「重伤退场」——保底 1 点气血，但必须付真实代价。

    为什么这样设计：让命可以随便丢，长局就失去重量；直接 game over 又会打断叙事。
    折中为「永不死亡 + 明确代价」，且代价必须写进状态文件——此前 stress 测试靠直接
    改内存 p['hp']=hp_max 假装复活，状态文件从未变化，属于假修复。
    """
    player["hp"] = 1
    gold = int(player.get("gold", 0) or 0)
    gold_lost = int(gold * 0.30)
    player["gold"] = gold - gold_lost
    player["mind_scars"] = int(player.get("mind_scars", 0) or 0) + 1
    player["near_death_count"] = int(player.get("near_death_count", 0) or 0) + 1
    result["near_death"] = True
    result["near_death_cost"] = {"gold_lost": gold_lost, "mind_scars": 1,
                                 "total": player["near_death_count"]}
    result["defender_hp_after"] = player["hp"]
    result["events"].append(
        f"{player.get('name', '玩家')}气血耗尽，重伤退场："
        f"散落 {gold_lost} 钱财，心伤 +1（第 {player['near_death_count']} 次濒死）")
