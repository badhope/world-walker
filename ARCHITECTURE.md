# World Walker 架构

文档版本：v1.18.0 · 2026-11-22

World Walker 有两个入口，但只有一套引擎：

1. **玩家页面（默认）**：本地页面 + OpenAI-compatible 模型，玩家直接对话。
2. **MCP 独立接口（可选）**：外部 AI 通过 MCP 调工具，自己当 GM、自己叙述，不使用本地页面。

两条入口共用同一个状态文件、同一套确定性规则和同一个事务写入源。

## 数据流

```
玩家页面 / 外部 AI
        │
        ▼
panel.py ──► dialog_runtime.py ──► tool_registry.py ──► game_service.py
        │                                │
        │                                ▼
        │                         rules/ 确定性结算
        │                                │
        └────────────► state_schema.py ◄─┘
                          │
                          ├─ save.json
                          ├─ .bak
                          ├─ action_log.jsonl
                          └─ viz.jsonl
```

MCP 模式走：

```
外部 AI ──► mcp_server.py ──► 同一 rules/ + state_schema.py + gameplay.py
```

`mcp_server.py` 不依赖 `panel.py`。MCP 模式不需要页面、SSE 或前端资源。

## 入口层

### 玩家页面：`panel.py`

- 提供 `/api/v1/health`、`bootstrap`、`state`、`open`、`new`、`chat`、
  `session-zero/preview`、`model/config`、`model/test`、`saves`、`export`、`events`。
- `bootstrap` 返回大厅、世界目录、模型状态和 Session Zero 选项。
- `new` 接受 `narrative`；未指定模板时按类型自动配骨架。
- `chat` 调 `DialogRuntime.respond()`，模型通过 28 个玩家工具推进；其中 `campaign` 负责“一回合一场戏”，`tick` 不再是玩家工具。

### 场景层：`gameplay.py`

- 把“时间驱动的 tick”换成“场景驱动”的战役循环：3 幕、每幕 3–6 场；
  每场有目标、障碍、压力钟、最多一条线索、无论成败的代价、下一场。
- `campaign(action=brief|open|resolve|clock|journal)` 是 MCP 与玩家页面共用的入口；
  `resolve` 只接受 `yes / yes-but / no-and`，结算场景但不推进 `tick`。
- 六套设定包各带 `gameplay`：`acts / clocks / fronts / choice_policy / progression / session`；
  缺失时退回三幕骨架，而不是空白。

### 对话运行时：`dialog_runtime.py`

- 组装 GM 系统提示：POLICY（绝对规则）、CANON（只读世界圣经）、当前局面、
  GAME PROFILE、CONTRACT（本场契约：幕/目标/障碍/压力/线索/代价）、TOOLS；
  之后追加 DIRECTOR NOTE、TABLE RULES、ACTIVE SKILLS、HOOK NOTES。
- 跑 OpenAI-compatible 工具循环；模型可以多轮调用工具。
- 回合开始跑 `rule_events.turn`，每次工具后跑 `rule_events.tool`；规则效果写进工具结果。
- `before_turn` 钩子可以注入提示词或阻断回合；`after_tool` / `after_turn` 钩子只追加 note。
- 收尾时写 `turns`，并把 `narrative_rules.audit_turn` 的发现写入 `audit`。
- 不直接改写游戏数值；所有数值变更由工具完成。

### 知识库：`library.py`

- `library/playbooks/*.json` 是预制玩法，只固定世界、循环、难度、基调和风格；
  不写剧情，不替玩家做决定。开局仍走标准 Session Zero。
- `library/archives/*.md` 是设计档案：救生筏、预制玩法规范、发布纪律。
- `GET /api/v1/library` 只读；面板“知识库”按预制玩法/设计档案两页展示。
- `wg setup` 写入内置技能与导演备注；`library` 与 `narrative_skills` 都进 wheel 和 exe。

### 调校层：`harness_config.py` / `harness_hooks.py`

- `harness_config.py` 管全局导演备注、桌面规则、叙事技能和运行时开关，
  默认落 `~/.world-walker/harness.json`（0600）。
- `narrative_skills/*.md` 是 GM 提示词包，解析 `# 标题` 与 `> 摘要`；最多启用 8 个。
- `harness_hooks.py` 用隔离子进程跑 `before_turn / after_tool / after_turn`，
  只交换 JSON；超时、异常和审计拦截都只返回错误，不中断回合。
- 钩子是协作护栏，不是安全沙箱：默认关闭，脚本以用户权限运行。

### 世界圣经：`canon.py`

- `normalize`：把模板/设定包的 bible 归一化为 `immutable / revealed / rumors / hidden / unknown`。
  `hidden` 是“世界默认有、但主角不知道”的真相；`revealed` 才是主角已知。
- `brief`：每回合返回根设定、相关已揭示事实、迷雾问题，以及单独的 `hidden` 列表；GM 先读它再叙事。
- `render`：把 `hidden` 标成“世界默认（主角未知；GM 只能用于判定，不得直接讲给玩家）”。
- `check`：确定性冲突检查；同 id 或同 subject+predicate 且 value 不同即冲突，hidden 也参与比对。
- `commit`：把探索到的新事实写入 `revealed`/`rumor`；揭示一条 hidden 时自动从 hidden 移除；
  根设定改动必须显式 override。

### 知识库投影：`knowledge.py`

- **JSON 存档仍是唯一事实源**；SQLite 是旁边的可丢弃索引 `<save>.knowledge.db`，可随时重建。
- `sqlite3` + WAL + FTS5 `trigram`，中文按 3 字以上子串检索；1–2 字查询回退 `LIKE`，不依赖嵌入模型。
- 统一表 `items(kind, item_id, title, body, keys, tick, extra)`：角色卡、世界书、canon、
  事实、事件时间线、地点、关系、摘要都投影到这里；单角色档案另带 activity / intent / mood /
  status / last_seen_tick。
- `knowledge` MCP 工具：`search / pack / graph / who_knows / audit / stats / character /
  update_character / worldbook_add / timeline_add / sync`；玩家工具面同时暴露同一套 action。
- 别名解析：角色的 `name / aliases` 同时用于 `_entity_id` 和检索正文；NPC 的
  `agenda`（长期动机）与 `intent`（下一步）分开存。
- `graph` 只沿 `state.relations` 做 1–2 跳 BFS，不推断关系；`who_knows` 直接复用
  事实台账的 `witnesses/public`；`pack` 按字符预算裁剪并去重；`audit` 检查悬空引用、
  重复世界书主键、坏卡、未来摘要等数据质量问题。
- 运行时写世界书仍写回 `state["lore"]`，时间线仍写回 `state["event_log"]`，不另造第二套事实源。
- 不引入 Postgres、ORM、常驻服务或向量库；需要语义检索时再加可选 `sqlite-vec` 适配器。

### Session Zero：`narrative_rules.py`

- `normalize`：把玩家选择归一化为类型、玩法、角色、基调、难度、边界、fronts、clocks。
- `preview`：建局前返回开局卡，不写存档。
- `attach`：建局后把叙事配置、开局卡、钩子和钟写进 `state["narrative"]`。
- `turn_brief`：每回合给模型一张场面卡。
- `audit_turn`：S2/S3 启发式审计，不阻断生成。
- `template_for`：类型 → 规则骨架；模板只提供骨架与种子，不预写剧情。

### MCP 独立接口：`mcp_server.py`

- 暴露工具、资源和提示词；宿主 AI 自己负责叙述。
- `session_zero` 提示词负责开局问询；`new_game` 提示词负责开局后的回合契约。
- `publish_prose` 是 MCP 模式唯一正文出口。
- 资源：`world://state/current`、`world://summary/current`、
  `world://settings/index`、`world://docs/protocol`。
- 不调用 `open_panel`；MCP 模式完全由对话展示。

## 状态与不变量

- **一个写入源**：所有 mutation 通过 `state_schema.transact_state` 或等价事务写入。
- **确定性**：同 state + seed + action log 可重放；`rng_counter` 持久化。
- **有界**：事件日志、karma ledger、prose、sidecar 都有上限，溢出合并/归档而不是无限增长。
- **可恢复**：原子替换 + `.bak`；若出现 `<state>.archive-pending` 或
  `.ww-session-transaction-pending`，受保护读写会被拒绝，不自动解析或恢复，也不承诺回滚磁盘归档。
  人工恢复见 [`docs/ARCHIVE_RECOVERY.md`](docs/ARCHIVE_RECOVERY.md)。

## 目录

```
world-walker/
├── panel.py / panel.html / panel.css / panel.js   # 玩家页面
├── dialog_runtime.py                              # GM 提示词与工具循环
├── harness_config.py                              # 导演备注 / 桌面规则 / 技能 / 运行开关
├── harness_hooks.py                               # 本地 before_turn / after_tool / after_turn
├── narrative_skills/                              # GM 提示词包
├── library.py / library/                          # 预制玩法与设计档案
├── narrative_rules.py                             # Session Zero / 开局卡 / 场面卡 / 审计
├── canon.py                                       # 世界圣经 / 硬 canon / 冲突检查
├── knowledge.py                                   # SQLite sidecar 索引：角色卡 / 世界书 / 时间线
├── player_view.py                                 # 存档 → 玩家视图
├── model_config.py                                # OpenAI-compatible 配置
├── tool_registry.py                               # 28 个玩家工具
├── game_service.py                                # 工具意图层
├── mcp_server.py / mcp_primitives.py              # 可选 MCP 独立接口
├── state_schema.py                                # 状态 / 原子写 / 锁 / 归档
├── sessions.py                                    # 存档库路径 / 快照 / 回收站
├── session_factory.py                             # 设定/模板 → 新局的唯一建局入口
├── templates.py                                   # 9 套骨架
├── mapgen.py                                      # 蓝图 → 本局地图（固定拓扑 / 可变外观）
├── rules/                                         # 确定性规则
├── settings/                                      # 设定包
├── docs/MCP_PLAY.md                               # MCP 对话游玩协议
└── scripts/                                       # 验证与构建
```

## 设计取舍

- 不做多人、云端账号、插件市场、预写战役售卖。
- 不把旧管理台、i18n、主题脚本、ECharts 带回玩家壳。
- MCP 保留为独立模式，不回灌到玩家页面；两条路径共享引擎，不共享 UI。
