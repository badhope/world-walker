"""
增强版演示脚本：
- 可视化图表
- 数据质量报告
- Excel报告
- 超参数调优
- 增量更新
"""

import sys
from pathlib import Path

root_path = Path(__file__).parent
sys.path.insert(0, str(root_path))

import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

from backend.retail_location import RetailDataAdapter, RetailLocationAnalyzer, RetailLocationConfig


def demo_basic_analysis():
    """基础分析演示"""
    print("\n" + "=" * 80)
    print("1. 基础分析（含可视化）")
    print("=" * 80)

    # 生成数据
    adapter = RetailDataAdapter()
    data = adapter.generate_sample_data(num_stores=150)
    print(f"[ok] 生成数据: {data.shape}")

    # 运行分析
    config = RetailLocationConfig.get_default_config()
    analyzer = RetailLocationAnalyzer(config)
    results = analyzer.run_full_analysis(data, save_results=True, output_dir="data/retail_enhanced")

    # 显示结果
    print("\n[ok] 分析完成！")
    print(f"最佳模型: {results['insights']['best_model']['name']}")
    print(f"R² Score: {results['insights']['best_model']['r2_score']:.4f}")
    print(f"\n生成的可视化: {results['visualizations']}")

    return analyzer, data

def demo_hyperparameter_tuning():
    """超参数调优演示"""
    print("\n" + "=" * 80)
    print("2. 超参数调优演示")
    print("=" * 80)

    # 生成数据
    adapter = RetailDataAdapter()
    data = adapter.generate_sample_data(num_stores=200)

    # 运行带超参数调优的分析
    config = RetailLocationConfig.get_default_config()
    analyzer = RetailLocationAnalyzer(config)

    print("开始超参数调优（可能需要一点时间）...")
    results = analyzer.run_full_analysis(
        data,
        save_results=True,
        output_dir="data/retail_tuning",
        do_hyperparameter_tuning=True,  # 启用超参数调优
    )

    print("\n[ok] 超参数调优完成！")
    print(f"最佳模型: {results['insights']['best_model']['name']}")
    print(f"R² Score: {results['insights']['best_model']['r2_score']:.4f}")

    return analyzer

def demo_incremental_update(analyzer, initial_data):
    """增量更新演示"""
    print("\n" + "=" * 80)
    print("3. 模型增量更新演示")
    print("=" * 80)

    # 生成新数据（模拟后续收集的数据）
    adapter = RetailDataAdapter()
    new_data = adapter.generate_sample_data(num_stores=50)
    print(f"[ok] 生成新数据: {new_data.shape}")

    # 准备新数据用于增量更新
    target_col = analyzer.config.target_column
    processed_new, _ = analyzer._process_features(new_data)

    X_new = processed_new.drop(columns=[target_col])
    y_new = processed_new[target_col]

    # 增量更新模型
    print("正在增量更新模型...")
    updated_model = analyzer.model_trainer.update_model(
        analyzer.model_trainer.best_model,
        X_new,
        y_new,
        method="retrain",  # 重新训练（或者用 "partial" 如果支持）
    )

    # 评估更新后的模型（用新数据测试）
    y_pred = updated_model.predict(X_new)
    from sklearn.metrics import r2_score

    new_r2 = r2_score(y_new, y_pred)

    print("\n[ok] 增量更新完成！")
    print(f"新数据上的R² Score: {new_r2:.4f}")

def demo_prediction(analyzer):
    """预测演示"""
    print("\n" + "=" * 80)
    print("4. 新店预测演示")
    print("=" * 80)

    # 生成预测数据
    adapter = RetailDataAdapter()
    predict_data = adapter.generate_sample_data(num_stores=5)

    # 预测
    predictions = analyzer.predict_new_location(predict_data)

    print("\n[ok] 预测结果：")
    print(predictions[["store_id", "store_area", "predicted_sales"]])

    return predictions

def main():
    print("=" * 80)
    print("零售门店选址分析 - 增强版完整演示")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    try:
        # 1. 基础分析
        analyzer, data = demo_basic_analysis()

        # 2. 预测演示
        demo_prediction(analyzer)

        # 3. 增量更新演示
        demo_incremental_update(analyzer, data)

        # 4. 超参数调优演示（可选，花时间）
        print("\n" + "=" * 80)
        print("提示: 超参数调优需要较多时间，如需演示可取消注释")
        print("=" * 80)
        # demo_hyperparameter_tuning()

        print("\n" + "=" * 80)
        print(" 增强版演示完成！")
        print("=" * 80)
        print("\n生成的文件:")
        print("  - data/retail_enhanced/")
        print("    - processed_data.csv")
        print("    - best_model.pkl")
        print("    - best_model_metadata.json")
        print("    - analysis_report.json")
        print("    - analysis_report.xlsx (Excel报告)")
        print("    - analysis_summary.txt")
        print("    - 可视化图表 (.png)")

    except Exception as e:
        print(f"\n[x] 错误: {e}")
        import traceback

        traceback.print_exc()

if __name__ == "__main__":
    main()
