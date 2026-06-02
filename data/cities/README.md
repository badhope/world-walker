# City Data / 城市数据

> **External data store for the Regional Economic Analysis Platform.**
>
> 城市经济数据的外部存储目录。

## File layout

| File | Purpose |
|------|---------|
| `cities.yaml` | 10 城市 × 22 指标静态数据 (YAML) |
| `historical/` | (reserved) 城市历史时序数据，2024 之前年度 |

## How cities.yaml is loaded

`backend/data/city_data.py` reads this file at import time:

```python
_DEFAULT_YAML_PATH = Path(__file__).resolve().parents[2] / "data" / "cities" / "cities.yaml"
_DATA_YAML_PATH = Path(os.getenv("CITY_DATA_YAML", str(_DEFAULT_YAML_PATH)))
```

You can override the path at runtime:

```bash
export CITY_DATA_YAML=/path/to/my_cities.yaml
```

## How to add a new city

1. Open `cities.yaml`
2. Add a new entry under `cities:` (use one of the existing entries as a template)
3. Make sure all 22 fields are filled (use `0` for unknown numeric, `""` for unknown text)
4. Run the test suite: `pytest tests/backend/test_city_data.py -v`
5. Run the diagnose: `python full_diagnose.py`

That's it — **no Python code changes needed**.

## How to update an existing metric

1. Open `cities.yaml`
2. Modify the value
3. Bump `_meta.version` and `_meta.last_updated`
4. Commit the change with a Conventional Commit message:
   ```
   data(cities): update Shenzhen land_price to 1480 (2025-Q1)
   ```

## Why YAML and not Python / SQL?

- **YAML** is the standard for static reference data in open-source projects
  (e.g. country codes, ISO standards, AOSP prebuilt lists).
- **Diff-friendly**: a city data update is a 3-line git diff, not a code change.
- **Reviewable** by non-developers (e.g. analysts, economists).
- **Pluggable** at runtime via `CITY_DATA_YAML` env var (A/B testing, region-specific
  datasets, custom demo data).

## Schema

```yaml
_meta:
  version: "2024.12"
  last_updated: "2024-12-31"
  city_count: 10
  sources:
    - name: "国家统计局"
      url: "http://www.stats.gov.cn"
      coverage: "全国"
  update_frequency: "年度"
  license: "内部使用 / Internal use only"

score_weights:
  business_cost: 0.30
  supply_chain: 0.25
  policy_benefit: 0.15
  ...

cities:
  "深圳":
    name: "深圳"
    province: "广东"
    region: "华南"
    year: 2024
    gdp: 34606.4
    gdp_growth: 6.7
    population: 1768.2
    land_price: 1450.0
    salary_level: 12500.0
    energy_cost: 0.78
    financing_cost: 4.15
    tax_burden: 22.5
    talent_pool: 92.0
    supply_chain_maturity: 95.0
    policy_benefit: 88.0
    innovation_index: 95.5
    infra_score: 93.0
    living_quality: 86.0
    local_support_rate: 78.0
    avg_delivery_time: 2.5
    location_quotient: 1.85
    tax_reduction: 18.0
    tax_coverage: 65.0
    rd_subsidy: 220.0
    avg_approval_time: 5.0
```

## Regenerate from code

If you need to rebuild this file from a code-side seed (e.g. for migration):

```bash
python scripts/regen_cities_yaml.py
python scripts/regen_cities_yaml.py --version 2025.06
python scripts/regen_cities_yaml.py --out /tmp/test.yaml
```

See [scripts/regen_cities_yaml.py](../../scripts/regen_cities_yaml.py).
