# Regional Economic Analysis Agent — Web Console Guide (v9.1)

> **Status**: stable · v9.1.0
> **Audience**: 数据分析师、产品经理、运营、PM、临时想做一次分析但不想写代码的人
>
> 在 v9.1 之前,使用 RCA Agent 只能通过 Python SDK 或 CLI(见 [SDK_CLI_GUIDE.md](SDK_CLI_GUIDE.md))。
> v9.1 起,新增了 **Web Console** — 一个零代码、零安装的浏览器管理界面,让任何人都能直接跑 9 项分析工具、查看历史、配置 LLM、和 LLM Agent 流式对话。

---

## 1. 概览

### 1.1 它是什么

RCA Web Console 是挂在 FastAPI 后端的一个静态 SPA(vanilla JS + ECharts)。它**不实现任何分析逻辑** — 所有计算都在后端跑,Console 只是 UI。

```
浏览器 ──HTTP──> FastAPI ──> backend.ai.tool_executor ──> 9 项工具
   ↑                │
   │                ├──> /api/v1/admin/chat         (LLM Agent SSE)
   │                ├──> /api/v1/admin/config       (PUT 改 model/temp/...)
   │                └──> /api/v1/admin/history      (1000 条 ring buffer)
   └──<── 静态资源 /console/index.html ──┘
```

### 1.2 它不是什么

- **不是**独立的网站(必须先跑后端,再访问 `/console`)
- **不是** GitHub Pages 展示站(那是 v9.1 Phase 3,单独的展示用途)
- **不**存任何数据到数据库(所有 history/config 都在内存,重启后端就清空)
- **不**需要登录认证(假定你在 trusted 私有部署跑)

### 1.3 适合谁

- 想试试 RCA Agent 但不想 `pip install` 的产品/运营同学
- 需要点几下就出图表、不想写 Python 的分析师
- 想看 LLM 实时在调什么 tool、想看历史调用、想调 model 的人
- 给老板/客户演示时用浏览器开一个窗口就够的场景

---

## 2. 启动

### 2.1 后端必须先跑

Web Console 只是后端的一个静态资源挂载点,所有功能都依赖后端的 8 个 `/api/v1/admin/*` endpoint + 9 个 tool。

```bash
# 1. 装好 Python 依赖
pip install -e .

# 2. 配置 LLM 凭据(任选一个后端)
export LLM_OPENAI_API_KEY=sk-...            # OpenAI
# 或者
export LLM_OLLAMA_BASE_URL=http://localhost:11434  # Ollama(本地免费)

# 3. 启动 FastAPI
python -m uvicorn backend.api.main:app --port 8000
```

看到 `Application startup complete` 后,后端就绪。

### 2.2 访问 Console

打开浏览器:
- **本地**: <http://localhost:8000/console/>
- **远程**: `https://<your-host>/console/`

会自动跳到 `index.html`(Dashboard 页)。

---

## 3. 页面导览

### 3.1 Dashboard (`/`)

入口页,3 块内容:

- **System Status** — 当前 LLM 配置(6 项 metrics,model / active_backend / fallback chain / temperature / max_tokens / max_tool_rounds)
- **Tools · 9 项分析工具** — 9 张卡片网格,点击跳到对应 tool 页
- **Recent History · 最近 5 条** — 任何人刚跑的 tool 都会在这里出现

### 3.2 9 个 Tool 页 (`/tool/<name>.html`)

每个 tool 一个独立页,统一结构:

```
┌────────────────────────────────────────────┐
│ Header: 中英标题 + 一句话说明                │
├────────────────────────────────────────────┤
│ Form: scope / name / indicator / years     │
│   (部分 tool 无 years,部分无 indicator)     │
├────────────────────────────────────────────┤
│ [Run · xxx]  按钮                           │
├────────────────────────────────────────────┤
│ Result 区(运行后才显示):                    │
│   - 主图(折线 / bar / 扇形 / sparkline)     │
│   - 关键指标卡(2-5 个)                       │
│   - 详细表(可点击展开 Raw JSON)             │
└────────────────────────────────────────────┘
```

#### 各 tool 一览

| # | 路径 | 中文 | 主要图表 | 输入参数 | 关键输出 |
|---|------|------|----------|----------|----------|
| 1 | `forecast.html` | 预测 | ensemble 折线 + 95% CI 区间带 | scope/name/indicator/years | data_points / MAPE / 末年值 |
| 2 | `diagnostics.html` | 残差诊断 | 5 项 bar | scope/name/indicator | verdict (PASS/WARN/FAIL) + 5 项 p-value |
| 3 | `backtest.html` | 回测 | 实际 vs 预测双线 | scope/name/indicator | MAPE/RMSE/MASE/sMAPE/Coverage |
| 4 | `risk.html` | 风险 | VaR/CVaR 4 bar | scope/name/indicator | VaR_95/VaR_99/CVaR_95/CVaR_99 + GARCH |
| 5 | `scenarios.html` | 情景 | 4 档折线对比 | scope/name/indicator/years | baseline/optimistic/pessimistic/recession 末年值 |
| 6 | `monte-carlo.html` | 蒙特卡洛 | P5/P50/P95 扇形带 | scope/name/indicator/years | 500 次模拟分位数 + 区间宽 |
| 7 | `data-provenance.html` | 数据血缘 | 树形 HTML | name | URL/NBSC 源/置信度/估算标记 |
| 8 | `macro-data.html` | 宏观协变量 | 4 sparkline | (无) | national_gdp/cpi_yoy/lpr_1y/fdi_inflow 当前 + 同比 |
| 9 | `list-cities.html` | 城市列表 | 卡片网格 | (无) | 支持的城市/省份/指标 + 过滤搜索 |

### 3.3 Chat 页 (`/chat.html`)

LLM Agent 流式对话界面。

- 左侧消息列(你的 + AI 交替)
- 底部输入框,Submit 后 SSE 流式渲染 AI 思考过程
- session_id 每次刷新随机生成(`console-xxxxxx`),后端按 session 保留上下文
- **Sync 按钮**:不开 SSE,直接等 AI 完整回答

不依赖 Ollama / 任何特定 LLM — 用后端当前配置(`/admin/config` 里看到的那个)。

### 3.4 Settings 页 (`/settings.html`)

可视化改 LLM 配置 — 表单 GET / PUT `/api/v1/admin/config`。

可改字段:
- `model`(e.g. `gpt-4o-mini` / `qwen-max`)
- `base_url`(e.g. `https://api.openai.com/v1` / `http://localhost:11434/v1`)
- `temperature`(0 ~ 2)
- `max_tokens`(64 ~ 32000)
- `max_tool_rounds`(1 ~ 20)
- `timeout_sec`(5 ~ 600)

**改动立即生效**,但存在后端内存,重启后端就回到 env var 默认值。

### 3.5 History 页 (`/history.html`)

最近 200 条 query(后端实际是 1000 条 ring buffer,Console 默认只拉 200 条避免太慢)。

每条显示:
- 时间 / tool 名 / 耗时 / id
- 入参(`{"scope": "city", ...}`)
- 结果摘要(forecast 显示 pred_first/pred_last/verdict,backtest 显示 mape/rmse,...)
- status badge(ok / err)+ 错误信息

支持:
- 按 tool 过滤(下拉)
- Reload
- Clear(确认后清空所有)

---

## 4. 设计语言

Web Console 严格继承 `frontend/index.html` 的 design tokens:

- **配色**:深墨蓝 `#0E1F3F` + 暖铜 `#D08560` + 纸感 `#FAF8F3`
- **字体**:标题 Fraunces / 正文 Geist / 数据 JetBrains Mono
- **侧栏**:240px 深底,主区白底
- **圆角**:6/10/16px 三档
- **阴影**:1/4/12px 三档
- **Verdict badge 配色**:PASS→绿 / WARN→黄 / FAIL→红 / INFO→深蓝

`css/console.css` 顶部把所有 design token 暴露成 CSS 变量(`--ink-900` / `--copper-500` / `--font-display` 等),要改色直接改一个变量就生效。

---

## 5. API(给自定义前端用)

如果你不想用 Console 的 UI 想自己写,所有数据来源都是这几个 endpoint。完整 schema 见后端 `/docs` Swagger。

| Endpoint | Method | 用途 |
|----------|--------|------|
| `/api/v1/admin/tools` | GET | 9 个 tool 的 metadata(name/params/description) |
| `/api/v1/admin/tools/{name}/run` | POST | 跑一个 tool,body 是 tool 参数 |
| `/api/v1/admin/history` | GET | 历史(可 `?tool=` `?limit=`) |
| `/api/v1/admin/history/{id}` | GET | 单条详情 |
| `/api/v1/admin/history` | DELETE | 清空 |
| `/api/v1/admin/config` | GET | 当前 LLM 配置 |
| `/api/v1/admin/config` | PUT | 改 LLM 配置 |
| `/api/v1/admin/chat` | POST | 同步 chat |
| `/api/v1/admin/chat/stream` | GET | SSE 流式 chat(`?session_id=` `?message=`) |

### 5.1 tool 输出形状(已知 backtest / diagnostics / monte carlo 的字段约定)

| Tool | 关键字段 |
|------|----------|
| `get_forecast` | `data.ensemble.{predictions, lower_ci, upper_ci}`,`data.diagnostics_verdict`,`data.backtest_mape` |
| `get_diagnostics` | `data.tests`(**dict,不是 array** — key 是 adf/kpss/ljung_box/jarque_bera/breusch_pagan),`data.verdict`,`data.verdict_reason` |
| `get_backtest` | `data.actuals[]`,`data.forecasts[]`,`data.metrics.{MAPE_pct, RMSE, MASE, sMAPE_pct, Coverage_pct}`(注意大写+后缀) |
| `get_risk` | `data.var_95.{var_pct, var_amount}`,`data.var_99`,`data.volatility`,`data.garch` |
| `get_scenarios` | `data.scenarios`(**dict** — key 是 baseline/optimistic/pessimistic/recession,每个有 `predictions[]`) |
| `get_monte_carlo` | `data.quantiles.{p05, p50, p95}`(**注意是 p05 不是 p5**),`data.years[]`,`data.n_sims` |
| `get_data_provenance` | `data.{city, url, nbsc_url, year_range, n_years, coverage, sample_provenance}` |
| `get_macro_data` | `data.{year, current: {national_gdp/cpi_yoy/lpr_1y/fdi_inflow}, yoy_pct}` |
| `get_list_cities` | `data.{cities[], city_pinyin{zh: en}, cities_pinyin[], provinces[], n_cities}` |

---

## 6. 故障排查

### 6.1 Console 打开空白 / JS 报错

打开浏览器 DevTools Console,看具体错:
- `Failed to fetch` → 后端没跑 / 端口错 / CORS 没放
- `404 on /api/v1/admin/tools` → 后端版本太老(< v9.1)
- ECharts 报错 → CDN 拉不到(检查网络)

### 6.2 Tool 跑出 "insufficient data"

数据不够(< 5 / < 8 / < 16 年)。Console 没法改,只能:
- 换城市(深圳/北京/上海/广州/成都/杭州/南京/武汉 都有 16 年数据)
- 换 indicator(默认 4 个都有)

### 6.3 Tool 跑出 "Unknown tool: xxx"

`/admin/tools/{name}/run` 里的 `name` 拼错了。参考 `GET /api/v1/admin/tools` 拿正确列表。

### 6.4 Chat 一直转圈

`/admin/chat/stream` 没返回。看后端日志:
- `LLMUnavailableError` → 当前配置的 LLM 不可达
- `ConfigError: No LLM backend available` → 没设任何 LLM 凭据,见 §2.1
- `tool argument error` → LLM 想调 tool 但参数不对(这个是 LLM 自己的事,Console 没法控制)

### 6.5 Settings 改了不生效

- 检查是否点击了 "Save · 保存" 按钮(只是改 input 不会触发 PUT)
- 改完可以去 Chat 页发一条消息验证
- 后端重启后会回到 env var 默认

---

## 7. 部署到生产

Console 是纯静态文件,部署只关心:
1. 后端在 trusted 私有网络跑
2. 反代(nginx)CORS 放行(见 `backend/api/main.py` CORS 中间件)
3. 不要把 `/admin/*` 暴露到公网(它没有认证)

如果要给非技术用户用,推荐在 nginx 层做个 simple basic auth 套 `/console/` 路径。

---

## 8. 相关

- [SDK_CLI_GUIDE.md](SDK_CLI_GUIDE.md) — Python SDK + CLI 完整文档(v9.0)
- [API.md](../API.md) — 完整 REST API 文档(>= 50 个 endpoint)
- [ARCHITECTURE.md](../ARCHITECTURE.md) — 系统架构
- `docs/superpowers/specs/2026-06-05-v91-web-console-design.md` — 本次设计 spec
- `docs/superpowers/plans/2026-06-05-v91-web-console.md` — 26 task 实施计划
