"""
模型训练器 - 支持多模型对比、自动调优、集成学习
"""
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from pathlib import Path
from sklearn.model_selection import train_test_split, TimeSeriesSplit, GridSearchCV, RandomizedSearchCV
import joblib

from backend.utils.model_security import save_with_signature, load_with_signature

from .models import (
    BaseModel, get_model_instance,
    ModelMetrics, ModelResult
)

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """训练配置"""
    model_names: List[str]
    target_column: str
    feature_columns: List[str]
    time_column: Optional[str] = None
    id_column: Optional[str] = None
    test_size: float = 0.2
    random_state: int = 42
    use_cross_validation: bool = True
    cv_folds: int = 5
    hyperparameter_tuning: bool = True
    tuning_method: str = 'grid'  # grid or random
    tuning_iterations: int = 50  # for random search
    scoring: str = 'r2'
    save_models: bool = True
    model_output_dir: str = './models'
    is_time_series: bool = False


@dataclass
class TrainingResult:
    """训练结果"""
    best_model: ModelResult
    all_results: List[ModelResult]
    config: TrainingConfig
    feature_importance: Optional[Dict[str, float]] = None
    
    def get_best_model_name(self) -> str:
        return self.best_model.model_name
    
    def get_best_metrics(self) -> ModelMetrics:
        return self.best_model.metrics


class ModelTrainer:
    """模型训练器"""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.results: List[ModelResult] = []
        self.X_train: Optional[pd.DataFrame] = None
        self.X_test: Optional[pd.DataFrame] = None
        self.y_train: Optional[pd.Series] = None
        self.y_test: Optional[pd.Series] = None
        
        if config.save_models:
            Path(config.model_output_dir).mkdir(exist_ok=True, parents=True)
    
    def prepare_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
        """准备训练数据"""
        X = df[self.config.feature_columns].copy()
        y = df[self.config.target_column].copy()
        
        # 处理缺失值
        X = X.fillna(0)
        
        if self.config.is_time_series and self.config.time_column:
            # 时间序列数据按时间分割
            df_sorted = df.sort_values(self.config.time_column)
            X = df_sorted[self.config.feature_columns]
            y = df_sorted[self.config.target_column]
            
            split_idx = int(len(X) * (1 - self.config.test_size))
            self.X_train, self.X_test = X.iloc[:split_idx], X.iloc[split_idx:]
            self.y_train, self.y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        else:
            # 随机分割
            self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
                X, y, test_size=self.config.test_size, random_state=self.config.random_state
            )
        
        logger.info(f"Data prepared: {len(self.X_train)} train, {len(self.X_test)} test samples")
        logger.info(f"Features: {self.config.feature_columns}")
        
        return self.X_train, self.X_test, self.y_train, self.y_test
    
    def train_single_model(self, model_name: str) -> ModelResult:
        """训练单个模型"""
        logger.info(f"Training model: {model_name}")
        
        model = get_model_instance(model_name)
        
        if self.config.hyperparameter_tuning:
            model = self._tune_hyperparameters(model)
        else:
            model.fit(self.X_train, self.y_train)
        
        # 评估
        metrics = model.evaluate(
            self.X_test, self.y_test,
            cv=self.config.cv_folds if self.config.use_cross_validation else None,
            X_train=self.X_train,
            y_train=self.y_train
        )
        
        logger.info(f"Model {model_name} metrics: {metrics}")
        
        # 获取特征重要性
        feature_importance = model.get_feature_importance()
        
        # 获取预测结果
        predictions = model.predict(self.X_test)
        
        # 获取超参数
        hyperparams = model.get_default_params() if hasattr(model, 'get_default_params') else None
        if hasattr(model.model, 'get_params'):
            hyperparams = model.model.get_params()
        
        # 保存模型
        if self.config.save_models:
            model_path = f"{self.config.model_output_dir}/{model_name}.pkl"
            model.save(model_path)
        
        result = ModelResult(
            model_name=model_name,
            model=model,
            metrics=metrics,
            feature_importance=feature_importance,
            predictions=predictions,
            hyperparameters=hyperparams,
        )
        
        return result
    
    def _tune_hyperparameters(self, model: BaseModel) -> BaseModel:
        """超参数调优"""
        logger.info(f"Tuning hyperparameters for {model.name}")
        
        param_grid = model.get_param_grid()
        n_jobs = min(os.cpu_count() or 1, 4)
        
        if self.config.tuning_method == 'grid':
            search = GridSearchCV(
                model.build_model(),
                param_grid=param_grid,
                cv=self.config.cv_folds,
                scoring=self.config.scoring,
                n_jobs=n_jobs,
                verbose=1,
            )
        else:
            search = RandomizedSearchCV(
                model.build_model(),
                param_distributions=param_grid,
                n_iter=self.config.tuning_iterations,
                cv=self.config.cv_folds,
                scoring=self.config.scoring,
                n_jobs=n_jobs,
                random_state=self.config.random_state,
                verbose=1,
            )
        
        search.fit(self.X_train, self.y_train)
        
        logger.info(f"Best params for {model.name}: {search.best_params_}")
        logger.info(f"Best score: {search.best_score_:.4f}")
        
        # 使用最佳参数重新训练
        model.fit(self.X_train, self.y_train, **search.best_params_)
        return model
    
    def train_all_models(self) -> TrainingResult:
        """训练所有模型"""
        self.results = []
        
        for model_name in self.config.model_names:
            try:
                result = self.train_single_model(model_name)
                self.results.append(result)
            except Exception as e:
                logger.error(f"Failed to train {model_name}: {e}", exc_info=True)
        
        if not self.results:
            raise RuntimeError("No models were trained successfully")
        
        # 找到最佳模型
        self.results.sort(key=lambda x: x.metrics.r2, reverse=True)
        best_result = self.results[0]
        
        logger.info(f"Best model: {best_result.model_name} (R2: {best_result.metrics.r2:.4f})")
        
        return TrainingResult(
            best_model=best_result,
            all_results=self.results,
            config=self.config,
        )
    
    def compare_models(self, sort_by: str = 'r2') -> pd.DataFrame:
        """模型对比"""
        data = []
        for result in self.results:
            data.append({
                'model': result.model_name,
                'mae': result.metrics.mae,
                'rmse': result.metrics.rmse,
                'mape': result.metrics.mape,
                'r2': result.metrics.r2,
            })
        
        df = pd.DataFrame(data)
        df = df.sort_values(sort_by, ascending=sort_by not in ['r2'])
        return df
    
    def predict_best(self, X: pd.DataFrame) -> np.ndarray:
        """使用最佳模型预测"""
        if not self.results:
            raise RuntimeError("No models trained yet")
        return self.results[0].model.predict(X)
    
    def load_best_model(self) -> BaseModel:
        """加载最佳模型"""
        if not self.results:
            raise RuntimeError("No models trained yet")
        return self.results[0].model
    
    def get_ensemble_prediction(self, X: pd.DataFrame, method: str = 'mean') -> np.ndarray:
        """集成预测"""
        predictions = []
        for result in self.results:
            pred = result.model.predict(X)
            predictions.append(pred)
        
        if method == 'mean':
            return np.mean(predictions, axis=0)
        elif method == 'median':
            return np.median(predictions, axis=0)
        elif method == 'weighted':
            # 基于R2加权
            weights = np.array([r.metrics.r2 for r in self.results])
            weights = weights / weights.sum()
            return np.sum(predictions * weights[:, None], axis=0)
        else:
            raise ValueError(f"Unknown ensemble method: {method}")


class TimeSeriesModelTrainer(ModelTrainer):
    """时间序列专用训练器"""
    
    def __init__(self, config: TrainingConfig):
        config.is_time_series = True
        super().__init__(config)
    
    def prepare_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
        """准备时间序列数据"""
        if self.config.time_column not in df.columns:
            raise ValueError(f"Time column {self.config.time_column} not found")
        
        df = df.sort_values(self.config.time_column).reset_index(drop=True)
        return super().prepare_data(df)


class AutoML:
    """自动化机器学习 - 一键训练多个模型并选优"""
    
    def __init__(
        self,
        target_column: str,
        feature_columns: List[str],
        model_names: Optional[List[str]] = None,
        time_column: Optional[str] = None,
        **kwargs
    ):
        if model_names is None:
            model_names = get_available_models()
        
        self.config = TrainingConfig(
            model_names=model_names,
            target_column=target_column,
            feature_columns=feature_columns,
            time_column=time_column,
            **kwargs
        )
        
        self.trainer = ModelTrainer(self.config) if time_column is None \
            else TimeSeriesModelTrainer(self.config)
        
        self.result: Optional[TrainingResult] = None
    
    def fit(self, df: pd.DataFrame) -> TrainingResult:
        """训练"""
        self.trainer.prepare_data(df)
        self.result = self.trainer.train_all_models()
        return self.result
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """预测"""
        if self.result is None:
            raise RuntimeError("Model not trained yet")
        return self.trainer.predict_best(X)
    
    def get_best_model(self) -> BaseModel:
        """获取最佳模型"""
        if self.result is None:
            raise RuntimeError("Model not trained yet")
        return self.result.best_model.model
    
    def get_comparison(self) -> pd.DataFrame:
        """获取模型对比"""
        if self.result is None:
            raise RuntimeError("Model not trained yet")
        return self.trainer.compare_models()
    
    def get_feature_importance(self) -> Dict[str, float]:
        """获取特征重要性"""
        if self.result is None or self.result.best_model.feature_importance is None:
            return {}
        return self.result.best_model.feature_importance


def load_model(path: str) -> BaseModel:
    """加载已保存的模型"""
    model = load_with_signature(path)
    return model


def save_result(result: TrainingResult, path: str):
    """保存训练结果"""
    data = {
        'best_model_name': result.best_model.model_name,
        'best_metrics': result.best_model.metrics.to_dict(),
        'all_metrics': {r.model_name: r.metrics.to_dict() for r in result.all_results},
        'config': result.config,
    }
    save_with_signature(data, path)
