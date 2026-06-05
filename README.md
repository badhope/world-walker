# Regional Economic Analysis Agent

> **v9.1** — multi-scenario analytics + self-developed LLM agent + 3 entry points
> (Web Dashboard / Python SDK / CLI / **Web Console v9.1**)

A multi-scenario analytics platform for **city comparison, retail site
selection, sales forecasting, and government industry-policy evaluation**
across 10 Chinese cities.

The question I built it to answer:
*"Where should the next factory be built? Which city grows fastest next year?
Is this retail location worth the rent?"*

---

## What it does

Four scenarios, one backend:

- **Retail site selection** — predict store revenue from foot-traffic, competitors, and rent.
- **Sales forecast** — **investment-grade**: 10 cities × 12 indicators × 16 years (2010-2025) of real public data + 4 macro covariates; 3-model ensemble (ARIMA + ETS + Linear Regression, AIC-weighted); 5 residual diagnostics (ADF / KPSS / Ljung-Box / Jarque-Bera / Breusch-Pagan); Chow test for structural breaks; walk-forward CV (5 metrics: MAPE / RMSE / MASE / sMAPE / Coverage); VaR / CVaR / GARCH(1,1) / volatility; 4 scenarios; 1000-iter Monte Carlo. See [docs/METHODOLOGY.md](docs/METHODOLOGY.md).
- **Enterprise environment** — rank cities by operating cost, supply chain, and policy support.
- **Government policy** — industrial chain completeness, fiscal leverage efficiency, GDP 5-year projection with confidence intervals.

LLM Agent (v7.0+ — **self-developed**, no LangGraph / Pydantic AI) — Trace + Fallback(5 models) + Parallel tools + Retry hint reflection; SSE streaming chat with `tool_call → token → done` event chain and full audit trace.

---

## Quick start

### 0 · Install + LLM key (one time)

```bash
pip install -e .                    # 装 rca 包 + rca CLI entry point
cp .env.example .env
# 至少配一种 LLM:
echo "LLM_OPENAI_API_KEY=sk-..." >> .env                              # OpenAI
# 或
echo "LLM_OLLAMA_BASE_URL=http://localhost:11434" >> .env              # 本地 Ollama
echo "LLM_ACTIVE_BACKEND=ollama LLM_DEFAULT_BACKEND=ollama" >> .env
```

### 1 · Start backend

```bash
python -m uvicorn backend.api.main:app --port 8000
# 看到 "Application startup complete" 即就绪
```

### 2 · Pick an entry point

| 入口 | 适用 | 命令 / 访问 |
|------|------|-------------|
| **Web Dashboard** | 看投资级图表(forecast / risk / scenarios / mc / backtest / diagnostics),只读 | 浏览器: <http://localhost:8000/> (或 `frontend/index.html`) |
| **Web Console** ⭐ v9.1 | 零代码跑 9 tool + LLM chat + 改配置 + 看历史 | 浏览器: <http://localhost:8000/console/> |
| **Python SDK** v9.0 | 写代码 / 集成到自己的 pipeline | `import rca; rca.forecast(...)` |
| **CLI** v9.0 | shell 一行 / cron / 脚本 | `rca forecast --city shenzhen --indicator gdp --years 5` |

> 4 个入口数据完全共享(都打后端),功能 100% 覆盖。Web Dashboard 重展示 / Console 重管理 / SDK+CLI 重集成。

### 3 · Verify it works

```bash
# Python SDK
python -c "import rca; print(rca.forecast(scope='city', name='shenzhen', indicator='gdp', years=3)['data']['ensemble']['predictions'])"
# → [45123.5, 47890.1, 50789.2] 之类的 3 个值

# CLI
rca list-cities --format plain

# HTTP API
curl -s http://localhost:8000/api/v1/admin/tools | python -m json.tool | head -10
```

---

## v9.1 · Web Console

> Zero-code, zero-install browser UI — 挂在 FastAPI 后端的 `/console/` 路径。

**9 项 tool 可视化** + **LLM Agent 流式 chat** + **配置页** + **历史记录**:
- 9 tool 独立页:forecast(ensemble + 95% CI)/ diagnostics(5 项 bar)/ backtest(双线 + 5 指标卡)/ risk(VaR/CVaR)/ scenarios(4 档对比)/ monte-carlo(P5-P50-P95 扇形)/ data-provenance(树形 HTML)/ macro-data(4 sparkline)/ list-cities
- LLM 流式 chat(SSE,支持 `thinking` / `token` / `tool_call` / `tool_result` / `final` / `error` 6 种 event)
- 在线改 LLM 配置(model / base_url / temperature / max_tokens / max_tool_rounds / timeout)— 立即生效
- 历史 1000 条 ring buffer + 按 tool 过滤 + 清空

**完整文档**:
- 用户指南: [docs/CONSOLE_GUIDE.md](docs/CONSOLE_GUIDE.md)(启动 / 13 页导览 / 9 tool 输入输出 / 设计语言 / API 表 / 故障排查)
- 设计 spec: [docs/superpowers/specs/2026-06-05-v91-web-console-design.md](docs/superpowers/specs/2026-06-05-v91-web-console-design.md)
- 实施计划: [docs/superpowers/plans/2026-06-05-v91-web-console.md](docs/superpowers/plans/2026-06-05-v91-web-console.md)

**后端 API**(给自定义前端用):

| Endpoint | Method | 用途 |
|----------|--------|------|
| `/api/v1/admin/tools` | GET | 9 个 tool 的 metadata |
| `/api/v1/admin/tools/{name}/run` | POST | 跑一个 tool |
| `/api/v1/admin/history` | GET / DELETE | 1000 条 ring buffer |
| `/api/v1/admin/history/{id}` | GET | 单条详情 |
| `/api/v1/admin/config` | GET / PUT | LLM 配置 |
| `/api/v1/admin/chat` | POST | 同步 chat |
| `/api/v1/admin/chat/stream` | GET | **SSE** 流式 chat |

---

## v9.0 · Python SDK + CLI

### Python SDK

```python
import rca
print(rca.__version__)  # '9.0.0'

# 9 个 tool 完全本地 — 0 LLM 调用、0 费用
fc = rca.forecast(scope="city", name="shenzhen", indicator="gdp", years=5)
print(fc["data"]["ensemble"]["predictions"])

# 跑 LLM agent(自动 multi-round)
result = rca.chat(session_id="u1", user_message="深圳 GDP 走势如何?")
print(result["content"])

# 流式
for ev in rca.chat_stream(session_id="u1", user_message="..."):
    if ev["type"] == "token":
        print(ev["content"], end="", flush=True)

# 9 tool 全部能用
rca.diagnostics(scope="city", name="shenzhen", indicator="gdp")
rca.backtest(scope="city", name="shenzhen", indicator="gdp")
rca.risk(scope="city", name="shenzhen", indicator="gdp")
rca.scenarios(scope="city", name="shenzhen", indicator="gdp", years=5)
rca.monte_carlo(scope="city", name="shenzhen", indicator="gdp", years=5)
rca.data_provenance(name="shenzhen")
rca.macro_data()
rca.list_cities()
```

### CLI

```bash
rca --format rich forecast --city shenzhen --indicator gdp --years 5
rca --format plain risk --city shenzhen --indicator gdp
rca --format json monte-carlo --city shenzhen --indicator gdp --years 5
rca chat --session u1 --message "深圳 GDP 走势如何?"
rca chat-stream --session u1 --message "..." | head -50
rca config show
rca config set --model gpt-4o-mini --temperature 0.5
rca list-cities
```

**11 CLI 子命令** · **3 输出格式**(rich / plain / json) · **完整错误处理 + 退出码** · **`rca config` 在线改 LLM 配置**。

**完整文档**: [docs/SDK_CLI_GUIDE.md](docs/SDK_CLI_GUIDE.md)(安装 / API 表 / 11 CLI 用法 / 3 输出格式 / 退出码 / 错误处理 / SDK vs CLI 何时用哪个 / FAQ)。

---

## v7.0+ · Self-developed LLM Agent

| 模块 | 文件 | 功能 |
|------|------|------|
| **Trace** | `backend/ai/trace.py` | `Step` + `TraceStore`,SSE `done` 事件含完整 `trace: [...]` |
| **Fallback** | `backend/ai/fallback.py` | 5 个百炼模型自动降级,401/403/404 立即抛,超时/429 降级 |
| **Parallel tools** | `backend/ai/parallel_tools.py` | `ThreadPoolExecutor` + 异常隔离 + 单 tool 超时 |
| **Retry** | `backend/ai/retry.py` | 7 类白名单(city_not_found / data_unavailable / ...)+ 反射 prompt |

**关键设计**:`run_with_fallback(base_cfg, ...)` 必填 `base_cfg`,**完全解耦 env vars**,支持多租户 / 隔离环境跑 eval。

SSE 事件链:
```
thinking → tool_call → token → done
                └─ error(失败时)
```

**Eval 框架** — 真 LLM 跑分,10 个真实业务 query:
```bash
export LLM_OPENAI_API_KEY=sk-... LLM_OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
python -m tests.eval.run_eval --model qwen-max
python -m tests.eval.run_eval --compare qwen-max deepseek-v3
```

模型注册表: [docs/AI_MODEL_REGISTRY.md](docs/AI_MODEL_REGISTRY.md)(25 个百炼全功能模型 + fallback 链选择)

---

## Investment-grade engine stack

| 引擎 | 装上 | 降级 |
|------|------|------|
| **ARIMA** | `statsforecast.AutoARIMA` (max_p/q=5) | `statsmodels` grid (ARIMA backend = `statsmodels`) |
| **GARCH** | `arch` GARCH(1,1) + 持续性 + 半衰期 | 滚动 std (volatility backend = `rolling-std`) |
| **Ensemble** | AIC-weighted | 同 |
| **Prophet** | `prophet` | 跳过(可选) |

`backend.core.engine_stack` 启动时探测一次,失败降级,**绝不抛异常**。沙箱/无 Docker 也能跑全流水线,响应里 `backend` 字段告诉你当前走的哪条路。

**方法学**: [docs/METHODOLOGY.md](docs/METHODOLOGY.md) §10。

---

## Architecture

```
                       ┌─────────────────────────────────────────────┐
                       │  FastAPI (single process, port 8000)        │
                       ├─────────────────────────────────────────────┤
                       │  /            Web Dashboard (index.html)   │
浏览器 ◀────HTTP──────▶│  /console/    Web Console v9.1 (13 页 SPA) │
                       │  /docs        Swagger                      │
                       │  /api/v1/...  50+ endpoint                 │
                       │    └ /admin/  8 admin endpoint v9.1        │
                       │    └ /ai/chat LLM Agent SSE                │
                       └────────────────┬────────────────────────────┘
                                        │
                       ┌────────────────▼────────────────────────────┐
                       │  backend.ai.tool_executor (9 tool + chat)   │
                       │  backend.ai.llm_client (litellm + fallback) │
                       └────────────────┬────────────────────────────┘
                                        │
                ┌───────────────────────┼──────────────────────┐
                ▼                       ▼                      ▼
        backend.core             backend.data            backend.retail
        (forecast/risk/MC)       (10 cities, 16y)        (store revenue)
```

Web UI 故意零 build step(CDN 拉 Tailwind + ECharts),`index.html` 直接打开能跑。Console 也一样 — 13 个静态 HTML + 3 JS helper + 1 CSS,无 npm / 无 webpack。

---

## Project layout

```
backend/
  api/          FastAPI routes + main app
    routes/
      admin.py          v9.1 Web Console 后端 8 endpoint
    admin_store.py      v9.1 HistoryStore + ConfigStore(线程安全)
  ai/           LLM chat assistant (v7.0): config / llm_client / tool_registry / tool_executor / chat_service
    trace.py / fallback.py / parallel_tools.py / retry.py   v8.0 自研
  analysis/     analyzers (enterprise / government / dimension / custom)
  core/         config, data manager, multi-city, caching, tasks, engine_stack
  data/         static city dataset (10 cities, 20+ indicators)
  data_collection/  akshare / NBS / finance / industry collectors
  data_processing/  cleaner / transformer / validator
  ml/           model registry, trainer
  models/       Pydantic schemas
  retail_location/  retail scenario
  sales_forecast/   sales scenario
  utils/        safe model loader, report generator, visualizer
cli/           v9.0 Typer CLI (11 子命令)
rca/           v9.0 Python SDK(完整 re-export 9 tool + chat + client)
config/        industry / region templates
data/cities/   city dataset (YAML, regenerable)
frontend/
  index.html           投资 dashboard
  console/             v9.1 Web Console
    index.html / chat.html / settings.html / history.html
    tool/              9 个 tool 独立页
    js/  api.js form-helpers.js chart.js sidebar.js
    css/ console.css
docs/
  CONSOLE_GUIDE.md     v9.1 Web Console 用户指南
  SDK_CLI_GUIDE.md     v9.0 Python SDK + CLI 用户指南
  METHODOLOGY.md       投资级方法学
  ARCHITECTURE.md
  AI_MODEL_REGISTRY.md 25 个百炼模型注册表
  superpowers/         v9.0 + v9.1 设计 spec + 实施计划
tests/
  backend/   pytest 单元测试 + 后端 + admin (v9.1)
  cli/       v9.0 CLI 18 测试
  api/       v9.0 + v9.1 API 24+12 测试
  rca/       v9.0 SDK 36 测试
  eval/      v8.0 真 LLM 跑分
  fuzz/      hypothesis property-based fuzz
scripts/     dev utilities + legacy demos
```

---

## Tests

```bash
# 单元测试(全 — 包含 v9.1 admin / v9.0 SDK CLI)
python -m pytest tests --continue-on-collection-errors -q
# 452 pass / 5 fail(全 pre-existing openpyxl 缺包) / 2 skip / 2 error(缺 matplotlib + hypothesis)

# 端到端 smoke
python scripts/diagnostics/full_diagnose.py
python scripts/diagnostics/browser_test.py   # browser screenshots
```

---

## Security

Copy `.env.example` to `.env`, set `SECRET_KEY` and `CORS_ORIGINS`, and
generate new `models/SHA256SUMS` when shipping new pickle files (the
loader refuses anything not on the manifest).

Pinned CI / Dependabot / CodeQL / Scorecard / Sigstore + SLSA L3
provenance on release. See [SECURITY.md](SECURITY.md).

Web Console (`/console/`) 假定 trusted 私有部署,**没有内置认证**。生产环境必须在 nginx 层套 basic auth 或反向代理加 SSO。

---

## License

GPL-3.0-or-later — see [LICENSE](LICENSE).
