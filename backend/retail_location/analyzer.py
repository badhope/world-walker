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
from backend.data_processing.cleaner import DataCleaner

logger = logging.getLogger(__name__)


class RetailLocationAnalyzer:
    """零售门店选址分析器"""
    
    def __init__(self, config: Optional[RetailLocationConfig] = None):
        self.config = config or RetailLocationConfig.get_default_config()
        self.data_adapter = RetailDataAdapter(self.config)
        self.data_cleaner = DataCleaner()
        self.feature_engineer = FeatureEngineer(self.config)
        self.model_trainer = RetailModelTrainer(self.config)
        
        # 存储中间结果
        self.raw_data = None
        self.cleaned_data = None
        self.processed_data = None
        self.analysis_result = None
    
    # ==================== 完整分析流程 ====================
    
    def run_full_analysis(
        self,
        data: pd.DataFrame,
        save_results: bool = True,
        output_dir: str = "data/retail_analysis"
    ) -> Dict[str, Any]:
        """
        运行完整的分析流程
        
        Args:
            data: 输入数据
            save_results: 是否保存结果
            output_dir: 输出目录
        
        Returns:
            分析结果
        """
        logger.info("=" * 60)
        logger.info("Starting Retail Location Analysis")
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
    
    # ==================== 数据清洗 ====================
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据清洗"""
        df_clean = df.copy()
        
        # 1. 检测缺失值
        missing_report = self.data_cleaner.detect_missing(df_clean)
        logger.info(f"Missing values: {missing_report['total_missing']} cells")
        
        # 2. 填充缺失值
        df_clean = self.data_cleaner.fill_missing(df_clean, method='median')
        
        # 3. 检测异常值
        outliers_report = self.data_cleaner.detect_outliers_iqr(df_clean)
        
        # 4. 处理异常值（盖帽法）
        df_clean = self.data_cleaner.cap_outliers(df_clean, method='iqr')
        
        return df_clean
    
    # ==================== 特征处理 ====================
    
    def _process_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """特征处理"""
        target_col = self.config.target_column
        
        # 先复制并处理
        df_processed = df.copy()
        
        # 1. 生成衍生特征
        df_processed = self.feature_engineer.generate_derived_features(df_processed)
        
        # 2. 编码分类特征（明确排除ID列）
        exclude_cols = ['store_id', 'store_name', 'address']
        categorical_cols = df_processed.select_dtypes(include=['object', 'category']).columns.tolist()
        categorical_cols = [col for col in categorical_cols if col not in exclude_cols and col != target_col]
        
        if categorical_cols:
            df_processed, encoders = self.feature_engineer.encode_categorical_features(
                df_processed, categorical_cols, exclude_columns=exclude_cols
            )
        
        # 3. 明确排除非特征列
        drop_cols = ['store_id', 'store_name', 'address', 'latitude', 'longitude']
        drop_cols = [col for col in drop_cols if col in df_processed.columns]
        df_processed = df_processed.drop(columns=drop_cols, errors='ignore')
        
        # 4. 确保没有NaN值
        df_processed = df_processed.fillna(0)
        
        meta_info = {}
        self.feature_engineer.feature_names = [col for col in df_processed.columns if col != target_col]
        
        return df_processed, meta_info
    
    # ==================== 模型训练 ====================
    
    def _train_models(self, df: pd.DataFrame) -> Dict[str, Any]:
        """训练模型"""
        results = self.model_trainer.train_full_pipeline(
            df,
            target_col=self.config.target_column,
            model_names=["linear", "random_forest", "gbm"],
            do_tuning=False
        )
        
        return results
    
    # ==================== 生成洞察 ====================
    
    def _generate_insights(self, training_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成业务洞察"""
        insights = {}
        
        # 1. 最佳模型信息
        best_model_name = training_result.get('best_model')
        best_score = training_result.get('best_score')
        insights["best_model"] = {
            "name": best_model_name,
            "r2_score": best_score
        }
        
        # 2. 模型对比
        model_comparison = []
        for model_name, scores in training_result.get('test_scores', {}).items():
            model_comparison.append({
                "model": model_name,
                "r2": scores.get('r2'),
                "mae": scores.get('mae'),
                "rmse": scores.get('rmse')
            })
        insights["model_comparison"] = model_comparison
        
        # 3. 特征重要性（如果有）
        if best_model_name and best_model_name in self.model_trainer.feature_importances:
            importances = self.model_trainer.feature_importances[best_model_name]
            sorted_importance = sorted(importances.items(), key=lambda x: x[1], reverse=True)
            
            insights["feature_importance"] = {
                "top_features": sorted_importance[:10],
                "all_features": sorted_importance
            }
        
        # 4. 业务建议
        insights["recommendations"] = self._generate_recommendations(insights)
        
        return insights
    
    def _generate_recommendations(self, insights: Dict) -> List[str]:
        """生成业务建议"""
        recommendations = []
        
        # 基于特征重要性的建议
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
        
        # 模型性能建议
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
    
    # ==================== 保存结果 ====================
    
    def _save_results(
        self,
        output_dir: str,
        training_result: Dict,
        insights: Dict
    ):
        """保存分析结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 1. 保存处理后的数据
        if self.processed_data is not None:
            self.processed_data.to_csv(
                output_path / "processed_data.csv",
                index=False,
                encoding='utf-8-sig'
            )
        
        # 2. 保存最佳模型
        if self.model_trainer.best_model is not None:
            model_path = output_path / "best_model.pkl"
            self.model_trainer.save_best_model(str(model_path))
        
        # 3. 保存洞察报告
        report_path = output_path / "analysis_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(insights, f, ensure_ascii=False, indent=2, default=str)
        
        # 4. 保存人类可读的报告
        human_readable_path = output_path / "analysis_summary.txt"
        self._generate_human_readable_report(insights, human_readable_path)
        
        logger.info(f"Results saved to: {output_path}")
    
    def _generate_human_readable_report(self, insights: Dict, file_path: Path):
        """生成人类可读的报告"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("零售门店选址分析报告\n")
            f.write("=" * 60 + "\n\n")
            
            # 模型表现
            best_model = insights.get('best_model', {})
            f.write(f"【最佳模型】\n")
            f.write(f"模型: {best_model.get('name')}\n")
            f.write(f"R²分数: {best_model.get('r2_score'):.4f}\n\n")
            
            # 特征重要性
            if 'feature_importance' in insights:
                f.write("【重要特征】\n")
                for i, (feature, importance) in enumerate(
                    insights['feature_importance']['top_features'][:8], 1
                ):
                    f.write(f"{i}. {feature}: {importance:.4f}\n")
                f.write("\n")
            
            # 业务建议
            f.write("【业务建议】\n")
            for i, rec in enumerate(insights.get('recommendations', []), 1):
                f.write(f"{i}. {rec}\n")
    
    # ==================== 新店预测 ====================
    
    def predict_new_location(self, new_data: pd.DataFrame) -> pd.DataFrame:
        """
        预测新店的销售额
        
        Args:
            new_data: 新店数据
        
        Returns:
            预测结果
        """
        if self.model_trainer.best_model is None:
            raise ValueError("No trained model available. Please run analysis first.")
        
        # 保存原始数据的非特征列
        id_cols = ['store_id', 'store_name', 'address', 'latitude', 'longitude']
        orig_data = new_data[[col for col in id_cols if col in new_data.columns]].copy()
        
        # 对新数据进行相同的特征处理
        processed, _ = self.feature_engineer.process_features(
            new_data,
            target_col=self.config.target_column,
            generate_derived=True,
            encode_categorical=True,
            standardize=False
        )
        
        # 确保特征一致
        feature_cols = self.feature_engineer.feature_names
        
        # 创建一个包含所有需要特征的DataFrame
        X_new = pd.DataFrame(index=processed.index)
        for col in feature_cols:
            if col in processed.columns:
                X_new[col] = processed[col]
            else:
                X_new[col] = 0
        
        # 确保列顺序一致
        X_new = X_new[feature_cols]
        
        # 预测
        predictions = self.model_trainer.best_model.predict(X_new)
        
        # 合并结果
        result = orig_data.copy()
        result['predicted_sales'] = predictions
        
        # 添加一些关键特征到结果中
        key_features = ['store_area', 'population_1km', 'competitor_count_1km', 'rent_per_sqm']
        for col in key_features:
            if col in new_data.columns:
                result[col] = new_data[col]
        
        return result
