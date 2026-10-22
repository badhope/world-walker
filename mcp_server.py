#!/usr/bin/env python3
"""
万界·行者 · MCP 服务器 (World Walker MCP Server)

把规则引擎包装成 MCP 工具，供任意 MCP 客户端（Claude Code / Codex / Cursor / 自建 Agent）
驱动一局文字对话互动游戏：读设定 → world_init 建世界 → 玩家每步行动都经引擎结算 →
Agent 只负责把引擎返回的 JSON 转写成文学描写。

设计约束（与 GAME_MASTER_PROTOCOL.md 一致）:
- 所有数值结算必须走引擎工具，Agent 不得手写 state JSON
- state 落盘为 JSON 文件，对局可中断续跑；服务器另记"当前对局"路径
- 可选种子: 同一 state + 同一 tick + 同一行动 → 同一结果（rng_seed）

World Walker rule engine exposed over MCP. The host agent narrates; the engine decides.
"""

import functools
import json
import os
import random
import re
import sys

# 引擎内部用 `import game_engine.*`，要求仓库目录名恰好是 game_engine。
# 这里注册包别名，使任意克隆目录名 / pip 安装方式都能工作。
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if "game_engine" not in sys.modules:
    import importlib.util

    _spec = importlib.util.spec_from_file_location(
        "game_engine",
        os.path.join(_SCRIPT_DIR, "__init__.py"),
        submodule_search_locations=[_SCRIPT_DIR],
    )
    _engine_pkg = importlib.util.module_from_spec(_spec)
    _engine_pkg.__path__ = [_SCRIPT_DIR]
    sys.modules["game_engine"] = _engine_pkg

from mcp.server.mcpserver import MCPServer

from game_engine.rules.cognition import daily_cognitive_budget, should_use_system2
from game_engine.rules.combat import resolve_combat
from game_engine.rules.economy import resolve_trade, tick_market
from game_engine.rules.karma import get_karma_consequence, resolve_karma
from game_engine.rules.narrative_engine import (
    check_world_emergent_events,
    flow_channel_status,
    panarchy_phase_check,
    player_identity_vector,
    update_player_moral_identity,
)
from game_engine.rules.social import resolve_social_event
from game_engine.rules.social_extended import merit_quality
from game_engine.rules.world_dynamics import event_information
from game_engine.rules.models import model as _model_fn, model_names as _model_names
from game_engine.state_schema import entity_key, load_state, log_event, save_state, seed_rng
from game_engine.viz_series import record_sample

from pydantic import BaseModel, Field


class WorldInfo(BaseModel):
    """世界基本盘（设定里的世界观信息）。"""
    name: str = Field(description="世界名，如「临江渡口」「青云界」")
    era: str = Field(default="", description="纪元/时代，如「江湖历三年」")
    location_desc: str = Field(default="", description="开场地点描写（两三句，用于开局叙事）")


class EntityIn(BaseModel):
    """一个角色。主角用 player 参数传入；NPC 放进 entities 数组并给 id。"""
    id: str | None = Field(default=None, description="实体 id（NPC 必填；player 不用填）")
    name: str = Field(description="显示名")
    faction: str = Field(default="", description="阵营/势力")
    attrs: dict[str, int] = Field(default_factory=dict,
                                 description="五维属性 str/dex/int/con/cha，缺省按 10")
    hp: int | None = Field(default=None, description="当前生命，缺省等于 hp_max")
    hp_max: int = Field(default=100, description="生命上限")
    mp: int = Field(default=0, description="当前内力/法力")
    mp_max: int = Field(default=0, description="内力上限")
    level: str = Field(default="凡人", description="境界/等级，如「练气三层」「一流高手」「C-class」")
    gold: int = Field(default=0, description="钱财")
    location: str = Field(default="", description="所在地（要与 market 的 location 一致才可交易）")
    items: dict[str, int] = Field(default_factory=dict,
                                  description="随身物品 {商品 key: 数量}（可选，设定里可给初始持有；卖出须持有）")
    skills: list[str] = Field(default_factory=list, description="技能名（可选）")
    morality: list[int] = Field(default_factory=list, description="六维道德向量（可选，默认全 0）")


class MarketItemIn(BaseModel):
    """市场里的一件商品。交易工具用 key 定位它（不是显示名）。"""
    key: str = Field(description="商品 key，交易时传它，如 chen_jiu")
    name: str = Field(description="显示名，如「陈酒」")
    price: int = Field(default=50, description="当前价")
    supply: int = Field(default=20, description="库存")
    base_price: int | None = Field(default=None, description="基准价（价格会回归它），缺省等于 price")
    type: str = Field(default="", description="类别（丹药/武器/情报…）")
    desc: str = Field(default="", description="一句话描述")


class MarketIn(BaseModel):
    """一个地点的市场。"""
    location: str = Field(description="地点（与角色的 location 一致）")
    items: list[MarketItemIn] = Field(default_factory=list, description="该地点的商品")


class RelationIn(BaseModel):
    """一条关系（键由引擎按字母序生成，不用你操心顺序）。"""
    a: str = Field(description="实体 id 之一")
    b: str = Field(description="实体 id 之二")
    affinity: int = Field(default=0, description="亲密度 -100~100")
    respect: int = Field(default=0, description="敬重/畏惧 -100~100")


server = MCPServer(
    name="world-walker",
    version="0.8.0",
    instructions=(
        "万界·行者规则引擎：世界观无关的因果推演内核。主持文字互动游戏时："
        "先 world_schema 了解状态结构，按玩家设定调用 world_init 建世界；"
        "玩家的每个行动都交给对应工具结算，你只把返回的 JSON 转写成文学描写，"
        "不得自行编造数值结果；回合结束调用 tick；每 3-5 回合调用 narrative 与 status 一次。"
    ),
)

# 工具里"有意拒绝"的原因必须回到宿主手里。MCP SDK 对非 ToolError 的异常只回
# "Error executing tool X"（原因留在服务端日志），宿主 Agent 无从自纠；这里把
# 规则层的 ValueError/KeyError 统一转成 ToolError，报错正文原样透传。
try:
    from mcp.server.mcpserver.exceptions import ToolError as _ToolError
except ImportError:  # 兼容旧版 SDK 布局
    try:
        from mcp.server.fastmcp.exceptions import ToolError as _ToolError
    except ImportError:
        class _ToolError(Exception):
            pass

_raw_tool = server.tool


def _guarded_tool(*dargs, **dkwargs):
    _decorate = _raw_tool(*dargs, **dkwargs)

    def _wrap(fn):
        @functools.wraps(fn)
        def _guarded(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except _ToolError:
                raise
            except (ValueError, KeyError) as exc:
                msg = exc.args[0] if (isinstance(exc, KeyError) and exc.args) else str(exc)
                raise _ToolError(str(msg)) from exc
        return _decorate(_guarded)
    return _wrap


server.tool = _guarded_tool

NEW_GAME_BRIEF = """你在主持一局文字互动游戏，数值结算必须全部通过 world-walker 的工具完成。

## 铁律
1. 所有数值（命中/伤害/价格/关系/因果）必须由工具结算，不许自行编造或心算。
2. 玩家只该看到你的文学描写；JSON 与字段名不要让玩家看到，数值要自然融进叙事。
3. 不要手改状态文件，一切变更都经工具落盘。

## 回合流程
- 开局：`world_init`（设定与状态文件路径见下）→ 写两三百字开场（可用 world_info.location_desc）。
- 每个玩家行动：需要时 `read_state` 看现状 → 选对应工具结算（combat / trade / social / karma）
  → `narration_context`（传当下场景文字，拿到触发的设定条目、在场角色的卡面文字与编年史）
  → 把返回 JSON 转写成文学描写。
- 移动：`travel`（只有它能改玩家的 location；首次到达自动进图鉴）。玩家说要"去某地/进某个房间"就用它。
- 回合收尾：`tick`。
- 每 3-5 回合：`narrative`（涌现事件与相位）与 `status`（心流/身份/道德/认知）各一次，
  把结果织进叙事节奏（例如心流偏低就安排一段缓冲剧情）。
- 字段不清楚时先 `world_schema` 查（world_init 的入参 schema 已带字段说明，通常不必查）。
- 仓库自带设定包时可直接 `load_setting(path=...)` 一键开局（如 `settings/玄枢界.setting.json`）。
- 有角色卡（酒馆生态的 .png/.json 卡）或世界书文件时：`character_card_read` 先看 → `add_character`
  把人收进局（卡面文字会自动进叙事层）→ 设定类文件用 `import_lorebook` 并入。
- 玩家想反悔/分叉剧情：`snapshot` 存点、`restore` 回退（引擎状态是确定性的，回退后重放同种子一致）。
- 买东西用 `use_item`（丹药回气血是引擎结算、要花钱，不是白拿）；没有角色卡的新人物用 `spawn_npc` 入局。
- 要算"效果大概多大"时先 `model_list` 查模型目录（价格回归/势力消长/谣言传播/厄运概率/心境摆荡…），
  再用 `model(name, params)` 直接得数值——例如 `model('lerner_price', {'cogs': 60, 'elasticity': 2.5})`、
  `model('logistic_sigmoid', {'x': 150, 'x0': 150})`——宿主别心算，也别再靠临场推理编数字。
- 开局后调一次 `open_panel`：给玩家一个只读实况主舞台（叙事/HUD/事件时间线/图鉴/行情，自动刷新）——
  玩家记不住的东西（去过哪、见过谁、什么价）都在上面。
- 成长走 `advance`（突破由引擎判定，别自己改等级）；每 20-50 回合调一次 `write_summary` 写摘要，
  接不上前文时用 `recap`；玩家提到很久以前的事，用 `recall` 按关键词把旧事捞回来——
  叙述只带「最近若干回合 + 最新摘要 + 大事记」，永远不要把全部历史塞进上下文。

## 本次设定
{setting}

## 状态文件
{state_path}（seed={seed}，同种子可复现）

现在开始：先 `world_init` 开起这局，然后写开场。"""


@server.prompt(name="new_game", title="开一局新游戏",
               description="把设定交给规则引擎，开始一局文字互动游戏。参数 setting 填你的设定（世界观/主角/NPC/地点/商品表）")
def new_game(setting: str, state_path: str = "ww_state.json", seed: int = 20261014) -> str:
    """生成「开局指令」：协议 + 你的设定 + 状态文件，客户端把它作为一条用户消息发给 Agent。"""
    return (NEW_GAME_BRIEF.replace("{setting}", setting.strip())
                         .replace("{state_path}", state_path)
                         .replace("{seed}", str(seed)))


_active = {"path": None}
PANELS = {}
ATTR_KEYS = ("str", "dex", "int", "con", "cha")
SOCIAL_EVENTS = ("help", "harm", "threaten", "intimidate", "gift", "betray",
                 "cooperate", "insult", "praise", "murder")
KARMA_TYPES = ("murder_innocent", "murder_evil", "theft", "lie", "betray",
               "help_innocent", "help_evil", "repay_debt", "oath_broken")



# ────────────────────────── 角色卡与世界书（复用酒馆生态格式）──────────────────────────
# 支持: 角色卡 V1/V2/V3（.json 或 .png 内嵌 tEXt: chara/ccv3）与
#       SillyTavern world-info（{"entries": {...}}）两套字段名。
_CARD_PNG_KEYS = ("chara", "ccv3")


def _read_png_card(path):
    """从 PNG 的 tEXt/iTXt 块里取嵌卡（base64 JSON）。"""
    import base64, struct
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    pos = 8
    while pos + 8 <= len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        if ctype in (b"tEXt", b"iTXt"):
            key, _, value = chunk.partition(b"\x00")
            if key.decode("latin-1", "ignore").strip() in _CARD_PNG_KEYS:
                try:
                    return json.loads(base64.b64decode(value.strip()).decode("utf-8"))
                except Exception:  # nosec B110 —— 角色卡 tEXt 块可能是任意内容，解析失败就试下一个块
                    pass
        pos += 12 + length
    return None


def _load_card(path):
    """读角色卡并返回 data 段（V1 平铺 / V2、V3 的 data 均可）。"""
    if path.lower().endswith(".png"):
        raw = _read_png_card(path)
        if raw is None:
            raise ValueError("PNG 里没有嵌卡（tEXt 关键字 chara/ccv3）: %s" % path)
    else:
        raw = json.load(open(path, encoding="utf-8"))
    nested = isinstance(raw, dict) and isinstance(raw.get("data"), dict)
    data = raw["data"] if nested else raw
    if not isinstance(data, dict) or not data.get("name"):
        raise ValueError("不是可识别的角色卡（缺 name）: %s" % path)
    spec = (raw.get("spec_version") or raw.get("spec")) if nested else "v1"
    return data, (spec or "unknown")


def _normalize_lore_entry(e):
    """规范化世界书条目；同时吃角色卡 character_book 与 ST world-info 两套字段名。"""
    if not isinstance(e, dict):
        return None
    keys = e.get("keys", e.get("key")) or []
    if isinstance(keys, str):
        keys = [keys]
    sec = e.get("secondary_keys", e.get("keysecondary")) or []
    if isinstance(sec, str):
        sec = [sec]
    content = str(e.get("content") or "").strip()
    keys = [str(k).strip() for k in keys if str(k).strip()]
    if not keys or not content:
        return None
    if "enabled" in e:
        enabled = bool(e["enabled"])
    else:
        enabled = not bool(e.get("disable", False))
    return {
        "keys": keys,
        "secondary_keys": [str(k).strip() for k in sec if str(k).strip()],
        "content": content,
        "comment": str(e.get("comment") or e.get("name") or ""),
        "selective": bool(e.get("selective", False)),
        "constant": bool(e.get("constant", False)),
        "case_sensitive": bool(e.get("case_sensitive", False)),
        "order": int(e.get("insertion_order", e.get("order", 100)) or 0),
        "enabled": enabled,
    }


def _load_lorebook(path):
    """读世界书文件；支持 ST world-info 与角色卡自带 book。"""
    d = json.load(open(path, encoding="utf-8"))
    if isinstance(d, dict) and isinstance(d.get("data"), dict):
        d = d["data"]
    entries = None
    if isinstance(d, dict):
        if isinstance(d.get("character_book"), dict):
            entries = d["character_book"].get("entries")
        elif isinstance(d.get("entries"), (list, dict)):
            entries = d["entries"]
    elif isinstance(d, list):
        entries = d
    if isinstance(entries, dict):
        entries = list(entries.values())
    if not isinstance(entries, list):
        raise ValueError("不是可识别的世界书（缺 entries）: %s" % path)
    return [n for n in (_normalize_lore_entry(e) for e in entries) if n]


def _trigger_lore(lore, text):
    """关键词触发（与酒馆同语义）：主键命中；selective 时副键也要命中；constant 常驻。"""
    low = text.lower()

    def hit(e, k):
        return (k in text) if e.get("case_sensitive") else (k.lower() in low)

    hits = []
    for e in lore:
        if not e.get("enabled"):
            continue
        if e.get("constant") or any(hit(e, k) for k in e.get("keys", [])):
            if e.get("selective") and e.get("secondary_keys") and not any(
                    hit(e, k) for k in e["secondary_keys"]):
                continue
            hits.append(e)
    hits.sort(key=lambda x: x.get("order", 100))
    return hits


def _state_path() -> str:
    if not _active["path"]:
        raise ValueError("当前没有进行中的对局：先调用 world_init（新建）或 world_open（续跑）")
    return _active["path"]


def _load() -> dict:
    return load_state(_state_path())


def _finish(state: dict, result: dict) -> dict:
    """状态落盘（save_state 里顺带归档旧事件），并在返回给 Agent 的结果上标注当前 tick。"""
    save_state(state, _state_path())
    try:
        record_sample(_state_path(), state)   # 长局态势侧写（写 <state>.viz.jsonl，不碰状态文件）
    except Exception:  # nosec B110; aqg: top-level boundary —— 侧写是观测数据，任何异常都不许影响对局结算
        pass
    result["_tick"] = state.get("tick", 0)
    return result


def _seed_rng(state: dict) -> None:
    """确定性种子委托：见 state_schema.seed_rng（CLI 与 MCP 共用同一实现）。"""
    seed_rng(state)


def _codex(state: dict) -> dict:
    """探索图鉴：地点/人物/物品/设定词条。面板渲染它，也是"玩家记不住"的台账。"""
    c = state.setdefault("codex", {})
    for k in ("locations", "people", "items", "lore"):
        c.setdefault(k, [])
    return c


def _remember(state: dict, kind: str, value: str) -> bool:
    """记一条图鉴；返回是否首次见到。"""
    v = str(value or "").strip()
    if not v:
        return False
    lst = _codex(state)[kind]
    if v in lst:
        return False
    lst.append(v)
    if len(lst) > 200:
        del lst[0]
    return True


DEFAULT_CONFIG = {"event_log_keep": 200, "archive": True, "recap_budget_chars": 1500,
                  "summary_keep": 30, "milestone_keep": 200, "panel_port": 8765,
                  "karma_ledger_keep": 500, "stage_max": 20}


def _cfg(state: dict) -> dict:
    """对局配置（缺省值补齐；configure 工具可改）。"""
    c = state.setdefault("config", {})
    for k, v in DEFAULT_CONFIG.items():
        c.setdefault(k, v)
    return c


def _archive_path() -> str:
    return _state_path() + ".log.jsonl"


def _all_archive_files() -> list:
    """当前局的全部分代归档文件（`<state>.log.jsonl` + `<state>.log.<gen>.jsonl`）。

    按世代分文件后，回退旧快照不会删除任何历史；recall 要能跨世代回捞。
    """
    base = _state_path()
    out = []
    legacy = base + ".log.jsonl"
    if os.path.exists(legacy):
        out.append(legacy)
    import glob as _glob
    out.extend(sorted(_glob.glob(base + ".log.*.jsonl")))
    return out


def _milestone(state: dict, kind: str, desc: str) -> None:
    """记一条大事记（recap 与面板都用它；长局里"记住发生了什么"靠这个）。"""
    ms = state.setdefault("milestones", [])
    ms.append({"tick": state.get("tick", 0), "kind": kind, "desc": str(desc)[:200]})
    keep = int(_cfg(state).get("milestone_keep", 200))
    if len(ms) > keep:
        del ms[:len(ms) - keep]


def _require_entity(state: dict, entity_id: str, role: str) -> dict:
    ent = state.get("entities", {}).get(entity_id)
    if not ent:
        raise ValueError("%s不存在: %s（当前实体: %s）" % (role, entity_id, ", ".join(state.get("entities", {}))))
    return ent


def _normalize_entity(entity_id: str, raw: dict) -> dict:
    if not isinstance(raw, dict) or not raw.get("name"):
        raise ValueError("实体 %s 缺少 name" % entity_id)
    attrs = dict(raw.get("attrs") or {})
    for k in ATTR_KEYS:
        v = attrs.get(k, 10)
        if not isinstance(v, (int, float)):
            raise ValueError("实体 %s 的属性 %s 必须是数字" % (entity_id, k))
        attrs[k] = int(v)
    hp_max = int(raw.get("hp_max", 100))
    mp_max = int(raw.get("mp_max", 0))
    ent = {
        "name": str(raw["name"]),
        "faction": str(raw.get("faction", "")),
        "attrs": attrs,
        "hp": int(raw.get("hp", hp_max)),
        "hp_max": hp_max,
        "mp": int(raw.get("mp", mp_max)),
        "mp_max": mp_max,
        "level": str(raw.get("level", "凡人")),
        "gold": int(raw.get("gold", 0)),
        "location": str(raw.get("location", "")),
    }
    for extra in ("desc", "personality", "speech"):
        if raw.get(extra):
            ent[extra] = str(raw[extra])[:1200]
    if raw.get("skills"):
        ent["skills"] = list(raw["skills"])
    if raw.get("morality"):
        ent["morality"] = list(raw["morality"])[:6]
    items = raw.get("items")
    if items:
        cleaned = {}
        for k, v in dict(items).items():
            try:
                n = int(v)
            except (TypeError, ValueError):
                continue
            if n > 0:
                cleaned[str(k)] = n
        if cleaned:
            ent["items"] = cleaned
    return ent


@server.tool()
def world_schema() -> dict:
    """返回世界状态的数据结构说明（Chinese: 供 Agent 按玩家设定构造 world_init 入参）。
    Schema reference for building world_init arguments."""

    return {
        "state_fields": {
            "tick": "回合数（整数，引擎维护）",
            "rng_seed": "随机种子（整数，决定可复现性）",
            "world_info": {"name": "世界名", "era": "纪元", "location_desc": "开场地点描写"},
            "entities": "entity_id -> 实体对象（见 entity_shape）",
            "relations": "关系表，键为 'a:b'（字母序，引擎自动生成），值为 {affinity, respect}（-100~100）",
            "market": "location -> {item_key -> item_shape}；交易工具用 item_key 而非 name",
            "karma_ledger": "因果债流水（引擎维护）",
            "world_flags": "已触发的世界事件标记（字符串数组）",
            "ui": "面板皮肤与品牌（可选）{skin: xuanshu|neutral|ink|neon, accent: '#rrggbb', motif: 文案, brand: 字标, tagline: 标语}",
            "event_log": "最近事件（引擎维护，保留量见 config.event_log_keep，默认 200；溢出自动归档）",
        },
        "entity_shape": {
            "name": "显示名（必填）",
            "faction": "阵营/势力",
            "attrs": {"str": "力量", "dex": "敏捷", "int": "悟性/智力", "con": "体质", "cha": "魅力"},
            "hp": "当前生命", "hp_max": "生命上限",
            "mp": "当前内力/法力", "mp_max": "内力上限",
            "level": "境界/等级（如 '练气三层'、'一流高手'、'C-class'）",
            "gold": "钱财",
            "location": "所在地（需与 market 的 location 键一致才可交易）",
            "items": "{item_key: 数量} 随身物品（买入自动记入；卖出须持有）",
            "skills": "技能名数组（可选）",
            "morality": "六维道德向量（可选，默认 [0,0,0,0,0,0]）",
            "desc": "角色外观/背景文字（可选；add_character 从角色卡带入）",
            "personality": "性格文字（可选）",
            "speech": "口癖/语气示例（可选，来自卡的 mes_example）",
        },
        "lore": "世界书条目数组（keys/secondary_keys/content/selective/constant/order/enabled）；"
                "由 import_lorebook 或角色卡的 character_book 带入， narration_context 按关键词触发",
        "codex": "探索图鉴 {locations, people, items, lore}——引擎自动记录，open_panel 的面板会渲染它",
        "milestones": "大事记（突破/击杀/初次抵达/因果升级自动记；recap 与面板都读它）",
        "summaries": "章节摘要（write_summary 写入；长局靠「摘要+大事记+recall」三层记忆）",
        "config": "对局配置（event_log_keep/recap_budget_chars/summary_keep/milestone_keep/panel_port）",
        "currency": "货币名（默认「灵石」；设定包里给 currency=「玄晶」即全局生效）",
        "market_item_shape": {
            "name": "显示名（如 '安神丹'）", "price": "当前价", "supply": "库存",
            "base_price": "基准价（价格会回归它）", "type": "类别", "desc": "描述",
        },
        "world_init_args": {
            "state_path": "状态文件路径，默认 ww_state.json",
            "world": "{name, era, location_desc}",
            "player": "entity_shape（id 固定为 'player'）",
            "entities": "[{id, ...entity_shape}]，NPC 列表",
            "market": "[{location, items: [{key, ...market_item_shape}]}]",
            "relations": "[{a, b, affinity, respect}]（键由引擎按字母序生成）",
            "world_flags": "字符串数组（可选）",
            "ui": "{skin, accent, motif}（可选；面板皮肤，换世界风格用）",
            "seed": "整数种子（可选，默认 20261014）",
        },
        "action_tools": {
            "combat": "attacker/defender/action_type(attack|heavy|flee)/skill",
            "trade": "location/item_key/quantity/direction(buy|sell)/entity；买入记入持有，卖出须先持有",
            "social": "actor/target/event(%s)/intensity" % "|".join(SOCIAL_EVENTS),
            "karma": "actor/victim(可空)/karma_type(%s)" % "|".join(KARMA_TYPES),
            "tick": "回合结束（市场演化 + tick+1）",
            "narrative": "涌现事件 + 世界相位（每 3-5 回合查一次）",
            "status": "心流/身份/相位/道德/认知 聚合（每 3-5 回合查一次）",
            "merit": "功德值（纯函数：aid 救助 0~1, sincerity 诚心 0~1）",
            "narrative_weight": "事件叙事权重 = -log P(事件)（纯函数）",
            "model": "按命名闭式模型算效果：name=模型名（见 model_list）, params=模型参数；不写状态",
            "model_list": "列出模型层全部命名模型（公式/适用场景），先查再用 model",
            "narration_context": "叙事上下文包：触发设定 + 在场角色卡面 + 编年史（每回合调）",
            "character_card_read": "读角色卡（.png/.json，V1/V2/V3）",
            "add_character": "角色卡入局当 NPC（卡面进叙事层，卡内世界书并入）",
            "import_lorebook": "导入 SillyTavern world-info 世界书",
            "snapshot": "存快照（回退/分叉用）",
            "restore": "从快照恢复",
            "travel": "移动（唯一能改玩家 location 的工具；首次到达记图鉴）",
            "use_item": "用一件物品：持有则自备消耗（买入时已付）；未持有则按所在地市场价现买现用",
            "spawn_npc": "现场生成一个 NPC（无角色卡也能入局；有卡请用 add_character）",
            "open_panel": "打开实况主舞台（只读网页：叙事/HUD/时间线/抽屉，自动刷新）",
            "load_setting": "从设定包一键开一局（settings/*.setting.json）",
            "advance": "突破（引擎判定成败并给数值后果；长局的核心成长循环）",
            "recall": "按关键词回捞历史事件（归档 + 近期事件）",
            "write_summary": "写章节摘要（长局记忆；每 20-50 回合一次）",
            "recap": "回顾包：最新摘要 + 大事记 + 最近事件（按字符预算裁剪）",
            "configure": "查看/修改对局配置（归档保留量、摘要预算等）",
        },
    }


@server.tool()
def world_init(state_path: str, world: WorldInfo, player: EntityIn,
               entities: list[EntityIn] | None = None, market: list[MarketIn] | None = None,
               relations: list[RelationIn] | None = None, world_flags: list[str] | None = None,
               ui: dict | None = None,
               seed: int = 20261014) -> dict:
    """按玩家设定创建一局新游戏并写盘（Chinese: 设定 → 世界状态；创建后即成为当前对局。
    ui 可给面板皮肤：{"skin": "xuanshu|neutral|ink|neon", "accent": "#rrggbb", "motif": "自由文案"}）。
    Create a new game from the player's setting bible and make it the active session."""

    state_entities = {"player": _normalize_entity("player", player.model_dump(exclude_none=True))}
    for npc in entities or []:
        raw = npc.model_dump(exclude_none=True)
        eid = str(raw.get("id") or "").strip()
        if not eid:
            raise ValueError("entities 里每个 NPC 都必须有 id")
        if eid == "player":
            raise ValueError("entities 里不要重复定义 player")
        state_entities[eid] = _normalize_entity(eid, raw)

    state_market = {}
    for loc in market or []:
        items = {}
        for item in loc.items:
            d = item.model_dump(exclude_none=True)
            items[item.key] = {
                "name": d.get("name", item.key),
                "price": int(d.get("price", 50)),
                "supply": int(d.get("supply", 20)),
                "base_price": int(d.get("base_price", d.get("price", 50))),
                "type": str(d.get("type", "")),
                "desc": str(d.get("desc", "")),
            }
        state_market[loc.location] = items

    state_relations = {}
    for rel in relations or []:
        for eid in (rel.a, rel.b):
            if eid not in state_entities:
                raise ValueError("关系引用了不存在的实体: %s" % eid)
        state_relations[entity_key(rel.a, rel.b)] = {
            "affinity": int(rel.affinity),
            "respect": int(rel.respect),
        }

    state = {
        "tick": 0,
        "rng_seed": int(seed),
        "entities": state_entities,
        "relations": state_relations,
        "market": state_market,
        "karma_ledger": [],
        "world_flags": list(world_flags or []),
        "ui": dict(ui or {}),
        "event_log": [],
        "world_info": {
            "name": world.name,
            "era": world.era,
            "location_desc": world.location_desc,
        },
    }
    log_event(state, "system", "世界「%s」开局：%s" % (state["world_info"]["name"],
                                                  state["world_info"]["location_desc"] or "旅程开始"))

    _remember(state, "locations", state_entities["player"].get("location", ""))
    _active["path"] = os.path.abspath(state_path)
    save_state(state, _active["path"])
    return {
        "state_path": _active["path"],
        "world": state["world_info"]["name"],
        "entities": len(state["entities"]),
        "market_locations": sorted(state_market),
        "relations": len(state_relations),
        "seed": int(seed),
        "message": "世界已创建。玩家所在位置: %s" % state_entities["player"].get("location", ""),
    }


@server.tool()
def world_open(state_path: str) -> dict:
    """打开已有状态文件继续对局（Chinese: 断点续跑）。Resume a saved game state."""

    if not os.path.exists(state_path):
        raise ValueError("状态文件不存在: %s" % state_path)
    state = load_state(state_path)
    _active["path"] = os.path.abspath(state_path)
    return {
        "state_path": _active["path"],
        "tick": state.get("tick", 0),
        "world": (state.get("world_info") or {}).get("name", ""),
        "entities": sorted(state.get("entities", {})),
    }


@server.tool()
def read_state() -> dict:
    """返回当前对局的完整状态 JSON（Chinese: Agent 读它来决定调用哪个行动工具）。
    Full state of the active game."""

    return _load()


@server.tool()
def combat(attacker: str, defender: str, action_type: str = "attack",
           skill: dict | None = None) -> dict:
    """结算一次战斗（Chinese: action_type 取 attack|heavy|flee；skill 形如 {name, power, mp_cost}）。
    Resolve one combat exchange."""

    if action_type not in ("attack", "heavy", "flee"):
        raise ValueError("action_type 只能是 attack / heavy / flee")
    state = _load()
    _seed_rng(state)
    _require_entity(state, attacker, "攻击方")
    _require_entity(state, defender, "防守方")
    result = resolve_combat(state, attacker, defender, action_type, skill)
    for e in result.get("events", []):
        log_event(state, "combat", e)
    _remember(state, "people", state.get("entities", {}).get(defender, {}).get("name", defender))
    if result.get("defender_dead"):
        _milestone(state, "击杀", "%s 击败了 %s" % (attacker, result.get("defender", defender)))
    result["attacker_hp"] = state.get("entities", {}).get(attacker, {}).get("hp", 0)
    return _finish(state, result)


@server.tool()
def trade(location: str, item: str, direction: str, quantity: int = 1,
          entity: str = "player") -> dict:
    """结算一次交易（Chinese: item 传市场里的 item_key，不是显示名；direction 取 buy|sell。
    买入会记进持有（entity.items）；卖出必须先持有——卖自己没有的东西会被拒。
    Settle one trade at a market location (selling requires holding the goods)."""

    if direction not in ("buy", "sell"):
        raise ValueError("direction 只能是 buy / sell")
    state = _load()
    _seed_rng(state)
    _require_entity(state, entity, "交易方")
    if location not in state.get("market", {}):
        raise ValueError("此地没有市场: %s（可用: %s）" % (location, ", ".join(state.get("market", {}))))
    result = resolve_trade(state, location, item, int(quantity), direction == "buy", entity)
    for e in result.get("events", []):
        log_event(state, "trade", e)
    if result.get("success"):
        it = state.get("market", {}).get(location, {}).get(item) or {}
        _remember(state, "items", it.get("name", item))
    return _finish(state, result)


@server.tool(description="结算一次社交事件并更新关系：event 取 "
                       + "|".join(SOCIAL_EVENTS) + "，intensity 为强度倍率。Settle a social event.")
def social(actor: str, target: str, event: str, intensity: float = 1.0) -> dict:

    if event not in SOCIAL_EVENTS:
        raise ValueError("event 只能是: %s" % ", ".join(SOCIAL_EVENTS))
    state = _load()
    _seed_rng(state)
    _require_entity(state, actor, "发起方")
    _require_entity(state, target, "目标")
    result = resolve_social_event(state, actor, target, event, float(intensity))
    for e in result.get("events", []):
        log_event(state, "social", e)
    _remember(state, "people", state.get("entities", {}).get(target, {}).get("name", target))
    return _finish(state, result)


@server.tool(description="记录一次因果债：karma_type 取 " + "|".join(KARMA_TYPES)
                       + "，victim 可为空（无具体受害者时）。Record causal debt.")
def karma(actor: str, karma_type: str, victim: str | None = None) -> dict:

    if karma_type not in KARMA_TYPES:
        raise ValueError("karma_type 只能是: %s" % ", ".join(KARMA_TYPES))
    state = _load()
    _seed_rng(state)
    _require_entity(state, actor, "行动者")
    if victim:
        _require_entity(state, victim, "受害方")
    result = resolve_karma(state, actor, victim, karma_type)
    for e in result.get("events", []):
        log_event(state, "karma", e)
    consequence = get_karma_consequence(state, actor)
    if consequence["triggered"]:
        result["karma_consequence"] = consequence
        if consequence.get("type") in ("strong_pressure", "catastrophe"):
            _milestone(state, "因果", "业债累积触发「%s」" % consequence.get("desc", ""))
    return _finish(state, result)


@server.tool()
def tick() -> dict:
    """推进一个回合：市场演化 + tick+1（Chinese: 每回合结束时调用一次）。Advance one turn."""

    state = _load()
    _seed_rng(state)
    tick_market(state)
    state["tick"] = state.get("tick", 0) + 1
    log_event(state, "tick", "回合%d结束" % state["tick"])
    return _finish(state, {"events": ["回合%d结束" % state["tick"]]})


@server.tool()
def narrative() -> dict:
    """检查世界的涌现事件与相位（Chinese: 每 3-5 回合调用一次，用于埋设伏笔）。
    Emergent world events and the current world phase."""

    state = _load()
    _seed_rng(state)
    events = check_world_emergent_events(state)
    phase = panarchy_phase_check(state)
    for e in events:
        desc = e.get("desc") or e.get("type", "")
        log_event(state, "emergent", str(desc))
    return _finish(state, {"emergent_events": events, "panarchy_phase": phase})


@server.tool()
def status() -> dict:
    """聚合玩家的心理/身份/道德与世界相位（Chinese: 心流、Bartle 身份、六维道德、认知预算）。
    Aggregated insights: flow, identity, morality, world phase, cognition."""

    state = _load()
    _seed_rng(state)
    player = state.get("entities", {}).get("player", {})
    attrs = player.get("attrs", {})
    realm_level = int(attrs.get("int", 10) // 5)
    budget = daily_cognitive_budget(realm_level, "正常")
    return _finish(state, {
        "flow": flow_channel_status(state),
        "identity": player_identity_vector(state),
        "panarchy_phase": panarchy_phase_check(state),
        "moral_vector": update_player_moral_identity(state),
        "cognition": {
            "cognitive_budget": budget,
            "system2_likely": should_use_system2(budget, max(0.1, float(attrs.get("int", 10)) / 20)),
        },
        "unsettled_karma": sum(e["amount"] for e in state.get("karma_ledger", [])
                               if e["from"] == "player" and not e["settled"]),
        "latest_summary": ((state.get("summaries") or [{}])[-1].get("text", "")),
        "milestones": ["第%d回合·%s" % (m.get("tick", 0), m.get("desc", ""))
                       for m in state.get("milestones", [])[-6:]],
    })


@server.tool()
def merit(aid: float = 0.5, sincerity: float = 0.5) -> dict:
    """功德值（Chinese: 纯函数，aid=救助程度 0~1，sincerity=诚心 0~1）。
    Merit quality of an act (pure function)."""

    return {"merit_value": merit_quality(float(aid), float(sincerity))}


@server.tool()
def narrative_weight(probability: float) -> dict:
    """事件叙事权重 = 自信息量 -log P（Chinese: 纯函数；概率越低越值得浓墨重彩）。
    Narrative weight of an event (pure function)."""

    if not (0.0 < probability <= 1.0):
        raise ValueError("probability 必须在 (0, 1] 区间")
    return {"info_weight": event_information(float(probability))}


@server.tool()
def model(name: str, params: dict[str, float] | None = None) -> dict:
    """按命名闭式模型算效果（Chinese: 宿主不用自己推理——价格回归/势力消长/谣言传播/
    厄运概率/心境摆荡都在这里，传模型名+参数直接得数值结果）。
    Evaluate a named closed-form model (economics/population/epidemiology/probability/
    thermodynamics/opinion): model('lotka_volterra', {'prey': 8, 'predator': 3})."""

    res = _model_fn(name, **(params or {}))
    res["params"] = params or {}
    return res


@server.tool()
def model_list() -> dict:
    """列出全部可用命名模型（Chinese: 模型层目录——名字/公式/适用场景，先查再用 model 调）。
    List the named models available to the model tool."""

    return {"models": _model_names()}



@server.tool()
def character_card_read(path: str) -> dict:
    """读一张角色卡并返回要点（Chinese: .png 嵌卡或 .json，V1/V2/V3；不改状态，先看再决定要不要入局）。
    Inspect a SillyTavern-style character card (PNG or JSON)."""
    d, spec = _load_card(path)
    book = (d.get("character_book") or {}).get("entries") or []
    if isinstance(book, dict):
        book = list(book.values())
    return {
        "name": d.get("name"),
        "spec": spec,
        "description": (d.get("description") or "")[:600],
        "personality": (d.get("personality") or "")[:300],
        "scenario": (d.get("scenario") or "")[:300],
        "first_mes": (d.get("first_mes") or "")[:300],
        "tags": d.get("tags") or [],
        "creator": d.get("creator") or "",
        "book_entries": len(book),
    }


@server.tool()
def add_character(path: str, entity_id: str, attrs: dict[str, int] | None = None,
                  hp: int = 100, gold: int = 0, location: str = "", level: str = "凡人") -> dict:
    """把角色卡作为 NPC 加进当前对局（Chinese: 卡面文字进叙事层，卡内世界书并入状态）。
    Add a character card to the active game as an NPC."""
    state = _load()
    d, _spec = _load_card(path)
    if entity_id in state.get("entities", {}):
        raise ValueError("实体已存在: %s（换个 entity_id 或先 remove）" % entity_id)
    ent = _normalize_entity(entity_id, {
        "name": d.get("name"), "attrs": attrs or {}, "hp": hp, "hp_max": hp,
        "gold": gold, "location": location or state.get("entities", {}).get("player", {}).get("location", ""),
        "level": level,
        "desc": d.get("description") or "",
        "personality": d.get("personality") or "",
        "speech": d.get("mes_example") or "",
    })
    state.setdefault("entities", {})[entity_id] = ent
    book = (d.get("character_book") or {}).get("entries") or []
    if isinstance(book, dict):
        book = list(book.values())
    added = 0
    for e in book:
        n = _normalize_lore_entry(e)
        if n:
            state.setdefault("lore", []).append(n)
            added += 1
    _remember(state, "people", ent["name"])
    log_event(state, "system", "角色卡「%s」入局（%s），世界书 +%d 条" % (ent["name"], entity_id, added))
    return _finish(state, {"entity_id": entity_id, "name": ent["name"], "lore_added": added,
                           "entities": len(state["entities"])})


@server.tool()
def import_lorebook(path: str) -> dict:
    """导入世界书文件（Chinese: SillyTavern world-info JSON 或角色卡自带 book），并入当前对局。
    Import a world-info style lorebook into the active game."""
    state = _load()
    entries = _load_lorebook(path)
    state.setdefault("lore", []).extend(entries)
    log_event(state, "system", "导入世界书 %d 条" % len(entries))
    return _finish(state, {"imported": len(entries), "total": len(state["lore"])})


@server.tool()
def narration_context(scene_text: str = "", recent: int = 12) -> dict:
    """叙事上下文包：关键词触发的设定条目 + 在场角色的卡面文字 + 自动编年史（Chinese: 每回合都调一次，把这些织进描写）。
    Narration kit: triggered lore, on-scene cast (card prose), deterministic chronicle."""
    state = _load()
    player = state.get("entities", {}).get("player", {})
    text = scene_text or " ".join(
        [player.get("location", "")] + [e.get("name", "") for e in state.get("entities", {}).values()])
    lore = _trigger_lore(state.get("lore", []), text)
    for e in lore[:12]:
        _remember(state, "lore", e.get("comment") or e["content"][:24])
    loc = player.get("location", "")
    present = [{"id": k, "name": e.get("name"), "desc": e.get("desc", ""),
                "personality": e.get("personality", ""), "speech": e.get("speech", "")}
               for k, e in state.get("entities", {}).items()
               if k != "player" and (not loc or e.get("location") == loc)]
    return _finish(state, {
        "triggered_lore": [{"comment": e["comment"], "content": e["content"]} for e in lore[:12]],
        "lore_total": len(state.get("lore", [])),
        "present_cast": present[:8],
        "chronicle": [e.get("desc") for e in state.get("event_log", [])[-int(recent):] if e.get("desc")],
        "flags": state.get("world_flags", []),
        "unsettled_karma": sum(e["amount"] for e in state.get("karma_ledger", [])
                               if e["from"] == "player" and not e["settled"]),
        "latest_summary": ((state.get("summaries") or [{}])[-1].get("text", "")),
        "milestones": ["第%d回合·%s" % (m.get("tick", 0), m.get("desc", ""))
                       for m in state.get("milestones", [])[-6:]],
    })


@server.tool()
def advance(next_level: str, insight: float = 0.0) -> dict:
    """尝试突破（Chinese: 引擎按状态判定成败并给数值后果；next_level 是你按设定阶梯取的下一层名，
    insight 是你对"这次突破的叙事依据"打分 0~1——顿悟/点拨/生死一线才给高分）。
    Attempt a breakthrough: the engine decides success and applies the consequences."""
    state = _load()
    _seed_rng(state)
    player = state.get("entities", {}).get("player")
    if not player:
        raise ValueError("状态里没有 player")
    attrs = player.get("attrs", {})
    hp_max = max(1, int(player.get("hp_max", 1)))
    hp_ratio = float(player.get("hp", hp_max)) / hp_max
    flow = flow_channel_status(state).get("state")
    karma = sum(e.get("amount", 0) for e in state.get("karma_ledger", [])
                if e.get("from") == "player" and not e.get("settled"))
    penalty = 0.30 if karma >= 300 else 0.15 if karma >= 150 else 0.05 if karma >= 60 else 0.0
    base = 0.45 + 0.25 * max(0.0, min(1.0, float(insight))) + 0.15 * (hp_ratio - 0.5)
    base += 0.10 if flow == "flow" else (-0.10 if flow in ("anxiety", "boredom") else 0.0)
    chance = max(0.05, min(0.95, base - penalty))
    ok = random.random() < chance  # nosec B311 —— 游戏骰子，非密码学用途
    if ok:
        player["hp_max"] = int(hp_max * 1.12)
        player["hp"] = player["hp_max"]
        player["mp_max"] = int(int(player.get("mp_max", 0)) * 1.15)
        player["mp"] = player["mp_max"]
        for k in ATTR_KEYS:
            attrs[k] = int(attrs.get(k, 10)) + 1
        player["level"] = str(next_level)
        cap = int((state.get("config") or {}).get("stage_max", 20))
        old_stage = int(player.get("stage", 0))
        player["stage"] = old_stage + 1 if cap <= 0 else min(old_stage + 1, cap)
        log_event(state, "breakthrough", "突破至 %s" % next_level)
        _milestone(state, "突破", "突破至 %s（第 %d 次%s）" % (next_level, player["stage"],
                                                              "，已达设定上限" if cap > 0 and player["stage"] >= cap else ""))
    else:
        backlash = max(1, int(hp_max * 0.25))
        player["hp"] = max(1, int(player.get("hp", 1)) - backlash)
        player["mind_scars"] = int(player.get("mind_scars", 0)) + 1
        log_event(state, "breakthrough", "冲击 %s 失败，反噬 %d 点气血" % (next_level, backlash))
        _milestone(state, "突破失败", "冲击 %s 失败（心伤 +1）" % next_level)
    return _finish(state, {"success": ok, "chance": round(chance, 2), "level": player.get("level"),
                           "hp": player.get("hp"), "hp_max": player.get("hp_max"),
                           "mp_max": player.get("mp_max"), "mind_scars": player.get("mind_scars", 0),
                           "hint": "业债压成功率；心境不稳（焦虑/无聊）也会减成——先稳住，再冲。"})


@server.tool()
def recall(query: str, limit: int = 8) -> dict:
    """按关键词回捞历史事件（Chinese: 长局必备——玩家提到很久以前的事时，先把旧事找回来）。
    Keyword search over the event archive and the recent log."""
    q = str(query or "").strip()
    if not q:
        raise ValueError("query 不能为空")
    terms = [t.lower() for t in re.split(r"[\s,，、]+", q) if t]
    state = _load()
    from collections import deque
    tail = deque(maxlen=int(limit))
    archives = _all_archive_files()
    for path in archives:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except Exception:  # nosec B112 —— 归档文件可能有半行（进程被杀），跳过坏行继续
                    continue
                if any(t in str(e.get("desc", "")).lower() for t in terms):
                    tail.append(e)
    hits = list(tail)
    for e in state.get("event_log", []):
        if any(t in str(e.get("desc", "")).lower() for t in terms):
            hits.append(e)
    hits = sorted(hits, key=lambda x: int(x.get("tick", 0)), reverse=True)[:int(limit)]
    return {"query": q, "matches": hits, "archived_events": int(state.get("archived_events", 0)),
            "archive_file": _archive_path(), "archive_files": archives}


@server.tool()
def write_summary(text: str) -> dict:
    """写下这一段的摘要（Chinese: 长局记忆的核心——只写"变了什么"，三五句就够，别写流水账）。
    Store a chapter summary for long games."""
    state = _load()
    body = str(text or "").strip()
    if not body:
        raise ValueError("摘要不能为空")
    ss = state.setdefault("summaries", [])
    ss.append({"upto_tick": int(state.get("tick", 0)), "text": body[:1500]})
    keep = int(_cfg(state).get("summary_keep", 30))
    if len(ss) > keep:
        del ss[:len(ss) - keep]
    return _finish(state, {"summaries": len(ss), "upto_tick": ss[-1]["upto_tick"]})


@server.tool()
def recap(recent: int = 12, budget_chars: int = 0) -> dict:
    """长局回顾包（Chinese: 最新摘要 + 大事记 + 最近事件，按字符预算裁剪；接不上前文时先看它）。
    Long-game recap: latest summary + milestones + recent events, budgeted."""
    state = _load()
    cfg = _cfg(state)
    budget = int(budget_chars or cfg.get("recap_budget_chars", 1500))
    summaries = state.get("summaries") or []
    out = {"summary": (summaries[-1]["text"] if summaries else ""),
           "summary_upto_tick": (summaries[-1]["upto_tick"] if summaries else None),
           "milestones": [], "recent_events": [],
           "archived_events": int(state.get("archived_events", 0)),
           "lore_entries": len(state.get("lore", [])),
           "codex": {k: len(v) for k, v in (state.get("codex") or {}).items()}}
    used = len(out["summary"])
    for m in reversed(state.get("milestones", [])):
        s = "第%d回合·%s" % (m.get("tick", 0), m.get("desc", ""))
        if used + len(s) > budget:
            break
        out["milestones"].append(s)
        used += len(s)
    for e in list(reversed(state.get("event_log", [])))[:int(recent)]:
        s = "第%d回合·%s" % (e.get("tick", 0), e.get("desc", ""))
        if used + len(s) > budget:
            break
        out["recent_events"].append(s)
        used += len(s)
    out["budget_chars"] = budget
    out["used_chars"] = used
    return out


@server.tool()
def configure(event_log_keep: int | None = None, recap_budget_chars: int | None = None,
              summary_keep: int | None = None, milestone_keep: int | None = None,
              panel_port: int | None = None, currency: str | None = None) -> dict:
    """查看/修改对局配置（Chinese: 留空的项不改；返回当前全量配置。长局的存档/归档行为都在这里调）。
    View or update per-game config."""
    state = _load()
    cfg = _cfg(state)
    for key, val in (("event_log_keep", event_log_keep), ("recap_budget_chars", recap_budget_chars),
                     ("summary_keep", summary_keep), ("milestone_keep", milestone_keep),
                     ("panel_port", panel_port)):
        if val is not None:
            cfg[key] = int(val)
    if currency:
        state["currency"] = str(currency)
    return _finish(state, cfg)


@server.tool()
def load_setting(path: str, state_path: str = "", seed: int | None = None) -> dict:
    """从「设定包」一键开一局（Chinese: 包里含 world/player/entities/market/relations/lore，
    示例见 settings/玄枢界.setting.json，格式见 settings/README.md）。
    Boot a full game from a setting bundle in one call."""
    b = json.load(open(path, encoding="utf-8"))
    if not isinstance(b, dict) or "world" not in b or "player" not in b:
        raise ValueError("不是合法的设定包（缺 world/player）: %s" % path)
    sp = state_path or b.get("state_path_hint") or "ww_state.json"
    res = world_init(state_path=sp,
                     world=WorldInfo(**b["world"]),
                     player=EntityIn(**b["player"]),
                     entities=[EntityIn(**e) for e in b.get("entities", [])],
                     market=[MarketIn(**m) for m in b.get("market", [])],
                     relations=[RelationIn(**r) for r in b.get("relations", [])],
                     world_flags=list(b.get("world_flags", [])),
                     ui=dict(b.get("ui") or {}),
                     seed=int(seed if seed is not None else b.get("seed", 20261014)))
    if b.get("currency"):
        state = _load()
        state["currency"] = str(b["currency"])
        _finish(state, {})
    lore_n = 0
    if b.get("lore"):
        state = _load()
        for e in b["lore"]:
            n = _normalize_lore_entry(e)
            if n:
                state.setdefault("lore", []).append(n)
                lore_n += 1
        log_event(state, "system", "设定包「%s」载入：世界书 %d 条" % (b.get("name", ""), lore_n))
        _finish(state, {})
    return {**res, "setting": b.get("name", ""), "lore_entries": lore_n,
            "player_level": (b.get("player") or {}).get("level", ""),
            "hint": "开局前可先 open_panel 把实况主舞台给玩家；行动用 combat/trade/social/karma 结算，移动用 travel。"}


@server.tool()
def travel(location: str, note: str = "") -> dict:
    """移动到新地点（Chinese: 玩家的 location 只由本工具修改；首次到达会记进探索图鉴）。
    Move the player to a location; first arrival is recorded in the codex."""
    state = _load()
    player = state.get("entities", {}).get("player")
    if not player:
        raise ValueError("状态里没有 player")
    loc = str(location).strip()
    if not loc:
        raise ValueError("location 不能为空")
    known = (set(state.get("market", {}))
             | {e.get("location", "") for k, e in state.get("entities", {}).items() if k != "player"})
    first = _remember(state, "locations", loc)
    player["location"] = loc
    here = [k for k, e in state.get("entities", {}).items() if k != "player" and e.get("location") == loc]
    for k in here:
        _remember(state, "people", state["entities"][k].get("name", k))
    log_event(state, "travel", "抵达「%s」%s%s" % (loc, "（初次探索）" if first else "",
                                                  ("：" + note) if note else ""))
    if first:
        _milestone(state, "探索", "初次抵达「%s」" % loc)
    return _finish(state, {"location": loc, "first_time": first,
                           "has_market": loc in state.get("market", {}),
                           "entities_here": here,
                           "in_setting": loc in known})


@server.tool()
def open_panel(port: int = 8765) -> dict:
    """打开实况主舞台（Chinese: 只读网页——叙事主舞台/HUD/事件时间线/分级弹窗与提示/图鉴/行情，
    状态一变自动刷新，缺档给可读横幅）。
    Open the read-only live stage (auto-refreshing web view of the game state)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("ww_panel", os.path.join(_SCRIPT_DIR, "panel.py"))
    panel = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(panel)
    srv, actual = panel.start(_state_path(), port)
    PANELS["server"] = srv
    return {"url": "http://127.0.0.1:%d/" % actual, "port": actual,
            "state": _state_path(), "note": "面板只读；状态一变就推新数据"}


@server.tool()
def use_item(item: str, quantity: int = 1, location: str = "") -> dict:
    """使用一件物品（Chinese: 买过就记在随身（items）里，用自备的不再扣钱；没买过则当"现买现用"，
    按所在地市场价结算——丹药回气血，其余类目收而备用。花的是钱，不是白拿）。
    Consume an owned item for free, or buy-and-use at the local market when not owned."""
    state = _load()
    _seed_rng(state)
    p = state.get("entities", {}).get("player")
    if not p:
        raise ValueError("状态里没有 player")
    qty = max(1, int(quantity))
    cur = state.get("currency", "灵石")
    inv = p.get("items")
    if not isinstance(inv, dict):
        inv = p["items"] = {}
    owned = int(inv.get(item, 0))
    mkt_any = next((v for mk in state.get("market", {}).values()
                    for k, v in mk.items() if k == item), None)
    if owned >= qty:
        inv[item] = owned - qty
        if inv[item] <= 0:
            del inv[item]
        price, source = 0, "自备"
        it = mkt_any or {}
    else:
        loc = str(location or p.get("location", "")).strip()
        mkt = state.get("market", {}).get(loc)
        if not mkt or item not in mkt:
            raise ValueError("此地没有「%s」，也未持有「%s」（所在地: %s）" % (item, item, loc or "未知"))
        it = mkt[item]
        if int(it.get("supply", 0)) < qty:
            raise ValueError("库存不足：「%s」只剩 %d" % (item, int(it.get("supply", 0))))
        price = int(it.get("price", 0)) * qty
        if p.get("gold", 0) < price:
            raise ValueError("%s不足：需要%d，只有%d" % (cur, price, p.get("gold", 0)))
        p["gold"] -= price
        it["supply"] = int(it.get("supply", 0)) - qty
        source = "现买现用"
    t = str(it.get("type", ""))
    name = it.get("name", item)
    unit = int(it.get("price", 0)) or 50
    if "丹药" in t or "药" in t:
        heal = max(8, unit * qty // 5)
        p["hp"] = min(int(p.get("hp_max", 100)), int(p.get("hp", 0)) + heal)
        effect = "回复%d气血" % heal
    elif "玄器" in t:
        effect = "检视一过（玄器要养，暂无即时效果）"
    else:
        effect = "收而备用"
    pay = ("花费%d%s" % (price, cur)) if price else "自备（买入时已付）"
    log_event(state, "use_item", "使用%s×%d（%s）：%s" % (name, qty, pay, effect))
    _remember(state, "items", name)
    return _finish(state, {"item": item, "used": qty, "cost": price, "currency": cur,
                           "source": source, "items_after": int(inv.get(item, 0)),
                           "effect": effect, "hp": p["hp"], "hp_max": p.get("hp_max", 0),
                           "gold": p["gold"]})


@server.tool()
def spawn_npc(id: str, name: str, faction: str = "", attrs: dict[str, int] | None = None,
              level: str = "凡人", hp: int = 60, gold: int = 0, location: str = "",
              desc: str = "", personality: str = "") -> dict:
    """现场生成一个 NPC（Chinese: 自由游玩时"新人物进场"就用它——没有卡文件也能入局；
              有角色卡请用 add_character。新人自动进探索图鉴）。
    Spawn a freeform NPC into the active game (no card file needed)."""
    state = _load()
    eid = str(id or "").strip()
    if not eid or not str(name or "").strip():
        raise ValueError("id 与 name 必填")
    if eid in state.get("entities", {}):
        raise ValueError("实体已存在: %s（换个 id）" % eid)
    ent = _normalize_entity(eid, {
        "name": name, "faction": faction, "attrs": attrs or {}, "hp": hp, "hp_max": hp,
        "gold": gold, "location": location or state.get("entities", {}).get("player", {}).get("location", ""),
        "level": level, "desc": desc, "personality": personality,
    })
    state.setdefault("entities", {})[eid] = ent
    _remember(state, "people", ent["name"])
    log_event(state, "system", "新人入局：%s（%s，%s）" % (name, eid, ent["location"]))
    return _finish(state, {"entity_id": eid, "name": name, "entities": len(state["entities"]),
                           "location": ent["location"]})


@server.tool()
def snapshot(label: str = "") -> dict:
    """把当前状态存一个快照（Chinese: 回退/分叉剧情用；状态本身确定性，所以回退是干净的）。
    Save a state snapshot (for undo / branching)."""
    import shutil, time
    src = _state_path()
    suffix = (".%s" % label) if label else (".%d" % int(time.time()))
    dst = src + ".snap" + suffix
    shutil.copyfile(src, dst)
    return {"snapshot": dst, "tick": load_state(src).get("tick", 0)}


@server.tool()
def restore(snapshot_path: str) -> dict:
    """从快照恢复状态（Chinese: 回退到某个存档点）。Restore state from a snapshot."""
    if not os.path.exists(snapshot_path):
        raise ValueError("快照不存在: %s" % snapshot_path)
    state = load_state(snapshot_path)
    # 回退到一个分叉点：后续归档写进新世代文件，不覆盖也不删除既有归档。
    # 同时把 archived_events 校正为"所有世代归档文件的实际行数之和"——
    # 归档是只增不减的总账，回退分支不该让它变小。
    current = _load()
    gen = max(int(state.get("archive_generation", 0) or 0),
              int(current.get("archive_generation", 0) or 0)) + 1
    state["archive_generation"] = gen
    total = 0
    for af in _all_archive_files():
        try:
            total += sum(1 for _ in open(af, encoding="utf-8"))
        except OSError:
            pass
    state["archived_events"] = max(int(state.get("archived_events", 0) or 0), total)
    save_state(state, _state_path())
    return {"restored": snapshot_path, "tick": state.get("tick", 0),
            "entities": sorted(state.get("entities", {})),
            "archive_generation": state["archive_generation"]}


def main() -> None:
    server.run("stdio")


if __name__ == "__main__":
    main()
