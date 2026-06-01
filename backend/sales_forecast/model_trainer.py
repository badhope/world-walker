"""
销售预测模型训练器
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from sklearn.model_selection import train_test_split, cross_validate, GridSearchCV
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import joblib
import logging
from pathlib import Path
import json

from backend.utils.model_security import save_with_signature, load_with_signature

logger = logging.getLogger(__name__)


class SalesModelTrainer:
    """销售预测模型训练器"""
    
    def __init__(self, config: Optional[Any] = None):
        self.config = config
        self.models = {}
        self.best_model = None
        self.best_model_name = None
        self.model_scores = {}
        self.feature_importances = {}
        self.feature_names = []
        self.target_col = None
        self.training_history = []
        self.is_trained = False
    
    def _get_model(self, model_name: str, params: Optional[Dict] = None) -> Any:
        if params is None:
            params = {}
        
        model_map = {
            "linear": LinearRegression,
            "ridge": Ridge,
            "lasso": Lasso,
            "random_forest": RandomForestRegressor,
            "gbm": GradientBoostingRegressor,
        }
        
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
    
    def validate_data(self, df: pd.DataFrame, target_col: str) -> Tuple[bool, List[str]]:
        issues = []
        if len(df) < 10:
            issues.append(f"数据量太少，至少需要10条数据")
        if len(df) < 30:
            logger.warning(f"数据量较少，建议至少30条数据")
        if target_col not in df.columns:
            issues.append(f"目标列 '{target_col}' 不存在")
        if not pd.api.types.is_numeric_dtype(df[target_col]):
            issues.append(f"目标列 '{target_col}' 不是数值型")
        missing_target = df[target_col].isna().sum()
        if missing_target > 0:
            issues.append(f"目标列有 {missing_target} 个缺失值")
        return len(issues) == 0, issues
    
    def prepare_data(
        self,
        df: pd.DataFrame,
        target_col: str,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        feature_cols = [col for col in df.columns if col != target_col]
        self.feature_names = feature_cols.copy()
        self.target_col = target_col
        
        X = df[feature_cols].copy()
        y = df[target_col].copy()
        
        min_train_size = max(5, int(len(df) * (1 - test_size)))
        if min_train_size < 5:
            test_size = 0.1
            logger.warning("数据量较少，调整测试集比例为10%")
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state)
        
        logger.info(f"Data split: train={len(X_train)}, test={len(X_test)}")
        return X_train, X_test, y_train, y_test
    
    def train_single_model(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        model_name: str,
        params: Optional[Dict] = None
    ) -> Tuple[Any, Dict[str, float]]:
        logger.info(f"Training model: {model_name}")
        
        try:
            model = self._get_model(model_name, params)

            if len(X_train) < 5:
                logger.warning(f"训练数据太少，跳过交叉验证")
                model.fit(X_train, y_train)
                cv_results = {'test_r2': np.array([0.0]), 'test_mae': np.array([0.0]), 'test_rmse': np.array([0.0]), 'test_mape': np.array([0.0])}
            else:
                cv_num = min(5, len(X_train) // 5)
                cv_num = max(2, cv_num)
                cv_results = cross_validate(
                    model, X_train, y_train, cv=cv_num,
                    scoring={
                        'r2': 'r2',
                        'mae': 'neg_mean_absolute_error',
                        'rmse': 'neg_root_mean_squared_error',
                        'mape': 'neg_mean_absolute_percentage_error'
                    }
                )

            model.fit(X_train, y_train)

            scores = {
                "cv_mean_r2": float(np.mean(cv_results['test_r2'])),
                "cv_std_r2": float(np.std(cv_results['test_r2'])),
                "cv_mean_mae": float(np.mean(-cv_results.get('test_mae', [0]))),
                "cv_mean_rmse": float(np.mean(-cv_results.get('test_rmse', [0]))),
                "cv_score": float(np.mean(cv_results['test_r2'])),
            }

            logger.info(f"{model_name} CV R²: {scores['cv_mean_r2']:.4f} (±{scores['cv_std_r2']:.4f})")
            return model, scores
            
        except Exception as e:
            logger.error(f"Error training {model_name}: {str(e)}")
            raise RuntimeError(f"Model training failed for {model_name}: {e}") from e
    
    def train_multiple_models(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        model_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
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
                model, cv_scores = self.train_single_model(X_train, y_train, model_name)
                y_pred = model.predict(X_test)
                test_r2 = r2_score(y_test, y_pred)
                test_mae = mean_absolute_error(y_test, y_pred)
                test_rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
                
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
                
                if hasattr(model, 'feature_importances_'):
                    importances = dict(zip(X_train.columns, model.feature_importances_))
                    self.feature_importances[model_name] = importances
                
                logger.info(f"{model_name} Test R²: {test_r2:.4f}")
                
            except Exception as e:
                logger.error(f"Error training {model_name}: {str(e)}")
                continue
        
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
    
    def save_model(self, model: Any, file_path: str, metadata: Optional[Dict] = None):
        file_path_obj = Path(file_path)
        file_path_obj.parent.mkdir(parents=True, exist_ok=True)
        save_with_signature(model, file_path)
        
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
        model = load_with_signature(file_path)
        self.best_model = model
        
        file_path_obj = Path(file_path)
        meta_path = file_path_obj.parent / f"{file_path_obj.stem}_metadata.json"
        
        metadata = {}
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            self.feature_names = metadata.get("feature_names", [])
            self.target_col = metadata.get("target_col")
            self.best_model_name = metadata.get("best_model_name")
            self.model_scores = metadata.get("model_scores", {})
            self.feature_importances = metadata.get("feature_importances", {})
            self.is_trained = True
        
        logger.info(f"Model loaded from: {file_path}")
        return model, metadata
    
    def save_best_model(self, file_path: str):
        if self.best_model is not None:
            self.save_model(self.best_model, file_path)
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained or self.best_model is None:
            raise ValueError("No trained model available!")
        
        X = X.copy()
        for col in self.feature_names:
            if col not in X.columns:
                logger.warning(f"Missing feature {col}, filling with 0")
                X[col] = 0
        
        X = X[self.feature_names]
        return self.best_model.predict(X)
    
    def train_full_pipeline(
        self,
        df: pd.DataFrame,
        target_col: str,
        model_names: Optional[List[str]] = None,
        do_tuning: bool = False
    ) -> Dict[str, Any]:
        is_valid, issues = self.validate_data(df, target_col)
        if not is_valid:
            raise ValueError(f"Data validation failed: {issues}")
        
        X_train, X_test, y_train, y_test = self.prepare_data(df, target_col)
        results = self.train_multiple_models(X_train, y_train, X_test, y_test, model_names)
        return results
