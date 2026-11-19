# 贡献指南

World Walker 是轻量的单人 AI 跑团引擎。改动以“玩家能不能直接开聊”和“MCP 能不能独立跑”为验收标准。

## 开始

```bash
python3 -m pip install -e ".[dev]"
python3 panel.py --state docs/demo/折剑行.save.json --port 8899
```

打开 `http://127.0.0.1:8899/`，先用任意 OpenAI-compatible 模型配置跑一局。

## 架构边界

- 玩家页面：`panel.py` + `panel.html/css/js`。
- 对话循环：`dialog_runtime.py`。
- 开局与回合叙事：`narrative_rules.py`。
- 玩家工具：`tool_registry.py` → `game_service.py`。
- MCP 独立接口：`mcp_server.py` + `mcp_primitives.py`。
- 状态：`state_schema.py`，所有写入走事务。

不要把旧管理台、i18n、主题脚本、ECharts 或 `open_panel` 必需流程带回来。

## 改动要求

- 影响状态字段：同步 `state_schema.py`、`player_view.py`、存档兼容。
- 影响 MCP：同步 `docs/MCP_PLAY.md` 和 `scripts/verify_mcp_stdio.py`。
- 影响开局：同步 `narrative_rules.py` 与页面向导。
- 新增文档放在 `docs/`，过时的审计/调研文档直接删，不留在仓库里当历史包袱。

## 验证

```bash
python3 scripts/verify_player_shell.py
python3 scripts/verify_surface.py
python3 scripts/verify_docs.py
python3 scripts/verify_mcp_stdio.py
```

提交前保证工作区干净，`main` 与 `origin/main` 一致。
