# Roadmap / 路线图

> **Current version**: v9.1.0 (2026-06)
> **Release cadence**: 季度大版本 + 持续小补丁

This document outlines the high-level direction of the **Regional Economic Analysis Agent** —
production-grade multi-scenario analytics with self-developed LLM agent and 3 entry points
(Web Dashboard / Python SDK / CLI / **Web Console**).

---

## v9.1.0 (2026-06) ✅ **Current — Web Console**

### Headline features
- 🌐 **Web Console** `/console/` — 零代码、零安装浏览器管理界面
  - 9 项 tool 可视化(ensemble / diagnostics / backtest / risk / scenarios / MC / provenance / macro / cities)
  - LLM Agent 流式 chat(SSE)
  - 在线改 LLM 配置(model / base_url / temperature / max_tokens / max_tool_rounds / timeout)
  - 历史 1000 条 ring buffer + tool 过滤 + 清空
- 🛠 后端 8 个 admin endpoint (`/api/v1/admin/*`) + `HistoryStore` + `ConfigStore`(thread-safe)
- 🎨 13 个静态 HTML + 4 JS helper + 1 CSS(零 build step,继承 `index.html` design tokens)
- 🐛 修 4 处前端/后端字段不匹配漏洞(diagnostics.tests / ensemble.ci / backtest.metrics / monte_carlo.quantiles)
- 🧪 +82 测试(370 → 452 pass)
- 📚 `docs/CONSOLE_GUIDE.md`(257 行用户指南)

---

## v9.0.0 (2026-06) ✅ — Python SDK + CLI

### Headline features
- 🐍 **Python SDK `rca` 包** — 9 tool + chat + chat_stream + RCAClient + 4 错误类,完整 re-export
- 🖥 **CLI `rca` 命令** — 11 Typer 子命令(9 tool + chat + chat-stream + config)
- 📤 **3 输出格式** — `rich` / `plain` / `json`
- 🔧 **`rca config`** — 在线查/改 LLM 配置(set / show)
- 🐛 修 `--model` / `--base-url` show-only 漏洞(2 个回归 test)
- 🧪 +66 测试(304 → 370 pass)
- 📚 `docs/SDK_CLI_GUIDE.md`(完整用户指南)
- ⚙️ `pyproject.toml` 加 `rca = "cli.main:app"` entry point

---

## v8.0.0 (2026-06) ✅ — Self-developed LLM Agent + Eval

### Headline features
- 🧠 **4 个自研模块**(不引 LangGraph / Pydantic AI):
  - `Trace` — 完整审计 + SSE `done` 事件含 `trace: [...]`
  - `Fallback` — 5 个百炼模型自动降级,401/403/404 立即抛,超时/429 降级
  - `Parallel tools` — `ThreadPoolExecutor` + 异常隔离 + 单 tool 超时
  - `Retry hint` — 7 类白名单 + 反射 prompt
- 📊 **Eval 框架** — 10 个真实业务 query 跑分(6 维度评分 + case 对比)

---

## v7.0.0 (2026-06) ✅ — AI chat assistant

### Headline features
- 🤖 LLM 对话助手(LiteLLM 统一 OpenAI / Claude / Ollama)
- 🛠 9 个 tool(Function Calling 自动路由到现有 API)
- 💬 浮动 chat widget(SSE 流式 + 打字机)
- 🔄 双模式可切换(云端 API ↔ 本地 Ollama)

---

## v6.1.0 (2026-06) ✅ — Docker investment-grade engine stack

### Headline features
- 🐳 **Docker 投资级引擎栈**:`statsforecast` / `arch` / `pmdarima` 预装
- ⚙️ **`backend/core/engine_stack.py`** — 运行时库探测模块,自动 fallback
- 🚀 `auto_arima_native()` — AutoARIMA 路径(statsforecast > pmdarima > statsmodels)
- 📈 `garch_volatility()` — GARCH(1,1) 条件波动率 + 持续性 + 半衰期

---

## v6.0.0 (2026-06) ✅ — Investment-grade forecasting platform

### Headline features
- 📊 **10 城 × 12 指标 × 16 年** 真实公开数据(1920 数据点)
- 🌍 4 宏观协变量(NBSC / PBOC / MOFCOM,2010-2025)
- 🎯 **3 模型集成**(ARIMA + ETS + LR, AIC-weighted)
- 🩺 **5 项残差诊断**(ADF / KPSS / Ljung-Box / Jarque-Bera / Breusch-Pagan)
- 🧪 **5 项 walk-forward CV**(MAPE / RMSE / MASE / sMAPE / Coverage)
- 📉 **风险分析**:VaR / CVaR / 4 档情景 / 1000-iter Monte Carlo
- 🧬 **结构突变检测**(Chow test)
- 🕵️ **数据血缘**:每条数据带 source URL + confidence + estimated flag
- 🌐 **7 个新投资端点**(`/api/v1/investment/*`)+ **5 个血缘端点**(`/api/v1/lineage/*`)
- 📊 `frontend/investment_grade.html` — 投资决策级 dashboard

---

## v9.2.0 (Target: 2026-07) 📋 **Next**

### 🎯 Theme: Console 增强 + Phase 3 展示站

- [ ] **GitHub Pages 改展示站** — `frontend/index.html` 改成 RCA 介绍 marketing 站(功能 / demo 截图 / 文档链接 / 引导到 Console)
- [ ] **Console 用户认证** — Web Console 加 basic auth 套件 / 集成 OAuth(配合 nginx)
- [ ] **Console 导出** — 单 tool 结果导出 CSV / PNG / PDF
- [ ] **Console 主题切换** — light / dark 模式
- [ ] **Console 国际化** — zh-CN / en-US toggle

### Console 健壮性
- [ ] history 持久化(可选 SQLite 替代 ring buffer)
- [ ] tool result 缓存(避免重跑相同 query)
- [ ] LLM chat WebSocket(替代 SSE,支持双向)

### Quality
- [ ] Console 前端单测(Playwright)
- [ ] Console 无障碍(ARIA roles)
- [ ] Console 性能:Lighthouse 90+

---

## v9.3.0 (Target: 2026-08) 📋 Planned

### 🎯 Theme: 数据采集 + 第三方集成

- [ ] **Wind / 同花顺** 数据连接器
- [ ] **NBS / CEIC** 公开数据 cron 自动刷新
- [ ] **Anomaly detection** — 数据接入时 flag 异常值
- [ ] **5 个新城市**:苏州 / 重庆 / 长沙 / 青岛 / 宁波
- [ ] **Bilingual labels** — zh-CN / en-US toggle

### Performance
- [ ] Redis 适配器(查询结果缓存)
- [ ] Response-time SLA dashboard

---

## v10.0.0 (Target: 2026-10) 🔭 Vision

### 🎯 Theme: Multi-tenancy & 实时

- [ ] **User accounts / roles / orgs** — 多租户 + 权限
- [ ] **API key management** 外部集成
- [ ] **Audit log** — 谁在何时做了什么
- [ ] **WebSocket** 实时推送(forecast 更新)
- [ ] **Streaming analytics** — Kafka / Pulsar 接入
- [ ] **Mobile app** — React Native
- [ ] **GraphQL API** 与 REST 并行

---

## Long-term vision (2026 Q4+)

- 🌐 **Open data marketplace** — 分享 derived datasets
- 🏆 **Industry benchmarks** — 社区贡献的评分标准
- 🤝 **Partner ecosystem** — 第三方 plugin / theme
- 🎓 **Education edition** — 学生沙箱环境
- 🏢 **Enterprise edition** — SSO / RBAC / 审计

---

## Won't do / 不做的事情

To stay focused, we will **not** add the following to the core product:

- ❌ **Real-time stock trading** (we do forecasting, not execution)
- ❌ **CRM / ERP** features (use a dedicated product for that)
- ❌ **Blockchain / Web3** (out of scope)
- ❌ **End-user marketing automation** (out of scope)

If you need any of these, please build on top of our public API.

---

## Contributing to the roadmap / 参与规划

- 💭 **Open a Discussion** in the `roadmap` category
- 🗳️ **Vote on existing proposals** with 👍 / 👎 reactions
- 📝 **Submit a Feature Request** issue
- 🤝 **Maintainer nomination** for a topic area

---

**Last updated**: 2026-06-05
**Current version**: v9.1.0
**Next review**: 2026-07 (v9.2.0 planning)
