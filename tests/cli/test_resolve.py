"""cli._resolve — CLI args → SDK 调用 kwargs。"""
import pytest

from cli._resolve import (
    build_backtest_args,
    build_data_provenance_args,
    build_diagnostics_args,
    build_forecast_args,
    build_list_cities_args,
    build_macro_data_args,
    build_monte_carlo_args,
    build_risk_args,
    build_scenarios_args,
)


def test_build_forecast_args_required_only():
    args = build_forecast_args(city="shenzhen", indicator="gdp", years=None)
    assert args == {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 5}


def test_build_forecast_args_province_scope():
    args = build_forecast_args(city="guangdong", indicator="gdp", scope="province", years=3)
    assert args["scope"] == "province"
    assert args["years"] == 3


def test_build_forecast_args_custom_years():
    args = build_forecast_args(city="shenzhen", indicator="gdp", years=10)
    assert args["years"] == 10


def test_build_data_provenance_args():
    assert build_data_provenance_args(city="shenzhen") == {"name": "shenzhen"}


def test_build_macro_data_args():
    assert build_macro_data_args() == {}


def test_build_list_cities_args():
    assert build_list_cities_args() == {}


def test_build_diagnostics_args():
    assert build_diagnostics_args(city="shanghai", indicator="gdp") == {"scope": "city", "name": "shanghai", "indicator": "gdp"}


def test_build_backtest_args():
    assert build_backtest_args(city="beijing", indicator="gdp") == {"scope": "city", "name": "beijing", "indicator": "gdp"}


def test_build_risk_args():
    assert build_risk_args(city="guangzhou", indicator="gdp") == {"scope": "city", "name": "guangzhou", "indicator": "gdp"}


def test_build_scenarios_args_default_years():
    assert build_scenarios_args(city="shenzhen", indicator="gdp") == {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 5}


def test_build_scenarios_args_custom_years():
    assert build_scenarios_args(city="shenzhen", indicator="gdp", years=10)["years"] == 10


def test_build_monte_carlo_args_default_years():
    assert build_monte_carlo_args(city="hangzhou", indicator="gdp")["years"] == 5


def test_build_monte_carlo_args_custom_years():
    assert build_monte_carlo_args(city="hangzhou", indicator="gdp", years=20)["years"] == 20
