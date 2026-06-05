# Architecture

> **Current version**: v9.1.0 (2026-06-05)
> **Stack**: Python 3.12+ / FastAPI / Pydantic v2 / SQLite-in-memory / ECharts 5.6 / LiteLLM

This document describes the high-level architecture of the
**Regional Economic Analysis Agent** — a production-grade multi-scenario
analytics system with **3 entry points** (Web Dashboard / Python SDK / CLI /
**Web Console v9.1**).

---

## 1 · High-level diagram

```
                       ┌─────────────────────────────────────────────┐
                       │  FastAPI app (single process, port 8000)     │
                       ├─────────────────────────────────────────────┤
                       │  /            Web Dashboard (index.html)   │
   浏览器 ◀────HTTP────▶│  /console/    Web Console v9.1 (13 页 SPA) │
                       │  /docs        Swagger UI                    │
                       │  /api/v1/...  80+ endpoint                  │
                       │    ├ /admin/  8 admin endpoint v9.1         │
                       │    ├ /ai/chat LLM Agent SSE                 │
                       │    ├ /investment/  7 forecast endpoint       │
                       │    └ /lineage/    5 data-lineage endpoint   │
                       └────────────────┬────────────────────────────┘
                                        │
              ┌─────────────────────────┼──────────────────────────┐
              │                         │                          │
              ▼                         ▼                          ▼
   backend.core                backend.ai                   backend.data
   (forecast_engine /         (LLM Agent v7+:              (10 城 × 12 指标
    risk_engine /              trace / fallback /           × 16 年 = 1920
    engine_stack)              parallel_tools /             + 4 宏观协变量)
                               retry / tool_executor)
              │                         │                          │
              └─────────────────────────┼──────────────────────────┘
                                        │
                                        ▼
                              SQLite-in-memory cache
                              (LRU, no Redis required)


   Other entry points (打同一后端,功能 100% 覆盖):

   ┌─────────────────┐  ┌─────────────────┐
   │  Python SDK     │  │  CLI            │
   │  rca package    │  │  rca command    │
   │  (9 tool + chat)│  │  (11 子命令)    │
   └─────────────────┘  └─────────────────┘
   pip install -e .     rca = "cli.main:app"
   (pyproject.toml)
```

---

## 2 · Tech decisions / 关键技术决策

| 决策 | 替代方案 | 选择理由 |
|------|---------|---------|
| **单 HTML + CDN** | Vue 3 + Vite | 零构建依赖、即开即用、容器化更小 |
| **FastAPI + Pydantic v2** | Flask / Django | 自动 OpenAPI、类型注解、依赖注入 |
| **ECharts 5.6** | Chart.js / D3 | 中文文档完善、置信区间/雷达/热力图原生支持 |
| **In-memory data** | PostgreSQL | 10 城硬编码 1920 数据点 + 4 宏观 = 满足需求,延迟 < 1ms,零运维 |
| **Pydantic Settings** | python-decouple | 类型安全、IDE 提示、自动 `.env` 加载 |
| **LiteLLM** | 直接调 SDK | 统一 OpenAI / Claude / Ollama / 百炼,fallback chain 简单 |
| **Typer + Rich** | argparse | v9.0 CLI:3 输出格式 + 错误处理 + 退出码 + auto-completion |
| **SSE 文本流** | WebSocket | v9.1 chat stream:单向、HTTP 友好、CDN 代理不破坏 |

---

## 3 · Project layout / 目录结构

```
backend/
  api/                  FastAPI 路由层（HTTP 边界）
    main.py             应用入口 + 中间件 + StaticFiles mount /console/
    admin_store.py      v9.1 HistoryStore(deque+Lock)+ ConfigStore(Lock+frozen swap)
    routes/
      admin.py          v9.1 8 admin endpoint(/tools /history /config /chat + SSE)
      cities.py / cities_v2.py / analysis.py / forecast.py / static.py
      data.py           /api/v1/data/*  (legacy 12)
      scenarios.py      /api/v1/scenarios/*  (4)
      data_lineage.py   /api/v1/lineage/*  (5)
      investment.py     /api/v1/investment/*  (7)
    schemas.py          Pydantic v2 request/response models
    deps.py             依赖注入 (auth / rate-limit)
  ai/                   v7.0+ LLM Agent
    config.py / llm_client.py   LiteLLM 包装
    tool_registry.py / tool_executor.py   9 tool dispatch
    chat_service.py     同步 + 流式 chat
    trace.py            v8.0 Step + TraceStore
    fallback.py         v8.0 5 模型降级链
    parallel_tools.py   v8.0 ThreadPoolExecutor + 异常隔离
    retry.py            v8.0 7 类白名单 + 反射
  analysis/             业务分析器
    enterprise_analyzer_v3.py / government_analyzer.py
    retail_location_analyzer.py / sales_forecast_analyzer.py
  core/                 业务核心
    forecast_engine.py  v6.0 投资级 forecast 流水线
    risk_engine.py      v6.0 VaR/CVaR/GARCH/scenarios/Monte Carlo
    engine_stack.py     v6.1 运行时库探测 + 自动 fallback
    explainability.py / ensemble.py / scorable.py
  data/                 数据访问
    historical_extended.py  v6.0 10 城 × 12 指标 × 16 年 + provenance
    macro_data.py           v6.0 4 宏观协变量 (2010-2025)
    cities/cities.yaml      canonical 城市列表
    city_data.py            legacy 兼容层
  data_collection/      akshare / NBS / finance / industry 采集器
  data_processing/      cleaner / transformer / validator
  ml/                   model registry + trainer
  models/               Pydantic schemas
  retail_location/      零售场景
  sales_forecast/       销售场景
  utils/                safe model loader / report generator / visualizer

cli/                    v9.0 Typer CLI(11 子命令 + 3 输出格式)
  main.py               Typer app + Rich 表格 + 错误处理

rca/                    v9.0 Python SDK
  __init__.py           完整 re-export 9 tool + chat + chat_stream + RCAClient + 4 错误类
  _config.py            SDK 独立的 LLM config 加载
  _errors.py            4 错误类
  _resolve.py           scope/name/indicator 解析
  client.py             RCAClient 高层 API
  tools.py              9 tool wrapper
  chat.py               chat / chat_stream
  _formatters.py        rich / plain / json 格式化器

config/                 全局配置
  settings.py           Pydantic Settings
  industries.yaml / regions.yaml

data/cities/            城市数据集
  cities.yaml           10 城清单
  *.yaml                per-city 数据

frontend/
  index.html            投资 dashboard(只读,Plan: Phase 3 改展示站)
  favicon.ico
  console/              v9.1 Web Console
    index.html          Dashboard 页(6 metric + 9 tool 卡片 + 5 历史)
    chat.html           SSE 流式 chat
    settings.html       GET/PUT config 表单
    history.html        列表 + tool 过滤
    tool/               9 个 tool 独立页
      forecast.html / diagnostics.html / backtest.html
      risk.html / scenarios.html / monte-carlo.html
      data-provenance.html / macro-data.html / list-cities.html
    js/                 4 JS helper
      api.js            rcaFetch 包装 8 endpoint + SSE 解析
      form-helpers.js   populateCityDatalist / formToDict / toast / escapeHtml
      chart.js          7 ECharts helper
      sidebar.js        共享侧栏 + 自动高亮
    css/console.css     完整继承 index.html design tokens

docs/                   详细文档
  CONSOLE_GUIDE.md      v9.1 Web Console 用户指南
  SDK_CLI_GUIDE.md      v9.0 Python SDK + CLI 用户指南
  METHODOLOGY.md        投资级方法学 §1-10
  AI_MODEL_REGISTRY.md  25 个百炼模型
  CONFIG_GUIDE.md / DEMO_GUIDE.md / EXAMPLE_ANALYSIS.md
  superpowers/
    specs/2026-06-05-v90-sdk-cli-design.md
    specs/2026-06-05-v91-web-console-design.md
    plans/2026-06-05-v90-sdk-cli.md
    plans/2026-06-05-v91-web-console.md

tests/
  backend/              pytest 单元 + 集成
  cli/                  v9.0 CLI 18 测试
  api/                  v9.0 + v9.1 admin 36 测试
  rca/                  v9.0 SDK 36 测试
  eval/                 v8.0 真 LLM 跑分
  fuzz/                 hypothesis property-based fuzz

scripts/                dev utilities + legacy demos
```

---

## 4 · Core data flow

### 4.1 Web Console tool call (v9.1)

```
Browser /console/tool/forecast.html
  ↓ submit form
  RCA.api.runTool("get_forecast", {scope, name, indicator, years})
  ↓ fetch POST /api/v1/admin/tools/get_forecast/run
  backend.api.routes.admin::run_tool
    ├─ _resolve_tool_func("get_forecast")  ← 动态 getattr(rca.tools, "forecast")
    ├─ try: func(**payload) → result
    ├─ _summarize(result)  ← result_summary 摘要存 history
    └─ HistoryStore.add(QueryRecord{...})  ← deque(maxlen=1000) + Lock
  ↓ return {data, duration_ms, id}
Browser ← setOption({...}) ← ECharts 渲染
```

### 4.2 SDK call (v9.0)

```
import rca
rca.forecast(scope="city", name="shenzhen", indicator="gdp", years=5)
  ↓
rca._resolve.resolve_city("shenzhen") → ("city", "深圳")
  ↓
rca.tools.forecast(scope, name, indicator, years)
  ↓
backend.core.forecast_engine.forecast_full_pipeline(...)
  ├─ run_ensemble(values)         # 3 模型集成
  ├─ run_diagnostics(residuals)   # 5 项
  ├─ run_backtest(values)         # walk-forward
  ├─ run_risk(returns)            # VaR/CVaR/GARCH
  └─ return {data: {...}}  ← packed
  ↓
rca._formatters.format(result, "rich")   ← CLI 用
return dict                                       ← SDK 用
```

### 4.3 LLM Agent chat (v7.0+ → v8.0 → v9.1)

```
User: "深圳 GDP 走势如何?"
  ↓
rca.chat(session_id="u1", message=...)
  ↓
backend.ai.chat_service.chat(cfg, session_id, message)
  ↓
  run_with_fallback(base_cfg, ...)                ← v8.0
  ├─ try qwen-max
  │   └─ LLMClient.call(messages, tools=9) → tool_call: get_forecast
  │       └─ ParallelTools.execute(tool_call)   ← v8.0
  │           └─ backend.core.forecast_engine.forecast(...)
  │       └─ LLMClient.call(messages + tool_result) → final text
  ├─ on 401/403/404: raise (immediately)
  └─ on timeout/429: fallback next model
  ↓
  return {content, tool_calls[], trace, usage}
```

### 4.4 SSE chat stream (v9.1)

```
Browser /console/chat.html
  ↓ fetch GET /api/v1/admin/chat/stream?session_id=...&message=...
backend.api.routes.admin::chat_stream
  ↓ StreamingResponse(generator, media_type="text/event-stream")
  for event in chat_service.chat_stream(cfg, session_id, message):
    yield f"data: {json.dumps(event)}\n\n"
  ↓
Browser RCA.api.streamChat() parses:
  - {type: "thinking"}    → status bar "思考中…"
  - {type: "tool_call"}   → status "调 tool: ..."
  - {type: "token"}       → textContent += content
  - {type: "tool_result"} → status "tool 返回"
  - {type: "final"}       → status "就绪"
  - {type: "error"}       → render error
```

---

## 5 · 4 entry points — 共享数据 / 共享 API

| 入口 | 触发方式 | 数据来源 | 适合 |
|------|----------|----------|------|
| **Web Dashboard** | 浏览器 `/` | `frontend/index.html` 直接拉 `/api/v1/investment/*` + `/api/v1/lineage/*` | 看投资级图表(只读) |
| **Web Console v9.1** | 浏览器 `/console/` | 13 静态 HTML + `RCA.api.*` 打 `/api/v1/admin/*` | 零代码跑 9 tool + chat + 改配置 + 看历史 |
| **Python SDK v9.0** | `import rca; rca.forecast(...)` | `rca.tools.forecast` → `backend.core.forecast_engine.forecast_full_pipeline` | 写代码 / 集成 |
| **CLI v9.0** | `rca forecast --city shenzhen ...` | `cli/main.py` Typer → `rca.tools.*` → `rca._formatters.format(...)` | shell / cron / 脚本 |

**重要**:4 个入口**完全打同一个后端**。Web Console 改的 LLM 配置(Dashboard 不存持久化)是 in-memory ring buffer,后端重启后回到 env var 默认。SDK/CLI 是 stateless,每次调起都读 env var。

---

## 6 · Extension points / 扩展点

### 6.1 Add a new tool to Console (v9.1)

1. 写 tool 函数到 `rca/tools.py`(或 `backend/ai/tool_executor.py`)
2. 在 `backend/api/routes/admin.py` `_TOOL_META` 加 metadata + `_TOOL_FUNC_NAMES` 加 mapping
3. 在 `frontend/console/tool/<name>.html` 写可视化页
4. 写测试:`tests/api/test_admin.py` 加 dispatch case
5. 重启后端即可,自动出现在 Console Dashboard 卡片网格

### 6.2 Add a city (v6.0+)

1. `data/cities/<city_en>.yaml` 添加数据集(参照其它城市格式)
2. `data/cities/cities.yaml` 注册城市
3. `scripts/regen_cities_yaml.py` 重生成
4. 重启后端,自动出现在 `/console/tool/list-cities.html`

### 6.3 Add a new LLM model to fallback chain (v8.0+)

1. `backend/ai/fallback.py` `_DEFAULT_FALLBACK_CHAIN` 加 model id
2. `docs/AI_MODEL_REGISTRY.md` 加 metadata(25 个已注册)
3. `tests/api/test_admin.py` 验证 `updateConfig` 接受新 model

### 6.4 Add a new analyzer (v3.0+ 模式)

1. `backend/analysis/<scenario>_analyzer.py` 继承 `BaseAnalyzer`
2. `backend/api/routes/` 注册 endpoint
3. `tests/backend/test_analysis.py` 加用例

### 6.5 Add a new LLM tool call (v7.0+)

1. `backend/ai/tool_executor.py` 加 tool wrapper(签名/参数 JSON schema)
2. `rca/tools.py` 加 SDK 包装
3. `cli/main.py` 加 Typer 子命令
4. `tests/rca/test_tools.py` + `tests/cli/test_main.py` 加 case

---

## 7 · Performance / 性能特征

| 端点 | 平均响应 | P99 | 备注 |
|------|--------|-----|------|
| `/health` | 2ms | 5ms | 内存读取 |
| `/api/v1/admin/tools` | 5ms | 10ms | 9 tool metadata |
| `/api/v1/admin/tools/{name}/run`(forecast) | 1.2s | 3s | 3 模型集成 + 5 诊断 |
| `/api/v1/admin/tools/{name}/run`(backtest) | 0.6s | 1.5s | walk-forward |
| `/api/v1/admin/tools/{name}/run`(risk) | 0.4s | 1s | VaR/CVaR/GARCH |
| `/api/v1/admin/tools/{name}/run`(monte_carlo) | 4s | 10s | 1000 iter bootstrap |
| `/api/v1/admin/history` | 2ms | 5ms | 1000 条 ring buffer |
| `/api/v1/admin/config` GET/PUT | 1ms | 3ms | Lock + frozen swap |
| `/api/v1/admin/chat/stream` | 5-30s | 60s | 取决于 LLM |
| `/console/index.html` | 200ms | 500ms | CDN 拉 ECharts |
| `/console/tool/*.html` | 150ms | 400ms | 静态 HTML + 1 ECharts |

---

## 8 · Security / 安全模型

- **CORS**: 默认白名单模式(`CORS_ORIGINS` 环境变量)
- **XSS**: Console 所有用户输入通过 `escapeHtml` 转义;`textContent` 优先,`innerHTML` 仅用于可信静态字符串
- **CSRF**: `/api/v1/admin/config` PUT 用 `SameSite=Strict` cookie(将来)
- **认证**: Web Console (`/console/`) 假定 trusted 私有部署,**没有内置认证**;生产环境必须在 nginx 层套 basic auth 或反向代理加 SSO
- **SSE Origin**: 强制 same-origin(防 cross-origin 拉取)
- **History ring buffer**: 1000 条 maxlen,自动丢弃旧的(防 DoS)
- **AIConfig frozen + Lock**: 配置改动构造新 frozen 对象,Lock 串行化,杜绝 hot-swap race
- **模型签名**: 加载的 ML 模型使用 HMAC-SHA256 签名校验(不引入第三方)
- **Env 隔离**: SDK (`rca._config.load_config`) 读 env var,**不** 改;Web Console 改的是后端 in-memory,SDK 不感知

---

## 9 · Deployment / 部署架构

详见 [DEPLOYMENT.md](DEPLOYMENT.md)。

- **Docker compose** — 单容器
- **Systemd** — 裸 Python 进程
- **Kubernetes** — 多副本 + ingress
- **Web Console** — 同后端 single process,无需单独 frontend server

---

**Last updated**: 2026-06-05
**See also**: [README.md](README.md) · [QUICKSTART.md](QUICKSTART.md) · [docs/METHODOLOGY.md](docs/METHODOLOGY.md) · [docs/CONSOLE_GUIDE.md](docs/CONSOLE_GUIDE.md) · [docs/SDK_CLI_GUIDE.md](docs/SDK_CLI_GUIDE.md)
