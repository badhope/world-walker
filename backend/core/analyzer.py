"""
Generic analyzer — ties config, data loading, and ML into one workflow.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..ml.models import get_available_models
from ..ml.trainer import AutoML, TrainingResult
from .config import get_config_manager
from .data_manager import Dataset, get_data_manager

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """分析结果"""

    project_name: str
    dataset: Dataset
    benchmarks: dict[str, Any]
    ml_result: TrainingResult | None = None
    insights: list[dict[str, Any]] = None
    recommendations: list[str] = None


class UniversalAnalyzer:
    """通用分析器 - 一站式分析解决方案"""

    def __init__(self, config_name: str = "default", config_dir: str | None = None, data_dir: str | None = None):
        self.config_manager = get_config_manager(config_dir)
        self.config = self.config_manager.load_config(config_name)
        self.data_manager = get_data_manager(data_dir)
        self.dataset: Dataset | None = None
        self.result: AnalysisResult | None = None

        logger.info(f"UniversalAnalyzer initialized: {self.config.project_name}")

    def load_data(self, data_source: str, source_type: str = "csv", **kwargs) -> Dataset:
        """加载数据"""
        if source_type == "csv":
            self.dataset = self.data_manager.load_csv(data_source, **kwargs)
        elif source_type == "excel":
            self.dataset = self.data_manager.load_excel(data_source, **kwargs)
        elif source_type == "json":
            self.dataset = self.data_manager.load_json(data_source, **kwargs)
        elif source_type == "database":
            self.dataset = self.data_manager.load_database(data_source, **kwargs)
        else:
            raise ValueError(f"Unknown source type: {source_type}")

        logger.info(f"Data loaded: {self.dataset.name}, {len(self.dataset.data)} records")
        return self.dataset

    def load_data_from_dataframe(
        self,
        df: pd.DataFrame,
        name: str = "dataset",
        id_column: str = "region_id",
        name_column: str = "region_name",
        year_column: str = "year",
        source_column: str = "source",
    ) -> Dataset:
        """从DataFrame加载数据"""
        df_processed = df.copy()

        # 确保必需列存在
        if id_column not in df_processed.columns:
            df_processed[id_column] = range(len(df_processed))
        if name_column not in df_processed.columns:
            df_processed[name_column] = [f"Region_{i}" for i in range(len(df_processed))]
        if year_column not in df_processed.columns:
            df_processed[year_column] = 2025
        if source_column not in df_processed.columns:
            df_processed[source_column] = "direct"

        # 重命名列
        df_processed = df_processed.rename(
            columns={id_column: "region_id", name_column: "region_name", year_column: "year", source_column: "source"}
        )

        self.dataset = Dataset.from_dataframe(df_processed, name=name)
        logger.info(f"Data loaded from DataFrame: {len(self.dataset.data)} records")
        return self.dataset

    def preprocess_data(self, clean: bool = True, normalize: bool = False, **kwargs) -> Dataset:
        """数据预处理"""
        if self.dataset is None:
            raise ValueError("No data loaded yet")

        processed = self.dataset

        if clean:
            processed = self.data_manager.clean_data(processed, **kwargs)

        if normalize:
            processed = self.data_manager.normalize_data(processed, **kwargs)

        self.dataset = processed
        return self.dataset

    def calculate_benchmarks(self) -> dict[str, Any]:
        """计算基准值"""
        if self.dataset is None:
            raise ValueError("No data loaded yet")

        df = self.dataset.to_dataframe()
        benchmarks = {}

        for metric in self.config.industry.data_requirements:
            if metric in df.columns:
                benchmarks[metric] = self.data_manager.calculate_benchmarks(self.dataset, metric)

        return benchmarks

    def run_ml_analysis(
        self,
        target_column: str | None = None,
        feature_columns: list[str] | None = None,
        model_names: list[str] | None = None,
        time_column: str | None = None,
        **kwargs,
    ) -> TrainingResult:
        """运行机器学习分析"""
        if self.dataset is None:
            raise ValueError("No data loaded yet")

        df = self.dataset.to_dataframe()

        # 使用配置或提供的参数
        target = target_column or self.config.ml_config.target_metric
        features = feature_columns or self.config.ml_config.feature_columns
        models = model_names or self.config.ml_config.models
        time_col = time_column or self.config.ml_config.time_column

        # 确保所有特征列存在
        available_features = [f for f in features if f in df.columns]
        if not available_features:
            raise ValueError(f"No feature columns found: {features}")

        logger.info(f"Running ML analysis: target={target}, features={available_features}")

        # 创建AutoML
        automl = AutoML(
            target_column=target, feature_columns=available_features, model_names=models, time_column=time_col, **kwargs
        )

        # 训练
        result = automl.fit(df)

        logger.info(f"ML analysis complete. Best model: {result.best_model.model_name}")
        return result

    def generate_insights(self) -> list[dict[str, Any]]:
        """生成洞察"""
        if self.dataset is None:
            raise ValueError("No data loaded yet")

        df = self.dataset.to_dataframe()
        insights = []

        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            mean_val = df[col].mean()
            std_val = df[col].std()

            insights.append(
                {
                    "metric": col,
                    "type": "statistical",
                    "mean": mean_val,
                    "std": std_val,
                    "min": df[col].min(),
                    "max": df[col].max(),
                }
            )

        return insights

    def analyze(self, run_ml: bool = True, **kwargs) -> AnalysisResult:
        """完整分析流程"""
        if self.dataset is None:
            raise ValueError("No data loaded yet")

        logger.info("Starting full analysis...")

        # 1. 预处理
        self.preprocess_data()

        # 2. 计算基准
        benchmarks = self.calculate_benchmarks()

        # 3. 机器学习
        ml_result = None
        if run_ml:
            try:
                ml_result = self.run_ml_analysis(**kwargs)
            except Exception as e:
                logger.error(f"ML analysis failed: {e}", exc_info=True)

        # 4. 生成洞察
        insights = self.generate_insights()

        # 5. 生成建议
        recommendations = self._generate_recommendations(insights, ml_result)

        self.result = AnalysisResult(
            project_name=self.config.project_name,
            dataset=self.dataset,
            benchmarks=benchmarks,
            ml_result=ml_result,
            insights=insights,
            recommendations=recommendations,
        )

        logger.info("Analysis complete!")
        return self.result

    def _generate_recommendations(self, insights: list[dict], ml_result: TrainingResult | None) -> list[str]:
        """生成建议"""
        recommendations = []

        if ml_result:
            recommendations.append(
                f"最佳预测模型: {ml_result.best_model.model_name} (R² = {ml_result.best_model.metrics.r2:.4f})"
            )

        return recommendations

    def save_result(self, output_dir: str = "./output"):
        """保存结果"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)

        if self.dataset:
            self.data_manager.save_dataset(self.dataset)

        if self.result and self.result.ml_result:
            # 保存模型对比
            comparison_data = []
            for model_res in self.result.ml_result.all_results:
                comparison_data.append(
                    {
                        "model": model_res.model_name,
                        "mae": model_res.metrics.mae,
                        "rmse": model_res.metrics.rmse,
                        "mape": model_res.metrics.mape,
                        "r2": model_res.metrics.r2,
                    }
                )

            import pandas as pd

            comparison_df = pd.DataFrame(comparison_data)
            comparison_df.to_csv(output_path / "model_comparison.csv", index=False)

        logger.info(f"Results saved to {output_dir}")


def create_sample_data(n_regions: int = 10, n_years: int = 5, seed: int = 42) -> pd.DataFrame:
    """创建示例数据用于演示"""
    np.random.seed(seed)

    regions = [f"Region_{i:02d}" for i in range(n_regions)]
    years = list(range(2020, 2020 + n_years))

    data = []
    for region in regions:
        for year in years:
            base_val = regions.index(region) * 10
            data.append(
                {
                    "region_id": region,
                    "region_name": region,
                    "year": year,
                    "source": "sample",
                    "land_price": 500 + base_val + np.random.normal(0, 50),
                    "labor_cost": 3000 + base_val * 50 + np.random.normal(0, 200),
                    "energy_cost": 0.8 + base_val * 0.02 + np.random.normal(0, 0.1),
                    "market_size": 100 + base_val * 2 + (year - 2020) * 10 + np.random.normal(0, 20),
                    "talent_pool": 50 + base_val + np.random.normal(0, 10),
                    "infrastructure": 70 + base_val * 0.5 + np.random.normal(0, 10),
                    "tax_incentive": 5 + base_val * 0.3 + np.random.normal(0, 1),
                    "subsidy": 3 + base_val * 0.2 + np.random.normal(0, 0.5),
                    "approval_efficiency": 10 - base_val * 0.5 + np.random.normal(0, 1),
                }
            )

    return pd.DataFrame(data)


def quick_start_demo():
    """快速开始演示"""
    print("=" * 80)
    print("通用分析器 - 快速开始演示")
    print("=" * 80)

    # 1. 创建分析器
    analyzer = UniversalAnalyzer()
    print(f"\n✓ 项目配置已加载: {analyzer.config.project_name}")
    print(f"✓ 行业: {analyzer.config.industry.industry_name}")
    print(f"✓ 可用模型: {get_available_models()}")

    # 2. 创建并加载示例数据
    sample_df = create_sample_data()
    dataset = analyzer.load_data_from_dataframe(sample_df, name="sample_data")
    print(f"\n✓ 示例数据已加载: {len(dataset.data)} 条记录")
    print("✓ 数据列:", sample_df.columns.tolist())

    # 3. 运行分析
    print(f"\n{'=' * 80}")
    print("开始完整分析...")
    print(f"{'=' * 80}")

    result = analyzer.analyze(
        run_ml=True,
        target_column="market_size",
        feature_columns=["land_price", "labor_cost", "energy_cost", "talent_pool", "infrastructure"],
        model_names=["linear_regression", "random_forest", "gbdt"],
        hyperparameter_tuning=False,
        test_size=0.2,
    )

    # 4. 展示结果
    print(f"\n{'=' * 80}")
    print("分析结果")
    print(f"{'=' * 80}")

    if result.ml_result:
        # 构建模型对比表
        print("\n模型对比:")
        comparison_data = []
        for model_res in result.ml_result.all_results:
            comparison_data.append(
                {
                    "Model": model_res.model_name,
                    "R²": f"{model_res.metrics.r2:.4f}",
                    "MAE": f"{model_res.metrics.mae:.4f}",
                    "RMSE": f"{model_res.metrics.rmse:.4f}",
                    "MAPE": f"{model_res.metrics.mape:.4f}",
                }
            )

        # 简单打印表格
        print(f"{'Model':<20} {'R²':<10} {'MAE':<10} {'RMSE':<10} {'MAPE':<10}")
        print("-" * 60)
        for row in comparison_data:
            print(f"{row['Model']:<20} {row['R²']:<10} {row['MAE']:<10} {row['RMSE']:<10} {row['MAPE']:<10}")

        best = result.ml_result.best_model
        print(f"\n最佳模型: {best.model_name}")
        print(f"  R²: {best.metrics.r2:.4f}")
        print(f"  MAE: {best.metrics.mae:.4f}")
        print(f"  MAPE: {best.metrics.mape:.4f}")

        if best.feature_importance:
            print("\n特征重要性:")
            for feat, imp in sorted(best.feature_importance.items(), key=lambda x: x[1], reverse=True):
                print(f"  {feat}: {imp:.4f}")

    # 5. 保存结果
    analyzer.save_result()
    print(f"\n{'=' * 80}")
    print("✓ 分析完成！结果已保存。")
    print("=" * 80)

    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    quick_start_demo()
