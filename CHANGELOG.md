# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/).
Versioning: [SemVer](https://semver.org/).

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
