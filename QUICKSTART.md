# Quick start

```bash
pip install -r requirements.txt
python main.py --mode example
```

That single command generates a sample dataset, trains the bundled
estimators, runs a multi-city forecast, and writes an HTML report into
`examples/shenzhen_semiconductor_2025/outputs/`. Open the `.html` file
to see the dashboard.

## Run the web app

```bash
# terminal 1 — API on :8000
uvicorn backend.api.main:app --reload

# terminal 2 — frontend on :8080
cd frontend && python3 -m http.server 8080
# open http://localhost:8080/index.html
```

The web app is a single `index.html` — Tailwind and ECharts load from a
CDN, no `npm install` required. The same file works behind nginx, plain
`http.server`, and a tunnel.

## Run the test suite

```bash
pytest tests/backend/ -v          # 185 unit + integration tests
pytest tests/fuzz/ -v             # hypothesis property-based fuzz
python full_diagnose.py           # end-to-end smoke (API + SPA)
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
