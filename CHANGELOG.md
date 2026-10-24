# 更新日志

本项目遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。
版本号的单一信源是 `__init__.py:__version__`，`pyproject.toml` 必须与之一致（由测试断言）。

---

## v1.0.0 — 2026-10-24

首个"可以直接交付给别人玩"的版本。相比 v0.9.0，这一版修掉了三个**会让项目在某些环境里根本跑不起来**
的缺陷，并把"世界自己会动"从"部分成立"做到"四套世界观都成立"。

### 修复（阻断级）

- **MCP SDK 布局不兼容**：`mcp_server.py` 只 `from mcp.server.mcpserver import MCPServer`，
  而 PyPI 当前稳定版（mcp 1.30）的入口是 `mcp.server.fastmcp.FastMCP`。
  结果是：装了 mcp 的环境下**所有 31 个工具全部无法调用**（客户端只看到 "Connection closed"）。
  现在两套布局都支持（`_MCPServer` 兼容层），并且 `FastMCP` 不接受 `version` 参数的情况也已处理。
- **`seed_rng` 裸 import numpy 挂死 MCP 子进程**：每次结算都会 `import numpy` 试图重置全局种子。
  在本机 MCP stdio 子进程里，这个 import 会让 `status` / `narrative` / `tick` 全部超时（实测 15s+ 无响应），
  而 CLI 里完全正常——这是最难查的一类 bug。现在只在 numpy **已经被导入**时才同步种子，
  符合"零第三方依赖"的宣称，也消除了挂死。
- **包元数据未执行**：多处 `importlib` 别名注册只创建 module 对象、不执行 `__init__.py`，
  导致 `from game_engine import __version__` 永远失败。现在统一在注册后 `exec_module`。

### 修复（语义分裂）

- **CLI 的 `tick` 不驱动世界演化**：只有 MCP 的 `tick` 调 `evolve_world`。
  同一份存档走 CLI 与走 MCP 会得到两个不同的世界（违反 INV-E4/E6）。
  现在 CLI 的 `tick` 与 MCP 完全同构，`verify_cli.py` 新增断言锁定。
- **只读工具偷偷落盘**：`status` / `world_state` 会 `save_state` 并推进 `rng_counter`。
  这意味着"查没查状态"会改变后续战斗结果——直接破坏可复现性。
  现在只读工具零副作用（字节与 mtime 都不变），`verify_mcp_stdio.py` 断言。
- **死目标刷屏**：对已倒下目标继续攻击会重复写编年史，500 回合存档里同一条"已经没有还手之力"出现 ×12。
  现在返回提示但不写事件。
- **势力演化两个极端**：先"全体贴 100"（排行榜变平线），改成共享总容量后变成"全体 35.5"（同样没信息量）。
  现在每个势力有由名字确定性派生的禀赋上限 + 温和 LV 压制 + 挑战者回流，长期有格局、短期有换手。
- **`save_state` 偶发 PermissionError**：Windows 上杀毒/索引器瞬时占用目标文件会让一次正常回合失败。
  现在 `os.replace` 带 5 次退避重试。

### 新增

- **三套新设定包**：`折剑行`（武侠）、`霓虹深渊`（赛博朋克）、`雾港`（调查悬疑）。
  加上 `玄枢界` 共四套，覆盖四种完全不同的世界观与术语体系。
- **`scripts/verify_settings.py`（17 项断言）**：逐包验证载入完整性、术语覆盖、货币/品牌落盘、
  地点描写、连跑 15 回合后势力与相位都在动。已接入门禁与 CI。
- **面板：行动队列（双向通道）**：浏览器里可以排队行动，写入 `<state>.inbox.jsonl` 侧写；
  Agent 用新工具 `pending_actions` 取走并照常结算。状态文件仍然只读，确定性不被破坏。
  三道闸：同源 Origin、`application/json`、长度上限。
- **面板：世界脉搏卡**：Panarchy 相位 / 存量 / 连接度 / 烈度 / 势力存量 / 崩解次数。
- **面板：命令面板**（`Ctrl/⌘ + K`）、**分享模式**、**状态导出**、**时间线搜索与类型筛选**、
  **角色卡详情弹窗**（卡面文字来自设定包）。
- **`scripts/make_demo.py`**：确定性生成四套世界的真实演示存档（含世界演化、大事记、摘要、正文）。
- **`scripts/shots.py`**：真实浏览器逐项断言后截图 + 录制交互视频（`docs/screenshots/walkthrough.mp4`）。
- **`docs/BENCHMARK.md`**：7 个具名竞品的逐维度对标，含 10 条差距的四类处置。
- **`CHANGELOG.md` / `ROADMAP.md` / `CONTRIBUTING.md` / `SECURITY.md`**。
- **34 个 MCP 工具**（新增 `pending_actions`）。

### 重构（行为不变）

- `engine.py::main` 拆成命令表 + 14 个处理函数（圈复杂度 D(25) → A(1.75)）。
- `panel.py::build_scene` 拆成 7 个小函数（E(35) → A）；`classify_event` 拆成类型规则表（D(24) → A）。
- `mcp_server.py::load_setting` 拆出 `_apply_bundle_extras`（D(29) → C(16)）。
- `state_schema.seed_rng` 的 numpy 分支改为惰性。
- `init_game.py` 的 `current_location_desc` 改为 `location_desc`（与 engine/panel 一致）。

### 测试

- 断言审计：547 条（0 可疑）。
- 变异测试：**32 个变异，杀死 32，存活率 0%**（新增 M26–M32：只读落盘、CLI tick 分裂、死目标刷屏、
  队列无上限、跨站请求、文档版本漂移、README 工具数漂移）。同时把"变异片段失效"从静默 SKIP
  改为失败——历史上正是一次 SKIP 让一条规则从未被真正验证过。
- 门禁 17 项全绿（编译 / 审计 / 8 套自检 / 覆盖率 / 压测 / 界面 / 变异 / 打包 / wheel）。
- 覆盖率 88%（核心域），bandit 0 / pyflakes 0。

### 已知限制

- 面板未做 WCAG 2.1 AA 全量审计（无 axe-core 扫描）。
- 世界书 GUI 编辑器未做（与"面板严格只读"的架构决策冲突）。
- 长局记忆是关键词检索，不是向量语义检索（见 ROADMAP P2）。

---

## v0.9.0 — 2026-10-23

- 定位闭环：世界演化驱动（势力/谣言/风气/NPC/Panarchy）、相位与心流参与结算、
  六维道德由业债累加、面板术语可配置、叙事正文落盘。
- 修 3 个真 bug（暴击算成失败 / 道德恒 0 / 涌现事件重复）与台账无界。
- 新增 `verify_world.py`（46 项）与变异 M20–M25。

## v0.8.0 — 2026-10-15

- 打包完整性、面板截图、双 README 预览区，首个可安装版本。

更早的历史见 `ARCHITECTURE.md` 的任务清单（T1–T27）与 `docs/` 下的两轮审查报告。
