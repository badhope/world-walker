"""
投资决策级预测引擎 — Phase 4-7 整合实现。

组件:
1. auto_arima: statsmodels AIC-driven grid search
2. ets: statsmodels ExponentialSmoothing
3. linear_regression: sklearn OLS + t 分布 PI (fallback)
4. diagnostics: ADF / KPSS / Ljung-Box / Jarque-Bera / Breusch-Pagan
5. structural_breaks: Chow test
6. backtest: 滚动 walk-forward + 5 项指标 (MAPE/RMSE/MASE/sMAPE/coverage)
7. ensemble: 3 模型 AIC-weighted 集成

设计:
- 模块独立,可单独使用
- `forecast_full_pipeline()` 是主入口,串起所有步骤
- 全部带真实数学(非占位)
"""
from __future__ import annotations

import itertools
import logging
import math
import warnings
from typing import Any

import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression

from backend.core.engine_stack import (
    pmdarima_available,
    primary_arima_backend,
    statsforecast_available,
)

logger = logging.getLogger(__name__)

_ARIMA_BACKEND = primary_arima_backend()
logger.info("Forecast engine: ARIMA backend = %s", _ARIMA_BACKEND)


# --------------------------------------------------------------------------- #
# 1. auto_arima — statsmodels AIC-driven grid search (fallback)
# --------------------------------------------------------------------------- #


def auto_arima(values: list[float], max_p: int = 2, max_d: int = 1, max_q: int = 2) -> dict[str, Any]:
    """
    AIC 驱动的 grid search。

    网格:(p, d, q) ∈ {0..max_p} × {0..max_d} × {0..max_q},但排除 (0,0,0)。
    返回 AIC 最小的模型 + (p, d, q) + AIC + BIC + 残差。

    适合样本量 n ≥ 8;样本太小直接走 fallback。
    """
    y = np.asarray(values, dtype=float)
    n = len(y)
    if n < 5:
        return {"model": None, "order": None, "aic": float("inf"), "bic": float("inf"), "n": n, "reason": "n<5", "backend": "statsmodels"}

    from statsmodels.tsa.arima.model import ARIMA

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
                if np.isfinite(m.aic) and m.aic < best_aic:
                    best_aic = m.aic
                    best_order = (p, d, q)
                    best_model = m
        except Exception as e:
            logger.debug("ARIMA(%d,%d,%d) failed: %s", p, d, q, e)
            continue

    if best_model is None:
        return {"model": None, "order": None, "aic": float("inf"), "bic": float("inf"), "n": n, "reason": "all orders failed", "backend": "statsmodels"}
    return {
        "model": best_model,
        "order": best_order,
        "aic": float(best_aic),
        "bic": float(best_model.bic),
        "n": n,
        "backend": "statsmodels",
    }


# --------------------------------------------------------------------------- #
# 1b. auto_arima_native — 高级路径(statsforecast > pmdarima > statsmodels)
# --------------------------------------------------------------------------- #


def auto_arima_native(values: list[float], max_p: int = 5, max_d: int = 2, max_q: int = 5) -> dict[str, Any]:
    """
    高级 AutoARIMA — 优先用 statsforecast(快 + 多季节 + 节假日),
    回退到 pmdarima,再回退到 statsmodels grid。

    返回 dict 形态与 statsmodels auto_arima 兼容(供 arima_forecast / ensemble_forecast 使用)。
    """
    y = np.asarray(values, dtype=float)
    n = len(y)
    if n < 5:
        return {"model": None, "order": None, "aic": float("inf"), "bic": float("inf"), "n": n, "reason": "n<5", "backend": _ARIMA_BACKEND}

    # --- 路径 1: statsforecast ---
    if statsforecast_available():
        try:
            import pandas as pd
            from statsforecast import StatsForecast
            from statsforecast.models import AutoARIMA as SF_AutoARIMA

            logger.debug("ARIMA: using statsforecast.AutoARIMA")
            sf = StatsForecast(models=[SF_AutoARIMA(season_length=1)], freq=1, n_jobs=1)
            df = pd.DataFrame(
                {
                    "unique_id": ["y"] * n,
                    "ds": pd.date_range("2010-01-01", periods=n, freq="YS"),
                    "y": y,
                }
            )
            sf.fit(df)
            sf_model = sf.models[0]
            order = tuple(sf_model.order) if hasattr(sf_model, "order") and sf_model.order else None
            aic = float(getattr(sf_model, "aic", float("inf"))) if order else float("inf")
            bic = float(getattr(sf_model, "bic", float("inf"))) if order else float("inf")
            if order is None:
                raise RuntimeError("statsforecast did not return an order")
            return {
                "model": sf_model,
                "order": order,
                "aic": aic,
                "bic": bic,
                "n": n,
                "backend": "statsforecast",
            }
        except Exception as e:
            logger.warning("statsforecast.AutoARIMA failed: %s, falling back", e)

    # --- 路径 2: pmdarima ---
    if pmdarima_available():
        try:
            import pmdarima as pm

            logger.debug("ARIMA: using pmdarima.auto_arima")
            m = pm.auto_arima(
                y,
                start_p=0,
                start_q=0,
                max_p=max_p,
                max_d=max_d,
                max_q=max_q,
                seasonal=False,
                stepwise=True,  # stepwise 比 grid 快且效果近似
                suppress_warnings=True,
                error_action="ignore",
                information_criterion="aic",
            )
            return {
                "model": m,
                "order": tuple(m.order),
                "aic": float(m.aic()),
                "bic": float(m.bic()),
                "n": n,
                "backend": "pmdarima",
            }
        except Exception as e:
            logger.warning("pmdarima.auto_arima failed: %s, falling back", e)

    # --- 路径 3: 现有 statsmodels grid (fallback) ---
    return auto_arima(values, max_p=2, max_d=1, max_q=2)


def arima_forecast(values: list[float], years: int, confidence: float = 0.95) -> dict[str, Any]:
    """
    用 auto_arima_native 选出的最佳模型预测未来 years 年。
    返回:{predictions, lower_ci, upper_ci, method, order, aic, bic}
    """
    fit = auto_arima_native(values)
    if fit["model"] is None:
        return {
            "predictions": [float(v) for v in values[-years:]] if values else [0.0] * years,
            "lower_ci": [0.0] * years,
            "upper_ci": [0.0] * years,
            "method": "ARIMA failed",
            "order": None,
            "aic": None,
            "bic": None,
        }

    backend = fit.get("backend", "statsmodels")
    model = fit["model"]
    n = len(values)
    y_arr = np.asarray(values, dtype=float)
    z = stats.norm.ppf(0.5 + confidence / 2)

    try:
        if backend == "statsforecast":
            # 重新 fit (单 series) 然后 predict h=years
            import pandas as pd
            from statsforecast import StatsForecast
            from statsforecast.models import AutoARIMA as SF_AutoARIMA

            sf = StatsForecast(models=[SF_AutoARIMA(season_length=1)], freq=1, n_jobs=1)
            df = pd.DataFrame(
                {
                    "unique_id": ["y"] * n,
                    "ds": pd.date_range("2010-01-01", periods=n, freq="YS"),
                    "y": y_arr,
                }
            )
            sf.fit(df)
            fc_df = sf.predict(h=years)
            col = "AutoARIMA" if "AutoARIMA" in fc_df.columns else fc_df.columns[-1]
            preds = [float(x) for x in fc_df[col].tolist()]
            # statsforecast 不带 conf_int → 用 in-sample 残差 std 算近似
            try:
                sf_model = sf.models[0]
                fitted = sf_model.fitted_values if hasattr(sf_model, "fitted_values") else None
                if fitted is not None and len(fitted) == n:
                    resid = y_arr - np.asarray(fitted)
                else:
                    raise RuntimeError("no fitted_values")
            except Exception:
                resid = np.diff(y_arr, prepend=y_arr[0])
            sigma = float(np.std(resid, ddof=1)) or 1.0
            lower = [p - z * sigma * math.sqrt(i + 1) for i, p in enumerate(preds)]
            upper = [p + z * sigma * math.sqrt(i + 1) for i, p in enumerate(preds)]

        elif backend == "pmdarima":
            fc = model.predict(n_periods=years, return_conf_int=True, alpha=1 - confidence)
            if isinstance(fc, tuple) and len(fc) == 2:
                preds_arr, ci = fc
                preds = [float(x) for x in preds_arr]
                lower = [float(x) for x in ci[:, 0]]
                upper = [float(x) for x in ci[:, 1]]
            else:
                preds = [float(x) for x in fc]
                resid_std = float(np.std(model.resid())) or 1.0
                lower = [p - z * resid_std * math.sqrt(i + 1) for i, p in enumerate(preds)]
                upper = [p + z * resid_std * math.sqrt(i + 1) for i, p in enumerate(preds)]

        else:
            # statsmodels (fallback)
            fc = model.get_forecast(steps=years)
            ci = np.asarray(fc.conf_int(alpha=1 - confidence))
            preds = [float(x) for x in fc.predicted_mean.tolist()]
            lower = [float(x) for x in ci[:, 0]]
            upper = [float(x) for x in ci[:, 1]]

    except Exception as e:
        logger.warning("ARIMA predict failed (%s backend): %s", backend, e)
        last = float(values[-1]) if values else 0.0
        return {
            "predictions": [last] * years,
            "lower_ci": [last * 0.95] * years,
            "upper_ci": [last * 1.05] * years,
            "method": f"ARIMA predict failed ({backend})",
            "order": list(fit["order"]) if fit["order"] else None,
            "aic": fit["aic"],
            "bic": fit["bic"],
        }

    return {
        "predictions": preds,
        "lower_ci": lower,
        "upper_ci": upper,
        "method": f"ARIMA{list(fit['order'])} ({backend}, AIC={fit['aic']:.1f})",
        "order": list(fit["order"]) if fit["order"] else None,
        "aic": fit["aic"],
        "bic": fit["bic"],
    }


# --------------------------------------------------------------------------- #
# 2. ETS — Exponential Smoothing (statsmodels)
# --------------------------------------------------------------------------- #


def ets_forecast(values: list[float], years: int, confidence: float = 0.95) -> dict[str, Any]:
    """
    Holt-Winters 加法趋势 / 乘法趋势。n<8 时用简单指数平滑 (SES)。
    """
    n = len(values)
    if n < 4:
        return {
            "predictions": [float(v) for v in values[-years:]] if values else [0.0] * years,
            "lower_ci": [0.0] * years,
            "upper_ci": [0.0] * years,
            "method": "ETS (insufficient data)",
            "aic": float("inf"),
        }
    from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing

    y = np.asarray(values, dtype=float)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if n >= 8:
                # 尝试 Holt's linear trend,失败回退 SES
                try:
                    model = ExponentialSmoothing(y, trend="add", seasonal=None, initialization_method="estimated").fit(
                        optimized=True
                    )
                except Exception:
                    model = SimpleExpSmoothing(y, initialization_method="estimated").fit(optimized=True)
            else:
                model = SimpleExpSmoothing(y, initialization_method="estimated").fit(optimized=True)

        fc = model.forecast(years)
        if hasattr(fc, "values"):
            fc_arr = fc.values
        else:
            fc_arr = np.asarray(fc)
        residuals = model.resid
        if hasattr(residuals, "values"):
            residuals = residuals.values
        sigma = float(np.std(residuals, ddof=1)) if len(residuals) > 1 else 0.0
        # 简单 PI:±1.96·σ 随时间放大
        z = stats.norm.ppf(0.5 + confidence / 2)
        lower = [float(fc_arr[i] - z * sigma * math.sqrt(i + 1)) for i in range(years)]
        upper = [float(fc_arr[i] + z * sigma * math.sqrt(i + 1)) for i in range(years)]
        aic = float(getattr(model, "aic", float("inf")))
        return {
            "predictions": [float(x) for x in fc.tolist()],
            "lower_ci": lower,
            "upper_ci": upper,
            "method": f"ETS (statsmodels, AIC={aic:.1f})",
            "aic": aic,
        }
    except Exception as e:
        logger.warning("ETS failed: %s, fallback to naive", e)
        return {
            "predictions": [float(values[-1])] * years,
            "lower_ci": [float(values[-1] * 0.95)] * years,
            "upper_ci": [float(values[-1] * 1.05)] * years,
            "method": f"ETS failed ({e})",
            "aic": float("inf"),
        }


# --------------------------------------------------------------------------- #
# 3. Linear Regression + t-distribution PI (fallback)
# --------------------------------------------------------------------------- #


def linear_regression_forecast(values: list[float], years: int, confidence: float = 0.95) -> dict[str, Any]:
    """
    OLS + t 分布 PI(基于残差标准误 + 杠杆修正)。
    用于样本太小或 ARIMA 失败时 fallback。
    """
    n = len(values)
    if n < 3:
        return {
            "predictions": [float(values[-1])] * years if values else [0.0] * years,
            "lower_ci": [0.0] * years,
            "upper_ci": [0.0] * years,
            "method": "LR (insufficient data)",
            "aic": float("inf"),
            "bic": float("inf"),
        }
    x = np.arange(n).reshape(-1, 1).astype(float)
    y = np.array(values, dtype=float)
    model = LinearRegression().fit(x, y)
    y_hat = model.predict(x)
    resid = y - y_hat
    dof = n - 2
    sigma = float(np.sqrt(np.sum(resid**2) / dof))
    x_mean = float(x.mean())
    sxx = float(np.sum((x - x_mean) ** 2))
    t_crit = float(stats.t.ppf(0.5 + confidence / 2, dof))

    future_x = np.arange(n, n + years).reshape(-1, 1).astype(float)
    preds = model.predict(future_x)
    lowers, uppers = [], []
    for fx, p in zip(future_x.flatten(), preds):
        leverage = 1.0 + 1.0 / n + (fx - x_mean) ** 2 / sxx if sxx > 0 else 1.0
        hw = t_crit * sigma * math.sqrt(leverage)
        lowers.append(float(p - hw))
        uppers.append(float(p + hw))

    # AIC 估计:对 n 个残差,n+2 参数(α,β,σ²)
    rss = float(np.sum(resid**2))
    # 防止 rss=0 时 log(0) 报错
    rss_safe = max(rss, 1e-9 * n) if n > 0 else 1.0
    aic = n * math.log(rss_safe / n) + 2 * 2  # 简化
    bic = n * math.log(rss_safe / n) + math.log(max(n, 1)) * 2
    return {
        "predictions": [float(x) for x in preds],
        "lower_ci": lowers,
        "upper_ci": uppers,
        "method": f"LinearRegression (OLS + t{confidence*100:.0f}%)",
        "aic": float(aic),
        "bic": float(bic),
    }


# --------------------------------------------------------------------------- #
# 4. Ensemble — AIC-weighted
# --------------------------------------------------------------------------- #


def ensemble_forecast(
    arima: dict[str, Any],
    ets: dict[str, Any],
    lr: dict[str, Any],
) -> dict[str, Any]:
    """
    3 模型集成,按 1/AIC 加权(归一化)。
    CI 集成用 delta method 简化版:各 CI 的加权。
    """
    weights = {}
    for name, r in [("arima", arima), ("ets", ets), ("lr", lr)]:
        aic = r.get("aic", float("inf"))
        if aic is None or not np.isfinite(aic):
            weights[name] = 0.0
        else:
            # AIC 越小越好 → 权重 ∝ exp(-AIC/2) ≈ 1/AIC 简化
            weights[name] = 1.0 / max(abs(aic), 1e-6)
    total = sum(weights.values()) or 1.0
    weights = {k: v / total for k, v in weights.items()}

    n_pred = len(arima["predictions"])
    pred = [0.0] * n_pred
    lower = [0.0] * n_pred
    upper = [0.0] * n_pred
    for name, r in [("arima", arima), ("ets", ets), ("lr", lr)]:
        w = weights[name]
        for i in range(n_pred):
            pred[i] += w * r["predictions"][i]
            lower[i] += w * r["lower_ci"][i]
            upper[i] += w * r["upper_ci"][i]

    return {
        "predictions": pred,
        "lower_ci": lower,
        "upper_ci": upper,
        "method": "Ensemble(ARIMA+ETS+LR, AIC-weighted)",
        "weights": {k: round(v, 4) for k, v in weights.items()},
    }


# --------------------------------------------------------------------------- #
# 5. 残差诊断 — 5 项
# --------------------------------------------------------------------------- #


def run_diagnostics(values: list[float], order: tuple[int, int, int] | None = None) -> dict[str, Any]:
    """
    5 项残差诊断:
    1. ADF 平稳性
    2. KPSS 平稳性
    3. Ljung-Box 自相关
    4. Jarque-Bera 正态性
    5. Breusch-Pagan 异方差

    返回每项的 statistic / pvalue / 结论 + 综合 verdict。
    """
    n = len(values)
    out: dict[str, Any] = {"n": n, "tests": {}}

    if n < 8:
        return {"n": n, "tests": {}, "verdict": "INSUFFICIENT_DATA", "verdict_reason": f"n={n} < 8"}

    y = np.asarray(values, dtype=float)
    from statsmodels.stats.diagnostic import acorr_ljungbox, het_breuschpagan
    from statsmodels.stats.stattools import jarque_bera
    from statsmodels.tsa.stattools import adfuller, kpss

    # 1. ADF(原假设:有单位根 → 不平稳)
    try:
        adf_stat, adf_p, *_ = adfuller(y, autolag="AIC")
        out["tests"]["adf"] = {
            "statistic": round(float(adf_stat), 4),
            "pvalue": round(float(adf_p), 4),
            "stationary": adf_p < 0.05,
            "conclusion": "reject unit root (stationary)" if adf_p < 0.05 else "fail to reject (non-stationary)",
        }
    except Exception as e:
        out["tests"]["adf"] = {"error": str(e)}

    # 2. KPSS(原假设:无单位根 → 平稳)
    try:
        kpss_stat, kpss_p, *_ = kpss(y, regression="c", nlags="auto")
        out["tests"]["kpss"] = {
            "statistic": round(float(kpss_stat), 4),
            "pvalue": round(float(kpss_p), 4),
            "stationary": kpss_p > 0.05,
            "conclusion": "fail to reject (stationary)" if kpss_p > 0.05 else "reject (non-stationary)",
        }
    except Exception as e:
        out["tests"]["kpss"] = {"error": str(e)}

    # 拟合 ARIMA 拿残差(诊断的对象是残差)
    try:
        from statsmodels.tsa.arima.model import ARIMA

        if order is None:
            order = (1, 1, 0)  # 默认 random walk + drift
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m = ARIMA(y, order=order).fit()
        resid = np.asarray(m.resid)
    except Exception as e:
        out["verdict"] = "DIAGNOSTIC_FAILED"
        out["verdict_reason"] = f"ARIMA fit failed: {e}"
        return out

    # 3. Ljung-Box(原假设:无自相关)
    try:
        lb_result = acorr_ljungbox(resid, lags=[min(10, n // 5)], return_df=True)
        lb_stat = float(lb_result["lb_stat"].iloc[0])
        lb_p = float(lb_result["lb_pvalue"].iloc[0])
        out["tests"]["ljung_box"] = {
            "statistic": round(lb_stat, 4),
            "pvalue": round(lb_p, 4),
            "no_autocorrelation": lb_p > 0.05,
            "conclusion": "fail to reject (no autocorr)" if lb_p > 0.05 else "reject (autocorrelation present)",
        }
    except Exception as e:
        out["tests"]["ljung_box"] = {"error": str(e)}

    # 4. Jarque-Bera(原假设:正态)
    try:
        jb_stat, jb_p, skew, kurt = jarque_bera(resid)
        out["tests"]["jarque_bera"] = {
            "statistic": round(float(jb_stat), 4),
            "pvalue": round(float(jb_p), 4),
            "skewness": round(float(skew), 4),
            "kurtosis": round(float(kurt), 4),
            "normal": jb_p > 0.05,
            "conclusion": "fail to reject (normal)" if jb_p > 0.05 else "reject (non-normal)",
        }
    except Exception as e:
        out["tests"]["jarque_bera"] = {"error": str(e)}

    # 5. Breusch-Pagan(原假设:同方差)
    try:
        # 残差对原值回归,看异方差
        exog = np.column_stack([np.ones(n), np.arange(n)])
        bp_stat, bp_p, _, _ = het_breuschpagan(resid**2, exog)
        out["tests"]["breusch_pagan"] = {
            "statistic": round(float(bp_stat), 4),
            "pvalue": round(float(bp_p), 4),
            "homoscedastic": bp_p > 0.05,
            "conclusion": "fail to reject (homoscedastic)" if bp_p > 0.05 else "reject (heteroscedastic)",
        }
    except Exception as e:
        out["tests"]["breusch_pagan"] = {"error": str(e)}

    # 综合 verdict
    fails = 0
    for name, t in out["tests"].items():
        if "error" in t:
            continue
        # 转换 numpy.bool → python bool
        for key in ("stationary", "no_autocorrelation", "normal", "homoscedastic"):
            if key in t:
                t[key] = bool(t[key])
                if t[key] is False:
                    fails += 1
    if fails == 0:
        out["verdict"] = "PASS"
    elif fails <= 1:
        out["verdict"] = "WARN"
    else:
        out["verdict"] = "FAIL"
    out["verdict_reason"] = f"{fails} test(s) failed"

    return out


# --------------------------------------------------------------------------- #
# 6. Chow test — 结构突变检测
# --------------------------------------------------------------------------- #


def _rss(x: np.ndarray, y: np.ndarray) -> float:
    """OLS RSS"""
    n = len(y)
    if n < 2:
        return float("nan")
    x_mean = x.mean()
    y_mean = y.mean()
    sxx = float(np.sum((x - x_mean) ** 2))
    sxy = float(np.sum((x - x_mean) * (y - y_mean)))
    if sxx == 0:
        return float(np.sum((y - y_mean) ** 2))
    slope = sxy / sxx
    intercept = y_mean - slope * x_mean
    y_hat = intercept + slope * x
    return float(np.sum((y - y_hat) ** 2))


def chow_test(values: list[float], breakpoint_idx: int) -> dict[str, Any]:
    """单点 Chow test。原假设:无结构突变。"""
    y = np.array(values)
    n = len(y)
    if breakpoint_idx < 2 or breakpoint_idx > n - 2:
        return {"f_stat": None, "pvalue": None, "structural_break": False, "reason": "invalid breakpoint"}
    x = np.arange(n)
    rss_full = _rss(x, y)
    rss1 = _rss(x[:breakpoint_idx], y[:breakpoint_idx])
    rss2 = _rss(x[breakpoint_idx:], y[breakpoint_idx:])
    rss_split = rss1 + rss2
    if rss_split == 0:
        return {"f_stat": 0.0, "pvalue": 1.0, "structural_break": False, "reason": "no residual variance"}
    k = 2
    f_stat = ((rss_full - rss_split) / k) / (rss_split / (n - 2 * k))
    pvalue = 1 - float(stats.f.cdf(f_stat, k, n - 2 * k))
    return {
        "f_stat": round(float(f_stat), 4),
        "pvalue": round(float(pvalue), 4),
        "structural_break": pvalue < 0.05,
        "conclusion": "reject no-break" if pvalue < 0.05 else "fail to reject no-break",
    }


def find_structural_breaks(values: list[float], min_segment: int = 3) -> list[dict[str, Any]]:
    """遍历所有候选断点,返回 p < 0.05 的显著突变点。"""
    n = len(values)
    breaks = []
    for i in range(min_segment, n - min_segment):
        result = chow_test(values, i)
        if result.get("structural_break"):
            result["breakpoint_idx"] = i
            breaks.append(result)
    return breaks


# --------------------------------------------------------------------------- #
# 7. 滚动 CV — 5 项指标
# --------------------------------------------------------------------------- #


def backtest_forecast(
    values: list[float],
    n_test: int = 3,
    model_func: Any | None = None,
) -> dict[str, Any]:
    """
    Walk-forward 滚动 CV。每次用前 n - k - n_test + 1 年的数据训练,预测未来 n_test 年。
    返回 5 项指标:MAPE, RMSE, MASE, sMAPE, Coverage。

    model_func: 一个函数 (values: list[float], years: int) -> {predictions, lower_ci, upper_ci}
    """
    n = len(values)
    if n < n_test + 4:
        return {"error": f"n={n} too small for n_test={n_test}", "metrics": {}}

    if model_func is None:

        def model_func(v, h):
            return arima_forecast(v, h)

    actuals: list[float] = []
    forecasts: list[float] = []
    lowers: list[float] = []
    uppers: list[float] = []

    for k in range(n_test, 0, -1):
        train = values[: n - k]
        actual = values[n - k]
        if len(train) < 4:
            continue
        try:
            result = model_func(train, 1)
            pred = result["predictions"][0]
            lo = result["lower_ci"][0]
            hi = result["upper_ci"][0]
        except Exception as e:
            logger.warning("backtest step %d failed: %s", k, e)
            continue
        actuals.append(actual)
        forecasts.append(pred)
        lowers.append(lo)
        uppers.append(hi)

    if not actuals:
        return {"error": "no successful backtest steps", "metrics": {}}

    a = np.array(actuals)
    f = np.array(forecasts)
    lo = np.array(lowers)
    hi = np.array(uppers)

    # 1. MAPE
    mape = float(np.mean(np.abs((a - f) / np.where(a == 0, 1.0, a))) * 100)
    # 2. RMSE
    rmse = float(np.sqrt(np.mean((a - f) ** 2)))
    # 3. MASE (mean(|actual - pred|) / mean(|actual_t - actual_{t-1}|))
    naive_err = np.mean(np.abs(np.diff(a)))
    mase = float(np.mean(np.abs(a - f)) / naive_err) if naive_err > 0 else float("inf")
    # 4. sMAPE
    smape = float(np.mean(2 * np.abs(a - f) / (np.abs(a) + np.abs(f) + 1e-9)) * 100)
    # 5. Coverage
    coverage = float(np.mean((a >= lo) & (a <= hi)) * 100)

    return {
        "n_test": len(actuals),
        "actuals": [float(x) for x in a],
        "forecasts": [float(x) for x in f],
        "metrics": {
            "MAPE_pct": round(mape, 4),
            "RMSE": round(rmse, 4),
            "MASE": round(mase, 4),
            "sMAPE_pct": round(smape, 4),
            "Coverage_pct": round(coverage, 4),
        },
    }


# --------------------------------------------------------------------------- #
# 8. 主入口:完整流水线
# --------------------------------------------------------------------------- #


def forecast_full_pipeline(
    values: list[float],
    start_year: int,
    years: int = 5,
    confidence: float = 0.95,
) -> dict[str, Any]:
    """
    投资决策级预测流水线:
    1. 三模型预测 (ARIMA + ETS + LR)
    2. 集成 (AIC-weighted)
    3. 残差诊断 (5 项)
    4. 结构突变 (Chow)
    5. 滚动 CV (5 项指标)
    6. CAGR + 增长率
    """
    if not values or len(values) < 4:
        return {"error": f"Insufficient data: n={len(values) if values else 0}"}

    # 1. 三模型
    arima = arima_forecast(values, years, confidence)
    ets = ets_forecast(values, years, confidence)
    lr = linear_regression_forecast(values, years, confidence)
    # 2. 集成
    ens = ensemble_forecast(arima, ets, lr)

    # 3. 残差诊断(基于 ARIMA 残差)
    order_raw = arima.get("order")
    order = tuple(order_raw) if order_raw else (1, 1, 0)
    diagnostics = run_diagnostics(values, order=order)

    # 4. 结构突变
    breaks = find_structural_breaks(values)

    # 5. 滚动 CV(用 ARIMA 跑)
    n_test = min(3, max(1, len(values) - 6))
    cv = backtest_forecast(values, n_test=n_test, model_func=lambda v, h: arima_forecast(v, h))

    # 6. CAGR
    n = len(values)
    hist_cagr = ((values[-1] / values[0]) ** (1 / (n - 1)) - 1) * 100 if values[0] > 0 else 0.0
    fc_cagr = ((ens["predictions"][-1] / values[-1]) ** (1 / years) - 1) * 100 if values[-1] > 0 else 0.0

    return {
        "models": {
            "arima": arima,
            "ets": ets,
            "linear_regression": lr,
        },
        "ensemble": ens,
        "diagnostics": diagnostics,
        "structural_breaks": breaks,
        "backtest": cv,
        "growth": {
            "historical_cagr_pct": round(hist_cagr, 4),
            "forecast_cagr_pct": round(fc_cagr, 4),
        },
        "years": list(range(start_year, start_year + years)),
        "n_history": n,
    }


if __name__ == "__main__":
    # 自检:深圳 GDP 16 年
    shenzhen_gdp = [9772, 11506, 12971, 14573, 16002, 17503, 19493, 22438, 25267, 26927, 27700, 30700, 32400, 34600, 36500, 38500]
    out = forecast_full_pipeline(shenzhen_gdp, start_year=2010, years=5)
    print("=== 深圳 GDP 5 年预测 ===")
    print("Ensemble:", [round(x) for x in out["ensemble"]["predictions"]])
    print("Lower 95:", [round(x) for x in out["ensemble"]["lower_ci"]])
    print("Upper 95:", [round(x) for x in out["ensemble"]["upper_ci"]])
    print("Weights:", out["ensemble"]["weights"])
    print("Diagnostics verdict:", out["diagnostics"].get("verdict"))
    print("Structural breaks:", len(out["structural_breaks"]))
    print("Backtest:", out["backtest"].get("metrics"))
    print("Historical CAGR:", out["growth"]["historical_cagr_pct"], "%")
    print("Forecast CAGR:", out["growth"]["forecast_cagr_pct"], "%")
