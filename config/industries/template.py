"""
产业配置模板
"""

from typing import Any


class IndustryConfig:
    """产业配置基类"""

    # 产业基本信息
    name: str = ""
    code: str = ""
    category: str = ""
    industry_level: str = "secondary"  # primary, secondary, tertiary

    # 产业链环节
    chain_links: list[str] = []

    # 关键指标定义
    key_indicators: dict[str, Any] = {}

    # 产业特点
    characteristics: list[str] = []

    # 产业链分析配置
    chain_analysis: dict[str, Any] = {
        "upstream_weight": 0.3,
        "midstream_weight": 0.4,
        "downstream_weight": 0.3,
        "key_bottlenecks": [],
    }

    # 市场规模和增长率
    market_data: dict[str, Any] = {
        "market_size": 0.0,  # 亿元
        "growth_rate": 0.0,  # %
        "global_market_share": 0.0,  # %
        "export_ratio": 0.0,  # %
    }

    # 技术成熟度
    technology_maturity: dict[str, Any] = {
        "rd_intensity": 0.0,  # 研发强度
        "patent_count": 0,
        "technology_level": "developing",  # leading, developing, catching_up
    }

    # 企业结构
    enterprise_structure: dict[str, Any] = {
        "total_enterprises": 0,
        "large_enterprises": 0,
        "sme_count": 0,
        "leading_enterprises": [],
    }

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": cls.name,
            "code": cls.code,
            "category": cls.category,
            "industry_level": cls.industry_level,
            "chain_links": cls.chain_links,
            "key_indicators": cls.key_indicators,
            "characteristics": cls.characteristics,
            "chain_analysis": cls.chain_analysis,
            "market_data": cls.market_data,
            "technology_maturity": cls.technology_maturity,
            "enterprise_structure": cls.enterprise_structure,
        }
