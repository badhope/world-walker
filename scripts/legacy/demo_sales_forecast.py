"""
销售预测框架演示脚本
"""

import sys
from pathlib import Path

root_path = Path(__file__).parent
sys.path.insert(0, str(root_path))

import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

from backend.sales_forecast import SalesDataAdapter, SalesForecastAnalyzer, SalesForecastConfig


def main():
    print("=" * 80)
    print("Sales Forecast Framework Demo")
    print("=" * 80)

    # 1. 生成模拟数据
    print("\n[Step 1] Generating sample data...")
    adapter = SalesDataAdapter()
    data = adapter.generate_sample_data(num_records=500, num_products=10)
    print(f"Generated data: {data.shape}")
    print("Sample data:")
    print(data.head())

    # 2. 创建分析器并运行
    print("\n[Step 2] Creating analyzer and running full analysis...")
    config = SalesForecastConfig.get_default_config()
    analyzer = SalesForecastAnalyzer(config)
    results = analyzer.run_full_analysis(data, save_results=True, output_dir="data/sales_forecast")

    # 3. 展示结果
    print("\n[Step 3] Displaying analysis results...")
    print("-" * 80)
    best_model = results["insights"]["best_model"]
    print(f"Best Model: {best_model['name']}")
    print(f"R² Score: {best_model['r2_score']:.4f}")

    print("\nModel Comparison:")
    for comp in results["insights"]["model_comparison"]:
        print(f"  - {comp['model']}: R²={comp['r2']:.4f}, MAE={comp['mae']:.2f}, RMSE={comp['rmse']:.2f}")

    if "feature_importance" in results["insights"]:
        print("\nTop 5 Important Features:")
        for i, (feature, importance) in enumerate(results["insights"]["feature_importance"]["top_features"][:5], 1):
            print(f"  {i}. {feature}: {importance:.4f}")

    print("\nRecommendations:")
    for i, rec in enumerate(results["insights"]["recommendations"], 1):
        print(f"  {i}. {rec}")

    # 4. 保存分析器
    print("\n[Step 4] Saving analyzer...")
    analyzer.save_analyzer("data/sales_forecast")
    print("Analyzer saved successfully.")

    # 5. 加载并预测
    print("\n[Step 5] Loading analyzer and predicting...")
    loaded_analyzer = SalesForecastAnalyzer.load_analyzer("data/sales_forecast")

    # 生成新的测试数据
    new_data = adapter.generate_sample_data(num_records=10, num_products=5)
    print(f"Generated new test data: {new_data.shape}")

    # 预测
    predictions = loaded_analyzer.predict(new_data)
    print("\nPredictions:")
    print(predictions[["date", "product_id", "price", "discount", "predicted_sales"]])

    # 6. 总结
    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print("\nResults saved to: data/sales_forecast/")
    print("- processed_data.csv: Processed feature data")
    print("- best_model.pkl: Trained model")
    print("- analysis_report.json: Insights in JSON format")
    print("- analysis_summary.txt: Human-readable summary")

    print("\n 销售预测框架第二个场景演示完成！")
    print("这表明我们的框架可以适用于不同的业务场景！")


if __name__ == "__main__":
    main()
