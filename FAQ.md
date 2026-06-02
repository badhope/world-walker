# Frequently Asked Questions / 常见问题

Answers to the most common questions about the **Regional Industrial Economic Analysis Platform**.

---

## General / 通用

### 1. What is this project? / 这是什么项目?

An open-source analytics platform for **regional economic analysis**, focused on
four scenarios: retail site selection, sales forecasting, enterprise
business-environment evaluation, and government industry-policy analysis.

一个开源的产业经济分析平台，聚焦 **4 大场景**：零售选址、销售预测、企业营商环境评估、政府产业政策分析。

### 2. Who is the target audience? / 目标用户是谁?

- Data analysts working on regional economics
- Corporate strategy & site-selection teams
- Government planning & development departments
- Data-science students looking for a production-grade reference project
- Anyone interested in Python + FastAPI + ECharts

### 3. Is it production-ready? / 可以用于生产吗?

**Yes.** The platform is at v4.0.0 with:
- 159 backend tests passing
- 70+ API endpoints
- Docker / Docker Compose deployment
- CORS / XSS / security hardening
- Comprehensive documentation

But: the underlying data is **synthetic** for demonstration. For production
use, replace [backend/data/city_data.py](backend/data/city_data.py) with
your own data source (database, API, or CSV).

数据是合成的演示数据。生产环境请替换为真实数据源。

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

### 9. How accurate are the time-series forecasts?

Depends on the model and data:
- **Linear / exponential**: 5–10 % MAPE on stable trends
- **ARIMA**: 8–15 % MAPE on seasonal data
- **Prophet**: 10–20 % MAPE on long-horizon forecasts

The system reports MAE and MAPE for every forecast so you can decide if the
accuracy is acceptable for your use case.

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

**Last updated**: 2026-06-02
**Have a question not answered here?** Open a [Discussion](https://github.com/your-org/regional-economic-analysis/discussions/new) or email <contact@example.com>.
