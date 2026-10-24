# AGENTS.md — 万界·行者 World Walker

AI 驱动的文字互动游戏引擎：规则结算内核（Python）+ MCP 服务器 + 只读网页主舞台。零第三方运行时依赖（MCP 为可选 extra）。

**`ARCHITECTURE.md` 是本项目唯一真理源**——凡影响架构/接口/数据模型/依赖/目录结构的变更，必须同步更新它。

## 结构

- 仓库根即 `game_engine` 包（`pyproject.toml` 中 `package-dir = { "game_engine" = "." }`，内部统一 `import game_engine.*`）
- `engine.py` — 规则结算内核
- `mcp_server.py` — MCP 工具入口（34 工具；兼容 mcp 1.x `fastmcp` 与 2.x `mcpserver` 两种布局）
- `panel.py` / `panel.html` / `panel.css` / `panel.js` — 只读主舞台（面板不许写状态；
  行动队列只写 `<state>.inbox.jsonl` 侧写，状态仍由 MCP 单点写入）
- `state_schema.py` — 状态模型（原子写 / 世代归档 / 种子）
- `settings_loader.py` — 设定包 → 状态（**纯标准库**；MCP 与零依赖自检共用，不要在这里引 mcp）
- `rules/` — 规则数据；`settings/` — 四套设定包；`scripts/` — 验证脚本（13 个 `verify_*.py` + 素材流水线）

## 运行

```bash
pip install -e .            # 或 pip install -e '.[mcp]' 装 MCP 依赖
world-walker                # CLI
world-walker-mcp            # MCP 服务器
bash play.sh                # 快速开局
```

## 验证（改完必须跑）

```bash
bash scripts/pre_push_gate.sh   # 推送前门禁，与 GitHub Actions 同判据
```

分项可跑：`verify_formulas.py`、`verify_memory.py`、`verify_mcp_stdio.py`、`verify_panel.py`、
`verify_injection.py`、`verify_branches.py`、`verify_cli.py`、`verify_near_death.py`、
`verify_world.py`、`verify_settings.py`、`verify_docs.py`、`verify_mutation.py`、`smoke_ui.py`。

**CI 的 core 作业不装 mcp**：任何要在 core 里跑的脚本都不得 import `mcp_server`（会 ModuleNotFoundError）。
设定包相关逻辑一律走 `settings_loader.py`。

素材流水线（不进门禁）：`python scripts/make_demo.py` 生成四套世界的演示存档，
`python scripts/shots.py` 断言后截图并录制 `docs/screenshots/walkthrough.mp4`。

**没有 pytest 测试套件**——验证靠上述脚本，不要假设 `pytest` 可用。

## 硬约束

- 数值确定性优先：同样的输入 + 随机种子必须复现同样结果，禁止引入不受控随机/时间依赖
- 面板严格只读：`panel.*` 不得写 `game_state.json`
- 零依赖原则：新增第三方依赖前必须先说明必要性（MCP 之外）
- 改数据模型必须同步 `ARCHITECTURE.md` 与 `state_schema.py`
- `game_state.json` / `demo_state.json` / `audit_state.json` 是演示与审计快照，改动会破坏 `audit_ui.py` 的 18 项断言

## 不要碰

- `__pycache__/`、`*.egg-info/`、`.venv/`
- `docs/screenshots/` 里的截图（由 `scripts/audit_ui.py` 断言后入库）
- `requirements-mcp.lock.txt`（经 OSV 扫描，加依赖需重扫）
- `game_state.json` 的真实存档（调试请用副本）
