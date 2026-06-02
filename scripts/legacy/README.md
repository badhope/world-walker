# Legacy Scripts / 历史脚本

> **These files have been moved here from the project root and are NO LONGER maintained.**
> They are kept only for historical reference and archaeology purposes.
>
> **Don't use these for new work.** See the recommended replacements below.

## Why are they here?

In early development the project accumulated a large number of
one-off scripts in the project root (`test_*.py`, `demo_*.py`,
`diagnose_*.py`, `verify_*.py`, `diag_*.py`, `quick_demo.py`,
`run_full_demo.py`). These scripts:

- duplicated functionality already covered by `tests/backend/`
- were not part of the CI pipeline
- made the project root visually noisy for reviewers
- made it ambiguous which file was the "real" entry point

Per a code review (2026-06), they were archived here so that the
project root contains **exactly one Python entry point**: `main.py`.

## Mapping to the supported entry points

| Legacy file (here) | Use instead |
|--------------------|-------------|
| `demo_complete.py` | `python main.py --mode example` |
| `demo_cross_industry.py` | `python main.py --mode example --type comprehensive` |
| `demo_enhanced.py` | `python main.py --mode example --type enterprise` |
| `demo_flexibility.py` | `python main.py --mode example` |
| `demo_retail_location.py` | `python main.py --mode example --type retail` |
| `demo_sales_forecast.py` | `python main.py --mode example --type sales` |
| `quick_demo.py` | `python main.py --mode example` |
| `run_full_demo.py` | `python main.py --mode example --verbose` |
| `test_functional.py` | `pytest tests/backend/test_analyzers.py` |
| `test_simple.py` | `pytest tests/backend/` |
| `test_robustness.py` | `pytest tests/backend/test_analyzers.py::TestRobustness` |
| `test_universal_system.py` | `pytest tests/backend/test_analysis.py` |
| `test_real_analysis.py` | `pytest tests/backend/test_real_data_analysis.py` |
| `test_full_interaction.py` | `pytest tests/fuzz/test_api_fuzz.py` |
| `test_all_apis.py` | `pytest tests/backend/test_api.py` |
| `test_config.py` | `pytest tests/backend/` |
| `diagnose_all.py` | `python full_diagnose.py` |
| `diag_full.py` | `python full_diagnose.py` |
| `full_diagnose.py` *(kept at root)* | `python full_diagnose.py` |
| `verify_day3.py` / `verify_day4.py` / `verify_project.py` | `python full_diagnose.py` |

## When can I delete this directory?

After **two minor releases** without anyone complaining that their
workflow is broken, this entire directory can be deleted in a cleanup PR.

For now (v4.0.x), we keep it for safety.
