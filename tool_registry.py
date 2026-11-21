"""The 28 player tools exposed to an OpenAI-compatible model.

Every tool is a thin, named intent over GameService.  Old MCP names stay
available to hosts, but the model only sees the new surface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from game_engine.game_service import GameService


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict
    handler: Callable


def _params(**props) -> dict:
    return {"type": "object", "properties": props, "additionalProperties": True}


def _str(desc: str) -> dict:
    return {"type": "string", "description": desc}


def _int(desc: str) -> dict:
    return {"type": "integer", "description": desc}


def _num(desc: str) -> dict:
    return {"type": "number", "description": desc}


def _bool(desc: str) -> dict:
    return {"type": "boolean", "description": desc}


def build_specs(svc: GameService) -> list[ToolSpec]:
    return [
        ToolSpec(
            "inspect",
            "读取当前局面。view=status 看全局摘要；state 看完整状态；world 看势力/谣言/市场；"
            "progress 看玩法与事业线；memory 看最近摘要。需要精确数值时先查这里。",
            _params(view={"type": "string", "enum": ["status", "state", "world", "progress", "memory"]}),
            svc.inspect,
        ),
        ToolSpec(
            "progress",
            "查看或推进目标。action=status 看当前阶段/失败钟；advance 手动完成一幕；"
            "failure 推进失败钟。不要把玩家没做到的事标记为完成。",
            _params(action={"type": "string", "enum": ["status", "advance", "failure"]},
                    quest=_str("事业线 id"), stage=_str("完成的阶段 id"),
                    note=_str("一句话说明"), amount=_int("失败钟推进量"), reason=_str("原因")),
            svc.progress,
        ),
        ToolSpec(
            "story",
            "发布本回合正文（action=publish），或读取世界的涌现事件（action=narrative）。"
            "正文只写玩家看到的文学描写，数值仍由其他工具结算。",
            _params(action={"type": "string", "enum": ["publish", "narrative"]},
                    text=_str("正文，2-4 段"), location=_str("地点；不填用玩家当前位置")),
            svc.story,
        ),
        ToolSpec(
            "memory",
            "长局记忆。recap 回顾；search 搜旧事件；summary 写摘要；remember 记事实；"
            "known 查某角色知道什么；tell 转告；search_facts 搜事实台账；forget 结案/删除。",
            _params(action={"type": "string", "enum": ["recap", "search", "summary", "remember",
                                                       "known", "tell", "search_facts", "forget"]},
                    query=_str("关键词"), text=_str("摘要或事实正文"), fact_id=_str("事实 id"),
                    to=_str("转告对象"), how=_str("told/overheard/rumored/witnessed"),
                    keys={"type": "array", "items": {"type": "string"}},
                    kind=_str("事实类型"), status=_str("open/done/expired"),
                    character=_str("角色 id"), limit=_int("条数上限"), recent=_int("回顾事件数")),
            svc.memory,
        ),
        ToolSpec(
            "context",
            "给本回合准备上下文。pack 按预算拼玩法/事实/场景/事件；narrate 取触发的世界书与在场角色；"
            "lookup 只查触发；import 导入世界书文件。",
            _params(action={"type": "string", "enum": ["pack", "narrate", "lookup", "import"]},
                    scene_text=_str("当下场景文字"), recent=_int("最近事件数"),
                    budget_chars=_int("字符预算"), text=_str("要查触发的文字"),
                    path=_str("世界书文件路径")),
            svc.context,
        ),
        ToolSpec(
            "canon",
            "世界圣经。brief 先读本回合根设定/已揭示事实/迷雾；check 检查新事实是否冲突；"
            "commit 把探索到的新事实入账；init 自建世界时建立根设定。"
            "每回合先 brief；正文里出现新地点/新历史/新关系后，先 check 再 commit。",
            _params(action={"type": "string", "enum": ["brief", "check", "commit", "init"]},
                    scene_text=_str("当下场景文字"), limit=_int("条数"),
                    facts={"type": "array", "items": {"type": "object"}},
                    status=_str("immutable/revealed/rumor"), source=_str("来源"),
                    allow_override=_bool("是否显式改根设定"), reason=_str("override 理由"),
                    bible={"type": "object"}),
            svc.canon,
        ),
        ToolSpec(
            "characters",
            "角色卡与 NPC。read 先看卡；add 把卡加入当前局；spawn 现场生成一个新 NPC。"
            "新人物进场优先 spawn；有卡文件才用 add。",
            _params(action={"type": "string", "enum": ["read", "add", "spawn"]},
                    path=_str("角色卡路径"), entity_id=_str("实体 id"), id=_str("实体 id（spawn）"),
                    name=_str("显示名"), faction=_str("阵营"), desc=_str("外观/背景"),
                    personality=_str("性格"), location=_str("所在地"), level=_str("境界/等级"),
                    hp=_int("生命"), gold=_int("钱财"), attrs={"type": "object"},
                    activity=_str("现在在做什么"), intent=_str("下一步打算"), mood=_str("情绪"),
                    routine=_str("日常作息"), status=_str("idle/忙碌/受伤/失踪等"),
                    agenda=_str("长期目标/动机"), aliases={"type": "array", "items": {"type": "string"}}),
            svc.characters,
        ),
        ToolSpec(
            "knowledge",
            "对局知识库。search 跨角色卡/世界书/canon/事实/事件/地点/关系检索；"
            "character 查看 NPC 的位置/活动/知道什么/关系/角色卡；graph 看关系网；"
            "who_knows 查谁知道某事实；pack 按字符预算取精简知识；audit 体检悬空引用/重复条目。"
            "update_character 写回 NPC 的 activity/intent/mood/status/location/agenda/aliases；"
            "worldbook_add 运行时写入世界书；timeline_add 记时间线（可带 thread/causes）。"
            "对话里问到 NPC 近况或旧事时优先 search/character，不要凭记忆编。",
            _params(action={"type": "string", "enum": ["search", "stats", "pack", "graph", "who_knows",
                                                       "audit", "character", "update_character",
                                                       "worldbook_add", "timeline_add", "sync"]},
                    query=_str("检索词"), kind=_str("character/worldbook/canon/fact/event/place/relation/summary"),
                    name=_str("角色 id/显示名/别名"), fields={"type": "object"},
                    title=_str("世界书条目标题"), keys={"type": "array", "items": {"type": "string"}},
                    secondary_keys={"type": "array", "items": {"type": "string"}},
                    content=_str("世界书正文"), scope=_str("session/world"),
                    text=_str("时间线正文"), actors={"type": "array", "items": {"type": "string"}},
                    location=_str("地点"), story_time=_str("故事内时间"),
                    fact_id=_str("事实 id（who_knows）"), thread=_str("剧情线/线索名"),
                    causes={"type": "array", "items": {"type": "string"}},
                    budget_chars=_int("pack 字符预算"), depth=_int("graph 深度 1-2"), limit=_int("条数")),
            svc.knowledge,
        ),
        ToolSpec(
            "sheet",
            "通用游戏档案。profile 读/设属性资源进度轨；adjust 调一个值；tag 增删世界标签；"
            "sheet 设自由表格字段。题材无关，任何游戏都能用。",
            _params(action={"type": "string", "enum": ["profile", "adjust", "tag", "sheet"]},
                    profile={"type": "object"}, key=_str("字段名"), kind=_str("resources/attributes/meters"),
                    delta=_num("增量"), value=_num("目标值"), tag=_str("标签"),
                    remove=_bool("删除"), fields={"type": "object"}),
            svc.sheet,
        ),
        ToolSpec(
            "systems",
            "可插拔体系。schema 查结构；define 定义；run 执行（time/loot/craft/reputation/achievement/progression/custom）；"
            "status 查看；remove 删除。",
            _params(action={"type": "string", "enum": ["schema", "define", "run", "status", "remove"]},
                    system={"type": "object"}, replace=_bool("同名覆盖"),
                    system_id=_str("体系 id"), run_action=_str("体系动作"), params={"type": "object"}),
            svc.systems,
        ),
        ToolSpec(
            "worlds",
            "世界内容包。schema 查世界结构；list 列模板；info 看模板；apply 把模板转成设定包（不落盘）。",
            _params(action={"type": "string", "enum": ["schema", "list", "info", "apply"]},
                    template=_str("模板 id"), overrides={"type": "object"},
                    name=_str("世界名"), player_name=_str("主角名")),
            svc.worlds,
        ),
        ToolSpec(
            "calc",
            "命名公式与纯函数。models 列目录；model 算一个闭式模型；merit 算功德；weight 算叙事权重。"
            "需要精确数值时用，不要心算。",
            _params(action={"type": "string", "enum": ["models", "model", "merit", "weight"]},
                    name=_str("模型名"), params={"type": "object"},
                    aid=_num("救助程度 0-1"), sincerity=_num("诚心 0-1"),
                    probability=_num("概率 0-1")),
            svc.calc,
        ),
        ToolSpec(
            "panel",
            "实况面板。pending 取玩家在旧队列里的行动；open/close 启停只读面板。"
            "内置对话模式不需要 open，除非玩家明确要一个旁观页。",
            _params(action={"type": "string", "enum": ["pending", "open", "close"]},
                    limit=_int("条数"), mark_done=_bool("标记已处理"), port=_int("端口")),
            svc.panel,
        ),
        ToolSpec(
            "new_game",
            "建一局新游戏并存进存档库。setting_path 是设定包，template 是模板 id；二选一。",
            _params(name=_str("局名"), setting_path=_str("设定包路径"), template=_str("模板 id"),
                    seed=_int("随机种子"), player_name=_str("主角名")),
            svc.new_game,
        ),
        ToolSpec(
            "open_game",
            "打开一局。path 是存档路径，name 是存档名；二选一。",
            _params(path=_str("状态文件路径"), name=_str("存档名")),
            svc.open_game,
        ),
        ToolSpec(
            "saves",
            "存档库。action=list 列出；manage 归档/回收站/还原/清空；import 导入外部状态。",
            _params(action={"type": "string", "enum": ["list", "manage", "import"]},
                    include_trash=_bool("含回收站"), manage_action=_str("archive/trash/restore/purge"),
                    name=_str("存档名"), path=_str("外部状态路径"), overwrite=_bool("覆盖同名")),
            svc.saves,
        ),
        ToolSpec(
            "snapshot",
            "快照。action=create 存点；restore 回退；list 列出。回退是干净的分叉，不改随机序列。",
            _params(action={"type": "string", "enum": ["create", "restore", "list"]},
                    label=_str("标签"), snapshot_path=_str("快照路径")),
            svc.snapshot,
        ),
        ToolSpec(
            "combat",
            "结算一次战斗。attacker/defender 用实体 id；action_type=attack/heavy/flee；"
            "skill 可给 {name, power, mp_cost}。不要自己算命中/伤害。",
            _params(attacker=_str("攻击方 id"), defender=_str("防守方 id"),
                    action_type={"type": "string", "enum": ["attack", "heavy", "flee"]},
                    skill={"type": "object"}),
            svc.combat,
        ),
        ToolSpec(
            "combat_preview",
            "战前推演，只读，不改状态。给玩家风险提示时用。",
            _params(attacker=_str("攻击方 id"), defender=_str("防守方 id"),
                    action_type={"type": "string", "enum": ["attack", "heavy", "flee"]}),
            svc.combat_preview,
        ),
        ToolSpec(
            "trade",
            "在地点市场买卖。item 是商品 key；direction=buy/sell；卖出必须持有。",
            _params(location=_str("地点"), item=_str("商品 key"),
                    direction={"type": "string", "enum": ["buy", "sell"]},
                    quantity=_int("数量"), entity=_str("交易者 id，默认 player")),
            svc.trade,
        ),
        ToolSpec(
            "social",
            "结算一次人情互动。event 取引擎支持的事件名；intensity 0.5-2。",
            _params(actor=_str("发起者 id"), target=_str("对象 id"), event=_str("事件名"),
                    intensity=_num("强度")),
            svc.social,
        ),
        ToolSpec(
            "karma",
            "结算一次因果/业债。karma_type 取引擎支持的类型；victim 可选。",
            _params(actor=_str("行为者 id"), karma_type=_str("因果类型"), victim=_str("受害者 id")),
            svc.karma,
        ),
        ToolSpec(
            "campaign",
            "场景驱动的战役循环。brief 取本场契约（目标/障碍/压力/线索/代价）；"
            "open 开一场；resolve 用 yes / yes-but / no-and 结算并付代价；clock 推压力钟；journal 看玩家台账。"
            "一回合 = 一场戏；不要用 tick 或“过了一天”代替场景。",
            _params(action={"type": "string", "enum": ["brief", "open", "resolve", "clock", "journal"]},
                    title=_str("本场标题"), goal=_str("本场目标"), obstacle=_str("谁/什么在阻止"),
                    pressure=_str("哪只钟会因拖延前进"), clue=_str("本场最多揭示的一条线索"),
                    cost=_str("无论成败的代价"), act_id=_str("幕 id"),
                    choices={"type": "array", "items": {"type": "string"}},
                    outcome={"type": "string", "enum": ["yes", "yes-but", "no-and"]},
                    note=_str("结果说明"), clocks={"type": "array", "items": {"type": "object"}},
                    name=_str("钟名"), delta=_int("钟变化量"), reason=_str("原因")),
            svc.campaign,
        ),
        ToolSpec("advance", "尝试突破。next_level 是设定里的下一层名；insight 0-1 表示叙事依据强弱。",
                 _params(next_level=_str("下一层名"), insight=_num("顿悟程度")), svc.advance),
        ToolSpec("travel", "移动玩家。只有它改玩家 location；首次到达自动进图鉴。desc 给一句场景描写。",
                 _params(location=_str("地点"), note=_str("备注"), desc=_str("场景描写")), svc.travel),
        ToolSpec("use_item", "使用一件物品。持有则免费，未持有则按当地市价现买现用。",
                 _params(item=_str("商品 key"), quantity=_int("数量"), location=_str("地点")), svc.use_item),
        ToolSpec(
            "roll",
            "通用判定。dice 支持 d20/2d6/3d6/d100/4dF/pool；mode=add/roll_under/pool/fate；"
            "可给属性、难度、修正、对抗对象。",
            _params(attribute=_str("属性名"), difficulty=_int("难度"), dice=_str("骰型"),
                    mode=_str("判定模式"), modifiers={"type": "array"}, actor=_str("角色 id"),
                    opposed_by=_str("对抗对象"), pool_size=_int("骰池数量"), reason=_str("原因")),
            svc.roll,
        ),
        ToolSpec(
            "configure",
            "调整这一局的运行参数：事件日志长度、摘要预算、市场波动、世界书递归/扫描深度等。",
            _params(event_log_keep=_int("事件日志保留"), recap_budget_chars=_int("回顾预算"),
                    summary_keep=_int("摘要保留"), milestone_keep=_int("大事记保留"),
                    panel_port=_int("面板端口"), currency=_str("货币名"),
                    market_jitter=_bool("市场波动"), lore_recursion=_int("世界书递归"),
                    lore_scan_depth=_int("世界书扫描深度")),
            svc.configure,
        ),
    ]


class ToolRegistry:
    def __init__(self, state_path: str):
        self.svc = GameService(state_path)
        self.specs = build_specs(self.svc)

    def as_openai(self) -> list[dict]:
        return [
            {"type": "function", "function": {
                "name": s.name, "description": s.description, "parameters": s.parameters}}
            for s in self.specs
        ]

    def execute(self, name: str, arguments: dict | None) -> dict:
        spec = next((s for s in self.specs if s.name == name), None)
        if spec is None:
            return {"ok": False, "error": "未知工具：%s" % name}
        args = arguments if isinstance(arguments, dict) else {}
        try:
            return spec.handler(**args)
        except TypeError as exc:
            return {"ok": False, "error": "参数不对：%s" % str(exc)[:180]}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)[:240]}
