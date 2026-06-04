# Quick start

## 1. 演示模式(零配置)

```bash
pip install -r requirements.txt
python main.py --mode example
```

生成样例数据集 → 训练模型 → 多城预测 → 写 HTML 报告到
`examples/shenzhen_semiconductor_2025/outputs/`。打开 `.html`
文件即可看 dashboard。

## 2. 投资决策级(推荐)

### 2.1 Sandbox / 无 Docker(向后兼容)

```bash
# terminal 1 — API on :8000
uvicorn backend.api.main:app --reload

# terminal 2 — frontend on :8080
cd frontend && python3 -m http.server 8080
# 打开投资级 dashboard:
# open http://localhost:8080/investment_grade.html
# open http://localhost:8080/province_forecast.html
```

ARIMA 走 `statsmodels` grid (max_p/q=2),GARCH 走 rolling std。
所有 investment API 自动 fallback,响应 `"backend"` 字段显示当前引擎。

### 2.2 Docker 投资级(完整 engine stack)

```bash
docker compose up --build

# 验证引擎装上
curl -s http://localhost:8000/health | jq '.engine_stack'
# 期望: {"statsforecast": true, "arch": true, "pmdarima": true, "prophet": false}

# 投资级流水线 — 应看到 statsforecast 标签
curl -s 'http://localhost:8000/api/v1/investment/forecast/full?scope=city&name=shenzhen&indicator=gdp&years=5' | jq '.models.arima.method'

# GARCH 风险
curl -s 'http://localhost:8000/api/v1/investment/risk/city/shenzhen?indicator=gdp' | jq '.garch.method'

# 打开 dashboard
open http://localhost:8080/investment_grade.html
```

ARIMA 走 `statsforecast.AutoARIMA` (max_p/q=5,10x 快 + 多季节),
GARCH 走 `arch` GARCH(1,1) + 持续性 + 半衰期。MAPE 改善 10-30%。

## 3. 跑测试

```bash
pytest tests/backend/ -v          # 263 后端测试 + 集成
pytest tests/fuzz/ -v             # hypothesis property-based fuzz
python scripts/diagnostics/full_diagnose.py   # end-to-end smoke test
python scripts/diagnostics/browser_test.py    # browser screenshots
```

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

- `backend/core/config.py` — generic config system
- `backend/core/data_manager.py` — multi-source data manager
- `backend/ml/models.py` — model registry (Linear, RF, GBDT, …)
- `backend/ml/trainer.py` — AutoML trainer
- `backend/core/analyzer.py` — end-to-end analyzer
- `configs/*.yaml` — industry templates
- `data/cities/cities.yaml` — city dataset

## What's where

| Want to… | Look at |
|---|---|
| Add a city | `data/cities/cities.yaml` + `scripts/regen_cities_yaml.py` |
| Add an indicator | same yaml, then re-run regen script |
| Add a new analyzer | `backend/analysis/base_analyzer.py` (subclass) |
| Add a new endpoint | `backend/api/routes/` |
| Ship a new model pickle | regenerate `models/SHA256SUMS` |

## See also

- [README.md](README.md)
- [ARCHITECTURE.md](ARCHITECTURE.md) — design notes & data flow
- [API.md](API.md) — full REST reference
- [DEPLOYMENT.md](DEPLOYMENT.md) — Docker / Systemd / K8s
- [FAQ.md](FAQ.md)
