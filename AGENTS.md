# AGENTS

面向在本仓库工作的 AI/开发者。先读 [`ARCHITECTURE.md`](ARCHITECTURE.md) 与 [`docs/MCP_PLAY.md`](docs/MCP_PLAY.md)。

## 当前产品

World Walker 是单人 AI 跑团 / 互动叙事引擎，不是游戏助手、不是小说生成器。

- 玩家页面：玩家直接和模型对话。
- MCP 模式：外部 AI 通过 MCP 当 GM，完全用对话展示，不需要页面。
- 模型只要求 OpenAI-compatible；`base_url / api_key / model` 自定义，不绑定厂商。

## 修改前

1. 读 `ARCHITECTURE.md` 的入口层、状态与不变量。
2. 改状态字段同步 `state_schema.py`；改玩家视图同步 `player_view.py`。
3. 改提示词同步 `dialog_runtime.py`；改开局问询同步 `narrative_rules.py`。
4. 改 MCP 契约同步 `mcp_server.py` / `mcp_primitives.py` / `docs/MCP_PLAY.md`。

## 禁止回潮

不要恢复：

- 旧管理台 `/admin`、`admin.html/js`
- `panel.i18n.js`、主题切换脚本
- `assets/echarts.min.js`
- 以 `open_panel` 为必需步骤的 MCP 流程
- 把旧 MCP 工具叙事（现 71 个工具）塞回玩家页面
- 用模板预写完整剧情

## 验证

```bash
python3 -m py_compile narrative_rules.py dialog_runtime.py player_view.py panel.py mcp_server.py
node --check panel.js
python3 scripts/verify_player_shell.py
python3 scripts/verify_surface.py
python3 scripts/verify_docs.py
python3 scripts/verify_mcp_stdio.py
```

浏览器流程用 `scripts/verify_player_shell.py` 或手动启动 `panel.py` 验证；不要用旧 `smoke_ui.py`。

## 提交

- 功能/修复分开提交。
- 版本最后一位是补丁位；小改小推只走 PATCH。
- 本地与远程 `main` 保持一致；推送前跑验证。
- 完成后在交付里明确写“已做完”，不要只留状态码。
