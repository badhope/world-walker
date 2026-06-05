"""
Phase 8-9 风险 + 情景 + Monte Carlo 测试
"""
import sys

sys.path.insert(0, ".")


def test_rolling_volatility():
    from backend.core.risk_engine import rolling_volatility

    y = [100, 105, 110, 108, 115, 120, 118, 125, 130]
    out = rolling_volatility(y, window=3)
    assert "volatility" in out
    assert "annualized_volatility" in out
    assert out["volatility"] > 0
    print(f"✓ 滚动波动率: {out['annualized_volatility']*100:.2f}% (3年窗口)")


def test_var_cvar_basic():
    from backend.core.risk_engine import var_cvar

    y = [100, 105, 110, 95, 100, 115, 120, 90, 105]  # 包含 1 次 -13.6% 大跌
    out = var_cvar(y, confidence=0.95)
    assert "var_pct" in out
    assert "cvar_pct" in out
    assert out["var_pct"] > 0
    assert out["cvar_pct"] >= out["var_pct"], "CVaR 应 ≥ VaR"
    print(f"✓ VaR 95%: 损失 {out['var_pct']*100:.2f}%, CVaR: 损失 {out['cvar_pct']*100:.2f}%")


def test_scenario_analysis_4_scenarios():
    from backend.core.risk_engine import scenario_analysis

    baseline = [40000, 42000, 44000, 46000, 48000]
    out = scenario_analysis(baseline, starting_value=38500)
    assert "scenarios" in out
    assert len(out["scenarios"]) == 4  # baseline + optimistic + pessimistic + recession
    for sid, s in out["scenarios"].items():
        assert "predictions" in s
        assert len(s["predictions"]) == 5
    # 验证冲击方向
    assert out["scenarios"]["optimistic"]["final_value"] > baseline[-1]
    assert out["scenarios"]["pessimistic"]["final_value"] < baseline[-1]
    assert out["scenarios"]["recession"]["final_value"] < out["scenarios"]["pessimistic"]["final_value"]
    print("✓ 4 情景:")
    for sid, s in out["scenarios"].items():
        print(f"    {s['name']} (shock {s['shock_per_year']*100:+.0f}%/y): 末年 {s['final_value']:.0f} ({s['final_change_pct']:+.2f}%)")


def test_monte_carlo_1000_sims():
    from backend.core.risk_engine import monte_carlo_simulation

    y = [100, 102, 105, 108, 110, 112, 115, 118, 120, 122, 125, 128, 130, 132, 135, 138]
    out = monte_carlo_simulation(y, years=5, n_sims=1000)
    assert "n_sims" in out
    assert out["n_sims"] == 1000
    assert "quantiles" in out
    assert "p05" in out["quantiles"]
    assert "p50" in out["quantiles"]
    assert "p95" in out["quantiles"]
    # P5 < P50 < P95
    assert out["quantiles"]["p05"][-1] < out["quantiles"]["p50"][-1] < out["quantiles"]["p95"][-1]
    # 末年值范围合理
    print("✓ Monte Carlo 1000 次:")
    print(f"    末年 P5/P50/P95: {out['quantiles']['p05'][-1]:.0f} / {out['quantiles']['p50'][-1]:.0f} / {out['quantiles']['p95'][-1]:.0f}")
    print(f"    高于 baseline 概率: {out['final_value_stats']['prob_above_baseline']*100:.1f}%")


def test_risk_full_pipeline():
    from backend.core.forecast_engine import forecast_full_pipeline
    from backend.core.risk_engine import risk_full_pipeline

    shenzhen_gdp = [9772, 11506, 12971, 14573, 16002, 17503, 19493, 22438, 25267, 26927, 27700, 30700, 32400, 34600, 36500, 38500]
    pipe = forecast_full_pipeline(shenzhen_gdp, 2010, 5)
    baseline = pipe["ensemble"]["predictions"]
    risk = risk_full_pipeline(shenzhen_gdp, baseline, 38500, n_sims=1000)

    assert "volatility" in risk
    assert "var_95" in risk
    assert "var_99" in risk
    assert "scenarios" in risk
    assert "monte_carlo" in risk
    print("\n✓ 深圳 GDP 风险全流水线:")
    print(f"    波动率: {risk['volatility']['annualized_volatility']*100:.2f}%")
    print(f"    VaR 95%: 损失 {risk['var_95']['var_pct']*100:.2f}%")
    print(f"    VaR 99%: 损失 {risk['var_99']['var_pct']*100:.2f}%")
    print(f"    衰退情景末年: {risk['scenarios']['scenarios']['recession']['final_value']:.0f}")
    print(f"    MC P5-P95 末年: {risk['monte_carlo']['quantiles']['p05'][-1]:.0f} ~ {risk['monte_carlo']['quantiles']['p95'][-1]:.0f}")


if __name__ == "__main__":
    test_rolling_volatility()
    test_var_cvar_basic()
    test_scenario_analysis_4_scenarios()
    test_monte_carlo_1000_sims()
    test_risk_full_pipeline()
    print("\n✅ Phase 8-9 风险 + 情景 + Monte Carlo — 全部测试通过")
