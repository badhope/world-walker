"""
投资决策级风险分析 — Phase 8-9。

组件:
1. rolling_volatility: 滚动年化波动率(对数收益 std)
2. var_cvar: 历史模拟 VaR / CVaR
3. scenario_analysis: 3 档情景(基线/乐观/悲观/衰退)
4. monte_carlo: 1000 次残差 bootstrap
"""
from __future__ import annotations

import logging
import math
import warnings
from typing import Any

import numpy as np

from backend.core.engine_stack import arch_available, primary_vol_backend

logger = logging.getLogger(__name__)

_VOL_BACKEND = primary_vol_backend()
logger.info("Risk engine: volatility backend = %s", _VOL_BACKEND)


# --------------------------------------------------------------------------- #
# 1. 滚动年化波动率
# --------------------------------------------------------------------------- #


def rolling_volatility(values: list[float], window: int = 3, annualize: bool = True) -> dict[str, Any]:
    """
    对数收益的滚动窗口标准差。
    annualize=True 时乘以 sqrt(periods_per_year),这里默认 1(年频数据)。
    """
    n = len(values)
    if n < 3:
        return {
            "volatility": 0.0,
            "annualized": 0.0,
            "window": window,
            "reason": "n<3",
            "backend": "rolling-std",
        }
    y = np.array(values, dtype=float)
    # 对数收益
    log_rets = np.diff(np.log(y))
    if len(log_rets) < window:
        window = len(log_rets)
    # 滚动 std(取最后 window 个)
    recent = log_rets[-window:]
    vol = float(np.std(recent, ddof=1))
    annualized = vol * math.sqrt(1) if annualize else vol
    return {
        "volatility": round(vol, 6),
        "annualized_volatility": round(annualized, 6),
        "window": window,
        "n_returns": len(log_rets),
        "backend": "rolling-std",
        "interpretation": (
            f"年化波动率 {annualized*100:.2f}%。"
            f"< 5% 为低波动, 5-15% 中等, > 15% 高波动"
        ),
    }


# --------------------------------------------------------------------------- #
# 1b. GARCH(p,q) 条件波动率(Docker only,需 arch 库)
# --------------------------------------------------------------------------- #


def garch_volatility(values: list[float], horizon: int = 1, p: int = 1, q: int = 1) -> dict[str, Any]:
    """
    GARCH(p,q) 条件波动率 — 用 arch 库。

    对年频数据(样本少)用 GARCH(1,1) 即可。返回:
    - conditional_vol_pct: 末年条件波动率(%)
    - forecast_vol_pct: horizon 期预测波动率(%)
    - persistence: alpha + beta 持续性,接近 1 表示波动高度聚集
    - half_life_years: 半衰期
    - aic/bic: 模型信息准则

    失败(库未装或拟合失败)时返回 dict 含 'method': 'GARCH failed (...)',
    调用方应改用 rolling_volatility。
    """
    if not arch_available():
        return {
            "method": "GARCH failed (arch library not installed)",
            "conditional_vol_pct": 0.0,
            "forecast_vol_pct": 0.0,
        }

    n = len(values)
    if n < 8:
        return {
            "method": "GARCH (insufficient data)",
            "conditional_vol_pct": 0.0,
            "forecast_vol_pct": 0.0,
            "reason": f"n={n} < 8",
        }

    try:
        from arch import arch_model

        y = np.array(values, dtype=float)
        # 算 YoY 收益率(%)
        returns = 100.0 * np.diff(y) / y[:-1]

        am = arch_model(returns, mean="Constant", vol="GARCH", p=p, q=q, dist="normal")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = am.fit(disp="off", show_warning=False)

        cond_vol = float(res.conditional_volatility.iloc[-1])
        # horizon 步预测
        fc = res.forecast(horizon=horizon)
        forecast_vol = float(np.sqrt(np.asarray(fc.variance.iloc[-1]).mean()))

        params = res.params
        alpha = float(params.get("alpha[1]", 0.0))
        beta = float(params.get("beta[1]", 0.0))
        persistence = alpha + beta
        if 0 < persistence < 1:
            half_life = math.log(0.5) / math.log(persistence)
        else:
            half_life = float("inf")

        return {
            "method": f"GARCH({p},{q}) via arch",
            "backend": "arch-garch",
            "conditional_vol_pct": round(cond_vol, 4),
            "conditional_vol_annualized_pct": round(cond_vol * math.sqrt(1), 4),
            "forecast_vol_pct": round(forecast_vol, 4),
            "persistence": round(persistence, 4),
            "half_life_years": round(half_life, 2) if half_life != float("inf") else None,
            "alpha": round(alpha, 4),
            "beta": round(beta, 4),
            "aic": round(float(res.aic), 2),
            "bic": round(float(res.bic), 2),
        }
    except Exception as e:
        logger.warning("GARCH fit failed: %s", e)
        return {
            "method": f"GARCH failed ({e})",
            "conditional_vol_pct": 0.0,
            "forecast_vol_pct": 0.0,
        }


# --------------------------------------------------------------------------- #
# 2. VaR / CVaR (历史模拟)
# --------------------------------------------------------------------------- #


def var_cvar(values: list[float], confidence: float = 0.95, lookback: int = 5) -> dict[str, Any]:
    """
    历史模拟 VaR / CVaR。
    - VaR: 在 (1-confidence) 处的最坏收益(负值)
    - CVaR: 收益低于 VaR 部分的平均(尾部期望损失)

    基于历史 n 年增长率,假设收益分布不变。
    """
    n = len(values)
    if n < 3:
        return {"var": 0.0, "cvar": 0.0, "confidence": confidence, "reason": "n<3"}

    y = np.array(values, dtype=float)
    # YoY 收益
    returns = (y[1:] - y[:-1]) / y[:-1]
    returns = returns[-lookback:]

    sorted_returns = np.sort(returns)  # 升序
    # VaR: 第 (1-confidence) 分位的损失
    var_idx = max(0, int(np.floor((1 - confidence) * len(sorted_returns))) - 1)
    var_pct = -float(sorted_returns[var_idx])  # 损失方向为正

    # CVaR: 排序后前 (1-confidence) 部分的平均
    tail = sorted_returns[: var_idx + 1]
    cvar_pct = -float(np.mean(tail)) if len(tail) > 0 else var_pct

    last_value = float(y[-1])
    return {
        "confidence": confidence,
        "method": "historical_simulation",
        "lookback_years": len(returns),
        "var_pct": round(var_pct, 6),
        "var_amount": round(var_pct * last_value, 4),
        "cvar_pct": round(cvar_pct, 6),
        "cvar_amount": round(cvar_pct * last_value, 4),
        "last_value": last_value,
        "interpretation": (
            f"在最坏的 {int((1-confidence)*100)}% 历史情景下,"
            f"未来 1 年最多损失 {var_pct*100:.2f}% (≈{var_pct*last_value:.0f} 亿元);"
            f"平均尾部损失 {cvar_pct*100:.2f}% (≈{cvar_pct*last_value:.0f} 亿元)"
        ),
    }


# --------------------------------------------------------------------------- #
# 3. 情景分析
# --------------------------------------------------------------------------- #


SCENARIOS = {
    "baseline": {
        "name": "基线",
        "description": "按历史趋势 + 集成模型预测",
        "shock_per_year": 0.0,
        "color": "#0E1F3F",
    },
    "optimistic": {
        "name": "乐观",
        "description": "国家政策刺激 + 出口超预期 + 投资扩张",
        "shock_per_year": 0.10,  # +10%/年
        "color": "#22C55E",
    },
    "pessimistic": {
        "name": "悲观",
        "description": "地缘冲击 + 需求收缩 + 地产拖累",
        "shock_per_year": -0.10,  # -10%/年
        "color": "#D08560",
    },
    "recession": {
        "name": "衰退",
        "description": "2008/2020 级别冲击,GDP 持续下行",
        "shock_per_year": -0.25,  # -25%/年
        "color": "#DC2626",
    },
}


def scenario_analysis(
    baseline_predictions: list[float],
    starting_value: float,
) -> dict[str, Any]:
    """
    3 档情景(+基线)对 baseline 预测施加冲击。
    冲击按复利累加:year_t = baseline_t × (1 + shock_per_year)^t
    """
    out: dict[str, Any] = {"scenarios": {}}
    for sid, meta in SCENARIOS.items():
        shock = meta["shock_per_year"]
        shocked = []
        for t, p in enumerate(baseline_predictions):
            factor = (1 + shock) ** (t + 1)
            shocked.append(p * factor)
        # 末年值
        out["scenarios"][sid] = {
            "name": meta["name"],
            "description": meta["description"],
            "shock_per_year": shock,
            "color": meta["color"],
            "predictions": [round(x, 2) for x in shocked],
            "final_value": round(shocked[-1], 2) if shocked else 0.0,
            "max_drawdown_pct": round((min(shocked) - starting_value) / starting_value * 100, 2)
            if shocked
            else 0.0,
            "final_change_pct": round((shocked[-1] - starting_value) / starting_value * 100, 2)
            if shocked
            else 0.0,
        }
    return out


# --------------------------------------------------------------------------- #
# 4. Monte Carlo — 残差 bootstrap
# --------------------------------------------------------------------------- #


def monte_carlo_simulation(
    values: list[float],
    years: int = 5,
    n_sims: int = 1000,
    confidence_levels: tuple[float, ...] = (0.05, 0.50, 0.95),
    seed: int = 42,
) -> dict[str, Any]:
    """
    残差 bootstrap 蒙特卡洛:
    1. 拟合 baseline 集成预测(传入 values,函数内部算 baseline)
    2. 残差 = actual - baseline_predicted
    3. 每次模拟:对残差有放回抽样,加到 baseline 上
    4. 返回每年的 P5/P50/P95 三个分位

    假设:残差独立同分布(实际时序有自相关,会低估尾部风险 — 已在文档中说明)
    """
    n = len(values)
    if n < 6:
        return {"error": f"n={n} too small for MC"}

    np.random.seed(seed)
    y = np.array(values, dtype=float)
    # 用 LR 算 baseline 残差(快、稳)
    x = np.arange(n).reshape(-1, 1).astype(float)
    from sklearn.linear_model import LinearRegression

    model = LinearRegression().fit(x, y)
    baseline_hist = model.predict(x)
    resid = y - baseline_hist
    sigma = float(np.std(resid, ddof=1))
    if sigma == 0:
        sigma = float(np.mean(np.abs(resid))) or 1.0

    future_x = np.arange(n, n + years).reshape(-1, 1).astype(float)
    baseline_fc = model.predict(future_x)

    # 模拟
    sims = np.zeros((n_sims, years))
    for s in range(n_sims):
        # 对残差有放回抽样
        sampled_resid = np.random.choice(resid, size=years, replace=True)
        # 可选:加白噪声 ~ N(0, sigma^2) 增强探索
        sims[s, :] = baseline_fc + sampled_resid

    # 分位
    quantiles: dict[str, list[float]] = {}
    for q in confidence_levels:
        quantiles[f"p{int(q*100):02d}"] = np.quantile(sims, q, axis=0).round(2).tolist()

    # 统计
    final_values = sims[:, -1]
    return {
        "n_sims": n_sims,
        "years": list(range(n, n + years)),
        "baseline": [round(float(x), 2) for x in baseline_fc.tolist()],
        "quantiles": quantiles,
        "final_value_stats": {
            "mean": round(float(np.mean(final_values)), 2),
            "std": round(float(np.std(final_values, ddof=1)), 2),
            "min": round(float(np.min(final_values)), 2),
            "max": round(float(np.max(final_values)), 2),
            "prob_above_baseline": round(float(np.mean(final_values > baseline_fc[-1])), 4),
            "prob_below_recession": round(float(np.mean(final_values < baseline_fc[-1] * 0.75)), 4),
        },
        "interpretation": (
            f"基于 {n_sims} 次 bootstrap 残差模拟,"
            f"末年值 {quantiles['p05'][0]:.0f} ~ {quantiles['p95'][0]:.0f} 亿元 (P5-P95);"
            f"高于 baseline 概率 {float(np.mean(final_values > baseline_fc[-1]))*100:.1f}%;"
            f"低于衰退情景 (baseline×0.75) 概率 {float(np.mean(final_values < baseline_fc[-1] * 0.75))*100:.1f}%"
        ),
    }


# --------------------------------------------------------------------------- #
# 5. 主入口:综合风险 + 情景 + MC
# --------------------------------------------------------------------------- #


def risk_full_pipeline(
    values: list[float],
    baseline_predictions: list[float],
    starting_value: float,
    n_sims: int = 1000,
) -> dict[str, Any]:
    """完整风险 + 情景 + MC 流水线"""
    vol = rolling_volatility(values, window=min(3, len(values) - 1))
    garch = garch_volatility(values)  # arch 未装时内部返回 failed dict
    var95 = var_cvar(values, confidence=0.95)
    var99 = var_cvar(values, confidence=0.99)
    scenarios = scenario_analysis(baseline_predictions, starting_value)
    mc = monte_carlo_simulation(values, years=len(baseline_predictions), n_sims=n_sims)
    return {
        "volatility": vol,
        "garch": garch,
        "var_95": var95,
        "var_99": var99,
        "scenarios": scenarios,
        "monte_carlo": mc,
        "engine_stack": {
            "arch": arch_available(),
        },
    }


if __name__ == "__main__":
    shenzhen_gdp = [9772, 11506, 12971, 14573, 16002, 17503, 19493, 22438, 25267, 26927, 27700, 30700, 32400, 34600, 36500, 38500]
    from backend.core.forecast_engine import forecast_full_pipeline

    pipe = forecast_full_pipeline(shenzhen_gdp, 2010, 5)
    baseline = pipe["ensemble"]["predictions"]
    risk = risk_full_pipeline(shenzhen_gdp, baseline, 38500, n_sims=1000)

    print("=== 深圳 GDP 风险 + 情景 + MC ===")
    print(f"波动率: 年化 {risk['volatility']['annualized_volatility']*100:.2f}%")
    print(f"VaR 95%: 损失 {risk['var_95']['var_pct']*100:.2f}% (≈{risk['var_95']['var_amount']:.0f} 亿元)")
    print(f"CVaR 95%: 平均尾部 {risk['var_95']['cvar_pct']*100:.2f}% (≈{risk['var_95']['cvar_amount']:.0f} 亿元)")
    print("\n情景(5 年后):")
    for sid, s in risk["scenarios"]["scenarios"].items():
        print(f"  {s['name']}: {s['final_value']:.0f} 亿元 ({s['final_change_pct']:+.2f}%)")
    print("\nMC 1000 次:")
    print(f"  末年 P5/P50/P95: {risk['monte_carlo']['quantiles']['p05'][-1]:.0f} / {risk['monte_carlo']['quantiles']['p50'][-1]:.0f} / {risk['monte_carlo']['quantiles']['p95'][-1]:.0f}")
    print(f"  低于衰退情景概率: {risk['monte_carlo']['final_value_stats']['prob_below_recession']*100:.1f}%")
