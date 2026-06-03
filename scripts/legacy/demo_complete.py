import logging
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

from backend.retail_location.analyzer import RetailLocationAnalyzer
from backend.retail_location.config import RetailLocationConfig
from backend.retail_location.data_adapter import RetailDataAdapter


def main():
    print("=" * 80)
    print("National Stats — 国家经济数据分析平台 — 完整演示")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    print("\n" + "=" * 80)
    print("1. 生成示例数据")
    print("=" * 80)

    adapter = RetailDataAdapter()
    data = adapter.generate_sample_data(num_stores=200)
    print(f"数据生成完成: {data.shape}")
    for col in data.columns:
        print(f"  - {col}")

    print("\n" + "=" * 80)
    print("2. 运行完整分析（含超参数调优 + 模型版本保存）")
    print("=" * 80)

    config = RetailLocationConfig.get_default_config()
    analyzer = RetailLocationAnalyzer(config)

    results = analyzer.run_full_analysis(
        data,
        save_results=True,
        output_dir="data/retail_complete",
        do_hyperparameter_tuning=True,
        save_model_version=True,
    )

    print("\n" + "=" * 80)
    print("3. 分析结果")
    print("=" * 80)

    print(f"\n最佳模型: {results['insights']['best_model']['name']}")
    print(f"R²: {results['insights']['best_model']['r2_score']:.4f}")

    print(f"\n数据质量评分: {results['data_quality']['overall_quality']['quality_score']:.1f}/100")
    print(f"评级: {results['data_quality']['overall_quality']['level']}")

    print("\n模型对比:")
    for comp in results["insights"]["model_comparison"]:
        print(f"  - {comp['model']}: R²={comp['r2']:.4f}, MAE={comp['mae']:.0f}")

    print("\nTop 5 重要特征:")
    for i, (feature, importance) in enumerate(results["insights"]["feature_importance"]["top_features"][:5], 1):
        print(f"  {i}. {feature}: {importance:.4f}")

    print("\n业务建议:")
    for i, rec in enumerate(results["insights"]["recommendations"][:3], 1):
        print(f"  {i}. {rec}")

    print("\n可视化图表:")
    for name, path in results.get("visualizations", {}).items():
        print(f"  - {name}: {path}")

    print("\n" + "=" * 80)
    print("4. 预测新店")
    print("=" * 80)

    new_store_data = adapter.generate_sample_data(num_stores=5)
    predictions = analyzer.predict(new_store_data)

    print("\n预测结果:")
    print(predictions[["store_id", "store_area", "predicted_sales"]])

    print("\n" + "=" * 80)
    print("5. 保存分析器")
    print("=" * 80)

    analyzer.save_analyzer("data/retail_complete/saved_analyzer")
    print("分析器已保存")

    print("\n" + "=" * 80)
    print("6. 加载分析器并再次预测")
    print("=" * 80)

    loaded_analyzer = RetailLocationAnalyzer.load_analyzer("data/retail_complete/saved_analyzer")
    print("分析器加载成功")

    another_new_store = adapter.generate_sample_data(num_stores=3)
    new_predictions = loaded_analyzer.predict(another_new_store)
    print("\n再次预测成功:")
    print(new_predictions[["store_id", "store_area", "predicted_sales"]])

    print("\n" + "=" * 80)
    print("7. 生成文件")
    print("=" * 80)

    output_dir = Path("data/retail_complete")
    if output_dir.exists():
        for f in sorted(output_dir.iterdir()):
            if f.is_file():
                print(f"  - {f.name}")
            elif f.is_dir():
                print(f"  - {f.name}/")
                for subf in sorted(f.iterdir()):
                    if subf.is_file():
                        print(f"    - {subf.name}")

    print("\n💡 提示:")
    print("  - 查看 analysis_summary.txt 获取文本报告")
    print("  - 查看 analysis_report.xlsx 查看 Excel 报告")
    print("  - 查看 analysis_report.json 查看 JSON 报告")
    print("  - 查看 analysis_report.pdf 查看 PDF 报告")
    print("  - 查看 .png 文件获取可视化图表")

    print("\n" + "=" * 80)
    print("演示完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()
