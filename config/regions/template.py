"""
地区配置模板
"""

from typing import Any


class RegionConfig:
    """地区配置基类"""

    # 地区基本信息
    name: str = ""
    code: str = ""
    province: str = ""
    country: str = "中国"

    # 统计口径
    statistical_caliber: str = "city"  # city, province, country

    # 行政区划
    administrative_divisions: dict[str, Any] = {}

    # 经济指标权重
    indicator_weights: dict[str, float] = {}

    # 地区经济特征
    economic_characteristics: list[str] = []

    # 基准数据（用于对比分析）
    benchmark_data: dict[str, Any] = {"gdp_per_capita": 0.0, "average_wage": 0.0, "industrial_efficiency": 0.0}

    # 数据来源配置
    data_sources: list[str] = [
        "nbs",  # 国家统计局
        "local_statistics_bureau",  # 地方统计局
        "industry_association",  # 行业协会
    ]

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": cls.name,
            "code": cls.code,
            "province": cls.province,
            "country": cls.country,
            "statistical_caliber": cls.statistical_caliber,
            "administrative_divisions": cls.administrative_divisions,
            "indicator_weights": cls.indicator_weights,
            "economic_characteristics": cls.economic_characteristics,
            "benchmark_data": cls.benchmark_data,
            "data_sources": cls.data_sources,
        }
