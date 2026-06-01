"""
机器学习模块 - 多种算法、模型选择、自动调优
"""
from .models import (
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
    get_model_instance,
    get_available_models,
)

try:
    from .models import XGBoostModel
except ImportError:
    pass

try:
    from .models import LightGBMModel
except ImportError:
    pass

try:
    from .models import ProphetModel
except ImportError:
    pass

from .trainer import (
    TrainingConfig,
    TrainingResult,
    ModelTrainer,
    TimeSeriesModelTrainer,
    AutoML,
    load_model,
    save_result,
)

__all__ = [
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
    'get_model_instance',
    'get_available_models',
    'TrainingConfig',
    'TrainingResult',
    'ModelTrainer',
    'TimeSeriesModelTrainer',
    'AutoML',
    'load_model',
    'save_result',
]
