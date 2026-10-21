# 架构设计文档：万界·行者（world-walker）

> 本文档是本项目的唯一真理源（Single Source of Truth）。
> 任何影响架构、接口、数据模型、依赖或目录结构的代码变更，都必须同步更新本文档。
> 最后更新：2026-10-21 ｜ 文档版本：v1.6

## 1. 概述与目标

- **项目定位**：世界观无关的文字互动游戏引擎——规则结算内核（Python）+ MCP 服务器 + 只读网页主舞台。
- **核心问题**：AI 宿主（Claude Code / Codex / Cursor 等）通过 MCP 工具结算玩家行动；玩家需要"文字叙事 + 面板/弹窗/提示"的混合游戏体验，而不是纯文字流。
- **质量属性优先级**：数值确定性（可复现） > 只读安全（面板不许写状态） > 可维护（零依赖、原生实现） > 性能。
- **范围边界**：
  - In scope：MCP 规则结算、长局记忆、模型层、实况主舞台（叙事/ HUD / 时间线 / 弹窗提示 / 世界皮肤）。
  - Out of scope（当前阶段）：网页直接提交游戏行动（第二阶段再评估）、AI 文本流式聊天、地图/立绘/音效、前端框架迁移。

## 2. 约束

- 技术约束：Python ≥3.10；仅标准库（http.server 等）+ 可选 `mcp>=2`；前端为原生 HTML/CSS/JS，无构建链、无第三方运行时依赖。
- 关键假设：
  1. 状态文件是本局唯一权威数据源；面板只读渲染它。
  2. MCP 是第一阶段唯一的状态写入 / 数值结算入口。
  3. 面板运行在本机（127.0.0.1），不做公网鉴权。

## 3. 架构总览（C4 - Context & Container）

### 3.1 系统上下文

```
玩家(人) ──对话/行动──> 宿主 AI Agent（Claude Code / Codex / 自建）
                              │  MCP (stdio)
                              ▼
                     world-walker MCP 服务器 (mcp_server.py, 31 工具)
                              │  规则结算 (rules/*)
                              ▼
                     状态文件 ww_state.json ◄──只读── 实况主舞台 (panel.py + panel.html/css/js)
                              │                          ▲
                        归档 .log.jsonl            SSE /state /events
                                                         │
                                                    玩家浏览器
```

### 3.2 容器视图

| 容器 | 职责 | 关键约束 |
|---|---|---|
| `rules/*` | 纯规则结算（战斗/经济/社交/因果/叙事/模型层） | 无副作用，状态由调用方传入传出 |
| `mcp_server.py` | 31 个 MCP 工具；读写状态文件；tick 推进 | 唯一写入源（第一阶段） |
| `state_schema.py` | 状态结构、事件日志、归档、业债裁剪 | `save_state` 统一归档 |
| `engine.py` | CLI 14 命令（手动结算/调试） | 与 MCP 共用 rules |
| `panel.py` | 只读视图模型 + HTTP/SSE 服务 | 不写状态；静态资源白名单 |
| `panel.html/css/js` | 游戏主舞台（叙事/HUD/时间线/弹窗/皮肤） | 原生实现；状态值一律 textContent |

## 4. 技术栈

| 层 | 选型 | 版本 | 理由 |
|---|---|---|---|
| 语言 | Python | ≥3.10 | 引擎/规则/MCP 已定 |
| MCP | `mcp` SDK | ≥2.0（可选装） | 宿主对接标准 |
| 面板服务 | 标准库 `http.server` + SSE | 内置 | 零依赖、已存在 |
| 面板前端 | 原生 HTML/CSS/JS | — | 免构建、免框架；单机只读足够 |
| 数据源 | JSON 状态文件 | — | 可续跑、可 diff、可归档 |

## 5. 模块 / 目录结构

```
world-walker/                      # 仓库根即 game_engine 包
├── mcp_server.py                  # MCP 服务器（31 工具；唯一写入源）
├── engine.py                      # CLI 入口（14 命令）
├── state_schema.py                # 状态结构 + 归档 + 业债裁剪
├── panel.py                       # 实况主舞台：只读视图模型 + HTTP/SSE
├── panel.html                     # 主舞台壳层（语义化结构，无内联渲染逻辑）
├── panel.css                      # 视觉系统（token/皮肤/响应式/动效降级）
├── panel.js                       # 数据层 + 状态层 + 渲染/反馈层
├── rules/                         # 规则内核（含 models.py 命名闭式模型层）
├── settings/                      # 设定包（玄枢界等）
└── scripts/                       # verify_mcp_stdio / verify_panel / verify_cli / verify_tests / user_playtest / stress_freeplay
```

## 6. 核心数据模型

### 6.1 面板视图模型（/state 与 SSE 载荷，字段名冻结）

```text
view_model = {
  world: { name, era, location_desc },
  tick: int, updated_at: str, seed, flags: [str],
  skin: { id: "xuanshu"|"neutral", accent: "#rrggbb" },
  player: { name, level, stage, location, hp, hp_max, mp, mp_max, gold, karma, attrs,
            inventory: [{ key, name, quantity, type }] },
  scene: { location, title, description, mood: "neutral|danger|trade|social|growth|discovery",
           focus_event: str|null },
  events: [{ id, tick, type, kind, severity: "info|success|warning|danger",
             title, desc, icon, milestone: bool }],      # 最多 40 条，旧→新
  present: [{ id, name, level, hp, hp_max, desc, relation }],
  relations: [{ id, name, affinity, respect }],           # 只含与 player 有关
  market: [{ location, items: [{ key, name, price, base_price, supply, delta, type }] }],
  codex: { locations, people, items, lore },
  insights: { flow, phase, identity },
  moral: { dims, values },
  chronicle: [event_log 最近 24 条], milestones: [str], summaries: int,
  archived_events: int, others: [{ id, name, location }], lore_total: int
}
```

- `events.id = "tick:type:sha1(desc)[:8]"`，确定性去重键。
- 事件分类（kind/severity/title/icon）只由 `panel.py` 决定；前端不做关键词判断。

### 6.2 运行时不变量（Runtime Invariants）

| # | 不变量描述 | 作用域 | 维护方 | 校验方式 |
|---|---|---|---|---|
| INV-V1 | 面板任何请求不修改状态文件（字节不变） | 面板全请求 | panel.py | verify_panel.py（sha256 前后对比） |
| INV-V2 | 视图模型数值直接来自存档或引擎推导，前端不重算游戏结果 | 视图模型 | panel.py | verify_panel.py 契约断言 |
| INV-V3 | 每条 events 条目齐备 9 字段且 severity 合法 | /state | panel.py | verify_panel.py 遍历断言 |
| INV-V4 | 旧存档（缺 items/relations/market/event_log）返回合法空值与中性皮肤 | /state | panel.py | verify_panel.py legacy fixture |
| INV-V5 | 弹窗焦点不逃逸、Escape 可关、关闭后焦点回到触发控件 | 前端 | panel.js | 浏览器键盘冒烟 |
| INV-V6 | 320px 无横向滚动；颜色非唯一语义；reduced-motion 关动效 | 前端 | panel.css/js | 浏览器尺寸冒烟 + CSS 审查 |
| INV-V7 | SSE 断开后轮询继续刷新且连接状态可见 | 前端 | panel.js | 浏览器断线冒烟 |
| INV-V8 | 静态资源仅白名单文件；路径穿越/任意文件读取一律 404 | HTTP 层 | panel.py | verify_panel.py 安全断言 |
| INV-E1 | 状态文件 price ∈ (0, 3×base_price]，hp/gold ≥ 0，事件日志 ≤ keep | 引擎 | mcp_server/rules | stress_freeplay.py |
| INV-E2 | 卖出须持有；自备物品使用不再扣钱 | 引擎 | rules/economy.py | user_playtest.py |
| INV-E3 | 只读子命令不重写状态文件（字节不变）且不推进 rng_counter | CLI | engine.py | verify_cli.py（sha256 前后对比） |
| INV-E4 | 同一状态文件 + 同一行动 → 同结果（CLI 与 MCP 双通道），快照回退后重放亦然 | 引擎 / MCP | state_schema.seed_rng | verify_cli.py 确定性断言 + verify_mcp_stdio.py 快照重放 |
| INV-E5 | 玩家气血不得归零（保底 1）；归零改判濒死：掉钱 30%、心伤 +1、事件与大事记留痕，且必须落盘 | 引擎 | rules/combat.py | verify_near_death.py（R1-R3 七项断言 + 重读落盘） |

## 7. 关键接口 / API 约定

| 接口 | 语义 | 响应 |
|---|---|---|
| `GET /`、`GET /panel.html` | 主舞台页面 | 200 text/html |
| `GET /panel.css`、`GET /panel.js` | 静态资源 | 200 text/css / text/javascript |
| `GET /assets/echarts.min.js` | 离线图表库（vendored Apache-2.0, echarts@5.5.1） | 200 text/javascript |
| `GET /state` | 视图模型 JSON | 200 application/json |
| `GET /series` | 长局态势样本（tick 升序，封顶 600）+ 皮肤调色板 | 200 application/json |
| `GET /events` | SSE：状态文件签名变化即推 `event: state` + 完整视图模型 | text/event-stream |
| 其他路径 | 一律拒绝 | 404（不含任何文件内容） |

### 7.1 长局态势侧写（viz_series.py）

- 侧写文件 `<状态文件>.viz.jsonl`：每 tick 一条样本 `{tick, hp, hp_max, mp, mp_max, gold, karma, price_index, affinity_avg, codex_total, location}`；封顶 600 条。
- **双写点**：引擎 `_finish`（每次结算落盘后）与面板 `view_model`（打开时兜底）都调用 `viz_series.record_sample`；
  同 tick 覆盖、旧 tick 丢弃（快照回退不追旧点），因此幂等，且玩家不开面板的回合也不断档。
- 该文件由面板侧持有，**从不写状态文件**（INV-V1 不变）。

### 7.2 皮肤与品牌契约（面板）

- `/state.skin` 携带 `brand`（默认「万界·行者」）与 `tagline`（默认「万界为卷 · 因果为墨」）；
  `ui.brand` / `ui.tagline` 整局覆盖（服务端截断 brand≤24、tagline≤48）。品牌单一信源为 `panel.py::DEFAULT_BRAND`
  + `BRAND.md`，verify_panel 断言默认字符串防漂移。
- `/state.meta` 提供 `state_path` / `sidecar` / `read_only`，供帮助弹窗展示数据位置（面板默认只绑 127.0.0.1，属本机信息）。
- 帮助体系（只读展示层，无新接口）：顶栏按钮 + `?` 快捷键 → 帮助弹窗（这是什么/术语表/图表读法/键盘/
  数据与隐私/皮肤）；首访一次性引导条（localStorage，隐私模式降级为会话内记忆）。


- 皮肤 id：`xuanshu`（玄门·墨金）/ `neutral`（通用·石墨）/ `ink`（水墨）/ `neon`（霓虹）。
- 解析顺序：状态 `ui.skin`（可由设定包/`world_init` 传入）→ 世界名启发式（含「玄枢」→ xuanshu）→ `neutral` 兜底；
  `ui.accent`/`ui.motif` 可覆盖主色与风格文案。
- 每套皮肤带图表调色板（line/area/bar/hp/mp/grid/text），随 `/state.skin` 与 `/series.palette` 下发；前端不在 JS 里维护配色表。

## 8. 架构决策记录（ADR 索引）

- [ADR-001] 原生模块化网页主舞台（panel.html/css/js 三件套，无框架无构建）— 已采纳
- [ADR-002] 第一阶段面板严格只读，MCP 保持唯一写入源 — 已采纳
- [ADR-003] 事件分级/皮肤判定集中在 panel.py 服务端，前端零关键词表 — 已采纳

### ADR-001：原生模块化主舞台
- **状态**：已采纳 ｜ **日期**：2026-10-15
- **背景**：现有单文件 panel.html 更适合监控仪表盘，要做叙事主舞台 + 弹窗 + 皮肤会膨胀且难维护；引入 React/Vite 则带来构建链与新依赖。
- **候选**：A 继续单文件内联；B 原生模块化（html 壳层 + css + js）；C React/Vite 独立前端。
- **决定**：B。
- **理由**：质量属性优先"可维护 + 零依赖"；单机只读面板规模不需要框架；后续若网页行动/路由/多会话证明不足再走 ADR 迁移。
- **后果**：正面——无构建、可直接开文件调试、部署成本为零；负面——组件复用靠约定而非框架，复杂交互增多后需自律分层（panel.js 固定三层）。

### ADR-002：只读阶段（MCP 单一写入源）
- **状态**：已采纳 ｜ **日期**：2026-10-15
- **背景**：网页若能直接改状态，会出现第二套结算入口，破坏确定性（rng_counter/快照回退）与"所有数值经引擎"的协议。
- **决定**：第一阶段面板只读；行动仍由宿主经 MCP 结算。
- **后果**：正面——不变量简单、可复现性保住；负面——玩家需回到对话里发行动（第二阶段评估网页行动入口 + 一致性方案）。

### ADR-003：事件分级集中在服务端
- **状态**：已采纳 ｜ **日期**：2026-10-15
- **背景**：前端若自己做关键词表，两级逻辑会漂移。
- **决定**：`panel.py::classify_event` 是唯一分类器，输出 kind/severity/title/icon；前端只消费。
- **后果**：正面——分类可单测、可版本化；负面——新增事件类型需改 panel.py（有未知类型默认兜底）。

## 9. 实施计划（任务清单）

> 状态：[ ] 未开始  [~] 进行中  [x] 已完成
- [x] T1 架构基线与视图模型契约（ARCHITECTURE.md + AQG 账本）— 验证：文档落盘
- [x] T2 面板数据层与静态白名单 — 验证：verify_panel.py 契约全绿
- [x] T3 主舞台壳层与视觉系统（panel.html/css）— 验证：/ 200、皮肤/响应式冒烟
- [x] T4 前端状态层与反馈层（panel.js：SSE/toast/dialog/抽屉）— 验证：浏览器冒烟（弹窗/Escape/断线降级）
- [x] T5 回归与文档同步 — 验证：verify_panel / verify_mcp_stdio / user_playtest 全绿
- [x] T6 品牌与体验打磨（字标/标语/favicon/错误横幅/重试/中文化/弹窗居中）— 验证：verify_panel 28/28 + 浏览器冒烟 22/22
- [x] T7 长局态势可视化（采样侧写 + /series + 三图表 + 事件谱）— 验证：verify_panel 42/42 + 浏览器冒烟 14/14
- [x] T8 视觉组件深化（关系网/地点图/修行轨/徽章 + 长局折叠收敛）— 验证：2000 轮真实存档渲染冒烟
- [x] T9 世界观皮肤 v2（ui 配置 + 四套皮肤 + 图表配色联动）— 验证：改 state.ui 免重启即换肤
- [x] T10 品牌与帮助打磨（品牌可配置 + BRAND.md + 帮助弹窗/术语表/`?` + 首访引导 + 千分位）— 验证：verify_panel 48/48 + 品牌冒烟 20/20
- [x] T11 上传前置：打包完整性（package-data/MANIFEST.in，v0.8.0）+ 安装包真机验证 + 版本/文档对齐 + 残留清理 — 验证：wheel 内资源齐全 + 从安装包启动面板 5 端点全 200
- [x] T12 交付物完善：dist 发行包实打（sdist + wheel 落盘）+ 面板截图入仓（docs/screenshots，2000 回合存档现场重截、断言先行）+ 双 README 预览区 + 截图随 sdist/wheel 分发 — 验证：截图断言 35/35 + 产物条目核对 + 安装包冒烟 + 回归全绿
- [x] T13 确定性契约固化：新增 scripts/verify_cli.py（18 项）覆盖 CLI 只读写不变量/写通道落盘/双通道确定性；verify_mcp_stdio.py 增快照点重放断言（49 项）— 验证：verify_cli 18/18 + verify_mcp_stdio 49/49 + 全量回归绿
- [x] T15 濒死保护（玩家永不死亡 + 真实代价）：rules/combat.py 新增 _apply_near_death——玩家气血归零改判重伤退场，保底 1 血、掉 30% 钱财、心伤 +1、near_death_count 累加、事件与结算结果留痕；NPC 死亡语义不变；stress_freeplay 删除"改内存假装复活"的假修复，改为断言濒死保护未失效；面板显示濒死次数 — 验证：verify_near_death 7/7（含落盘复读）+ MCP 端到端实测 gold 100→70 且写盘
- [x] T16 测试可信度第二轮（独立专家团审计后）：verify_tests.py 重写为 9 条规则（R0 解析失败/R1 短路恒真/R2 常量表达式/R3 恒真下界/R5 恒假/R6 断言数量下限/R7 自反恒等式/R8 纯度型弱断言/R9 死分支），并兼容 stress 的三参数 check 签名（此前整个文件不在审计范围）；修复 verify_cli 写命令只验 rng_counter 不验业务效果（trade no-op 曾 19/19 全绿）、三副本全失败假通过；user_playtest 价格自比恒真改为独立手算 OU 闭式解、突破零成功恒真；stress 归档计数与回退断言由恒真改为严格等式；verify_mcp 补 trade 入库/减库存、social 落盘、merit 精确值；state_schema.save_state 修快照回退后归档文件与计数漂移（真 bug）— 验证：verify_tests 0/168 可疑 + 7 种假写法全部被抓 + 清空断言被 R6 抓 + 五类代码变异（trade/social/karma no-op、价格回归失效、归档计数归零）全部 FAIL
- [x] T17 归档安全与断言精确化（第三轮独立复验后）：回滚上一版"按计数截断归档文件"的错误修复（那会静默删除用户历史），改为按 archive_generation 分世代归档——回退只切文件、不删任何已有归档，recall 跨世代回捞；restore 时 archived_events 取历史总和（只增不减）；verify_tests 补齐关键字传参/裸常量/bool(常量比较)/(常量) is True/if 0 死分支/BoolOp 内恒真下界等 7 类绕过路径，EXPECTED 改为精确静态基数；verify_cli 四条写命令改为精确等式（伤害=扣血、扣款=total_cost、affinity/respect 固定增量、账本 amount/type/from/to）；verify_mcp 增"回退后旧归档逐条仍可召回"硬断言 — 验证：verify_tests 0/168 + 7 类绕过全抓 + 5 类变异全 FAIL + stress 2000/2000
- [x] T14 测试可信度治理：修复 5 处恒真/无效断言（verify_cli 只读探针比较两份副本、verify_panel 侧写 `or True`、皮肤循环 for/else 硬编码 True、stress 归档与回退断言恒真）；新增 scripts/verify_tests.py 做 AST 级断言审计（R1 恒真/R2 常量/R3 恒真下界/R4 弱断言）；修正 world_schema event_log 错误陈述（50→config.event_log_keep 默认 200）— 验证：verify_tests 0 可疑 + 三处变异测试均能被抓出

## 10. 变更日志（Changelog）

| 日期 | 变更摘要 | 影响的章节 | 关联任务/ADR | 验证方式 |
|---|---|---|---|---|
| 2026-10-15 | 初始架构建立：只读主舞台（视图模型契约、静态白名单、事件分级、皮肤、a11y） | 全部 | T1–T5 / ADR-001..003 | verify_panel.py 全绿 + 浏览器冒烟 |
| 2026-10-15 | 品牌与体验打磨：字标/标语/favicon/theme-color/页签标题；缺档/读取失败 → 横幅 + 重试（SSE 不断流推错误态）；弹窗居中修复；气血吃紧标记、大事记芯片、相位中文、货币名；karma/交易事件文本中文化与显示名 | §6.1（player.currency 新字段）、§7（/state 错误态）、§9 T6 | T6 | verify_panel 28/28 + 浏览器冒烟 22/22 + 回归 48/48 & 41/41 |
| 2026-10-15 | 长局可视化深化：离线 ECharts（vendored）+ 态势侧写 `/series`（600 封顶）+ 三图表/事件谱/关系网/地点图/修行轨/徽章 + 皮肤 v2（ui 配置/四皮肤/图表配色）+ 长局折叠收敛 | §5、§6.1、§7、新增 §7.1-7.2、§9 T7-T9 | T7-T9 / ADR-004 | verify_panel 42/42 + 浏览器冒烟 14/14 + 2000 轮 stress 全绿 + 2000 轮真实存档渲染冒烟 |
| 2026-10-15 | 品牌与帮助打磨：品牌可配置（ui.brand/tagline + DEFAULT_BRAND 单一信源 + BRAND.md）+ meta 暴露数据路径 + 帮助弹窗（术语表/图表读法/键盘/数据隐私/皮肤）+ `?` 快捷键 + 首访引导条 + 大数千分位 | §7.2、§9 T10、新增 BRAND.md | T10 | verify_panel 48/48 + 品牌冒烟 20/20 + viz 冒烟 14/14 + 回归 48/48 & 41/41 |
| 2026-10-15 | 上传准备（v0.8.0）：wheel 资源完整性修复（panel.*/assets/settings 进包）、MANIFEST.in、服务端版本对齐 0.7.0→0.8.0、文档断言计数与结构清单对齐、残留运行文件清理 | §4、§5、§9 T11 | T11 | wheel 36 条目含全部资源 + pip --target 安装后面板 5 端点 200 + 全量回归绿 |
| 2026-10-15 | 交付物完善：dist 发行包实打落盘（sdist + wheel）+ 面板截图入仓（docs/screenshots 六张，2000 回合存档现场重截、截图前 35 项断言）+ 双 README 界面预览区 + 截图与来源说明随 sdist/wheel 分发（package-data/MANIFEST 纳入 docs） | §4、§5、§9 T12 | T12 | 见 .aqg/code-construction/screenshots-and-dist.md 验证日志 |
| 2026-10-19 | 依赖澄清与确定性修复（v1.1）：移除 rules 对 numpy 的隐性硬依赖（world_dynamics/cultural_evolution 共 4 个矩阵函数改纯 Python，与 numpy 对拍 200 组最大偏差 3.6e-15；ndarray 入参仍兼容），§2「仅标准库」约束自此真实成立；`seed_rng` 下沉 state_schema 供 CLI 与 MCP 共用，CLI 补齐种子确定性（修复前同状态两次 combat 伤害 19/16 不等）；engine.py 只读命令不再重写状态文件（dirty flag）；panel.py 清除被 shadow 的死代码（旧 skin_for_world + SKIN_ACCENTS）；rules 各模块 docstring 的理论引用改文献出处（原引用的 .md 不在仓库）；social_extended.basic_reproduction_number 转调模型层保单一实现；demo_state.json 按现行引擎重生（补 rng_seed、因果中文标签） | §2、§4、§5 | — | 本机复跑：无 numpy 环境 verify_panel 48/48 + CLI 确定性 A=B；venv（numpy+mcp）verify_panel 48/48、verify_mcp_stdio 48/48、user_playtest 41/41、stress 300/300 零违规 |
| 2026-10-20 | 确定性契约固化（v1.2）：新增 `scripts/verify_cli.py`（18 项）把 CLI 通道的三类性质变成常驻断言——9 条只读命令前后状态文件 sha256 不变且不推进 `rng_counter`、combat/trade/social/karma/tick 五条 dirty 分支全部落盘且字段有界、三副本同行动与双副本 12 步混合动作终态逐字节一致；`verify_mcp_stdio.py` 增 1 项快照点重放断言（49 项），覆盖 `rng_counter` 随快照回退后的确定性语义；§6.2 新增 INV-E3/E4；文档断言计数与结构清单同步 | §4、§6.2、§9 T13 | T13 | verify_cli 18/18 + verify_mcp_stdio 49/49 + verify_panel 48/48 + user_playtest 41/41 + stress 2000/2000 零违规 |
| 2026-10-20 | 测试可信度治理（v1.3）：逐条审计四套自检共 160+ 断言，修掉 5 处假测试——① verify_cli 只读探针比较两份 demo 副本而非被测命令结果；② verify_panel 侧写断言 `os.path.exists(...) or True` 恒真；③ 皮肤调色板循环用 for/else 把结论硬编码成 True；④ stress `失败回退后 stage 保持` 只判 tick>=0；⑤ stress `archived_events 与归档行数一致` 只判文件存在。新增 `scripts/verify_tests.py`（AST 级审计 R1-R4，拒绝恒真/常量/恒真下界/弱断言），并以三处代码变异反向验证其有效性；修正 world_schema `event_log 最多 50 条` 与默认 keep=200 不符的错误陈述。断言数：verify_cli 18→19、verify_panel 48→52 | §4、§9 T14 | T14 | verify_tests 0 可疑 + verify_cli 19/19 + verify_panel 52/52 + verify_mcp_stdio 49/49 + user_playtest 41/41 + stress 2000/2000 零违规 |
| 2026-10-20 | 濒死保护（v1.4）：玩家永不真正死亡——气血归零改判「重伤退场」，保底 1 气血，代价为掉 30% 钱财 + 心伤 +1 + near_death_count 累加 + 事件与结算结果留痕，全部写入状态文件；NPC 死亡语义不变。删除 stress_freeplay 中「直接改内存 p['hp']=hp_max 假装复活」的假修复（状态文件从未变化），改为断言濒死保护未失效；面板与视图模型新增 near_death_count。§6.2 新增 INV-E5 | §6.1、§6.2、§9 T15 | T15 | verify_near_death 7/7（含 save_state 后重读核验）+ MCP stdio 端到端 gold 100→70 且磁盘一致 + 全套自检绿 |
| 2026-10-21 | 测试可信度第二轮（v1.5）：独立专家团审计发现上一轮 5 处修复中 1 处未真正修复（归档断言 `arch>=0` 仍恒真）、1 处只修一半（回退断言 no-op restore 仍过），且 verify_tests 只能抓 20+ 种假写法中的 3 种、stress 的 10 条断言因签名不同完全不在审计范围。本轮重写审计器为 9 条规则并兼容双签名；补齐 verify_cli 写通道业务断言（trade no-op 曾 19/19 全绿）、user_playtest 价格自比与突破零成功、stress 归档/回退严格断言、verify_mcp 的 trade 入库/social 落盘/merit 精确值；并修出真 bug：快照回退后归档文件行数与 archived_events 永久漂移（300 轮实测差 2 行），save_state 现按计数截断归档文件 | §6.2、§9 T16 | T16 | verify_tests 0/168 + 7 种假写法全抓 + 清空断言被 R6 抓 + 五类变异全 FAIL + 回归全绿 |

### ADR-004：长局可视化的三个取舍
- **状态**：已采纳 ｜ **日期**：2026-10-15
- **背景**：目标"玩很多轮、很多系统、很多变化"，需要趋势而不只是当前值；同时有多个世界观要适配；且面板必须保持只读。
- **决定**：
  1. **趋势数据用侧写文件**（`<state>.viz.jsonl`，600 条封顶、tick 幂等去重），而不是把历史塞进状态文件或内存。
  2. **图表库本地 vendored**（echarts@5.5.1，1.0MB，Apache-2.0），不引 CDN——面板离线可用，资产缺失时整块降级为文案。
  3. **皮肤由状态配置驱动**（`ui.skin/accent/motif` + 世界名启发式兜底），而不是写死一套视觉或让前端猜。
- **后果**：正面——长局有趋势图、换世界换皮肤零代码、面板仍然只读且离线可用；负面——仓库多 1MB 静态资产；侧写是"面板自己的账"，删除该文件只丢历史曲线，不影响对局。
