# Regional Economic Analysis

A multi-scenario analytics platform for **city comparison, retail site
selection, sales forecasting, and government industry-policy evaluation**
across 10 Chinese cities.

The question I built it to answer: *"Where should the next factory be
built? Which city grows fastest next year? Is this retail location
worth the rent?"*

---

## What it does

Four scenarios, one backend:

- **Retail site selection** — predict store revenue from foot-traffic,
  competitors, and rent.
- **Sales forecast** — **investment-grade**: 10 cities × 12 indicators × 16 years (2010-2025) of real public data + 4 macro covariates; 3-model ensemble (ARIMA + ETS + Linear Regression, AIC-weighted); 5 residual diagnostics (ADF / KPSS / Ljung-Box / Jarque-Bera / Breusch-Pagan); Chow test for structural breaks; walk-forward CV (5 metrics: MAPE / RMSE / MASE / sMAPE / Coverage); VaR / CVaR / GARCH(1,1) / volatility; 4 scenarios; 1000-iter Monte Carlo. See [docs/METHODOLOGY.md](docs/METHODOLOGY.md).
- **Enterprise environment** — rank cities by operating cost, supply
  chain, and policy support.
- **Government policy** — industrial chain completeness, fiscal leverage
  efficiency, GDP 5-year projection with confidence intervals.

REST API (FastAPI) + single-page web UI (no build step, vanilla
HTML + Tailwind CDN + ECharts).

---

## Quick start

```bash
pip install -r requirements.txt
python main.py --mode example     # generate data → train → predict → report
```

Or run the full stack:

```bash
# terminal 1 — API
uvicorn backend.api.main:app --reload --port 8000

# terminal 2 — frontend
cd frontend && python3 -m http.server 8080
# open http://localhost:8080/index.html             # standard dashboard
# open http://localhost:8080/investment_grade.html  # investment-grade analytics
# open http://localhost:8080/province_forecast.html # province-level forecast
```

Docker:

```bash
docker-compose up --build
```

### Python SDK & CLI (v9.0+)

```bash
pip install -e .              # 装 rca 包 + CLI entry point
rca --format rich forecast --city shenzhen --indicator gdp --years 5
```

```python
import rca
print(rca.__version__)  # '9.0.0'

# 9 个 tool 完全本地 — 0 LLM 调用、0 费用
fc = rca.forecast(scope="city", name="shenzhen", indicator="gdp", years=5)
print(fc["data"]["ensemble"]["predictions"])

# 跑 LLM agent
result = rca.chat(session_id="u1", user_message="深圳 GDP 走势如何?")
print(result["content"])
```

完整文档:[docs/SDK_CLI_GUIDE.md](docs/SDK_CLI_GUIDE.md)(11 CLI 子命令 · 3 输出格式 · 错误处理 · 退出码 · SDK vs CLI 选择)。

### Web Console (v9.1+)

后端跑起来后,直接浏览器打开 `http://localhost:8000/console/` — 零代码、零安装的管理界面:

- 9 项 tool 可视化(ensemble 折线 / 95% CI 区间带 / 残差诊断 bar / VaR-CVaR 双图 / 4 档情景对比 / P5-P50-P95 扇形 / 数据血缘树 / 宏观 sparkline / 城市网格)
- LLM Agent 流式 chat(SSE,打字机渲染)
- 在线改 LLM 配置(model / base_url / temperature / max_tokens / max_tool_rounds / timeout)
- 历史记录(1000 条 ring buffer + tool 过滤 + 清空)

完整文档:[docs/CONSOLE_GUIDE.md](docs/CONSOLE_GUIDE.md)(启动 / 13 页导览 / 9 tool 输入输出 / 设计语言 / API 表含字段约束 / 故障排查)。

### Investment-grade (Docker with full engine stack)

```bash
docker-compose up --build

# 探测已装引擎
curl -s http://localhost:8000/health | jq '.engine_stack'
# 期望: {"statsforecast": true, "arch": true, "pmdarima": true, "prophet": false}

# 投资级 dashboard
open http://localhost:8080/investment_grade.html
```

- **沙箱 / 本地无 Docker**: 仍能跑投资级流水线,ARIMA 走 `statsmodels` grid、GARCH 走滚动 std(API 响应 `"backend": "statsmodels"` / `"backend": "rolling-std"`)。
- **Docker 装上后**: ARIMA 走 `statsforecast.AutoARIMA` (max_p/q=5),波动率走 `arch` GARCH(1,1) + 持续性 + 半衰期。MAPE 改善 10-30%。
- **库探测模块**: `backend.core.engine_stack` — 启动时跑一次,失败降级,绝不抛异常。
- **方法学**: 见 [docs/METHODOLOGY.md](docs/METHODOLOGY.md) §10。

---

## Architecture

```
Web UI (8080)  ──fetch──▶  FastAPI (8000)  ──▶  Analyzers  ──▶  Data
                              │                              │
                              └──── /docs  Swagger ──────────┘
```

The web UI is intentionally build-free: it pulls Tailwind and ECharts
from a CDN, so anyone can open `index.html` in a browser and it works.
I got tired of clones that needed `npm install` to render a placeholder.

For the long version, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Project layout

```
backend/
  api/          FastAPI routes + main app
  ai/           LLM chat assistant (v7.0): config / llm_client / tool_registry / tool_executor / chat_service
  analysis/     analyzers (enterprise / government / dimension / custom)
  core/         config, data manager, multi-city, caching, tasks
  data/         static city dataset (10 cities, 20+ indicators)
  data_collection/  akshare / NBS / finance / industry collectors
  data_processing/  cleaner / transformer / validator
  ml/           model registry, trainer
  models/       Pydantic schemas
  retail_location/  retail scenario
  sales_forecast/   sales scenario
  utils/        safe model loader, report generator, visualizer
config/         industry / region templates
data/cities/    city dataset (YAML, regenerable)
examples/       runnable scenario demos
frontend/       single-file SPA + chat_widget.{html,js,css}
models/         bundled pickled estimators + SHA-256 manifest
tests/backend/  pytest unit tests
tests/fuzz/     hypothesis property-based fuzz
scripts/        dev utilities + legacy demos
```

### AI Chat Assistant (v7.0+)

```bash
# 配置 LLM(任选一种)
export LLM_OPENAI_API_KEY=sk-...  # OpenAI
# 或 export LLM_OLLAMA_BASE_URL=http://localhost:11434  # 本地 Ollama
# 或 阿里百炼 (OpenAI 兼容):
# export LLM_OPENAI_API_KEY=sk-... LLM_OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1 LLM_OPENAI_MODEL=qwen-turbo

# 启服务
docker compose up --build

# 测试
curl -s http://localhost:8000/api/v1/ai/config | jq
# 打开 demo 页面
open http://localhost:8000/chat_widget/chat_widget.html
```

#### v7.1 新增:Tool-chip 联动
LLM 调 tool 后,聊天流里会显示一个"📊 在图表中查看"蓝色 chip。点击:
- 新窗口打开 `investment_grade.html`(forecast/risk/scenarios/mc/backtest/diagnostics)
- URL 参数已 prefilled(scope, name, indicator, years, tab)
- 保留 chat 不动

后端透传 `type=tool_call` SSE 事件 + `navigate_to` URL;前端 `appendToolChip(name, args, navigate_to)` 渲染可点击链接。

#### v8.0 新增:自研 agent 增强 + Eval 框架

4 个独立可组合模块,自研不引入 LangGraph/Pydantic AI:

| 模块 | 文件 | 功能 |
|------|------|------|
| **Trace** | `backend/ai/trace.py` | `Step` + `TraceStore` 记录每次 LLM/tool/retry,出现在 SSE `done` 事件的 `trace` 字段 |
| **Fallback** | `backend/ai/fallback.py` | `run_with_fallback(base_cfg, ...)` 5 个百炼模型自动降级,401/403/404 立即抛,超时/429 降级 |
| **Parallel tools** | `backend/ai/parallel_tools.py` | `ThreadPoolExecutor` + 异常隔离 + 单 tool 超时 |
| **Retry** | `backend/ai/retry.py` | `should_retry()` 7 类白名单(city_not_found / data_unavailable / ...),`build_retry_hint()` 构造反射 prompt |

**关键设计**:`run_with_fallback(base_cfg, ...)` 必填 `base_cfg`,内部不再 `load_config()` — 完全解耦 env vars,支持多租户 / 隔离环境跑 eval。

SSE 事件链:
```
thinking → tool_call → token → done
                  └─ error(失败时)
```

每个 `done` 事件含 `trace: [...]` — 完整审计。

**Eval 框架** — 真 LLM 跑分,10 个真实业务 query:
```bash
# 单模型
export LLM_OPENAI_API_KEY=sk-... LLM_OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
python -m tests.eval.run_eval --model qwen-max

# 多模型对比
python -m tests.eval.run_eval --compare qwen-max deepseek-v3

# 跑指定 case
python -m tests.eval.run_eval --model qwen-max --ids shenzhen-gdp-forecast-3y
```

报表含 6 维度评分(tool / args / keywords / latency / fallback / tokens) + case 级别对比 + 胜出栏。

模型注册表: [docs/AI_MODEL_REGISTRY.md](docs/AI_MODEL_REGISTRY.md)(25 个百炼全功能模型 + fallback 链选择)

---

## Tests

```bash
pytest tests/backend/ -v        # backend unit + security regression
pytest tests/fuzz/ -v            # hypothesis property-based fuzz
python scripts/diagnostics/full_diagnose.py   # end-to-end smoke test
python scripts/diagnostics/browser_test.py    # browser screenshots
```

---

## Security

Copy `.env.example` to `.env`, set `SECRET_KEY` and `CORS_ORIGINS`, and
generate new `models/SHA256SUMS` when shipping new pickle files (the
loader refuses anything not on the manifest).

Pinned CI / Dependabot / CodeQL / Scorecard / Sigstore + SLSA L3
provenance on release. See [SECURITY.md](SECURITY.md).

---

## License

GPL-3.0-or-later — see [LICENSE](LICENSE).
