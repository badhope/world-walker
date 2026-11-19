"""
游戏模板库 (Templates) —— 开箱即用的完整游戏骨架

为什么需要：`settings/` 里的四套设定包是"完整示例"，但它们体量大、绑定特定世界观。
做一个新游戏时，真正需要的是**起点**：这套模板给出世界/角色/属性/资源/进度轨/玩法循环/
事业线/世界书/地点/市场/术语/体系，全部填好，改几个词就能玩。

模板分两层：
  · `GAME_TEMPLATES`：单文件模板（纯 Python dict），覆盖主流题材，随包分发、无需读盘；
  · `load(name)`：深拷贝 + 可选覆盖（overrides），返回可直接交给 build_state 的 bundle。

每个模板都通过 `validate()` 的结构校验（`scripts/verify_systems.py` 逐项断言），
保证"模板不缺基础件"——这是本层的核心承诺。
"""

import copy
import hashlib

MAX_TEMPLATES = 40


def _pack(tid, name, genre, loop, **kw):
    """构造一个标准模板（统一字段顺序与默认值）。"""
    base = {
        "id": tid,
        "name": name,
        "genre": genre,
        "loop": loop,
        "world": {},
        "player": {},
        "entities": [],
        "market": [],
        "relations": [],
        "world_flags": [],
        "level_tiers": [],
        "terms": {},
        "places": {},
        "lore": [],
        "currency": "金币",
        "ui": {},
        "playbook": {},
        "questlines": [],
        "systems": [],
        "game": {},
        "world_bible": {},
        "map_blueprint": {},
        "notes": "",
    }
    base.update(kw)
    return base


# ────────────────────────────── 模板定义 ──────────────────────────────

_JRPG = _pack(
    "jrpg", "日式奇幻冒险", "奇幻 / 成长", "freeform",
    notes="经典少年成长线：接受委托 → 探索 → 战斗 → 升级 → 揭开更大的阴谋。",
    world={"name": "艾瑟兰", "era": "王国历 412 年",
           "location_desc": "边境小镇洛恩的清晨，铁匠铺刚升起第一缕烟。冒险者公会的告示板上钉着一张新委托。"},
    player={"name": "旅人", "faction": "无", "level": "见习",
            "attrs": {"str": 10, "dex": 11, "int": 9, "con": 10, "cha": 10},
            "hp": 30, "hp_max": 30, "mp": 10, "mp_max": 10, "gold": 40,
            "location": "洛恩镇",
            "skills": ["基础剑术"], "items": {"potion": 2}},
    entities=[
        {"id": "guildmaster", "name": "公会会长 格雷", "faction": "冒险者公会",
         "level": "退役老兵", "attrs": {"str": 12, "dex": 9, "int": 11, "con": 12, "cha": 13},
         "hp": 40, "hp_max": 40, "gold": 200, "location": "洛恩镇",
         "desc": "左脸有一道旧疤，说话像在点兵。", "personality": "寡言、护短",
         "speech": "「活着回来，比什么委托都值钱。」"},
        {"id": "smith", "name": "铁匠 玛莎", "faction": "工匠行会",
         "level": "匠师", "attrs": {"str": 14, "dex": 8, "int": 10, "con": 13, "cha": 9},
         "hp": 35, "hp_max": 35, "gold": 120, "location": "洛恩镇",
         "desc": "手臂比寻常男人还粗，围裙上全是烫痕。", "personality": "直率",
         "speech": "「东西可以赊，命不能。」"},
    ],
    market=[{"location": "洛恩镇", "items": [
        {"key": "potion", "name": "治疗药水", "price": 12, "supply": 20, "base_price": 12, "type": "药品",
         "desc": "回复 20 点生命。"},
        {"key": "bread", "name": "干粮", "price": 3, "supply": 30, "base_price": 3, "type": "食物"},
        {"key": "dagger", "name": "短剑", "price": 35, "supply": 5, "base_price": 35, "type": "武器"},
    ]}],
    relations=[{"a": "player", "b": "guildmaster", "affinity": 10, "respect": 15}],
    level_tiers=["见习", "铜级", "银级", "金级", "白金", "传说"],
    terms={"hero": "冒险者", "level": "等级", "hp": "生命", "mp": "魔力", "gold": "金币",
           "track": "公会阶", "territory": "足迹", "inventory": "行囊", "codex": "见闻录"},
    places={
        "洛恩镇": {"desc": "边境小镇，木屋沿河而建，公会旗在风里响。",
                   "market": "洛恩镇"},
        "灰狼林": {"desc": "林间有新鲜爪印，鸟声突然断了。", "market": ""},
        "废弃哨塔": {"desc": "塔顶塌了一角，风穿过箭孔发出低鸣。", "market": ""},
    },
    currency="金币",
    ui={"skin": "neutral", "accent": "#d9a441", "motif": "奇幻·边境", "brand": "艾瑟兰",
        "tagline": "委托与远方"},
    playbook={"loop": "freeform", "input": "natural",
              "progress": {"axis": "level", "label": "公会阶", "max": 5},
              "failure": {"mode": "hp", "label": "重伤撤退", "max": 0},
              "beat": {"pattern": ["日常", "接委托", "路上", "交锋", "结算"], "every": 5},
              "settlement": ["combat", "trade", "social", "karma", "roll"],
              "context": {"inject": ["lore", "cast", "chronicle"], "max_lore": 10, "scan_depth": 2}},
    questlines=[{
        "id": "wolf_forest", "title": "灰狼林的爪印", "summary": "最近三支商队都没能穿过灰狼林。",
        "visibility": {"flag": "__start__"},
        "stages": [
            {"id": "accept", "title": "接下委托", "objectives": ["去找公会会长确认细节"],
             "exit_if": {"flag": "accepted_wolf"}, "next": ["track"]},
            {"id": "track", "title": "追踪", "objectives": ["在林中找到爪印的来源"],
             "exit_if": {"visited": "灰狼林"}, "next": ["tower"]},
            {"id": "tower", "title": "哨塔", "objectives": ["查明哨塔里的东西"], "next": []},
        ],
        "reward": {"gold": 120, "flags": ["wolf_forest_cleared"]},
    }],
    systems=[
        {"id": "clock", "kind": "time", "label": "时间",
         "config": {"start": {"day": 1, "hour": 7}, "days_per_season": 30}},
        {"id": "drops_wolf", "kind": "loot", "label": "灰狼掉落",
         "config": {"tables": {"wolf": {"rolls": 2, "entries": [
             {"item": "pelt", "name": "狼皮", "weight": 60, "qty": [1, 2]},
             {"item": "fang", "name": "狼牙", "weight": 30, "qty": [1, 1]},
             {"item": "core", "name": "兽核", "weight": 8, "qty": [1, 1]},
         ]}}}},
        {"id": "alchemy", "kind": "craft", "label": "调和",
         "config": {"recipes": [
             {"id": "potion", "name": "治疗药水", "inputs": {"herb": 2},
              "output": {"item": "potion", "name": "治疗药水", "qty": 1},
              "difficulty": 8, "attribute": "int"},
         ]}},
        {"id": "guild_rep", "kind": "reputation", "label": "公会声望",
         "config": {"factions": ["冒险者公会", "工匠行会", "边境守备"]}},
        {"id": "xp", "kind": "progression", "label": "成长",
         "config": {"base_xp": 100, "growth": 1.4, "max_level": 20,
                    "per_level": {"str": 1, "con": 1}, "level_label": "冒险者等级"}},
        {"id": "achievements", "kind": "achievement", "label": "成就",
         "config": {"items": [
             {"id": "first_blood", "name": "初次交锋", "desc": "赢下第一场战斗",
              "condition": {"counter_gte": {"key": "kills", "n": 1}}, "reward": {"xp": 50, "gold": 20}},
             {"id": "explorer", "name": "踏遍边境", "desc": "探索三处地点",
              "condition": {"counter_gte": {"key": "locations", "n": 3}}, "reward": {"xp": 80}},
         ]}},
        {"id": "actions", "kind": "custom", "label": "日常动作",
         "config": {"actions": {
             "rest": {"label": "扎营休息",
                      "effects": [{"op": "advance_time", "minutes": 480},
                                  {"op": "flag", "flag": "rested"}]},
             "train": {"label": "训练",
                       "effects": [{"op": "xp", "delta": 25},
                                   {"op": "attribute", "key": "str", "delta": 1}]},
         }}},
    ],
    game={"title": "艾瑟兰", "kind": "rpg",
          "resources": [{"key": "hp", "label": "生命", "value": 30, "min": 0, "max": 30, "color": "hp"},
                        {"key": "mp", "label": "魔力", "value": 10, "min": 0, "max": 10, "color": "mp"},
                        {"key": "gold", "label": "金币", "value": 40, "min": 0, "max": 0, "color": "gold"}],
          "attributes": [{"key": "str", "label": "力量", "value": 10},
                         {"key": "dex", "label": "敏捷", "value": 11},
                         {"key": "int", "label": "智力", "value": 9},
                         {"key": "con", "label": "体质", "value": 10},
                         {"key": "cha", "label": "魅力", "value": 10}],
          "meters": [{"key": "guild", "label": "公会阶", "value": 0, "min": 0, "max": 5}],
          "tags": ["边境"], "sheet": {"职业": "见习冒险者", "住所": "洛恩镇旅店"}},
    lore=[
        {"keys": ["基调", "文风"], "constant": True, "comment": "基调",
         "content": "英雄奇幻底色：委托驱动、成长可见、代价真实。战斗有风险，钱要算着花。"},
        {"keys": ["灰狼林", "爪印"], "comment": "灰狼林",
         "content": "灰狼林的爪印比寻常狼大一圈，树皮上有灼烧痕迹——不像野兽干的。"},
        {"keys": ["哨塔", "旧哨塔"], "comment": "哨塔",
         "content": "废弃哨塔是三十年前边境战争的遗留，塔基被刻意封过一次。"},
    ],
)

_MYSTERY = _pack(
    "mystery", "本格推理调查", "悬疑 / 调查", "choice",
    notes="线索链 + 时间线 + 嫌疑人口供。核心是「问对问题」，不是「打赢谁」。",
    world={"name": "雾港", "era": "民国十七年 · 深秋",
           "location_desc": "雾从海面漫上来，码头的灯一盏一盏亮起。巡捕房的电话在雨里响个不停。"},
    player={"name": "调查员", "level": "外行",
            "attrs": {"str": 8, "dex": 9, "int": 13, "con": 9, "cha": 11, "per": 12},
            "hp": 20, "hp_max": 20, "mp": 0, "mp_max": 0, "gold": 60,
            "location": "雾港码头", "items": {"notebook": 1, "flashlight": 1}},
    entities=[
        {"id": "inspector", "name": "巡捕 老陈", "faction": "巡捕房", "level": "老手",
         "attrs": {"str": 11, "dex": 9, "int": 11, "con": 11, "cha": 10, "per": 12},
         "hp": 25, "hp_max": 25, "gold": 30, "location": "雾港码头",
         "desc": "大衣下摆全是泥，眼睛里有常年熬夜的红血丝。", "personality": "疲惫但固执",
         "speech": "「这城里死人不稀奇，稀奇的是有人想让我们查。」"},
        {"id": "innkeeper", "name": "旅店老板 吴婶", "faction": "市井", "level": "平民",
         "attrs": {"str": 8, "dex": 8, "int": 10, "con": 9, "cha": 12, "per": 11},
         "hp": 15, "hp_max": 15, "gold": 80, "location": "雾港码头",
         "desc": "袖口永远干净，记账的本子藏在围裙里。", "personality": "热心但嘴严",
         "speech": "「客官，昨儿夜里那动静，我可什么都没听见。」"},
    ],
    market=[{"location": "雾港码头", "items": [
        {"key": "film", "name": "胶片", "price": 18, "supply": 10, "base_price": 18, "type": "工具"},
        {"key": "whisky", "name": "威士忌", "price": 22, "supply": 8, "base_price": 22, "type": "饮品"},
        {"key": "bandage", "name": "纱布", "price": 5, "supply": 20, "base_price": 5, "type": "药品"},
    ]}],
    relations=[{"a": "player", "b": "inspector", "affinity": 5, "respect": 10}],
    level_tiers=["外行", "学徒", "熟练", "专家", "传奇"],
    terms={"hero": "调查员", "level": "资历", "hp": "体力", "mp": "理智", "gold": "法币",
           "track": "调查阶", "territory": "走访范围", "inventory": "随身",
           "codex": "案卷", "quests": "线索链", "context": "案卷台账"},
    places={
        "雾港码头": {"desc": "货箱堆到人腰高，雾里能听见水声和远处的汽笛。", "market": "雾港码头"},
        "永昌号": {"desc": "船身锈得厉害，甲板上有一道被冲洗过的暗痕。", "market": ""},
        "灯塔": {"desc": "灯塔三年没亮过，铁门上的锁是新的。", "market": ""},
    },
    currency="法币",
    ui={"skin": "neutral", "accent": "#8aa6c8", "motif": "悬疑·雾港", "brand": "雾港",
        "tagline": "别让灯塔亮起来"},
    playbook={"loop": "choice", "input": "choice",
              "progress": {"axis": "knowledge", "label": "线索", "max": 24},
              "failure": {"mode": "sanity", "label": "理智", "max": 10},
              "beat": {"pattern": ["现场", "问询", "矛盾", "逼近", "代价"], "every": 4},
              "settlement": ["social", "roll", "travel", "trade"],
              "context": {"inject": ["lore", "cast", "chronicle"], "max_lore": 14, "scan_depth": 3}},
    questlines=[{
        "id": "lighthouse", "title": "别让灯塔亮起来", "summary": "有人在等灯塔重新亮起，有人不想它亮。",
        "visibility": {"flag": "__start__"},
        "stages": [
            {"id": "letter", "title": "无署名信", "objectives": ["弄清信是谁写的"],
             "exit_if": {"visited": "雾港码头"}, "next": ["keeper"]},
            {"id": "keeper", "title": "看守", "objectives": ["找到灯塔看守"],
             "exit_if": {"visited": "灯塔"}, "next": ["ledger"]},
            {"id": "ledger", "title": "名册", "objectives": ["对上那七个名字"], "next": []},
        ],
        "reward": {"flags": ["lighthouse_truth"]},
    }],
    systems=[
        {"id": "clock", "kind": "time", "label": "时间",
         "config": {"start": {"day": 1, "hour": 20}, "days_per_season": 30,
                    "seasons": ["深秋", "初冬", "隆冬", "早春"],
                    "weathers": [{"name": "雾", "weight": 50}, {"name": "雨", "weight": 30},
                                 {"name": "阴", "weight": 20}]}},
        {"id": "clues", "kind": "loot", "label": "现场勘查",
         "config": {"tables": {"scene": {"rolls": 2, "empty_weight": 30, "entries": [
             {"item": "fiber", "name": "纤维", "weight": 40, "qty": [1, 1]},
             {"item": "ash", "name": "灰烬", "weight": 30, "qty": [1, 1]},
             {"item": "note", "name": "残页", "weight": 20, "qty": [1, 1]},
         ]}}}},
        {"id": "trust", "kind": "reputation", "label": "信任",
         "config": {"factions": ["巡捕房", "市井", "教会", "船帮"],
                    "tiers": [{"min": -1000, "label": "戒备"}, {"min": -20, "label": "冷淡"},
                              {"min": 20, "label": "合作"}, {"min": 60, "label": "信任"}]}},
        {"id": "sanity", "kind": "custom", "label": "理智消耗",
         "config": {"actions": {
             "investigate": {"label": "深挖",
                             "effects": [{"op": "advance_time", "minutes": 120},
                                         {"op": "meter", "key": "clue", "delta": 1},
                                         {"op": "resource", "key": "sanity", "delta": -1}]},
             "rest": {"label": "休息",
                      "effects": [{"op": "advance_time", "minutes": 480},
                                  {"op": "resource", "key": "sanity", "delta": 2}]},
         }}},
        {"id": "achievements", "kind": "achievement", "label": "结案",
         "config": {"items": [
             {"id": "first_clue", "name": "第一条线索", "desc": "找到任何一条线索",
              "condition": {"counter_gte": {"key": "clues", "n": 1}}, "reward": {"xp": 20}},
         ]}},
    ],
    game={"title": "雾港调查", "kind": "investigation",
          "resources": [{"key": "sanity", "label": "理智", "value": 10, "min": 0, "max": 10, "color": "hp"},
                        {"key": "gold", "label": "法币", "value": 60, "min": 0, "max": 0, "color": "gold"}],
          "attributes": [{"key": "per", "label": "感知", "value": 12},
                         {"key": "int", "label": "推理", "value": 13},
                         {"key": "cha", "label": "话术", "value": 11}],
          "meters": [{"key": "clue", "label": "线索", "value": 0, "min": 0, "max": 24}],
          "tags": ["雨季"], "sheet": {"职业": "私家调查员", "委托人": "无署名信"}},
    lore=[
        {"keys": ["基调", "文风"], "constant": True, "comment": "基调",
         "content": "冷硬派调查：证据说话，口供有偏差，真相往往比谎言更伤人。"},
        {"keys": ["灯塔", "熄"], "comment": "灯塔",
         "content": "灯塔三年前熄灭，官方记录是设备老化，但维修单上的签名是伪造的。"},
        {"keys": ["名册", "七个名字"], "comment": "名册",
         "content": "永昌号的旧名册上有七个名字，其中三个在同一年先后死亡。"},
    ],
)

_MANAGEMENT = _pack(
    "management", "店铺经营", "经营 / 模拟", "mud",
    notes="进货 → 定价 → 雇人 → 扩张。核心是现金流与供需，不是打怪。",
    world={"name": "临川老街", "era": "市井",
           "location_desc": "老街的青石板被踩得发亮，你的铺子夹在茶摊和药铺之间，卷帘门刚拉起一半。"},
    player={"name": "掌柜", "level": "小摊",
            "attrs": {"str": 8, "dex": 9, "int": 12, "con": 9, "cha": 12},
            "hp": 20, "hp_max": 20, "mp": 0, "mp_max": 0, "gold": 300,
            "location": "临川老街", "items": {"tea": 10}},
    entities=[
        {"id": "clerk", "name": "伙计 阿福", "faction": "本店", "level": "学徒",
         "attrs": {"str": 10, "dex": 10, "int": 9, "con": 10, "cha": 11},
         "hp": 20, "hp_max": 20, "gold": 5, "location": "临川老街",
         "desc": "手脚麻利，算盘打得比嘴快。", "personality": "勤快", "speech": "「掌柜的，今儿进多少？」"},
        {"id": "supplier", "name": "茶商 周老板", "faction": "商行", "level": "行商",
         "attrs": {"str": 9, "dex": 9, "int": 12, "con": 10, "cha": 13},
         "hp": 22, "hp_max": 22, "gold": 500, "location": "临川老街",
         "desc": "袖子里永远揣着两泡样品。", "personality": "精明", "speech": "「量大从优，现银结算。」"},
    ],
    market=[{"location": "临川老街", "items": [
        {"key": "tea", "name": "粗茶", "price": 6, "supply": 60, "base_price": 6, "type": "货"},
        {"key": "cake", "name": "茶点", "price": 4, "supply": 40, "base_price": 4, "type": "货"},
        {"key": "silk", "name": "绸缎", "price": 30, "supply": 12, "base_price": 30, "type": "货"},
    ]}],
    relations=[{"a": "player", "b": "clerk", "affinity": 20, "respect": 10}],
    level_tiers=["小摊", "铺面", "商号", "行会", "巨贾"],
    terms={"hero": "掌柜", "level": "字号", "hp": "体力", "mp": "精力", "gold": "银钱",
           "track": "商号阶", "territory": "铺面", "inventory": "库存",
           "codex": "行商见闻", "quests": "经营目标"},
    places={
        "临川老街": {"desc": "铺面不大，柜台擦得发亮，门口的木牌写着「新茶上市」。", "market": "临川老街"},
        "后巷仓库": {"desc": "堆着上个月的茶箱，墙角有点返潮。", "market": ""},
        "南市集": {"desc": "人声鼎沸，批发价在这里才见真章。", "market": ""},
    },
    currency="银钱",
    ui={"skin": "ink", "accent": "#c9a86b", "motif": "市井·经营", "brand": "临川老街",
        "tagline": "一分利，撑起一间铺"},
    playbook={"loop": "mud", "input": "command",
              "progress": {"axis": "gold", "label": "资产", "max": 5000},
              "failure": {"mode": "clock", "label": "周转", "max": 12},
              "beat": {"pattern": ["进货", "定价", "待客", "盘账", "扩张"], "every": 5},
              "settlement": ["trade", "social", "roll", "tick"],
              "context": {"inject": ["lore", "cast", "chronicle"], "max_lore": 8, "scan_depth": 2}},
    questlines=[{
        "id": "first_month", "title": "第一个月", "summary": "先活过这个月，再谈扩张。",
        "visibility": {"flag": "__start__"},
        "stages": [
            {"id": "stock", "title": "备货", "objectives": ["库存里有 20 份茶"],
             "exit_if": {"item_gte": {"key": "tea", "n": 20}}, "next": ["profit"]},
            {"id": "profit", "title": "见利", "objectives": ["资产超过 400"],
             "exit_if": {"gold_gte": 400}, "next": []},
        ],
        "reward": {"gold": 100, "flags": ["first_month_done"]},
    }],
    systems=[
        {"id": "clock", "kind": "time", "label": "营业时间",
         "config": {"start": {"day": 1, "hour": 6}, "days_per_season": 30}},
        {"id": "supply", "kind": "loot", "label": "到货",
         "config": {"tables": {"restock": {"rolls": 2, "empty_weight": 20, "entries": [
             {"item": "tea", "name": "粗茶", "weight": 50, "qty": [5, 15]},
             {"item": "cake", "name": "茶点", "weight": 40, "qty": [5, 10]},
             {"item": "silk", "name": "绸缎", "weight": 10, "qty": [1, 3]},
         ]}}}},
        {"id": "books", "kind": "custom", "label": "经营动作",
         "config": {"actions": {
             "open_shop": {"label": "开门营业",
                           "effects": [{"op": "advance_time", "minutes": 600},
                                       {"op": "meter", "key": "turnover", "delta": 1}]},
             "restock": {"label": "补货",
                         "effects": [{"op": "advance_time", "minutes": 180},
                                     {"op": "resource", "key": "gold", "delta": -60}]},
         }}},
        {"id": "rep", "kind": "reputation", "label": "商誉",
         "config": {"factions": ["街坊", "商行", "行会"]}},
    ],
    game={"title": "临川老街", "kind": "management",
          "resources": [{"key": "gold", "label": "银钱", "value": 300, "min": 0, "max": 0, "color": "gold"},
                        {"key": "energy", "label": "精力", "value": 10, "min": 0, "max": 10, "color": "mp"}],
          "attributes": [{"key": "cha", "label": "口才", "value": 12},
                         {"key": "int", "label": "算账", "value": 12}],
          "meters": [{"key": "turnover", "label": "周转", "value": 0, "min": 0, "max": 12}],
          "tags": ["新开张"], "sheet": {"铺面": "临川老街 3 号", "主营": "茶与茶点"}},
    lore=[
        {"keys": ["基调", "文风"], "constant": True, "comment": "基调",
         "content": "市井经营：每天算账，偶尔人情。钱不是万能的，但没钱万万不能。"},
        {"keys": ["南市集", "批发"], "comment": "批发",
         "content": "南市集的批发价比零售低三成，但一次至少要拿五十份。"},
    ],
)

_SURVIVAL = _pack(
    "survival", "末日生存", "生存 / 资源管理", "mud",
    notes="体力/饥饿/口渴/温度四条线同时压着，白天搜刮，夜里躲藏。",
    world={"name": "灰区", "era": "崩坏第 47 天",
           "location_desc": "便利店的玻璃碎了一地，货架被翻得精光。远处的天是灰的，风里有铁锈味。"},
    player={"name": "幸存者", "level": "新手",
            "attrs": {"str": 10, "dex": 11, "int": 10, "con": 12, "cha": 8},
            "hp": 40, "hp_max": 40, "mp": 0, "mp_max": 0, "gold": 0,
            "location": "废弃便利店", "items": {"water": 1, "canned": 1}},
    entities=[
        {"id": "scavenger", "name": "拾荒者 老周", "faction": "散人", "level": "老手",
         "attrs": {"str": 11, "dex": 10, "int": 11, "con": 13, "cha": 7},
         "hp": 35, "hp_max": 35, "gold": 0, "location": "废弃便利店",
         "desc": "防毒面具推到额头上，露出一双总在打量你的眼睛。", "personality": "谨慎",
         "speech": "「东西可以换，别问从哪来的。」"},
    ],
    market=[{"location": "废弃便利店", "items": [
        {"key": "water", "name": "净水", "price": 15, "supply": 6, "base_price": 15, "type": "补给"},
        {"key": "canned", "name": "罐头", "price": 12, "supply": 8, "base_price": 12, "type": "补给"},
        {"key": "bandage", "name": "绷带", "price": 10, "supply": 5, "base_price": 10, "type": "医疗"},
    ]}],
    relations=[{"a": "player", "b": "scavenger", "affinity": 0, "respect": 5}],
    level_tiers=["新手", "老练", "硬核", "传奇幸存者"],
    terms={"hero": "幸存者", "level": "状态", "hp": "体力", "mp": "精神", "gold": "物资点",
           "track": "生存天数", "territory": "据点", "inventory": "背包",
           "codex": "生存笔记", "quests": "生存目标"},
    places={
        "废弃便利店": {"desc": "货架翻倒，收银台的抽屉被撬开，后门通向小巷。", "market": "废弃便利店"},
        "地下车库": {"desc": "阴影里堆着废弃车辆，偶尔有滴水声。", "market": ""},
        "水塔": {"desc": "铁梯锈得厉害，塔顶视野开阔但风很大。", "market": ""},
    },
    currency="物资点",
    ui={"skin": "neutral", "accent": "#c76b4a", "motif": "废土·灰区", "brand": "灰区",
        "tagline": "第四十七天，还活着"},
    playbook={"loop": "mud", "input": "command",
              "progress": {"axis": "knowledge", "label": "生存天数", "max": 30},
              "failure": {"mode": "hp", "label": "倒下", "max": 0},
              "beat": {"pattern": ["清晨", "搜刮", "遭遇", "夜宿", "清点"], "every": 4},
              "settlement": ["combat", "trade", "roll", "travel", "use_item"],
              "context": {"inject": ["lore", "cast", "chronicle"], "max_lore": 8, "scan_depth": 2}},
    questlines=[{
        "id": "water_tower", "title": "水塔", "summary": " rumor 说水塔里还有干净的水。",
        "visibility": {"flag": "__start__"},
        "stages": [
            {"id": "reach", "title": "抵达", "objectives": ["走到水塔"],
             "exit_if": {"visited": "水塔"}, "next": ["climb"]},
            {"id": "climb", "title": "攀爬", "objectives": ["爬上水塔检查水箱"], "next": []},
        ],
        "reward": {"flags": ["clean_water"]},
    }],
    systems=[
        {"id": "clock", "kind": "time", "label": "昼夜",
         "config": {"start": {"day": 47, "hour": 16}, "days_per_season": 30,
                    "seasons": ["崩坏季"], "weathers": [{"name": "灰霾", "weight": 60},
                                                       {"name": "酸雨", "weight": 25},
                                                       {"name": "晴", "weight": 15}]}},
        {"id": "scavenge", "kind": "loot", "label": "搜刮",
         "config": {"tables": {"store": {"rolls": 3, "empty_weight": 40, "entries": [
             {"item": "water", "name": "净水", "weight": 30, "qty": [1, 2]},
             {"item": "canned", "name": "罐头", "weight": 35, "qty": [1, 2]},
             {"item": "scrap", "name": "零件", "weight": 25, "qty": [1, 3]},
             {"item": "chip", "name": "电子元件", "weight": 8, "qty": [1, 1]},
         ]}}}},
        {"id": "survival", "kind": "custom", "label": "生存动作",
         "config": {"actions": {
             "eat": {"label": "进食",
                     "effects": [{"op": "resource", "key": "hp", "delta": 5},
                                 {"op": "flag", "flag": "fed"}]},
             "sleep": {"label": "睡觉",
                       "effects": [{"op": "advance_time", "minutes": 480},
                                   {"op": "resource", "key": "hp", "delta": 8}]},
             "scavenge": {"label": "搜刮周围",
                          "effects": [{"op": "advance_time", "minutes": 120},
                                      {"op": "meter", "key": "day", "delta": 1}]},
         }}},
        {"id": "rep", "kind": "reputation", "label": "据点关系",
         "config": {"factions": ["散人", "哨站", "车队"]}},
    ],
    game={"title": "灰区", "kind": "survival",
          "resources": [{"key": "hp", "label": "体力", "value": 40, "min": 0, "max": 40, "color": "hp"},
                        {"key": "water", "label": "水", "value": 1, "min": 0, "max": 20, "color": "mp"},
                        {"key": "food", "label": "食物", "value": 1, "min": 0, "max": 20, "color": "success"}],
          "attributes": [{"key": "str", "label": "力量", "value": 10},
                         {"key": "con", "label": "体质", "value": 12}],
          "meters": [{"key": "day", "label": "生存天数", "value": 0, "min": 0, "max": 30}],
          "tags": ["断水断电"], "sheet": {"据点": "废弃便利店", "队伍": "无"}},
    lore=[
        {"keys": ["基调", "文风"], "constant": True, "comment": "基调",
         "content": "废土生存：资源永远不够，每个选择都有代价，希望是奢侈品。"},
        {"keys": ["水塔", "干净的水"], "comment": "水塔",
         "content": "水塔顶层的储水箱有独立过滤层，可能还有存水。"},
    ],
)

_NARRATIVE = _pack(
    "narrative", "情感叙事", "剧情 / 关系", "freeform",
    notes="没有战斗，只有关系与选择。核心是「你说什么、你欠谁、你最后选了谁」。",
    world={"name": "长夏", "era": "毕业那年的夏天",
           "location_desc": "教室的风扇吱呀转着，桌上的试卷被风掀起一角。窗外的蝉叫得让人心慌。"},
    player={"name": "你", "level": "高三",
            "attrs": {"str": 8, "dex": 9, "int": 11, "con": 9, "cha": 13},
            "hp": 20, "hp_max": 20, "mp": 0, "mp_max": 0, "gold": 50,
            "location": "教室", "items": {"letters": 1}},
    entities=[
        {"id": "lin", "name": "林夏", "faction": "同班", "level": "同桌",
         "attrs": {"str": 7, "dex": 9, "int": 12, "con": 8, "cha": 14},
         "hp": 20, "hp_max": 20, "gold": 20, "location": "教室",
         "desc": "总把袖子挽到手肘，笑起来会眯眼。", "personality": "开朗但藏事",
         "speech": "「你要是敢忘了我，我就把你的卷子撕了。」"},
        {"id": "chen", "name": "陈老师", "faction": "教师", "level": "班主任",
         "attrs": {"str": 8, "dex": 8, "int": 14, "con": 10, "cha": 11},
         "hp": 20, "hp_max": 20, "gold": 60, "location": "办公室",
         "desc": "衬衫永远扣到最上面一颗。", "personality": "严厉但心软",
         "speech": "「你们以后会明白的。」"},
    ],
    market=[{"location": "校门口", "items": [
        {"key": "ice", "name": "冰棍", "price": 2, "supply": 30, "base_price": 2, "type": "零食"},
        {"key": "letter_paper", "name": "信纸", "price": 5, "supply": 20, "base_price": 5, "type": "文具"},
    ]}],
    relations=[{"a": "player", "b": "lin", "affinity": 40, "respect": 10}],
    level_tiers=["高一", "高二", "高三", "毕业"],
    terms={"hero": "你", "level": "学年", "hp": "心力", "mp": "勇气", "gold": "零花钱",
           "track": "时间线", "territory": "校园", "inventory": "口袋",
           "codex": "回忆", "quests": "未说出口的话", "context": "心事"},
    places={
        "教室": {"desc": "午后的光落在课桌上，粉笔灰在光里浮。", "market": ""},
        "天台": {"desc": "铁丝网外是整个县城，风把校服吹得鼓起来。", "market": ""},
        "校门口": {"desc": "小卖部的冰柜嗡嗡响，放学的自行车流从这里涌出去。", "market": "校门口"},
    },
    currency="零花钱",
    ui={"skin": "ink", "accent": "#d98f8f", "motif": "青春·长夏", "brand": "长夏",
        "tagline": "那个夏天没有说完的话"},
    playbook={"loop": "freeform", "input": "natural",
              "progress": {"axis": "level", "label": "学年", "max": 3},
              "failure": {"mode": "none", "label": "无失败", "max": 0},
              "beat": {"pattern": ["日常", "接近", "迟疑", "冲突", "坦白"], "every": 5},
              "settlement": ["social", "roll", "travel"],
              "context": {"inject": ["lore", "cast", "chronicle"], "max_lore": 8, "scan_depth": 2}},
    questlines=[{
        "id": "letter", "title": "那封信", "summary": "有封信一直没送出去。",
        "visibility": {"flag": "__start__"},
        "stages": [
            {"id": "hesitate", "title": "犹豫", "objectives": ["决定要不要写"],
             "exit_if": {"flag": "letter_written"}, "next": ["give"]},
            {"id": "give", "title": "交出", "objectives": ["把信交出去"], "next": []},
        ],
        "reward": {"flags": ["letter_delivered"]},
    }],
    systems=[
        {"id": "clock", "kind": "time", "label": "学期",
         "config": {"start": {"day": 1, "hour": 8}, "days_per_season": 60,
                    "seasons": ["初夏", "盛夏", "夏末", "秋初"]}},
        {"id": "bond", "kind": "reputation", "label": "羁绊",
         "config": {"factions": ["林夏", "陈老师", "家人", "同学"],
                    "tiers": [{"min": -1000, "label": "疏远"}, {"min": 0, "label": "普通"},
                              {"min": 30, "label": "亲近"}, {"min": 70, "label": "心意相通"}]}},
        {"id": "mood", "kind": "custom", "label": "心事动作",
         "config": {"actions": {
             "write": {"label": "写信",
                       "effects": [{"op": "flag", "flag": "letter_written"},
                                   {"op": "resource", "key": "courage", "delta": -2}]},
             "talk": {"label": "找她说话",
                      "effects": [{"op": "reputation", "system": "bond",
                                   "faction": "林夏", "delta": 5},
                                  {"op": "advance_time", "minutes": 60}]},
         }}},
        {"id": "memories", "kind": "achievement", "label": "回忆",
         "config": {"items": [
             {"id": "first_talk", "name": "第一次搭话", "desc": "主动和她说话",
              "condition": {"flag": "talked"}, "reward": {"xp": 10}},
         ]}},
    ],
    game={"title": "长夏", "kind": "story",
          "resources": [{"key": "courage", "label": "勇气", "value": 10, "min": 0, "max": 10, "color": "mp"},
                        {"key": "gold", "label": "零花钱", "value": 50, "min": 0, "max": 0, "color": "gold"}],
          "attributes": [{"key": "cha", "label": "表达", "value": 13},
                         {"key": "int", "label": "成绩", "value": 11}],
          "meters": [{"key": "days", "label": "夏天还剩", "value": 0, "min": 0, "max": 60}],
          "tags": ["毕业季"], "sheet": {"班级": "高三 2 班", "心事": "那封信"}},
    lore=[
        {"keys": ["基调", "文风"], "constant": True, "comment": "基调",
         "content": "克制的青春叙事：不煽情，用细节说话。每个选择都在减少某些可能性。"},
    ],
)

_COZY = _pack(
    "cozy", "田园生活", "休闲 / 建造", "freeform",
    notes="种地、钓鱼、送礼、修房子。没有失败条件，只有慢慢变好的生活。",
    world={"name": "雾溪村", "era": "初春",
           "location_desc": "溪水从屋后绕过，院里的桃树刚冒芽。镇上寄来的地契还压在门缝里。"},
    player={"name": "新村民", "level": "暂住",
            "attrs": {"str": 10, "dex": 10, "int": 10, "con": 11, "cha": 11},
            "hp": 30, "hp_max": 30, "mp": 0, "mp_max": 0, "gold": 200,
            "location": "自家小院", "items": {"seeds": 5, "hoe": 1}},
    entities=[
        {"id": "mayor", "name": "村长 温伯", "faction": "村民", "level": "长者",
         "attrs": {"str": 9, "dex": 8, "int": 11, "con": 10, "cha": 13},
         "hp": 25, "hp_max": 25, "gold": 150, "location": "雾溪村",
         "desc": "总在门口晒太阳，见谁都笑。", "personality": "和善", "speech": "「慢慢来，地跑不了。」"},
        {"id": "angler", "name": "钓鱼佬 阿海", "faction": "村民", "level": "闲人",
         "attrs": {"str": 10, "dex": 12, "int": 9, "con": 11, "cha": 9},
         "hp": 25, "hp_max": 25, "gold": 90, "location": "溪边",
         "desc": "一坐一整天，桶里常常是空的。", "personality": "悠哉", "speech": "「鱼不咬钩，人也不急。」"},
    ],
    market=[{"location": "雾溪村", "items": [
        {"key": "seeds", "name": "种子", "price": 8, "supply": 40, "base_price": 8, "type": "农资"},
        {"key": "bait", "name": "鱼饵", "price": 3, "supply": 30, "base_price": 3, "type": "杂货"},
        {"key": "wood", "name": "木料", "price": 12, "supply": 20, "base_price": 12, "type": "建材"},
    ]}],
    relations=[{"a": "player", "b": "mayor", "affinity": 15, "respect": 5}],
    level_tiers=["暂住", "落户", "村民", "乡贤"],
    terms={"hero": "村民", "level": "身份", "hp": "体力", "mp": "心气", "gold": "铜钱",
           "track": "村庄好感", "territory": "田地", "inventory": "储物",
           "codex": "村志", "quests": "小目标", "context": "村中杂记"},
    places={
        "自家小院": {"desc": "院墙有点歪，桃树下面堆着旧木箱。", "market": ""},
        "溪边": {"desc": "水清得能看见石头，柳枝垂到水面上。", "market": ""},
        "雾溪村": {"desc": "十几户人家沿溪而建，晒着被子和萝卜干。", "market": "雾溪村"},
    },
    currency="铜钱",
    ui={"skin": "ink", "accent": "#8fb87a", "motif": "田园·雾溪", "brand": "雾溪村",
        "tagline": "慢慢来，地跑不了"},
    playbook={"loop": "freeform", "input": "natural",
              "progress": {"axis": "knowledge", "label": "村庄好感", "max": 20},
              "failure": {"mode": "none", "label": "无失败", "max": 0},
              "beat": {"pattern": ["清晨", "劳作", "午后", "闲谈", "夜里"], "every": 4},
              "settlement": ["trade", "social", "roll", "use_item"],
              "context": {"inject": ["lore", "cast", "chronicle"], "max_lore": 8, "scan_depth": 2}},
    questlines=[{
        "id": "first_harvest", "title": "第一收", "summary": "把种子种下去，等它长出来。",
        "visibility": {"flag": "__start__"},
        "stages": [
            {"id": "plant", "title": "播种", "objectives": ["在院里种下种子"],
             "exit_if": {"flag": "planted"}, "next": ["harvest"]},
            {"id": "harvest", "title": "收获", "objectives": ["等作物成熟并收下"], "next": []},
        ],
        "reward": {"gold": 50, "flags": ["first_harvest"]},
    }],
    systems=[
        {"id": "clock", "kind": "time", "label": "农时",
         "config": {"start": {"day": 1, "hour": 6}, "days_per_season": 15,
                    "seasons": ["初春", "仲春", "暮春", "初夏"]}},
        {"id": "forage", "kind": "loot", "label": "采集",
         "config": {"tables": {"wild": {"rolls": 2, "empty_weight": 25, "entries": [
             {"item": "berries", "name": "野果", "weight": 50, "qty": [1, 4]},
             {"item": "mushroom", "name": "菌子", "weight": 30, "qty": [1, 2]},
             {"item": "flower", "name": "野花", "weight": 20, "qty": [1, 3]},
         ]}}}},
        {"id": "village", "kind": "reputation", "label": "村民好感",
         "config": {"factions": ["村民", "商队", "邻村"]}},
        {"id": "chores", "kind": "custom", "label": "日常",
         "config": {"actions": {
             "farm": {"label": "下地干活",
                      "effects": [{"op": "advance_time", "minutes": 240},
                                  {"op": "flag", "flag": "planted"}]},
             "fish": {"label": "钓鱼",
                      "effects": [{"op": "advance_time", "minutes": 180},
                                  {"op": "resource", "key": "energy", "delta": -1}]},
         }}},
    ],
    game={"title": "雾溪村", "kind": "management",
          "resources": [{"key": "energy", "label": "体力", "value": 10, "min": 0, "max": 10, "color": "hp"},
                        {"key": "gold", "label": "铜钱", "value": 200, "min": 0, "max": 0, "color": "gold"}],
          "attributes": [{"key": "str", "label": "干劲", "value": 10},
                         {"key": "cha", "label": "人缘", "value": 11}],
          "meters": [{"key": "harvest", "label": "收成", "value": 0, "min": 0, "max": 20}],
          "tags": ["初春"], "sheet": {"住处": "院墙有点歪的小院", "目标": "把日子过好"}},
    lore=[
        {"keys": ["基调", "文风"], "constant": True, "comment": "基调",
         "content": "温柔的田园日常：没有威胁，只有季节和人情。允许玩家什么都不做。"},
    ],
)

_TABLETOP = _pack(
    "tabletop", "桌面跑团", "跑团 / 战术", "ttrpg",
    notes="d20 + 属性 + 技能 + 难度。战斗有战术位，探索有技能检定，社交有对抗。",
    world={"name": "灰岩堡", "era": "第三纪元",
           "location_desc": "城堡的吊桥在夜里升起，酒馆的灯还亮着。门口贴着一张悬赏：地下墓穴有东西在动。"},
    player={"name": "冒险者", "level": "1 级",
            "attrs": {"str": 14, "dex": 12, "int": 10, "con": 13, "cha": 8},
            "hp": 28, "hp_max": 28, "mp": 0, "mp_max": 0, "gold": 25,
            "location": "灰岩堡", "items": {"rope": 1, "torch": 2}},
    entities=[
        {"id": "captain", "name": "守备队长 罗兰", "faction": "灰岩堡", "level": "5 级",
         "attrs": {"str": 15, "dex": 11, "int": 10, "con": 14, "cha": 12},
         "hp": 45, "hp_max": 45, "gold": 80, "location": "灰岩堡",
         "desc": "铠甲上有新添的凹痕，说话像在下命令。", "personality": "严肃", "speech": "「墓穴里的东西，不该出来。」"},
    ],
    market=[{"location": "灰岩堡", "items": [
        {"key": "torch", "name": "火把", "price": 2, "supply": 40, "base_price": 2, "type": "消耗品"},
        {"key": "rope", "name": "麻绳", "price": 5, "supply": 20, "base_price": 5, "type": "工具"},
        {"key": "heal_potion", "name": "治疗药剂", "price": 20, "supply": 8, "base_price": 20, "type": "药水"},
    ]}],
    relations=[{"a": "player", "b": "captain", "affinity": 5, "respect": 15}],
    level_tiers=["1 级", "2 级", "3 级", "4 级", "5 级", "6 级", "7 级", "8 级"],
    terms={"hero": "冒险者", "level": "等级", "hp": "生命", "mp": "法术位", "gold": "金币",
           "track": "等级", "territory": "地图", "inventory": "装备",
           "codex": "日志", "quests": "任务"},
    places={
        "灰岩堡": {"desc": "石墙厚重，火把在风里晃，酒馆门口有人在赌骰子。", "market": "灰岩堡"},
        "地下墓穴": {"desc": "石阶往下，空气里有股铁锈味，火把照不到尽头。", "market": ""},
        "旧礼拜堂": {"desc": "彩窗碎了，长椅上落满灰，祭坛后面有道暗门。", "market": ""},
    },
    currency="金币",
    ui={"skin": "xuanshu", "accent": "#b08968", "motif": "跑团·石堡", "brand": "灰岩堡",
        "tagline": "掷骰决定命运"},
    playbook={"loop": "ttrpg", "input": "command",
              "progress": {"axis": "level", "label": "等级", "max": 8},
              "failure": {"mode": "hp", "label": "倒下", "max": 0},
              "beat": {"pattern": ["探索", "遭遇", "战斗", "休整", "推进"], "every": 4},
              "settlement": ["combat", "roll", "social", "trade", "use_item"],
              "context": {"inject": ["lore", "cast", "chronicle"], "max_lore": 10, "scan_depth": 2}},
    questlines=[{
        "id": "crypt", "title": "墓穴里的动静", "summary": "守备队长想知道下面到底是什么。",
        "visibility": {"flag": "__start__"},
        "stages": [
            {"id": "brief", "title": "说明", "objectives": ["向队长了解情况"],
             "exit_if": {"flag": "briefed"}, "next": ["descend"]},
            {"id": "descend", "title": "下墓", "objectives": ["进入地下墓穴"],
             "exit_if": {"visited": "地下墓穴"}, "next": ["chapel"]},
            {"id": "chapel", "title": "礼拜堂", "objectives": ["找到祭坛后的暗门"], "next": []},
        ],
        "reward": {"gold": 150, "flags": ["crypt_cleared"]},
    }],
    systems=[
        {"id": "clock", "kind": "time", "label": "火炬计时",
         "config": {"start": {"day": 1, "hour": 19}, "days_per_season": 30}},
        {"id": "encounter", "kind": "loot", "label": "战利品",
         "config": {"tables": {"crypt": {"rolls": 2, "empty_weight": 20, "entries": [
             {"item": "bone_dust", "name": "骨粉", "weight": 50, "qty": [1, 3]},
             {"item": "old_coin", "name": "古币", "weight": 35, "qty": [1, 6]},
             {"item": "rune", "name": "符文石", "weight": 10, "qty": [1, 1]},
         ]}}}},
        {"id": "xp", "kind": "progression", "label": "经验",
         "config": {"base_xp": 300, "growth": 1.8, "max_level": 8,
                    "per_level": {"str": 1, "con": 1}, "level_label": "冒险者等级"}},
        {"id": "factions", "kind": "reputation", "label": "阵营",
         "config": {"factions": ["灰岩堡", "盗贼公会", "教会"]}},
        {"id": "skills", "kind": "custom", "label": "技能动作",
         "config": {"actions": {
             "search": {"label": "搜索",
                        "effects": [{"op": "loot", "system": "encounter", "table": "crypt", "grant": True},
                                    {"op": "advance_time", "minutes": 30}]},
             "short_rest": {"label": "短休",
                            "effects": [{"op": "resource", "key": "hp", "delta": 6},
                                        {"op": "advance_time", "minutes": 60}]},
         }}},
    ],
    game={"title": "灰岩堡", "kind": "rpg",
          "resources": [{"key": "hp", "label": "生命", "value": 28, "min": 0, "max": 28, "color": "hp"},
                        {"key": "gold", "label": "金币", "value": 25, "min": 0, "max": 0, "color": "gold"}],
          "attributes": [{"key": "str", "label": "力量", "value": 14},
                         {"key": "dex", "label": "敏捷", "value": 12},
                         {"key": "int", "label": "智力", "value": 10},
                         {"key": "con", "label": "体质", "value": 13},
                         {"key": "cha", "label": "魅力", "value": 8}],
          "meters": [{"key": "level", "label": "等级", "value": 1, "min": 1, "max": 8}],
          "tags": ["地下墓穴"], "sheet": {"职业": "战士", "背景": "雇佣兵"}},
    lore=[
        {"keys": ["基调", "文风"], "constant": True, "comment": "基调",
         "content": "经典跑团：掷骰即规则，失败要有代价，也要给出替代路径（失败前进）。"},
        {"keys": ["墓穴", "地下"], "comment": "墓穴",
         "content": "地下墓穴在城堡建成前就存在，墙壁上的符号比王国更古老。"},
    ],
)

_IMMERSIVE = _pack(
    "immersive", "沉浸模拟", "沉浸 / 自由", "ttrpg",
    notes="强调「有代价的解决方式」：潜行、说服、破坏、贿赂都能过，但都留痕迹。",
    world={"name": "科尔沃城", "era": "雾季",
           "location_desc": "运河上的雾气混着煤烟。钟楼敲了七下，街角的告示牌上贴着新的禁令。"},
    player={"name": "无名者", "level": "素人",
            "attrs": {"str": 9, "dex": 13, "int": 11, "con": 9, "cha": 10},
            "hp": 24, "hp_max": 24, "mp": 0, "mp_max": 0, "gold": 35,
            "location": "运河区", "items": {"lockpick": 1}},
    entities=[
        {"id": "fence", "name": "黑市商人 薇拉", "faction": "黑市", "level": "掮客",
         "attrs": {"str": 8, "dex": 11, "int": 13, "con": 9, "cha": 13},
         "hp": 20, "hp_max": 20, "gold": 400, "location": "运河区",
         "desc": "围巾遮到鼻梁，只露出眼睛。", "personality": "精于算计", "speech": "「价钱好说，痕迹难洗。」"},
        {"id": "guard", "name": "巡夜人 布伦", "faction": "城卫", "level": "哨兵",
         "attrs": {"str": 13, "dex": 10, "int": 9, "con": 12, "cha": 9},
         "hp": 30, "hp_max": 30, "gold": 25, "location": "钟楼",
         "desc": "靴子踩在湿石板上，声音传得很远。", "personality": "刻板", "speech": "「宵禁了，回去吧。」"},
    ],
    market=[{"location": "运河区", "items": [
        {"key": "lockpick", "name": "撬锁器", "price": 25, "supply": 6, "base_price": 25, "type": "工具"},
        {"key": "cloak", "name": "暗色斗篷", "price": 18, "supply": 10, "base_price": 18, "type": "装备"},
        {"key": "bribe", "name": "封口费", "price": 40, "supply": 5, "base_price": 40, "type": "道具"},
    ]}],
    relations=[{"a": "player", "b": "fence", "affinity": 5, "respect": 0}],
    level_tiers=["素人", "熟手", "行家", "传奇"],
    terms={"hero": "潜入者", "level": "名声", "hp": "伤势", "mp": "专注", "gold": "金币",
           "track": "名声阶", "territory": "势力范围", "inventory": "随身",
           "codex": "情报", "quests": "目标"},
    places={
        "运河区": {"desc": "水声盖住了脚步，雾里能看见对岸的灯。", "market": "运河区"},
        "钟楼": {"desc": "齿轮在头顶咬合，栏杆上的锈一碰就掉。", "market": ""},
        "档案馆": {"desc": "高窗投下的光柱里全是灰，架子上按年份排到三百年前。", "market": ""},
    },
    currency="金币",
    ui={"skin": "neutral", "accent": "#6f8cab", "motif": "潜入·雾城", "brand": "科尔沃",
        "tagline": "每条路都留痕迹"},
    playbook={"loop": "ttrpg", "input": "command",
              "progress": {"axis": "knowledge", "label": "情报", "max": 20},
              "failure": {"mode": "clock", "label": "警觉", "max": 8},
              "beat": {"pattern": ["踩点", "接近", "行动", "善后", "代价"], "every": 4},
              "settlement": ["roll", "social", "trade", "combat", "travel"],
              "context": {"inject": ["lore", "cast", "chronicle"], "max_lore": 10, "scan_depth": 2}},
    questlines=[{
        "id": "archive", "title": "档案馆的名单", "summary": "有人愿意出钱买一份名单。",
        "visibility": {"flag": "__start__"},
        "stages": [
            {"id": "contact", "title": "接头", "objectives": ["找到黑市商人薇拉"],
             "exit_if": {"flag": "met_vira"}, "next": ["plan"]},
            {"id": "plan", "title": "踩点", "objectives": ["摸清档案馆的巡逻"],
             "exit_if": {"visited": "档案馆"}, "next": ["take"]},
            {"id": "take", "title": "取件", "objectives": ["拿到名单"], "next": []},
        ],
        "reward": {"gold": 200, "flags": ["list_taken"]},
    }],
    systems=[
        {"id": "clock", "kind": "time", "label": "宵禁时钟",
         "config": {"start": {"day": 1, "hour": 19}, "days_per_season": 30}},
        {"id": "loot", "kind": "loot", "label": "搜身",
         "config": {"tables": {"pocket": {"rolls": 2, "empty_weight": 50, "entries": [
             {"item": "coin", "name": "零钱", "weight": 60, "qty": [1, 8]},
             {"item": "key", "name": "钥匙", "weight": 25, "qty": [1, 1]},
             {"item": "note", "name": "字条", "weight": 15, "qty": [1, 1]},
         ]}}}},
        {"id": "alert", "kind": "reputation", "label": "警觉度",
         "config": {"factions": ["城卫", "黑市", "平民"],
                    "tiers": [{"min": -1000, "label": "无视"}, {"min": 20, "label": "留意"},
                              {"min": 50, "label": "追查"}, {"min": 80, "label": "通缉"}]}},
        {"id": "tactics", "kind": "custom", "label": "潜入动作",
         "config": {"actions": {
             "sneak": {"label": "潜行",
                       "effects": [{"op": "advance_time", "minutes": 20},
                                   {"op": "reputation", "system": "alert", "faction": "城卫", "delta": 5}]},
             "bribe": {"label": "行贿",
                       "effects": [{"op": "resource", "key": "gold", "delta": -40},
                                   {"op": "reputation", "system": "alert", "faction": "城卫", "delta": -10}]},
         }}},
    ],
    game={"title": "科尔沃", "kind": "rpg",
          "resources": [{"key": "hp", "label": "伤势", "value": 24, "min": 0, "max": 24, "color": "hp"},
                        {"key": "gold", "label": "金币", "value": 35, "min": 0, "max": 0, "color": "gold"}],
          "attributes": [{"key": "dex", "label": "敏捷", "value": 13},
                         {"key": "int", "label": "洞察", "value": 11}],
          "meters": [{"key": "alert", "label": "警觉", "value": 0, "min": 0, "max": 8}],
          "tags": ["宵禁"], "sheet": {"身份": "无名者", "目标": "名单"}},
    lore=[
        {"keys": ["基调", "文风"], "constant": True, "comment": "基调",
         "content": "沉浸模拟：每个目标至少有三种解法（潜行/说服/暴力），越省事留的痕迹越多。"},
    ],
)

_XIANXIA = _pack(
    "xianxia", "青冥修仙", "修仙 / 成长", "freeform",
    notes="灵气是天地底层；凡人先看见灵泉变冷，才慢慢看见宗门、灵脉和境界。",
    world={"name": "青冥界", "era": "天衍历 317 年",
           "location_desc": "青石村后山的灵泉边，夜雾里有一线微光。村里人说，三个月前泉水开始变冷。"},
    player={"name": "林川", "faction": "青石村", "level": "凡人",
            "attrs": {"str": 8, "dex": 10, "int": 11, "con": 9, "cha": 9},
            "hp": 20, "hp_max": 20, "mp": 0, "mp_max": 0, "gold": 12,
            "location": "青石村",
            "skills": ["采药", "辨草"], "items": {"herb": 3, "dry_food": 2, "flint": 1}},
    entities=[
        {"id": "chen", "name": "陈伯", "faction": "青石村", "level": "凡人",
         "attrs": {"str": 7, "dex": 8, "int": 12, "con": 8, "cha": 10},
         "hp": 18, "hp_max": 18, "gold": 30, "location": "青石村",
         "desc": "背有点驼，手指常年沾着药汁；他认得每一种草，却从不谈山上的事。",
         "personality": "谨慎、护短", "speech": "「山上的东西，看见了也当没看见。」"},
        {"id": "shen", "name": "沈砚", "faction": "外乡人", "level": "凡人",
         "attrs": {"str": 10, "dex": 12, "int": 13, "con": 11, "cha": 11},
         "hp": 26, "hp_max": 26, "gold": 0, "location": "青石村",
         "desc": "住在村口破庙里的年轻人，脸色苍白，右手腕一直缠着布，布下有淡淡的灵纹。",
         "personality": "寡言、戒备", "speech": "「别碰我的手腕。」"},
    ],
    market=[{"location": "青石村", "items": [
        {"key": "dry_food", "name": "干粮", "price": 2, "supply": 30, "base_price": 2, "type": "食物"},
        {"key": "herb", "name": "止血草", "price": 5, "supply": 20, "base_price": 5, "type": "草药"},
        {"key": "flint", "name": "火折子", "price": 3, "supply": 15, "base_price": 3, "type": "工具"},
    ]}, {"location": "青石镇", "items": [
        {"key": "dry_food", "name": "干粮", "price": 2, "supply": 40, "base_price": 2, "type": "食物"},
        {"key": "herb", "name": "止血草", "price": 4, "supply": 30, "base_price": 4, "type": "草药"},
        {"key": "flint", "name": "火折子", "price": 2, "supply": 20, "base_price": 2, "type": "工具"},
        {"key": "dagger", "name": "铁匕首", "price": 15, "supply": 8, "base_price": 15, "type": "武器"},
    ]}],
    relations=[{"a": "player", "b": "chen", "affinity": 10, "respect": 5},
               {"a": "player", "b": "shen", "affinity": 0, "respect": 0}],
    level_tiers=["凡人", "炼气", "筑基", "金丹", "元婴", "化神", "炼虚", "合体", "大乘"],
    terms={"hero": "修士", "level": "境界", "hp": "气血", "mp": "灵力", "gold": "凡银",
           "track": "修为", "territory": "足迹", "inventory": "行囊", "codex": "见闻录",
           "quests": "因果"},
    places={
        "青石村": {"desc": "山村靠一条溪，屋后就是上山采药的石阶；夜里能听见后山的风。", "market": "青石村"},
        "后山灵泉": {"desc": "泉眼在石壁下，水面比上个月低了一截，石缝里有细小的灵光。", "market": ""},
        "落霞山": {"desc": "山门在雾里只剩一个轮廓，石阶尽头有断裂的牌坊。", "market": ""},
        "青石镇": {"desc": "镇上有药铺、铁匠铺和一间挂着旧幡的当铺，凡人很少往山那边去。", "market": "青石镇"},
    },
    currency="凡银",
    ui={"skin": "ink", "accent": "#7b9b8a", "motif": "修仙·青冥", "brand": "青冥界",
        "tagline": "灵气有尽，山路无穷"},
    playbook={"loop": "freeform", "input": "natural",
              "progress": {"axis": "level", "label": "修为", "max": 8},
              "failure": {"mode": "hp", "label": "气血耗尽", "max": 20},
              "beat": {"pattern": ["日常", "异象", "入山", "斗法", "代价"], "every": 5},
              "settlement": ["combat", "roll", "social", "trade", "use_item", "travel"],
              "context": {"inject": ["lore", "cast", "chronicle"], "max_lore": 12, "scan_depth": 2}},
    questlines=[{
        "id": "spirit_spring", "title": "灵泉为什么变冷", "summary": "青石村的灵泉在三个月前开始变冷，陈伯不肯多说。",
        "visibility": {"flag": "__start__"},
        "stages": [
            {"id": "ask", "title": "问陈伯", "objectives": ["向陈伯打听灵泉变冷的原因"],
             "exit_if": {"flag": "asked_spring"}, "next": ["night"]},
            {"id": "night", "title": "夜探灵泉", "objectives": ["夜里去后山灵泉查看"],
             "exit_if": {"visited": "后山灵泉"}, "next": ["shen"]},
            {"id": "shen", "title": "破庙里的人", "objectives": ["找到沈砚，问他在等什么"],
             "exit_if": {"flag": "met_shen"}, "next": ["mountain"]},
            {"id": "mountain", "title": "落霞山口", "objectives": ["沿灵脉走到落霞山外围"],
             "exit_if": {"visited": "落霞山"}, "next": []},
        ],
        "reward": {"flags": ["spirit_spring_trace"], "items": {"spirit_stone_shard": 1}},
    }],
    systems=[
        {"id": "clock", "kind": "time", "label": "山中时辰",
         "config": {"start": {"day": 1, "hour": 18}, "days_per_season": 30,
                    "seasons": ["春", "夏", "秋", "冬"],
                    "weathers": [{"name": "晴", "weight": 35}, {"name": "雨", "weight": 30},
                                 {"name": "雾", "weight": 25}, {"name": "雷", "weight": 10}]}},
        {"id": "spirit_loot", "kind": "loot", "label": "山中掉落",
         "config": {"tables": {"spirit": {"rolls": 2, "empty_weight": 25, "entries": [
             {"item": "herb", "name": "灵草", "weight": 45, "qty": [1, 2]},
             {"item": "spirit_stone_shard", "name": "灵石碎屑", "weight": 15, "qty": [1, 1]},
             {"item": "beast_core", "name": "兽核", "weight": 8, "qty": [1, 1]},
         ]}}}},
        {"id": "sect_rep", "kind": "reputation", "label": "宗门声望",
         "config": {"factions": ["青云宗", "万宝楼", "血影门", "散修盟"],
                    "tiers": [{"min": -1000, "label": "敌对"}, {"min": -40, "label": "冷淡"},
                              {"min": 0, "label": "无名"}, {"min": 30, "label": "记名"},
                              {"min": 70, "label": "内门"}]}},
        {"id": "cultivation", "kind": "custom", "label": "修行",
         "config": {"actions": {
             "meditate": {"label": "打坐引气",
                          "effects": [{"op": "advance_time", "minutes": 240},
                                      {"op": "xp", "delta": 10},
                                      {"op": "flag", "flag": "tried_meditation"}]},
             "gather": {"label": "上山采药",
                        "effects": [{"op": "advance_time", "minutes": 180},
                                    {"op": "loot", "table": "spirit"}]},
         }}},
        {"id": "xp", "kind": "progression", "label": "修为",
         "config": {"base_xp": 500, "growth": 2.0, "max_level": 8,
                    "per_level": {"int": 1, "con": 1}, "level_label": "境界"}},
    ],
    game={"title": "青冥界", "kind": "rpg",
          "resources": [{"key": "hp", "label": "气血", "value": 20, "min": 0, "max": 20, "color": "hp"},
                        {"key": "mp", "label": "灵力", "value": 0, "min": 0, "max": 0, "color": "mp"},
                        {"key": "gold", "label": "凡银", "value": 12, "min": 0, "max": 0, "color": "gold"}],
          "attributes": [{"key": "str", "label": "力量", "value": 8},
                         {"key": "dex", "label": "敏捷", "value": 10},
                         {"key": "int", "label": "根骨", "value": 11},
                         {"key": "con", "label": "体魄", "value": 9},
                         {"key": "cha", "label": "心性", "value": 9}],
          "meters": [{"key": "level", "label": "境界", "value": 0, "min": 0, "max": 8}],
          "tags": ["修仙", "灵脉"], "sheet": {"出身": "青石村采药少年", "灵根": "未检测"}},
    lore=[
        {"keys": ["基调", "文风"], "constant": True, "comment": "基调",
         "content": "修仙不是一路升级：灵气有浓度，功法有门槛，突破有代价。先让玩家感到“山里有东西”，再给解释。"},
        {"keys": ["灵泉", "后山", "水冷"], "comment": "灵泉",
         "content": "灵泉的水温比上个月低，石缝里有细小灵光；陈伯说这是“地脉翻身”，但不肯解释。", "constant": False},
        {"keys": ["仙人", "山上", "宗门"], "comment": "仙人传闻",
         "content": "村里老人说山上有仙人，但没人见过；沈砚听到这句话时，会下意识按住右腕。", "constant": False},
    ],
    map_blueprint={
        "start": "village",
        "core_nodes": [
            {"id": "village", "name": "青石村", "role": "start", "danger": 0,
             "desc": "山村靠一条溪，屋后就是上山采药的石阶；夜里能听见后山的风。", "market": "青石村"},
            {"id": "spring", "name": "后山灵泉", "role": "clue", "danger": 1,
             "desc": "泉眼在石壁下，水面比上个月低了一截，石缝里有细小的灵光。"},
            {"id": "luoxia", "name": "落霞山", "role": "gate", "danger": 2,
             "desc": "山门在雾里只剩一个轮廓，石阶尽头有断裂的牌坊。"},
            {"id": "town", "name": "青石镇", "role": "market", "danger": 1,
             "desc": "镇上有药铺、铁匠铺和一间挂着旧幡的当铺，凡人很少往山那边去。", "market": "青石镇"},
        ],
        "random_nodes": [
            {"id": "cave", "role": "dungeon", "danger": 3, "names": ["黑水洞", "枯藤洞", "落石洞"],
             "descs": ["洞口被藤蔓遮了一半，里面传来水滴声。",
                       "洞壁上有旧凿痕，深处有淡淡的灵气涌出。"]},
            {"id": "temple", "role": "ruin", "danger": 2, "names": ["山神庙", "废弃道观", "无名祠"],
             "descs": ["屋顶塌了一角，神像的脸被雨水磨平。",
                       "供桌上只剩一层冷灰，墙角却有一串新脚印。"]},
            {"id": "marsh", "role": "wild", "danger": 3, "names": ["黑水沼泽", "雾泽", "断桥泽"],
             "descs": ["水面浮着一层黑雾，踩下去会陷到脚踝。",
                       "断桥只剩半截，桥下有什么东西在慢慢游动。"]},
        ],
        "edges": [
            {"a": "village", "b": "spring", "minutes": [10, 20], "label": "后山石阶"},
            {"a": "village", "b": "town", "minutes": [40, 70], "label": "溪边土路"},
            {"a": "spring", "b": "luoxia", "minutes": [60, 120], "label": "断牌坊山道"},
            {"a": "town", "b": "luoxia", "minutes": [50, 90], "label": "官道"},
        ],
        "random_links": [
            {"id": "cave", "links": ["spring", "luoxia"]},
            {"id": "temple", "links": ["village", "luoxia"]},
            {"id": "marsh", "links": ["town", "luoxia"]},
        ],
        "rules": [
            "青石村、后山灵泉、落霞山、青石镇的名字与位置固定。",
            "每次开局从三个野外节点里抽两个，名字、描写和路程随机，但连接关系必须在青石村/灵泉/落霞山/青石镇之间。",
            "危险度：村 0，灵泉 1，镇 1，落霞山 2，野外节点 2-3。",
            "地图只改变外观与路程，不改变境界体系、灵脉方向和宗门关系。",
        ],
    },
)



TEMPLATES = {
    t["id"]: t for t in (_JRPG, _MYSTERY, _MANAGEMENT, _SURVIVAL,
                         _NARRATIVE, _COZY, _TABLETOP, _IMMERSIVE, _XIANXIA)
}


# ────────────────────────────── 世界根设定（canon） ──────────────────────────────
#
# 模板不只是“场景骨架”，还必须带一份开局前就锁死的世界根设定。这里每个世界
# 10 条 immutable fact：世界前提、力量规则、历史断层、地图节点、通行成本、
# 势力格局、社会秩序、经济底座、生死规则、玩家位置。细节留给 unknown，玩家
# 探索到再通过 canon_commit 升为 revealed；模板不预写整段历史。

def _canon_fact(subject, predicate, value, statement, tags=None):
    return {
        "subject": subject,
        "predicate": predicate,
        "value": value,
        "statement": statement,
        "status": "immutable",
        "locked": True,
        "source": "template",
        "tags": list(tags or []),
        "spoiler": "gm",
    }


def _canon_unknown(question, hint=""):
    return {"question": question, "hint": hint, "status": "unknown"}


def _canon_known(subject, predicate, value, statement, tags=None):
    fact = _canon_fact(subject, predicate, value, statement, tags)
    fact["status"] = "revealed"
    fact["locked"] = False
    return fact


def _canon_hidden(subject, predicate, value, statement, tags=None):
    return {
        "subject": subject,
        "predicate": predicate,
        "value": value,
        "statement": statement,
        "status": "hidden",
        "locked": True,
        "source": "template",
        "tags": list(tags or []),
        "spoiler": "gm",
    }


def _canon_rumor(statement, subject="传闻", predicate="内容", value="", tags=None):
    return {
        "subject": subject,
        "predicate": predicate,
        "value": value,
        "statement": statement,
        "status": "rumor",
        "locked": False,
        "source": "template",
        "tags": list(tags or []),
        "spoiler": "player",
    }


def _canon_bible(name, era, premise, genre, tone, facts, unknowns,
                 hidden=None, revealed=None, rumors=None):
    return {
        "version": 1,
        "world": {"name": name, "era": era, "premise": premise,
                  "genre": genre, "tone": tone},
        "immutable": facts,
        "revealed": list(revealed or []),
        "rumors": list(rumors or []),
        "hidden": list(hidden or []),
        "unknown": unknowns,
    }


WORLD_BIBLES = {
    "jrpg": _canon_bible(
        "艾瑟兰", "王国历 412 年",
        "旧王朝崩解后，边境公会填补王权真空；灰狼林里的旧战场正在重新醒来。",
        "奇幻 / 成长", "边境、旧伤、向上的希望",
        [
            _canon_fact("世界", "前提", "王权衰败，公会与行会维持边境秩序",
                        "艾瑟兰没有强势中央王权；边境靠冒险者公会、工匠行会和地方领主三方维持。", ["core"]),
            _canon_fact("力量", "规则与代价", "魔法需要媒介与咏唱，消耗体力，不能凭空造物",
                        "魔法必须有触媒或咏唱；每次施法消耗体力，不能复活死者，不能凭空创造活物。", ["rule", "power"]),
            _canon_fact("历史", "断层", "九十年前旧王朝内战，灰狼林是最后一处战场",
                        "九十年前旧王朝内战在此结束；王国放弃灰狼林，旧战场与万人坑至今未清理。", ["history"]),
            _canon_fact("历史", "近事", "三支商队在同一段路上失踪，公会才重新贴出委托",
                        "最近三支商队没有穿过灰狼林；公会以“清剿魔物”名义招募冒险者，实际在查旧战场。", ["history", "hook"]),
            _canon_fact("地图", "节点", "洛恩镇—灰狼林—废弃哨塔，沿河一条主路",
                        "洛恩镇在河边；灰狼林在镇北；废弃哨塔在林深处。三地之间只有一条可走的旧路。", ["map"]),
            _canon_fact("地图", "通行成本", "洛恩镇到灰狼林步行约半日，林中到哨塔再半日",
                        "骑马可缩短三分之一；夜里穿林风险翻倍；哨塔没有补给，必须自带火把与干粮。", ["map", "travel"]),
            _canon_fact("势力", "格局", "冒险者公会、工匠行会、旧王党残部",
                        "公会管委托与等级；行会管装备与价格；旧王党残部藏在边境，想借魔物之名收回旧地。", ["faction"]),
            _canon_fact("社会", "秩序", "冒险者必须登记；无公会牌者不能接委托、不能进城",
                        "洛恩镇以公会登记为身份；无牌者只能做零工；私下接委托会被公会追责。", ["society"]),
            _canon_fact("经济", "底座", "金币；药水靠草药，狼皮与兽核是硬通货",
                        "治疗药水由草药师制作，价格随草药收成浮动；灰狼皮可制甲，兽核是公会收购的施法材料。", ["economy"]),
            _canon_fact("生死", "规则", "气血归零为重伤濒死，不是立即死亡；无复活术",
                        "气血归零后进入濒死，需在当场用药物或判定救人；超过一场景未救则死亡，且不可复活。", ["death"]),
            _canon_fact("玩家", "位置", "见习冒险者，持临时公会牌，第一份委托在告示板上",
                        "玩家从洛恩镇公会门口开始；临时牌只能接最低阶委托，必须由老成员担保。", ["player"]),
        ],
        [
            _canon_unknown("废弃哨塔里到底有什么？", "旧战场、旧王党、魔物巢穴三种线索都可指向这里。"),
            _canon_unknown("公会会长格雷为什么隐瞒灰狼林的旧战史？", "他知道万人坑的位置，也知道谁在找它。"),
            _canon_unknown("灰狼林的爪印是魔物，还是有人在伪造？", "爪印比正常灰狼大一圈，但步距像人。"),
        ],
    ),
    "mystery": _canon_bible(
        "雾港", "民国十七年 · 深秋",
        "港口被雾、旧案和沉默包住；灯塔七年前烧过一次，最近又有人在等它亮。",
        "悬疑 / 调查", "雾、旧报纸、体面的谎言",
        [
            _canon_fact("世界", "前提", "雾港的秩序由巡捕房、码头帮和教会三方勉强维持",
                        "港口没有真正的统一政府；巡捕房管街面，码头帮管货，教会管穷人和死者。", ["core"]),
            _canon_fact("规则", "现实约束", "没有超自然力量；所有怪事都必须有人的动机",
                        "雾、灯、哭声都可以被解释成人为；如果出现无法解释的现象，先当作误认或骗局。", ["rule"]),
            _canon_fact("历史", "旧案", "七年前灯塔大火，七名守塔人失踪，名册被烧掉一半",
                        "官方结论是意外；实际名册上还有第八个名字，被巡捕房压了下来。", ["history", "secret"]),
            _canon_fact("历史", "近事", "有人在夜里重新点亮灯塔，随后出现无署名信",
                        "三周前灯塔短暂亮起；同一周，旅店收到没有署名的信，信里只写“别让它亮”。", ["history", "hook"]),
            _canon_fact("地图", "节点", "雾港码头—旅店—教堂—灯塔，沿港一条弧线",
                        "码头在东，旅店在中间，教堂在西，灯塔在防波堤尽头；雾天只能靠灯和钟声定位。", ["map"]),
            _canon_fact("地图", "通行成本", "码头到灯塔步行约一小时；雾天翻倍，夜间巡逻会拦人",
                        "涨潮时防波堤只露出半边；没有巡捕房通行证，夜里靠近灯塔会被带走。", ["map", "travel"]),
            _canon_fact("势力", "格局", "巡捕房要结案，码头帮要货，教会要死者安息",
                        "三方都不希望灯塔重新亮；但各自隐瞒的部分不同，谁先开口谁先死。", ["faction"]),
            _canon_fact("社会", "秩序", "港口宵禁；外来者必须住旅店并登记",
                        "宵禁后街面只允许巡捕与持证苦力；旅店老板必须抄报住客姓名，否则连坐。", ["society"]),
            _canon_fact("经济", "底座", "银元与铜板并行；胶片、威士忌、纱布是硬货",
                        "码头帮用银元结账，街面用铜板；胶片和纱布在黑市能换情报，威士忌用来买通夜班。", ["economy"]),
            _canon_fact("生死", "规则", "枪伤、溺水、火灾都可以致死；没有复活",
                        "致命伤按现实处理；尸体可以被调换、藏匿，但不能被“法术”救回。", ["death"]),
            _canon_fact("玩家", "位置", "外行调查员，受旅店老板私下委托，住在码头旅店",
                        "玩家没有官方身份；巡捕房视其为麻烦，码头帮视其为可用的外人。", ["player"]),
        ],
        [
            _canon_unknown("第八个守塔人是谁？", "名册残页、教会死亡登记、码头帮账本各有一半答案。"),
            _canon_unknown("谁在等灯塔亮？", "可能是幸存者、走私船，也可能是想把旧案翻出来的人。"),
            _canon_unknown("无署名信是谁写的？", "字迹像教会学校出来的，但纸是码头帮的货。"),
        ],
    ),
    "management": _canon_bible(
        "临川老街", "市井 · 春末",
        "老街夹在新商场和旧码头之间；一间小茶摊要在租金、货源和人情里活过第一个月。",
        "经营 / 人情", "烟火气、算盘、街坊的体面",
        [
            _canon_fact("世界", "前提", "老街正在被新商场挤出主街，旧码头仍养着半条街",
                        "新商场吸走年轻客；旧码头还有散货；老街的房东、商会、街坊三方互相牵制。", ["core"]),
            _canon_fact("规则", "现实约束", "没有超自然力量；经营成败由货源、现金流、人情决定",
                        "所有经营结果都要落到账、库存、租期和关系上；不允许“突然继承一笔钱”解决问题。", ["rule"]),
            _canon_fact("历史", "断层", "三十年前老街是茶马码头的主街，后来铁路通了就衰了",
                        "铁路绕开临川，码头只剩散货；老街的铺面一半靠老客，一半靠游客。", ["history"]),
            _canon_fact("历史", "近事", "新商场下月开业，房东要重签租约，茶商在压价",
                        "三件事撞在一起；玩家只有一个月现金流，错过续租就会被清退。", ["history", "hook"]),
            _canon_fact("地图", "节点", "茶摊—老街口—旧码头—茶山，步行半日可达",
                        "茶摊在街中段；老街口对着新商场；旧码头在西；茶山在城外，进货要半天。", ["map"]),
            _canon_fact("地图", "通行成本", "茶山进货往返一日；码头取货半日；新商场步行一刻钟",
                        "雨季茶山路会断；码头散货要等船；新商场只认月结，现金流会被拖住。", ["map", "travel"]),
            _canon_fact("势力", "格局", "商会、房东、街坊会；新商场是外部压力",
                        "商会管进货价，房东管租约，街坊会管口碑；新商场不直接出手，只抬租金和人工。", ["faction"]),
            _canon_fact("社会", "秩序", "老街讲人情和赊账；欠账不还，整条街都会知道",
                        "赊账靠面子，不靠合同；赖账一次，后面进货、借人手、办红白事都会被卡。", ["society"]),
            _canon_fact("经济", "底座", "铜板与银元并行；茶叶、茶点、绸缎是流水",
                        "粗茶走量，茶点留客，绸缎是送礼硬货；现金流比账面利润重要。", ["economy"]),
            _canon_fact("生死", "规则", "现实生死；经营失败是关门，不是角色死亡",
                        "角色不会因破产死亡；失败会失去铺面、信用和住处，但还能从头再来。", ["death"]),
            _canon_fact("玩家", "位置", "小摊掌柜，租着街中段半间铺面，手里只有一个月流水",
                        "玩家有手艺但没有靠山；第一个月要同时解决续租、备货和街坊信任。", ["player"]),
        ],
        [
            _canon_unknown("新商场背后是谁？", "可能是外地资本，也可能是老街房东联合起来抬价。"),
            _canon_unknown("茶商周老板为什么突然压价？", "他手里有一批来路不明的低价茶。"),
            _canon_unknown("旧码头夜里在卸什么？", "散货、私货，或者与新商场有关的东西。"),
        ],
    ),
    "survival": _canon_bible(
        "灰区", "崩坏第 47 天",
        "城市基础设施崩了四十七天；净水、药品和夜晚的安全同时不够。",
        "生存 / 压力", "灰霾、配给、谁值得救",
        [
            _canon_fact("世界", "前提", "崩坏不是一次性灾难，而是水、电、医疗逐层失效",
                        "没有统一政府；幸存者据点、拾荒者、旧军队残部各自管一小块。", ["core"]),
            _canon_fact("规则", "污染与感染", "灰霾会缓慢损伤呼吸；伤口感染不可逆，净水比食物贵",
                        "暴露在灰霾中每半日掉体力；伤口不处理会感染；感染到晚期不能靠药逆转。", ["rule", "health"]),
            _canon_fact("历史", "断层", "第四十六天夜里，最后一次全城广播后再没有官方消息",
                        "崩坏日之前有撤离令；大部分人没赶上；旧军队封了北区，没人知道里面还剩什么。", ["history"]),
            _canon_fact("历史", "近事", "水塔里传出还有干净水的传闻，三拨人先后去了没回来",
                        "传闻从拾荒者老周嘴里出来；他最后一次回来时，净水壶是满的，人却在发烧。", ["history", "hook"]),
            _canon_fact("地图", "节点", "据点—超市废墟—水塔—地铁口，四处在同一条街轴上",
                        "据点在东；超市在中；水塔在西；地铁口在南。越往西，灰霾越重。", ["map"]),
            _canon_fact("地图", "通行成本", "据点走到水塔要半日；负重会拖慢；夜里不能走",
                        "白天走开阔街面，半日到水塔；夜里灰霾更重且有拾荒者伏击；地铁口涨水时不能进。", ["map", "travel"]),
            _canon_fact("势力", "格局", "据点委员会、拾荒者、旧军队残部",
                        "委员会管配给但缺药；拾荒者管路线但要抽成；旧军队守北区，偶尔出来搜物资。", ["faction"]),
            _canon_fact("社会", "秩序", "配给制；外来者要交一份净水或等价物才能进据点",
                        "据点按人头配给；藏私会被驱逐；救人会消耗配给，但能换人手和情报。", ["society"]),
            _canon_fact("经济", "底座", "以物易物；净水、罐头、绷带、零件是四种硬通货",
                        "净水最贵；罐头次之；绷带和零件按需；旧币已经没人收。", ["economy"]),
            _canon_fact("生死", "规则", "感染与失血会死；没有复活；死亡会留下物资和债务",
                        "角色死亡后，随身物资可以被同伴取走，但会引发配给争议。", ["death"]),
            _canon_fact("玩家", "位置", "新手幸存者，刚进据点，只有一天配给和一只空水壶",
                        "玩家没有固定队伍；要先证明自己有用，才能拿到进入水塔行动的资格。", ["player"]),
        ],
        [
            _canon_unknown("水塔里还有没有干净水？", "水箱可能完好，也可能已经被污染。"),
            _canon_unknown("老周的发烧是感染还是别的原因？", "他可能碰过水塔里的东西。"),
            _canon_unknown("北区旧军队在守什么？", "仓库、实验室，或者封锁消息。"),
        ],
    ),
    "narrative": _canon_bible(
        "长夏", "毕业那年的夏天",
        "小城高中最后一个夏天；一封没送出的信，把三个人留在同一段走廊里。",
        "青春 / 关系", "蝉鸣、旧风扇、没说出口的话",
        [
            _canon_fact("世界", "前提", "小城高中，现实校园；没有超自然力量",
                        "故事只发生在学校、河边和旧电影院；所有转折都来自关系与选择。", ["core"]),
            _canon_fact("规则", "现实约束", "没有读心、没有时间回溯；说出口的话不能撤回",
                        "角色只能根据自己看到、听到、误会的部分行动；误会不能被“旁白”直接消除。", ["rule"]),
            _canon_fact("历史", "断层", "三年前玩家转学离开，又在这个夏天回来",
                        "玩家离开时没有告别；林夏和陈老师都知道原因不同，但都没说全。", ["history"]),
            _canon_fact("历史", "近事", "毕业前最后一个月，那封旧信被重新放回课桌",
                        "信是玩家当年写的；林夏发现后又放回去；陈老师看见了，但没有问。", ["history", "hook"]),
            _canon_fact("地图", "节点", "教学楼—河边—旧电影院—车站，步行一小时以内",
                        "学校在坡上；河边在坡下；旧电影院在街尾；车站在城外，是离开的唯一出口。", ["map"]),
            _canon_fact("地图", "通行成本", "学校到河边十分钟；到旧电影院二十分钟；到车站半小时",
                        "晚自习后校门会锁；河边没有路灯；末班车一天只有两趟。", ["map", "travel"]),
            _canon_fact("势力", "格局", "班级、家庭、教师办公室；没有反派组织",
                        "压力来自父母、成绩、同学眼光和即将到来的分离，不来自外部敌人。", ["faction"]),
            _canon_fact("社会", "秩序", "高考倒计时；恋爱被默认禁止但不被公开谈论",
                        "老师会睁一只眼闭一只眼；家长会突然出现；流言传播得比事实快。", ["society"]),
            _canon_fact("经济", "底座", "零花钱、冰棍、信纸、车票",
                        "钱只影响能不能买冰棍、信纸和车票；不构成阶层冲突。", ["economy"]),
            _canon_fact("生死", "规则", "现实生死；没有意外复活；离别是主要代价",
                        "角色不会因小伤死亡；真正的代价是错过、离开和关系破裂。", ["death"]),
            _canon_fact("玩家", "位置", "高三学生，刚回到原来的班级，坐在靠窗最后一排",
                        "玩家认识林夏和陈老师，但三年空白让每一句话都要重新校准。", ["player"]),
        ],
        [
            _canon_unknown("林夏为什么把信放回去？", "她可能看过，也可能只看到信封。"),
            _canon_unknown("陈老师知道玩家当年为什么离开吗？", "他知道一部分，但说出口会伤害另一个人。"),
            _canon_unknown("毕业那天谁会先走？", "车票、家庭、成绩都可能改变答案。"),
        ],
    ),
    "cozy": _canon_bible(
        "雾溪村", "初春",
        "山村靠溪水和季节过日子；新村民要在第一场春雨前把院子收拾出来。",
        "田园 / 日常", "潮湿的泥土、慢日子、邻里人情",
        [
            _canon_fact("世界", "前提", "雾溪村是现实山村，靠溪水、山地和季节农业维持",
                        "村里没有大危机；冲突来自土地、水源、老住户和新村民的生活习惯。", ["core"]),
            _canon_fact("规则", "现实约束", "没有超自然力量；作物、天气、体力都有现实限制",
                        "种下去不会立刻长出来；雨天不能翻地；体力不足会生病。", ["rule"]),
            _canon_fact("历史", "断层", "二十年前修水库，一半老屋迁走，村子从此只剩老人和空地",
                        "水库淹了旧祠堂；迁走的人偶尔回来；村委与老住户对土地归属仍有分歧。", ["history"]),
            _canon_fact("历史", "近事", "新村民租下溪边旧院，村长答应给一季时间试种",
                        "如果第一季没有收成，租约会被收回；老住户在观望，也有人想接手这块地。", ["history", "hook"]),
            _canon_fact("地图", "节点", "村口—溪边旧院—后山—镇集，步行半日以内",
                        "村口有公交；旧院在溪边；后山有野果和菌子；镇集在山外，走路要半日。", ["map"]),
            _canon_fact("地图", "通行成本", "旧院到镇集半日；后山来回两小时；雨天溪水会涨",
                        "公交一天两趟；雨后溪桥不能过；后山夜里没有灯。", ["map", "travel"]),
            _canon_fact("势力", "格局", "村委、老住户、外来租户",
                        "村委管地和水；老住户管人情和闲话；外来租户没有投票权，只能靠做事站稳。", ["faction"]),
            _canon_fact("社会", "秩序", "村里讲互助；不参加集体劳动的人会被慢慢排除",
                        "借工具、换工、红白事都要到场；不到场不会立刻翻脸，但会被记着。", ["society"]),
            _canon_fact("经济", "底座", "现金不多；种子、木料、劳力都可以换",
                        "镇集收农产品但压价；村里更认换工；现金主要用于买种子和药。", ["economy"]),
            _canon_fact("生死", "规则", "现实生死；农事失败不是死亡，是失去租约和信任",
                        "角色会因劳累生病；没有奇迹治愈；失败会让人离开村子。", ["death"]),
            _canon_fact("玩家", "位置", "新村民，租下溪边旧院，手里有种子和一个月口粮",
                        "玩家没有地权，只有一季试种权；要先赢得村长和老住户的最低信任。", ["player"]),
        ],
        [
            _canon_unknown("旧院前主人为什么搬走？", "可能和水库、债务或一段旧关系有关。"),
            _canon_unknown("后山那片荒地为谁所有？", "村委、老住户和迁走的人各有说法。"),
            _canon_unknown("今年春雨会早来还是晚来？", "老农看云，村长看历书，答案不一致。"),
        ],
    ),
    "tabletop": _canon_bible(
        "灰岩堡", "第三纪元",
        "边境城堡压着更古老的地下墓穴；雨夜里，守备队不敢下墓，只贴出悬赏。",
        "跑团 / 探索", "雨、石阶、火把、旧誓言",
        [
            _canon_fact("世界", "前提", "灰岩堡是边境要塞，地下墓穴比城堡更古老",
                        "城堡建在旧王国要塞上；墓穴在城堡与旧礼拜堂之间，入口被守备队封了一半。", ["core"]),
            _canon_fact("力量", "规则与代价", "魔法稀少且需要符文；火把与体力是下墓的硬成本",
                        "施法要触媒或符文；每场战斗后火把会消耗；墓穴里不能自然恢复生命。", ["rule", "power"]),
            _canon_fact("历史", "断层", "三百年前旧王国在此抵抗北境，撤退时封了墓门",
                        "旧王国把阵亡者与“不该带走的东西”一起封进墓穴；教会后来试图封圣，失败后撤离。", ["history"]),
            _canon_fact("历史", "近事", "最近墓穴里有东西在动，守备队长罗兰压下消息",
                        "罗兰三周前派人下去，只回来一个；他把报告扣下，只贴出悬赏找外人。", ["history", "hook"]),
            _canon_fact("地图", "节点", "灰岩堡—地下墓穴—旧礼拜堂，靠吊桥与山道连接",
                        "城堡在崖上；墓穴入口在城堡地窖；旧礼拜堂在崖下；吊桥是唯一正门。", ["map"]),
            _canon_fact("地图", "通行成本", "城堡到墓穴一刻钟；到旧礼拜堂要下崖半小时；夜里吊桥升起",
                        "下崖只能走旧石阶，雨天会滑；墓穴深处需要第二支火把；旧礼拜堂没有补给。", ["map", "travel"]),
            _canon_fact("势力", "格局", "守备队、盗贼公会、教会残部",
                        "守备队要封住墓穴；盗贼公会想拿墓里的古币；教会残部想找回被封的圣物。", ["faction"]),
            _canon_fact("社会", "秩序", "城堡法；夜里宵禁；下墓需要队长手令",
                        "没有手令下墓会被守备队当成盗墓贼；盗贼公会认暗号不认人；教会残部只认旧誓。", ["society"]),
            _canon_fact("经济", "底座", "金币；火把、麻绳、药水是下墓硬货；古币可换情报",
                        "城堡物价高；旧礼拜堂附近的黑市收古币；守备队不发补给，只给悬赏。", ["economy"]),
            _canon_fact("生死", "规则", "气血归零为濒死；墓穴里没有复活；尸体可能被东西利用",
                        "濒死需当场处理；死在墓里会被黑暗中的东西带走；复活不存在，只有未死的传言。", ["death"]),
            _canon_fact("玩家", "位置", "雇佣兵，刚接悬赏，持守备队临时手令",
                        "玩家从城堡大厅开始；手令只允许进墓穴第一层；罗兰要玩家带回“报告”，不是清理墓穴。", ["player"]),
        ],
        [
            _canon_unknown("墓穴墙上的符号是谁刻的？", "比旧王国更古老；教会说那是异端，盗贼说那是地图。"),
            _canon_unknown("罗兰三周前派下去的人遇到了什么？", "唯一回来的人疯了，只重复“门在下面”。"),
            _canon_unknown("旧礼拜堂的圣物还在不在？", "教会残部在找，盗贼公会也在找。"),
        ],
    ),
    "immersive": _canon_bible(
        "科尔沃城", "雾季",
        "运河城在宵禁和雾里运转；每条路都能走，但每条路都会留下痕迹。",
        "沉浸 / 自由", "煤烟、湿石板、被看见的代价",
        [
            _canon_fact("世界", "前提", "科尔沃是运河城，旧贵族、城卫和黑市三方分权",
                        "城卫管宵禁，贵族管码头税，黑市管情报；没有一方能独掌全城。", ["core"]),
            _canon_fact("规则", "现实约束", "没有魔法；潜行、说服、暴力、贿赂都可行，但都会留痕",
                        "每次行动都会改变警觉度或关系；不存在无痕迹的完美解法。", ["rule"]),
            _canon_fact("历史", "断层", "二十年前旧王朝退位，档案馆被封，名单被分成三份",
                        "旧王朝把效忠者名单拆成三份：城卫、教会、黑市各持一份；没人有完整版。", ["history"]),
            _canon_fact("历史", "近事", "雾季开始后，档案馆夜里有灯；城卫加了双岗",
                        "有人在找第三份名单；黑市商人薇拉愿意出钱，但她只给一半定金。", ["history", "hook"]),
            _canon_fact("地图", "节点", "运河区—钟楼—档案馆，水陆两条路",
                        "运河区在低处；钟楼在城中；档案馆在高处；水路快但会被巡夜人看见。", ["map"]),
            _canon_fact("地图", "通行成本", "运河区到档案馆陆路四十分钟，水路二十分钟但暴露风险高",
                        "宵禁后陆路要绕开钟楼；水路可以直达后门，但船夫会记住乘客。", ["map", "travel"]),
            _canon_fact("势力", "格局", "城卫、黑市、旧贵族",
                        "城卫要维持宵禁；黑市要名单换钱；旧贵族想拿名单清洗叛徒。", ["faction"]),
            _canon_fact("社会", "秩序", "宵禁；通行证；黑市认暗号不认身份",
                        "没有通行证夜里会被抓；黑市不问来历但要抵押；贵族用宴会代替公开审判。", ["society"]),
            _canon_fact("经济", "底座", "金币；封口费、撬锁器、暗色斗篷是硬货",
                        "城卫的罚金可以用钱抵；黑市收金币也收情报；贵族用欠条拖账。", ["economy"]),
            _canon_fact("生死", "规则", "现实生死；被杀会留下尸体和警觉度；没有复活",
                        "死亡会让城卫加岗、黑市涨价、贵族灭口；尸体本身就是线索。", ["death"]),
            _canon_fact("玩家", "位置", "无名潜入者，住在运河区，手里只有撬锁器和一张假通行证",
                        "玩家没有靠山；薇拉是第一个客户，城卫布伦是第一个风险。", ["player"]),
        ],
        [
            _canon_unknown("第三份名单在谁手里？", "档案馆、教会、旧贵族，三方都可能。"),
            _canon_unknown("薇拉为什么只要一半名单？", "她可能只要其中几个名字，或者她自己就在名单上。"),
            _canon_unknown("钟楼的巡夜人布伦在替谁做事？", "城卫、旧贵族，或者他自己的债主。"),
        ],
    ),
    "xianxia": _canon_bible(
        "青冥界", "天衍历 317 年",
        "灵气是天地根本。灵脉决定聚落、宗门和战争；三千年前灵潮退去，底层灵脉正在枯竭，凡人只看见泉水变冷。",
        "修仙 / 成长", "山雨、古观、灵气的代价",
        [
            _canon_fact("世界", "前提", "灵气是天地根本，灵脉决定聚落与宗门兴衰",
                        "青冥界的灵气来自地脉；灵脉经过的地方才有修士聚落、灵田和宗门。灵脉枯竭，法术、丹药、阵法都会失效。", ["core"]),
            _canon_fact("力量", "规则", "修炼需要灵根、功法与灵气浓度；施法消耗灵力，不能凭空造物",
                        "没有灵根不能引气入体；功法决定上限；同一法术在灵气稀薄处威力减半。不能复活死者，不能凭空创造活物。", ["rule", "power"]),
            _canon_fact("力量", "代价", "突破要靠功法、丹药和灵气，失败会伤道基；越阶斗法有反噬",
                        "每次破境都要满足资源与心境；强行越阶会损伤经脉、引爆心魔，甚至引动天劫。", ["rule", "cost"]),
            _canon_fact("历史", "断层", "三千年前灵潮退去，宗门封山，凡俗与修真界从此断裂",
                        "天衍历以前灵气充盈；灵潮退后，大宗门封闭山门，凡俗王朝只留下“仙人不问世事”的旧约。", ["history"]),
            _canon_fact("历史", "近事", "三个月前青石村灵泉变冷；落霞山灵脉有异动；一名外门弟子失踪",
                        "灵泉变冷与落霞山灵脉异动同时发生；青云宗外门弟子沈砚在附近失踪，宗门只派了一名执事来查。", ["history", "hook"]),
            _canon_fact("地图", "框架", "青石村—后山灵泉—落霞山—青石镇；更远处是云梦泽与天衍城",
                        "青石村在灵脉末梢；后山灵泉是末梢泉眼；落霞山是青云宗外围山门；青石镇是凡俗集市。云梦泽在西南，天衍城在东南。", ["map"]),
            _canon_fact("地图", "通行成本", "凡人走山路和官道；修士御剑或灵舟更快，但会暴露灵气",
                        "青石村到灵泉约一刻钟；到青石镇约一个时辰；到落霞山要走半天。夜里山路有妖兽，御剑会留下灵气痕迹。", ["map", "travel"]),
            _canon_fact("势力", "格局", "青云宗、万宝楼、血影门、散修盟、凡俗王朝",
                        "青云宗掌落霞山灵脉；万宝楼掌坊市与灵石兑换；血影门在云梦泽活动；散修盟无固定山门；凡俗王朝只管凡人城池。", ["faction"]),
            _canon_fact("社会", "秩序", "仙凡有别；宗门收徒；散修无籍；魔道通缉；凡人大多不知灵气",
                        "宗门在山门内执法；凡俗王朝管不了修士；散修没有宗门背书，进城要登记；血影门被各国通缉但仍有暗市。", ["society"]),
            _canon_fact("经济", "底座", "凡人用铜钱和银两；修士用灵石；灵石也是修炼资源",
                        "凡人集市用铜钱/碎银；修士坊市用下品、中品、上品灵石；灵石可被吸收修炼，也可布阵、炼器、买命。", ["economy"]),
            _canon_fact("生死", "规则", "寿元随境界增长；死亡不可复活；夺舍是禁术；高阶修士也会死于天劫",
                        "凡人寿约七十；修士寿元随境界增加。死亡不可逆；夺舍会留下因果；天劫失败会道消。", ["death"]),
            _canon_fact("玩家", "位置", "林川，十六岁，青石村采药少年；没有测过灵根，只知灵泉变冷和山里有仙人传说",
                        "林川父母早亡，靠采药换粮；他见过沈砚手腕上的灵纹，但不知道那是什么；他身上有十二枚铜钱和三日干粮。", ["player"]),
        ],
        [
            _canon_unknown("灵泉下面到底有什么？", "泉眼连着一条快枯竭的灵脉；下面可能有一处旧阵或一具尸骸。"),
            _canon_unknown("沈砚在青石村等谁？", "他在等青云宗的追兵，还是在等一个能帮他解开锁印的人？"),
            _canon_unknown("林川有没有灵根？", "没有测过；陈伯可能知道，但不愿说。"),
        ],
        hidden=[
            _canon_hidden("修仙体系", "境界阶梯", "凡人→炼气→筑基→金丹→元婴→化神→炼虚→合体→大乘→渡劫飞升",
                          "青冥界的正统修炼路径是：凡人引气入体成为炼气修士，之后筑基、结丹、化婴、化神、炼虚、合体、大乘。大乘圆满后渡飞升天劫；此界近三千年无人成功。", ["cultivation", "system"]),
            _canon_hidden("修仙体系·炼气", "境界职责", "引气入体，一至九层；寿元约百岁；能画符、御物、踏风；不能真正御剑飞行",
                          "炼气期把天地灵气引入经脉，分一至九层。一层可感气，三层可画低阶符，六层可御物，九层可踏风短跃。瓶颈是灵根品质与灵气浓度；灵气不足会卡在层数上，强行冲关会伤经脉。", ["cultivation", "realm"]),
            _canon_hidden("修仙体系·筑基", "境界职责", "筑道基，分初/中/后期；寿元约二百；可短途御剑、布小阵",
                          "筑基期把灵气压缩成道基，决定后续金丹的品质。初期能短途御剑，中期可布小阵，后期可引动一方法术。瓶颈是道基不稳、心魔和筑基丹；失败会跌回炼气。", ["cultivation", "realm"]),
            _canon_hidden("修仙体系·金丹", "境界职责", "结金丹；寿元约三百；可御剑飞行、祭炼本命法器",
                          "金丹期把道基凝结成金丹，灵力性质稳定。可御剑飞行、祭炼本命法器、以丹火炼器。瓶颈是结丹失败、丹毒、雷劫；金丹品质决定能否化婴。", ["cultivation", "realm"]),
            _canon_hidden("修仙体系·元婴", "境界职责", "碎丹成婴；寿元约五百至八百；元婴可离体、神念外放",
                          "元婴期金丹化婴，神念可外放探查，元婴能短暂离体。可夺舍（禁术）、可布大型阵法。瓶颈是婴变、心魔、夺舍因果；元婴受损会跌境。", ["cultivation", "realm"]),
            _canon_hidden("修仙体系·化神", "境界职责", "神念化域；寿元约一千；可引动天地灵气",
                          "化神期神念与天地共鸣，能在一域内引动灵气、改变天象。可开辟洞天、炼制灵宝。瓶颈是神与形合、天劫；道心不稳会被天地同化。", ["cultivation", "realm"]),
            _canon_hidden("修仙体系·炼虚", "境界职责", "炼虚合道；寿元约两千；可短暂遁入虚空、跨越阵法",
                          "炼虚期开始触碰空间法则，能短暂遁入虚空、穿过低阶阵法。可炼制虚空法器。瓶颈是虚空反噬、道心裂痕；迷失虚空会形神俱灭。", ["cultivation", "realm"]),
            _canon_hidden("修仙体系·合体", "境界职责", "肉身与天地合；寿元约三千；可移山填海",
                          "合体期肉身与天地灵气合一，能移山填海、长时间不食烟火。可镇守一域灵脉。瓶颈是合体天劫、因果反噬；杀孽过重会引动心魔。", ["cultivation", "realm"]),
            _canon_hidden("修仙体系·大乘", "境界职责", "大乘圆满；寿元约五千；可开宗立派、镇压一域",
                          "大乘期接近此界极限，能开宗立派、镇压一域、改写小范围天象。瓶颈是飞升天劫与天道功德；功德不足会道消，功德圆满可渡劫飞升。", ["cultivation", "realm"]),
            _canon_hidden("修仙体系·渡劫", "境界职责", "大乘之后的最后一道门；成功飞升，失败道消",
                          "渡劫不是境界，而是大乘圆满后的飞升天劫。雷劫会照见道心与因果；此界近三千年无人成功，最近一次失败在落霞山，留下“断牌坊”。", ["cultivation", "realm", "history"]),
            _canon_hidden("经济", "货币体系", "凡人铜钱/银两；修士下品/中品/上品灵石；1中品=100下品，1上品=100中品",
                          "凡人用铜钱和碎银；修士坊市用灵石。下品灵石供炼气/筑基吸收，中品供金丹/元婴，上品供化神以上。灵石也是布阵、炼器、买命的硬通货；凡银买不到灵石。", ["economy", "currency"]),
            _canon_hidden("修炼", "资源与门槛", "灵根分五行、杂灵根、天灵根；功法决定上限；丹药可辅突破但有丹毒",
                          "灵根决定引气速度与法术亲和；杂灵根慢但稳，天灵根快但易遭觊觎。功法分凡/黄/玄/地/天五阶；丹药可辅助破境，但服多了会积丹毒，降低下一次突破成功率。", ["cultivation", "resource"]),
            _canon_hidden("势力", "灵脉真相", "青云宗掌落霞山灵脉；万宝楼掌坊市；血影门在云梦泽；散修盟无固定山门",
                          "青石村在灵脉末梢，所以只有一口灵泉；落霞山是青云宗外围，山门内有筑基长老；万宝楼在青石镇设暗铺；血影门在云梦泽挖一条旧灵脉；散修盟靠坊市抽成。", ["faction", "map", "truth"]),
            _canon_hidden("人物", "沈砚身份", "青云宗外门弟子，偷带半块灵脉图逃出，被同门追杀；右腕灵纹是宗门锁印",
                          "沈砚不是普通外乡人。他是青云宗外门弟子，偷了半块灵脉图逃到青石村，右腕的灵纹是宗门锁印，封住了大半修为。追他的同门已经在青石镇落脚。", ["npc", "secret"]),
        ],
        revealed=[
            _canon_known("林川", "身世", "青石村采药少年，父母早亡，靠采药换粮",
                        "林川十六岁，住在青石村溪边；父母早亡，靠采药和替陈伯跑腿换粮。", ["player", "known"]),
            _canon_known("灵泉", "近况", "三个月前开始变冷，水面下降，夜里石缝有光",
                        "林川亲眼见过灵泉变冷；水面比上个月低了一截，夜里石缝偶尔有细小灵光。", ["known", "hook"]),
            _canon_known("陈伯", "态度", "知道些什么，但不愿说",
                        "林川问过陈伯灵泉的事；陈伯只说“地脉翻身”，之后不再解释。", ["known", "npc"]),
            _canon_known("沈砚", "现状", "村口破庙住着一个外乡人，右手腕缠布",
                        "林川见过沈砚；他脸色苍白，右手腕一直缠着布，布下有淡淡的灵纹。林川不知道灵纹是什么。", ["known", "npc"]),
            _canon_known("青石镇", "货币", "镇上用铜钱和碎银，药铺收草药",
                        "林川去青石镇卖过草药；镇上用铜钱和碎银，药铺赵掌柜收止血草。", ["known", "economy"]),
        ],
        rumors=[
            _canon_rumor("村里老人说，山上有仙人；没人见过，但每年都有人上山不回来。", "仙人", "传闻", "山上有仙人", ["rumor"]),
            _canon_rumor("青石镇有人说，最近有外地人在打听一个手腕缠布的年轻人。", "沈砚", "被打听", "外地人在找他", ["rumor", "npc"]),
        ],
    ),
}

for _tid, _bible in WORLD_BIBLES.items():
    TEMPLATES[_tid]["world_bible"] = _bible

CORE_TEMPLATE_IDS = tuple(TEMPLATES.keys())


# ────────────────────────────── 公共 API ──────────────────────────────

def list_templates() -> list:
    """模板目录（面板与宿主都用）：id/名称/题材/循环/体系数/事业线数。"""
    out = []
    for tid, t in TEMPLATES.items():
        out.append({
            "id": tid, "name": t["name"], "genre": t["genre"], "loop": t["loop"],
            "notes": t["notes"], "systems": len(t.get("systems") or []),
            "questlines": len(t.get("questlines") or []),
            "entities": len(t.get("entities") or []),
            "places": len(t.get("places") or {}),
            "lore": len(t.get("lore") or []),
            "canon_facts": len((t.get("world_bible") or {}).get("immutable") or []),
            "canon_hidden": len((t.get("world_bible") or {}).get("hidden") or []),
            "map": bool(t.get("map_blueprint")),
        })
    return out


def get(tid: str) -> dict:
    """取模板的深拷贝（调用方可随意修改，不会污染库）。"""
    key = str(tid or "").strip()
    if key not in TEMPLATES:
        raise ValueError("模板不存在: %r（可用: %s）" % (tid, ", ".join(TEMPLATES)))
    return copy.deepcopy(TEMPLATES[key])


def apply_overrides(template: dict, overrides: dict | None = None) -> dict:
    """把 overrides 合并进模板（深合并 dict，列表整体替换）。返回新对象。"""
    if not overrides:
        return template
    if not isinstance(overrides, dict):
        raise ValueError("overrides 必须是对象")
    merged = copy.deepcopy(template)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _deep_merge(base: dict, patch: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def to_bundle(tid: str, overrides: dict | None = None, name: str = "",
              player_name: str = "") -> dict:
    """模板 → 设定包（settings/*.setting.json 同构，可直接 load_setting / build_state）。"""
    tpl = apply_overrides(get(tid), overrides)
    world_flags = list(tpl["world_flags"])
    # 模板用 `visibility: {"flag": "__start__"}` 表示“开局即浮现”。
    # 这是模板语法，不是玩家世界里真实存在的一个 flag；转 bundle 时补上，
    # 否则新开局的所有事业线都会停在 dormant，玩家看不到主线。
    if any((q.get("visibility") or {}).get("flag") == "__start__"
           for q in (tpl.get("questlines") or [])):
        if "__start__" not in world_flags:
            world_flags.insert(0, "__start__")
    bundle_name = name or tpl["name"]
    # 带地图模板的每一局用“局名”派生 seed：同一局重开可复现，不同局名会得到不同地图。
    # 老模板没有 map_blueprint，继续用固定 seed，避免无谓地改变既有存档行为。
    if tpl.get("map_blueprint"):
        seed = int(hashlib.sha1(bundle_name.encode("utf-8")).hexdigest()[:8], 16)
    else:
        seed = 20261014
    bundle = {
        "name": bundle_name,
        "note": tpl["notes"],
        "seed": seed,
        "world": tpl["world"],
        "player": tpl["player"],
        "entities": tpl["entities"],
        "market": tpl["market"],
        "relations": tpl["relations"],
        "world_flags": world_flags,
        "level_tiers": tpl["level_tiers"],
        "terms": tpl["terms"],
        "places": {k: (v if isinstance(v, dict) else {"desc": str(v)})
                   for k, v in (tpl.get("places") or {}).items()},
        "lore": tpl["lore"],
        "world_bible": tpl.get("world_bible") or {},
        "map_blueprint": tpl.get("map_blueprint") or {},
        "currency": tpl["currency"],
        "ui": tpl["ui"],
        "playbook": tpl["playbook"],
        "questlines": tpl["questlines"],
        "systems": tpl.get("systems") or [],
        "game": tpl.get("game") or {},
    }
    if player_name:
        bundle["player"]["name"] = str(player_name)[:40]
    return bundle


def validate(tpl: dict) -> list:
    """结构校验：返回问题列表（空列表 = 通过）。模板必须"基础件齐全"。"""
    problems = []
    if not isinstance(tpl, dict):
        return ["模板不是对象"]
    for key in ("id", "name", "genre", "loop"):
        if not str(tpl.get(key) or "").strip():
            problems.append("缺少 %s" % key)
    world = tpl.get("world") or {}
    if not world.get("name"):
        problems.append("world.name 缺失")
    player = tpl.get("player") or {}
    if not player.get("name"):
        problems.append("player.name 缺失")
    if not isinstance(player.get("attrs"), dict):
        problems.append("player.attrs 缺失")
    for key in ("hp", "hp_max", "gold"):
        if key not in player:
            problems.append("player.%s 缺失" % key)
    if not tpl.get("level_tiers"):
        problems.append("level_tiers 为空")
    if not tpl.get("places"):
        problems.append("places 为空")
    if not tpl.get("market"):
        problems.append("market 为空")
    if not tpl.get("entities"):
        problems.append("entities 为空")
    playbook = tpl.get("playbook") or {}
    if not playbook.get("loop"):
        problems.append("playbook.loop 缺失")
    if not isinstance(playbook.get("progress"), dict):
        problems.append("playbook.progress 缺失")
    if not isinstance(playbook.get("failure"), dict):
        problems.append("playbook.failure 缺失")
    if not playbook.get("beat"):
        problems.append("playbook.beat 缺失")
    if not tpl.get("terms"):
        problems.append("terms 为空")
    if not tpl.get("lore"):
        problems.append("lore 为空")
    bible = tpl.get("world_bible") or {}
    if len(bible.get("immutable") or []) < 8:
        problems.append("world_bible.immutable 少于 8 条根设定")
    if not bible.get("unknown"):
        problems.append("world_bible.unknown 为空（探索迷雾没有入口）")
    hidden = bible.get("hidden") or []
    if hidden and len(hidden) < 6:
        problems.append("world_bible.hidden 少于 6 条世界默认（主角未知）设定")
    for i, fact in enumerate(hidden):
        if not isinstance(fact, dict) or not fact.get("statement"):
            problems.append("world_bible.hidden[%d] 缺 statement" % i)
    if not tpl.get("questlines"):
        problems.append("questlines 为空")
    if not tpl.get("systems"):
        problems.append("systems 为空")
    game = tpl.get("game") or {}
    if not game.get("resources"):
        problems.append("game.resources 为空")
    if not game.get("attributes"):
        problems.append("game.attributes 为空")
    if not game.get("kind"):
        problems.append("game.kind 缺失")
    # 引用完整性：place.market 必须指向 market 里存在的地点
    market_locs = {m.get("location") for m in (tpl.get("market") or []) if isinstance(m, dict)}
    for pname, pinfo in (tpl.get("places") or {}).items():
        if isinstance(pinfo, dict) and pinfo.get("market") and pinfo["market"] not in market_locs:
            problems.append("places[%s].market 指向不存在的市场 %r" % (pname, pinfo["market"]))
    place_names0 = set((tpl.get("places") or {}).keys())
    # 地图蓝图：起点必须存在；固定节点名称必须能在 places 里找到；
    # 边必须引用已知节点。随机节点允许只存在于蓝图，由 mapgen 生成。
    blueprint = tpl.get("map_blueprint") or {}
    if blueprint:
        core = {n.get("id"): n for n in (blueprint.get("core_nodes") or []) if isinstance(n, dict)}
        if blueprint.get("start") not in core:
            problems.append("map_blueprint.start 不在 core_nodes")
        for node in core.values():
            if node.get("name") and node["name"] not in place_names0:
                problems.append("map_blueprint 固定节点 %r 不在 places" % node["name"])
        node_ids = set(core)
        node_ids.update(n.get("id") for n in (blueprint.get("random_nodes") or []) if isinstance(n, dict))
        for edge in (blueprint.get("edges") or []):
            if edge.get("a") not in node_ids or edge.get("b") not in node_ids:
                problems.append("map_blueprint 边引用未知节点: %r" % (edge,))
    # 事业线谓词的 visited 目标必须在 places 里
    place_names = set((tpl.get("places") or {}).keys())
    for quest in tpl.get("questlines") or []:
        for stage in (quest.get("stages") or []):
            cond = stage.get("exit_if")
            if isinstance(cond, dict) and cond.get("visited") and cond["visited"] not in place_names:
                problems.append("quest %s stage %s 的 visited=%r 不在 places 里"
                                % (quest.get("id"), stage.get("id"), cond["visited"]))
    return problems
