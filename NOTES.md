# Notes

A few things I want to remember for next time, or explain to whoever
reads this repo. Not exhaustive.

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
