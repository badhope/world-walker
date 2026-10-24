#!/usr/bin/env python3
"""
万界·行者 · 实况面板 (World Walker Live Panel)

一个**只读**的小型 HTTP 服务：把状态文件渲染成可以长期挂着的游戏面板
（玩家血量/心流/图鉴/编年史/市场行情实时更新）。

单独用:
    python panel.py --state ww_state.json --port 8765
由 MCP 拉起: 调工具 open_panel（会自动指向当前对局的状态文件）

端点:
    GET /        面板页面（panel.html）
    GET /state   视图模型 JSON（状态 + 引擎推导的心流/相位/身份 + 图鉴）
    GET /events  SSE：状态文件一变就推送
"""

import argparse
import hashlib
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
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

from game_engine.rules import lorebook as lore_engine  # noqa: E402
from game_engine.rules import playbook as playbook_rules  # noqa: E402
from game_engine.rules import questline as quest_rules  # noqa: E402
from game_engine.rules.narrative_engine import (  # noqa: E402
    flow_channel_status, panarchy_phase_check, player_identity_vector)
from game_engine.state_schema import load_state  # noqa: E402

HTML_FILE = os.path.join(_SCRIPT_DIR, "panel.html")
HTML_DIR = _SCRIPT_DIR
MORAL_DIMS = ("关怀", "公平", "忠诚", "权威", "圣洁", "自由")
EVENTS_CAP = 40

# 唯一的事件分级表（前端不得再维护关键词表；未知类型走 EVENT_LABELS 兜底）
EVENT_LABELS = {
    "combat": ("交锋", "战"),
    "trade": ("交易", "交"),
    "social": ("人情", "情"),
    "karma": ("因果", "债"),
    "breakthrough": ("突破", "境"),
    "travel": ("行旅", "路"),
    "use_item": ("用物", "药"),
    "emergent": ("风起", "风"),
    "system": ("世界", "启"),
    "tick": ("回合", "回"),
    "prose": ("正文", "墨"),
    "world": ("世事", "势"),
    "quest": ("事业线", "线"),
}


_SEVERITY_BY_TYPE = {
    "system": "info",
    "tick": "info",
    "travel": "info",
    "prose": "info",
    "world": "info",
    "combat": "warning",
    "trade": "success",
    "social": "info",
    "karma": "warning",
    "emergent": "warning",
    "use_item": "success",
}


def _combat_kind(desc):
    """击杀 vs 交手：只按"结果"分类，不看谁赢。"""
    if any(w in desc for w in ("击败", "击杀", "倒下")):
        return "击杀", "danger"
    return "交手", "warning"


def _trade_kind(desc):
    if "购买" in desc:
        return "购入"
    if "出售" in desc:
        return "出售"
    return "交易"


def _social_kind(desc):
    return "人情"


def _breakthrough_kind(desc):
    if any(w in desc for w in ("失败", "反噬")):
        return "突破受挫", "danger"
    return "突破", "success"


def _travel_kind(desc):
    return ("初探" if "初次" in desc else "行旅")


def _social_severity(desc):
    return "success" if any(w in desc for w in ("好感", "敬重", "结盟", "帮助")) else "info"


_KIND_RULES = {
    "combat": _combat_kind,
    "trade": lambda d: (_trade_kind(d), "success"),
    "social": lambda d: ("人情", _social_severity(d)),
    "breakthrough": _breakthrough_kind,
    "travel": lambda d: (_travel_kind(d), "info"),
}


def classify_event(ev, milestone_ticks=()):
    """把一条 event_log 映射成前端可直接渲染的条目（kind/severity/title/icon 全在此决定）。

    分类逻辑按事件类型拆成小函数（`_KIND_RULES`），一行一个类型；
    未登记的类型走默认值，不抛错也不编造严重度。
    """
    etype = str(ev.get("type") or "system")
    desc = str(ev.get("desc") or "")
    tick = int(ev.get("tick", 0) or 0)
    title, icon = EVENT_LABELS.get(etype, ("事件", "·"))
    rule = _KIND_RULES.get(etype)
    if rule:
        kind, severity = rule(desc)
    else:
        kind, severity = "事件", _SEVERITY_BY_TYPE.get(etype, "info")
    # 事件 id 只是去重键，不用于任何安全用途（bandit B324 的 High 是误报，
    # 显式声明 usedforsecurity=False 让扫描器与读者都清楚这一点）
    digest = hashlib.sha1(desc.encode("utf-8"), usedforsecurity=False).hexdigest()[:8]
    return {"id": "%d:%s:%s" % (tick, etype, digest), "tick": tick, "type": etype,
            "kind": kind, "severity": severity, "title": title, "desc": desc,
            "icon": icon, "milestone": tick in set(milestone_ticks or ()),
            "repeat": int(ev.get("repeat", 1) or 1)}


SCENE_TEXT_CAP = 700
_SCENE_TEXT_SOURCES = (
    ("prose", "prose"),
    ("place", "places"),
    ("summary", "summaries"),
    ("world", "world_info"),
)


def _scene_prose(state, loc):
    """最新一段正文：只有它属于当前地点才算"当下"。"""
    prose = state.get("prose") or []
    if not prose or not isinstance(prose[-1], dict):
        return "", None
    last = prose[-1]
    last_loc = last.get("location")
    if loc and last_loc and last_loc != loc:
        return "", None
    return str(last.get("text") or ""), last.get("tick")


def _scene_place(state, loc):
    if not loc:
        return ""
    return str((state.get("places") or {}).get(loc, {}).get("desc") or "")


def _scene_summary(state):
    summaries = state.get("summaries") or []
    if not summaries:
        return ""
    return str(summaries[-1].get("text", "") or "")


def _scene_focus(events):
    """最近一条非 info 事件优先；没有就用最后一条。"""
    for e in reversed(events or []):
        if e.get("severity") != "info":
            return e.get("desc")
    return events[-1]["desc"] if events else None


_MOOD_BY_TYPE = {"trade": "trade", "social": "social", "travel": "discovery"}
_MOOD_BY_SEVERITY = {"danger": "danger", "success": "growth"}


def _scene_mood(events):
    if not events:
        return "neutral"
    last = events[-1]
    return (_MOOD_BY_TYPE.get(last.get("type"))
            or _MOOD_BY_SEVERITY.get(last.get("severity"))
            or "neutral")


def _scene_text(state, loc, focus):
    """按优先级取正文；每一级都只读状态，不推断剧情。"""
    text, prose_tick = _scene_prose(state, loc)
    for key, _label in _SCENE_TEXT_SOURCES[1:]:
        if text:
            break
        if key == "place":
            text = _scene_place(state, loc)
        elif key == "summary":
            text = _scene_summary(state)
        elif key == "world":
            text = str((state.get("world_info") or {}).get("location_desc") or "")
    if not text and focus:
        text = focus
    return text, prose_tick


def build_scene(state, events, player):
    """叙事主舞台标题/描述/氛围：只用状态里已有的文字，不编造剧情。

    正文优先级（越靠前越"当下"）：
      1. `prose` 最新一段（宿主用 publish_prose 写的本回合正文）
      2. `places[当前地点].desc`（travel 或 publish_prose 记下的本地描写）
      3. 最新章节摘要 `summaries[-1]`
      4. `world_info.location_desc`（开场描写）
      5. 最近事件文案
    这样移动之后面板显示的是新地方的描写，而不是永远停在开场那句。
    """
    world = state.get("world_info", {}) or {}
    loc = str(player.get("location", "") or "")
    focus = _scene_focus(events)
    desc, prose_tick = _scene_text(state, loc, focus)
    # 主舞台是"一屏可读"的叙事卡，不是阅读器：超长正文截断，完整正文仍在
    # 状态文件与 /export 里（面板只读，不丢数据）。
    shown = desc if len(desc) <= SCENE_TEXT_CAP else desc[:SCENE_TEXT_CAP].rstrip() + "…"
    return {"location": loc, "title": loc or str(world.get("name", "") or ""),
            "description": shown, "mood": _scene_mood(events), "focus_event": focus,
            "prose_tick": prose_tick, "full_length": len(desc)}


def build_inventory(state, player):
    """随身物品：以 player.items 为准，用市场元数据补显示名与类别。"""
    items = player.get("items")
    if not isinstance(items, dict):
        return []
    meta = {}
    for mk in (state.get("market") or {}).values():
        if isinstance(mk, dict):
            for k, it in mk.items():
                if isinstance(it, dict) and k not in meta:
                    meta[k] = it
    out = []
    for k in sorted(items):
        try:
            n = int(items[k])
        except (TypeError, ValueError):
            continue
        if n <= 0:
            continue
        it = meta.get(k) or {}
        out.append({"key": str(k), "name": str(it.get("name") or k),
                    "quantity": n, "type": str(it.get("type") or "")})
    return out


def build_relations(state, player_id="player"):
    """只返回与玩家有关的关系（键为字母序 a:b），带对方名字。"""
    rels = state.get("relations") or {}
    ents = state.get("entities") or {}
    out = []
    if not isinstance(rels, dict):
        return out
    for key, val in rels.items():
        if not isinstance(val, dict):
            continue
        parts = str(key).split(":")
        if len(parts) != 2 or player_id not in parts:
            continue
        other = parts[0] if parts[1] == player_id else parts[1]
        ent = ents.get(other) or {}
        out.append({"id": other, "name": str(ent.get("name") or other),
                    "affinity": int(val.get("affinity", 0) or 0),
                    "respect": int(val.get("respect", 0) or 0)})
    out.sort(key=lambda r: r["id"])
    return out


def _merge_adjacent(events):
    """把连续相同描述的事件合并为一条，并记 repeat 次数（缺省 1）。

    长局里战斗常连续多回合都是"攻击被闪避"，逐条铺开会让时间线失去信息量。
    只合并"紧邻且描述完全一致"的条目——不跨类型聚合，不改变事件先后顺序，
    因此既不掩盖真实叙事节奏，也不会把不同对象的事件混在一起。
    """
    out = []
    for e in events:
        desc = str(e.get("desc", ""))
        if out and str(out[-1].get("desc", "")) == desc:
            out[-1]["repeat"] = int(out[-1].get("repeat", 1)) + 1
            continue
        item = dict(e)
        item["repeat"] = 1
        out.append(item)
    return out


def _build_market(state):
    """market: [{location, items:[{key,name,price,base_price,supply,delta,type}]}]。

    按 location / item_key 排序，保证同一状态每次渲染顺序一致（面板每次刷新不该跳）。
    """
    out = []
    for loc, items in sorted((state.get("market") or {}).items()):
        rows = []
        for key, it in sorted((items or {}).items()):
            base = it.get("base_price") or it.get("price") or 0
            price = it.get("price", 0)
            rows.append({
                "key": key, "name": it.get("name", key), "price": price,
                "base_price": base, "supply": it.get("supply", 0),
                "delta": price - base, "type": it.get("type", ""),
            })
        out.append({"location": loc, "items": rows})
    return out


def _build_events(state):
    """时间线事件：滤掉 tick 心跳、合并相邻重复、再分类。

    返回 (events, milestone_ticks)。里程碑集合要给 classify_event 打标用，
    因此一并返回，避免调用方重复遍历。
    """
    milestone_ticks = {int(m.get("tick", 0) or 0) for m in (state.get("milestones") or [])}
    # tick 是心跳、prose 是正文（已在主舞台整段显示）：两者都不该占时间线。
    raw = [e for e in (state.get("event_log") or [])
           if e.get("type") not in ("tick", "prose")]
    events = [classify_event(e, milestone_ticks)
              for e in _merge_adjacent(raw)[-EVENTS_CAP:]]
    return events, milestone_ticks


def _build_player(state, player, loc, karma):
    """HUD 用的玩家切片：所有数值保持为数字，格式化留给前端（千分位/百分比）。"""
    return {
        "name": player.get("name", "玩家"), "level": player.get("level", ""),
        "stage": int(player.get("stage", 0) or 0),
        "stage_max": int((state.get("config") or {}).get("stage_max", 20) or 20),
        "mind_scars": int(player.get("mind_scars", 0) or 0),
        "near_death_count": int(player.get("near_death_count", 0) or 0),
        "hp": player.get("hp", 0), "hp_max": player.get("hp_max", 1),
        "mp": player.get("mp", 0), "mp_max": player.get("mp_max", 0),
        "gold": player.get("gold", 0), "location": loc,
        "currency": str(state.get("currency", "灵石")),
        "karma": karma,
        "attrs": player.get("attrs", {}),
        "inventory": build_inventory(state, player),
        "tier": _player_tier(state, player),
        "tier_max": len((state.get("config") or {}).get("level_tiers") or []) or None,
    }


def _player_tier(state, player):
    """等级阶梯序号（配置了 level_tiers 才有意义；否则返回 None 让前端回退到 stage）。"""
    try:
        from game_engine.rules.progression import level_tier
        if not (state.get("config") or {}).get("level_tiers"):
            return None
        return level_tier(state, player)
    except Exception:  # aqg: top-level boundary —— 阶梯坏了退回 stage 展示
        return None


DEFAULT_TERMS = {
    "hero": "行者",
    "level": "境界",
    "location": "所在",
    "hp": "气血",
    "mp": "内力",
    "gold": "钱财",
    "flow": "心流",
    "phase": "世界相位",
    "karma": "未清因果债",
    "inventory": "随身",
    "chronicle": "编年史",
    "present": "在场",
    "relations": "人情关系",
    "territory": "境地",
    "track": "修行轨",
    "stage": "阶段",
    "codex": "探索图鉴",
    "market": "市场行情",
    "milestones": "大事记",
    "factions": "势力",
    "rumors": "传闻",
    "culture": "风气",
    "quests": "事业线",
    "playbook": "玩法",
    "lorebook": "世界书",
}


def build_terms(state):
    """面板术语表：默认中文修真词 + 设定包 `ui.terms` 覆盖（世界观无关的最后一公里）。"""
    terms = dict(DEFAULT_TERMS)
    ui = state.get("ui") or {}
    override = ui.get("terms") if isinstance(ui.get("terms"), dict) else {}
    for k, v in (override or {}).items():
        key = str(k)
        if key in terms and str(v).strip():
            terms[key] = str(v)[:24]
    return terms


def build_world(state):
    """世界侧摘要（势力/相位/谣言/风气/物价指数）：面板右栏与顶部徽章用。"""
    try:
        from game_engine.rules.world_evolution import world_summary
        return world_summary(state)
    except Exception as e:  # aqg: top-level boundary —— 世界侧坏了不影响面板其余部分
        return {"error": str(e)[:120]}


def _build_cast(state, loc):
    """在场 / 别处两类 NPC 切片（面板右栏用）。

    `desc/personality/speech` 一并下发：点击角色卡要能看到完整的卡面文字，
    而不是只有被截断的一行简介（角色卡生态里这三段才是人物）。
    """
    present, others = [], []
    for eid, ent in (state.get("entities") or {}).items():
        if eid == "player":
            continue
        if not loc or ent.get("location") == loc:
            present.append({"id": eid, "name": ent.get("name", eid),
                            "level": ent.get("level", ""),
                            "faction": ent.get("faction", ""),
                            "hp": ent.get("hp"), "hp_max": ent.get("hp_max"),
                            "desc": (ent.get("desc") or "")[:240],
                            "personality": (ent.get("personality") or "")[:240],
                            "speech": (ent.get("speech") or "")[:240],
                            "mind_scars": int(ent.get("mind_scars", 0) or 0)})
        else:
            others.append({"id": eid, "name": ent.get("name", eid),
                           "location": ent.get("location", "")})
    return present, others


def _build_insights(state):
    """引擎推导块（心流/相位/身份）。任一计算失败只降级这一块，不让整页崩。"""
    try:
        return {
            "flow": flow_channel_status(state),
            "phase": panarchy_phase_check(state),
            "identity": player_identity_vector(state),
        }
    except Exception as e:  # aqg: top-level boundary —— 推导失败降级为错误字段，面板仍可用
        return {"error": str(e)[:120]}


def _build_codex(state):
    """探索图鉴四类（地点/人物/物品/设定词条）。"""
    c = state.get("codex") or {}
    return {"locations": c.get("locations", []), "people": c.get("people", []),
            "items": c.get("items", []), "lore": c.get("lore", [])}


def _build_playbook(state):
    """玩法剧本：这一局按什么循环、进度看什么、失败怎么算、当前节拍、宿主要怎么带。"""
    try:
        return playbook_rules.summary(state, state.get("playbook") or {})
    except Exception as exc:  # aqg: top-level boundary —— 剧本坏了不影响主舞台其余部分
        return {"error": str(exc)[:120]}


def _build_quests(state):
    """事业线：只给已浮现的（dormant 不占版面，避免变成待办清单）。"""
    try:
        quests = state.get("questlines") or []
        return {
            "rows": quest_rules.status(state, quests),
            "total": len(quests),
            "visible": quest_rules.visible_count(state, quests),
        }
    except Exception as exc:  # aqg: top-level boundary
        return {"rows": [], "total": 0, "visible": 0, "error": str(exc)[:120]}


def _build_lorebook(state):
    """世界书：每条目的触发次数、sticky/cooldown 剩余（只读展示，解释"为什么这段被触发"）。"""
    try:
        entries = state.get("lore") or []
        return {"rows": lore_engine.runtime_summary(state, entries), "total": len(entries)}
    except Exception as exc:  # aqg: top-level boundary
        return {"rows": [], "total": 0, "error": str(exc)[:120]}


def _unsettled_karma(state):
    return sum(e.get("amount", 0) for e in (state.get("karma_ledger") or [])
               if e.get("from") == "player" and not e.get("settled"))


def _chronicle(state):
    """编年史：同样是"滤心跳/正文 + 合并重复"，只取最近 24 条并倒序（最新在上）。"""
    raw = [e for e in (state.get("event_log") or [])
           if e.get("type") not in ("tick", "prose")]
    return _merge_adjacent(raw)[-24:][::-1]


def _milestones(state):
    return ["第%d回合·%s" % (m.get("tick", 0), m.get("desc", ""))
            for m in (state.get("milestones") or [])[-10:]][::-1]


def view_model(state_path):
    """把状态文件转成面板要用的视图模型（只读，不改状态）。

    本函数只做"取数 + 组装"：每个子块由一个 `_build_*` 负责，
    因此单函数复杂度保持低位，也让每块能独立测试。
    """
    state = load_state(state_path)
    record_sample(state_path, state)   # 侧写：态势采样（写 <state>.viz.jsonl，不碰状态文件）
    player = (state.get("entities") or {}).get("player") or {}
    loc = player.get("location", "")
    karma = _unsettled_karma(state)
    events, _ = _build_events(state)
    present, others = _build_cast(state, loc)

    return {
        "updated_at": time.strftime("%H:%M:%S"),
        "world": state.get("world_info", {}) or {},
        "tick": state.get("tick", 0),
        "seed": state.get("rng_seed"),
        "skin": skin_for_world(state),
        "terms": build_terms(state),
        "meta": {
            "state_path": os.path.abspath(state_path),
            "sidecar": os.path.abspath(series_path(state_path)),
            "inbox": os.path.abspath(inbox_path(state_path)),
            "read_only": True,
            "panel": "万界·行者 实况主舞台（只读）",
        },
        "scene": build_scene(state, events, player),
        "events": events,
        "relations": build_relations(state),
        "player": _build_player(state, player, loc, karma),
        "insights": _build_insights(state),
        "world_state": build_world(state),
        "moral": {
            "dims": MORAL_DIMS,
            "values": (player.get("morality") or [0, 0, 0, 0, 0, 0])[:6],
            "derived": _derived_moral(state),
        },
        "karma": karma,
        "present": present,
        "others": others,
        "codex": _build_codex(state),
        "lore_total": len(state.get("lore", [])),
        "market": _build_market(state),
        "chronicle": _chronicle(state),
        "milestones": _milestones(state),
        "summaries": len(state.get("summaries") or []),
        "archived_events": int(state.get("archived_events", 0)),
        "flags": state.get("world_flags", []),
        "prose_count": len(state.get("prose") or []),
        "inbox_pending": len(inbox_pending(state_path)),
        "playbook": _build_playbook(state),
        "quests": _build_quests(state),
        "lorebook": _build_lorebook(state),
    }


def _derived_moral(state):
    """引擎推导的六维道德（从业债台账/事件累加）；面板用它覆盖静态 morality。

    注意维度顺序必须与 `MORAL_DIMS`（中文展示名）一致，而引擎侧用的是英文键
    （care/fairness/loyalty/authority/sanctity/liberty）——两边顺序一一对应。
    推导失败时返回空表，前端自动回退到静态值。
    """
    try:
        from game_engine.rules.narrative_engine import MORAL_DIMS as ENGINE_DIMS
        from game_engine.rules.narrative_engine import update_player_moral_identity
        vec = update_player_moral_identity(state)
        return [int(vec.get(k, 0)) for k in ENGINE_DIMS]
    except Exception:  # aqg: top-level boundary —— 推导失败只用静态值
        return []


# ────────────────────────── 行动收件箱（双向通道，可选）──────────────────────────
# 面板仍然**只读状态文件**（INV-V1 不变）。玩家在浏览器里写的行动不进状态，
# 而是追加到 `<状态文件>.inbox.jsonl` 这个侧写文件；宿主 Agent 用 MCP 工具
# `pending_actions` 取走并照常经引擎结算。这样：
#   · 状态只有一个写入源（MCP），确定性 / 快照回退语义不被破坏；
#   · 玩家不必每回合切回对话框，浏览器就能排队行动；
#   · 宿主不在线时行动只是"排队"，不会凭空改世界。
INBOX_MAX_TEXT = 2000
INBOX_MAX_PENDING = 100


def inbox_path(state_path):
    """收件箱侧写路径（与状态文件同目录，不参与打包）。"""
    return state_path + ".inbox.jsonl"


def inbox_read_all(state_path):
    """读全部收件记录（坏行跳过，永不抛）。"""
    out = []
    path = inbox_path(state_path)
    if not state_path or not os.path.exists(path):
        return out
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if isinstance(rec, dict) and rec.get('text'):
                    out.append(rec)
    except OSError:
        return []
    return out


def inbox_pending(state_path):
    """未处理的行动（按写入顺序，封顶 INBOX_MAX_PENDING）。"""
    return [r for r in inbox_read_all(state_path) if not r.get('done')][-INBOX_MAX_PENDING:]


def _rewrite_inbox(state_path, records):
    path = inbox_path(state_path)
    with open(path, 'w', encoding='utf-8') as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')


def inbox_append(state_path, text, source='panel'):
    """追加一条行动；超出上限时丢弃最旧的未处理条目（侧写保持有界）。"""
    rec = {
        'id': hashlib.sha1(('%s|%s' % (time.time_ns(), text)).encode('utf-8'),
                           usedforsecurity=False).hexdigest()[:12],
        'ts': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'tick': None,
        'source': str(source)[:24],
        'text': text,
        'done': False,
    }
    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            rec['tick'] = int(json.load(f).get('tick', 0) or 0)
    except (OSError, ValueError, TypeError):
        pass
    records = inbox_read_all(state_path)
    records.append(rec)
    pending = [r for r in records if not r.get('done')]
    if len(pending) > INBOX_MAX_PENDING:
        drop = len(pending) - INBOX_MAX_PENDING
        keep = []
        for r in records:
            if drop > 0 and not r.get('done'):
                drop -= 1
                continue
            keep.append(r)
        records = keep
    _rewrite_inbox(state_path, records)
    return rec


def inbox_mark_done(state_path, ids):
    """把指定 id 标为已处理；返回实际标记条数。"""
    wanted = {str(i) for i in ids}
    records = inbox_read_all(state_path)
    n = 0
    for r in records:
        if str(r.get('id')) in wanted and not r.get('done'):
            r['done'] = True
            r['done_ts'] = time.strftime('%Y-%m-%dT%H:%M:%S')
            n += 1
    if n:
        _rewrite_inbox(state_path, records)
    return n


STATIC_WHITELIST = {
    "/": ("panel.html", "text/html; charset=utf-8"),
    "/panel.html": ("panel.html", "text/html; charset=utf-8"),
    "/panel.css": ("panel.css", "text/css; charset=utf-8"),
    "/panel.js": ("panel.js", "text/javascript; charset=utf-8"),
    "/assets/echarts.min.js": (os.path.join("assets", "echarts.min.js"),
                               "text/javascript; charset=utf-8"),
}

from game_engine.viz_series import SERIES_CAP, load_series, record_sample, series_path  # noqa: E402


# 皮肤注册表：id → 视觉与图表调色板（前端只消费，不在 JS 里写配色表）
SKINS = {
    "xuanshu": {
        "id": "xuanshu", "accent": "#e8b04b", "motif": "玄门·墨金",
        "palette": {"line": "#e8b04b", "area": "rgba(232,176,75,.18)", "bar": "#c07a3a",
                    "hp": "#d9534f", "mp": "#4a90d9", "grid": "#2b3341", "text": "#a3abb9"},
    },
    "neutral": {
        "id": "neutral", "accent": "#8aa6c8", "motif": "通用·石墨",
        "palette": {"line": "#8aa6c8", "area": "rgba(138,166,200,.16)", "bar": "#6f8cab",
                    "hp": "#d9534f", "mp": "#4a90d9", "grid": "#2b3341", "text": "#a3abb9"},
    },
    "ink": {
        "id": "ink", "accent": "#a8b6c1", "motif": "水墨·宣纸",
        "palette": {"line": "#8fb0c9", "area": "rgba(143,176,201,.14)", "bar": "#7d8b96",
                    "hp": "#b4553f", "mp": "#5d7fa3", "grid": "#333a44", "text": "#9aa4b0"},
    },
    "neon": {
        "id": "neon", "accent": "#4fe0c0", "motif": "霓虹·夜城",
        "palette": {"line": "#4fe0c0", "area": "rgba(79,224,192,.16)", "bar": "#c74fe0",
                    "hp": "#ff5d7d", "mp": "#4fa8ff", "grid": "#243044", "text": "#93a4bd"},
    },
}


# 品牌默认值（单一信源，BRAND.md 与 README 引用此处；ui.brand/tagline 可整局覆盖）
DEFAULT_BRAND = "万界·行者"
DEFAULT_TAGLINE = "万界为卷 · 因果为墨"


def skin_for_world(state):
    """世界皮肤：优先取状态里的 ui 配置（设定包可写），否则按世界名启发式，未知一律回退 neutral。
    ui.brand / ui.tagline 让基于本引擎的其他游戏带上自己的品牌。"""
    world = state.get("world_info", {}) or {}
    ui = state.get("ui") if isinstance(state.get("ui"), dict) else {}
    sid = str(ui.get("skin") or "").strip().lower()
    if sid not in SKINS:
        text = ("%s %s" % (world.get("name", ""), " ".join(str(f) for f in (state.get("world_flags") or [])))).lower()
        sid = "xuanshu" if ("xuanshu" in text or "玄枢" in text) else "neutral"
    skin = dict(SKINS[sid])
    skin["palette"] = dict(SKINS[sid]["palette"])
    if ui.get("accent"):
        skin["accent"] = str(ui["accent"])
    if ui.get("motif"):
        skin["motif"] = str(ui["motif"])
    skin["brand"] = str(ui.get("brand") or DEFAULT_BRAND)[:24]
    skin["tagline"] = str(ui.get("tagline") or DEFAULT_TAGLINE)[:48]
    return skin


class Handler(BaseHTTPRequestHandler):
    state_path = None

    def log_message(self, *args):  # 静音访问日志
        pass

    def handle_one_request(self):
        """浏览器/SSE 客户端随时可能掐断连接（刷新、关页签）——这是常态，不是错误。
        默认实现会把 ConnectionAbortedError 抛给 socketserver 打一整篇栈，这里吞掉。"""
        try:
            super().handle_one_request()
        except (ConnectionError, TimeoutError):
            self.close_connection = True

    # 基础安全响应头。面板是只读本地页，但"本地"不等于"可以裸奔"：
    # 任何页面都可能被别的本地进程/恶意扩展当作跳板，最小化攻击面是零成本的。
    _SECURITY_HEADERS = (
        ("X-Content-Type-Options", "nosniff"),          # 禁止 MIME 嗅探
        ("X-Frame-Options", "DENY"),                    # 禁止被 iframe 嵌入（防点击劫持）
        ("Referrer-Policy", "no-referrer"),             # 不外泄来源地址
        ("Content-Security-Policy",
         "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
         "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"),
    )

    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        for name, val in self._SECURITY_HEADERS:
            self.send_header(name, val)
        self.end_headers()
        self.wfile.write(body)

    def _static(self, path):
        """只发白名单里的固定文件；其余路径一律 404（不拼用户输入进文件系统）。"""
        entry = STATIC_WHITELIST.get(path)
        if not entry:
            self._send(404, "text/plain; charset=utf-8", b"not found")
            return
        fname, ctype = entry
        try:
            with open(os.path.join(HTML_DIR, fname), "rb") as f:
                self._send(200, ctype, f.read())
        except OSError:
            self._send(404, "text/plain; charset=utf-8", b"not found")

    def _json_body(self, limit=8192):
        try:
            n = int(self.headers.get('Content-Length') or 0)
        except ValueError:
            return None
        if n <= 0 or n > limit:
            return None
        try:
            return json.loads(self.rfile.read(n).decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            return None

    def do_POST(self):
        """唯一写入口：行动收件箱（状态文件仍然只读，INV-V1 不变）。

        本机服务不等于没有攻击面，因此：
          · 带 Origin 时必须与 Host 同源（跨站表单伪造会被拒）；
          · 只收 application/json（简单请求无法跨站伪造该 Content-Type）；
          · 请求体 ≤ 8KB、正文 ≤ 2000 字；
          · 未知路径一律 404，不回显任何内容。
        """
        path = self.path.split("?")[0]
        if path != '/action':
            self._send(404, 'text/plain; charset=utf-8', b'not found')
            return
        origin = self.headers.get('Origin') or ''
        host = self.headers.get('Host') or ''
        if origin and origin.split('//')[-1] != host:
            self._send(403, 'application/json; charset=utf-8',
                       json.dumps({'ok': False, 'error': '跨站请求被拒绝'},
                                  ensure_ascii=False).encode('utf-8'))
            return
        ctype = (self.headers.get('Content-Type') or '').split(';')[0].strip().lower()
        if ctype != 'application/json':
            self._send(415, 'application/json; charset=utf-8',
                       json.dumps({'ok': False, 'error': '只接受 application/json'},
                                  ensure_ascii=False).encode('utf-8'))
            return
        body = self._json_body()
        if not isinstance(body, dict):
            self._send(400, 'application/json; charset=utf-8',
                       json.dumps({'ok': False, 'error': '请求体不是合法 JSON'},
                                  ensure_ascii=False).encode('utf-8'))
            return
        text = str(body.get('text') or '').strip()
        if not text:
            self._send(400, 'application/json; charset=utf-8',
                       json.dumps({'ok': False, 'error': '行动不能为空'},
                                  ensure_ascii=False).encode('utf-8'))
            return
        if len(text) > INBOX_MAX_TEXT:
            self._send(400, 'application/json; charset=utf-8',
                       json.dumps({'ok': False,
                                   'error': '行动太长（上限 %d 字）' % INBOX_MAX_TEXT},
                                  ensure_ascii=False).encode('utf-8'))
            return
        try:
            rec = inbox_append(self.state_path, text)
        except OSError as exc:
            self._send(500, 'application/json; charset=utf-8',
                       json.dumps({'ok': False,
                                   'error': '写入收件箱失败：%s' % str(exc)[:120]},
                                  ensure_ascii=False).encode('utf-8'))
            return
        self._send(200, 'application/json; charset=utf-8',
                   json.dumps({'ok': True, 'queued': rec,
                               'pending': len(inbox_pending(self.state_path))},
                              ensure_ascii=False).encode('utf-8'))

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/state":
            try:
                vm = json.dumps(view_model(self.state_path), ensure_ascii=False).encode("utf-8")
            except FileNotFoundError:
                vm = json.dumps({
                    "error": "对局状态文件不存在：%s" % self.state_path,
                    "hint": "先在对话里开一局（world_init / load_setting），本页会自动接上。",
                }, ensure_ascii=False).encode("utf-8")
            except Exception as e:  # aqg: top-level boundary —— HTTP 端点：任何读取失败都转成页面可读错误，不抛栈
                vm = json.dumps({
                    "error": "状态文件读取失败：%s" % str(e)[:180],
                    "hint": "文件可能正在写入或格式不合法；稍候重试，或先用 snapshot 校验存档。",
                }, ensure_ascii=False).encode("utf-8")
            self._send(200, "application/json; charset=utf-8", vm)
        elif path == "/actions":
            body = json.dumps({'pending': inbox_pending(self.state_path)},
                              ensure_ascii=False).encode('utf-8')
            self._send(200, 'application/json; charset=utf-8', body)
        elif path == "/export":
            try:
                with open(self.state_path, 'rb') as f:
                    raw = f.read()
            except OSError as exc:
                self._send(404, 'application/json; charset=utf-8',
                           json.dumps({'error': '状态文件不可读：%s' % str(exc)[:120]},
                                      ensure_ascii=False).encode('utf-8'))
                return
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Content-Disposition',
                             'attachment; filename="%s"' % os.path.basename(self.state_path))
            for name, val in self._SECURITY_HEADERS:
                self.send_header(name, val)
            self.end_headers()
            self.wfile.write(raw)
        elif path == "/series":
            body = json.dumps(self._series_payload(), ensure_ascii=False).encode("utf-8")
            self._send(200, "application/json; charset=utf-8", body)
        elif path == "/events":
            self._sse()
        else:
            self._static(path)

    def _series_payload(self):
        """长局态势序列：直接读侧写文件（不读也不写状态文件）。"""
        try:
            samples = load_series(self.state_path)
        except (OSError, ValueError, TypeError):
            samples = []          # 侧写坏行/缺文件 → 图表空态，接口照常 200
        skin = SKINS["neutral"]
        try:
            skin = skin_for_world(load_state(self.state_path))
        except (OSError, ValueError, TypeError):
            pass                  # 状态不可读时调色板退回 neutral；错误态由 /state 负责展示
        return {"samples": samples, "cap": SERIES_CAP, "palette": skin.get("palette", {})}

    def _state_payload(self):
        """SSE 每帧的 JSON：状态不可读时不是断流，而是把原因推给页面显示。"""
        try:
            return json.dumps(view_model(self.state_path), ensure_ascii=False)
        except FileNotFoundError:
            return json.dumps({
                "error": "对局状态文件不存在：%s" % self.state_path,
                "hint": "先在对话里开一局（world_init / load_setting），本页会自动接上。",
            }, ensure_ascii=False)
        except Exception as e:  # aqg: top-level boundary —— SSE 端点：状态不可读时推错误帧而不是断流
            return json.dumps({
                "error": "状态文件读取失败：%s" % str(e)[:180],
                "hint": "文件可能正在写入或格式不合法；稍候重试，或先用 snapshot 校验存档。",
            }, ensure_ascii=False)

    def _sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        last = object()
        try:
            while True:
                try:
                    st = os.stat(self.state_path)
                    sig = (st.st_mtime_ns, st.st_size)
                except OSError:
                    sig = None
                if sig != last:
                    last = sig
                    body = self._state_payload()
                    self.wfile.write(("event: state\ndata: %s\n\n" % body).encode("utf-8"))
                else:
                    self.wfile.write(b": ping\n\n")
                self.wfile.flush()
                time.sleep(0.5)
        except (BrokenPipeError, ConnectionResetError, OSError, ValueError):
            return


class _PanelServer(ThreadingHTTPServer):
    """面板 HTTP 服务。

    allow_reuse_address 必须是 False：Python 的 HTTPServer 默认把它设为 1
    （SO_REUSEADDR）。在 Windows 上这允许**两个进程同时绑定同一端口**，
    结果是请求被别的进程抢走、面板返回 404 而自己毫无察觉
    （实测被一个无关的 `python -m http.server 8791` 抢过）。
    关掉它，端口冲突就会正常抛 OSError，从而走下面的顺延逻辑。
    """
    allow_reuse_address = False


def start(state_path, port=8765, host="127.0.0.1"):
    """启动面板服务（后台线程），返回 (server, 实际端口)。端口被占则自动顺延。"""
    Handler.state_path = os.path.abspath(state_path)
    srv = None
    for p in range(int(port), int(port) + 10):
        try:
            srv = _PanelServer((host, p), Handler)
            break
        except OSError:
            continue
    if srv is None:
        raise RuntimeError("端口 %s~%s 都被占用" % (port, int(port) + 9))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def main():
    ap = argparse.ArgumentParser(description="万界·行者 实况面板")
    ap.add_argument("--state", default="ww_state.json", help="状态文件路径")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    if not os.path.exists(args.state):
        print("状态文件不存在: %s" % args.state)
        return 1
    srv, port = start(args.state, args.port, args.host)
    print("面板已启动: http://%s:%d/   （盯住 %s，Ctrl+C 退出）" % (args.host, port, args.state))
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        srv.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
