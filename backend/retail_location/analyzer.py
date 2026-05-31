"""
零售门店选址分析器 - 整合所有模块
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import logging
from pathlib import Path
import json

from backend.retail_location.config import RetailLocationConfig
from backend.retail_location.data_adapter import RetailDataAdapter
from backend.retail_location.feature_engineer import FeatureEngineer
from backend.retail_location.model_trainer import RetailModelTrainer
from backend.retail_location.visualizer import RetailVisualizer
from backend.data_processing.cleaner import DataCleaner
from backend.report_generator import ReportGenerator
from backend.model_versioning import ModelVersionManager, FeedbackLoop

logger = logging.getLogger(__name__)


class RetailLocationAnalyzer:
    """零售门店选址分析器"""
    
    def __init__(self, config: Optional[RetailLocationConfig] = None):
        self.config = config or RetailLocationConfig.get_default_config()
        self.data_adapter = RetailDataAdapter(self.config)
        self.data_cleaner = DataCleaner()
        self.feature_engineer = FeatureEngineer(self.config)
        self.model_trainer = RetailModelTrainer(self.config)
        
        # 新增模块
        self.visualizer = None
        self.report_generator = None
        self.version_manager = None
        self.feedback_loop = None
        
        # 存储中间结果
        self.raw_data = None
        self.cleaned_data = None
        self.processed_data = None
        self.analysis_result = None
        self.X_test = None
        self.y_test = None
        self.y_pred = None
    
    # ==================== 完整分析流程 ====================
    
    def run_full_analysis(
        self,
        data: pd.DataFrame,
        save_results: bool = True,
        output_dir: str = "data/retail_analysis",
        do_hyperparameter_tuning: bool = False,
        save_model_version: bool = False
    ) -> Dict[str, Any]:
        """
        运行完整的分析流程
        
        Args:
            data: 输入数据
            save_results: 是否保存结果
            output_dir: 输出目录
            do_hyperparameter_tuning: 是否进行超参数调优
            save_model_version: 是否保存模型版本
            
        Returns:
            分析结果
        """
        logger.info("=" * 60)
        logger.info("Starting Retail Location Analysis")
        logger.info("=" * 60)
        
        self.raw_data = data.copy()
        self.visualizer = RetailVisualizer(output_dir)
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
        training_result = self._train_models(self.processed_data, do_hyperparameter_tuning)
        
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
            
            # 保存模型版本（如果需要）
            if save_model_version and self.model_trainer.best_model:
                logger.info("\n[8/8] Saving model version...")
                self._save_model_version(
                    output_dir,
                    insights,
                    data_quality_report
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
    
    # ==================== 数据清洗 ====================
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df_clean = df.copy()
        missing_report = self.data_cleaner.detect_missing(df_clean)
        logger.info(f"Missing values: {missing_report['total_missing']} cells")
        df_clean = self.data_cleaner.fill_missing(df_clean, method='median')
        return df_clean
    
    # ==================== 特征工程 ====================
    
    def _process_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        df_processed = df.copy()
        df_processed, meta = self.feature_engineer.process_features(
            df_processed,
            target_col=self.config.target_column,
            generate_derived=True,
            encode_categorical=True,
            standardize=False
        )
        
        drop_cols = ['store_id', 'store_name', 'address', 'latitude', 'longitude']
        drop_cols = [col for col in drop_cols if col in df_processed.columns]
        df_processed = df_processed.drop(columns=drop_cols, errors='ignore')
        df_processed = df_processed.fillna(0)
        
        return df_processed, meta
    
    # ==================== 模型训练 ====================
    
    def _train_models(
        self,
        df: pd.DataFrame,
        do_tuning: bool = False
    ) -> Dict[str, Any]:
        target_col = self.config.target_column
        X_train, X_test, y_train, y_test = self.model_trainer.prepare_data(
            df, target_col
        )
        
        self.X_test = X_test
        self.y_test = y_test
        
        results = self.model_trainer.train_full_pipeline(
            df, target_col, do_tuning=do_tuning
        )
        
        return results
    
    # ==================== 数据质量检查 ====================
    
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
    
    # ==================== 洞察生成 ====================
    
    def _generate_insights(self, training_result: Dict[str, Any]) -> Dict[str, Any]:
        insights = {}
        
        best_score = training_result.get('best_score', 0)
        best_model_name = training_result.get('best_model', 'unknown')
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
        
        if self.model_trainer.best_model_name and self.model_trainer.best_model_name in self.model_trainer.feature_importances:
            importances = self.model_trainer.feature_importances[self.model_trainer.best_model_name]
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
                if "population" in feature.lower():
                    recommendations.append(
                        f"人口相关特征（{feature}）是重要影响因素，优先选择人口密集区域"
                    )
                elif "competitor" in feature.lower():
                    recommendations.append(
                        f"竞争因素（{feature}）需要重点评估，避免过度竞争区域"
                    )
                elif "distance" in feature.lower() or "subway" in feature.lower():
                    recommendations.append(
                        f"交通便利性（{feature}）显著影响业绩，靠近地铁/公交站更佳"
                    )
                elif "rent" in feature.lower():
                    recommendations.append(
                        f"租金成本（{feature}）需要与预期收益平衡评估"
                    )
                elif "area" in feature.lower():
                    recommendations.append(
                        f"门店面积（{feature}）与业绩相关，选择合适面积的铺位"
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
    
    # ==================== 可视化生成 ====================
    
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
            sales_data = self.raw_data[self.config.target_column].dropna()
            if len(sales_data) > 0:
                plot_path = self.visualizer.plot_sales_distribution(sales_data)
                if plot_path:
                    visualizations["sales_distribution"] = str(plot_path)
        
        if self.processed_data is not None:
            plot_path = self.visualizer.plot_correlation_heatmap(self.processed_data)
            if plot_path:
                visualizations["correlation_heatmap"] = str(plot_path)
        
        logger.info(f"生成了 {len(visualizations)} 个可视化图表")
        return visualizations
    
    # ==================== 保存结果 ====================
    
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
        
        if self.model_trainer.best_model:
            self.model_trainer.save_best_model(str(output_path / "best_model.pkl"))
        
        if self.report_generator:
            self.report_generator.generate_all_reports(
                data_quality_report,
                insights,
                self.processed_data,
                visualizations
            )
        
        logger.info(f"结果已保存到: {output_path}")
    
    # ==================== 模型版本管理 ====================
    
    def _save_model_version(
        self,
        output_dir: str,
        insights: Dict,
        data_quality_report: Dict
    ):
        if self.version_manager is None:
            self.version_manager = ModelVersionManager(str(Path(output_dir) / "versions"))
        
        version_info = {
            "model_type": insights.get('best_model', {}).get('name', 'unknown'),
            "r2_score": insights.get('best_model', {}).get('r2_score', 0),
            "data_quality_score": data_quality_report.get('overall_quality', {}).get('quality_score', 0)
        }
        
        metadata = {
            "feature_names": self.model_trainer.feature_names,
            "target_col": self.config.target_column,
            "insights": insights
        }
        
        version_id = self.version_manager.save_version(
            self.model_trainer.best_model,
            version_info,
            metadata=metadata
        )
        
        logger.info(f"模型版本 {version_id} 已保存")
        return version_id
    
    # ==================== 分析器持久化 ====================
    
    def save_analyzer(self, output_dir: str):
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if self.model_trainer.best_model:
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
        
        logger.info(f"分析器已保存到: {output_path}")
    
    @classmethod
    def load_analyzer(cls, input_dir: str) -> 'RetailLocationAnalyzer':
        input_path = Path(input_dir)
        
        with open(input_path / "analyzer_meta.json", 'r', encoding='utf-8') as f:
            meta = json.load(f)
        
        config = RetailLocationConfig(
            target_column=meta.get("target_col", "monthly_sales")
        )
        
        analyzer = cls(config)
        
        model_path = input_path / "best_model.pkl"
        if model_path.exists():
            analyzer.model_trainer.load_model(str(model_path))
        
        analyzer.model_trainer.feature_names = meta.get("feature_names", [])
        
        logger.info(f"分析器已从 {input_path} 加载")
        return analyzer
    
    # ==================== 新店预测 ====================
    
    def predict_new_location(self, new_data: pd.DataFrame) -> pd.DataFrame:
        if not self.model_trainer.is_trained or self.model_trainer.best_model is None:
            raise ValueError("没有训练好的模型，请先运行分析。")
        
        id_cols = ['store_id', 'store_name', 'address', 'latitude', 'longitude']
        orig_data = new_data[[col for col in id_cols if col in new_data.columns]].copy()
        
        cleaned_data = self._clean_data(new_data)
        processed, _ = self._process_features(cleaned_data)
        
        target_col = self.config.target_column
        if target_col in processed.columns:
            processed = processed.drop(columns=[target_col])
        
        predictions = self.model_trainer.predict(processed)
        
        result = orig_data.copy()
        result['predicted_sales'] = predictions
        
        key_features = ['store_area', 'population_1km', 'competitor_count_1km', 'rent_per_sqm']
        for col in key_features:
            if col in new_data.columns:
                result[col] = new_data[col]
        
        return result
