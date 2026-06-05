# Quick start

> 5 分钟从 0 到能跑。所有 3 个入口(Dashboard / Python SDK / CLI / Web Console)都打同一个后端。

## 0 · 装包 + LLM 凭据(1 分钟)

```bash
# 1. 装包
pip install -e .

# 2. 配 LLM(任选一种)
cp .env.example .env
echo "LLM_OPENAI_API_KEY=sk-..." >> .env                                # OpenAI
# 或
echo "LLM_OLLAMA_BASE_URL=http://localhost:11434" >> .env                # 本地 Ollama
echo "LLM_ACTIVE_BACKEND=ollama LLM_DEFAULT_BACKEND=ollama" >> .env
```

## 1 · 启动后端(10 秒)

```bash
python -m uvicorn backend.api.main:app --port 8000
# 看到 "Application startup complete" 即就绪
```

## 2 · 选入口

| 入口 | 命令 | 适合 |
|------|------|------|
| **Web Console** ⭐ v9.1 | 浏览器: <http://localhost:8000/console/> | 零代码,跑 9 tool + chat + 改配置 + 看历史 |
| **Web Dashboard** | 浏览器: <http://localhost:8000/> (或 `frontend/index.html`) | 看投资级图表(forecast / risk / scenarios / mc) |
| **Python SDK** | `import rca; rca.forecast(...)` | 写代码 / 集成 |
| **CLI** | `rca forecast --city shenzhen --indicator gdp --years 5` | shell / cron / 脚本 |

## 3 · 30 秒验证(任选一个)

```bash
# SDK
python -c "import rca; print(rca.forecast(scope='city', name='shenzhen', indicator='gdp', years=3)['data']['ensemble']['predictions'])"

# CLI
rca list-cities --format plain

# HTTP API
curl -s http://localhost:8000/api/v1/admin/tools | python -m json.tool | head

# Web Console — 浏览器开 http://localhost:8000/console/
# 选 "Forecast" → 填 shenzhen / gdp / 5 → Run → 看 ensemble 折线 + 95% CI
```

---

## 4 · Docker 投资级(完整 engine stack)

```bash
docker compose up --build

# 验证引擎装上
curl -s http://localhost:8000/health | jq '.engine_stack'
# 期望: {"statsforecast": true, "arch": true, "pmdarima": true, "prophet": false}

# 投资级流水线 — 应看到 statsforecast 标签
curl -s 'http://localhost:8000/api/v1/investment/forecast/full?scope=city&name=shenzhen&indicator=gdp&years=5' | jq '.models.arima.method'
```

ARIMA 走 `statsforecast.AutoARIMA` (max_p/q=5, 10x 快),GARCH 走 `arch` GARCH(1,1) + 持续性 + 半衰期。MAPE 改善 10-30%。

## 5 · 跑测试

```bash
# 关键测试(api + rca + cli)
python -m pytest tests/api tests/rca tests/cli -q
# 113 passed

# 全测试(含 backend — 一些需要 openpyxl/matplotlib,缺包会 skip 或 error)
python -m pytest tests --continue-on-collection-errors -q
# 452 pass / 5 fail(pre-existing openpyxl 缺包) / 2 skip

# 端到端 smoke
python scripts/diagnostics/full_diagnose.py
python scripts/diagnostics/browser_test.py    # browser screenshots
```

---

## Python SDK 一览(9 tool)

```python
import rca

# 9 tool 完全本地 — 0 LLM 调用、0 费用
rca.forecast(scope="city", name="shenzhen", indicator="gdp", years=5)
rca.diagnostics(scope="city", name="shenzhen", indicator="gdp")
rca.backtest(scope="city", name="shenzhen", indicator="gdp")
rca.risk(scope="city", name="shenzhen", indicator="gdp")
rca.scenarios(scope="city", name="shenzhen", indicator="gdp", years=5)
rca.monte_carlo(scope="city", name="shenzhen", indicator="gdp", years=5)
rca.data_provenance(name="shenzhen")
rca.macro_data()
rca.list_cities()

# LLM Agent(自动 multi-round tool call)
rca.chat(session_id="u1", user_message="深圳 GDP 走势如何?")
for ev in rca.chat_stream(session_id="u1", user_message="..."):
    if ev["type"] == "token":
        print(ev["content"], end="", flush=True)
```

## CLI 一览(11 子命令)

```bash
# 9 tool
rca forecast --city shenzhen --indicator gdp --years 5
rca diagnostics --city shenzhen --indicator gdp
rca backtest --city shenzhen --indicator gdp
rca risk --city shenzhen --indicator gdp
rca scenarios --city shenzhen --indicator gdp --years 5
rca monte-carlo --city shenzhen --indicator gdp --years 5
rca data-provenance --name shenzhen
rca macro-data
rca list-cities

# LLM Agent
rca chat --session u1 --message "深圳 GDP 走势如何?"
rca chat-stream --session u1 --message "..." | head -50

# 3 输出格式
rca --format rich forecast --city shenzhen --indicator gdp --years 5   # 彩色表格
rca --format plain risk --city shenzhen --indicator gdp               # 纯文本
rca --format json monte-carlo --city shenzhen --indicator gdp --years 5 # JSON

# 改 LLM 配置
rca config show
rca config set --model gpt-4o-mini --temperature 0.5
```

---

## Web Console 一览(13 页)

打开 <http://localhost:8000/console/>:

| 路径 | 用途 |
|------|------|
| `/console/` (index.html) | Dashboard:6 metric System Status + 9 tool 卡片 + Recent History 5 条 |
| `/console/tool/forecast.html` | ensemble 折线 + 95% CI 区间带 + 末年值卡 |
| `/console/tool/diagnostics.html` | 5 项残差诊断 bar + verdict badge |
| `/console/tool/backtest.html` | walk-forward 双线 + 5 指标卡 + 逐年明细 |
| `/console/tool/risk.html` | VaR / CVaR 4 bar + 详细表 + GARCH 解释 |
| `/console/tool/scenarios.html` | 4 档情景对比折线 + 末年值 / 回撤表 |
| `/console/tool/monte-carlo.html` | P5 / P50 / P95 扇形带 + 区间宽 |
| `/console/tool/data-provenance.html` | 树形 HTML + URL / 置信度 / 估算标记 |
| `/console/tool/macro-data.html` | 4 协变量 sparkline + 同比 |
| `/console/tool/list-cities.html` | 城市卡片网格 + 过滤搜索 |
| `/console/chat.html` | LLM Agent SSE 流式 chat + 同步 sync 按钮 |
| `/console/settings.html` | GET / PUT LLM 配置表单 |
| `/console/history.html` | 列表 200 条 + tool 过滤 + 清空 |

完整文档:[docs/CONSOLE_GUIDE.md](docs/CONSOLE_GUIDE.md)

---

## Customise the analysis

```python
from backend import UniversalAnalyzer, create_sample_data

analyzer = UniversalAnalyzer(config_name="default")
df = create_sample_data()
dataset = analyzer.load_data_from_dataframe(df)

result = analyzer.analyze(
    run_ml=True,
    target_column="market_size",
    feature_columns=["land_price", "labor_cost", "energy_cost"],
)
print(result.ml_result.best_model.model_name, result.ml_result.best_model.metrics.r2)
```

## Files of interest

- `backend/core/config.py` — 通用配置
- `backend/core/data_manager.py` — 多源数据
- `backend/ml/models.py` — 模型注册表
- `backend/core/engine_stack.py` — 运行时库探测 + 自动 fallback
- `backend/ai/` — LLM Agent(trace / fallback / parallel_tools / retry)
- `backend/api/admin_store.py` — v9.1 HistoryStore + ConfigStore
- `backend/api/routes/admin.py` — v9.1 8 admin endpoint
- `cli/main.py` — v9.0 Typer CLI 11 子命令
- `rca/__init__.py` — v9.0 Python SDK public API
- `frontend/console/` — v9.1 Web Console 13 页 + 4 JS + 1 CSS
- `data/cities/cities.yaml` — 10 城数据集

## What's where

| Want to… | Look at |
|---|---|
| Add a city | `data/cities/cities.yaml` + `scripts/regen_cities_yaml.py` |
| Add an indicator | same yaml, then re-run regen script |
| Add a new analyzer | `backend/analysis/base_analyzer.py` (subclass) |
| Add a new endpoint | `backend/api/routes/` |
| Add a new tool to Console | `backend/api/routes/admin.py` `_TOOL_META` + `frontend/console/tool/<name>.html` |
| Ship a new model pickle | regenerate `models/SHA256SUMS` |
| Change default LLM | `.env` `LLM_*` vars,或 Console `/settings.html` |
| Run a real LLM eval | `python -m tests.eval.run_eval --model qwen-max` |

## See also

- [README.md](README.md) — v9.1 总览
- [ARCHITECTURE.md](ARCHITECTURE.md) — 设计 + 数据流
- [API.md](API.md) — REST API 完整参考
- [DEPLOYMENT.md](DEPLOYMENT.md) — Docker / Systemd / K8s
- [FAQ.md](FAQ.md) — 常见问题
- [docs/CONSOLE_GUIDE.md](docs/CONSOLE_GUIDE.md) — v9.1 Web Console 用户指南
- [docs/SDK_CLI_GUIDE.md](docs/SDK_CLI_GUIDE.md) — v9.0 Python SDK + CLI 用户指南
- [CHANGELOG.md](CHANGELOG.md) — 全部版本变更
