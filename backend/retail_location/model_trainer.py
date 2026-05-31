"""
零售门店模型训练器
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import joblib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class RetailModelTrainer:
    """零售门店模型训练器"""
    
    def __init__(self, config: Optional[Any] = None):
        self.config = config
        self.models = {}
        self.best_model = None
        self.best_model_name = None
        self.model_scores = {}
        self.feature_importances = {}
        self.training_history = []
    
    # ==================== 模型定义 ====================
    
    def _get_model(self, model_name: str, params: Optional[Dict] = None) -> Any:
        """获取模型实例"""
        if params is None:
            params = {}
        
        model_map = {
            "linear": LinearRegression,
            "ridge": Ridge,
            "lasso": Lasso,
            "random_forest": RandomForestRegressor,
            "gbm": GradientBoostingRegressor,
        }
        
        # 模型默认参数
        default_params = {
            "linear": {},
            "ridge": {"alpha": 1.0, "random_state": 42},
            "lasso": {"alpha": 1.0, "random_state": 42},
            "random_forest": {
                "n_estimators": 100,
                "max_depth": 10,
                "min_samples_split": 5,
                "random_state": 42,
                "n_jobs": -1
            },
            "gbm": {
                "n_estimators": 100,
                "learning_rate": 0.1,
                "max_depth": 5,
                "random_state": 42
            },
        }
        
        if model_name not in model_map:
            raise ValueError(f"Unknown model: {model_name}")
        
        merged_params = {**default_params.get(model_name, {}), **params}
        return model_map[model_name](**merged_params)
    
    # ==================== 数据准备 ====================
    
    def prepare_data(
        self,
        df: pd.DataFrame,
        target_col: str,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        准备训练数据和测试数据
        
        Returns:
            (X_train, X_test, y_train, y_test)
        """
        feature_cols = [col for col in df.columns if col != target_col]
        X = df[feature_cols]
        y = df[target_col]
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        logger.info(f"Data split: train={len(X_train)}, test={len(X_test)}")
        return X_train, X_test, y_train, y_test
    
    # ==================== 单模型训练 ====================
    
    def train_single_model(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        model_name: str,
        params: Optional[Dict] = None
    ) -> Tuple[Any, Dict[str, float]]:
        """
        训练单个模型
        
        Returns:
            (训练好的模型, 交叉验证得分)
        """
        logger.info(f"Training model: {model_name}")
        
        model = self._get_model(model_name, params)
        
        # 交叉验证
        cv_scores = cross_val_score(
            model, X_train, y_train, cv=5, scoring='r2'
        )
        
        # 训练完整模型
        model.fit(X_train, y_train)
        
        scores = {
            "cv_mean_r2": cv_scores.mean(),
            "cv_std_r2": cv_scores.std()
        }
        
        logger.info(f"{model_name} CV R²: {scores['cv_mean_r2']:.4f} (±{scores['cv_std_r2']:.4f})")
        
        return model, scores
    
    # ==================== 多模型对比与自动选择 ====================
    
    def train_multiple_models(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        model_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        训练多个模型并对比，自动选择最优模型
        
        Args:
            X_train: 训练特征
            y_train: 训练目标
            X_test: 测试特征
            y_test: 测试目标
            model_names: 要训练的模型列表
        
        Returns:
            训练结果
        """
        if model_names is None:
            model_names = ["linear", "random_forest", "gbm"]
        
        results = {
            "models": {},
            "test_scores": {},
            "best_model": None,
            "best_score": -np.inf
        }
        
        for model_name in model_names:
            try:
                # 训练模型
                model, cv_scores = self.train_single_model(X_train, y_train, model_name)
                
                # 测试集评估
                y_pred = model.predict(X_test)
                test_r2 = r2_score(y_test, y_pred)
                test_mae = mean_absolute_error(y_test, y_pred)
                test_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                
                # 保存模型和结果
                self.models[model_name] = model
                results["models"][model_name] = model
                results["test_scores"][model_name] = {
                    "r2": test_r2,
                    "mae": test_mae,
                    "rmse": test_rmse,
                    **cv_scores
                }
                
                self.model_scores[model_name] = results["test_scores"][model_name]
                
                # 特征重要性（如果模型支持）
                if hasattr(model, 'feature_importances_'):
                    importances = dict(zip(X_train.columns, model.feature_importances_))
                    self.feature_importances[model_name] = importances
                
                # 更新最佳模型
                if test_r2 > results["best_score"]:
                    results["best_score"] = test_r2
                    results["best_model"] = model_name
                    self.best_model = model
                    self.best_model_name = model_name
                
                logger.info(f"{model_name} Test R²: {test_r2:.4f}")
                
            except Exception as e:
                logger.error(f"Error training {model_name}: {str(e)}")
        
        self.training_history.append(results)
        
        logger.info(f"Best model: {results['best_model']} with R²: {results['best_score']:.4f}")
        return results
    
    # ==================== 超参数调优 ====================
    
    def hyperparameter_tuning(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        model_name: str,
        param_grid: Dict[str, List],
        cv: int = 5
    ) -> Tuple[Any, Dict]:
        """
        超参数调优（Grid Search）
        
        Args:
            X_train: 训练特征
            y_train: 训练目标
            model_name: 模型名称
            param_grid: 参数网格
            cv: 交叉验证折数
        
        Returns:
            (最优模型, 调优结果)
        """
        logger.info(f"Hyperparameter tuning for {model_name}")
        
        base_model = self._get_model(model_name)
        
        grid_search = GridSearchCV(
            base_model,
            param_grid,
            cv=cv,
            scoring='r2',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        
        logger.info(f"Best parameters: {grid_search.best_params_}")
        logger.info(f"Best CV score: {grid_search.best_score_:.4f}")
        
        return grid_search.best_estimator_, {
            "best_params": grid_search.best_params_,
            "best_score": grid_search.best_score_,
            "cv_results": grid_search.cv_results_
        }
    
    # ==================== 模型增量更新（任务5） ====================
    
    def update_model(
        self,
        model: Any,
        X_new: pd.DataFrame,
        y_new: pd.Series,
        method: str = "retrain"
    ) -> Any:
        """
        模型增量更新
        
        Args:
            model: 已有的模型
            X_new: 新数据特征
            y_new: 新数据目标
            method: 更新方法 ('retrain' 完全重训练, 'partial' 增量学习)
        
        Returns:
            更新后的模型
        """
        logger.info(f"Updating model with {len(X_new)} new samples")
        
        if method == "retrain":
            # 方法1: 完全重训练（需要保存历史数据）
            # 这里简化实现，只做演示
            if hasattr(model, 'fit'):
                model.fit(X_new, y_new)
        
        elif method == "partial":
            # 方法2: 增量学习（不是所有模型都支持）
            if hasattr(model, 'partial_fit'):
                model.partial_fit(X_new, y_new)
            else:
                logger.warning("Model does not support partial_fit, using retrain instead")
                model.fit(X_new, y_new)
        
        return model
    
    # ==================== 模型评估 ====================
    
    def evaluate_model(
        self,
        model: Any,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> Dict[str, float]:
        """
        评估模型性能
        
        Returns:
            评估指标字典
        """
        y_pred = model.predict(X_test)
        
        metrics = {
            "r2": r2_score(y_test, y_pred),
            "mae": mean_absolute_error(y_test, y_pred),
            "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
            "mape": np.mean(np.abs((y_test - y_pred) / y_test)) * 100
        }
        
        return metrics
    
    # ==================== 模型持久化 ====================
    
    def save_model(self, model: Any, file_path: str):
        """保存模型"""
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, file_path)
        logger.info(f"Model saved to: {file_path}")
    
    def load_model(self, file_path: str) -> Any:
        """加载模型"""
        model = joblib.load(file_path)
        logger.info(f"Model loaded from: {file_path}")
        return model
    
    def save_best_model(self, file_path: str):
        """保存最佳模型"""
        if self.best_model is not None:
            self.save_model(self.best_model, file_path)
            # 同时保存一些元信息
            meta_path = Path(file_path).parent / f"{Path(file_path).stem}_meta.json"
            import json
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "best_model_name": self.best_model_name,
                    "scores": self.model_scores.get(self.best_model_name, {})
                }, f, ensure_ascii=False, indent=2)
        else:
            logger.warning("No best model to save")
    
    # ==================== 完整训练流程 ====================
    
    def train_full_pipeline(
        self,
        df: pd.DataFrame,
        target_col: str,
        model_names: Optional[List[str]] = None,
        do_tuning: bool = False
    ) -> Dict[str, Any]:
        """
        完整的训练流程
        
        Args:
            df: 处理好的数据
            target_col: 目标列
            model_names: 要训练的模型列表
            do_tuning: 是否进行超参数调优
        
        Returns:
            训练结果
        """
        # 1. 数据准备
        X_train, X_test, y_train, y_test = self.prepare_data(df, target_col)
        
        # 2. 训练多个模型
        results = self.train_multiple_models(
            X_train, y_train, X_test, y_test, model_names
        )
        
        # 3. (可选) 对最佳模型进行超参数调优
        if do_tuning and self.best_model_name == "random_forest":
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [5, 10, None],
                'min_samples_split': [2, 5, 10]
            }
            tuned_model, tuning_results = self.hyperparameter_tuning(
                X_train, y_train, "random_forest", param_grid
            )
            
            # 评估调优后的模型
            tuned_metrics = self.evaluate_model(tuned_model, X_test, y_test)
            
            if tuned_metrics['r2'] > results['best_score']:
                self.best_model = tuned_model
                results['best_model'] = 'random_forest_tuned'
                results['best_score'] = tuned_metrics['r2']
                self.models['random_forest_tuned'] = tuned_model
        
        return results
