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

logger = logging.getLogger(__name__)


class RetailLocationAnalyzer:
    """零售门店选址分析器"""
    
    def __init__(self, config: Optional[RetailLocationConfig] = None):
        self.config = config or RetailLocationConfig.get_default_config()
        self.data_adapter = RetailDataAdapter(self.config)
        self.data_cleaner = DataCleaner()
        self.feature_engineer = FeatureEngineer(self.config)
        self.model_trainer = RetailModelTrainer(self.config)
        self.visualizer = None
        
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
        do_hyperparameter_tuning: bool = False
    ) -> Dict[str, Any]:
        """
        运行完整的分析流程
        
        Args:
            data: 输入数据
            save_results: 是否保存结果
            output_dir: 输出目录
            do_hyperparameter_tuning: 是否进行超参数调优
        
        Returns:
            分析结果
        """
        logger.info("=" * 60)
        logger.info("Starting Retail Location Analysis")
        logger.info("=" * 60)
        
        self.raw_data = data.copy()
        self.visualizer = RetailVisualizer(output_dir)
        
        # 1. 数据验证
        logger.info("\n[1/7] Validating data...")
        data_quality_report = self._data_quality_check(data)
        
        # 2. 数据清洗
        logger.info("\n[2/7] Cleaning data...")
        self.cleaned_data = self._clean_data(data)
        
        # 3. 特征工程
        logger.info("\n[3/7] Engineering features...")
        self.processed_data, feature_meta = self._process_features(self.cleaned_data)
        
        # 4. 模型训练
        logger.info("\n[4/7] Training models...")
        training_result = self._train_models(self.processed_data, do_hyperparameter_tuning)
        
        # 5. 生成预测结果用于可视化
        if self.model_trainer.best_model and self.X_test is not None:
            self.y_pred = self.model_trainer.predict(self.X_test)
        
        # 6. 生成洞察和可视化
        logger.info("\n[5/7] Generating insights...")
        insights = self._generate_insights(training_result)
        
        logger.info("\n[6/7] Generating visualizations...")
        visualizations = self._generate_visualizations()
        
        # 7. 保存结果
        if save_results:
            logger.info("\n[7/7] Saving results...")
            self._save_results(output_dir, training_result, insights, data_quality_report)
        
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
    
    # ==================== 分析器持久化 ====================
    
    def save_analyzer(self, output_dir: str):
        """保存整个分析器（模型+元数据）"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 保存最佳模型
        if self.model_trainer.best_model is not None:
            self.model_trainer.save_best_model(str(output_path / "best_model.pkl"))
        
        # 保存配置和处理后的特征信息
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
    def load_analyzer(cls, input_dir: str) -> 'RetailLocationAnalyzer':
        """加载保存的分析器"""
        input_path = Path(input_dir)
        
        # 加载元数据
        with open(input_path / "analyzer_meta.json", 'r', encoding='utf-8') as f:
            meta = json.load(f)
        
        # 创建配置
        config = RetailLocationConfig(
            target_column=meta.get("target_col", "monthly_sales")
        )
        
        # 创建分析器
        analyzer = cls(config)
        
        # 加载模型
        model_path = input_path / "best_model.pkl"
        if model_path.exists():
            analyzer.model_trainer.load_model(str(model_path))
        
        # 恢复特征信息
        analyzer.model_trainer.feature_names = meta.get("feature_names", [])
        
        logger.info(f"Analyzer loaded from: {input_path}")
        return analyzer
    
    # ==================== 新店预测 ====================
    
    def predict_new_location(self, new_data: pd.DataFrame) -> pd.DataFrame:
        """
        预测新店的销售额
        
        Args:
            new_data: 新店数据
        
        Returns:
            预测结果
        """
        if not self.model_trainer.is_trained or self.model_trainer.best_model is None:
            raise ValueError("No trained model available. Please run analysis first.")
        
        # 保存原始数据的非特征列
        id_cols = ['store_id', 'store_name', 'address', 'latitude', 'longitude']
        orig_data = new_data[[col for col in id_cols if col in new_data.columns]].copy()
        
        # 数据清洗（同训练时）
        cleaned_data = self._clean_data(new_data)
        
        # 特征处理（同训练时）
        processed, _ = self._process_features(cleaned_data)
        
        # 移除目标列（如果存在）
        target_col = self.config.target_column
        if target_col in processed.columns:
            processed = processed.drop(columns=[target_col])
        
        # 使用模型训练器的预测功能（自动处理特征一致性）
        predictions = self.model_trainer.predict(processed)
        
        # 合并结果
        result = orig_data.copy()
        result['predicted_sales'] = predictions
        
        # 添加一些关键特征到结果中
        key_features = ['store_area', 'population_1km', 'competitor_count_1km', 'rent_per_sqm']
        for col in key_features:
            if col in new_data.columns:
                result[col] = new_data[col]
        
        return result
    
    # ==================== 数据质量检查 ====================
    
    def _data_quality_check(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        增强版数据质量检查
        
        Args:
            df: 输入数据
        
        Returns:
            数据质量报告
        """
        report = {}
        
        # 1. 基本信息
        report["basic_info"] = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / (1024 * 1024)
        }
        
        # 2. 缺失值统计
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
        
        # 3. 重复值检查
        duplicate_count = df.duplicated().sum()
        report["duplicates"] = {
            "total_duplicates": int(duplicate_count),
            "duplicate_percent": float((duplicate_count / len(df)) * 100)
        }
        
        # 4. 数据类型检查
        dtype_summary = {}
        for col in df.columns:
            dtype_name = str(df[col].dtype)
            if dtype_name not in dtype_summary:
                dtype_summary[dtype_name] = []
            dtype_summary[dtype_name].append(col)
        report["data_types"] = dtype_summary
        
        # 5. 异常值检测（数值列）
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        outlier_report = {}
        for col in numeric_cols:
            data = df[col].dropna()
            if len(data) == 0:
                continue
            
            # 使用IQR方法检测异常值
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
        
        # 6. 总体评分
        total_issues = (
            missing_stats.sum() +
            duplicate_count +
            sum(o.get("outlier_count", 0) for o in outlier_report.values())
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
    
    # ==================== 模型训练（增强版） ====================
    
    def _train_models(self, df: pd.DataFrame, do_tuning: bool = False) -> Dict[str, Any]:
        """
        训练模型，支持超参数调优
        
        Args:
            df: 处理后的数据
            do_tuning: 是否进行超参数调优
        
        Returns:
            训练结果
        """
        target_col = self.config.target_column
        
        # 准备数据
        X_train, X_test, y_train, y_test = self.model_trainer.prepare_data(
            df, target_col
        )
        
        # 保存测试数据用于可视化
        self.X_test = X_test
        self.y_test = y_test
        
        # 训练模型
        if do_tuning:
            logger.info("启用超参数调优...")
            results = self.model_trainer.train_full_pipeline(
                df, target_col, do_tuning=True
            )
        else:
            results = self.model_trainer.train_full_pipeline(
                df, target_col, do_tuning=False
            )
        
        return results
    
    # ==================== 可视化生成 ====================
    
    def _generate_visualizations(self) -> Dict[str, str]:
        """
        生成所有可视化图表
        
        Returns:
            图表路径字典
        """
        if self.visualizer is None:
            return {}
        
        visualizations = {}
        
        # 1. 特征重要性图
        if self.model_trainer.best_model_name in self.model_trainer.feature_importances:
            fi = self.model_trainer.feature_importances[self.model_trainer.best_model_name]
            plot_path = self.visualizer.plot_feature_importance(fi)
            if plot_path:
                visualizations["feature_importance"] = str(plot_path)
        
        # 2. 模型对比图
        if self.model_trainer.model_scores:
            plot_path = self.visualizer.plot_model_comparison(self.model_trainer.model_scores)
            if plot_path:
                visualizations["model_comparison"] = str(plot_path)
        
        # 3. 预测vs实际值图
        if self.y_test is not None and self.y_pred is not None:
            plot_path = self.visualizer.plot_predicted_vs_actual(self.y_test, self.y_pred)
            if plot_path:
                visualizations["pred_vs_actual"] = str(plot_path)
        
        # 4. 销售额分布图
        if self.raw_data is not None and self.config.target_column in self.raw_data.columns:
            sales_data = self.raw_data[self.config.target_column].dropna()
            if len(sales_data) > 0:
                plot_path = self.visualizer.plot_sales_distribution(sales_data)
                if plot_path:
                    visualizations["sales_distribution"] = str(plot_path)
        
        # 5. 相关性热力图
        if self.processed_data is not None:
            plot_path = self.visualizer.plot_correlation_heatmap(self.processed_data)
            if plot_path:
                visualizations["correlation_heatmap"] = str(plot_path)
        
        logger.info(f"生成了 {len(visualizations)} 个可视化图表")
        return visualizations
    
    # ==================== 保存结果（增强版） ====================
    
    def _save_results(
        self,
        output_dir: str,
        training_result: Dict,
        insights: Dict,
        data_quality_report: Dict
    ):
        """
        保存结果，支持Excel导出
        
        Args:
            output_dir: 输出目录
            training_result: 训练结果
            insights: 洞察结果
            data_quality_report: 数据质量报告
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 1. 保存处理后的数据（CSV）
        if self.processed_data is not None:
            self.processed_data.to_csv(
                output_path / "processed_data.csv",
                index=False,
                encoding='utf-8-sig'
            )
        
        # 2. 保存模型
        if self.model_trainer.best_model is not None:
            self.model_trainer.save_best_model(str(output_path / "best_model.pkl"))
        
        # 3. 保存JSON报告
        full_report = {
            "data_quality": data_quality_report,
            "insights": insights,
            "timestamp": str(pd.Timestamp.now())
        }
        
        with open(output_path / "analysis_report.json", 'w', encoding='utf-8') as f:
            json.dump(full_report, f, ensure_ascii=False, indent=2, default=str)
        
        # 4. 保存Excel报告（新增）
        try:
            self._save_excel_report(output_path, insights, data_quality_report)
        except Exception as e:
            logger.warning(f"Excel报告保存失败: {e}")
        
        # 5. 保存人类可读的报告
        self._generate_human_readable_report(insights, data_quality_report, 
                                          output_path / "analysis_summary.txt")
    
    def _save_excel_report(self, output_path: Path, insights: Dict, data_quality_report: Dict):
        """
        保存Excel格式报告
        
        Args:
            output_path: 输出目录
            insights: 洞察结果
            data_quality_report: 数据质量报告
        """
        excel_path = output_path / "analysis_report.xlsx"
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # 1. 数据质量页
            dq_data = [
                ["指标", "值"],
                ["总行数", data_quality_report["basic_info"]["total_rows"]],
                ["总列数", data_quality_report["basic_info"]["total_columns"]],
                ["内存使用(MB)", f"{data_quality_report['basic_info']['memory_usage_mb']:.2f}"],
                ["缺失单元格总数", data_quality_report["missing_values"]["total_missing_cells"]],
                ["重复行数", data_quality_report["duplicates"]["total_duplicates"]],
                ["数据质量评分", f"{data_quality_report['overall_quality']['quality_score']:.1f}/100"],
                ["质量等级", data_quality_report['overall_quality']['rating']]
            ]
            pd.DataFrame(dq_data[1:], columns=dq_data[0]).to_excel(
                writer, sheet_name='数据质量', index=False
            )
            
            # 2. 模型对比页
            if "model_comparison" in insights:
                model_df = pd.DataFrame(insights["model_comparison"])
                model_df.to_excel(writer, sheet_name='模型对比', index=False)
            
            # 3. 特征重要性页
            if "feature_importance" in insights:
                fi_df = pd.DataFrame(
                    insights["feature_importance"]["all_features"],
                    columns=["特征", "重要性"]
                )
                fi_df.to_excel(writer, sheet_name='特征重要性', index=False)
            
            # 4. 业务建议页
            if "recommendations" in insights:
                rec_df = pd.DataFrame(
                    enumerate(insights["recommendations"], 1),
                    columns=["序号", "建议"]
                )
                rec_df.to_excel(writer, sheet_name='业务建议', index=False)
            
            # 5. 数据预览
            if self.processed_data is not None:
                self.processed_data.head(50).to_excel(
                    writer, sheet_name='数据预览', index=False
                )
        
        logger.info(f"Excel报告已保存至: {excel_path}")
    
    def _generate_human_readable_report(
        self,
        insights: Dict,
        data_quality_report: Dict,
        file_path: Path
    ):
        """
        生成人类可读的报告
        
        Args:
            insights: 洞察结果
            data_quality_report: 数据质量报告
            file_path: 保存路径
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("零售门店选址分析报告\n")
            f.write("=" * 80 + "\n\n")
            
            # 1. 数据质量
            f.write("【数据质量报告】\n")
            f.write(f"数据质量评分: {data_quality_report['overall_quality']['quality_score']:.1f}/100\n")
            f.write(f"质量等级: {data_quality_report['overall_quality']['rating']}\n")
            f.write(f"总行数: {data_quality_report['basic_info']['total_rows']}\n")
            f.write(f"总列数: {data_quality_report['basic_info']['total_columns']}\n")
            f.write(f"缺失单元格: {data_quality_report['missing_values']['total_missing_cells']}\n\n")
            
            # 2. 最佳模型
            best_model = insights.get('best_model', {})
            f.write("【最佳模型】\n")
            f.write(f"模型: {best_model.get('name', 'N/A')}\n")
            f.write(f"R² Score: {best_model.get('r2_score', 0):.4f}\n\n")
            
            # 3. 模型对比
            if "model_comparison" in insights:
                f.write("【模型对比】\n")
                for item in insights["model_comparison"]:
                    f.write(f"  - {item['model']}: R²={item['r2']:.4f}, MAE={item['mae']:.2f}\n")
                f.write("\n")
            
            # 4. 特征重要性
            if "feature_importance" in insights:
                f.write("【Top 10 重要特征】\n")
                for i, (feature, importance) in enumerate(
                    insights["feature_importance"]["top_features"][:10], 1
                ):
                    f.write(f"{i}. {feature}: {importance:.4f}\n")
                f.write("\n")
            
            # 5. 业务建议
            f.write("【业务建议】\n")
            for i, rec in enumerate(insights.get('recommendations', []), 1):
                f.write(f"{i}. {rec}\n")
