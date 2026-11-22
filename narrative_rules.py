"""Narrative profile (session zero) and turn-quality checks.

The engine owns the truth; this module owns the *contract* between the player
and the GM: what kind of game this is, how lethal it is, what must not happen,
and what the GM should check before sending a turn.

It is deliberately small and dependency-free.  The profile lives inside the
save file under ``narrative`` so a game remains portable and a reload keeps the
same tone, boundaries and opening card.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from game_engine.state_schema import load_state, transact_state
from game_engine.rules import modes as mode_rules

GENRES = [
    "悬疑", "奇幻", "武侠仙侠", "科幻", "都市", "历史",
    "恋爱", "恐怖", "生存", "日常",
]
PLAYS = [
    "探索解谜", "生存压力", "权谋经营", "关系情感",
    "战斗成长", "调查恐怖", "轻松日常",
]
TONES = ["明亮", "阴郁", "热血", "克制", "荒诞"]
DIFFICULTIES = ["轻松", "标准", "硬核", "铁人"]
ROLES = ["random", "custom", "preset"]
BOUNDARIES = ["不写玩家内心决定", "不出现现代科技", "不写血腥细节", "不写恋爱线", "不无故杀死 NPC"]

WORLD_LINES = {
    "悬疑": "一座被雾、旧案和沉默包住的城市。",
    "奇幻": "边境之地，委托与旧王朝的裂缝同时出现。",
    "武侠仙侠": "江湖上有人立规矩，也有人不打算守。",
    "科幻": "人类已经离开地表，但有些东西没走。",
    "都市": "这座城白天很正常，晚上不是。",
    "历史": "王朝末年，所有人都在给自己找退路。",
    "恋爱": "关系比事件更难处理，你说的每句话都留痕。",
    "恐怖": "有些地方不该去，但你已经听见了。",
    "生存": "资源只够三天，外面还有别的人。",
    "日常": "日子很慢，但每个人的心事都不小。",
}

PLAY_PRESSURES = {
    "探索解谜": "有一条线索已经被人先一步动过。",
    "生存压力": "补给、时间和信任同时不够。",
    "权谋经营": "每个人都在算账，包括你的盟友。",
    "关系情感": "有人对你说真话，有人只说一半。",
    "战斗成长": "你能赢，但赢的代价会留在身上。",
    "调查恐怖": "你知道得越多，越不安全。",
    "轻松日常": "没有大危机，只有一地小事。",
}

GENRE_QUESTIONS = {
    "悬疑": "这件事里，谁最不想让你查下去？",
    "奇幻": "旧王朝留下的裂缝，会先吞掉谁？",
    "武侠仙侠": "规矩和活命，你只能选一个时选哪个？",
    "科幻": "离开地表的人，还算不算人？",
    "都市": "这座城晚上发生的事，白天为什么没人提？",
    "历史": "王朝倒下时，你想保住什么？",
    "恋爱": "你愿意为一个人做到哪一步？",
    "恐怖": "你听见的那个声音，真的是从外面来的吗？",
    "生存": "只剩三天时，你还会把水给别人吗？",
    "日常": "一件小事，能不能改变一个人的一整年？",
}

TEMPLATE_BY_GENRE = {
    "奇幻": "jrpg",
    "悬疑": "mystery",
    "恐怖": "mystery",
    "生存": "survival",
    "都市": "management",
    "历史": "management",
    "恋爱": "narrative",
    "日常": "cozy",
    "科幻": "immersive",
    "武侠仙侠": "tabletop",
}

TEMPLATE_WORLD_NAMES = {
    "jrpg": "艾瑟兰",
    "mystery": "雾港",
    "management": "临川老街",
    "survival": "灰区",
    "narrative": "长夏",
    "cozy": "雾溪村",
    "tabletop": "灰岩堡",
    "immersive": "科尔沃城",
}

RANDOM_NAMES = {
    "悬疑": ["沈默", "陆见", "周砚", "苏晚"],
    "奇幻": ["艾琳", "凯尔", "洛恩", "米拉"],
    "武侠仙侠": ["韩照", "沈孤", "顾青", "林晚"],
    "科幻": ["零", "阿岚", "K", "诺拉"],
    "都市": ["陈默", "林一", "许安", "周可"],
    "历史": ["李昭", "裴行", "沈度", "崔宁"],
    "恋爱": ["夏至", "程野", "林知", "沈星"],
    "恐怖": ["闻声", "白夜", "顾怕", "陈默"],
    "生存": ["阿灰", "老七", "小满", "路平"],
    "日常": ["林小满", "陈午", "阿禾", "周宁"],
}


def random_name(genre):
    import random
    pool = RANDOM_NAMES.get(genre) or ["无名", "阿行", "小满"]
    return random.choice(pool)

SUGGESTED_FRONTS = {
    "探索解谜": ["有人先一步动过现场", "一个证人正在改口", "线索指向不该有人的地方"],
    "生存压力": ["补给点正在被截断", "夜里出现了不属于这里的脚印", "同伴开始藏东西"],
    "权谋经营": ["盟友在给自己留后路", "账本上有一笔对不上", "上头派了一个不该来的人"],
    "关系情感": ["有人说了半句真话", "旧账被重新提起", "一个选择会让两个人同时失望"],
    "战斗成长": ["对手在等你先出手", "胜利的代价会落到旁人身上", "有人想借你的刀"],
    "调查恐怖": ["你知道得太多", "现场少了一样东西", "有人希望你继续查"],
    "轻松日常": ["一件小事反复出现", "有人不好意思开口", "旧物里藏着一段关系"],
}


def _clean_text(value, limit=240, default=""):
    text = str(value or "").strip()
    return text[:limit] if text else default


def _clean_list(value, allowed=None, limit=8):
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple)):
        return []
    out = []
    seen = set()
    for item in value:
        text = _clean_text(item, 60)
        if not text or text in seen:
            continue
        if allowed is not None and text not in allowed:
            continue
        seen.add(text)
        out.append(text)
        if len(out) >= limit:
            break
    return out


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize(raw):
    """Return a stable narrative profile. Unknown values fall back, never raise."""
    src = raw if isinstance(raw, dict) else {}
    genre = _clean_text(src.get("genre"), 16, "悬疑")
    if genre not in GENRES:
        genre = "悬疑"
    play = _clean_text(src.get("play"), 16, "探索解谜")
    if play not in PLAYS:
        play = "探索解谜"
    tone = _clean_list(src.get("tone"), TONES, 3) or ["克制"]
    difficulty = _clean_text(src.get("difficulty"), 8, "标准")
    if difficulty not in DIFFICULTIES:
        difficulty = "标准"
    mode_raw = _clean_text(src.get("mode"), 12)
    if mode_raw:
        mode = mode_rules.normalize(mode_raw)
        difficulty = mode_rules.MODE_SPECS[mode]["difficulty"]
    else:
        mode = mode_rules.normalize(difficulty)
    role = _clean_text(src.get("role"), 12, "random")
    if role not in ROLES:
        role = "random"
    boundaries = _clean_list(src.get("boundaries"), None, 6)
    name = _clean_text(src.get("player_name") or src.get("name"), 24)
    world_kind = _clean_text(src.get("world_kind"), 12)
    world_id = _clean_text(src.get("world_id"), 240)
    world_name = _clean_text(src.get("world_name"), 60)
    style = _clean_text(src.get("style"), 200)
    prefab = _clean_text(src.get("prefab"), 40)
    skill_ids = _clean_list(src.get("skill_ids"), None, 8)
    central_question = _clean_text(
        src.get("central_question"), 160, GENRE_QUESTIONS.get(genre, ""))
    fronts = _clean_list(src.get("fronts"), None, 5) or list(SUGGESTED_FRONTS.get(play, []))
    clocks = src.get("clocks") if isinstance(src.get("clocks"), list) else []
    clean_clocks = []
    for clock in clocks[:4]:
        if not isinstance(clock, dict):
            continue
        clean_clocks.append({
            "name": _clean_text(clock.get("name"), 40, "局势恶化"),
            "segments": max(2, min(12, int(clock.get("segments", 6) or 6))),
            "filled": max(0, min(12, int(clock.get("filled", 0) or 0))),
        })
    if not clean_clocks:
        clean_clocks = [{"name": "局势恶化", "segments": 6, "filled": 0}]
    hints = _clean_list(src.get("hints"), None, 3)
    if not hints:
        hints = [
            "有人比你先到过现场。",
            "一个本该沉默的人，最近话很多。",
            "你带着的东西，可能不是你的。",
        ]
    return {
        "genre": genre,
        "play": play,
        "tone": tone,
        "difficulty": difficulty,
        "mode": mode,
        "mode_label": mode_rules.MODE_SPECS[mode]["label"],
        "role": role,
        "player_name": name,
        "world_kind": world_kind,
        "world_id": world_id,
        "world_name": world_name,
        "boundaries": boundaries,
        "central_question": central_question,
        "fronts": fronts,
        "clocks": clean_clocks,
        "hints": hints,
        "style": style,
        "prefab": prefab,
        "skill_ids": skill_ids,
        "updated_at": _now(),
    }


def preview(raw, world_name="", world_desc="", player_name=""):
    """A player-facing card.  No hidden fronts, no spoilers."""
    cfg = normalize(raw)
    name = _clean_text(player_name or cfg.get("player_name"), 24)
    default_world = TEMPLATE_WORLD_NAMES.get(template_for(cfg), "未命名世界")
    world = _clean_text(world_name or cfg.get("world_name"), 60, default_world)
    world_line = _clean_text(world_desc, 160, WORLD_LINES.get(cfg["genre"], ""))
    if not name and cfg.get("role") == "random":
        player_line = "你会随机得到一个名字；这个世界会先给你一个身份。"
    elif not name:
        player_line = "你还没有名字；这个世界会先给你一个身份。"
    elif cfg.get("role") == "preset":
        player_line = "你以「%s」的身份进入这个局面。" % name
    else:
        player_line = "你是%s；过去不重要，重要的是你接下来做什么。" % name
    pressure = PLAY_PRESSURES.get(cfg["play"], "有一件事正在变坏。")
    mode_spec = mode_rules.summary(cfg.get("mode"))
    rules = "模式：%s（世界强度 %s）· 难度：%s · 基调：%s · 死亡：%s" % (
        mode_spec["label"], mode_spec["world_intensity"], cfg["difficulty"],
        " / ".join(cfg["tone"]),
        "不可逆" if mode_spec["id"] == "hardcore" else "有代价",
    )
    opening = "你站在%s。%s\n\n%s\n\n%s\n\n%s\n\n你可以先看一眼、问一句，或者直接说出你要做什么。" % (
        world, world_line, player_line, pressure, rules,
    )
    return {
        "ok": True,
        "headline": "《%s》· %s" % (world, cfg["genre"]),
        "genre": cfg["genre"],
        "play": cfg["play"],
        "tone": cfg["tone"],
        "difficulty": cfg["difficulty"],
        "mode": cfg["mode"],
        "mode_label": cfg["mode_label"],
        "mode_spec": mode_rules.summary(cfg["mode"]),
        "boundaries": cfg["boundaries"],
        "world_line": world_line,
        "player_line": player_line,
        "pressure_line": pressure,
        "rules_line": rules,
        "hints": cfg["hints"],
        "central_question": cfg["central_question"],
        "opening": opening,
        "narrative": cfg,
    }


def template_for(cfg):
    """Pick a skeleton when the player did not choose a world explicitly."""
    return TEMPLATE_BY_GENRE.get((cfg or {}).get("genre") or "", "tabletop")


def template_overrides(cfg):
    """Small, safe overrides: tags and a visible sheet, never the plot."""
    cfg = normalize(cfg)
    return {
        "game": {
            "tags": [cfg["genre"], cfg["play"], cfg["mode_label"]],
            "sheet": {
                "类型": cfg["genre"],
                "玩法": cfg["play"],
                "模式": cfg["mode_label"],
                "难度": cfg["difficulty"],
                "核心问题": cfg["central_question"],
            },
        },
    }


def attach(state_path, raw, world_name="", world_desc="", player_name=""):
    """Persist the profile into the save after the skeleton has been built."""
    cfg = normalize(raw)
    state = load_state(state_path)
    world = state.get("world_info") or {}
    player = (state.get("entities") or {}).get("player") or {}
    world_name = world_name or str(world.get("name") or "")
    world_desc = world_desc or str(world.get("location_desc") or "")
    player_name = player_name or str(player.get("name") or "")

    card = preview(cfg, world_name=world_name, world_desc=world_desc,
                   player_name=player_name)
    cfg["world_name"] = world_name
    cfg["player_name"] = player_name
    prologue = [str(x).strip() for x in (world.get("prologue") or []) if str(x).strip()]
    opening_actions = [str(x).strip() for x in (world.get("opening_actions") or []) if str(x).strip()]
    world_line = str(world.get("brief_line") or card["world_line"])
    cfg["brief"] = {
        "headline": card["headline"],
        "world_line": world_line,
        "player_line": card["player_line"],
        "pressure_line": card["pressure_line"],
        "rules_line": card["rules_line"],
        "hints": card["hints"],
        "central_question": card["central_question"],
        "prologue": prologue[:8],
        "opening_actions": opening_actions[:4],
    }
    cfg["prologue"] = prologue[:8]
    cfg["opening_actions"] = opening_actions[:4]
    cfg["opening"] = ("\n\n".join(prologue) + "\n\n" if prologue else "") + card["opening"]

    def edit(state):
        state["narrative"] = cfg

    transact_state(edit, state_path, allow_create=False)
    # The gameplay contract is attached in the same breath as the narrative
    # profile.  A game may have no authored gameplay block; normalize() still
    # gives it a three-act skeleton rather than a blank screen.
    try:
        from game_engine import gameplay as gameplay_rules
        gameplay_rules.attach(state_path, raw=state.get("gameplay"),
                              narrative=cfg, bundle=state)
    except Exception:
        pass
    return cfg


def _player_gameplay(state):
    """Player-facing slice of the scene contract: act, scene, clocks, journal."""
    try:
        from game_engine import gameplay as gameplay_rules
        brief = gameplay_rules.brief(state)
        return {
            "act": brief.get("act") or {},
            "scene": {k: (brief.get("scene") or {}).get(k) for k in
                      ("title", "goal", "obstacle", "pressure", "clue", "cost")},
            "journal": brief.get("journal") or {},
        }
    except Exception:
        return {}


def player_narrative(state):
    """What the player may see: no hidden fronts, no GM-only notes."""
    raw = state.get("narrative") if isinstance(state.get("narrative"), dict) else {}
    if not raw:
        return {}
    cfg = normalize(raw)
    clocks = []
    for clock in cfg["clocks"]:
        clocks.append({
            "name": clock["name"],
            "segments": clock["segments"],
            "filled": clock["filled"],
            "label": "%s %s/%s" % (clock["name"], clock["filled"], clock["segments"]),
        })
    brief = raw.get("brief") if isinstance(raw.get("brief"), dict) else {}
    if not brief:
        brief = {
            "headline": "《%s》" % (cfg.get("world_name") or "这一局"),
            "world_line": "",
            "player_line": "",
            "pressure_line": PLAY_PRESSURES.get(cfg["play"], ""),
            "rules_line": "难度：%s" % cfg["difficulty"],
            "hints": cfg["hints"],
            "central_question": cfg["central_question"],
        }
    return {
        "genre": cfg["genre"],
        "play": cfg["play"],
        "tone": cfg["tone"],
        "difficulty": cfg["difficulty"],
        "mode": cfg["mode"],
        "mode_label": cfg["mode_label"],
        "mode_spec": mode_rules.summary(cfg["mode"]),
        "boundaries": cfg["boundaries"],
        "player_name": cfg.get("player_name") or "",
        "central_question": cfg["central_question"],
        "hints": cfg["hints"],
        "clocks": clocks,
        "front_count": len(cfg["fronts"]),
        "brief": brief,
        "opening": str(raw.get("opening") or ""),
        "gameplay": _player_gameplay(state),
    }


def turn_brief(state):
    """A compact scene card the runtime injects before the model writes."""
    player = (state.get("entities") or {}).get("player") or {}
    world = state.get("world_info") or {}
    narrative = state.get("narrative") if isinstance(state.get("narrative"), dict) else {}
    location = str(player.get("location") or world.get("location_desc") or "")
    present = []
    for eid, ent in sorted((state.get("entities") or {}).items()):
        if eid == "player" or not isinstance(ent, dict):
            continue
        if str(ent.get("location") or "") != location:
            continue
        present.append({
            "id": eid,
            "name": str(ent.get("name") or eid),
            "agenda": str(ent.get("agenda") or ""),
            "speech": str(ent.get("speech") or ""),
        })
    facts = []
    for fact in ((state.get("context") or {}).get("facts") or [])[-8:]:
        if not isinstance(fact, dict) or fact.get("status") != "open":
            continue
        facts.append("%s：%s" % (fact.get("kind") or "fact", fact.get("text") or ""))
    clocks = []
    for clock in (narrative.get("clocks") or []):
        if isinstance(clock, dict):
            clocks.append("%s %s/%s" % (
                clock.get("name") or "局势", clock.get("filled", 0), clock.get("segments", 6)))
    try:
        from game_engine import gameplay as gameplay_rules
        scene_card = gameplay_rules.brief(state)
    except Exception:
        scene_card = {}
    mode = state.get("mode") if isinstance(state.get("mode"), dict) else {}
    return {
        "location": location,
        "present": present,
        "player": {
            "name": str(player.get("name") or "玩家"),
            "hp": player.get("hp", 0),
            "hp_max": player.get("hp_max", 0),
            "gold": player.get("gold", 0),
        },
        "facts": facts,
        "clocks": clocks,
        "mode": {
            "id": mode.get("id", "balanced"),
            "label": mode.get("label", "适中"),
            "narrative_rule": mode.get("narrative_rule", ""),
            "edge": mode.get("edge", ""),
        },
        "gameplay": {
            "act": scene_card.get("act"),
            "scene": scene_card.get("scene"),
            "clocks": scene_card.get("clocks"),
            "choice_policy": scene_card.get("choice_policy"),
        } if scene_card else {},
    }


def _last_assistant_text(state):
    for turn in reversed((state.get("turns") or [])):
        if isinstance(turn, dict) and turn.get("role") == "assistant":
            return str(turn.get("text") or "")
    return ""


def audit_turn(reply, tools_used, before, after):
    """Cheap, non-blocking checks.  Findings are stored on the turn for debugging."""
    findings = []
    text = str(reply or "").strip()
    paragraphs = [p for p in re.split(r"\n{2,}", text) if p.strip()]
    if len(text) < 80:
        findings.append({"severity": "S3", "category": "prose",
                         "issue": "回复过短，可能没有推进", "fix": "补一个具体变化或可行动画面"})
    if len(paragraphs) > 6:
        findings.append({"severity": "S3", "category": "prose",
                         "issue": "段落过多，叙事焦点分散", "fix": "压到 2–4 段"})
    last = _last_assistant_text(before)
    if last and text[:30] == last[:30]:
        findings.append({"severity": "S2", "category": "repetition",
                         "issue": "开头与上一回合重复", "fix": "换一个进入画面的角度"})
    if re.search(r"你(决定|选择|打算|同意|拒绝)", text):
        findings.append({"severity": "S2", "category": "agency",
                         "issue": "可能替玩家做了决定", "fix": "改成世界反应或让玩家确认"})
    changed = (
        int(after.get("tick", 0) or 0) != int(before.get("tick", 0) or 0)
        or len(after.get("event_log") or []) != len(before.get("event_log") or [])
        or bool(tools_used)
    )
    if not changed:
        findings.append({"severity": "S3", "category": "continuity",
                         "issue": "这一回合没有可见的状态变化", "fix": "推进时间/信息/关系/资源之一"})
    before_scene = int(before.get("scene_count", 0) or 0)
    after_scene = int(after.get("scene_count", 0) or 0)
    if after_scene <= before_scene:
        findings.append({"severity": "S2", "category": "scene",
                         "issue": "这一回合没有结算任何场景，可能又退回了 tick 流水账",
                         "fix": "用 campaign(action='resolve', outcome=..., cost=...) 收尾"})
    open_scene = after.get("scene") if isinstance(after.get("scene"), dict) else None
    if not open_scene:
        findings.append({"severity": "S3", "category": "scene",
                         "issue": "回合结束后没有下一场已开的戏", "fix": "用 campaign(action='open') 开下一场"})
    policy = ((after.get("gameplay") or {}).get("choice_policy") or {})
    if policy.get("must_cost"):
        # Cheap heuristic: choices that all look like "safe / safer / safest"
        # are not choices.  This only flags; it never rewrites prose.
        if re.search(r"(安全|稳妥|保险|什么都不做|原地等待)", text):
            findings.append({"severity": "S2", "category": "choice",
                             "issue": "选项/叙述出现无代价的安全牌", "fix": "让每个选择都失去一点东西"})
    return findings


def options():
    """Frontend/bootstrap options: one source of truth for the wizard."""
    return {
        "genres": GENRES,
        "plays": PLAYS,
        "tones": TONES,
        "difficulties": DIFFICULTIES,
        "modes": mode_rules.catalog(),
        "roles": [
            {"id": "random", "label": "随机生成", "desc": "让引擎给你一个能直接玩的人"},
            {"id": "custom", "label": "我自己写一句", "desc": "名字和身份由你定"},
            {"id": "preset", "label": "用预设角色", "desc": "用模板里的主角"},
        ],
        "boundaries": BOUNDARIES,
    }
