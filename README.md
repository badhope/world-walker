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
