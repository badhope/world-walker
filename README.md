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
- **Sales forecasting** — multi-model (Linear / RF / GBDT) forecast from
  historical sales.
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
# open http://localhost:8080/index.html
```

Docker:

```bash
docker-compose up --build
```

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
  analysis/     analyzers (enterprise / government / dimension / custom)
  core/         config, data manager, multi-city, caching, tasks
  data/         static city dataset (8 cities, 20+ indicators)
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
frontend/       single-file SPA
models/         bundled pickled estimators + SHA-256 manifest
tests/backend/  pytest unit tests
tests/fuzz/     hypothesis property-based fuzz
scripts/        dev utilities + legacy demos
```

---

## Tests

```bash
pytest tests/backend/ -v        # 185 tests
python full_diagnose.py         # end-to-end smoke test
python scripts/diagnostics/browser_test.py   # browser screenshots
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
