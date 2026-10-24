import io

P = 'mcp_server.py'
s = io.open(P, encoding='utf-8').read()

ANCHOR = '''@server.tool()
def status() -> dict:'''

NEW = '''@server.tool()
def playbook_info() -> dict:
    """玩法剧本说明（Chinese: 这一局按什么循环玩、进度看什么、失败怎么算、当前节拍）。
    Playbook: loop type, progress axis, failure mode, current beat, host guide."""

    state = _load()
    pb = state.get("playbook") or playbook_rules.DEFAULT_PLAYBOOK
    out = playbook_rules.summary(state, pb)
    out["catalog"] = playbook_rules.configurable_axes()
    out["quests"] = quest_rules.status(state, state.get("questlines") or [])
    out["quests_total"] = len(state.get("questlines") or [])
    return _read(out)


@server.tool()
def quest_status(include_dormant: bool = False) -> dict:
    """查看事业线（Chinese: 当前在追的线、做到哪一幕、下一步目标、有没有到期）。
    Questline status: visible quests, current stage, objectives, deadlines."""

    state = _load()
    quests = state.get("questlines") or []
    rows = quest_rules.status(state, quests, only_active=not include_dormant)
    return _read({
        "quests": rows,
        "total": len(quests),
        "visible": quest_rules.visible_count(state, quests),
        "hint": "只显示已浮现的事业线；dormant 的线由 visibility 谓词控制何时出现。",
    })


@server.tool()
def quest_advance(quest: str, stage: str, tick_note: str = "") -> dict:
    """手动完成一幕（Chinese: 当目标无法由数值推断时用，例如"把信交给林小姐"）。
    引擎仍负责判定下一幕的门禁；这个工具只记录"这一幕确实做到了"。
    Mark a quest stage as completed (for goals the engine cannot infer)."""

    state = _load()
    _seed_rng(state)
    quests = state.get("questlines") or []
    if not quests:
        raise ValueError("本局没有配置事业线（设定包 questlines 字段为空）")
    before = {r["id"]: (r["status"], r["stage"]) for r in quest_rules.status(state, quests, False)}
    row = quest_rules.complete_stage(state, quests, quest, stage,
                                     tick=int(state.get("tick", 0) or 0))
    changes = quest_rules.advance(state, quests, tick=int(state.get("tick", 0) or 0))
    log_event(state, "quest", "手动记录：事业线「%s」完成 %s%s"
              % (quest, stage, ("（" + tick_note + "）") if tick_note else ""),
              quest=quest, stage=stage)
    for ch in changes:
        if ch.get("change") == "done":
            _milestone(state, "事业线", "完成「%s」" % ch.get("quest"))
    after = {r["id"]: (r["status"], r["stage"]) for r in quest_rules.status(state, quests, False)}
    return _finish(state, {"quest": quest, "stage": stage, "row": row,
                           "changes": changes, "before": before, "after": after,
                           "visible": quest_rules.status(state, quests)})


@server.tool()
def lore_lookup(text: str, tick_note: str = "") -> dict:
    """查这一刻会触发哪些世界书条目（Chinese: 调试/解释用——玩家问"为什么提到这个"时能给出依据）。
    Which lorebook entries would fire for this text right now (with runtime gates)."""

    state = _load()
    res = _trigger_lore_state(state, text)
    log_event(state, "system", "世界书查询：%s" % text[:40])
    return _finish(state, {
        "matched": [{"comment": e.get("comment"), "depth": e.get("_depth"),
                     "reason": e.get("_reason"), "keys": e.get("keys")}
                    for e in res["entries"]],
        "by_depth": res["by_depth"],
        "skipped": res["skipped"],
        "recursion_cap": res["recursion_cap"],
        "scan_depth": res["scan_depth"],
        "hint": "sticky 条目会持续保留若干回合；cooldown 内的条目不会重复触发。",
    })


@server.tool()
def failure_tick(amount: int = 1, reason: str = "") -> dict:
    """推进"失败钟"（Chinese: 只有 playbook.failure.mode == clock 时生效；
    用于"再拖两回合就来不及了"这类压力，而不是直接扣血）。
    Advance the failure clock (only when the playbook uses clock mode)."""

    state = _load()
    pb = state.get("playbook") or playbook_rules.DEFAULT_PLAYBOOK
    if pb["failure"].get("mode") != "clock":
        raise ValueError("本局失败模式是 %s，不是 clock；改 playbook.failure.mode 才可用"
                         % pb["failure"].get("mode"))
    before = dict((state.get("failure_clock") or {}))
    after = playbook_rules.tick_failure(state, pb, amount=int(amount), reason=reason)
    if after != playbook_rules.failure_state(state, pb):
        pass
    if after.get("failed") and before.get("filled", 0) < after.get("value", 0):
        _milestone(state, "败局", "失败钟填满：%s" % (reason or "局势失控"))
    return _finish(state, {"failure": after, "playbook": playbook_rules.summary(state, pb)})


@server.tool()
def status() -> dict:'''

assert s.count(ANCHOR) == 1
s = s.replace(ANCHOR, NEW, 1)

# extend status payload with playbook + quests
old = '''        "milestones": ["第%d回合·%s" % (m.get("tick", 0), m.get("desc", ""))
                       for m in state.get("milestones", [])[-6:]],
    }),'''
new = '''        "milestones": ["第%d回合·%s" % (m.get("tick", 0), m.get("desc", ""))
                       for m in state.get("milestones", [])[-6:]],
        "playbook": playbook_rules.summary(state, state.get("playbook") or {}),
        "quests": quest_rules.status(state, state.get("questlines") or []),
    }),'''
assert s.count(old) == 1
s = s.replace(old, new, 1)

# world_schema: register new tools
old = '''            "pending_actions": "取走面板「行动队列」里玩家排的行动（唯一双向通道；状态仍只由 MCP 写）",'''
new = '''            "pending_actions": "取走面板「行动队列」里玩家排的行动（唯一双向通道；状态仍只由 MCP 写）",
            "playbook_info": "这一局的玩法剧本（循环/进度/失败/节拍/宿主指南）",
            "quest_status": "事业线进度（当前幕、目标、期限）",
            "quest_advance": "手动完成一幕（数值推断不出的目标才用它）",
            "lore_lookup": "查这一刻会触发哪些世界书条目（含递归/sticky/cooldown 原因）",
            "failure_tick": "推进失败钟（仅 clock 模式）",'''
assert s.count(old) == 1
s = s.replace(old, new, 1)

io.open(P, 'w', encoding='utf-8').write(s)
print('5 new tools added')
