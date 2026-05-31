import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import logging
from pathlib import Path
import json

from backend.sales_forecast.config import SalesForecastConfig
from backend.sales_forecast.data_adapter import SalesDataAdapter
from backend.sales_forecast.feature_engineer import SalesFeatureEngineer
from backend.sales_forecast.model_trainer import SalesModelTrainer
from backend.sales_forecast.visualizer import SalesForecastVisualizer
from backend.data_processing.cleaner import DataCleaner
from backend.report_generator import ReportGenerator
from backend.analysis.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class SalesForecastAnalyzer(BaseAnalyzer):

    def __init__(self, config: Optional[SalesForecastConfig] = None):
        super().__init__()
        self.config = config or SalesForecastConfig.get_default_config()
        self.data_adapter = SalesDataAdapter(self.config)
        self.data_cleaner = DataCleaner()
        self.feature_engineer = SalesFeatureEngineer(self.config)
        self.model_trainer = SalesModelTrainer(self.config)

        self.visualizer = None
        self.report_generator = None

        self.raw_data = None
        self.cleaned_data = None
        self.processed_data = None
        self.analysis_result = None
        self.X_test = None
        self.y_test = None
        self.y_pred = None

    def run_full_analysis(
        self,
        data: pd.DataFrame,
        save_results: bool = True,
        output_dir: str = "data/sales_forecast",
        do_hyperparameter_tuning: bool = False,
        save_model_version: bool = False
    ) -> Dict[str, Any]:
        logger.info("=" * 60)
        logger.info("Starting Sales Forecast Analysis")
        logger.info("=" * 60)

        self.raw_data = data.copy()
        self.visualizer = SalesForecastVisualizer(output_dir)
        self.report_generator = ReportGenerator(output_dir)

        # 1. 数据验证
        logger.info("\n[1/8] Validating data...")
        data_quality_report = self._data_quality_check(data)

        # 2. 数据清洗
        logger.info("\n[2/8] Cleaning data...")
        self.cleaned_data = self._clean_data(data)

        # 3. 特征工程
        logger.info("\n[3/8] Engineering features...")
        self.processed_data, feature_meta = self._process_features(self.cleaned_data)

        # 4. 模型训练
        logger.info("\n[4/8] Training models...")
        training_result = self._train_models(self.processed_data)

        # 5. 生成预测结果
        if self.model_trainer.best_model and self.X_test is not None:
            self.y_pred = self.model_trainer.predict(self.X_test)

        # 6. 生成洞察
        logger.info("\n[5/8] Generating insights...")
        insights = self._generate_insights(training_result)

        # 7. 生成可视化
        logger.info("\n[6/8] Generating visualizations...")
        visualizations = self._generate_visualizations()

        # 8. 保存结果
        if save_results:
            logger.info("\n[7/8] Saving results...")
            self._save_results(
                output_dir,
                training_result,
                insights,
                data_quality_report,
                visualizations
            )

        self.analysis_result = {
            "data": {
                "raw_shape": data.shape,
                "cleaned_shape": self.cleaned_data.shape,
                "processed_shape": self.processed_data.shape
            },
            "data_quality": data_quality_report,
            "training_result": training_result,
            "insights": insights,
            "feature_meta": feature_meta,
            "visualizations": visualizations
        }

        logger.info("\n" + "=" * 60)
        logger.info("Analysis complete!")
        logger.info("=" * 60)

        return self.analysis_result

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df_clean = df.copy()

        missing_report = self.data_cleaner.detect_missing(df_clean)
        logger.info(f"Missing values: {missing_report['total_missing']} cells")

        df_clean = self.data_cleaner.fill_missing(df_clean, method='median')

        return df_clean

    def _process_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        target_col = self.config.target_column
        df_processed = df.copy()

        df_processed, meta = self.feature_engineer.process_features(
            df_processed,
            target_col=target_col,
            generate_derived=True,
            encode_categorical=True,
            standardize=False
        )

        drop_cols = ['date', 'product_id']
        drop_cols = [col for col in drop_cols if col in df_processed.columns]
        df_processed = df_processed.drop(columns=drop_cols, errors='ignore')

        df_processed = df_processed.fillna(0)

        return df_processed, meta

    def _train_models(self, df: pd.DataFrame) -> Dict[str, Any]:
        target_col = self.config.target_column
        X_train, X_test, y_train, y_test = self.model_trainer.prepare_data(
            df, target_col
        )

        self.X_test = X_test
        self.y_test = y_test

        results = self.model_trainer.train_full_pipeline(
            df, target_col, do_tuning=False
        )

        return results

    def _data_quality_check(self, df: pd.DataFrame) -> Dict[str, Any]:
        report = {}

        report["basic_info"] = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / (1024 * 1024)
        }

        missing_stats = df.isnull().sum()
        missing_percent = (df.isnull().sum() / len(df)) * 100

        report["missing_values"] = {
            "total_missing_cells": int(missing_stats.sum()),
            "columns_with_missing": [
                {
                    "column": col,
                    "missing_count": int(missing_stats[col]),
                    "missing_percent": float(missing_percent[col])
                }
                for col in df.columns if missing_stats[col] > 0
            ]
        }

        duplicate_count = df.duplicated().sum()
        report["duplicates"] = {
            "total_duplicates": int(duplicate_count),
            "duplicate_percent": float((duplicate_count / len(df)) * 100)
        }

        dtype_summary = {}
        for col in df.columns:
            dtype_name = str(df[col].dtype)
            if dtype_name not in dtype_summary:
                dtype_summary[dtype_name] = []
            dtype_summary[dtype_name].append(col)
        report["data_types"] = dtype_summary

        numeric_cols = df.select_dtypes(include=[np.number]).columns
        outlier_report = {}
        for col in numeric_cols:
            data = df[col].dropna()
            if len(data) == 0:
                continue

            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            outliers = data[(data < lower_bound) | (data > upper_bound)]
            outlier_report[col] = {
                "outlier_count": len(outliers),
                "outlier_percent": float((len(outliers) / len(data)) * 100),
                "min_value": float(data.min()),
                "max_value": float(data.max()),
                "mean_value": float(data.mean()),
                "median_value": float(data.median())
            }
        report["outliers"] = outlier_report

        total_issues = (
            missing_stats.sum() +
            duplicate_count +
            sum(o.get('outlier_count', 0) for o in outlier_report.values())
        )
        max_possible_issues = len(df) * len(df.columns)
        quality_score = max(0, 100 - (total_issues / max_possible_issues) * 100)

        report["overall_quality"] = {
            "quality_score": float(quality_score),
            "rating": "Excellent" if quality_score >= 90 else
                      "Good" if quality_score >= 70 else
                      "Fair" if quality_score >= 50 else "Poor"
        }

        logger.info(f"数据质量评分: {quality_score:.1f}/100")
        return report

    def _generate_insights(self, training_result: Dict[str, Any]) -> Dict[str, Any]:
        insights = {}

        best_model_name = training_result.get('best_model')
        best_score = training_result.get('best_score')
        insights["best_model"] = {
            "name": best_model_name,
            "r2_score": best_score
        }

        model_comparison = []
        for model_name, scores in training_result.get('test_scores', {}).items():
            model_comparison.append({
                "model": model_name,
                "r2": scores.get('r2'),
                "mae": scores.get('mae'),
                "rmse": scores.get('rmse')
            })
        insights["model_comparison"] = model_comparison

        if best_model_name and best_model_name in self.model_trainer.feature_importances:
            importances = self.model_trainer.feature_importances[best_model_name]
            sorted_importance = sorted(importances.items(), key=lambda x: x[1], reverse=True)
            insights["feature_importance"] = {
                "top_features": sorted_importance[:10],
                "all_features": sorted_importance
            }

        insights["recommendations"] = self._generate_recommendations(insights)

        return insights

    def _generate_recommendations(self, insights: Dict) -> List[str]:
        recommendations = []

        if "feature_importance" in insights:
            top_features = insights["feature_importance"]["top_features"]

            for feature, importance in top_features[:5]:
                if 'price' in feature.lower() or 'discount' in feature.lower():
                    recommendations.append(
                        f"价格和折扣因素对销售影响很大（{feature}），建议优化定价策略"
                    )
                elif 'promotion' in feature.lower():
                    recommendations.append(
                        f"促销预算（{feature}）是重要影响因素，建议合理分配促销费用"
                    )
                elif 'inventory' in feature.lower():
                    recommendations.append(
                        f"库存水平（{feature}）与销售量相关，需要优化库存管理"
                    )
                elif 'holiday' in feature.lower() or 'weekend' in feature.lower():
                    recommendations.append(
                        f"节假日和周末（{feature}）对销售有明显影响，应提前准备"
                    )
                elif 'category' in feature.lower():
                    recommendations.append(
                        f"产品分类（{feature}）是重要因素，需要针对不同类别优化策略"
                    )

        r2_score = insights.get("best_model", {}).get("r2_score", 0)
        if r2_score > 0.8:
            recommendations.append(
                "模型预测精度优秀，可以作为决策的重要参考依据"
            )
        elif r2_score > 0.6:
            recommendations.append(
                "模型有一定预测能力，但建议结合业务经验综合判断"
            )
        else:
            recommendations.append(
                "建议收集更多历史数据或优化特征，以提升模型预测能力"
            )

        return recommendations

    def _generate_visualizations(self) -> Dict[str, str]:
        if self.visualizer is None:
            return {}

        visualizations = {}

        if self.model_trainer.best_model_name in self.model_trainer.feature_importances:
            fi = self.model_trainer.feature_importances[self.model_trainer.best_model_name]
            plot_path = self.visualizer.plot_feature_importance(fi)
            if plot_path:
                visualizations["feature_importance"] = str(plot_path)

        if self.model_trainer.model_scores:
            plot_path = self.visualizer.plot_model_comparison(self.model_trainer.model_scores)
            if plot_path:
                visualizations["model_comparison"] = str(plot_path)

        if self.y_test is not None and self.y_pred is not None:
            plot_path = self.visualizer.plot_predicted_vs_actual(self.y_test, self.y_pred)
            if plot_path:
                visualizations["pred_vs_actual"] = str(plot_path)

        if self.raw_data is not None and self.config.target_column in self.raw_data.columns:
            target_data = self.raw_data[self.config.target_column].dropna()
            if len(target_data) > 0:
                try:
                    date_col = 'date'
                    if date_col in self.raw_data.columns:
                        historical_dates = pd.to_datetime(self.raw_data[date_col])
                        historical_values = self.raw_data[self.config.target_column]
                        sorted_idx = historical_dates.argsort()
                        historical_dates = historical_dates.iloc[sorted_idx]
                        historical_values = historical_values.iloc[sorted_idx]

                        if self.y_pred is not None and self.X_test is not None:
                            forecast_dates = pd.date_range(
                                start=historical_dates.iloc[-1],
                                periods=len(self.y_pred) + 1,
                                freq='D'
                            )[1:]
                            plot_path = self.visualizer.plot_sales_forecast(
                                historical_dates, historical_values,
                                forecast_dates, self.y_pred
                            )
                            if plot_path:
                                visualizations["sales_forecast"] = str(plot_path)
                except Exception as e:
                    logger.warning(f"生成销售预测图失败: {e}")

        logger.info(f"生成了 {len(visualizations)} 个可视化图表")
        return visualizations

    def _save_results(
        self,
        output_dir: str,
        training_result: Dict,
        insights: Dict,
        data_quality_report: Dict,
        visualizations: Dict
    ):
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if self.processed_data is not None:
            self.processed_data.to_csv(
                output_path / "processed_data.csv",
                index=False,
                encoding='utf-8-sig'
            )

        if self.model_trainer.best_model is not None:
            model_path = output_path / "best_model.pkl"
            self.model_trainer.save_best_model(str(model_path))

        if self.report_generator:
            self.report_generator.generate_all_reports(
                data_quality_report,
                insights,
                self.processed_data,
                visualizations
            )

        logger.info(f"Results saved to: {output_path}")

    def save_analyzer(self, output_dir: str):
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if self.model_trainer.best_model is not None:
            self.model_trainer.save_best_model(str(output_path / "best_model.pkl"))

        meta = {
            "feature_names": self.model_trainer.feature_names,
            "target_col": self.config.target_column,
            "config": {
                "target_column": self.config.target_column
            }
        }

        with open(output_path / "analyzer_meta.json", 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        logger.info(f"Analyzer saved to: {output_path}")

    @classmethod
    def load_analyzer(cls, input_dir: str) -> 'SalesForecastAnalyzer':
        input_path = Path(input_dir)

        with open(input_path / "analyzer_meta.json", 'r', encoding='utf-8') as f:
            meta = json.load(f)

        config = SalesForecastConfig(
            target_column=meta.get("target_col", "sales")
        )

        analyzer = cls(config)

        model_path = input_path / "best_model.pkl"
        if model_path.exists():
            analyzer.model_trainer.load_model(str(model_path))

        analyzer.model_trainer.feature_names = meta.get("feature_names", [])
        logger.info(f"Analyzer loaded from: {input_path}")
        return analyzer

    def predict(self, new_data: pd.DataFrame) -> pd.DataFrame:
        if not self.model_trainer.is_trained or self.model_trainer.best_model is None:
            raise ValueError("No trained model available. Please run analysis first.")

        id_cols = ['date', 'product_id']
        orig_data = new_data[[col for col in id_cols if col in new_data.columns]].copy()

        cleaned_data = self._clean_data(new_data)
        processed, _ = self._process_features(cleaned_data)

        target_col = self.config.target_column
        if target_col in processed.columns:
            processed = processed.drop(columns=[target_col])

        predictions = self.model_trainer.predict(processed)

        result = orig_data.copy()
        result['predicted_sales'] = predictions

        key_features = ['price', 'discount', 'inventory', 'promotion_budget']
        for col in key_features:
            if col in new_data.columns:
                result[col] = new_data[col]

        return result
