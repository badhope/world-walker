import warnings
warnings.filterwarnings('ignore')

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import pandas as pd
import numpy as np

from backend.data_processing.cleaner import DataCleaner
from backend.retail_location.feature_engineer import FeatureEngineer
from backend.retail_location.config import RetailLocationConfig
from backend.retail_location.model_trainer import RetailModelTrainer
from backend.retail_location.data_adapter import RetailDataAdapter
from backend.ml.models import (
    BaseModel,
    LinearRegressionModel,
    RandomForestModel,
    GBDTModel,
    RidgeModel,
    ModelMetrics,
    get_model,
    get_available_models,
)
from backend.ml.trainer import ModelTrainer, TrainingConfig, AutoML


def _make_sample_df(n=80, seed=42):
    np.random.seed(seed)
    x1 = np.random.randn(n)
    x2 = np.random.randn(n)
    x3 = np.random.randn(n)
    y = 3 * x1 + 2 * x2 - x3 + np.random.randn(n) * 0.5
    return pd.DataFrame({"x1": x1, "x2": x2, "x3": x3, "target": y})


def _make_dirty_df(n=100, seed=42):
    np.random.seed(seed)
    df = pd.DataFrame({
        "a": np.random.randn(n),
        "b": np.random.randn(n),
        "c": np.random.choice(["X", "Y", "Z"], n),
    })
    df.loc[np.random.choice(n, 10), "a"] = np.nan
    df.loc[np.random.choice(n, 5), "b"] = np.nan
    return df


class TestDataCleaner:

    def setup_method(self):
        self.cleaner = DataCleaner()

    def test_detect_missing(self):
        df = _make_dirty_df()
        result = self.cleaner.detect_missing(df)
        assert result["total_missing"] > 0
        assert "columns" in result
        assert "a" in result["columns"]

    def test_fill_missing_median(self):
        df = _make_dirty_df()
        result = self.cleaner.fill_missing(df, method="median")
        assert result["a"].isna().sum() == 0
        assert result["b"].isna().sum() == 0

    def test_fill_missing_mean(self):
        df = _make_dirty_df()
        result = self.cleaner.fill_missing(df, method="mean")
        assert result["a"].isna().sum() == 0

    def test_fill_missing_zero(self):
        df = _make_dirty_df()
        result = self.cleaner.fill_missing(df, method="zero")
        assert result["a"].isna().sum() == 0

    def test_fill_missing_forward(self):
        df = _make_dirty_df()
        result = self.cleaner.fill_missing(df, method="linear")
        assert result["a"].isna().sum() == 0

    def test_detect_outliers_iqr(self):
        np.random.seed(42)
        df = pd.DataFrame({"val": np.append(np.random.randn(90), [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])})
        result = self.cleaner.detect_outliers_iqr(df)
        assert result["method"] == "iqr"
        assert "val" in result["columns"]
        assert result["columns"]["val"]["outlier_count"] > 0

    def test_detect_outliers_zscore(self):
        np.random.seed(42)
        df = pd.DataFrame({"val": np.append(np.random.randn(90), [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])})
        result = self.cleaner.detect_outliers_zscore(df)
        assert result["method"] == "zscore"
        assert "val" in result["columns"]

    def test_remove_outliers(self):
        np.random.seed(42)
        df = pd.DataFrame({"val": np.append(np.random.randn(90), [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])})
        result = self.cleaner.remove_outliers(df, method="iqr")
        assert len(result) < len(df)

    def test_cap_outliers(self):
        np.random.seed(42)
        df = pd.DataFrame({"val": np.append(np.random.randn(90), [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])})
        result = self.cleaner.cap_outliers(df, method="iqr")
        assert len(result) == len(df)

    def test_normalize_minmax(self):
        df = pd.DataFrame({"a": [1, 2, 3, 4, 5], "b": [10, 20, 30, 40, 50]})
        result, params = self.cleaner.normalize_minmax(df)
        assert result["a"].min() >= 0
        assert result["a"].max() <= 1

    def test_standardize_zscore(self):
        df = pd.DataFrame({"a": [1, 2, 3, 4, 5], "b": [10, 20, 30, 40, 50]})
        result, params = self.cleaner.standardize_zscore(df)
        assert abs(result["a"].mean()) < 1e-10

    def test_generate_quality_report(self):
        df = _make_dirty_df()
        report = self.cleaner.generate_quality_report(df)
        assert "shape" in report
        assert "missing" in report
        assert "outliers_zscore" in report


class TestFeatureEngineer:

    def setup_method(self):
        self.config = RetailLocationConfig()
        self.engineer = FeatureEngineer(self.config)

    def test_generate_derived_features(self):
        data = RetailDataAdapter.generate_sample_data(num_stores=30, random_seed=42)
        result = self.engineer.generate_derived_features(data)
        assert "log_population_1km" in result.columns

    def test_encode_categorical_features(self):
        data = RetailDataAdapter.generate_sample_data(num_stores=30, random_seed=42)
        result, encoders = self.engineer.encode_categorical_features(data)
        assert len(encoders) > 0

    def test_process_features(self):
        data = RetailDataAdapter.generate_sample_data(num_stores=30, random_seed=42)
        cleaned = DataCleaner().fill_missing(data, method="median")
        result, meta = self.engineer.process_features(
            cleaned,
            target_col="monthly_sales",
            generate_derived=True,
            encode_categorical=True,
            standardize=False
        )
        assert "monthly_sales" in result.columns
        assert len(result.columns) > 0

    def test_feature_names_populated(self):
        data = RetailDataAdapter.generate_sample_data(num_stores=30, random_seed=42)
        cleaned = DataCleaner().fill_missing(data, method="median")
        self.engineer.process_features(
            cleaned,
            target_col="monthly_sales",
            generate_derived=True,
            encode_categorical=True,
            standardize=False
        )
        assert len(self.engineer.feature_names) > 0


class TestModelTrainer:

    def setup_method(self):
        self.trainer = RetailModelTrainer()

    def test_train_single_model(self):
        df = _make_sample_df(n=60)
        X_train, X_test, y_train, y_test = self.trainer.prepare_data(df, "target")
        model, scores = self.trainer.train_single_model(X_train, y_train, "linear")
        assert model is not None
        assert "cv_mean_r2" in scores

    def test_train_multiple_models(self):
        df = _make_sample_df(n=60)
        X_train, X_test, y_train, y_test = self.trainer.prepare_data(df, "target")
        results = self.trainer.train_multiple_models(
            X_train, y_train, X_test, y_test,
            model_names=["linear", "ridge"]
        )
        assert "best_model" in results
        assert results["best_score"] > -10

    def test_full_pipeline(self):
        df = _make_sample_df(n=60)
        results = self.trainer.train_full_pipeline(df, "target")
        assert "best_model" in results
        assert self.trainer.is_trained

    def test_predict(self):
        df = _make_sample_df(n=60)
        self.trainer.train_full_pipeline(df, "target")
        X_new = df.drop(columns=["target"]).head(3)
        preds = self.trainer.predict(X_new)
        assert len(preds) == 3

    def test_evaluate_model(self):
        df = _make_sample_df(n=60)
        X_train, X_test, y_train, y_test = self.trainer.prepare_data(df, "target")
        model, _ = self.trainer.train_single_model(X_train, y_train, "linear")
        metrics = self.trainer.evaluate_model(model, X_test, y_test)
        assert "r2" in metrics
        assert "mae" in metrics
        assert "rmse" in metrics

    def test_validate_data(self):
        df = _make_sample_df(n=60)
        is_valid, issues = self.trainer.validate_data(df, "target")
        assert is_valid

    def test_validate_data_missing_target(self):
        df = pd.DataFrame({"x1": [1, 2, 3], "target": ["a", "b", "c"]})
        is_valid, issues = self.trainer.validate_data(df, "target")
        assert not is_valid

    def test_save_and_load_model(self, tmp_path):
        df = _make_sample_df(n=60)
        self.trainer.train_full_pipeline(df, "target")
        model_path = str(tmp_path / "model.pkl")
        self.trainer.save_best_model(model_path)
        new_trainer = RetailModelTrainer()
        loaded_model, metadata = new_trainer.load_model(model_path)
        assert loaded_model is not None


class TestHyperparameterTuning:

    def test_hyperparameter_tuning(self):
        df = _make_sample_df(n=80)
        trainer = RetailModelTrainer()
        X_train, X_test, y_train, y_test = trainer.prepare_data(df, "target")
        param_grid = {"n_estimators": [10, 20], "max_depth": [3, 5]}
        tuned_model, tuning_results = trainer.hyperparameter_tuning(
            X_train, y_train, "random_forest", param_grid, cv=2
        )
        assert tuned_model is not None
        assert "best_params" in tuning_results
        assert "best_score" in tuning_results

    def test_full_pipeline_with_tuning(self):
        df = _make_sample_df(n=80)
        trainer = RetailModelTrainer()
        results = trainer.train_full_pipeline(df, "target", do_tuning=True)
        assert "best_model" in results


class TestModelEvaluationMetrics:

    def test_model_metrics_dataclass(self):
        metrics = ModelMetrics(mae=1.0, rmse=2.0, mape=0.1, r2=0.9)
        assert metrics.mae == 1.0
        assert metrics.rmse == 2.0
        assert metrics.mape == 0.1
        assert metrics.r2 == 0.9

    def test_model_metrics_to_dict(self):
        metrics = ModelMetrics(mae=1.0, rmse=2.0, mape=0.1, r2=0.9)
        d = metrics.to_dict()
        assert "mae" in d
        assert "rmse" in d
        assert "r2" in d

    def test_model_metrics_str(self):
        metrics = ModelMetrics(mae=1.0, rmse=2.0, mape=0.1, r2=0.9)
        s = str(metrics)
        assert "MAE" in s
        assert "R2" in s

    def test_linear_regression_evaluate(self):
        df = _make_sample_df(n=80)
        model = LinearRegressionModel()
        X = df.drop(columns=["target"])
        y = df["target"]
        model.fit(X, y)
        metrics = model.evaluate(X, y)
        assert metrics.r2 > 0

    def test_random_forest_evaluate(self):
        df = _make_sample_df(n=80)
        model = RandomForestModel()
        X = df.drop(columns=["target"])
        y = df["target"]
        model.fit(X, y)
        metrics = model.evaluate(X, y)
        assert metrics.r2 > 0

    def test_get_available_models(self):
        models = get_available_models()
        assert isinstance(models, list)
        assert "linear_regression" in models
        assert "random_forest" in models

    def test_get_model(self):
        model = get_model("linear_regression")
        assert isinstance(model, BaseModel)

    def test_get_model_invalid(self):
        with pytest.raises(ValueError):
            get_model("nonexistent_model")
