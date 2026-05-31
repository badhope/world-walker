"""
零售门店模型训练器 - 增强版
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
import json

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
        self.feature_names = []  # 新增：保存特征列表
        self.target_col = None  # 新增：保存目标列
        self.training_history = []
        self.is_trained = False  # 新增：训练状态标记
    
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
    
    # ==================== 数据验证 ====================
    
    def validate_data(self, df: pd.DataFrame, target_col: str) -> Tuple[bool, List[str]]:
        """
        验证数据是否合法
        
        Returns:
            (是否有效, 问题列表)
        """
        issues = []
        
        # 检查数据量
        if len(df) < 10:
            issues.append(f"数据量太少，至少需要10条数据")
        if len(df) < 30:
            logger.warning(f"数据量较少，建议至少30条数据")
        
        # 检查目标列
        if target_col not in df.columns:
            issues.append(f"目标列 '{target_col}' 不存在")
        
        # 检查目标列是否为数值型
        if not pd.api.types.is_numeric_dtype(df[target_col]):
            issues.append(f"目标列 '{target_col}' 不是数值型")
        
        # 检查目标列是否有缺失值
        missing_target = df[target_col].isna().sum()
        if missing_target > 0:
            issues.append(f"目标列有 {missing_target} 个缺失值")
        
        return len(issues) == 0, issues
    
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
        # 保存特征列
        feature_cols = [col for col in df.columns if col != target_col]
        self.feature_names = feature_cols.copy()
        self.target_col = target_col
        
        X = df[feature_cols].copy()
        y = df[target_col].copy()
        
        # 确保数据量足够
        min_train_size = max(5, int(len(df) * (1 - test_size)))
        if min_train_size < 5:
            test_size = 0.1
            logger.warning("数据量较少，调整测试集比例为10%")
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state)
        
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
        训练单个模型 - 增加错误处理
        
        Returns:
            (训练好的模型, 评估指标)
        """
        logger.info(f"Training model: {model_name}")
        
        try:
            model = self._get_model(model_name, params)
            
            # 检查数据量
            if len(X_train) < 5:
                logger.warning(f"训练数据太少，跳过交叉验证")
                model.fit(X_train, y_train)
                cv_scores = [0.0]
            else:
                # 交叉验证
                cv = min(5, len(X_train) // 5)
                cv = max(2, cv)
                cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring='r2')
            
            # 训练完整模型
            model.fit(X_train, y_train)
            
            scores = {
                "cv_mean_r2": float(np.mean(cv_scores)),
                "cv_std_r2": float(np.std(cv_scores))
            }
            
            logger.info(f"{model_name} CV R²: {scores['cv_mean_r2']:.4f} (±{scores['cv_std_r2']:.4f})")
            
            return model, scores
            
        except Exception as e:
            logger.error(f"Error training {model_name}: {str(e)}")
            # 降级策略：尝试简单模型
            if model_name != "linear":
                logger.info(f"Falling back to linear model")
                return self.train_single_model(X_train, y_train, "linear")
            raise
    
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
        
        successful_models = []
        
        for model_name in model_names:
            try:
                # 训练模型
                model, cv_scores = self.train_single_model(X_train, y_train, model_name)
                
                # 测试集评估
                y_pred = model.predict(X_test)
                test_r2 = r2_score(y_test, y_pred)
                test_mae = mean_absolute_error(y_test, y_pred)
                test_rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
                
                # 保存模型和结果
                self.models[model_name] = model
                results["models"][model_name] = model
                results["test_scores"][model_name] = {
                    "r2": float(test_r2),
                    "mae": float(test_mae),
                    "rmse": float(test_rmse),
                    **cv_scores
                }
                
                successful_models.append((test_r2, model_name))
                
                self.model_scores[model_name] = results["test_scores"][model_name]
                
                # 特征重要性（如果模型支持）
                if hasattr(model, 'feature_importances_'):
                    importances = dict(zip(X_train.columns, model.feature_importances_))
                    self.feature_importances[model_name] = importances
                
                logger.info(f"{model_name} Test R²: {test_r2:.4f}")
                
            except Exception as e:
                logger.error(f"Error training {model_name}: {str(e)}")
                continue
        
        # 选择最优模型
        if successful_models:
            successful_models.sort(reverse=True)
            best_score, best_name = successful_models[0]
            results["best_score"] = best_score
            results["best_model"] = best_name
            self.best_model = self.models[best_name]
            self.best_model_name = best_name
            self.is_trained = True
            logger.info(f"Best model: {best_name} with R²: {best_score:.4f}")
        else:
            logger.error("No models trained successfully!")
        
        self.training_history.append(results)
        return results
    
    # ==================== 超参数调优 ====================
    
    def hyperparameter_tuning(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        model_name: str,
        param_grid: Dict,
        cv: int = 5
    ) -> Tuple[Any, Dict]:
        """
        超参数调优（GridSearch）
        """
        logger.info(f"Hyperparameter tuning for {model_name}")
        
        try:
            base_model = self._get_model(model_name)
            
            # 调整CV折数
            cv = min(cv, len(X_train) // 5)
            cv = max(2, cv)
            
            grid_search = GridSearchCV(
                base_model, param_grid, cv=cv, scoring='r2', n_jobs=-1, verbose=1)
            
            grid_search.fit(X_train, y_train)
            
            logger.info(f"Best parameters: {grid_search.best_params_}")
            logger.info(f"Best CV score: {grid_search.best_score_:.4f}")
            
            return grid_search.best_estimator_, {
                "best_params": grid_search.best_params_,
                "best_score": float(grid_search.best_score_),
            }
            
        except Exception as e:
            logger.error(f"Error in hyperparameter tuning: {str(e)}")
            # 返回简单模型
            return self.train_single_model(X_train, y_train, "linear")
    
    # ==================== 模型增量更新 ====================
    
    def update_model(
        self,
        model: Any,
        X_new: pd.DataFrame,
        y_new: pd.Series,
        method: str = "retrain"
    ) -> Any:
        """
        模型增量更新
        """
        logger.info(f"Updating model with {len(X_new)} new samples")
        
        try:
            if method == "retrain":
                if hasattr(model, 'fit'):
                    model.fit(X_new, y_new)
            elif method == "partial":
                if hasattr(model, 'partial_fit'):
                    model.partial_fit(X_new, y_new)
                else:
                    logger.warning("Model does not support partial_fit, using retrain instead")
                    model.fit(X_new, y_new)
            return model
        except Exception as e:
            logger.error(f"Error updating model: {str(e)}")
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
        """
        y_pred = model.predict(X_test)
        
        metrics = {
            "r2": float(r2_score(y_test, y_pred)),
            "mae": float(mean_absolute_error(y_test, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
            "mape": float(np.mean(np.abs((y_test - y_pred) / y_test)) * 100)
        }
        
        return metrics
    
    # ==================== 模型持久化（增强版）====================
    
    def save_model(self, model: Any, file_path: str, metadata: Optional[Dict] = None):
        """保存模型（包含元数据）"""
        file_path_obj = Path(file_path)
        file_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存模型
        joblib.dump(model, file_path)
        
        # 保存元数据
        if metadata is None:
            metadata = {}
        
        metadata.update({
            "feature_names": self.feature_names,
            "target_col": self.target_col,
            "best_model_name": self.best_model_name,
            "model_scores": self.model_scores,
            "feature_importances": self.feature_importances
        })
        
        meta_path = file_path_obj.parent / f"{file_path_obj.stem}_metadata.json"
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Model saved to: {file_path}")
        logger.info(f"Metadata saved to: {meta_path}")
    
    def load_model(self, file_path: str) -> Tuple[Any, Dict]:
        """加载模型（包含元数据）"""
        model = joblib.load(file_path)
        self.best_model = model
        
        # 加载元数据
        file_path_obj = Path(file_path)
        meta_path = file_path_obj.parent / f"{file_path_obj.stem}_metadata.json"
        
        metadata = {}
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # 恢复状态
            self.feature_names = metadata.get("feature_names", [])
            self.target_col = metadata.get("target_col")
            self.best_model_name = metadata.get("best_model_name")
            self.model_scores = metadata.get("model_scores", {})
            self.feature_importances = metadata.get("feature_importances", {})
            self.is_trained = True
        
        logger.info(f"Model loaded from: {file_path}")
        return model, metadata
    
    def save_best_model(self, file_path: str):
        """保存最佳模型"""
        if self.best_model is not None:
            self.save_model(self.best_model, file_path)
        else:
            logger.warning("No best model to save")
    
    # ==================== 预测功能（增强版）====================
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        预测 - 确保特征一致性
        
        Args:
            X: 输入数据
        
        Returns:
            预测结果
        """
        if not self.is_trained or self.best_model is None:
            raise ValueError("No trained model available!")
        
        # 确保特征一致
        X = X.copy()
        for col in self.feature_names:
            if col not in X.columns:
                logger.warning(f"Missing feature {col}, filling with 0")
                X[col] = 0
        
        # 只保留需要的特征并确保顺序一致
        X = X[self.feature_names]
        
        # 预测
        return self.best_model.predict(X)
    
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
        """
        # 1. 数据验证
        is_valid, issues = self.validate_data(df, target_col)
        if not is_valid:
            raise ValueError(f"Data validation failed: {issues}")
        
        # 2. 数据准备
        X_train, X_test, y_train, y_test = self.prepare_data(df, target_col)
        
        # 3. 训练多个模型
        results = self.train_multiple_models(X_train, y_train, X_test, y_test, model_names)
        
        # 4. 超参数调优（真实实现！）
        if do_tuning and self.best_model_name in ["random_forest", "gbm"]:
            logger.info("="*50)
            logger.info("开始超参数调优...")
            logger.info("="*50)
            
            param_grid = {
                "random_forest": {
                    'n_estimators': [50, 100],
                    'max_depth': [5, 10],
                    'min_samples_split': [2, 5]
                },
                "gbm": {
                    'n_estimators': [50, 100],
                    'learning_rate': [0.05, 0.1],
                    'max_depth': [3, 5]
                }
            }
            
            if self.best_model_name in param_grid:
                try:
                    tuned_model, tuning_results = self.hyperparameter_tuning(
                        X_train, y_train, self.best_model_name, param_grid[self.best_model_name]
                    )
                    
                    # 评估调优后的模型
                    tuned_metrics = self.evaluate_model(tuned_model, X_test, y_test)
                    results['tuning_results'] = tuning_results
                    results['tuned_metrics'] = tuned_metrics
                    
                    logger.info(f"调优后的测试集R²: {tuned_metrics['r2']:.4f}")
                    
                    # 比较，更新最佳模型
                    if tuned_metrics['r2'] > results['best_score']:
                        logger.info(f"超参数调优有效！R²从 {results['best_score']:.4f} 提升到 {tuned_metrics['r2']:.4f}")
                        self.best_model = tuned_model
                        results['best_model'] = f"{self.best_model_name}_tuned"
                        results['best_score'] = tuned_metrics['r2']
                        self.models[f"{self.best_model_name}_tuned"] = tuned_model
                        self.model_scores[f"{self.best_model_name}_tuned"] = tuned_metrics
                    else:
                        logger.info(f"超参数调优无明显改善，保持原模型")
                        
                except Exception as e:
                    logger.error(f"超参数调优失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
        
        return results
