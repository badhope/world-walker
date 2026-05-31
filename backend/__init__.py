"""
通用数据分析系统 - 完整框架
支持任意行业、任意地区的数据分析
"""
from .core import (
    ConfigManager,
    ProjectConfig,
    IndustryConfig,
    DimensionConfig,
    MetricConfig,
    MLConfig,
    get_config_manager,
    DataManager,
    Dataset,
    RegionData,
    get_data_manager,
    UniversalAnalyzer,
    AnalysisResult,
    create_sample_data,
    quick_start_demo,
)
from .ml import (
    BaseModel,
    ModelMetrics,
    ModelResult,
    LinearRegressionModel,
    RandomForestModel,
    GBDTModel,
    RidgeModel,
    LassoModel,
    SVRModel,
    KNNModel,
    get_model,
    get_available_models,
    TrainingConfig,
    TrainingResult,
    ModelTrainer,
    TimeSeriesModelTrainer,
    AutoML,
    load_model,
    save_result,
)

__version__ = "2.0.0"
__author__ = "Data Analyst"

__all__ = [
    # Core
    'ConfigManager',
    'ProjectConfig',
    'IndustryConfig',
    'DimensionConfig',
    'MetricConfig',
    'MLConfig',
    'get_config_manager',
    'DataManager',
    'Dataset',
    'RegionData',
    'get_data_manager',
    'UniversalAnalyzer',
    'AnalysisResult',
    'create_sample_data',
    'quick_start_demo',
    # ML
    'BaseModel',
    'ModelMetrics',
    'ModelResult',
    'LinearRegressionModel',
    'RandomForestModel',
    'GBDTModel',
    'RidgeModel',
    'LassoModel',
    'SVRModel',
    'KNNModel',
    'get_model',
    'get_available_models',
    'TrainingConfig',
    'TrainingResult',
    'ModelTrainer',
    'TimeSeriesModelTrainer',
    'AutoML',
    'load_model',
    'save_result',
]
