"""
完整演示 - 展示所有功能
"""
import sys
from pathlib import Path

root_path = Path(__file__).parent
sys.path.insert(0, str(root_path))

import pandas as pd
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from backend.retail_location import RetailLocationConfig, RetailDataAdapter, RetailLocationAnalyzer


def main():
    print("=" * 80)
    print("通用数据分析框架 - 完整演示")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # ---------------------------
    # 1. 生成示例数据
    # ---------------------------
    print("\n" + "=" * 80)
    print("1. 生成示例数据")
    print("=" * 80)
    
    adapter = RetailDataAdapter()
    data = adapter.generate_sample_data(num_stores=200)
    print(f"✅ 数据生成完成: {data.shape}")
    print("数据列:")
    for col in data.columns:
        print(f"  - {col}")
    
    # ---------------------------
    # 2. 运行完整分析
    # ---------------------------
    print("\n" + "=" * 80)
    print("2. 运行完整分析（含可视化和报告）")
    print("=" * 80)
    
    config = RetailLocationConfig.get_default_config()
    analyzer = RetailLocationAnalyzer(config)
    
    results = analyzer.run_full_analysis(
        data,
        save_results=True,
        output_dir="data/retail_complete",
        do_hyperparameter_tuning=True,  # 启用超参数调优
        save_model_version=True  # 保存模型版本
    )
    
    # ---------------------------
    # 3. 展示结果
    # ---------------------------
    print("\n" + "=" * 80)
    print("3. 分析结果")
    print("=" * 80)
    
    print(f"\n✅ 最佳模型: {results['insights']['best_model']['name']}")
    print(f"✅ R² 分数: {results['insights']['best_model']['r2_score']:.4f}")
    
    print(f"\n📊 数据质量评分: {results['data_quality']['overall_quality']['quality_score']:.1f}/100")
    print(f"   评级: {results['data_quality']['overall_quality']['rating']}")
    
    print("\n📈 模型对比:")
    for comp in results['insights']['model_comparison']:
        print(f"  - {comp['model']}: R²={comp['r2']:.4f}, MAE={comp['mae']:.0f}")
    
    print("\n🔑 Top 5 重要特征:")
    for i, (feature, importance) in enumerate(results['insights']['feature_importance']['top_features'][:5], 1):
        print(f"  {i}. {feature}: {importance:.4f}")
    
    print("\n💡 业务建议:")
    for i, rec in enumerate(results['insights']['recommendations'][:3], 1):
        print(f"  {i}. {rec}")
    
    print("\n📊 可视化图表:")
    for name, path in results.get('visualizations', {}).items():
        print(f"  - {name}: {path}")
    
    # ---------------------------
    # 4. 预测新店
    # ---------------------------
    print("\n" + "=" * 80)
    print("4. 预测新店销售额")
    print("=" * 80)
    
    new_store_data = adapter.generate_sample_data(num_stores=5)
    predictions = analyzer.predict_new_location(new_store_data)
    
    print("\n✅ 预测结果:")
    print(predictions[['store_id', 'store_area', 'predicted_sales']])
    
    # ---------------------------
    # 5. 保存分析器
    # ---------------------------
    print("\n" + "=" * 80)
    print("5. 保存分析器")
    print("=" * 80)
    
    analyzer.save_analyzer("data/retail_complete/saved_analyzer")
    print("✅ 分析器已保存")
    
    # ---------------------------
    # 6. 加载分析器并再次预测
    # ---------------------------
    print("\n" + "=" * 80)
    print("6. 加载分析器并再次预测")
    print("=" * 80)
    
    loaded_analyzer = RetailLocationAnalyzer.load_analyzer("data/retail_complete/saved_analyzer")
    print("✅ 分析器加载成功")
    
    # 生成新数据
    another_new_store = adapter.generate_sample_data(num_stores=3)
    new_predictions = loaded_analyzer.predict_new_location(another_new_store)
    
    print("\n✅ 再次预测成功:")
    print(new_predictions[['store_id', 'store_area', 'predicted_sales']])
    
    # ---------------------------
    # 完成
    # ---------------------------
    print("\n" + "=" * 80)
    print("🎉 完整演示完成！")
    print("=" * 80)
    
    print("\n📁 生成的文件:")
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
    print("  - 查看 analysis_summary.txt 获取报告概述")
    print("  - 查看 analysis_report.xlsx 获取详细报告")
    print("  - 查看 .png 文件获取可视化图表")
    print("  - 查看 best_model.pkl 获取训练好的模型")
    print("\n✅ 所有任务已完成！")


if __name__ == "__main__":
    main()
