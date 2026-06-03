"""
分析配置
"""

from typing import Any


class AnalysisConfig:
    """分析配置类"""

    # 默认分析参数
    DEFAULT_YEAR = 2025
    DEFAULT_REGION = "深圳"
    DEFAULT_INDUSTRY = "半导体"

    # 默认评分配置
    DEFAULT_SCORES = {
        "business_cost": 75.0,
        "supply_chain": 80.0,
        "policy_benefit": 70.0,
        "fiscal_leverage": 75.0,
        "industry_driving": 82.0,
    }

    # 评分权重配置
    SCORE_WEIGHTS = {
        "business_cost": {"land_cost": 0.3, "labor_cost": 0.4, "energy_cost": 0.2, "financing_cost": 0.1},
        "supply_chain": {"localization_rate": 0.4, "delivery_time": 0.3, "agglomeration_index": 0.3},
        "policy_benefit": {"tax_reduction": 0.3, "subsidy": 0.3, "approval_efficiency": 0.4},
        "fiscal_leverage": {"deficit_rate": 0.3, "self_sufficiency": 0.3, "funding_efficiency": 0.4},
        "industry_driving": {"employment": 0.3, "tax_contribution": 0.3, "related_industry": 0.4},
    }

    # 阈值配置
    THRESHOLDS = {
        "cost_high": 80.0,  # 成本高的阈值
        "cost_medium": 60.0,  # 成本中等的阈值
        "supply_chain_good": 75.0,
        "policy_benefit_good": 70.0,
        "fiscal_healthy": 70.0,
        "industry_driving_strong": 80.0,
    }

    # 分析维度开关
    ENABLED_ANALYSES = {
        "business_cost": True,
        "supply_chain": True,
        "policy_benefits": True,
        "fiscal_leverage": True,
        "industry_driving": True,
        "industry_chain": True,
    }

    # 数据采集指标配置
    DATA_COLLECTION = {
        "default_indicators": [
            "gdp",
            "cpi",
            "pmi",
            "fiscal_revenue",
            "fiscal_expenditure",
            "industrial_output",
            "employment",
        ],
        "years_range": [2020, 2021, 2022, 2023, 2024, 2025],
    }

    # 可视化配置
    VISUALIZATION = {
        "theme": "plotly_white",
        "default_width": 1200,
        "default_height": 600,
        "color_palette": [
            "#667eea",
            "#764ba2",
            "#f093fb",
            "#f5576c",
            "#4facfe",
            "#00f2fe",
            "#43e97b",
            "#38f9d7",
            "#fa709a",
            "#fee140",
        ],
        "charts": {
            "time_series": {"width": 1200, "height": 500},
            "bar": {"width": 1000, "height": 600},
            "radar": {"width": 800, "height": 800},
            "heatmap": {"width": 900, "height": 700},
            "dashboard": {"width": 1200, "height": 800},
        },
    }

    # 输出格式配置
    OUTPUT = {
        "formats": ["json", "csv", "excel", "html", "pdf"],
        "default_format": "json",
        "report_template": "default",
    }

    @classmethod
    def get_config(cls) -> dict[str, Any]:
        """获取完整配置"""
        return {
            "default_year": cls.DEFAULT_YEAR,
            "default_region": cls.DEFAULT_REGION,
            "default_industry": cls.DEFAULT_INDUSTRY,
            "default_scores": cls.DEFAULT_SCORES,
            "score_weights": cls.SCORE_WEIGHTS,
            "thresholds": cls.THRESHOLDS,
            "enabled_analyses": cls.ENABLED_ANALYSES,
            "data_collection": cls.DATA_COLLECTION,
            "visualization": cls.VISUALIZATION,
            "output": cls.OUTPUT,
        }
