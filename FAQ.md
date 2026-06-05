# Frequently Asked Questions / 常见问题

Answers to the most common questions about the **Regional Economic Analysis Agent**.

---

## General / 通用

### 1. What is this project? / 这是什么项目?

An open-source analytics agent for **regional economic analysis**, focused on
four scenarios: retail site selection, sales forecasting, enterprise
business-environment evaluation, and government industry-policy analysis.

**v9.0+ 新增**: Python SDK + CLI(任选入口),所有 9 项分析 + LLM Agent。

**v9.1+ 新增**: Web Console(`/console/`),零代码、零安装浏览器管理界面 — 9 tool 可视化 + LLM chat + 改 LLM 配置 + 看历史。

一个开源的产业经济分析 agent,聚焦 **4 大场景**:零售选址、销售预测、企业营商环境评估、政府产业政策分析。

### 2. Who is the target audience? / 目标用户是谁?

- Data analysts working on regional economics
- Corporate strategy & site-selection teams
- Government planning & development departments
- Product managers / operations(non-coders, use Web Console)
- Data-science students looking for a production-grade reference project
- Anyone interested in Python + FastAPI + ECharts + LLM agent

### 3. Is it production-ready? / 可以用于生产吗?

**Yes.** The agent is at **v9.1.0** with:
- **452 backend tests passing** (v6.0 263 + v6.1 10 + v7.0 14 + v8.0 7 + v9.0 66 + v9.1 82 + 10 misc)
- **80+ API endpoints** (40 base + 7 investment + 5 lineage + 8 admin v9.1 + others)
- **3 entry points**: Web Dashboard(只读展示)/ Python SDK / CLI / **Web Console v9.1**(零代码管理)
- **Investment-grade forecasting**: 10 cities × 12 indicators × 16 years (2010-2025) real public data + 4 macro covariates; 3-model ensemble (ARIMA + ETS + LR, AIC-weighted); 5 residual diagnostics; 5 walk-forward CV metrics; VaR / CVaR / GARCH(1,1) / volatility; 4 scenarios; 1000-iter Monte Carlo
- **Self-developed LLM agent** (no LangGraph / Pydantic AI): Trace + Fallback(5 models) + Parallel tools + Retry hint
- **Web Console v9.1**: 8 admin endpoint + 13 静态 HTML + 4 JS helper + 1 CSS
- **Docker investment-grade engine stack**: `statsforecast` / `arch` / `pmdarima` pre-installed; runtime detection via `engine_stack.py`; automatic fallback to `statsmodels` / rolling-std if libraries unavailable
- **Data lineage**: every data point carries source URL + confidence + estimated flag + methodology_change
- **Provincial aggregation**: absolute sums + population-weighted rates (广东 GDP 2026 forecast validated at 74,402 亿元)
- **CORS / XSS / security hardening**
- **Comprehensive documentation** (README, QUICKSTART, METHODOLOGY §1-10, ARCHITECTURE, DEPLOYMENT, API, FAQ, ROADMAP, CHANGELOG, NOTES, CONSOLE_GUIDE v9.1, SDK_CLI_GUIDE v9.0)

But: the underlying data is **publicly sourced from NBSC + city statistical bureaus** with 2024+ marked as `estimated=True, confidence=0.85`. For production
use, integrate live feeds from NBSC / Wind / akshare or your internal data warehouse.

数据来自 NBSC + 各市统计局公开数据(2024+ 标记为 estimated,confidence=0.85)。生产环境建议接入实时数据源。

---

## Installation & setup

### 4. What are the system requirements?

- Python 3.11 or higher
- 4 GB RAM minimum (8 GB recommended)
- Modern web browser (Chrome / Firefox / Safari / Edge)
- Optional: Docker 24+

### 5. Why is the project not running after `git clone`?

Common causes:
- **Python version too old** — need 3.11+
- **Dependencies not installed** — run `pip install -r requirements.txt`
- **Port in use** — change `APP_PORT` in `.env`
- **Missing `data/` directory** — created automatically on first run

### 6. How do I switch from SQLite to PostgreSQL?

Edit `.env`:
```ini
DATABASE_URL=postgresql://user:password@localhost:5432/rea
```

Install the driver:
```bash
pip install psycopg2-binary
```

For migrations, integrate Alembic.

---

## Data & accuracy / 数据与准确度

### 7. Where does the city data come from?

The bundled [backend/data/city_data.py](backend/data/city_data.py) is a **synthetic
dataset** based on publicly-available 2023-2024 figures from the National
Bureau of Statistics and municipal yearbooks. It is suitable for **demonstration
and method validation**, not for legal or business-critical decisions.

For production, integrate with:
- [国家统计局](http://www.stats.gov.cn) (NBS)
- [CEIC](https://www.ceicdata.com)
- [Wind](https://www.wind.com.cn)
- Your own internal data warehouse

### 8. How are the scores calculated?

Each metric (land price, salary, energy, …) is scored 0–100 by comparing the
city to the **statistical quantile benchmarks** derived from all 10 cities in
the dataset:
- low (bottom third)
- medium (middle third)
- high (top third)

Final weighted score = Σ(metric_score × weight). Default weights are stored
in `SCORE_WEIGHTS` and configurable per request.

### 9. How accurate are the time-series forecasts? / 时间序列预测准确度如何?

投资级流水线(深圳 GDP 16 年实测):
- **MAPE 0.40%** — 远低于 5% 优秀阈值
- **MASE 0.07** — 远优于 naive 预测
- **Coverage 100%** — 95% CI 覆盖所有历史样本(略偏保守)

不同模型的典型 MAPE:
- **Linear / LR**: 5-10% on stable trends
- **ETS (Holt)**: 3-8% on trending data
- **ARIMA (statsmodels grid)**: 2-6% on autocorrelated data
- **AutoARIMA (statsforecast)**: 1-5%(Docker 装上后)
- **3-model ensemble**: 0.5-3%(AIC-weighted)

系统对每次预测返回 5 项 CV 指标 + 5 项残差诊断 + 结构突变 +
4 档情景 + 1000-iter MC。你可以根据 verdict(PASS/WARN/FAIL)决定
是否信任当前预测。详见 [docs/METHODOLOGY.md](docs/METHODOLOGY.md) §2-6。

---

## Investment-grade / 投资级

### 26. What does "investment-grade" mean here? / 这里的"投资级"是什么意思?

指用于**投资决策辅助**的预测精度,不是金融术语。平台对每个预测提供:
- **5 项 CV 指标**(MAPE / RMSE / MASE / sMAPE / Coverage)— 模型精度
- **5 项残差诊断**(ADF / KPSS / Ljung-Box / Jarque-Bera / Breusch-Pagan)
- **结构突变检测**(Chow test)
- **VaR / CVaR 95/99** — 风险敞口
- **4 档情景** — 决策收益分布
- **1000-iter Monte Carlo** — 尾部概率
- **数据血缘** — 关键数据点的来源与置信度

不适用:衍生品定价、高频交易、单笔 1 亿元+ 投资、极端事件预测。
详见 [docs/METHODOLOGY.md](docs/METHODOLOGY.md) §8 投资决策使用建议。

### 27. Why isn't `statsforecast` / `arch` installed? / 为什么 sandbox 装不上 statsforecast/arch?

这些库在 pip 安装时与 numpy 2.x / pandas 2.x 有版本冲突。
**解决方案**:
- **Docker 装上**(推荐):`docker compose up --build`,自动装 `statsforecast>=1.5` + `arch>=7.0` + `pmdarima>=2.0`
- **Sandbox 走 fallback**:`engine_stack.py` 运行时探测,自动用 `statsmodels` grid + rolling std,所有 API 输出 `"backend"` 字段标识当前引擎

启动后 `curl /health | jq .engine_stack` 即可看到当前已装库。

### 28. What's the `engine_stack` module? / engine_stack 是什么?

[`backend/core/engine_stack.py`](backend/core/engine_stack.py) 是**运行时库探测模块**:
- 4 个 `*_available()` 函数 — `statsforecast` / `arch` / `pmdarima` / `prophet`
- `engine_stack()` — 4 个 bool 的 dict
- `primary_arima_backend()` — 返回 `statsforecast` / `pmdarima` / `statsmodels` 之一
- `primary_vol_backend()` — 返回 `arch-garch` / `rolling-std` 之一

启动时探测一次(模块级缓存),失败返回 False 不抛异常。所有 investment / risk API 自动切换。

---

## Data sources / 数据来源

### 7. Where does the city data come from? / 城市数据从哪来?

**v6.0.0 起**: 10 城 × 12 指标 × 16 年(2010-2025)**真实公开数据**,来源:
- [NBSC 国家统计局](http://www.stats.gov.cn/) 年度国民经济统计公报
- 各市统计局年度统计公报(URL 在 [`backend/data/historical_extended.py:SOURCE_URLS`](backend/data/historical_extended.py))
- 2024+ 标记 `estimated=True, confidence=0.85`
- 2020 人口口径变更(深圳)标 `methodology_change`

每条数据带 provenance:`source` / `url` / `estimated` / `confidence` /
`methodology_change` / `last_updated`。通过 `GET /api/v1/lineage/provenance/city/{name}` 查询。

**v4.0.0 之前**: 合成数据(基于 2023-2024 公开数字,仅供演示)。

---

## Customisation / 自定义

### 10. How do I add a new city?

Edit [backend/data/city_data.py](backend/data/city_data.py):

```python
CITY_DATA["杭州"] = {
    "name": "杭州",
    "province": "浙江",
    "region": "华东",
    "year": 2024,
    "gdp": 21140.0,
    "gdp_growth": 5.6,
    # ... all required fields
}
```

The system automatically regenerates benchmarks and historical data on next
API call. Restart is not required.

### 11. How do I change the scoring weights?

Default weights in [backend/data/city_data.py](backend/data/city_data.py):

```python
SCORE_WEIGHTS = {
    "business_cost": 0.30,
    "supply_chain": 0.25,
    "policy_benefit": 0.15,
    "talent_pool": 0.15,
    "innovation": 0.10,
    "infrastructure": 0.05,
}
```

You can override per-request in the API body, or modify the defaults.

### 12. Can I integrate it with my own data source?

Yes. Implement a custom loader and inject it into the analysis pipeline:

```python
# backend/data/loaders/custom.py
from backend.data.city_data import get_city_data

def get_city_data(city_name):
    # your custom logic
    return ...
```

---

## Deployment / 部署

### 13. How do I deploy to production?

See [DEPLOYMENT.md](DEPLOYMENT.md). The three main options are:
1. **Systemd** (single-node)
2. **Docker / Docker Compose** (recommended)
3. **Kubernetes** (multi-node, high-availability)

### 14. Does it support horizontal scaling?

Yes. The FastAPI backend is **stateless** and supports running multiple
workers behind a load balancer. Use Redis for shared cache in multi-node
deployments.

### 15. Is HTTPS supported?

Yes. The recommended setup is:
- Nginx as a reverse proxy
- Let's Encrypt for free TLS certificates
- See the Nginx example in [DEPLOYMENT.md](DEPLOYMENT.md)

---

## Contributing / 贡献

### 16. How do I contribute?

See [CONTRIBUTING.md](CONTRIBUTING.md). The short version:

```bash
git clone <repo>
cd regional-economic-analysis
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
pytest tests/backend/
```

### 17. What's the code style?

- **Python**: PEP 8 + Black (line length 120) + isort + ruff
- **HTML / JS**: 2-space indent
- **Commits**: Conventional Commits
- **Docstrings**: Google style

Pre-commit hooks enforce most of these automatically.

### 18. How do I report a security issue?

**Do not** open a public GitHub issue. Email <security@example.com>.
See [SECURITY.md](SECURITY.md) for the full policy and response timeline.

---

## Troubleshooting / 排错

### 19. CORS errors in the browser

Add your frontend URL to `CORS_ORIGINS` in `.env`:

```ini
CORS_ORIGINS=["http://localhost:8080","https://your-domain.com"]
```

Restart the backend.

### 20. "ModuleNotFoundError: backend.data"

This usually means the project root is not on `PYTHONPATH`. Run from the
project root:

```bash
cd /path/to/regional-economic-analysis
python -m uvicorn backend.api.main:app
```

Or with `make run`.

### 21. Forecasts return 0 or NaN

The dataset may not have enough history. Try:
- A shorter forecast horizon (e.g. `years: 3`)
- A simpler model (`model: "linear"`)
- Check for missing data in your input

### 22. Tests fail with "fastapi not installed"

```bash
pip install -r requirements.txt
```

If you installed with `--user`, also run `export PATH=$HOME/.local/bin:$PATH`.

---

## License & legal

### 23. What license is this project under?

**GNU General Public License v3.0 or later (GPL-3.0-or-later)**.
See [LICENSE](LICENSE).

### 24. Can I use it in my commercial product?

Yes, under the terms of the GPLv3:
- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ⚠️ **Share-alike**: derivative works must also be GPLv3
- ⚠️ **Source disclosure**: you must provide the source

For proprietary use, contact <commercial@example.com> for a separate licence.

### 25. How do I cite this project in academic work?

See [CITATION.cff](CITATION.cff) for the canonical citation metadata. GitHub
will auto-generate a "Cite this repository" button from this file.

---

## AI chat assistant (v7.0)

### 26. How does the AI chat assistant work? / AI 助手怎么用?

平台 v7.0 新增。打开 `chat_widget.html` 或任意页面右下角浮动按钮。

示例对话:
- "深圳 GDP 2026 预测多少?" → 调 `get_forecast`
- "广东 GDP 5 年情景分析" → 调 `get_scenarios`
- "数据从哪来?" → 调 `get_data_provenance`

支持 LLM: OpenAI(默认 gpt-4o-mini)/ Claude 3.5 / 本地 Ollama(qwen2.5 / llama3.1)。

**不做**: 投资建议、报告生成、RAG 文档问答。

### 27. 隐私 / 数据出本机 / Privacy?

云端 LLM(OpenAI/Claude)→ 你的问题 + tool 数据会发到外部。
**隐私场景建议用本地 Ollama**:配置 `LLM_OLLAMA_BASE_URL=http://localhost:11434`,
所有请求只在本机处理。

---

## Python SDK + CLI (v9.0+)

### 28. 怎么装 SDK? / How to install SDK?

```bash
pip install -e .          # 装 rca 包 + rca CLI entry point
rca --version             # 应输出: 9.0.0(或者 git describe 给出的实际 version)
python -c "import rca; print(rca.__version__)"  # 同
```

### 29. SDK vs CLI 怎么选?

- **SDK** — 写代码、需要 flow control、要集成到自己的 pipeline、产出供别人调用
- **CLI** — shell 一行 / cron / 脚本 / 没 Python 环境的机器
- **Web Console** v9.1 — 零代码、可视化、不想装任何东西
- **Web Dashboard** — 看投资级图表(只读)

### 30. CLI 支持哪些输出格式?

3 种:`rich`(默认,彩色表格,terminal 友好)/ `plain`(纯文本,管道友好)/ `json`(机器可读)。

```bash
rca --format rich forecast --city shenzhen --indicator gdp --years 5
rca --format plain risk --city shenzhen --indicator gdp
rca --format json monte-carlo --city shenzhen --indicator gdp --years 5 | jq
```

### 31. 怎么用 SDK 改 LLM 配置?

SDK 不直接改(改的是后端 in-memory 状态),但可以通过 HTTP API:

```python
import httpx
httpx.put("http://localhost:8000/api/v1/admin/config", json={"model": "gpt-4o-mini", "temperature": 0.5})
# 或用 CLI
```

也可以用 CLI:`rca config set --model gpt-4o-mini --temperature 0.5`。

### 32. SDK 出错有几种?

4 种错误类,都从 `rca` 直接 re-export:
- `RCAError` — 基类
- `ToolArgumentError` — tool 收到错参数
- `ToolNotFoundError` — tool 名拼错
- `LLMUnavailableError` — LLM 不可达 / fallback 链全失败

详情见 [docs/SDK_CLI_GUIDE.md](docs/SDK_CLI_GUIDE.md)。

---

## Web Console (v9.1+)

### 33. 怎么打开 Console?

后端起来后: <http://localhost:8000/console/>。**不需要** 装任何东西,也不需要单独起 frontend。

### 34. Console 和 Dashboard 什么区别?

| | Dashboard (`/`) | Console (`/console/`) |
|---|---|---|
| 用途 | 投资级图表(只读) | 跑 9 tool + chat + 改配置 + 看历史 |
| 写操作 | 无 | 有(改 LLM 配置、清历史、chat 发消息) |
| 写代码 | 无 | 无 |
| 用户 | 看数据的人 | 跑分析的人(分析师 / PM / 运营) |
| API | `/api/v1/investment/*` 之类 | `/api/v1/admin/*` 之类 |

### 35. Console 怎么保证安全?

**没内置认证**。假定 trusted 私有部署。生产环境在 nginx 层套 basic auth:

```nginx
location /console/ {
    auth_basic "RCA Console";
    auth_basic_user_file /etc/nginx/.htpasswd;
}
```

### 36. Console 的历史存多久?

1000 条 in-memory ring buffer,**重启后端就清空**。需要持久化请提 issue(已在 v9.2 计划)。

### 37. Console 怎么调 LLM?

**先选 model**:`/settings.html` 改 model / base_url / temperature / max_tokens / max_tool_rounds / timeout,Save。
**再 chat**:`/chat.html` 发消息,支持 6 种 SSE event(`thinking` / `token` / `tool_call` / `tool_result` / `final` / `error`)。

完整文档见 [docs/CONSOLE_GUIDE.md](docs/CONSOLE_GUIDE.md)。

---

**Last updated**: 2026-06-05
**Have a question not answered here?** Open a [Discussion](https://github.com/badhope/national_stats/discussions/new) or email <contact@example.com>.
