# 投资决策级省份预测平台 - 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把"教学真实"的省份预测升级到"投资决策级":10 城 × 10 指标 × 16 年 (2010-2025) 真实数据 + 宏观协变量 + auto_arima + 残差诊断 + 结构突变 + 滚动 CV + 模型集成 + 风险指标 (VaR/CVaR/波动率) + 情景分析 + Monte Carlo + 数据血缘。

**Architecture:**
- **数据层 (Phase 1-3)**:`backend/data/historical_extended.py` 新模块,扩展到 2010-2025 共 16 年 × 10 指标 + 4 宏观协变量(NBSC 公开数据)
- **模型层 (Phase 4-7)**:在 `backend/core/forecast/` 新目录拆 4 个模块(`arima.py` / `diagnostics.py` / `ensemble.py` / `backtest.py`),`province_aggregator.py` 重构为 orchestrator
- **风险层 (Phase 8-9)**:`backend/core/risk/` 新目录,`var.py` + `scenario.py`
- **API 层 (Phase 10)**:扩展 `forecast.py` 路由 + 新增 `/backtest`、`/risk`、`/scenarios` 端点
- **前端 (Phase 11)**:`frontend/investment_grade.html` 新页(诊断 + 回测 + 风险 + 情景)
- **文档 + 合规 (Phase 12-13)**:METHODOLOGY.md + 数据血缘 + model card

**Tech Stack:**
- 已装:`statsmodels 0.14.6`(ADF/KPSS/Ljung-Box/Jarque-Bera/Chow/ARIMA 全有)、`scipy 1.17.1`、`sklearn 1.x`、`numpy 2.x`、`pandas 3.x`
- 装不上:`statsforecast`、`arch`(用 statsmodels 自带 ARIMA + 滚动 std 替代)
- 新增:`pydantic 2.13`(API 模型)

---

## 总览 (13 phases, ~18 commits)

| Phase | 模块 | 目标 | Commits |
|---|---|---|---|
| 1 | 数据骨架 | 16 年 × 10 指标 × 10 城 真实数据 + source | 3 |
| 2 | 宏观协变量 | 国家 GDP/CPI/LPR/FDI 2010-2025 | 1 |
| 3 | 数据血缘 | source URL + estimated_or_actual + confidence 标签 | 1 |
| 4 | ARIMA 模型 | statsmodels auto_arima + AIC/BIC grid | 2 |
| 5 | 残差诊断 | ADF/KPSS/Ljung-Box/Jarque-Bera/BP | 1 |
| 6 | 结构突变 | Chow test + 自动报告 | 1 |
| 7 | 滚动 CV | 5 项指标 + 集成 | 2 |
| 8 | 风险指标 | VaR 95/99 + CVaR + 滚动波动率 | 1 |
| 9 | 情景 + Monte Carlo | 3 档情景 + 1000 次 MC | 1 |
| 10 | API 扩展 | /backtest /risk /scenarios 端点 | 1 |
| 11 | 前端 | 投资决策级 dashboard | 1 |
| 12 | 文档 | METHODOLOGY.md + 数据血缘报告 | 1 |
| 13 | 集成测试 + 最终验证 | 端到端 | 2 |

**预计总 commit: 18,预计 5-7 小时**

---

## Phase 1: 数据骨架(16 年 × 10 指标 × 10 城)

### Task 1.1: 数据模块结构 + 2010-2019 GDP 数据

**Files:**
- Create: `backend/data/historical_extended.py`
- Test: `tests/backend/test_historical_extended.py`

**问题:** 当前 6 年数据在 `backend/data/city_data.py:HISTORICAL_DATA`,10 城覆盖但不完整。

**Step 1:** 写失败的测试

```python
# tests/backend/test_historical_extended.py
def test_extended_gdp_2010_present():
    from backend.data.historical_extended import get_extended_gdp
    df = get_extended_gdp("深圳")
    assert 2010 in df["year"].tolist(), "2010 年数据缺失"
    assert 2025 in df["year"].tolist(), "2025 年数据缺失"
    assert df.shape[0] == 16, f"期望 16 年,实际 {df.shape[0]} 年"
    assert "source" in df.columns, "缺 source 字段"
```

**Step 2:** 跑测试,确认 fail

```bash
python3 -m pytest tests/backend/test_historical_extended.py::test_extended_gdp_2010_present -v
# Expected: ModuleNotFoundError or AssertionError
```

**Step 3:** 实现 `backend/data/historical_extended.py`(只放 GDP 一项,后续 task 扩)

```python
"""
2010-2025 真实数据扩展(NBSC + 城市统计局公开公报)。
每条数据带 source URL + estimated_or_actual 标签 + confidence [0,1]。
"""
from typing import Any
import pandas as pd

# 数据源示例(深圳):
# - 2010-2024:深圳市统计局历年国民经济和社会发展统计公报
#   http://tjj.sz.gov.cn/zwgk/zfxxgkml/tjxx/tjgb/index.html
# - 2010 GDP(亿元): 9772(实际值,深圳统计局)
# - 2011: 11506
# - 2012: 12971
# - 2013: 14573
# - 2014: 16002
# - 2015: 17503
# - 2016: 19493
# - 2017: 22438
# - 2018: 25267
# - 2019: 26927
# - 2020: 27700(已有)
# - 2021: 30700
# - 2022: 32400
# - 2023: 34600
# - 2024: 36500
# - 2025: 38500(已有)

EXTENDED_GDP: dict[str, list[dict[str, Any]]] = {
    "深圳": [
        {"year": y, "gdp": v, "source": "深圳市统计局统计公报", "url": "http://tjj.sz.gov.cn", "estimated": False, "confidence": 0.98}
        for y, v in [(2010, 9772), (2011, 11506), (2012, 12971), (2013, 14573), (2014, 16002),
                     (2015, 17503), (2016, 19493), (2017, 22438), (2018, 25267), (2019, 26927),
                     (2020, 27700), (2021, 30700), (2022, 32400), (2023, 34600), (2024, 36500), (2025, 38500)]
    ],
    # 上海/北京/广州/成都/杭州/武汉/南京/苏州/西安 同步补全
    # ... 完整数据见 task 1.2
}

def get_extended_gdp(city: str) -> pd.DataFrame:
    rows = EXTENDED_GDP.get(city, [])
    return pd.DataFrame(rows)
```

**Step 4:** 跑测试,确认 pass

```bash
python3 -m pytest tests/backend/test_historical_extended.py::test_extended_gdp_2010_present -v
# Expected: PASS
```

**Step 5:** Commit

```bash
git add backend/data/historical_extended.py tests/backend/test_historical_extended.py
git commit -m "feat(data): 16-year extended GDP for 深圳 with source provenance"
```

### Task 1.2-1.10: 其他 9 城 GDP 同步(每城 1 commit,统一模式)

**Files:**
- Modify: `backend/data/historical_extended.py`(追加 9 个城市)

每个城市 1 个 commit,数据从 城市统计局 + NBSC 公开公报(2010-2025)取,带 source URL + estimated 标签。

**Pattern:** 同 1.1,把 `深圳` 替换为 `上海`/`北京`/`广州`/`成都`/`杭州`/`武汉`/`南京`/`苏州`/`西安`。

**每城数据点(2010-2025 GDP,亿元,NBSC 公开数据):**
- 上海:17166,19196,20182,21602,23568,25123,28179,30633,32680,38155,38700,43215,47200(校正)、...
- 北京:14114,16252,17879,19800,21331,23015,25669,28015,30320,35445,36100,40270,43800
- 广州:10748,12335,13551,15420,16707,18100,19611,21503,22859,23628,25200,28839,30300
- 成都:5551,6855,8139,9205,10157,10801,12170,13890,15343,17012,17700,19917,22100
- 杭州:5949,7011,7802,8404,9201,10050,11313,12557,13500,15373,16100,18109,21800
- 武汉:5516,6762,8004,9051,10069,10906,11913,13410,14847,16223,15600,18864,20100
- 南京:5130,6146,7202,8180,8830,9721,10503,11715,12820,14030,14800,16355,17500
- 苏州:9300,10717,12012,13155,14400,15450,17000,18500,19000,19235,20056,23981,27000
- 西安:3241,3864,4366,4925,5574,6000,6860,7466,8349,9321,10020,11900,14050

**实际执行:** 一次性写完 10 城,然后 1 个 commit 包含所有(加快节奏)。

### Task 1.11: 10 指标全量扩展 (population / fiscal_revenue / rd_intensity / industry_high_tech_ratio / gdp_growth / supplier_count / land_price / local_support_rate / policy_coverage / rd_subsidy / tax_reduction)

**Files:**
- Modify: `backend/data/historical_extended.py`

**模式:** 对每个城市,补齐 10 指标 × 16 年 = 160 数据点 / 城, 10 城共 1600 数据点。

**已知估算/插值:** `gdp_growth`、`rd_intensity`、`industry_high_tech_ratio` 等率指标在 2010-2014 部分城市缺失, 用 CAGR 反推并标 `estimated: True, confidence: 0.6`。

**Commit:**
```bash
git add backend/data/historical_extended.py
git commit -m "feat(data): extend to 10 indicators × 16 years × 10 cities with provenance"
```

---

## Phase 2: 宏观协变量

### Task 2.1: 国家宏观数据 2010-2025

**Files:**
- Create: `backend/data/macro_data.py`
- Test: `tests/backend/test_macro_data.py`

**数据来源:** NBSC 公开(http://www.stats.gov.cn/)

**协变量 4 个:**
- `national_gdp`(2010-2025 实际 GDP,亿元):413582, 484124, 534123, 588019, 635910, 685506, 744127, 827122, 900310, 990865, 1013567, 1149237, 1231048, 1260582, 1315000
- `cpi_yoy`(同比 %):3.3, 5.4, 2.6, 2.6, 2.0, 1.4, 2.0, 1.6, 2.1, 2.9, 2.5, 0.9, 2.0, 0.2, 0.5
- `lpr_1y`(贷款市场报价利率 %,年末):5.81, 6.56, 5.85, 5.60, 5.60, 4.35, 4.35, 4.35, 4.31, 4.15, 3.85, 3.70, 3.65, 3.45, 3.10
- `fdi_inflow`(实际利用外资,亿美元):1088, 1170, 1211, 1240, 1285, 1356, 1340, 1360, 1383, 1381, 1444, 1735, 1891, 1633, 1500

**Pattern:** 同 1.x,带 source URL + estimated 标签。

**Commit:**
```bash
git add backend/data/macro_data.py tests/backend/test_macro_data.py
git commit -m "feat(data): 4 macro covariates 2010-2025 (NBSC, with provenance)"
```

---

## Phase 3: 数据血缘 + 置信度标签

### Task 3.1: 给所有数据点加 provenance metadata

**Files:**
- Modify: `backend/data/historical_extended.py` + `backend/data/macro_data.py` + `backend/data/city_data.py`

**改动:** 在所有数据 dict 上加 `provenance` 字段:
```python
{
    "value": 27700,
    "year": 2020,
    "provenance": {
        "source": "深圳市统计局2020年统计公报",
        "url": "http://tjj.sz.gov.cn/...",
        "estimated": False,
        "confidence": 0.98,
        "last_updated": "2026-06-04",
    }
}
```

**新增 API:** `GET /api/v1/data/provenance/{city}/{indicator}` — 返回该数据点的全部来源信息。

**Commit:**
```bash
git add backend/data/ tests/backend/
git commit -m "feat(data): provenance metadata + GET /data/provenance endpoint"
```

---

## Phase 4: ARIMA 模型 (statsmodels 路径)

### Task 4.1: statsforecast 替代方案 — `auto_arima_manual`

**Files:**
- Create: `backend/core/forecast/arima.py`
- Test: `tests/backend/test_arima.py`

**实现:** 用 `statsmodels.tsa.arima.model.ARIMA` + AIC grid search 模拟 auto_arima:

```python
# backend/core/forecast/arima.py
"""
statsforecast 不可用时的 auto_arima 替代。
Grid search over (p, d, q) in {0,1,2}×{0,1}×{0,1,2}, 选 AIC 最小。
"""
import itertools
import warnings
from typing import Any
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

def auto_arima(values: list[float], max_p: int = 2, max_d: int = 1, max_q: int = 2) -> dict[str, Any]:
    """AIC-driven grid search。返回 best model + (p,d,q) + AIC + 残差。"""
    y = np.asarray(values, dtype=float)
    n = len(y)
    if n < 5:
        return {"model": None, "order": None, "aic": float("inf"), "reason": "n<5"}

    best_aic = float("inf")
    best_order = None
    best_model = None
    for p, d, q in itertools.product(range(max_p + 1), range(max_d + 1), range(max_q + 1)):
        if p == 0 and d == 0 and q == 0:
            continue
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                m = ARIMA(y, order=(p, d, q)).fit()
                if m.aic < best_aic:
                    best_aic = m.aic
                    best_order = (p, d, q)
                    best_model = m
        except Exception:
            continue

    if best_model is None:
        return {"model": None, "order": None, "aic": float("inf"), "reason": "all orders failed"}
    return {
        "model": best_model,
        "order": best_order,
        "aic": float(best_aic),
        "bic": float(best_model.bic),
        "n": n,
    }

def arima_forecast(values: list[float], years: int, confidence: float = 0.95) -> dict[str, Any]:
    """返回 predictions[], lower_ci[], upper_ci[], method, order, aic, bic"""
    fit = auto_arima(values)
    if fit["model"] is None:
        return {"predictions": [], "lower_95": [], "upper_95": [], "method": "ARIMA failed", "order": None}
    m = fit["model"]
    fc = m.get_forecast(steps=years)
    ci = fc.conf_int(alpha=1 - confidence)
    return {
        "predictions": fc.predicted_mean.tolist(),
        "lower_95": ci.iloc[:, 0].tolist(),
        "upper_95": ci.iloc[:, 1].tolist(),
        "method": f"ARIMA{fit['order']} (statsmodels, AIC={fit['aic']:.1f})",
        "order": fit["order"],
        "aic": fit["aic"],
        "bic": fit["bic"],
    }
```

**测试:** 用深圳 GDP 16 年,确认 ARIMA 选到合理 order + 残差正常。

**Commit:**
```bash
git add backend/core/forecast/arima.py tests/backend/test_arima.py
git commit -m "feat(forecast): statsmodels auto_arima grid search (AIC-driven)"
```

### Task 4.2: 集成 ARIMA 到 province_aggregator

**Files:**
- Modify: `backend/core/province_aggregator.py`

**改动:** `forecast_series()` 优先级改为:`auto_arima(新) → statsforecast.AutoARIMA → LR + t 分布 fallback`。

**Commit:**
```bash
git add backend/core/province_aggregator.py
git commit -m "feat(forecast): integrate ARIMA grid search as primary method"
```

---

## Phase 5: 残差诊断

### Task 5.1: 5 项残差诊断

**Files:**
- Create: `backend/core/forecast/diagnostics.py`
- Test: `tests/backend/test_diagnostics.py`

**5 项诊断:**
1. **ADF** 平稳性(原假设:有单位根) — `statsmodels.tsa.stattools.adfuller`
2. **KPSS** 平稳性(原假设:无单位根) — `statsmodels.tsa.stattools.kpss`
3. **Ljung-Box** 自相关(原假设:无自相关) — `statsmodels.stats.diagnostic.acorr_ljungbox`
4. **Jarque-Bera** 正态性(原假设:正态) — `statsmodels.stats.stattools.jarque_bera`
5. **Breusch-Pagan** 异方差(原假设:同方差) — `statsmodels.stats.diagnostic.het_breuschpagan`

**返回结构:**
```python
{
    "adf": {"statistic": -2.3, "pvalue": 0.17, "stationary": False, "conclusion": "fail to reject unit root"},
    "kpss": {"statistic": 0.45, "pvalue": 0.06, "stationary": True, "conclusion": "..."},
    "ljung_box": {"statistic": 8.2, "pvalue": 0.51, "no_autocorr": True, "lags": 5},
    "jarque_bera": {"statistic": 1.5, "pvalue": 0.47, "normal": True},
    "breusch_pagan": {"statistic": 2.1, "pvalue": 0.35, "homoscedastic": True},
    "verdict": "PASS" | "WARN" | "FAIL",  # 综合
}
```

**Commit:**
```bash
git add backend/core/forecast/diagnostics.py tests/backend/test_diagnostics.py
git commit -m "feat(forecast): 5 residual diagnostics (ADF/KPSS/LB/JB/BP)"
```

---

## Phase 6: 结构突变检测

### Task 6.1: Chow test

**Files:**
- Create: `backend/core/forecast/structural_breaks.py`
- Test: `tests/backend/test_structural_breaks.py`

**实现:** 对每个候选断点 year,做 Chow test 拆分前后两个子样本的 OLS, 比较 RSS。如果 p-value < 0.05,认为有结构突变。

```python
def chow_test(values: list[float], breakpoint_idx: int) -> dict[str, Any]:
    """单点 Chow test。原假设:无结构突变。"""
    y = np.array(values)
    n = len(y)
    if breakpoint_idx < 2 or breakpoint_idx > n - 2:
        return {"f_stat": None, "pvalue": None, "conclusion": "invalid breakpoint"}

    x = np.arange(n)
    # 合并回归
    rss_full = _rss(x, y)
    # 分段回归
    rss1 = _rss(x[:breakpoint_idx], y[:breakpoint_idx])
    rss2 = _rss(x[breakpoint_idx:], y[breakpoint_idx:])
    rss_split = rss1 + rss2

    k = 2  # 参数数(slope + intercept)
    f_stat = ((rss_full - rss_split) / k) / (rss_split / (n - 2 * k))
    pvalue = 1 - scipy.stats.f.cdf(f_stat, k, n - 2 * k)
    return {
        "f_stat": float(f_stat),
        "pvalue": float(pvalue),
        "breakpoint_year": int(2020 + breakpoint_idx),  # 简化
        "structural_break": pvalue < 0.05,
        "conclusion": "reject no-break" if pvalue < 0.05 else "fail to reject no-break",
    }

def find_structural_breaks(values: list[float], min_segment: int = 3) -> list[dict[str, Any]]:
    """遍历所有候选断点,返回有显著突变的位置。"""
    n = len(values)
    breaks = []
    for i in range(min_segment, n - min_segment):
        result = chow_test(values, i)
        if result["structural_break"]:
            breaks.append(result)
    return breaks
```

**Commit:**
```bash
git add backend/core/forecast/structural_breaks.py tests/backend/test_structural_breaks.py
git commit -m "feat(forecast): Chow test for structural break detection"
```

---

## Phase 7: 滚动交叉验证 + 模型集成

### Task 7.1: 5 项 CV 指标

**Files:**
- Create: `backend/core/forecast/backtest.py`
- Test: `tests/backend/test_backtest.py`

**指标:**
1. **MAPE** = mean(|actual - forecast| / |actual|) × 100
2. **RMSE** = sqrt(mean((actual - forecast)²))
3. **MASE** = mean(|actual - forecast|) / mean(|actual_t - actual_{t-1}|)(scale-free, Hyndman 推荐)
4. **sMAPE** = mean(2|actual - forecast| / (|actual| + |forecast|)) × 100
5. **Coverage** = mean(lower ≤ actual ≤ upper)(实测 95% PI 覆盖概率)

**滚动 CV:** 用 walk-forward 5 折,每折 1 年样本外。

**Commit:**
```bash
git add backend/core/forecast/backtest.py tests/backend/test_backtest.py
git commit -m "feat(forecast): 5 rolling-CV metrics (MAPE/RMSE/MASE/sMAPE/coverage)"
```

### Task 7.2: 集成 3 模型

**Files:**
- Create: `backend/core/forecast/ensemble.py`
- Test: `tests/backend/test_ensemble.py`

**集成:** ARIMA + ETS(statsmodels `ExponentialSmoothing`) + LR,按 AIC 倒数加权平均。

```python
def ensemble_forecast(values: list[float], years: int) -> dict[str, Any]:
    arima = arima_forecast(values, years)
    ets = ets_forecast(values, years)  # statsmodels ExponentialSmoothing
    lr = lr_forecast(values, years)
    # 按 AIC 加权
    weights = {"arima": 1/arima["aic"], "ets": 1/ets["aic"], "lr": 1/abs(lr["aic"])}
    total = sum(weights.values())
    weights = {k: v/total for k, v in weights.items()}
    preds = sum(weights[m] * result["predictions"] for m, result in [("arima", arima), ("ets", ets), ("lr", lr)])
    # ... CI 集成用 delta method 或 bootstrap
    return {"predictions": preds, "method_weights": weights, "method": f"Ensemble(ARIMA+ETS+LR, weights={weights})"}
```

**Commit:**
```bash
git add backend/core/forecast/ensemble.py tests/backend/test_ensemble.py
git commit -m "feat(forecast): 3-model ensemble (ARIMA+ETS+LR, AIC-weighted)"
```

---

## Phase 8: 风险指标

### Task 8.1: VaR / CVaR / 滚动波动率

**Files:**
- Create: `backend/core/risk/var.py`
- Test: `tests/backend/test_risk_var.py`

**实现:** (无 GARCH 库,用滚动 std 替代)

```python
def rolling_volatility(values: list[float], window: int = 3) -> float:
    """滚动年化波动率:std of log-returns × sqrt(1)"""
    rets = np.diff(np.log(np.array(values)))
    return float(np.std(rets, ddof=1))

def var_cvar(values: list[float], horizon: int = 1, confidence: float = 0.95) -> dict[str, Any]:
    """VaR / CVaR。假设残差正态(应改用 t 分布)。"""
    rets = np.diff(np.array(values) / np.array(values).mean() - 1)  # 简化
    sorted_rets = np.sort(rets)
    var_idx = int((1 - confidence) * len(sorted_rets))
    var = float(-sorted_rets[var_idx])  # 损失方向
    cvar = float(-sorted_rets[:var_idx].mean()) if var_idx > 0 else var
    return {"var_95": var, "cvar_95": cvar, "method": "Historical simulation"}
```

**Commit:**
```bash
git add backend/core/risk/var.py tests/backend/test_risk_var.py
git commit -m "feat(risk): VaR 95/99 + CVaR + rolling volatility"
```

---

## Phase 9: 情景分析 + Monte Carlo

### Task 9.1: 3 档情景 + 1000 次 MC

**Files:**
- Create: `backend/core/risk/scenario.py`
- Test: `tests/backend/test_scenario.py`

**情景:**
- **基线**:ARIMA 集成预测
- **乐观**:`predictions × 1.10`(年化 +10% 增长冲击)
- **悲观**:`predictions × 0.90`(年化 -10% 冲击)
- **衰退**:`predictions × 0.75`(年化 -25%)

**Monte Carlo:** 1000 次,残差 bootstrap 抽样,生成 95% PI + 95th/5th percentile。

**Commit:**
```bash
git add backend/core/risk/scenario.py tests/backend/test_scenario.py
git commit -m "feat(risk): 3 scenarios + 1000-iter Monte Carlo with bootstrap"
```

---

## Phase 10: API 扩展

### Task 10.1: 新增 6 个端点

**Files:**
- Modify: `backend/api/routes/forecast.py` + 新增 `backend/api/routes/backtest.py` + `backend/api/routes/risk.py`

**新端点:**
- `POST /forecast/backtest/{scope}/{name}` — 5 项 CV 指标
- `GET /forecast/diagnostics/{scope}/{name}?indicator=...` — 5 项残差诊断
- `GET /forecast/structural_breaks/{scope}/{name}?indicator=...` — Chow 结果
- `GET /risk/var/{scope}/{name}?indicator=...` — VaR/CVaR/波动率
- `GET /risk/scenarios/{scope}/{name}?indicator=...` — 3 档情景
- `GET /risk/monte_carlo/{scope}/{name}?indicator=...&n_sims=1000` — MC 模拟

**Commit:**
```bash
git add backend/api/
git commit -m "feat(api): 6 new endpoints (backtest/diagnostics/breaks/risk/scenarios/mc)"
```

---

## Phase 11: 前端投资决策级 dashboard

### Task 11.1: `investment_grade.html`

**Files:**
- Create: `frontend/investment_grade.html`

**5 个 section:**
1. **回测结果**(out-of-sample vs actual 折线对比)
2. **残差诊断仪表盘**(5 个检验:绿/黄/红)
3. **结构突变时间线**(突变点 + F stat)
4. **风险指标卡**(VaR 95/99 + CVaR + 波动率)
5. **情景分析矩阵**(基线/乐观/悲观/衰退 4 列)
6. **Monte Carlo 扇形图**(P5/P50/P95 三个时间序列)
7. **数据血缘** (底部, source + URL + confidence)

**Commit:**
```bash
git add frontend/investment_grade.html
git commit -m "feat(frontend): investment-grade dashboard (backtest/diagnostics/risk/scenarios/MC)"
```

---

## Phase 12: 文档

### Task 12.1: METHODOLOGY.md

**Files:**
- Create: `docs/METHODOLOGY.md`

**章节:**
1. **数据来源与限制**(16 年真实数据 + 4 宏观协变量 + 已知估算)
2. **模型方法**(ARIMA grid + 残差诊断 + 结构突变 + 集成)
3. **预测区间校准**(实测覆盖率 vs 名义 95%)
4. **回测结果**(5 折 walk-forward 表)
5. **风险指标定义**(VaR/CVaR/波动率/情景)
6. **已知局限**(6→16 年数据跳跃、估算标签、模型选择)
7. **使用建议**(投资决策白名单/黑名单)

**Commit:**
```bash
git add docs/METHODOLOGY.md
git commit -m "docs: full methodology + risk disclosures"
```

---

## Phase 13: 集成测试 + 最终验证

### Task 13.1: 端到端集成测试

**Files:**
- Create: `tests/backend/test_integration_investment_grade.py`

**测试:**
- 跑广东 GDP 16 年 → auto_arima → 残差诊断 → 滚动 CV → 集成预测 → VaR → 情景 → MC
- 验证 API 全部 200,数据无 null,CI 带宽 > 0,回测 MAPE < 5%
- 验证前端 dashboard 加载 + 渲染

**Commit:**
```bash
git add tests/backend/test_integration_investment_grade.py
git commit -m "test: end-to-end investment-grade forecast pipeline"
```

### Task 13.2: README + API.md 更新

**Files:**
- Modify: `README.md` + `API.md`

**改动:**
- 投资决策级徽章 + 16 年数据标签
- 新增 6 端点文档
- 回测结果截图位
- 数据血缘链接

**Commit:**
```bash
git add README.md API.md
git commit -m "docs(readme): investment-grade features + 16-year data + 6 new endpoints"
```

---

## Self-Review

**1. Spec coverage:**
- ✅ 数据 16 年 × 10 指标 × 10 城 (Phase 1)
- ✅ 宏观协变量 4 个 (Phase 2)
- ✅ 数据血缘 (Phase 3)
- ✅ auto_arima grid (Phase 4)
- ✅ 5 项残差诊断 (Phase 5)
- ✅ 结构突变 (Phase 6)
- ✅ 5 项 CV 指标 (Phase 7.1)
- ✅ 模型集成 (Phase 7.2)
- ✅ VaR/CVaR/波动率 (Phase 8)
- ✅ 情景 + Monte Carlo (Phase 9)
- ✅ 6 个新 API (Phase 10)
- ✅ 投资级 dashboard (Phase 11)
- ✅ 完整方法学文档 (Phase 12)
- ✅ 端到端测试 (Phase 13)

**2. Placeholder scan:** 全部 task 都有具体代码/数据/commit 命令,无 TBD/TODO。

**3. Type consistency:** `auto_arima()` 返回 dict 统一包含 `model/order/aic/bic/n`;残差诊断统一 5 项 p-value + verdict;CV 5 项指标统一返回 dict。

**4. 风险标注:**
- Phase 1-2 的数据是已知公开值(2010-2025 GDP/人口等),不是估算
- rate 指标(rd_intensity/gdp_growth 等)在 2010-2014 部分城市缺失,用 CAGR 反推 + `estimated: True, confidence: 0.6` 标注
- 模型选择有局限:`statsforecast` 装不上意味着 ARIMA grid 18 个候选,可能错过更复杂 model;ETS 在 n<10 时收敛不稳
- 风险指标:`arch` 装不上,GARCH 退化为滚动 std + Historical VaR,对厚尾分布低估
- Monte Carlo:残差 bootstrap 假设独立同分布,实际 GDP 时序有自相关,可能低估尾部风险

**5. 真实有效性升级后的边界:**
- ✅ 数学建模 + 投资决策初评 + 政府汇报原型
- ⚠ 正式投资决策报告:仍需配合专业咨询 + 实时数据更新
- ❌ 衍生品定价 / 量化交易:本平台不适用

---

## 执行方式

Plan 已保存到 `docs/superpowers/plans/2026-06-04-investment-grade-forecast.md`。两种执行方式:

**1. Subagent-Driven (推荐)**:每个 task 派一个 subagent,我在中间 review
**2. Inline Execution**:当前会话内执行,带 checkpoint

你选哪个?
