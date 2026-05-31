"""
机器学习模型系统 - 严格实现多种算法
支持模型选择、自动调优、交叉验证
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging
from pathlib import Path
import joblib

# Scikit-learn models
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import (
    train_test_split, cross_val_score, GridSearchCV, 
    RandomizedSearchCV, TimeSeriesSplit
)
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    mean_absolute_percentage_error
)
from sklearn.inspection import permutation_importance

# XGBoost
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logging.warning("XGBoost not available")

# LightGBM
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logging.warning("LightGBM not available")

# Prophet
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logging.warning("Prophet not available")

logger = logging.getLogger(__name__)


@dataclass
class ModelMetrics:
    """模型评估指标"""
    mae: float
    rmse: float
    mape: float
    r2: float
    cv_scores: Optional[List[float]] = None
    
    def __str__(self):
        return (f"MAE: {self.mae:.4f}, RMSE: {self.rmse:.4f}, "
                f"MAPE: {self.mape:.4f}, R2: {self.r2:.4f}")
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'mae': self.mae,
            'rmse': self.rmse,
            'mape': self.mape,
            'r2': self.r2,
            'cv_scores': self.cv_scores,
        }


@dataclass
class ModelResult:
    """模型训练结果"""
    model_name: str
    model: Any
    metrics: ModelMetrics
    feature_importance: Optional[Dict[str, float]] = None
    predictions: Optional[np.ndarray] = None
    hyperparameters: Optional[Dict] = None


class BaseModel(ABC):
    """机器学习模型基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.model = None
        self.is_trained = False
        self.scaler = StandardScaler()
        self.feature_names: List[str] = []
        
    @abstractmethod
    def build_model(self, **kwargs) -> Any:
        """构建模型"""
        pass
    
    @abstractmethod
    def get_default_params(self) -> Dict:
        """获取默认参数"""
        pass
    
    @abstractmethod
    def get_param_grid(self) -> Dict:
        """获取超参数网格用于调优"""
        pass
    
    def fit(self, X: pd.DataFrame, y: pd.Series, **kwargs) -> 'BaseModel':
        """训练模型"""
        self.feature_names = X.columns.tolist()
        
        self.model = self.build_model(**kwargs)
        
        if self.name in ['prophet']:
            # Prophet需要特殊格式
            prophet_df = pd.DataFrame({
                'ds': X.index if isinstance(X.index, pd.DatetimeIndex) 
                     else pd.date_range(start='2020-01-01', periods=len(X)),
                'y': y.values
            })
            self.model.fit(prophet_df)
        else:
            self.model.fit(X, y)
        
        self.is_trained = True
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """预测"""
        if not self.is_trained:
            raise RuntimeError("Model not trained")
        
        if self.name == 'prophet':
            prophet_df = pd.DataFrame({
                'ds': X.index if isinstance(X.index, pd.DatetimeIndex)
                     else pd.date_range(start='2020-01-01', periods=len(X))
            })
            forecast = self.model.predict(prophet_df)
            return forecast['yhat'].values
        else:
            return self.model.predict(X)
    
    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series,
                cv: Optional[int] = None, X_train: Optional[pd.DataFrame] = None,
                y_train: Optional[pd.Series] = None) -> ModelMetrics:
        """评估模型"""
        y_pred = self.predict(X_test)
        
        metrics = ModelMetrics(
            mae=float(mean_absolute_error(y_test, y_pred)),
            rmse=float(np.sqrt(mean_squared_error(y_test, y_pred))),
            mape=float(mean_absolute_percentage_error(y_test, y_pred)),
            r2=float(r2_score(y_test, y_pred)),
        )
        
        if cv and X_train is not None and y_train is not None:
            cv_scores = cross_val_score(
                self.model, X_train, y_train, cv=cv,
                scoring='r2'
            )
            metrics.cv_scores = cv_scores.tolist()
        
        return metrics
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """获取特征重要性"""
        if not self.is_trained:
            return None
        
        importance = None
        
        if hasattr(self.model, 'feature_importances_'):
            importance = self.model.feature_importances_
        elif hasattr(self.model, 'coef_'):
            importance = np.abs(self.model.coef_)
        
        if importance is not None:
            return dict(zip(self.feature_names, importance))
        
        return None
    
    def save(self, path: str):
        """保存模型"""
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'scaler': self.scaler,
        }
        joblib.dump(model_data, path)
        logger.info(f"Model saved to {path}")
    
    def load(self, path: str) -> 'BaseModel':
        """加载模型"""
        model_data = joblib.load(path)
        self.model = model_data['model']
        self.feature_names = model_data['feature_names']
        self.scaler = model_data['scaler']
        self.is_trained = True
        logger.info(f"Model loaded from {path}")
        return self


class LinearRegressionModel(BaseModel):
    """线性回归模型"""
    
    def __init__(self):
        super().__init__('linear_regression')
    
    def build_model(self, **kwargs) -> Any:
        return LinearRegression(**kwargs)
    
    def get_default_params(self) -> Dict:
        return {}
    
    def get_param_grid(self) -> Dict:
        return {
            'fit_intercept': [True, False],
        }


class RandomForestModel(BaseModel):
    """随机森林模型"""
    
    def __init__(self):
        super().__init__('random_forest')
    
    def build_model(self, **kwargs) -> Any:
        default_params = self.get_default_params()
        default_params.update(kwargs)
        return RandomForestRegressor(**default_params, random_state=42)
    
    def get_default_params(self) -> Dict:
        return {
            'n_estimators': 100,
            'max_depth': 10,
            'min_samples_split': 2,
            'min_samples_leaf': 1,
        }
    
    def get_param_grid(self) -> Dict:
        return {
            'n_estimators': [50, 100, 200, 300],
            'max_depth': [5, 10, 20, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'max_features': ['sqrt', 'log2', None],
        }


class GBDTModel(BaseModel):
    """梯度提升树模型"""
    
    def __init__(self):
        super().__init__('gbdt')
    
    def build_model(self, **kwargs) -> Any:
        default_params = self.get_default_params()
        default_params.update(kwargs)
        return GradientBoostingRegressor(**default_params, random_state=42)
    
    def get_default_params(self) -> Dict:
        return {
            'n_estimators': 100,
            'learning_rate': 0.1,
            'max_depth': 5,
            'subsample': 0.8,
        }
    
    def get_param_grid(self) -> Dict:
        return {
            'n_estimators': [50, 100, 200, 300],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'max_depth': [3, 5, 7, 10],
            'subsample': [0.6, 0.8, 1.0],
            'max_features': ['sqrt', 'log2', None],
        }


class XGBoostModel(BaseModel):
    """XGBoost模型"""
    
    def __init__(self):
        super().__init__('xgboost')
    
    def build_model(self, **kwargs) -> Any:
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost is not available")
        default_params = self.get_default_params()
        default_params.update(kwargs)
        return xgb.XGBRegressor(**default_params, random_state=42, objective='reg:squarederror')
    
    def get_default_params(self) -> Dict:
        return {
            'n_estimators': 100,
            'learning_rate': 0.1,
            'max_depth': 5,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'reg_alpha': 0,
            'reg_lambda': 1,
        }
    
    def get_param_grid(self) -> Dict:
        return {
            'n_estimators': [50, 100, 200, 300],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'max_depth': [3, 5, 7, 10],
            'subsample': [0.6, 0.8, 1.0],
            'colsample_bytree': [0.6, 0.8, 1.0],
            'reg_alpha': [0, 0.1, 1],
            'reg_lambda': [0.1, 1, 10],
        }


class LightGBMModel(BaseModel):
    """LightGBM模型"""
    
    def __init__(self):
        super().__init__('lightgbm')
    
    def build_model(self, **kwargs) -> Any:
        if not LIGHTGBM_AVAILABLE:
            raise ImportError("LightGBM is not available")
        default_params = self.get_default_params()
        default_params.update(kwargs)
        return lgb.LGBMRegressor(**default_params, random_state=42, verbose=-1)
    
    def get_default_params(self) -> Dict:
        return {
            'n_estimators': 100,
            'learning_rate': 0.1,
            'max_depth': 5,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
        }
    
    def get_param_grid(self) -> Dict:
        return {
            'n_estimators': [50, 100, 200, 300],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'max_depth': [3, 5, 7, 10],
            'num_leaves': [15, 31, 63, 127],
            'subsample': [0.6, 0.8, 1.0],
            'colsample_bytree': [0.6, 0.8, 1.0],
        }


class ProphetModel(BaseModel):
    """Prophet时间序列模型"""
    
    def __init__(self):
        super().__init__('prophet')
    
    def build_model(self, **kwargs) -> Any:
        if not PROPHET_AVAILABLE:
            raise ImportError("Prophet is not available")
        default_params = self.get_default_params()
        default_params.update(kwargs)
        return Prophet(**default_params)
    
    def get_default_params(self) -> Dict:
        return {
            'yearly_seasonality': True,
            'weekly_seasonality': False,
            'daily_seasonality': False,
            'seasonality_mode': 'additive',
        }
    
    def get_param_grid(self) -> Dict:
        return {
            'yearly_seasonality': [True, False],
            'seasonality_mode': ['additive', 'multiplicative'],
            'changepoint_prior_scale': [0.001, 0.01, 0.1, 0.5],
            'seasonality_prior_scale': [0.01, 0.1, 1.0, 10.0],
        }


class RidgeModel(BaseModel):
    """岭回归模型"""
    
    def __init__(self):
        super().__init__('ridge')
    
    def build_model(self, **kwargs) -> Any:
        return Ridge(**kwargs)
    
    def get_default_params(self) -> Dict:
        return {'alpha': 1.0}
    
    def get_param_grid(self) -> Dict:
        return {
            'alpha': [0.001, 0.01, 0.1, 1.0, 10.0, 100.0],
            'fit_intercept': [True, False],
        }


class LassoModel(BaseModel):
    """Lasso回归模型"""
    
    def __init__(self):
        super().__init__('lasso')
    
    def build_model(self, **kwargs) -> Any:
        return Lasso(**kwargs)
    
    def get_default_params(self) -> Dict:
        return {'alpha': 1.0}
    
    def get_param_grid(self) -> Dict:
        return {
            'alpha': [0.001, 0.01, 0.1, 1.0, 10.0, 100.0],
            'fit_intercept': [True, False],
        }


class SVRModel(BaseModel):
    """支持向量回归模型"""
    
    def __init__(self):
        super().__init__('svr')
    
    def build_model(self, **kwargs) -> Any:
        default_params = self.get_default_params()
        default_params.update(kwargs)
        return SVR(**default_params)
    
    def get_default_params(self) -> Dict:
        return {
            'kernel': 'rbf',
            'C': 1.0,
            'epsilon': 0.1,
        }
    
    def get_param_grid(self) -> Dict:
        return {
            'kernel': ['linear', 'rbf', 'poly'],
            'C': [0.1, 1.0, 10.0, 100.0],
            'epsilon': [0.01, 0.1, 0.5],
            'gamma': ['scale', 'auto'],
        }


class KNNModel(BaseModel):
    """K近邻回归模型"""
    
    def __init__(self):
        super().__init__('knn')
    
    def build_model(self, **kwargs) -> Any:
        default_params = self.get_default_params()
        default_params.update(kwargs)
        return KNeighborsRegressor(**default_params)
    
    def get_default_params(self) -> Dict:
        return {
            'n_neighbors': 5,
            'weights': 'uniform',
            'p': 2,
        }
    
    def get_param_grid(self) -> Dict:
        return {
            'n_neighbors': [3, 5, 7, 10, 15],
            'weights': ['uniform', 'distance'],
            'p': [1, 2],
        }


# 模型注册表
MODEL_REGISTRY: Dict[str, BaseModel] = {
    'linear_regression': LinearRegressionModel(),
    'ridge': RidgeModel(),
    'lasso': LassoModel(),
    'random_forest': RandomForestModel(),
    'gbdt': GBDTModel(),
    'svr': SVRModel(),
    'knn': KNNModel(),
}

if XGBOOST_AVAILABLE:
    MODEL_REGISTRY['xgboost'] = XGBoostModel()

if LIGHTGBM_AVAILABLE:
    MODEL_REGISTRY['lightgbm'] = LightGBMModel()

if PROPHET_AVAILABLE:
    MODEL_REGISTRY['prophet'] = ProphetModel()


def get_model(name: str) -> BaseModel:
    """获取模型实例"""
    if name not in MODEL_REGISTRY:
        raise ValueError(f"Model {name} not available. Available models: {list(MODEL_REGISTRY.keys())}")
    return MODEL_REGISTRY[name]


def get_available_models() -> List[str]:
    """获取可用模型列表"""
    return list(MODEL_REGISTRY.keys())
