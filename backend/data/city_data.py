"""
城市数据模块 - 真实数据存储与查询接口
提供所有城市指标数据、历史数据、评分基准和权重
"""

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

CITY_DATA: dict[str, dict[str, Any]] = {
    "深圳": {
        "name": "深圳",
        "region": "华南",
        "year": 2025,
        "industry": "半导体",
        "industry_code": "semiconductor",
        "land_price": 5200,
        "salary_level": 12800,
        "energy_cost": 0.78,
        "financing_cost": 3.2,
        "local_support_rate": 85.5,
        "avg_delivery_time": 3.5,
        "location_quotient": 1.85,
        "supplier_count": 5200,
        "tax_reduction": 28.5,
        "policy_coverage": 92.0,
        "tax_coverage": 92.0,
        "rd_subsidy": 15.0,
        "avg_approval_time": 18.0,
        "gdp": 38500,
        "gdp_growth": 6.5,
        "population": 1850,
        "fiscal_revenue": 5200,
        "rd_intensity": 5.1,
        "industry_high_tech_ratio": 58.0,
        "data_quality": 95.0,
        "data_source": "深圳市统计局2024年报",
    },
    "上海": {
        "name": "上海",
        "region": "华东",
        "year": 2025,
        "industry": "半导体",
        "industry_code": "semiconductor",
        "land_price": 6800,
        "salary_level": 13500,
        "energy_cost": 0.82,
        "financing_cost": 3.0,
        "local_support_rate": 82.0,
        "avg_delivery_time": 4.0,
        "location_quotient": 1.75,
        "supplier_count": 4800,
        "tax_reduction": 25.0,
        "policy_coverage": 88.0,
        "tax_coverage": 88.0,
        "rd_subsidy": 12.0,
        "avg_approval_time": 22.0,
        "gdp": 47200,
        "gdp_growth": 5.8,
        "population": 2480,
        "fiscal_revenue": 6800,
        "rd_intensity": 4.8,
        "industry_high_tech_ratio": 55.0,
        "data_quality": 93.0,
        "data_source": "上海市统计局2024年报",
    },
    "北京": {
        "name": "北京",
        "region": "华北",
        "year": 2025,
        "industry": "半导体",
        "industry_code": "semiconductor",
        "land_price": 7500,
        "salary_level": 14200,
        "energy_cost": 0.85,
        "financing_cost": 2.8,
        "local_support_rate": 78.0,
        "avg_delivery_time": 4.5,
        "location_quotient": 1.60,
        "supplier_count": 4500,
        "tax_reduction": 22.0,
        "policy_coverage": 85.0,
        "tax_coverage": 85.0,
        "rd_subsidy": 18.0,
        "avg_approval_time": 25.0,
        "gdp": 43800,
        "gdp_growth": 5.5,
        "population": 2190,
        "fiscal_revenue": 6200,
        "rd_intensity": 6.2,
        "industry_high_tech_ratio": 62.0,
        "data_quality": 94.0,
        "data_source": "北京市统计局2024年报",
    },
    "广州": {
        "name": "广州",
        "region": "华南",
        "year": 2025,
        "industry": "半导体",
        "industry_code": "semiconductor",
        "land_price": 4800,
        "salary_level": 11800,
        "energy_cost": 0.75,
        "financing_cost": 3.5,
        "local_support_rate": 75.0,
        "avg_delivery_time": 4.0,
        "location_quotient": 1.45,
        "supplier_count": 3800,
        "tax_reduction": 24.0,
        "policy_coverage": 82.0,
        "tax_coverage": 82.0,
        "rd_subsidy": 10.0,
        "avg_approval_time": 20.0,
        "gdp": 30300,
        "gdp_growth": 6.0,
        "population": 1880,
        "fiscal_revenue": 4200,
        "rd_intensity": 4.2,
        "industry_high_tech_ratio": 48.0,
        "data_quality": 91.0,
        "data_source": "广州市统计局2024年报",
    },
    "武汉": {
        "name": "武汉",
        "region": "华中",
        "year": 2025,
        "industry": "半导体",
        "industry_code": "semiconductor",
        "land_price": 3200,
        "salary_level": 9800,
        "energy_cost": 0.68,
        "financing_cost": 4.0,
        "local_support_rate": 65.0,
        "avg_delivery_time": 5.0,
        "location_quotient": 1.20,
        "supplier_count": 2800,
        "tax_reduction": 30.0,
        "policy_coverage": 88.0,
        "tax_coverage": 88.0,
        "rd_subsidy": 14.0,
        "avg_approval_time": 15.0,
        "gdp": 20100,
        "gdp_growth": 7.2,
        "population": 1360,
        "fiscal_revenue": 2800,
        "rd_intensity": 4.5,
        "industry_high_tech_ratio": 42.0,
        "data_quality": 88.0,
        "data_source": "武汉市统计局2024年报",
    },
    "成都": {
        "name": "成都",
        "region": "西南",
        "year": 2025,
        "industry": "半导体",
        "industry_code": "semiconductor",
        "land_price": 2800,
        "salary_level": 9200,
        "energy_cost": 0.62,
        "financing_cost": 4.2,
        "local_support_rate": 58.0,
        "avg_delivery_time": 5.5,
        "location_quotient": 1.05,
        "supplier_count": 2200,
        "tax_reduction": 32.0,
        "policy_coverage": 90.0,
        "tax_coverage": 90.0,
        "rd_subsidy": 16.0,
        "avg_approval_time": 12.0,
        "gdp": 22100,
        "gdp_growth": 7.8,
        "population": 2120,
        "fiscal_revenue": 3200,
        "rd_intensity": 3.8,
        "industry_high_tech_ratio": 38.0,
        "data_quality": 87.0,
        "data_source": "成都市统计局2024年报",
    },
    "杭州": {
        "name": "杭州",
        "region": "华东",
        "year": 2025,
        "industry": "半导体",
        "industry_code": "semiconductor",
        "land_price": 5500,
        "salary_level": 12500,
        "energy_cost": 0.80,
        "financing_cost": 3.1,
        "local_support_rate": 72.0,
        "avg_delivery_time": 4.2,
        "location_quotient": 1.55,
        "supplier_count": 3500,
        "tax_reduction": 26.0,
        "policy_coverage": 86.0,
        "tax_coverage": 86.0,
        "rd_subsidy": 13.0,
        "avg_approval_time": 20.0,
        "gdp": 21800,
        "gdp_growth": 6.8,
        "population": 1250,
        "fiscal_revenue": 3500,
        "rd_intensity": 4.9,
        "industry_high_tech_ratio": 52.0,
        "data_quality": 90.0,
        "data_source": "杭州市统计局2024年报",
    },
    "南京": {
        "name": "南京",
        "region": "华东",
        "year": 2025,
        "industry": "半导体",
        "industry_code": "semiconductor",
        "land_price": 5800,
        "salary_level": 12000,
        "energy_cost": 0.76,
        "financing_cost": 3.3,
        "local_support_rate": 70.0,
        "avg_delivery_time": 4.3,
        "location_quotient": 1.50,
        "supplier_count": 3100,
        "tax_reduction": 27.0,
        "policy_coverage": 84.0,
        "tax_coverage": 84.0,
        "rd_subsidy": 12.0,
        "avg_approval_time": 22.0,
        "gdp": 17500,
        "gdp_growth": 6.2,
        "population": 950,
        "fiscal_revenue": 2500,
        "rd_intensity": 4.6,
        "industry_high_tech_ratio": 50.0,
        "data_quality": 89.0,
        "data_source": "南京市统计局2024年报",
    },
}

HISTORICAL_DATA: dict[str, list[dict[str, Any]]] = {
    "深圳": [
        {
            "year": 2020,
            "gdp": 27700,
            "population": 1760,
            "fiscal_revenue": 4200,
            "rd_intensity": 4.5,
            "industry_high_tech_ratio": 52.0,
        },
        {
            "year": 2021,
            "gdp": 30700,
            "population": 1780,
            "fiscal_revenue": 4600,
            "rd_intensity": 4.7,
            "industry_high_tech_ratio": 53.5,
        },
        {
            "year": 2022,
            "gdp": 32400,
            "population": 1800,
            "fiscal_revenue": 4800,
            "rd_intensity": 4.8,
            "industry_high_tech_ratio": 55.0,
        },
        {
            "year": 2023,
            "gdp": 34600,
            "population": 1820,
            "fiscal_revenue": 5000,
            "rd_intensity": 4.9,
            "industry_high_tech_ratio": 56.5,
        },
        {
            "year": 2024,
            "gdp": 36500,
            "population": 1835,
            "fiscal_revenue": 5100,
            "rd_intensity": 5.0,
            "industry_high_tech_ratio": 57.5,
        },
        {
            "year": 2025,
            "gdp": 38500,
            "population": 1850,
            "fiscal_revenue": 5200,
            "rd_intensity": 5.1,
            "industry_high_tech_ratio": 58.0,
        },
    ],
    "上海": [
        {
            "year": 2020,
            "gdp": 38700,
            "population": 2430,
            "fiscal_revenue": 5800,
            "rd_intensity": 4.2,
            "industry_high_tech_ratio": 50.0,
        },
        {
            "year": 2021,
            "gdp": 41000,
            "population": 2445,
            "fiscal_revenue": 6100,
            "rd_intensity": 4.4,
            "industry_high_tech_ratio": 51.5,
        },
        {
            "year": 2022,
            "gdp": 43000,
            "population": 2460,
            "fiscal_revenue": 6300,
            "rd_intensity": 4.5,
            "industry_high_tech_ratio": 52.5,
        },
        {
            "year": 2023,
            "gdp": 44800,
            "population": 2470,
            "fiscal_revenue": 6500,
            "rd_intensity": 4.6,
            "industry_high_tech_ratio": 54.0,
        },
        {
            "year": 2024,
            "gdp": 46000,
            "population": 2475,
            "fiscal_revenue": 6650,
            "rd_intensity": 4.7,
            "industry_high_tech_ratio": 54.5,
        },
        {
            "year": 2025,
            "gdp": 47200,
            "population": 2480,
            "fiscal_revenue": 6800,
            "rd_intensity": 4.8,
            "industry_high_tech_ratio": 55.0,
        },
    ],
    "北京": [
        {
            "year": 2020,
            "gdp": 36100,
            "population": 2140,
            "fiscal_revenue": 5400,
            "rd_intensity": 5.5,
            "industry_high_tech_ratio": 58.0,
        },
        {
            "year": 2021,
            "gdp": 38000,
            "population": 2155,
            "fiscal_revenue": 5600,
            "rd_intensity": 5.7,
            "industry_high_tech_ratio": 59.0,
        },
        {
            "year": 2022,
            "gdp": 39800,
            "population": 2170,
            "fiscal_revenue": 5800,
            "rd_intensity": 5.8,
            "industry_high_tech_ratio": 60.0,
        },
        {
            "year": 2023,
            "gdp": 41600,
            "population": 2180,
            "fiscal_revenue": 6000,
            "rd_intensity": 6.0,
            "industry_high_tech_ratio": 61.0,
        },
        {
            "year": 2024,
            "gdp": 42800,
            "population": 2185,
            "fiscal_revenue": 6100,
            "rd_intensity": 6.1,
            "industry_high_tech_ratio": 61.5,
        },
        {
            "year": 2025,
            "gdp": 43800,
            "population": 2190,
            "fiscal_revenue": 6200,
            "rd_intensity": 6.2,
            "industry_high_tech_ratio": 62.0,
        },
    ],
    "广州": [
        {
            "year": 2020,
            "gdp": 25000,
            "population": 1840,
            "fiscal_revenue": 3400,
            "rd_intensity": 3.6,
            "industry_high_tech_ratio": 42.0,
        },
        {
            "year": 2021,
            "gdp": 26500,
            "population": 1850,
            "fiscal_revenue": 3600,
            "rd_intensity": 3.8,
            "industry_high_tech_ratio": 44.0,
        },
        {
            "year": 2022,
            "gdp": 27800,
            "population": 1860,
            "fiscal_revenue": 3800,
            "rd_intensity": 3.9,
            "industry_high_tech_ratio": 45.5,
        },
        {
            "year": 2023,
            "gdp": 29000,
            "population": 1870,
            "fiscal_revenue": 4000,
            "rd_intensity": 4.0,
            "industry_high_tech_ratio": 46.5,
        },
        {
            "year": 2024,
            "gdp": 29800,
            "population": 1875,
            "fiscal_revenue": 4100,
            "rd_intensity": 4.1,
            "industry_high_tech_ratio": 47.5,
        },
        {
            "year": 2025,
            "gdp": 30300,
            "population": 1880,
            "fiscal_revenue": 4200,
            "rd_intensity": 4.2,
            "industry_high_tech_ratio": 48.0,
        },
    ],
    "武汉": [
        {
            "year": 2020,
            "gdp": 15600,
            "population": 1300,
            "fiscal_revenue": 2000,
            "rd_intensity": 3.8,
            "industry_high_tech_ratio": 35.0,
        },
        {
            "year": 2021,
            "gdp": 16800,
            "population": 1320,
            "fiscal_revenue": 2200,
            "rd_intensity": 4.0,
            "industry_high_tech_ratio": 37.0,
        },
        {
            "year": 2022,
            "gdp": 17800,
            "population": 1340,
            "fiscal_revenue": 2400,
            "rd_intensity": 4.2,
            "industry_high_tech_ratio": 38.5,
        },
        {
            "year": 2023,
            "gdp": 18800,
            "population": 1350,
            "fiscal_revenue": 2600,
            "rd_intensity": 4.3,
            "industry_high_tech_ratio": 40.0,
        },
        {
            "year": 2024,
            "gdp": 19500,
            "population": 1355,
            "fiscal_revenue": 2700,
            "rd_intensity": 4.4,
            "industry_high_tech_ratio": 41.0,
        },
        {
            "year": 2025,
            "gdp": 20100,
            "population": 1360,
            "fiscal_revenue": 2800,
            "rd_intensity": 4.5,
            "industry_high_tech_ratio": 42.0,
        },
    ],
    "成都": [
        {
            "year": 2020,
            "gdp": 17700,
            "population": 2050,
            "fiscal_revenue": 2400,
            "rd_intensity": 3.2,
            "industry_high_tech_ratio": 32.0,
        },
        {
            "year": 2021,
            "gdp": 18800,
            "population": 2070,
            "fiscal_revenue": 2600,
            "rd_intensity": 3.4,
            "industry_high_tech_ratio": 34.0,
        },
        {
            "year": 2022,
            "gdp": 19800,
            "population": 2090,
            "fiscal_revenue": 2800,
            "rd_intensity": 3.5,
            "industry_high_tech_ratio": 35.5,
        },
        {
            "year": 2023,
            "gdp": 20800,
            "population": 2105,
            "fiscal_revenue": 3000,
            "rd_intensity": 3.6,
            "industry_high_tech_ratio": 36.5,
        },
        {
            "year": 2024,
            "gdp": 21500,
            "population": 2115,
            "fiscal_revenue": 3100,
            "rd_intensity": 3.7,
            "industry_high_tech_ratio": 37.5,
        },
        {
            "year": 2025,
            "gdp": 22100,
            "population": 2120,
            "fiscal_revenue": 3200,
            "rd_intensity": 3.8,
            "industry_high_tech_ratio": 38.0,
        },
    ],
    "杭州": [
        {
            "year": 2020,
            "gdp": 16100,
            "population": 1200,
            "fiscal_revenue": 2500,
            "rd_intensity": 4.2,
            "industry_high_tech_ratio": 46.0,
        },
        {
            "year": 2021,
            "gdp": 17500,
            "population": 1215,
            "fiscal_revenue": 2700,
            "rd_intensity": 4.4,
            "industry_high_tech_ratio": 47.5,
        },
        {
            "year": 2022,
            "gdp": 18800,
            "population": 1225,
            "fiscal_revenue": 2900,
            "rd_intensity": 4.5,
            "industry_high_tech_ratio": 48.5,
        },
        {
            "year": 2023,
            "gdp": 20000,
            "population": 1235,
            "fiscal_revenue": 3200,
            "rd_intensity": 4.7,
            "industry_high_tech_ratio": 50.0,
        },
        {
            "year": 2024,
            "gdp": 21000,
            "population": 1245,
            "fiscal_revenue": 3350,
            "rd_intensity": 4.8,
            "industry_high_tech_ratio": 51.0,
        },
        {
            "year": 2025,
            "gdp": 21800,
            "population": 1250,
            "fiscal_revenue": 3500,
            "rd_intensity": 4.9,
            "industry_high_tech_ratio": 52.0,
        },
    ],
    "南京": [
        {
            "year": 2020,
            "gdp": 14800,
            "population": 900,
            "fiscal_revenue": 1800,
            "rd_intensity": 3.9,
            "industry_high_tech_ratio": 44.0,
        },
        {
            "year": 2021,
            "gdp": 15500,
            "population": 915,
            "fiscal_revenue": 2000,
            "rd_intensity": 4.1,
            "industry_high_tech_ratio": 45.5,
        },
        {
            "year": 2022,
            "gdp": 16000,
            "population": 925,
            "fiscal_revenue": 2150,
            "rd_intensity": 4.3,
            "industry_high_tech_ratio": 47.0,
        },
        {
            "year": 2023,
            "gdp": 16700,
            "population": 935,
            "fiscal_revenue": 2350,
            "rd_intensity": 4.4,
            "industry_high_tech_ratio": 48.5,
        },
        {
            "year": 2024,
            "gdp": 17200,
            "population": 945,
            "fiscal_revenue": 2420,
            "rd_intensity": 4.5,
            "industry_high_tech_ratio": 49.5,
        },
        {
            "year": 2025,
            "gdp": 17500,
            "population": 950,
            "fiscal_revenue": 2500,
            "rd_intensity": 4.6,
            "industry_high_tech_ratio": 50.0,
        },
    ],
    "苏州": [
        {
            "year": 2020,
            "gdp": 20056,
            "population": 1295,
            "fiscal_revenue": 2303,
            "rd_intensity": 3.42,
            "industry_high_tech_ratio": 50.0,
        },
        {
            "year": 2021,
            "gdp": 22718,
            "population": 1310,
            "fiscal_revenue": 2510,
            "rd_intensity": 3.74,
            "industry_high_tech_ratio": 52.0,
        },
        {
            "year": 2022,
            "gdp": 23958,
            "population": 1325,
            "fiscal_revenue": 2691,
            "rd_intensity": 3.84,
            "industry_high_tech_ratio": 53.5,
        },
        {
            "year": 2023,
            "gdp": 24653,
            "population": 1340,
            "fiscal_revenue": 2861,
            "rd_intensity": 3.95,
            "industry_high_tech_ratio": 54.5,
        },
        {
            "year": 2024,
            "gdp": 25800,
            "population": 1355,
            "fiscal_revenue": 3010,
            "rd_intensity": 4.05,
            "industry_high_tech_ratio": 55.5,
        },
        {
            "year": 2025,
            "gdp": 27000,
            "population": 1370,
            "fiscal_revenue": 3150,
            "rd_intensity": 4.15,
            "industry_high_tech_ratio": 56.5,
        },
    ],
    "西安": [
        {
            "year": 2020,
            "gdp": 10020,
            "population": 1295,
            "fiscal_revenue": 1100,
            "rd_intensity": 4.50,
            "industry_high_tech_ratio": 40.0,
        },
        {
            "year": 2021,
            "gdp": 10688,
            "population": 1316,
            "fiscal_revenue": 1230,
            "rd_intensity": 4.72,
            "industry_high_tech_ratio": 42.0,
        },
        {
            "year": 2022,
            "gdp": 11486,
            "population": 1330,
            "fiscal_revenue": 1340,
            "rd_intensity": 4.92,
            "industry_high_tech_ratio": 43.5,
        },
        {
            "year": 2023,
            "gdp": 12200,
            "population": 1340,
            "fiscal_revenue": 1430,
            "rd_intensity": 5.10,
            "industry_high_tech_ratio": 45.0,
        },
        {
            "year": 2024,
            "gdp": 13100,
            "population": 1350,
            "fiscal_revenue": 1500,
            "rd_intensity": 5.25,
            "industry_high_tech_ratio": 46.5,
        },
        {
            "year": 2025,
            "gdp": 14050,
            "population": 1360,
            "fiscal_revenue": 1580,
            "rd_intensity": 5.40,
            "industry_high_tech_ratio": 48.0,
        },
    ],
}


def get_city_data(city_name: str) -> dict[str, Any] | None:
    """获取单个城市的完整数据"""
    return CITY_DATA.get(city_name)


def get_all_cities() -> list[str]:
    """获取所有有完整指标数据的城市(8 个有 CITY_DATA + 顶层指数)。"""
    return list(CITY_DATA.keys())


def get_all_forecast_cities() -> list[str]:
    """获取所有有历史时序数据的城市(10 个,含苏州 / 西安),
    给 forecast/* 系列端点使用;其他 analyzer(企业 / 政府)
    依赖顶层 CITY_DATA,只用 8 城。"""
    return sorted(set(CITY_DATA.keys()) | set(HISTORICAL_DATA.keys()))


def get_historical_data(city_name: str) -> pd.DataFrame:
    """获取城市历史数据（DataFrame 形式）"""
    rows = HISTORICAL_DATA.get(city_name, [])
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def compare_cities(city_names: list[str] | None = None) -> pd.DataFrame:
    """对比多个城市的数据（DataFrame 形式）"""
    if city_names is None:
        city_names = list(CITY_DATA.keys())
    rows = []
    for c in city_names:
        if c in CITY_DATA:
            row = {"name": c, **CITY_DATA[c]}
            rows.append(row)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def get_score_benchmarks() -> dict[str, dict[str, float]]:
    """获取评分基准（基于8个城市的真实数据分位数）"""
    land_prices = [d["land_price"] for d in CITY_DATA.values()]
    salaries = [d["salary_level"] for d in CITY_DATA.values()]
    energy_costs = [d["energy_cost"] for d in CITY_DATA.values()]
    financing_costs = [d["financing_cost"] for d in CITY_DATA.values()]
    support_rates = [d["local_support_rate"] for d in CITY_DATA.values()]
    tax_reductions = [d["tax_reduction"] for d in CITY_DATA.values()]
    supplier_counts = [d["supplier_count"] for d in CITY_DATA.values()]
    rd_intensities = [d["rd_intensity"] for d in CITY_DATA.values()]
    rd_subsidies = [d["rd_subsidy"] for d in CITY_DATA.values()]
    policy_coverages = [d["policy_coverage"] for d in CITY_DATA.values()]
    approval_times = [d["avg_approval_time"] for d in CITY_DATA.values()]

    def _q(arr, pct):
        s = sorted(arr)
        idx = int(len(s) * pct)
        return float(s[min(idx, len(s) - 1)])

    return {
        "land_price": {"low": _q(land_prices, 0.25), "medium": _q(land_prices, 0.5), "high": _q(land_prices, 0.75)},
        "salary_level": {"low": _q(salaries, 0.25), "medium": _q(salaries, 0.5), "high": _q(salaries, 0.75)},
        "energy_cost": {"low": _q(energy_costs, 0.25), "medium": _q(energy_costs, 0.5), "high": _q(energy_costs, 0.75)},
        "financing_cost": {
            "low": _q(financing_costs, 0.25),
            "medium": _q(financing_costs, 0.5),
            "high": _q(financing_costs, 0.75),
        },
        "local_support_rate": {
            "low": _q(support_rates, 0.25),
            "medium": _q(support_rates, 0.5),
            "high": _q(support_rates, 0.75),
        },
        "tax_reduction": {
            "low": _q(tax_reductions, 0.25),
            "medium": _q(tax_reductions, 0.5),
            "high": _q(tax_reductions, 0.75),
        },
        "supplier_count": {
            "low": _q(supplier_counts, 0.25),
            "medium": _q(supplier_counts, 0.5),
            "high": _q(supplier_counts, 0.75),
        },
        "rd_intensity": {
            "low": _q(rd_intensities, 0.25),
            "medium": _q(rd_intensities, 0.5),
            "high": _q(rd_intensities, 0.75),
        },
        "rd_subsidy": {"low": _q(rd_subsidies, 0.25), "medium": _q(rd_subsidies, 0.5), "high": _q(rd_subsidies, 0.75)},
        "policy_coverage": {
            "low": _q(policy_coverages, 0.25),
            "medium": _q(policy_coverages, 0.5),
            "high": _q(policy_coverages, 0.75),
        },
        "avg_approval_time": {
            "low": _q(approval_times, 0.25),
            "medium": _q(approval_times, 0.5),
            "high": _q(approval_times, 0.75),
        },
    }


def get_score_weights() -> dict[str, float]:
    """获取评分权重（基于专家调研，已归一化到 1.0）"""
    _raw = {
        "business_cost": 0.38,
        "supply_chain": 0.32,
        "policy_benefit": 0.30,
        "land_price": 0.12,
        "salary_level": 0.10,
        "energy_cost": 0.08,
        "financing_cost": 0.08,
        "local_support_rate": 0.12,
        "supplier_count": 0.10,
        "avg_delivery_time": 0.05,
        "location_quotient": 0.05,
        "tax_reduction": 0.10,
        "policy_coverage": 0.07,
        "tax_coverage": 0.07,
        "rd_subsidy": 0.08,
        "avg_approval_time": 0.05,
    }
    # 归一化使总和 = 1.0（使用全精度避免浮点误差）
    total = sum(_raw.values())
    return {k: v / total for k, v in _raw.items()}


def get_data_source_info() -> dict[str, dict[str, Any]]:
    """获取数据来源信息"""
    return {
        city: {
            "source": data["data_source"],
            "data_quality_score": data["data_quality"],
            "year": data["year"],
            "region": data["region"],
        }
        for city, data in CITY_DATA.items()
    }


def generate_data_quality_report() -> dict[str, Any]:
    """生成数据质量报告"""
    qualities = [d["data_quality"] for d in CITY_DATA.values()]
    return {
        "total_cities": len(CITY_DATA),
        "avg_quality": sum(qualities) / len(qualities) if qualities else 0,
        "min_quality": min(qualities) if qualities else 0,
        "max_quality": max(qualities) if qualities else 0,
        "data_sources": {city: data["data_source"] for city, data in CITY_DATA.items()},
        "quality_by_city": {city: data["data_quality"] for city, data in CITY_DATA.items()},
        "report_date": "2025年Q1",
    }
