# World Walker

**v1.12.0** · [English](README.md) · **简体中文** · [架构](ARCHITECTURE.md) · [玩法层](docs/GAMEPLAY.md) · [更新日志](CHANGELOG.md)

> **你说话，AI 演，引擎判，存档记。**

World Walker 是**单人 AI 跑团 / 互动叙事引擎**，不是游戏助手，也不是后台管理台。
打开一个页面，先告诉它你想玩什么类型、怎么玩、以谁的身份进去，然后就像和真人 GM
聊天一样直接玩。没有外部宿主要接，没有第二个 App 要开。

模型层是厂商中立的：任何支持 OpenAI-compatible `/chat/completions` 的端点都能用。
你只填 `base_url`、`api_key`、`model`；自带网关、本地模型、聚合平台都行，没有厂商绑定。

确定性的部分是叙述者不该乱编的东西：血量、价格、背包、关系、钟、线索、存档与回放。
AI 写场面，引擎拥有事实。

`206 个规则函数` · `67 个 MCP 工具` · `26 个玩家工具` · `4 套设定包` · `8 套模板` ·
`20 个可执行自检` · `0 个运行时依赖`

## 它解决什么

多数“AI 跑团”死在三个地方。World Walker 把这三件事写进契约，而不是写进更长的提示词。

| 失败 | 常见情况 | World Walker 的做法 |
|---|---|---|
| **AI 替你玩** | 它写你的内心、决定、下一句话 | GM 只能写世界和 NPC，不能替玩家做决定；玩家代理权是硬规则 |
| **NPC 全知** | 每个 NPC 都像读过整本设定集 | NPC 只能用 `memory(action=known, character=...)` 返回的事实；不知道就回避、撒谎或反问 |
| **回合没有代价** | 文笔很好，但血量、线索、钟、关系一项都没变 | 每回合先填场面卡，回合后做审计；没有可见变化的回合会被标出来 |

战役是**玩出来的**，像真人 GM 带桌，不是小说式预写。开局先问类型、玩法、角色、基调、
难度和边界；之后每回合是 `场面卡 → 玩家行动 → 世界反应 → 状态变化 → 下一个钩子`。

## 安装

```bash
pip install -e ".[mcp]"      # 核心仅标准库；mcp 是 MCP 模式的可选依赖
```

接入任意 MCP 客户端（Claude Code / Codex / Cursor / opencode）：

```json
{ "mcpServers": { "world-games": { "command": "world-games-mcp" } } }
```

`world-walker-mcp` 仍作为兼容别名可用。

远程 agent 也可以走 HTTP 接入，不必经 stdio：

```bash
wg mcp --http --port 8620   # 客户端连 http://127.0.0.1:8620/mcp 即可
```

## 直接开玩

```bash
pip install -e ".[mcp]"
wg init my-game.json
wg play --state my-game.json
```

`wg play` 启动本地页面。打开 `http://127.0.0.1:8899/` 就是大厅：继续旧局，或开一个新世界。
不需要外部宿主、插件或第二个 App。

玩家界面只有一屏：左边叙事流，右边窄栏（角色/任务/人情/世界），底部一个输入框。
旧管理台、翻译层、主题脚本和离线图表库都已移除；玩家壳是原生 HTML/CSS/JS，没有构建链。

## 模型

World Walker 不绑定厂商。模型层只假设一个 OpenAI-compatible `/chat/completions` 端点：

```json
{ "base_url": "https://你的网关/v1", "api_key": "sk-...", "model": "任意模型" }
```

在页面里点“模型 · 去设置”，或用 `WW_MODEL_BASE_URL / WW_MODEL_API_KEY / WW_MODEL_NAME`。
配置文件在 `~/.world-walker/model.json`，权限 `0600`。没有厂商列表、没有厂商 SDK、没有隐藏回退。

## 开局先问你想玩什么（Session Zero）

新游戏不是先选模板，而是先问四步：

1. **类型** — 悬疑、奇幻、武侠仙侠、科幻、都市、历史、恋爱、恐怖、生存、日常。
2. **玩法** — 探索解谜、生存压力、权谋经营、关系情感、战斗成长、调查恐怖、轻松日常。
3. **角色** — 随机、自己写一句、用模板预设。
4. **体验** — 基调、难度、内容边界、可选世界覆盖。

引擎按类型自动配规则骨架（武侠仙侠→`tabletop`，悬疑→`mystery`），然后写一张**开局卡**：
你在哪、你是谁、什么已经在动、死亡规则、三个钩子、核心问题。模板只给骨架和种子，不预写剧情。

## 一回合，完整流程

**玩家：** 我推门进去，先看柜台后面的人。

```
场面卡      → 你在灰岩堡的酒馆；罗兰在柜台后；他不想让你下墓穴；悬赏还贴着
玩家行动    → 推门、观察
世界反应    → 罗兰先开口，试图把话题岔开
状态变化    → 关系/线索/钟至少变一项
下一个钩子  → 他手边有一把不属于他的钥匙
```

模型写正文，引擎结算数值并落盘。如果这一回合没有产生任何后果，审计会标出来，下一回合可以修正。

## 工具

模型看到的是 26 个玩家工具，不是旧的 67 个 MCP 工具面：

`inspect` `progress` `story` `memory` `context` `characters` `sheet` `systems` `worlds` `calc`
`panel` `new_game` `open_game` `saves` `snapshot` `combat` `combat_preview` `trade` `social`
`karma` `tick` `advance` `travel` `use_item` `roll` `configure`

MCP 仍可供高级宿主使用，但它不再是前门。玩家页面才是。

## 体系与模板

### 七类可插拔体系

玩法机制是**数据**，不是代码。运行时随时增删。

| 体系 | kind | 管什么 | 动作 |
|---|---|---|---|
| 时间 | `time` | 日/时/分、季节、天气 | `advance(minutes)`、`status` |
| 掉落 | `loot` | 加权掉落表、数量区间、空掉落 | `roll(table, times, grant)`、`list` |
| 制造 | `craft` | 配方、材料校验、技能判定、失败返还 | `craft(recipe)`、`list` |
| 声望 | `reputation` | 势力声望 −100..100 + 分档 | `adjust(faction, delta)`、`status` |
| 成就 | `achievement` | 条件（复用事业线谓词）+ 奖励 | `check`、`list` |
| 成长 | `progression` | XP 曲线、等级、每级属性成长 | `grant(amount)`、`status` |
| 自定义 | `custom` | 受限效果列表（资源/属性/进度轨/标签/事实/声望/XP/时间/掉落） | `<动作名>`、`list` |

全部**确定性**：时间/掉落/制造的随机都由 `sha256(seed|tick|...)` 派生，不消耗 `rng_counter`。
运行态写进 `state["systems"]["rt"]`，快照回退会连体系一起回退。

### 八套开箱即用的模板

| 模板 | 题材 | 玩法循环 | 体系数 |
|---|---|---|---|
| `jrpg` | 日式奇幻冒险 | freeform | 7 |
| `mystery` | 本格推理调查 | choice | 5 |
| `management` | 店铺经营 | mud | 4 |
| `survival` | 末日生存 | mud | 4 |
| `narrative` | 情感叙事 | freeform | 4 |
| `cozy` | 田园生活 | freeform | 4 |
| `tabletop` | 桌面跑团 | ttrpg | 5 |
| `immersive` | 沉浸模拟 | ttrpg | 4 |

模板是起点不是锁死：`overrides` 深合并 dict、列表整体替换；
`template_apply` 只返回 bundle 不落盘。

---

## 四种玩法循环，同一套规则

`playbook` 描述一局游戏怎么玩，并为宿主提供叙事指引。

| 字段 | 可选值 | 作用 |
|---|---|---|
| `loop` | `freeform` / `choice` / `mud` / `ttrpg` | 自由推进 / 选项推进 / 地点命令 / 声明→判定→后果 |
| `input` | `natural` / `choice` / `command` | 玩家输入形态 |
| `progress` | `{axis, label, max}` | 进度轴：`level` / `gold` / `reputation` / `knowledge` / `clock` |
| `failure` | `{mode, label, max}` | 失败条件：`hp` / `sanity` / `clock` / `deadline` / `none` |
| `beat` | `{pattern, every}` | 节拍序列，如「日常·摩擦·升级·代价·回收」 |
| `context` | `{inject, max_lore, scan_depth}` | 每回合上下文注入策略 |

循环是给宿主的指引，不由引擎强制执行。失败不等于扣血——债主上门、被人盯上、理智耗尽
都是可配置的失败条件，由 `failure_tick` 推进。

四套设定包分别演示四种循环：玄枢界 `freeform`、折剑行 `ttrpg`、霓虹深渊 `mud`、雾港 `choice`。

### 事业线

事业线是 stage DAG，谓词只读世界状态：

```json
{
  "id": "fog_lighthouse",
  "title": "别让灯塔亮起来",
  "visibility": {"flag": "无署名信"},
  "stages": [
    {"id": "letter", "title": "信", "objectives": ["弄清信是谁写的"],
     "exit_if": {"visited": "雾港码头"}, "next": ["keeper"]},
    {"id": "keeper", "title": "看守", "objectives": ["找到沈伯"], "next": []}
  ],
  "reward": {"flags": ["灯塔真相"]}
}
```

- **谓词：** `flag` / `visited` / `gold_gte` / `karma_gte` / `tier_gte` / `relation_gte` / `item_gte` / `counter_gte` / `stage_done`，支持 `all` / `any` / `not` 组合。
- **dormant 不显示** —— 没满足 `visibility` 的事业线不进面板，避免变成待办清单。
- **只有 `exit_if` 才推进** —— 没有它的一幕永不自动往前跑；由宿主调用 `quest_advance`。
- **失败优先** —— `fail_if` 或 `deadline_tick` 命中直接判失败。
- **奖励只发一次** —— 完成后反复 tick 不会重复给钱。
- 载入时校验 DAG：有环、`next` 指向不存在的 stage 一律报错。

### 世界书

与 SillyTavern 语义对齐，但逐回合确定性：

| 语义 | 状态 |
|---|---|
| `keys` / `secondary_keys` / `selective` | 支持 |
| `selectiveLogic` 四值（AND_ANY / NOT_ALL / NOT_ANY / AND_ALL） | 支持 |
| `constant` / `insertion_order` / `enabled` | 支持 |
| `probability` / `use_probability` | 支持，由 `sha256(seed|tick|entry)` 派生 |
| `sticky` / `cooldown` / `delay` | 支持，按 tick 计，写进状态 |
| `group` / `group_weight` / `group_override` | 支持，同组只出一条 |
| `scan_depth` / `match_whole_words` / `exclude_recursion` | 支持 |
| 递归扫描 | 支持，但**默认关闭** |
| `position` / `depth` / `role` / `outlet` | 不支持 —— 提示词布局属于宿主 |
| `vectorized` / `automationId` / `characters` 过滤器 | 不支持 —— 需要嵌入模型或前端脚本 |

面板「世界书」抽屉显示每条设定的触发次数与 sticky/cooldown 剩余，
用来回答"为什么这一段被触发了"。`lore_lookup` 可以按任意文本预演一次触发，
不写状态也不消耗冷却。

### 设定包

一个 JSON 就是一个世界。格式说明：[settings/README.md](settings/README.md)。

| 设定包 | 类型 | 特色 |
|---|---|---|
| [`玄枢界`](settings/玄枢界.setting.json) | 东方玄幻 | 十阶修行、玄晶经济、八股势力、21 条世界书 |
| [`折剑行`](settings/折剑行.setting.json) | 武侠 | 七阶身手、断剑主线、当铺经济 |
| [`霓虹深渊`](settings/霓虹深渊.setting.json) | 赛博朋克 | F–S 评级、信用点、义体与记忆、雨季氛围 |
| [`雾港`](settings/雾港.setting.json) | 调查悬疑 | 六阶调查、理智/体力、灯塔谜题 |

`scripts/verify_settings.py` 对每个包断言：载入完整、术语覆盖生效且无未声明的外来词、
货币与品牌落盘、地点描写生效、连跑 15 回合后势力与相位都在动。

---

## 项目范围

**在范围内：** 单人 AI GM、Session Zero、回合契约与审计、确定性规则结算、
设定包、存档、上下文台账、NPC 知情边界、回放。

**明确不做：** 多人联机、云端账号、插件市场、以售卖内容为目的的预写战役、图像生成。

---

## 质量

项目没有 pytest 套件，这是设计选择。验证由 `scripts/verify_*.py`、行为回归和变异测试组成：
**断言必须能被杀死，而不是只被覆盖率统计到。**

| 自检 | 断言数 | 锁住什么 |
|---|---|---|
| `verify_formulas.py` | 122 | 按 docstring 的数学式独立重算 77 个函数 |
| `verify_branches.py` | 192 | 低覆盖模块的异常路径与状态分支 |
| `verify_cli.py` | 21 | CLI 只读不变量 / 写命令业务效果 / 双通道确定性 / tick 驱动世界 |
| `verify_panel.py` | 103 | 视图模型契约 / 旧存档兼容 / 静态白名单 / 行动队列三道闸 / 主题接线 |
| `verify_mcp_stdio.py` | 67 | 真实 stdio 端到端 / HTTP 传输握手 / 酒馆生态 / 只读零副作用 |
| `verify_world.py` | 54 | 世界自演化 / 相位 / 心流 / 道德 / 术语 / 正文 / 台账 |
| `verify_settings.py` | 17 | 四套世界观的载入与演化（零依赖路径） |
| `verify_docs.py` | — | 版本单一信源 / 工具数 / 断言计数 / 素材引用 |
| `verify_i18n.py` | 12 | 面板词典：键唯一 / 模板无歧义 / 输出无中文 / 双语接线 |
| `verify_mechanics.py` | 44 | 规则书优先级与截断 / 循环检测 / NPC 知识边界 / 战斗推演 / 事业线 DAG / 访问计数 / 前缀哈希 / 谣言热度 / 势力意向 |
| `verify_theme.py` | 25 | 亮色默认 / 两套主题实测 WCAG AA 对比度 / 图表重绘 / 骨架屏 |
| `verify_replay.py` | 15 | 动作日志链 / seq 落盘 / canonical 哈希 / 确定性指纹 |
| `verify_gameplay.py` | 65 | 玩法剧本 / 事业线 DAG / 世界书语义 |
| `verify_generic.py` | 104 | 通用判定 / 游戏档案 / 上下文台账 / 存档库 / 品牌 |
| `verify_systems.py` | 161 | 七类体系 / 八套模板 / 计数器 / 面板契约 |
| `verify_injection.py` | 23 | 注入特征识别与 `untrusted` 标记 |
| `verify_near_death.py` | 7 | 濒死保护 |
| `verify_audit_fix.py` | 22 | 快照恢复 / 并发读改写 / 严格 JSON / 输入边界 / 只读零副作用 |
| `verify_memory.py` | 7 | 三段对照查泄漏 + 三重有界 |
| `user_playtest.py` | 47 | 玩家视角：卖没有的东西 / 超量交易 / 边界输入 / 报错可读性 |
| `smoke_ui.py` | 20 | 真实 Edge 渲染 / 卡片抽屉 / 响应式 / 零 JS 错误 |
| `verify_tests.py` | — | 静态 AST：拒绝恒真/恒假/弱断言 |
| `verify_mutation.py` | 53 个变异 | **故意改坏代码，确认测试会红**；存活率必须为 0% |

```bash
bash scripts/pre_push_gate.sh     # 28 个步骤；缺必要依赖时门禁失败
```

另有两套端到端压测：`stress_freeplay.py 500`（CI）与 `stress_freeplay.py 2000`（本机），
全程走真实 MCP stdio。最近一次 500 轮：0 意外错误、0 不变量破坏。

覆盖率门禁：核心域 ≥70%（实测 82%，含通用游戏层）；`pyflakes` 0。
`bandit` 在引擎核心为 0；仓库级扫描仍会在测试脚本里报低危项。

---

## 项目结构

```
world-walker/                  # 仓库根即 game_engine 包
├── panel.py                   # 玩家 HTTP/SSE 服务 + 开局/新局/对话 API
├── panel.html / .css / .js    # 原生玩家壳：大厅、向导、对局、右栏
├── dialog_runtime.py          # GM 系统提示、工具循环、回合收尾与审计
├── narrative_rules.py         # Session Zero、开局卡、场面卡、回合审计
├── player_view.py             # 存档 -> 玩家视图
├── model_config.py            # OpenAI-compatible base_url / key / model
├── tool_registry.py           # 26 个玩家工具
├── game_service.py            # 引擎上的轻量意图层
├── host_adapter.py            # 可选外部宿主桥（不是默认路径）
├── state_schema.py            # 状态模型 / 原子写 / 事务锁
├── templates.py               # 8 套规则骨架
├── rules/                     # 确定性结算函数
├── settings/                  # 可直接开玩的设定包
├── saves/                     # 本地存档库
└── scripts/                   # 自检 + 构建工具
```

---

## 常见问题

**需要联网吗？**
只有模型端点在远端时才需要。引擎与存档都在本地；任何 OpenAI-compatible 网关、本地模型或聚合平台都行。

**需要 OpenAI / Claude 的 API Key 吗？**
真实模型端点通常需要。Key 存在 `~/.world-walker/model.json`，权限 `0600`，接口永远只返回掩码。

**能用于商业项目吗？**
MIT 许可。演示包里的人物、势力、地名全部原创，可自由替换。

**为什么不用 pytest？**
断言必须经得起"改坏代码看测试红不红"的检验。`verify_tests.py` 静态拒绝恒真断言，
`verify_mutation.py` 注入 50 个真实缺陷并要求全部被杀。两者都在门禁里。

**谁写存档？**
引擎。玩家页面调用本地 API，模型调用工具；所有变更都穿过同一个事务写入源，
确定性与回退才可信。

**保证断电安全吗？**
不保证，我们也不这样宣称。存档使用原子替换 + `.bak` 降级 + Windows/POSIX 可重入锁，
崩溃测试覆盖多个中断窗口。若存在 `<state>.archive-pending` 或 `.ww-session-transaction-pending`，
相关受保护读写会被拒绝，且不会自动恢复——请停止写入、保留现场并人工核对。
保存失败时恢复调用方内存中的状态对象，不等于磁盘归档回滚。
详见[归档人工恢复指南](docs/ARCHIVE_RECOVERY.md)。

---

## 重新生成演示素材

```bash
python scripts/make_demo.py          # 4 套世界的真实演示存档 → docs/demo/
python scripts/shots.py              # 逐项断言 + 截图 + 录屏 → docs/screenshots/
python scripts/verify_settings.py    # 四套设定包全量校验
```

---

## 许可

MIT。图表库 [ECharts](https://echarts.apache.org/) 5.5.1（Apache-2.0）。
酒馆生态格式的兼容实现参考了 SillyTavern 社区公开的角色卡与世界书规范；
本项目不复用任何作品的名词与设定。
