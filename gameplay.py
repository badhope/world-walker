"""Scene-driven gameplay contract.

This is the layer that replaces "tick every turn" with "a scene with a
question, a pressure, a cost, and a consequence".  It is deliberately
world-agnostic: every setting bundle can carry its own acts, set pieces,
clocks and fronts, while the engine owns the same deterministic state.

State shape::

    state["gameplay"] = {
        "version": 1,
        "acts": [...],
        "clocks": [...],
        "fronts": [...],
        "choice_policy": {...},
        "progression": [...],
        "session": {...},
    }
    state["scene"] = {open scene or absent}
    state["scene_log"] = [closed scenes]

The model is a GM, not the author: it opens a scene, plays the NPCs, then
resolves the scene with an outcome and a cost.  The engine never advances a
calendar just because a message was sent.
"""

from __future__ import annotations

import copy
import re
from datetime import datetime, timezone

from game_engine.state_schema import load_state, transact_state

OUTCOMES = ("yes", "yes-but", "no-and")
MAX_ACTS = 6
MAX_SET_PIECES = 8
MAX_CLOCKS = 8
MAX_FRONTS = 8
MAX_SCENES = 100

DEFAULT_CHOICE_POLICY = {
    "min": 2,
    "max": 3,
    "free_input": True,
    "must_cost": True,
    "no_advice": True,
    "no_consequence_preview": True,
}

DEFAULT_GAMEPLAY = {
    "version": 1,
    "acts": [
        {
            "id": "act1",
            "title": "进入局面",
            "question": "你愿意拿什么，换一个留下来的理由？",
            "set_pieces": [
                "第一场：一个不能全拿的 offer",
                "第二场：一个不该先到的人",
                "第三场：一次必须付代价的检查",
            ],
        },
        {
            "id": "act2",
            "title": "代价显现",
            "question": "你已经开始失去，接下来还要不要继续？",
            "set_pieces": [
                "第一场：盟友的要价",
                "第二场：一个已经太晚的线索",
                "第三场：必须选择一边的夜晚",
            ],
        },
        {
            "id": "act3",
            "title": "做出选择",
            "question": "真相和活命，你只能带走一个时，带哪个？",
            "set_pieces": [
                "第一场：门前的最后条件",
                "第二场：把谁留在外面",
                "第三场：结束这一局的答案",
            ],
        },
    ],
    "clocks": [
        {"name": "局势恶化", "segments": 6, "filled": 0,
         "on_full": "局势越过临界点，世界替你做出一个坏决定。"},
    ],
    "fronts": [],
    "choice_policy": copy.deepcopy(DEFAULT_CHOICE_POLICY),
    "progression": [
        {"id": "knowledge", "label": "知道的东西", "max": 8,
         "note": "线索不是收藏品；知道得越多，越有人想让你闭嘴。"},
    ],
    "session": {"length": "3-5 次", "scenes": "每次 4-6 场", "ending": "由选择决定"},
}


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _text(value, limit=160, default=""):
    text = str(value or "").strip()
    return text[:limit] if text else default


def _int(value, default, lo, hi):
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = default
    return max(lo, min(hi, n))


def _list(value, limit=8):
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple)):
        return []
    out = []
    seen = set()
    for item in value:
        text = _text(item, 180)
        if text and text not in seen:
            out.append(text)
            seen.add(text)
        if len(out) >= limit:
            break
    return out


def _clock(raw):
    src = raw if isinstance(raw, dict) else {}
    segments = _int(src.get("segments"), 6, 2, 20)
    return {
        "name": _text(src.get("name"), 40, "局势恶化"),
        "segments": segments,
        "filled": _int(src.get("filled"), 0, 0, segments),
        "on_full": _text(src.get("on_full"), 200,
                         "钟满了：这件事不再等玩家，世界先动手。"),
        "visible": bool(src.get("visible", True)),
    }


def _front(raw):
    src = raw if isinstance(raw, dict) else {"name": raw}
    return {
        "name": _text(src.get("name"), 40, "未命名前线"),
        "want": _text(src.get("want"), 160, "它想要的东西还没写清。"),
        "move": _text(src.get("move"), 160, "下次它出现时，会先做一件让玩家难受的事。"),
        "visible": bool(src.get("visible", False)),
    }


def _act(raw, index):
    src = raw if isinstance(raw, dict) else {}
    aid = _text(src.get("id"), 24, "act%d" % (index + 1))
    return {
        "id": aid,
        "title": _text(src.get("title"), 40, "第 %d 幕" % (index + 1)),
        "question": _text(src.get("question"), 160, "你愿意拿什么，换什么？"),
        "set_pieces": _list(src.get("set_pieces"), MAX_SET_PIECES) or
                     ["第一场：一个不能全拿的 offer"],
    }


def normalize(raw=None, narrative=None, bundle=None):
    """Return a complete gameplay contract. Unknown fields fall back, never raise."""
    src = raw if isinstance(raw, dict) else {}
    nar = narrative if isinstance(narrative, dict) else {}
    b = bundle if isinstance(bundle, dict) else {}

    acts = []
    for i, row in enumerate(src.get("acts") or []):
        if i >= MAX_ACTS:
            break
        acts.append(_act(row, i))
    if not acts:
        # Derive a spine from questlines if the setting has one; otherwise use
        # the genre-agnostic three-act default.  This is a skeleton, not a plot.
        qs = b.get("questlines") or []
        if qs:
            for i, q in enumerate(qs[:3]):
                if not isinstance(q, dict):
                    continue
                acts.append(_act({
                    "id": "act%d" % (i + 1),
                    "title": _text(q.get("title"), 40, "第 %d 幕" % (i + 1)),
                    "question": _text(q.get("summary"), 160, "你愿意拿什么，换什么？"),
                    "set_pieces": [
                        "第一场：%s 的开价" % _text(q.get("title"), 40, "这件事"),
                        "第二场：有人先到一步",
                        "第三场：必须付代价的选择",
                    ],
                }, i))
        # A bundle with one or two questlines still needs a three-act spine:
        # the missing acts are structural, not content the setting forgot.
        while 0 < len(acts) < 3:
            acts.append(copy.deepcopy(DEFAULT_GAMEPLAY["acts"][len(acts)]))
    if not acts:
        acts = copy.deepcopy(DEFAULT_GAMEPLAY["acts"])

    clocks = []
    for row in src.get("clocks") or []:
        if len(clocks) >= MAX_CLOCKS:
            break
        clocks.append(_clock(row))
    if not clocks:
        for row in nar.get("clocks") or []:
            if isinstance(row, dict):
                clocks.append(_clock(row))
    if not clocks:
        clocks = [copy.deepcopy(DEFAULT_GAMEPLAY["clocks"][0])]

    fronts = []
    for row in src.get("fronts") or []:
        if len(fronts) >= MAX_FRONTS:
            break
        fronts.append(_front(row))
    if not fronts:
        for row in nar.get("fronts") or []:
            if len(fronts) >= MAX_FRONTS:
                break
            fronts.append(_front(row))

    policy = copy.deepcopy(DEFAULT_CHOICE_POLICY)
    if isinstance(src.get("choice_policy"), dict):
        for key in policy:
            if key in src["choice_policy"]:
                policy[key] = src["choice_policy"][key]
        policy["min"] = _int(policy.get("min"), 2, 2, 3)
        policy["max"] = _int(policy.get("max"), 3, policy["min"], 4)
        policy["must_cost"] = bool(policy.get("must_cost", True))

    progression = []
    for row in src.get("progression") or []:
        if not isinstance(row, dict):
            continue
        progression.append({
            "id": _text(row.get("id"), 24, "track%d" % (len(progression) + 1)),
            "label": _text(row.get("label"), 40, "进度"),
            "max": _int(row.get("max"), 5, 1, 200),
            "note": _text(row.get("note"), 160, ""),
        })
    if not progression:
        progression = copy.deepcopy(DEFAULT_GAMEPLAY["progression"])

    session = copy.deepcopy(DEFAULT_GAMEPLAY["session"])
    if isinstance(src.get("session"), dict):
        for key in session:
            if key in src["session"]:
                session[key] = _text(src["session"][key], 60, session[key])

    return {
        "version": 1,
        "acts": acts,
        "clocks": clocks,
        "fronts": fronts,
        "choice_policy": policy,
        "progression": progression,
        "session": session,
        "updated_at": _now(),
    }


def attach(state_path, raw=None, narrative=None, bundle=None):
    """Persist the contract into the save.  Safe to call after the state exists."""
    state = load_state(state_path)
    gp = normalize(raw if raw is not None else state.get("gameplay"),
                   narrative=narrative if narrative is not None else state.get("narrative"),
                   bundle=bundle if bundle is not None else state)
    def edit(s):
        s["gameplay"] = gp
        s.setdefault("scene", None)
        s.setdefault("scene_log", [])
        s.setdefault("scene_count", 0)
    transact_state(edit, state_path, allow_create=False)
    return gp


def _state_gp(state):
    raw = state.get("gameplay") if isinstance(state.get("gameplay"), dict) else {}
    return normalize(raw, narrative=state.get("narrative"), bundle=state)


def _current_act(gp, state):
    idx = int(state.get("scene_count", 0) or 0) // 5
    idx = max(0, min(idx, len(gp["acts"]) - 1))
    return gp["acts"][idx]


def _next_set_piece(gp, state):
    act = _current_act(gp, state)
    pieces = act.get("set_pieces") or [act.get("title") or "下一场"]
    idx = int(state.get("scene_count", 0) or 0) % len(pieces)
    return act, str(pieces[idx])


def suggested_scene(state):
    """A GM-facing scene skeleton. It is not prose; it is a contract."""
    gp = _state_gp(state)
    act, piece = _next_set_piece(gp, state)
    return {
        "act_id": act["id"],
        "act_title": act["title"],
        "act_question": act["question"],
        "title": piece,
        "goal": "玩家在这一场要拿到/守住/放弃什么。",
        "obstacle": "谁或什么在阻止；它有它自己的目的。",
        "pressure": "哪一只钟会因拖延/失败而前进。",
        "clue": "这一场最多只给一条新信息；不要一次讲完。",
        "cost": "无论成败，玩家都要失去一点东西。",
        "outcome_hint": "yes / yes-but / no-and",
    }


def _clocks_view(gp):
    out = []
    for c in gp.get("clocks") or []:
        out.append({
            "name": c["name"],
            "segments": c["segments"],
            "filled": c["filled"],
            "label": "%s %d/%d" % (c["name"], c["filled"], c["segments"]),
            "on_full": c["on_full"],
            "visible": c.get("visible", True),
        })
    return out


def brief(state):
    """GM-facing scene contract + clocks + fronts + journal."""
    gp = _state_gp(state)
    scene = state.get("scene") if isinstance(state.get("scene"), dict) else None
    if scene:
        scene = dict(scene)
    else:
        scene = suggested_scene(state)
    act = _current_act(gp, state)
    return {
        "gameplay_version": gp["version"],
        "act": {"id": act["id"], "title": act["title"], "question": act["question"]},
        "scene": scene,
        "clocks": _clocks_view(gp),
        "fronts": [dict(f) for f in gp.get("fronts") or []],
        "choice_policy": dict(gp.get("choice_policy") or {}),
        "progression": list(gp.get("progression") or []),
        "journal": journal(state),
        "instruction": "本回合只演这一场。先给一个具体压力，再让玩家做有代价的选择；"
                       "结尾用 campaign(action='resolve', outcome=yes/yes-but/no-and, cost=...)。",
    }


def journal(state):
    """Player-facing journal.  Hidden fronts are not included."""
    gp = _state_gp(state)
    player = (state.get("entities") or {}).get("player") or {}
    quests = []
    for q in (state.get("quests") or {}).values():
        if isinstance(q, dict) and q.get("status") == "active":
            quests.append({
                "title": q.get("title") or q.get("id") or "未命名线",
                "stage": q.get("stage_title") or q.get("stage") or "",
                "objective": (q.get("objectives") or [""])[0] if q.get("objectives") else "",
            })
    facts = []
    for fact in ((state.get("context") or {}).get("facts") or [])[-8:]:
        if isinstance(fact, dict) and fact.get("status") == "open":
            facts.append(_text(fact.get("text"), 160))
    scenes = []
    for row in (state.get("scene_log") or [])[-3:]:
        if isinstance(row, dict):
            scenes.append({
                "title": row.get("title", ""),
                "outcome": row.get("outcome", ""),
                "cost": row.get("cost", ""),
            })
    clocks = [c for c in _clocks_view(gp) if c.get("visible", True)]
    return {
        "day": (state.get("clock") or {}).get("day"),
        "location": player.get("location", ""),
        "hp": player.get("hp", 0),
        "hp_max": player.get("hp_max", 0),
        "gold": player.get("gold", 0),
        "quests": quests,
        "facts": facts,
        "clocks": [{"name": c["name"], "label": c["label"]} for c in clocks],
        "recent_scenes": scenes,
        "act": _current_act(gp, state)["title"],
    }


def open_scene(state_path, title="", goal="", obstacle="", pressure="", clue="",
               cost="", act_id="", choices=None):
    """Open the current scene.  Replaces an already-open scene only explicitly."""
    state = load_state(state_path)
    gp = _state_gp(state)
    current = state.get("scene") if isinstance(state.get("scene"), dict) else None
    if current and current.get("status") == "open":
        raise ValueError("已经有一场没结算；先 campaign(action='resolve')，不要叠场景")
    act = _current_act(gp, state)
    if act_id:
        act = next((a for a in gp["acts"] if a["id"] == act_id), act)
    if not title:
        act, title = _next_set_piece(gp, state)
    scene = {
        "id": "scene-%d" % (int(state.get("scene_count", 0) or 0) + 1),
        "act_id": act["id"],
        "act_title": act["title"],
        "title": _text(title, 80, "未命名场景"),
        "goal": _text(goal, 200, "玩家在这一场要做出一个选择。"),
        "obstacle": _text(obstacle, 200, "有人不愿意让玩家顺利做到。"),
        "pressure": _text(pressure, 200, "拖下去，某只钟会往前走。"),
        "clue": _text(clue, 200, "这一场最多只给一条新信息。"),
        "cost": _text(cost, 200, "无论成败，玩家都要失去一点东西。"),
        "choices": [_text(c, 120) for c in (choices or [])][:3],
        "status": "open",
        "opened_at": _now(),
        "opened_scene_count": int(state.get("scene_count", 0) or 0),
    }
    def edit(s):
        s["gameplay"] = gp
        s["scene"] = scene
    transact_state(edit, state_path, allow_create=False)
    return scene


def resolve_scene(state_path, outcome, note="", cost="", clocks=None, next_scene=None):
    """Close the current scene.  No calendar tick, no automatic world evolution."""
    if outcome not in OUTCOMES:
        raise ValueError("outcome 只能是 yes / yes-but / no-and")
    state = load_state(state_path)
    scene = state.get("scene") if isinstance(state.get("scene"), dict) else None
    if not scene or scene.get("status") != "open":
        raise ValueError("当前没有可结算的场景；先 campaign(action='open')")
    gp = _state_gp(state)
    closed = dict(scene)
    closed["status"] = "closed"
    closed["outcome"] = outcome
    closed["note"] = _text(note, 300, "")
    closed["cost"] = _text(cost, 200, closed.get("cost", ""))
    closed["closed_at"] = _now()
    clock_rows = list(clocks or [])
    # A plain failure must cost the player something even if the GM forgot to
    # name a clock: the first unresolved pressure moves one segment.
    if outcome == "no-and" and not clock_rows:
        for c in gp.get("clocks") or []:
            if c["filled"] < c["segments"]:
                clock_rows.append({"name": c["name"], "delta": 1})
                break
    changed_clocks = []
    for row in clock_rows:
        if not isinstance(row, dict):
            continue
        name = _text(row.get("name"), 40)
        delta = _int(row.get("delta"), 0, -20, 20)
        for c in gp.get("clocks") or []:
            if c["name"] == name:
                c["filled"] = max(0, min(c["segments"], c["filled"] + delta))
                changed_clocks.append({"name": name, "filled": c["filled"], "segments": c["segments"]})
                break
    def edit(s):
        s["gameplay"] = gp
        s["scene"] = next_scene if isinstance(next_scene, dict) else None
        s["scene_log"] = (s.get("scene_log") or [])[-(MAX_SCENES - 1):] + [closed]
        s["scene_count"] = int(s.get("scene_count", 0) or 0) + 1
        s.setdefault("world_flags", [])
        flag = "场景:%s" % closed.get("title", "")
        if flag not in s["world_flags"]:
            s["world_flags"].append(flag)
        s.setdefault("event_log", []).append({
            "tick": int(s.get("tick", 0) or 0),
            "type": "scene",
            "desc": "%s：%s%s" % (
                closed.get("title", "场景"),
                closed.get("outcome", ""),
                ("（%s）" % closed.get("cost")) if closed.get("cost") else "",
            ),
        })
        for c in gp.get("clocks") or []:
            if c["filled"] >= c["segments"]:
                full = "钟满:%s" % c["name"]
                if full not in s["world_flags"]:
                    s["world_flags"].append(full)
    transact_state(edit, state_path, allow_create=False)
    return {"scene": closed, "clocks": changed_clocks,
            "scene_count": int(state.get("scene_count", 0) or 0) + 1,
            "journal": journal(load_state(state_path))}


def adjust_clock(state_path, name, delta=1, reason=""):
    state = load_state(state_path)
    gp = _state_gp(state)
    target = None
    for c in gp.get("clocks") or []:
        if c["name"] == _text(name, 40):
            target = c
            break
    if target is None:
        raise ValueError("没有这只钟：%s" % name)
    target["filled"] = max(0, min(target["segments"], target["filled"] + int(delta)))
    full = target["filled"] >= target["segments"]
    def edit(s):
        s["gameplay"] = gp
        if full:
            flag = "钟满:%s" % target["name"]
            s.setdefault("world_flags", [])
            if flag not in s["world_flags"]:
                s["world_flags"].append(flag)
    transact_state(edit, state_path, allow_create=False)
    return {"clock": _clock(target), "full": full, "reason": _text(reason, 200, "")}
