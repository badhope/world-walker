# World Walker 架构

文档版本：v1.12 · 2026-11-19

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
外部 AI ──► mcp_server.py ──► 同一 rules/ + state_schema.py
```

`mcp_server.py` 不依赖 `panel.py`。MCP 模式不需要页面、SSE 或前端资源。

## 入口层

### 玩家页面：`panel.py`

- 提供 `/api/v1/health`、`bootstrap`、`state`、`open`、`new`、`chat`、
  `session-zero/preview`、`model/config`、`model/test`、`saves`、`export`、`events`。
- `bootstrap` 返回大厅、世界目录、模型状态和 Session Zero 选项。
- `new` 接受 `narrative`；未指定模板时按类型自动配骨架。
- `chat` 调 `DialogRuntime.respond()`，模型通过 26 个玩家工具推进。

### 对话运行时：`dialog_runtime.py`

- 组装 GM 系统提示：世界状态、这局是什么、本回合场面卡、12 条硬规则。
- 跑 OpenAI-compatible 工具循环；模型可以多轮调用工具。
- 收尾时写 `turns`，并把 `narrative_rules.audit_turn` 的发现写入 `audit`。
- 不直接改写游戏数值；所有数值变更由工具完成。

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
├── narrative_rules.py                             # Session Zero / 开局卡 / 场面卡 / 审计
├── player_view.py                                 # 存档 → 玩家视图
├── model_config.py                                # OpenAI-compatible 配置
├── tool_registry.py                               # 26 个玩家工具
├── game_service.py                                # 工具意图层
├── mcp_server.py / mcp_primitives.py              # 可选 MCP 独立接口
├── state_schema.py                                # 状态 / 原子写 / 锁 / 归档
├── templates.py                                   # 8 套骨架
├── rules/                                         # 确定性规则
├── settings/                                      # 设定包
├── docs/MCP_PLAY.md                               # MCP 对话游玩协议
└── scripts/                                       # 验证与构建
```

## 设计取舍

- 不做多人、云端账号、插件市场、预写战役售卖。
- 不把旧管理台、i18n、主题脚本、ECharts 带回玩家壳。
- MCP 保留为独立模式，不回灌到玩家页面；两条路径共享引擎，不共享 UI。
