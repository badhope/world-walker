"""
省份聚合 + 预测 - 把"按城市的历史数据"按所属省份聚合,
再用 ARIMA(若可用)/ 线性回归 + t 分布置信区间预测未来 N 年。

设计:
- 绝对量(GDP / population / fiscal_revenue / supplier_count)按省份内
  各城市求和。
- 率(rd_intensity / industry_high_tech_ratio / gdp_growth / data_quality)
  按省份内人口加权(以 population 为权重)。
- 预测:优先 statsforecast.AutoARIMA,fallback sklearn LinearRegression +
  t 分布预测区间(基于残差标准误 + 杠杆修正 + t(0.975, df=n-2))。
- 所有结果带 MAE / MAPE / R² 指标,让"过去的发展找规律"可见可量化。
"""

import logging
import math
from collections import defaultdict
from typing import Any

import numpy as np
import pandas as pd

from backend.data.city_data import get_all_forecast_cities, get_historical_data

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# 指标分类 — 决定聚合方式
# --------------------------------------------------------------------------- #

# 绝对量:省份值 = sum(各城)
_ABSOLUTE_INDICATORS = frozenset(
    {
        "gdp",
        "population",
        "fiscal_revenue",
        "supplier_count",
        "land_price",  # 加权平均更合理,但 sum 也能解读为"全省土地市场总量"
    }
)

# 率:省份值 = 加权平均,权重 = 同年同城市 population
_RATE_INDICATORS = frozenset(
    {
        "rd_intensity",
        "industry_high_tech_ratio",
        "gdp_growth",
        "data_quality",
        "rd_subsidy",
        "local_support_rate",
        "policy_coverage",
        "tax_reduction",
    }
)


def aggregate_indicator(aggregation: str) -> str:
    """返回 'sum' / 'weighted_avg' / 'avg'(默认),由调用方决定如何聚合"""
    if aggregation in ("sum", "weighted_avg", "avg"):
        return aggregation
    if aggregation in _ABSOLUTE_INDICATORS:
        return "sum"
    if aggregation in _RATE_INDICATORS:
        return "weighted_avg"
    return "avg"


# --------------------------------------------------------------------------- #
# 省份→城市 反向索引
# --------------------------------------------------------------------------- #


def _build_province_index() -> dict[str, list[str]]:
    """从 HISTORICAL_DATA + CityConfig 反推 city -> province 映射。
    注:CITY_DATA 顶层 dict 没省信息,但 CityConfig / CityDataManager 有。
    这里直接从 cities.yaml 取真实映射。
    """
    try:
        import yaml

        with open("data/cities/cities.yaml", encoding="utf-8") as f:
            doc = yaml.safe_load(f)
    except Exception as e:
        logger.warning("cities.yaml 读取失败,降级为单城省份: %s", e)
        return {}

    province_of: dict[str, str] = {}
    for name, info in doc.get("cities", {}).items():
        province_of[name] = info.get("province", "")

    out: dict[str, list[str]] = defaultdict(list)
    for city, prov in province_of.items():
        if prov:
            out[prov].append(city)
    return dict(out)


_PROVINCE_INDEX: dict[str, list[str]] | None = None


def get_province_index() -> dict[str, list[str]]:
    """省份 → 城市列表(惰性初始化)"""
    global _PROVINCE_INDEX
    if _PROVINCE_INDEX is None:
        _PROVINCE_INDEX = _build_province_index()
    return _PROVINCE_INDEX


# --------------------------------------------------------------------------- #
# 省级时序聚合
# --------------------------------------------------------------------------- #


def get_province_timeseries(
    province: str,
    indicator: str,
) -> pd.DataFrame:
    """
    把省份内所有城市的某指标按年聚合,返回 DataFrame[year, value, cities, sources]。

    - 绝对量 → 求和
    - 率指标 → 人口加权平均

    空省份返回空 DataFrame。
    """
    cities = get_province_index().get(province, [])
    if not cities:
        return pd.DataFrame(columns=["year", "value", "cities", "sources"])

    aggregation = aggregate_indicator(indicator)
    rows: list[dict[str, Any]] = []
    years = sorted(
        {int(item["year"]) for city in cities for item in get_historical_data(city).to_dict(orient="records")}
    )

    for year in years:
        city_values: list[tuple[float, float]] = []  # (value, weight)
        city_names: list[str] = []
        for city in cities:
            df = get_historical_data(city)
            if df.empty or indicator not in df.columns:
                continue
            row = df[df["year"] == year]
            if row.empty:
                continue
            v = row[indicator].iloc[0]
            if pd.isna(v):
                continue
            # 权重:率指标用 population 加权,绝对量用 1
            if aggregation == "weighted_avg":
                pop = row["population"].iloc[0] if "population" in df.columns else 1.0
                if pd.isna(pop) or pop <= 0:
                    pop = 1.0
                weight = float(pop)
            else:
                weight = 1.0
            city_values.append((float(v), weight))
            city_names.append(city)

        if not city_values:
            continue

        if aggregation == "sum":
            value = sum(v for v, _ in city_values)
        elif aggregation == "weighted_avg":
            total_w = sum(w for _, w in city_values)
            value = sum(v * w for v, w in city_values) / total_w if total_w > 0 else 0.0
        else:  # avg
            value = sum(v for v, _ in city_values) / len(city_values)

        rows.append(
            {
                "year": int(year),
                "value": round(float(value), 4),
                "cities": city_names,
                "sources": [f"{c}统计局年报" for c in city_names],
            }
        )

    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# 预测 — ARIMA 优先,LR + t 分布 CI fallback
# --------------------------------------------------------------------------- #


def _arima_forecast(values: list[float], years: int) -> dict[str, Any] | None:
    """优先 statsforecast.AutoARIMA,失败返回 None 走 fallback。"""
    try:
        from statsforecast import StatsForecast
        from statsforecast.models import AutoARIMA

        df = pd.DataFrame(
            {
                "ds": pd.date_range(start="2020-01-01", periods=len(values), freq="YE"),
                "y": [float(v) for v in values],
            }
        )
        sf = StatsForecast(models=[AutoARIMA(season_length=1)], freq="YE")
        sf.fit(df)
        out = sf.predict(h=years, level=[80, 95])
        # statsforecast 列名: AutoARIMA / AutoARIMA-lo-80 / AutoARIMA-hi-80
        col_mean = "AutoARIMA"
        # 不同版本字段名不同,做兼容
        candidates_lo95 = [c for c in out.columns if "lo-95" in c.lower()]
        candidates_hi95 = [c for c in out.columns if "hi-95" in c.lower()]
        lo = out[candidates_lo95[0]].tolist() if candidates_lo95 else out[col_mean].tolist()
        hi = out[candidates_hi95[0]].tolist() if candidates_hi95 else out[col_mean].tolist()
        mean = out[col_mean].tolist()
        return {
            "predictions": [float(x) for x in mean],
            "lower_95": [float(x) for x in lo],
            "upper_95": [float(x) for x in hi],
            "method": "AutoARIMA (statsforecast)",
        }
    except Exception as e:
        logger.info("ARIMA fallback 触发: %s", e)
        return None


def _linear_regression_forecast(values: list[float], years: int, confidence: float = 0.95) -> dict[str, Any]:
    """
    简单 OLS + t 分布预测区间。
    PI = ŷ ± t(α/2, n-2) · σ̂ · sqrt(1 + 1/n + (x_new - x̄)² / Sxx)
    """
    n = len(values)
    if n < 3:
        return {
            "predictions": [float(values[-1])] * years,
            "lower_95": [float(values[-1])] * years,
            "upper_95": [float(values[-1])] * years,
            "method": "Insufficient data (<3 points)",
        }

    from sklearn.linear_model import LinearRegression

    x = np.arange(n).reshape(-1, 1).astype(float)
    y = np.array(values, dtype=float)

    model = LinearRegression()
    model.fit(x, y)
    y_hat = model.predict(x)
    resid = y - y_hat
    dof = n - 2
    sigma = float(np.sqrt(np.sum(resid**2) / dof))  # 残差标准误

    x_mean = float(x.mean())
    sxx = float(np.sum((x - x_mean) ** 2))
    slope = float(model.coef_[0])
    intercept = float(model.intercept_)

    # 拟合优度
    ss_res = float(np.sum(resid**2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    mae = float(np.mean(np.abs(resid)))
    mape = float(np.mean(np.abs(resid / np.where(y == 0, 1.0, y))) * 100)

    # 置信区间临界值
    try:
        from scipy import stats

        t_crit = float(stats.t.ppf(0.5 + confidence / 2, dof))
    except Exception:
        t_crit = 1.96  # 退化

    future_x = np.arange(n, n + years).reshape(-1, 1).astype(float)
    preds = model.predict(future_x)

    lowers, uppers = [], []
    for fx in future_x.flatten():
        leverage = 1.0 + 1.0 / n + (fx - x_mean) ** 2 / sxx if sxx > 0 else 1.0
        half_width = t_crit * sigma * math.sqrt(leverage)
        lowers.append(float(preds[0]))  # 占位,下面覆盖
        uppers.append(float(preds[0]))

    # 重新写,免得上面占位
    lowers = []
    uppers = []
    for fx, p in zip(future_x.flatten(), preds):
        leverage = 1.0 + 1.0 / n + (fx - x_mean) ** 2 / sxx if sxx > 0 else 1.0
        half_width = t_crit * sigma * math.sqrt(leverage)
        lowers.append(float(p - half_width))
        uppers.append(float(p + half_width))

    return {
        "predictions": [float(x) for x in preds],
        "lower_95": lowers,
        "upper_95": uppers,
        "method": "Linear Regression (OLS + t-distribution 95% PI)",
        "metrics": {
            "r_squared": round(r2, 4),
            "mae": round(mae, 4),
            "mape_pct": round(mape, 4),
            "slope_per_year": round(slope, 4),
            "intercept": round(intercept, 4),
            "residual_std": round(sigma, 4),
            "t_critical_95": round(t_crit, 4),
            "n_points": n,
        },
    }


def forecast_series(
    values: list[float],
    years: int,
    start_year: int,
    confidence: float = 0.95,
) -> dict[str, Any]:
    """
    主入口:对一段历史时序做未来 years 年预测。
    返回 {predictions[], lower_95[], upper_95[], method, metrics?, years[]}
    """
    if not values or len(values) < 2:
        return {
            "predictions": [0.0] * years,
            "lower_95": [0.0] * years,
            "upper_95": [0.0] * years,
            "method": "Insufficient data",
            "years": list(range(start_year + 1, start_year + 1 + years)),
        }

    # 优先 ARIMA
    arima = _arima_forecast(values, years)
    if arima is not None:
        arima["years"] = list(range(start_year + 1, start_year + 1 + years))
        # ARIMA 不带回 metrics,补充 R²/MAE/MAPE 用于历史拟合
        try:
            from sklearn.linear_model import LinearRegression

            n = len(values)
            x = np.arange(n).reshape(-1, 1).astype(float)
            y = np.array(values, dtype=float)
            lr = LinearRegression().fit(x, y)
            resid = y - lr.predict(x)
            ss_res = float(np.sum(resid**2))
            ss_tot = float(np.sum((y - y.mean()) ** 2))
            arima["metrics"] = {
                "r_squared": round(1.0 - ss_res / ss_tot, 4) if ss_tot > 0 else 0.0,
                "mae": round(float(np.mean(np.abs(resid))), 4),
                "mape_pct": round(float(np.mean(np.abs(resid / np.where(y == 0, 1.0, y))) * 100), 4),
                "n_points": n,
            }
        except Exception:
            arima["metrics"] = {"n_points": len(values)}
        return arima

    # fallback LR
    lr_result = _linear_regression_forecast(values, years, confidence)
    lr_result["years"] = list(range(start_year + 1, start_year + 1 + years))
    return lr_result


# --------------------------------------------------------------------------- #
# 高层:对某 city/province 的某 indicator 做端到端预测
# --------------------------------------------------------------------------- #


def forecast_city_indicator(
    city: str,
    indicator: str,
    years: int = 5,
) -> dict[str, Any]:
    """对单个城市 × 某指标做未来 years 年预测(支持 5 个核心时序指标)"""
    cities = get_all_forecast_cities()
    if city not in cities:
        return {"error": f"City '{city}' not in forecast registry {cities}"}

    df = get_historical_data(city)
    if df.empty or indicator not in df.columns:
        return {"error": f"Indicator '{indicator}' not available for {city}"}

    hist = df[["year", indicator]].dropna()
    if hist.empty:
        return {"error": f"No historical data for {city}/{indicator}"}

    values = hist[indicator].astype(float).tolist()
    start_year = int(hist["year"].max())
    forecast = forecast_series(values, years, start_year)

    # 计算 CAGR(历史 + 预测)
    cagr_hist = _cagr(values[0], values[-1], len(values) - 1) if len(values) >= 2 else 0.0
    cagr_forecast = (
        _cagr(forecast["predictions"][0], forecast["predictions"][-1], len(forecast["predictions"]) - 1)
        if len(forecast["predictions"]) >= 2
        else 0.0
    )

    return {
        "scope": "city",
        "city": city,
        "indicator": indicator,
        "historical_years": hist["year"].astype(int).tolist(),
        "historical_values": [round(v, 4) for v in values],
        "forecast_years": forecast["years"],
        "forecast_values": [round(v, 4) for v in forecast["predictions"]],
        "lower_95": [round(v, 4) for v in forecast["lower_95"]],
        "upper_95": [round(v, 4) for v in forecast["upper_95"]],
        "method": forecast["method"],
        "metrics": forecast.get("metrics", {}),
        "growth": {
            "historical_cagr_pct": round(cagr_hist, 4),
            "forecast_cagr_pct": round(cagr_forecast, 4),
        },
    }


def forecast_province_indicator(
    province: str,
    indicator: str,
    years: int = 5,
) -> dict[str, Any]:
    """对某省 × 某指标做未来 years 年预测。先按城市聚合,再预测。"""
    if province not in get_province_index():
        return {"error": f"Province '{province}' not in registry", "available": list(get_province_index().keys())}

    df = get_province_timeseries(province, indicator)
    if df.empty:
        return {"error": f"No aggregated data for {province}/{indicator}"}

    values = df["value"].astype(float).tolist()
    start_year = int(df["year"].max())
    forecast = forecast_series(values, years, start_year)

    cagr_hist = _cagr(values[0], values[-1], len(values) - 1) if len(values) >= 2 else 0.0
    cagr_forecast = (
        _cagr(forecast["predictions"][0], forecast["predictions"][-1], len(forecast["predictions"]) - 1)
        if len(forecast["predictions"]) >= 2
        else 0.0
    )

    return {
        "scope": "province",
        "province": province,
        "indicator": indicator,
        "aggregation": aggregate_indicator(indicator),
        "included_cities": df["cities"].iloc[-1] if not df.empty else [],
        "historical_years": df["year"].astype(int).tolist(),
        "historical_values": [round(v, 4) for v in values],
        "forecast_years": forecast["years"],
        "forecast_values": [round(v, 4) for v in forecast["predictions"]],
        "lower_95": [round(v, 4) for v in forecast["lower_95"]],
        "upper_95": [round(v, 4) for v in forecast["upper_95"]],
        "method": forecast["method"],
        "metrics": forecast.get("metrics", {}),
        "growth": {
            "historical_cagr_pct": round(cagr_hist, 4),
            "forecast_cagr_pct": round(cagr_forecast, 4),
        },
    }


def forecast_all_provinces(
    indicator: str,
    years: int = 5,
) -> dict[str, Any]:
    """7 个省份 × 1 个指标 批量预测。"""
    provinces = sorted(get_province_index().keys())
    out: dict[str, Any] = {
        "indicator": indicator,
        "forecast_horizon_years": years,
        "aggregation": aggregate_indicator(indicator),
        "provinces": {},
        "comparison": [],
    }
    for prov in provinces:
        result = forecast_province_indicator(prov, indicator, years)
        if "error" not in result:
            out["provinces"][prov] = {
                "historical_years": result["historical_years"],
                "historical_values": result["historical_values"],
                "forecast_years": result["forecast_years"],
                "forecast_values": result["forecast_values"],
                "lower_95": result["lower_95"],
                "upper_95": result["upper_95"],
                "method": result["method"],
                "metrics": result["metrics"],
                "included_cities": result["included_cities"],
                "growth": result["growth"],
            }
            out["comparison"].append(
                {
                    "province": prov,
                    "latest_value": result["historical_values"][-1],
                    "forecast_value": result["forecast_values"][-1],
                    "forecast_cagr_pct": result["growth"]["forecast_cagr_pct"],
                    "method": result["method"],
                }
            )

    # 排序:末年预测值降序
    out["comparison"].sort(key=lambda r: r["forecast_value"], reverse=True)
    return out


# --------------------------------------------------------------------------- #
# 工具
# --------------------------------------------------------------------------- #


def _cagr(start: float, end: float, years: int) -> float:
    if start is None or end is None or start <= 0 or years <= 0:
        return 0.0
    try:
        result: float = ((end / start) ** (1 / years) - 1) * 100
        return result
    except (ValueError, ZeroDivisionError):
        return 0.0


SUPPORTED_INDICATORS = sorted(_ABSOLUTE_INDICATORS | _RATE_INDICATORS)
