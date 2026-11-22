# MCP 对话游玩模式

这是 World Walker 的第二个入口：**不打开本地页面，让外部 AI 通过 MCP 当 GM，完全用对话展示世界。**

适用场景：

- 你想在自己的 AI 客户端里玩，不想多开一个网页。
- 你的客户端支持 MCP（stdio 或 streamable-http）。
- 你希望由宿主 AI 自己写场景、NPC、气氛，只把数值交给你给引擎。

## 启动

```bash
pip install -e ".[mcp]"

# stdio（本地客户端最常见）
wg mcp

# 或远程 HTTP
wg mcp --http --host 127.0.0.1 --port 8620
```

MCP 客户端配置示例：

```json
{
  "mcpServers": {
    "world-walker": {
      "command": "world-walker-mcp"
    }
  }
}
```

HTTP 模式则把客户端指向 `http://127.0.0.1:8620/mcp`。

MCP 不要求模型厂商；宿主 AI 用哪个模型由你的客户端决定。

## 开局

如果设定包带 `world.opening`，`load_setting` / `session_new` / `template_start` 会返回 `opening.brief_line`、`opening.prologue` 和 `opening.actions`。宿主先把序章逐段讲给玩家，再把三枚动作当作可选开头；不要改写系统公告。没有 `opening` 的模板才由宿主自己写开局卡。

外部 AI 先使用 `session_zero` 提示词（或直接把同样的问法发给模型）：

1. 想玩什么类型？
2. 想怎么玩？
3. 以谁的身份？
4. 模式（爽文 / 适中 / 硬核）、基调、内容边界？

拿到答案后，**第一次写正文前**必须把世界根设定定下来。不要一次写百科全书，只锁底层：

1. 世界前提：最基本现状、谁维持秩序、哪里失控。
2. 力量规则：能做什么、代价、绝对不能做什么。
3. 历史断层：哪段过去仍在影响现在、官方说法与真相是否不同。
4. 地图边界：玩家在哪、最近三四个地点、通行时间、哪里进不去。
5. 社会与生死：什么被禁止/惩罚、受伤/濒死/死亡怎么处理。

写成 10–12 条 `immutable` 事实，细节和未探索区放 `unknown`。然后选一条路：

```text
templates_list()
template_start(template="tabletop", name="灰岩堡", player_name="韩照",
               overrides={"game": {"tags": ["硬核"]}})
```

模板已自带根设定、unknown、可选 `hidden`（世界默认但主角未知）和 `revealed`（主角已知）；开局后先 `canon_brief` 读一遍，再写开场。

自建世界：

```text
world_init(world={...}, player={...}, entities=[...], state_path="my-game.json")
canon_init(bible={world: {...}, immutable: [...], unknown: [...]})
```

`canon_init` 至少 8 条 `immutable`；没有世界圣经就不开始叙事。开局后让 AI 写一张开局卡：

- 你在哪
- 你是谁
- 什么已经在动
- 死亡规则
- 三个钩子
- 核心问题

## 一局怎么走

一局不是 2000 个 tick，而是 **3 幕、每幕 3–6 场戏**。每场戏有：目标、障碍、压力钟、最多一条线索、无论成败的代价、下一场。

```text
campaign(action="brief")               # 本场契约：幕/目标/障碍/压力/线索/代价
campaign(action="open", title="...", goal="...", obstacle="...",
         pressure="...", clue="...", cost="...", choices=["...", "..."])
canon_brief(scene_text=...)            # 世界圣经（根设定 + 已知/迷雾）
read_state()                           # 或 context_pack(scene_text=...)
roll(attribute="dex", difficulty=12)   # 需要判定时
knowledge(action="character", name="roland")  # 写 NPC 对话前：位置/活动/知道什么
publish_prose(text="...")              # 唯一正文出口
campaign(action="resolve", outcome="yes-but", cost="...",
         clocks=[{"name": "夜潮", "delta": 1}])  # 收尾：结算这一场
```

规则：

- **一回合 = 一场戏**。没有场景就不写“过了一天”；`tick` 只是内部 debug，玩家面不要用。
- 每场结尾必须 `campaign(action="resolve")`，`outcome` 只能是 `yes` / `yes-but` / `no-and`。失败不是重来，是 `no-and`：给新信息、新代价、新选择。
- 每场最多 2–3 个选择；每个选择都要有**不同的代价**，不要“安全/稳妥/什么都不做”，不要预告后果，不要替玩家推荐。
- 拖延、失败、错过时机：`campaign(action="clock", name="...", delta=1)`。钟满时世界先动手，用叙事兑现。
- 阶段推进看 `campaign(action="brief").act`，不是看等级或日期。
- 数值只由工具结算，宿主不心算、不编造。
- `canon_brief` 每回合先读；状态 > 记忆 > 推理，根设定不许改，不许 retcon。
- `hidden` 是 GM 判定用的世界真相，不是主角已知信息；不要把隐藏设定直接倒给玩家，只能通过调查/对话/踩点逐步升为 `revealed`。
- `publish_prose` 只写玩家看到的文学描写；不写 JSON、字段名、工具名。
- 不替玩家写内心决定、台词或下一步。
- 正文出现新地点/新历史/新组织/新规则：先 `canon_check`，通过才 `canon_commit`；冲突就修正叙述，不许自己圆。
- 不确定的过去先 `canon_brief` 查；查不到留在 `unknown` 或传闻，不补成既定事实。
- NPC 只能引用 `knowledge(action=character).knowledge` 返回的事实；不知道就回避、撒谎或反问。
- NPC 换地点/换状态后用 `knowledge(action=update_character, ...)` 写回；稳定新设定用 `worldbook_add`，重大事件用 `timeline_add`。
- 失败也要前进：给新信息、新代价或新选择。
- 不预设结局；只准备压力、种子、钟。
- 每 3–5 场看一次 `campaign(action="journal")` / `status`，把世界变化织进叙事；不要用 `narrative` 的涌现事件刷屏。

### 改根设定

根设定是硬 canon。确实要改（例如玩家要求重开世界观）时，必须显式覆盖并说明理由：

```text
canon_commit(facts=[...], status="immutable", allow_override=true,
             reason="玩家要求把墓穴改到城北")
```

没有 `reason` 的覆盖会被拒绝；默认流程只写 `revealed` 或 `rumor`。

## 资源

宿主可以把这些只读资源固定进上下文：

| URI | 内容 |
|---|---|
| `world://state/current` | 当前完整状态 |
| `world://summary/current` | 紧凑摘要（回合、玩家、地点、相位、未结因果、最新正文） |
| `world://settings/index` | 已安装设定包 |
| `world://docs/protocol` | 本文件的协议版本 |

## 与玩家页面的区别

| | 玩家页面 | MCP 模式 |
|---|---|---|
| 谁写正文 | 本地 `dialog_runtime` 调模型 | 外部宿主 AI |
| 谁展示 | 本地页面 + SSE | 宿主自己的对话 |
| 需要页面 | 是 | 否 |
| 模型配置 | 页面内 `base_url/api_key/model` | 宿主客户端自己的模型 |
| 共享 | 同一套规则、存档、事务写入 | 同一套规则、存档、事务写入 |

MCP 模式不调用 `open_panel`。这是故意的：它应该看起来像一场纯对话，而不是一个仪表盘。
