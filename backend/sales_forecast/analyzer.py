"""
销售预测分析器
"""
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
from backend.data_processing.cleaner import DataCleaner

logger = logging.getLogger(__name__)


class SalesForecastAnalyzer:
    """销售预测分析器"""
    
    def __init__(self, config: Optional[SalesForecastConfig] = None):
        self.config = config or SalesForecastConfig.get_default_config()
        self.data_adapter = SalesDataAdapter(self.config)
        self.data_cleaner = DataCleaner()
        self.feature_engineer = SalesFeatureEngineer(self.config)
        self.model_trainer = SalesModelTrainer(self.config)
        
        self.raw_data = None
        self.cleaned_data = None
        self.processed_data = None
        self.analysis_result = None
    
    def run_full_analysis(
        self,
        data: pd.DataFrame,
        save_results: bool = True,
        output_dir: str = "data/sales_forecast"
    ) -> Dict[str, Any]:
        """完整分析流程"""
        logger.info("=" * 60)
        logger.info("Starting Sales Forecast Analysis")
        logger.info("=" * 60)
        
        self.raw_data = data.copy()
        
        # 1. 数据验证
        logger.info("\n[1/6] Validating data...")
        is_valid, missing_cols = self.config.validate_data_columns(data.columns)
        if not is_valid:
            logger.warning(f"Missing required columns: {missing_cols}")
        
        # 2. 数据清洗
        logger.info("\n[2/6] Cleaning data...")
        self.cleaned_data = self._clean_data(data)
        
        # 3. 特征工程
        logger.info("\n[3/6] Engineering features...")
        self.processed_data, feature_meta = self._process_features(self.cleaned_data)
        
        # 4. 模型训练
        logger.info("\n[4/6] Training models...")
        training_result = self._train_models(self.processed_data)
        
        # 5. 生成洞察
        logger.info("\n[5/6] Generating insights...")
        insights = self._generate_insights(training_result)
        
        # 6. 保存结果
        if save_results:
            logger.info("\n[6/6] Saving results...")
            self._save_results(output_dir, training_result, insights)
        
        self.analysis_result = {
            "data": {
                "raw_shape": data.shape,
                "cleaned_shape": self.cleaned_data.shape,
                "processed_shape": self.processed_data.shape
            },
            "training_result": training_result,
            "insights": insights,
            "feature_meta": feature_meta
        }
        
        logger.info("\n" + "=" * 60)
        logger.info("Analysis complete!")
        logger.info("=" * 60)
        
        return self.analysis_result
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据清洗"""
        df_clean = df.copy()
        
        missing_report = self.data_cleaner.detect_missing(df_clean)
        logger.info(f"Missing values: {missing_report['total_missing']} cells")
        
        df_clean = self.data_cleaner.fill_missing(df_clean, method='median')
        
        return df_clean
    
    def _process_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """特征处理"""
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
        """训练模型"""
        results = self.model_trainer.train_full_pipeline(
            df,
            target_col=self.config.target_column,
            model_names=["linear", "random_forest", "gbm"],
            do_tuning=False
        )
        return results
    
    def _generate_insights(self, training_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成洞察"""
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
        """生成建议"""
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
    
    def _save_results(
        self,
        output_dir: str,
        training_result: Dict,
        insights: Dict
    ):
        """保存结果"""
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
        
        report_path = output_path / "analysis_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(insights, f, ensure_ascii=False, indent=2, default=str)
        
        human_readable_path = output_path / "analysis_summary.txt"
        self._generate_human_readable_report(insights, human_readable_path)
        
        logger.info(f"Results saved to: {output_path}")
    
    def _generate_human_readable_report(self, insights: Dict, file_path: Path):
        """生成人类可读报告"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("Sales Forecast Analysis Report\n")
            f.write("=" * 60 + "\n\n")
            
            best_model = insights.get('best_model', {})
            f.write(f"【Best Model】\n")
            f.write(f"Model: {best_model.get('name')}\n")
            f.write(f"R² Score: {best_model.get('r2_score'):.4f}\n\n")
            
            if 'feature_importance' in insights:
                f.write("【Top Features】\n")
                for i, (feature, importance) in enumerate(
                    insights['feature_importance']['top_features'][:8], 1
                ):
                    f.write(f"{i}. {feature}: {importance:.4f}\n")
                f.write("\n")
            
            f.write("【Recommendations】\n")
            for i, rec in enumerate(insights.get('recommendations', []), 1):
                f.write(f"{i}. {rec}\n")
    
    def save_analyzer(self, output_dir: str):
        """保存分析器"""
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
        """加载分析器"""
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
        """预测"""
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
