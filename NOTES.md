# Notes

A few things I want to remember for next time, or explain to whoever
reads this repo. Not exhaustive.

## 2026-06-04 — v6.1.0 Docker 投资级引擎栈

### 关键决策
- **代码改成动态 import + 探测**: `engine_stack.py` 运行时检测 4 个可选库(statsforecast / arch / pmdarima / prophet),`auto_arima_native` 走 `statsforecast > pmdarima > statsmodels` 优先级,`garch_volatility` 走 `arch` 失败 fallback 到 rolling std。**所有改动向后兼容**,sandbox 仍能跑。
- **Dockerfile 加 `build-essential` + `gfortran`**: pmdarima / arch 编译依赖。
- **版本锁定**: `statsforecast>=1.5,<3.0`(支持 numpy 2.x) / `arch>=7.0,<8.0` / `pmdarima>=2.0,<3.0`(支持 Python 3.11)。

### 实施细节
- `arima_forecast` 按 backend 分支处理 predict:
  - statsforecast: 重新 fit 单 series + `predict(h=years)`,CI 用 in-sample 残差 std + z 估计(statsforecast 自带的 `prediction_intervals` 形参对单 series 不稳定)
  - pmdarima: `predict(n_periods, return_conf_int=True, alpha=1-confidence)`
  - statsmodels: `get_forecast(steps=years).conf_int()`
- 所有返回 dict 加 `"backend"` 字段,前端可显示当前引擎。
- `risk_full_pipeline` 输出加 `garch` + `engine_stack: {arch: bool}` 字段。
- `arima_forecast` 的 `auto_arima_native` 包装了所有逻辑,`auto_arima` 函数保持 statsmodels-only,作为底层 fallback。

### 验证
- 273 后端测试通过(原 263 + 10 新 engine_stack),ruff 新代码 clean。
- sandbox 探测:`{'statsforecast': False, 'arch': False, 'pmdarima': False, 'prophet': False}` → 全部走 fallback,流水线结果与之前完全一致。
- Docker 验证待用户在自有环境跑 `docker compose up --build`。

### 已知问题
- 实际上 sandbox 测得沙箱里 pandas/numpy 装得是 2.x(从 forecast_engine imports 看),但 `arch` 装不上确实是因为 C 编译依赖。
- pmdarima 装不上是 pypi 源里没 aarch64 + numpy 2.x 的 wheel,只能靠 Docker 编译。

### Files changed (this batch)
- NEW: `backend/core/engine_stack.py` (89 行)
- NEW: `tests/backend/test_engine_stack.py` (200+ 行,10 测试)
- MODIFY: `backend/core/forecast_engine.py` (+120 行 `auto_arima_native` + arima_forecast 改写)
- MODIFY: `backend/core/risk_engine.py` (+100 行 `garch_volatility` + import + risk_full_pipeline)
- MODIFY: `Dockerfile` (+4 行 build-essential/gfortran + 显式升级 pip)
- MODIFY: `requirements.txt` (+8 行 3 个新库锁版本)
- MODIFY: `docs/METHODOLOGY.md` (§2.1 / §6.2.1 / §7 / §10)
- MODIFY: `README.md` (Quick start + Investment-grade 段)

---

## 2026-06-04 — v6.0.0 投资决策级平台

### 关键决策
- 1920 数据点(10 城 × 12 指标 × 16 年)+ 64 宏观数据点(4 协变量 16 年)。
- 3 模型集成(ARIMA 30% + ETS 35% + LR 35%,AIC-weighted)。
- 5 项残差诊断 + 5 项 walk-forward CV + VaR/CVaR + 4 档情景 + 1000-iter MC。
- 7 个投资端点(`/api/v1/investment/*`)+ 5 个血缘端点(`/api/v1/lineage/*`)。
- 数据血缘:每条数据带 source URL + estimated + confidence + methodology_change。

### 实施细节
- `forecast_full_pipeline()` 主入口 → 串接 auto_arima / ets / lr → ensemble → diagnostics → backtest
- `risk_full_pipeline()` 主入口 → 串接 vol / VaR / CVaR / scenarios / MC
- `_get_scope_timeseries()` 在 investment.py 中处理 province 聚合:绝对量 sum、率按人口加权(广东 GDP 2026 = 74,402 = 深圳+广州+... 真实和)
- `/data/{id}` 路由冲突 → `data_lineage.py` 改前缀为 `/lineage`
- numpy.bool PydanticSerializationError → `t[key] = bool(t[key])` 转换

### 验证
- 263 后端测试通过(原 253 + 10 新 investment/lineage 集成)
- 深圳 GDP 16 年实测 MAPE 0.40% / MASE 0.07 / Coverage 100%

---

## 2026-05-25 — v4.0.0 多场景分析平台

- 4 个分析场景(企业 / 零售 / 销售 / 政府)
- 70+ REST API 端点
- 零构建 web UI(HTML + Tailwind CDN + ECharts CDN)
- 完整开源合规(LICENSE / CONTRIBUTING / CODE_OF_CONDUCT / SECURITY 等)
- 159 后端测试通过

---

## 2026-05-20 — Initial release

- 10 城基础数据集
- 4 项核心分析
- 基础 API + UI
- Docker 部署

## Why a single-page HTML frontend, not React/Vue

I started with a Vue 3 + Vite SPA and then deleted it. The problem was
that every reviewer who cloned the repo had to `npm install` 600 MB of
node_modules to see a placeholder page. Switching to one `index.html`
that pulls Tailwind and ECharts from a CDN means:

- clone → open `index.html` → it works
- no build step, no `package.json`, no `node_modules` in the diff
- the same file works behind nginx, `http.server`, or a tunnel

The trade-off is no real bundling, no component system, and a longer
first paint on cold cache. That's the right trade for a demo project.

## Why I bundled pickled estimators with a SHA-256 manifest

The `models/*.pkl` files are loaded with `backend/utils/safe_model_loader.py`,
which refuses anything whose hash isn't in `models/SHA256SUMS`. Pickle
deserialisation is a known RCE surface, so a manifest is the simplest
defence that still lets me ship a model with the repo. See
`tests/backend/test_safe_model_loader.py` for the test cases.

If I were deploying this for real I'd retrain on the live data and
ship the training code + the model registry, not the pickle.

## City data is YAML now

It used to live in a 569-line hardcoded dict in `backend/data/city_data.py`,
which made adding a city a Python change. Moving it to
`data/cities/cities.yaml` and adding `scripts/regen_cities_yaml.py` means
adding a city is a one-file PR. The Python module re-exports the YAML
on import, so the API surface didn't change.

## Why `python-jose` is gone

Unmaintained for a while, has open CVEs against the `cryptography`
backend. Switched to `PyJWT[crypto]` and the auth route compares
credentials with `hmac.compare_digest` to close the timing-attack
window on the constant string compare.

## CORS

The defaults in `.env.example` cover local dev (`localhost:8000/8080`,
`127.0.0.1:8000/8080`, and the legacy `5173` port). For prod, set
`CORS_ORIGINS` to your real origin and **don't** include `*` if you
also need credentials — the middleware will refuse it.

## The `docs/archive/` directory

There used to be 22 files in there (PROJECT_SUMMARY, FINAL_SUMMARY,
RESUME_PROJECT, etc.) — they were self-written project summaries that
just added noise. They're gone. The README and CHANGELOG are the only
project history that matters.

## Things I'd do next

- Replace the static city dataset with live ingestion from NBS / Wind /
  akshare; the collectors are stubbed in `backend/data_collection/`.
- Move the model training pipeline out of the API process and into a
  proper job queue (the WebSocket route already has a hook for this).
- Wire up a real CI cache for `pip` so we don't re-download the
  world on every PR.
