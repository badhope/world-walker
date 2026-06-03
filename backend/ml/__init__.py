"""
机器学习模块 - 多种算法、模型选择、自动调优
"""

from .models import (
    BaseModel,
    GBDTModel,
    KNNModel,
    LassoModel,
    LinearRegressionModel,
    ModelMetrics,
    ModelResult,
    RandomForestModel,
    RidgeModel,
    SVRModel,
    get_available_models,
    get_model_instance,
)

try:
    from .models import XGBoostModel  # noqa: F401
except ImportError:
    pass

try:
    from .models import LightGBMModel  # noqa: F401
except ImportError:
    pass

try:
    from .models import ProphetModel  # noqa: F401
except ImportError:
    pass

from .trainer import (
    AutoML,
    ModelTrainer,
    TimeSeriesModelTrainer,
    TrainingConfig,
    TrainingResult,
    load_model,
    save_result,
)

__all__ = [
    "BaseModel",
    "ModelMetrics",
    "ModelResult",
    "LinearRegressionModel",
    "RandomForestModel",
    "GBDTModel",
    "RidgeModel",
    "LassoModel",
    "SVRModel",
    "KNNModel",
    "get_model_instance",
    "get_available_models",
    "TrainingConfig",
    "TrainingResult",
    "ModelTrainer",
    "TimeSeriesModelTrainer",
    "AutoML",
    "load_model",
    "save_result",
]
