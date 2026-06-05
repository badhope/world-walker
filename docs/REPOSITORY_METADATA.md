# GitHub Repository Metadata / GitHub 仓库元数据

> GitHub's "About" section (description + topics + website + social preview) can only be edited through the GitHub web UI, not from files in the repository. Copy-paste the values below into the **Settings → General → "About"** panel of your GitHub repository.
>
> GitHub 的"About"区域(描述、主题、网站、社交预览)只能通过 GitHub Web UI 编辑,无法由仓库内的文件直接控制。请把下面的值复制到 **Settings → General → "About"** 面板中。
>
> **Current version**: v9.1.0 · **Last updated**: 2026-06-05

---

## Repository name (建议)

**`regional-economic-analysis`**

(简明、聚焦、可搜索。)

---

## Description / 描述

> _A production-grade multi-scenario analytics agent for regional economic analysis — 10 Chinese cities × 12 indicators × 16 years of real public data + 4 macro covariates. **Investment-grade forecasting** (3-model ensemble + 5 residual diagnostics + walk-forward CV + VaR / CVaR / GARCH / 4 scenarios / 1000-iter Monte Carlo). **Self-developed LLM agent** (no LangGraph / Pydantic AI) with 9 tool calls. **3 entry points**: Web Dashboard / Python SDK / CLI / **Web Console**. FastAPI · Pydantic v2 · 452 tests._

长度:**750 字符以内** (GitHub 限制 ≤ 350,最佳 ≤ 180)
> 实际 GitHub 描述字段最大 350 字符 — 用下面的"短版本"。

### 短版本 (推荐,~178 字符)

> _Production-grade multi-scenario analytics agent for regional economic analysis — 10 cities × 12 indicators × 16 years. Investment-grade forecasting + self-developed LLM agent. Web Dashboard / Python SDK / CLI / Web Console._

### 中文版本

> _生产级多场景区域经济分析 agent:10 城 × 12 指标 × 16 年真实公开数据 + 4 宏观协变量;投资级 forecast(3 模型集成 + 5 残差诊断 + VaR/CVaR/MC)+ 自研 LLM Agent(9 tool call);3 入口(Dashboard / SDK / CLI / Web Console)。_

---

## Topics / 主题 (推荐 15 个以内)

在 GitHub 仓库主页点击 "⚙️" 旁的齿轮,添加以下标签(按重要性排序):

| # | Topic | 含义 |
|---|-------|------|
| 1 | `regional-economy` | 区域经济(核心定位) |
| 2 | `economic-analysis` | 经济分析 |
| 3 | `llm-agent` | 自研 LLM Agent(v7.0+ 核心) |
| 4 | `time-series-forecasting` | 时序预测(ARIMA / ETS / LR) |
| 5 | `risk-analysis` | VaR / CVaR / GARCH |
| 6 | `monte-carlo` | 蒙特卡洛模拟 |
| 7 | `data-provenance` | 数据血缘(每点带 source URL) |
| 8 | `python-sdk` | v9.0 Python SDK |
| 9 | `cli` | v9.0 Typer CLI |
| 10 | `web-console` | v9.1 Web Console(零代码) |
| 11 | `fastapi` | 后端技术栈 |
| 12 | `echarts` | 前端图表库 |
| 13 | `pydantic` | 类型安全 |
| 14 | `data-science` | 学科领域 |
| 15 | `open-source` | 开源 |

---

## Website URL / 网站

设置为:<https://github.com/badhope/national_stats>

(如果没有自定义域名,可以指向仓库主页本身,或留空。Phase 3 计划加 GitHub Pages 展示站后会更新。)

---

## Releases / Releases 标签

发布 v9.1.0 时建议附带:

```markdown
## What's New in v9.1.0 — Web Console

### Highlights
- 🌐 **Web Console `/console/`** — 零代码、零安装浏览器管理界面
  - 9 项 tool 可视化(ensemble / diagnostics / backtest / risk / scenarios / MC / provenance / macro / cities)
  - LLM Agent 流式 chat(SSE)
  - 在线改 LLM 配置(model / base_url / temperature / max_tokens / max_tool_rounds / timeout)
  - 历史 1000 条 ring buffer + tool 过滤 + 清空
- 🛠 后端 8 个 admin endpoint + `HistoryStore` + `ConfigStore`(thread-safe)
- 🎨 13 个静态 HTML + 4 JS helper + 1 CSS(零 build step,继承 design tokens)
- 🐛 修 4 处前端/后端字段不匹配漏洞(diagnostics.tests / ensemble.ci / backtest.metrics / monte_carlo.quantiles)
- 🧪 +82 测试(370 → 452 pass)

### v9.0.0 — Python SDK + CLI
- 🐍 **Python SDK `rca` 包** — 9 tool + chat + RCAClient
- 🖥 **CLI `rca` 命令** — 11 Typer 子命令,3 输出格式
- 📚 `docs/SDK_CLI_GUIDE.md`
- ⚙️ `pyproject.toml` 加 `rca = "cli.main:app"` entry point
- 🧪 +66 测试

### v8.0.0 — Self-developed LLM Agent
- 🧠 **4 个自研模块**:Trace / Fallback / Parallel tools / Retry hint
- 📊 Eval 框架 — 10 个真实业务 query 跑分

### Stack
FastAPI · Pydantic v2 · statsmodels / statsforecast / arch · LiteLLM · Typer · Rich · ECharts 5.6 · 452 pytest
```

---

## Social Preview Image / 社交预览图

GitHub 仓库 → **Settings → General → Social preview**:

- 推荐尺寸: **1280 × 640 px**
- 格式: PNG 或 JPG,< 1 MB
- 内容建议:项目 Logo + 一句话定位 + 关键特性图标 + **3 入口**视觉

参考开源项目示例:
- <https://github.com/tiangolo/fastapi> (FastAPI 官方)
- <https://github.com/streamlit/streamlit>

---

## Pinned Issues / 置顶 Issue

发布后建议置顶 2-3 个 Issue 来引导社区:

1. **Welcome / 欢迎** — 项目介绍 + 如何贡献
2. **Roadmap / 路线图** — v9.2 / v9.3 / v10.0 计划([ROADMAP.md](../ROADMAP.md) 完整版)
3. **Help Wanted / 寻求帮助** — 列出 good first issue

模板可在 GitHub 上创建后置顶。

---

## GitHub Pages / 项目主页 (Phase 3 计划)

**当前**:`frontend/index.html` 是投资 dashboard(只读),GitHub Pages 默认从 main branch 的 root 渲染。

**Phase 3 计划(v9.2)**:
- 把 `frontend/index.html` 改成 RCA 介绍 marketing 站(功能 / demo 截图 / 文档链接 / 引导用户到 Console)
- 配置 `frontend/index.html` 为 GitHub Pages source

启用方法:
1. **Settings → Pages**
2. **Source**: `Deploy from a branch`
3. **Branch**: `main` / `frontend` (看你想 publish 哪个)
4. **Path**: `/` (root) 或 `/frontend`

---

## PyPI 发布 (可选)

如需发布到 PyPI:

1. 注册账号:<https://pypi.org/account/register/>
2. 配置 `~/.pypirc`
3. 构建包:
   ```bash
   python -m pip install --upgrade build twine
   python -m build
   ```
4. 上传:
   ```bash
   python -m twine upload dist/*
   ```
5. 安装验证:
   ```bash
   pip install regional-economic-analysis
   rea-api
   ```

发布到 PyPI 后,描述和标签会从 [pyproject.toml](../pyproject.toml) 和 [setup.py](../setup.py) 自动同步。

---

## 快速复制清单

- [ ] 仓库名:`regional-economic-analysis`
- [ ] 描述:`Production-grade multi-scenario analytics agent for regional economic analysis — 10 cities × 12 indicators × 16 years. Investment-grade forecasting + self-developed LLM agent. Web Dashboard / Python SDK / CLI / Web Console.`
- [ ] 主题:`regional-economy` `economic-analysis` `llm-agent` `time-series-forecasting` `risk-analysis` `monte-carlo` `data-provenance` `python-sdk` `cli` `web-console` `fastapi` `echarts` `pydantic` `data-science` `open-source`
- [ ] Website:`https://github.com/badhope/national_stats`
- [ ] Releases:v9.1.0
- [ ] Social preview 图:1280×640 PNG
- [ ] GitHub Pages 启用(Phase 3 后)
- [ ] PyPI 发布(可选)

---

**最后更新**:2026-06-05 (v9.1.0)
**适用版本**:v9.1.0+
**配套文档**:
- [README.md](../README.md) — 项目总览
- [QUICKSTART.md](../QUICKSTART.md) — 5 分钟上手
- [CHANGELOG.md](../CHANGELOG.md) — 全部版本变更
- [ROADMAP.md](../ROADMAP.md) — 未来计划
- [ARCHITECTURE.md](../ARCHITECTURE.md) — 架构
- [API.md](../API.md) — REST API
- [DEPLOYMENT.md](../DEPLOYMENT.md) — 部署
- [docs/CONSOLE_GUIDE.md](CONSOLE_GUIDE.md) — v9.1 Web Console
- [docs/SDK_CLI_GUIDE.md](SDK_CLI_GUIDE.md) — v9.0 Python SDK + CLI
