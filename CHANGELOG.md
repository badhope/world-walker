# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/).
Versioning: [SemVer](https://semver.org/).

## 8.0.0 — 2026-06-05

### Added
- **自研 agent 增强** — 4 个独立可组合模块,不引入 LangGraph/Pydantic AI:
  - `backend/ai/trace.py` — `Step` + `TraceStore`(bounded deque),所有 LLM/tool/retry 步骤结构化记录
  - `backend/ai/fallback.py` — `ModelEntry` + `run_with_fallback()` 多模型降级链,错误分类(fatal vs retryable)
  - `backend/ai/parallel_tools.py` — `execute_tools_parallel()` 用 ThreadPoolExecutor,异常隔离 + 单 tool 超时
  - `backend/ai/retry.py` — `should_retry()` + `build_retry_hint()` 反射重试(白名单 7 类可重试错误)
- **AIConfig 新字段** — `fallback_chain: tuple[ModelEntry, ...]` + `tool_timeout_sec` + `parallel_max_workers`
- **`chat_stream_with_trace` 重构** — 组合 4 模块,事件链 `thinking → tool_call → token → done`(done/error 含 trace)
- **阿里百炼模型注册表** — `docs/AI_MODEL_REGISTRY.md`,含 25 个全功能模型 + 5 个 fallback 链
- **Eval 框架** — `tests/eval/` 子包,支持真 LLM 跑分:
  - `golden_cases.jsonl` — 10 个真实业务 query(覆盖 7 个投资类 + 3 个数据类 tool)
  - `scorer.py` — 6 维度评分(tool 30 + args 20 + keywords 20 + latency 15 + fallback 10 + tokens 5)
  - `reporter.py` — JSON + Markdown 报表,含 case 级别对比
  - `run_eval.py` — CLI(`--model` / `--compare` / `--ids`),无 API key 时给清晰错误并 exit 2
- **设计修复** — `run_with_fallback(base_cfg, ...)` 必填 base_cfg,**去掉内部 `load_config()`**(解耦 env vars,支持多租户/隔离环境)

### Changed
- `backend/ai/chat_service.py` — 4 模块组合 + 事件流 + 反射重试
- `backend/ai/config.py` — `AIConfig` 加 3 字段(frozen=True,tuple for fallback_chain)
- `backend/ai/llm_client.py` — 不变,但 env 双写(`LLM_OPENAI_API_KEY` + `OPENAI_API_KEY`)litellm 兼容

### Tests
- v8.0 新增 36 个测试:5 trace + 4 fallback + 4 parallel + 4 retry + 5 stream_v8 + 7 eval + 4 stream_trace(向后兼容)
- **总测试:113 pass / 2 skip**(v7.1 76 + v8.0 37)
- 真 LLM eval:`qwen-max` 80% pass(77.8 avg) / `deepseek-v3` 90% pass(74.4 avg),case 级别对比 + 胜出栏

## 7.1.0 — 2026-06-04

### Added
- **Tool-call UI 联动** — LLM 调 tool 后,前端 chat widget 渲染"📊 在图表中查看" chip,点击新窗口打开 `investment_grade.html` / `index.html` 并 prefilled URL 参数
- **SSE 新事件类型** `type=tool_call`(老 client 兼容,新 client 渲染 chip)
- **`/chat` 响应新增** `tool_calls` 字段(老 client 也能拿到导航 URL)
- **`tool_executor` 返回结构升级** — `{"data": ..., "navigate_to": <url|None>}`(v7.0 老内部 API 也兼容)
- **OpenAI 兼容 base_url 支持** — `LLM_OPENAI_BASE_URL` env var,让百炼 / 自建 gateway 走 OpenAI 客户端

### Changed
- `chat_service.chat_stream_with_trace()` — 新生成器模式 yield `{thinking, tool_call, token, done}` 事件
- `chat_service.chat()` — 累积 `tool_calls_log` 给响应
- `frontend/chat_widget.js` — `appendToolChip(name, args, navigate_to)` 改 `<a target=_blank>`
- `frontend/chat_widget.css` — 新增 `.rca-tool-chip` 样式(浅蓝 chip + hover)
- `routes/ai.py` `/chat/stream` — 改用 `chat_stream_with_trace` 拿事件流

### Tests
- 新增 11 个测试:`5 stream trace + 2 route + 4 widget chip`(10 navigate_to 在 v7.0 阶段)
- 总测试:**335 pass / 2 skip**

## 7.0.0 — 2026-06-04

### Added
- **AI 对话助手** — LiteLLM 统一 3 类 LLM backend(OpenAI/Claude/Ollama)
- **9 个 tool** — 7 投资(forecast/diagnostics/backtest/risk/scenarios/monte_carlo)+ 2 数据(provenance/macro/list_cities)
- **FastAPI 路由** — `/api/v1/ai/chat`, `/api/v1/ai/chat/stream`, `/api/v1/ai/tools`, `/api/v1/ai/config`
- **前端 chat widget** — 浮动按钮 + SSE 消费 + 打字机渲染
- **`backend/ai/` 模块** — 6 文件:config / llm_client / tool_registry / tool_executor / chat_service / conversation / prompts
- **双模式可切换** — 云端 API(开发)+ 本地 Ollama(隐私/生产)
- **短期对话历史** — 内存 dict,TTL 30 分钟
- **14 个新测试** — `tests/backend/test_ai_*.py`

### 不做
- 报告生成 / 投资建议 / RAG / Agent 协作 / 长期记忆(后续可加)

## 6.1.0 — 2026-06-04

### Added
- **Docker investment-grade engine stack** — `Dockerfile` 预装
  `statsforecast>=1.5`、`arch>=7.0`、`pmdarima>=2.0`(与 Python 3.11
  + numpy 2.x 兼容);`build-essential` + `gfortran` 编译依赖。
- **`backend/core/engine_stack.py`** — 运行时库探测模块
  (`statsforecast_available()` / `arch_available()` / `pmdarima_available()`
  / `prophet_available()` + `engine_stack()` 汇总 +
  `primary_arima_backend()` / `primary_vol_backend()` 优先级选择)。
  启动时探测一次,失败返回 False 不抛异常。
- **`arima_forecast` AutoARIMA 路径** — `auto_arima_native()` 走
  statsforecast > pmdarima > statsmodels 优先级,sandbox 装不上时
  自动 fallback 到现有 statsmodels grid search。
- **GARCH(1,1) 路径** — `garch_volatility()` 用 `arch` 库,输出
  conditional_vol_pct / persistence / half_life_years / alpha / beta;
  arch 未装时降级为 rolling std + 历史 VaR。
- **`engine_stack.py` 探测测试** (`tests/backend/test_engine_stack.py`,
  10 个新测试) — 覆盖:探测函数永不抛异常、缓存稳定、sandbox
  fallback 路径、schema 不变、向后兼容。
- **`docs/METHODOLOGY.md` §10** — Docker 部署与引擎探测章节
  (镜像能力、运行时探测、fallback 矩阵、验证步骤)。
- **`docs/superpowers/plans/2026-06-05-docker-investment-grade-libraries.md`**
  — 8 个 task 的升级实施计划。

### Changed
- `forecast_engine.arima_forecast` 改用 `auto_arima_native`,按
  backend 分支处理 predict(statsforecast / pmdarima / statsmodels),
  所有返回 dict 加 `"backend"` 字段。
- `risk_engine.rolling_volatility` 加 `"backend"` 字段;
  `risk_full_pipeline` 输出含 `garch` + `engine_stack` 字段。
- `forecast_engine.auto_arima` 返回 dict 加 `"backend": "statsmodels"`,
  向后兼容。
- `docs/METHODOLOGY.md` §2.1 三模型表加 backend 双列(Docker /
  sandbox fallback);§6.2.1 新增 GARCH 章节;§7 局限表重排(移除
  "未装"3 项,改写为 fallback 描述)。
- `README.md` Quick start 加 Investment-grade 段(docker compose
  up --build + 引擎探测命令)。

## 6.0.0 — 2026-06-04

### Added
- **Investment-grade forecasting platform** — 10 城 × 12 指标 × 16 年
  (2010-2025) 真实公开数据(1920 数据点) + 4 宏观协变量(national_gdp /
  cpi_yoy / lpr_1y / fdi_inflow,64 数据点)。
- **`backend/data/historical_extended.py`** — 12 指标 × 16 年 × 10 城
  完整数据集,每条带 provenance(source URL + estimated flag +
  confidence + methodology_change,2020 人口口径变更)。
- **`backend/data/macro_data.py`** — 4 宏观协变量(2010-2025)。
- **`backend/core/forecast_engine.py`** — 投资决策级预测引擎:
  - `auto_arima` — statsmodels AIC-driven grid search(p/d/q ∈
    {0..2}×{0..1}×{0..2})
  - `ets_forecast` — statsmodels ExponentialSmoothing(Holt 加法趋势
    + SES fallback)
  - `linear_regression_forecast` — sklearn OLS + t 分布杠杆修正 PI
  - `ensemble_forecast` — 3 模型 AIC-weighted 集成
  - `run_diagnostics` — 5 项残差诊断(ADF / KPSS / Ljung-Box /
    Jarque-Bera / Breusch-Pagan)+ 综合 verdict
  - `chow_test` / `find_structural_breaks` — 结构突变检测
  - `backtest_forecast` — 5 项 walk-forward CV(MAPE / RMSE / MASE /
    sMAPE / Coverage)
  - `forecast_full_pipeline` — 主入口
- **`backend/core/risk_engine.py`** — 投资决策级风险分析:
  - `rolling_volatility` — 滚动年化波动率(对数收益 std)
  - `var_cvar` — 历史模拟 VaR 95/99 + CVaR
  - `scenario_analysis` — 4 档情景(baseline / optimistic +10% /
    pessimistic -10% / recession -25%)
  - `monte_carlo_simulation` — 1000-iter 残差 bootstrap(P5/P50/P95)
  - `risk_full_pipeline` — 主入口
- **`backend/api/routes/investment.py`** — 7 个新投资端点
  (`/api/v1/investment/*`):
  - `/forecast/full` — 完整流水线(forecast + diagnostics + backtest)
  - `/diagnostics/{scope}/{name}` — 残差诊断
  - `/structural-breaks/{scope}/{name}` — 结构突变
  - `/backtest/{scope}/{name}` — 滚动回测
  - `/risk/{scope}/{name}` — 风险 + VaR / CVaR
  - `/scenarios/{scope}/{name}` — 4 档情景
  - `/monte-carlo/{scope}/{name}` — MC 1000 iter
- **`backend/api/routes/data_lineage.py`** — 5 个血缘端点
  (`/api/v1/lineage/*`):
  - `/summary` `/coverage` `/macro` `/macro/growth`
  - `/provenance/city/{name}`
- **`frontend/investment_grade.html`** — 投资决策级 dashboard
  (7 区块 + 4 ECharts 图表,ECharts 5.6 加载)。
- **`docs/METHODOLOGY.md`** — 完整方法学(9 章节 + 9 局限 +
  投资决策使用建议 + 引用)。
- **`docs/superpowers/plans/2026-06-04-investment-grade-forecast.md`**
  — 13 phases 投资级升级计划。
- 4 个新投资端点测试组(`tests/backend/test_integration_investment.py`,
  4 个 e2e 测试)— 验证 7+5 端点全部 200,无 null,CI 带宽非零。

### Fixed
- **`/data/{id}` 路由冲突** — `data_lineage.py` 改前缀为
  `/lineage`,避开 `data.py` 的 `/data/{indicator_id}` 路由。
- **`province 绝对量错误除以城市数`** — 修复 `investment.py` 中
  `_get_scope_timeseries()`:绝对量用 sum,率按人口加权(广东 GDP
  2026 预测从 37,205 修正为 74,402 亿元)。
- **`numpy.bool` PydanticSerializationError** — `run_diagnostics`
  中 `t[key] = bool(t[key])` 转换。
- **ETS API 错** — `fc.iloc[i]` 改为 `fc.values[i]`(新 statsmodels
  返回 ndarray)。
- **LR RSS=0 时 log(0)** — `rss_safe = max(rss, 1e-9 * n)` 兜底。

### Quality
- 全量 263 后端测试通过(原 253 + 10 新 investment/lineage 集成),
  ruff 新代码 clean。
- 深圳 GDP 16 年实测:MAPE 0.40% / MASE 0.07 / Coverage 100%(优秀)。

## Unreleased

### Changed
- Moved city dataset from a hardcoded dict in `backend/data/city_data.py`
  to `data/cities/cities.yaml` so adding a city is a one-file PR.
- Bundled model pickle files are now SHA-256 manifest-checked on load
  (see `models/SHA256SUMS`). The loader refuses anything not on the list.
- JWT layer moved from `python-jose` to `PyJWT[crypto]`; the former has
  been unmaintained for a while.
- Auth route compares credentials with `hmac.compare_digest` to close
  the timing-attack window.
- Workflow actions (CodeQL, Scorecard, gitleaks, lighthouse-ci,
  docker/login) pinned to verified commit SHAs.
- CI / CodeQL / Scorecard jobs run `step-security/harden-runner` for
  egress auditing.

### Fixed
- `cities_v2.py` DataFrame truthiness ambiguity.
- `enterprise_analyzer_v3.py` 500 when `supplier_count` was missing.
- `cities/compare` accepts a plain array body in addition to the typed
  form.
- A handful of `innerHTML` string concatenations in the SPA replaced
  with `createElement` / `esc()`.
- Frontend API base URL resolves relative to the page, so the same
  `index.html` works behind nginx, `http.server`, and a tunnel.
- `requirements.txt` no longer has a stray `python>=3.11` header line
  that was breaking some resolvers.

### Added
- `tests/fuzz/` — hypothesis property-based tests for SQL/XSS/path
  traversal/template injection + city/industry/weight/timeseries fuzz.
- `scripts/setup_branch_protection.sh` — configures main with required
  status checks, CODEOWNERS review, linear history, no force-push.
- `.editorconfig`, `.gitattributes`, `.pre-commit-config.yaml`,
  `CODEOWNERS`, `FUNDING.yml`.
- `tests/fuzz/conftest.py` / `tests/conftest.py` — shared pytest config.
- `requirements-dev.txt`, `requirements-lock.txt`.
- `AUTHORS`, `NOTICE`, `CITATION.cff`, `SUPPORT.md`, `ROADMAP.md`,
  `FAQ.md`, `API.md`.
- `OPENSSF_SCORECARD_REPORT.md` — link to the live report.

## 4.0.0 — 2026-05-01

### Added
- 8-city economic dataset (Shenzhen, Shanghai, Beijing, Guangzhou,
  Wuhan, Chengdu, Hangzhou, Nanjing).
- Enterprise V3: 12-indicator / 3-dimension scorecard + radar chart.
- Government analyzer: 5-year GDP forecast with confidence intervals.
- Multi-city compare: 8-city time series + heatmap + detail table.
- 40+ REST API endpoints, auto OpenAPI docs.
- Web UI: gradient area charts, confidence bands, skeleton loaders,
  toast notifications, ARIA + SEO meta + global error listeners.
- Docker / docker-compose deployment.

## 3.x and earlier

Older iterations live in `git log`.
