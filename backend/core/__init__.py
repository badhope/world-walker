"""
核心模块 - 通用数据分析系统
包含配置管理、数据管理和通用分析器
"""

from .analyzer import (
    AnalysisResult,
    UniversalAnalyzer,
    create_sample_data,
    quick_start_demo,
)
from .config import (
    ConfigManager,
    DimensionConfig,
    IndustryConfig,
    MetricConfig,
    MLConfig,
    ProjectConfig,
    get_config_manager,
)
from .data_manager import (
    DataManager,
    Dataset,
    RegionData,
    get_data_manager,
)

__all__ = [
    "ConfigManager",
    "ProjectConfig",
    "IndustryConfig",
    "DimensionConfig",
    "MetricConfig",
    "MLConfig",
    "get_config_manager",
    "DataManager",
    "Dataset",
    "RegionData",
    "get_data_manager",
    "UniversalAnalyzer",
    "AnalysisResult",
    "create_sample_data",
    "quick_start_demo",
]
