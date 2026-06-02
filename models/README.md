# Pre-trained Models

> **This directory contains pickled scikit-learn / joblib models.**
> Pickle loading executes arbitrary Python — see the **Security** section
> below. The platform enforces SHA-256 integrity verification on every load.

## Files

| File | Algorithm | Size | Purpose |
|------|-----------|------|---------|
| `linear_regression.pkl` | Linear Regression | 4 KB | Baseline cost prediction |
| `ridge.pkl`             | Ridge Regression | 4 KB | L2-regularised cost prediction |
| `random_forest.pkl`     | Random Forest     | 392 KB | Production cost / sales forecast |
| `gbdt.pkl`              | Gradient Boosting | 280 KB | Production cost / sales forecast |
| `SHA256SUMS`            | —                 | 1 KB  | SHA-256 manifest (mandatory) |

## Security

### Why this matters

`pickle.load()` (and `joblib.load()`) executes arbitrary Python code
on load. A malicious or corrupted `.pkl` file can result in
**Remote Code Execution** (CVE-class issue, e.g. CVE-2019-12725).

### How we mitigate this

1. **SHA-256 manifest** — `models/SHA256SUMS` lists the expected digest of
   every `.pkl` file. The list is committed to the repo and reviewed
   in every PR that touches `models/`.

2. **Mandatory verification** — every load goes through
   `backend.utils.safe_model_loader.load_model`, which:
   - refuses to load any file **not listed in `SHA256SUMS`**
   - refuses to load any file whose SHA-256 **does not match**
   - refuses to load any file **larger than 100 MB** (zip-bomb guard)
   - uses **constant-time comparison** to avoid timing side-channels

3. **Size cap** — files larger than `MAX_MODEL_SIZE_MB = 100` are rejected
   outright (configurable in `safe_model_loader.py`).

4. **Optional HMAC signing** — release artefacts can also be signed
   with `backend.utils.model_security.load_with_signature` (uses
   `MODEL_SIGNING_KEY` env var). This is a stronger guarantee
   (provenance + integrity) for production deployments.

### Usage

```python
from backend.utils.safe_model_loader import load_model

model = load_model("models/random_forest.pkl")
predictions = model.predict(X)
```

If you need to bypass verification during development (e.g. you are
locally training a new model), set:

```bash
export ALLOW_UNVERIFIED_MODELS=1
```

…but **never** in production.

### Updating the SHA-256 manifest

When you re-train and re-save a model:

```bash
sha256sum models/*.pkl > models/SHA256SUMS
git add models/SHA256SUMS
git commit -m "model(retrain): bump random_forest weights (2025-Q1)"
```

The PR review must include a confirmation that the new model was
trained by an authorised process (CI job or maintainer's local run),
and that the `.pkl` was not transferred over an unsecured channel.

## When to consider moving away from pickle

For multi-MB or production deployments we recommend migrating to:

- **ONNX** (`.onnx`) — language-agnostic, integrity is just bytes
- **joblib + HMAC** (current) — acceptable, but requires discipline
- **TensorFlow SavedModel** (`.pb`) — for deep models

A migration issue is tracked in [ROADMAP.md §4.2](../../ROADMAP.md).
