"""
Engine stack 探测 + fallback 测试。

覆盖:
- 4 个 *_available() 返回 bool,绝不抛异常
- engine_stack() 包含所有 4 个键
- primary_arima_backend / primary_vol_backend 给出有效字符串
- 在 sandbox 中(无 4 个库),forecast_full_pipeline 仍能跑(fallback 路径)
- arima_forecast 的返回值 schema 不变
- garch_volatility 在 arch 未装时返回 failed dict,不抛异常
- risk_full_pipeline 输出含 garch + engine_stack 字段
"""
import sys

sys.path.insert(0, ".")


def test_engine_stack_has_four_keys():
    from backend.core.engine_stack import engine_stack

    stack = engine_stack()
    assert isinstance(stack, dict)
    expected = {"statsforecast", "arch", "pmdarima", "prophet"}
    assert set(stack.keys()) == expected, f"keys 不匹配: {set(stack.keys())}"
    for k, v in stack.items():
        assert isinstance(v, bool), f"{k} 应为 bool, 实际 {type(v)}"
    print(f"✓ engine_stack: {stack}")


def test_primary_backends_return_strings():
    from backend.core.engine_stack import primary_arima_backend, primary_vol_backend, stack_summary

    arima_b = primary_arima_backend()
    vol_b = primary_vol_backend()
    assert arima_b in {"statsforecast", "pmdarima", "statsmodels"}
    assert vol_b in {"arch-garch", "rolling-std"}
    s = stack_summary()
    assert s["primary_arima_backend"] == arima_b
    assert s["primary_vol_backend"] == vol_b
    print(f"✓ Primary backends: arima={arima_b}, vol={vol_b}")


def test_availability_functions_never_raise():
    """探测函数应永不抛异常(库未装时返回 False)"""
    from backend.core.engine_stack import (
        arch_available,
        pmdarima_available,
        prophet_available,
        statsforecast_available,
    )

    for fn, name in [
        (statsforecast_available, "statsforecast"),
        (arch_available, "arch"),
        (pmdarima_available, "pmdarima"),
        (prophet_available, "prophet"),
    ]:
        v = fn()
        assert isinstance(v, bool), f"{name} 返回 {type(v)}"
        # 二次调用应返回缓存值,不抛异常
        v2 = fn()
        assert v == v2
    print("✓ 4 个 *_available() 函数永不抛异常,缓存稳定")


def test_auto_arima_backend_fallback():
    """sandbox 中 auto_arima_native 应自动 fallback 到 statsmodels"""
    from backend.core.forecast_engine import auto_arima, auto_arima_native

    y = [10, 12, 14, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 37, 39]
    fit = auto_arima(y)
    assert fit.get("backend") == "statsmodels"
    assert fit["order"] is not None
    print(f"✓ auto_arima (statsmodels): order={fit['order']}, AIC={fit['aic']:.1f}")

    fit2 = auto_arima_native(y)
    assert fit2.get("backend") in {"statsmodels", "pmdarima", "statsforecast"}
    # 在 sandbox 中应能 fit 成功
    assert fit2["model"] is not None
    print(f"✓ auto_arima_native: backend={fit2.get('backend')}, order={fit2['order']}")


def test_arima_forecast_schema_unchanged():
    """无论走哪个 backend,arima_forecast 返回的 dict schema 相同"""
    from backend.core.forecast_engine import arima_forecast

    y = [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40]
    out = arima_forecast(y, years=3, confidence=0.95)
    for k in ("predictions", "lower_ci", "upper_ci", "method", "order", "aic", "bic"):
        assert k in out, f"缺字段 {k}"
    assert len(out["predictions"]) == 3
    assert len(out["lower_ci"]) == 3
    assert len(out["upper_ci"]) == 3
    # CI 带宽 > 0
    assert out["upper_ci"][0] > out["lower_ci"][0]
    # method 应包含 backend 标签
    assert "statsmodels" in out["method"] or "statsforecast" in out["method"] or "pmdarima" in out["method"]
    print(f"✓ arima_forecast schema: method={out['method']}, CI width={out['upper_ci'][0]-out['lower_ci'][0]:.2f}")


def test_garch_volatility_fallback_or_compute():
    """arch 未装时 garch_volatility 应返回 failed dict,不抛异常"""
    from backend.core.engine_stack import arch_available
    from backend.core.risk_engine import garch_volatility

    y = [10000, 11000, 12000, 13000, 14000, 15000, 16000, 17000, 17500, 18000, 18500, 19000]
    out = garch_volatility(y)
    assert "method" in out
    assert "conditional_vol_pct" in out
    if arch_available():
        # 装上时,应给出有效数字
        assert out["conditional_vol_pct"] > 0
        assert "persistence" in out
        print(f"✓ GARCH(1,1): cond_vol={out['conditional_vol_pct']:.2f}%, persistence={out['persistence']}")
    else:
        # 未装时,method 应包含 "GARCH failed" 或 "insufficient data"
        assert "GARCH" in out["method"] or "insufficient" in out["method"]
        assert "conditional_vol_pct" in out
        print(f"✓ GARCH fallback: method={out['method']}")


def test_rolling_volatility_has_backend_field():
    """rolling_volatility 输出应始终有 'backend' 字段"""
    from backend.core.risk_engine import rolling_volatility

    y = [10000, 11000, 12000, 13000, 14000, 15000, 16000, 17000, 17500, 18000, 18500, 19000]
    out = rolling_volatility(y, window=3)
    assert "backend" in out
    assert out["backend"] == "rolling-std"
    print(f"✓ rolling_volatility.backend = {out['backend']}")


def test_risk_pipeline_includes_engine_stack():
    from backend.core.risk_engine import risk_full_pipeline

    y = [10000, 11000, 12000, 13000, 14000, 15000, 16000, 17000, 17500, 18000, 18500, 19000]
    baseline = [19500, 20000, 20500, 21000, 21500]
    out = risk_full_pipeline(y, baseline, 19000, n_sims=200)
    assert "volatility" in out
    assert "garch" in out
    assert "engine_stack" in out
    assert "arch" in out["engine_stack"]
    assert isinstance(out["garch"], dict)
    assert "method" in out["garch"]
    print(f"✓ risk_full_pipeline: arch={out['engine_stack']['arch']}, garch method={out['garch']['method']}")


def test_full_pipeline_still_works_without_extras():
    """核心:即使 4 个新库都没装,全流水线仍能跑(向后兼容)"""
    from backend.core.engine_stack import engine_stack
    from backend.core.forecast_engine import forecast_full_pipeline

    # 先确认 sandbox 状态
    stack = engine_stack()
    shenzhen_gdp = [9772, 11506, 12971, 14573, 16002, 17503, 19493, 22438, 25267, 26927, 27700, 30700, 32400, 34600, 36500, 38500]
    out = forecast_full_pipeline(shenzhen_gdp, start_year=2010, years=5)
    assert "ensemble" in out
    assert "diagnostics" in out
    assert "backtest" in out
    # 集成预测应合理(深圳 GDP 2026 应在 38000-45000)
    pred_2026 = out["ensemble"]["predictions"][0]
    assert 38000 < pred_2026 < 45000, f"2026 预测 {pred_2026} 异常"
    # arima method 应带 backend 标签
    method = out["models"]["arima"]["method"]
    backend = stack.get("statsforecast") or stack.get("pmdarima") or "statsmodels"
    assert backend in method
    print(f"✓ Full pipeline(无 extras, backend={backend}): 2026 pred={pred_2026:.0f}")
    print(f"    arima method = {method}")


def test_engine_stack_module_self_check():
    """engine_stack module 的 __main__ 自检可跑"""
    import subprocess

    result = subprocess.run(
        ["python", "-m", "backend.core.engine_stack"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"engine_stack self-check failed: {result.stderr}"
    assert "primary_arima_backend" in result.stdout
    print("✓ engine_stack self-check 输出正常")


if __name__ == "__main__":
    test_engine_stack_has_four_keys()
    test_primary_backends_return_strings()
    test_availability_functions_never_raise()
    test_auto_arima_backend_fallback()
    test_arima_forecast_schema_unchanged()
    test_garch_volatility_fallback_or_compute()
    test_rolling_volatility_has_backend_field()
    test_risk_pipeline_includes_engine_stack()
    test_full_pipeline_still_works_without_extras()
    test_engine_stack_module_self_check()
    print("\n✅ Engine stack 探测 + fallback 测试全部通过")
