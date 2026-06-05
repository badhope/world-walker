"""
Phase 4-7 投资决策级预测引擎测试
"""
import sys

sys.path.insert(0, ".")

import math


def test_auto_arima_finds_best_order():
    from backend.core.forecast_engine import arima_forecast, auto_arima

    # 已知带趋势的序列
    y = [10, 12, 14, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 37, 39]
    fit = auto_arima(y)
    assert fit["model"] is not None, "auto_arima 应该能选到 order"
    assert fit["order"] is not None
    print(f"✓ auto_arima selected order={fit['order']}, AIC={fit['aic']:.2f}")


def test_ets_forecast_basic():
    from backend.core.forecast_engine import ets_forecast

    # 加 noise 的趋势数据,ETS 能正常拟合
    y = [10, 12, 14, 15, 18, 20, 22, 24, 26, 28, 30, 32]
    out = ets_forecast(y, years=3)
    assert "predictions" in out
    assert len(out["predictions"]) == 3
    # 趋势数据预测应保持单调或近似
    assert out["predictions"][-1] > y[-1] * 0.9, f"ETS 末年预测 {out['predictions'][-1]} 应接近 {y[-1]}"
    # 注意:完美线性 → ETS residuals=0 → CI 宽度=0(此时 CI 失去意义)
    # 现实数据总有 noise,所以 CI 宽度 > 0
    print(f"✓ ETS forecast: {[round(p, 1) for p in out['predictions']]}, width={round(out['upper_ci'][0]-out['lower_ci'][0], 1)}")


def test_linear_regression_forecast():
    from backend.core.forecast_engine import linear_regression_forecast

    y = list(range(10, 30))  # 完美线性
    out = linear_regression_forecast(y, years=3)
    # 完美线性下预测应该接近 30, 31, 32
    assert abs(out["predictions"][0] - 30) < 1.0
    assert abs(out["predictions"][1] - 31) < 1.0
    print(f"✓ LR forecast: {[round(p) for p in out['predictions']]} (期望 30, 31, 32)")


def test_ensemble_weights_sum_to_one():
    from backend.core.forecast_engine import arima_forecast, ensemble_forecast, ets_forecast, linear_regression_forecast

    y = [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32]
    ar = arima_forecast(y, 3)
    et = ets_forecast(y, 3)
    lr = linear_regression_forecast(y, 3)
    ens = ensemble_forecast(ar, et, lr)
    total_w = sum(ens["weights"].values())
    assert abs(total_w - 1.0) < 0.01, f"权重和应为 1,实际 {total_w}"
    print(f"✓ Ensemble weights sum: {total_w:.4f} ({ens['weights']})")


def test_diagnostics_5_tests():
    from backend.core.forecast_engine import run_diagnostics

    y = [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40]
    out = run_diagnostics(y, order=(1, 1, 0))
    assert "tests" in out
    assert "verdict" in out
    expected_tests = ["adf", "kpss", "ljung_box", "jarque_bera", "breusch_pagan"]
    for t in expected_tests:
        assert t in out["tests"], f"缺 {t}"
        if "error" not in out["tests"][t]:
            assert "statistic" in out["tests"][t]
            assert "pvalue" in out["tests"][t]
            assert "conclusion" in out["tests"][t]
    print(f"✓ 5 项诊断:verdict={out['verdict']}")
    for name, t in out["tests"].items():
        if "error" not in t:
            print(f"    {name}: stat={t['statistic']}, p={t['pvalue']} → {t['conclusion']}")


def test_chow_test_no_break_on_linear():
    """完美线性数据应该没有结构突变"""
    from backend.core.forecast_engine import chow_test, find_structural_breaks

    y = list(range(10, 30))  # 完美线性
    # 中间断点应该不显著
    result = chow_test(y, 10)
    assert not result["structural_break"], f"完美线性不应有突变:p={result['pvalue']}"
    print(f"✓ Chow test: 完美线性序列,中点 p={result['pvalue']:.4f} (>0.05)")

    breaks = find_structural_breaks(y, min_segment=3)
    assert len(breaks) == 0, f"完美线性不应找到突变,实际 {len(breaks)}"
    print("✓ find_structural_breaks: 0 个突变点")


def test_chow_test_detects_break():
    """有明显断点的数据应该被检测到"""
    from backend.core.forecast_engine import find_structural_breaks

    # 2010-2017 斜率 = 1000,2017 后斜率 = 0
    y = [10000, 11000, 12000, 13000, 14000, 15000, 16000, 17000, 17000, 17000, 17000, 17000, 17000, 17000, 17000, 17000]
    breaks = find_structural_breaks(y, min_segment=3)
    assert len(breaks) > 0, "有断点的数据应被检测到"
    print(f"✓ Chow test 检测到 {len(breaks)} 个显著断点(预期 ≥1)")
    for b in breaks[:2]:
        print(f"    idx={b['breakpoint_idx']}, F={b['f_stat']}, p={b['pvalue']}")


def test_backtest_5_metrics():
    from backend.core.forecast_engine import backtest_forecast

    y = [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40]
    out = backtest_forecast(y, n_test=3)
    assert "metrics" in out
    expected = ["MAPE_pct", "RMSE", "MASE", "sMAPE_pct", "Coverage_pct"]
    for m in expected:
        assert m in out["metrics"], f"缺 {m}"
    print("✓ Backtest 5 项指标:")
    for k, v in out["metrics"].items():
        print(f"    {k}: {v}")


def test_full_pipeline_shenzhen_gdp():
    """深圳 GDP 16 年全流水线"""
    from backend.core.forecast_engine import forecast_full_pipeline

    shenzhen_gdp = [9772, 11506, 12971, 14573, 16002, 17503, 19493, 22438, 25267, 26927, 27700, 30700, 32400, 34600, 36500, 38500]
    out = forecast_full_pipeline(shenzhen_gdp, start_year=2010, years=5)
    assert "ensemble" in out
    assert "diagnostics" in out
    assert "backtest" in out
    assert "growth" in out

    # 集成预测 2026 应在 39000-42000 之间(基线 38500 + 4% CAGR)
    pred_2026 = out["ensemble"]["predictions"][0]
    assert 38000 < pred_2026 < 45000, f"2026 预测 {pred_2026} 异常"
    # CI 带宽
    assert out["ensemble"]["lower_ci"][0] < out["ensemble"]["upper_ci"][0]
    # 诊断
    assert out["diagnostics"]["verdict"] in ("PASS", "WARN", "FAIL")
    # CAGR
    assert out["growth"]["historical_cagr_pct"] > 5
    assert out["growth"]["forecast_cagr_pct"] > 0
    print("\n✓ 深圳 GDP 16 年全流水线:")
    print(f"    集成预测 5 年: {[round(p) for p in out['ensemble']['predictions']]}")
    print(f"    95% CI width: {round(out['ensemble']['upper_ci'][0] - out['ensemble']['lower_ci'][0])}")
    print(f"    集成权重: {out['ensemble']['weights']}")
    print(f"    残差诊断: {out['diagnostics']['verdict']}")
    print(f"    结构突变: {len(out['structural_breaks'])} 个")
    print(f"    Backtest: MAPE={out['backtest']['metrics'].get('MAPE_pct')}%, MASE={out['backtest']['metrics'].get('MASE')}, Coverage={out['backtest']['metrics'].get('Coverage_pct')}%")
    print(f"    CAGR: 历史 {out['growth']['historical_cagr_pct']}% / 预测 {out['growth']['forecast_cagr_pct']}%")


if __name__ == "__main__":
    test_auto_arima_finds_best_order()
    test_ets_forecast_basic()
    test_linear_regression_forecast()
    test_ensemble_weights_sum_to_one()
    test_diagnostics_5_tests()
    test_chow_test_no_break_on_linear()
    test_chow_test_detects_break()
    test_backtest_5_metrics()
    test_full_pipeline_shenzhen_gdp()
    print("\n✅ Phase 4-7 投资决策级预测引擎 — 全部测试通过")
