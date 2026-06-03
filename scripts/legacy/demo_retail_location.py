"""
零售门店选址分析 - 完整演示脚本
"""

import logging
import sys

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", stream=sys.stdout
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 70)
    logger.info("零售门店选址分析 - 完整演示")
    logger.info("=" * 70)

    # 导入模块（放在函数内部，避免循环导入）
    from backend.retail_location import RetailDataAdapter, RetailLocationAnalyzer, RetailLocationConfig

    # ============================================
    # 步骤1: 生成示例数据
    # ============================================
    logger.info("\n" + "=" * 70)
    logger.info("步骤1: 生成模拟零售门店数据")
    logger.info("=" * 70)

    data_adapter = RetailDataAdapter()
    sample_data = data_adapter.generate_sample_data(num_stores=100)

    logger.info(f"\n生成数据形状: {sample_data.shape}")
    logger.info("\n数据预览:")
    logger.info(
        sample_data[["store_id", "store_area", "population_1km", "competitor_count_1km", "monthly_sales"]].head()
    )

    logger.info("\n目标变量(月销售额)统计:")
    logger.info(sample_data["monthly_sales"].describe())

    # ============================================
    # 步骤2: 创建分析器并运行完整分析
    # ============================================
    logger.info("\n" + "=" * 70)
    logger.info("步骤2: 运行完整的选址分析流程")
    logger.info("=" * 70)

    config = RetailLocationConfig.get_default_config()
    analyzer = RetailLocationAnalyzer(config)

    results = analyzer.run_full_analysis(sample_data, save_results=True, output_dir="data/retail_analysis")

    # ============================================
    # 步骤3: 展示分析结果
    # ============================================
    logger.info("\n" + "=" * 70)
    logger.info("步骤3: 分析结果摘要")
    logger.info("=" * 70)

    # 最佳模型
    insights = results.get("insights", {})
    best_model = insights.get("best_model", {})

    logger.info(f"\n[ok] 最佳模型: {best_model.get('name')}")
    logger.info(f"[i] R²分数: {best_model.get('r2_score'):.4f}")

    # 模型对比
    logger.info("\n[+] 各模型对比:")
    for mc in insights.get("model_comparison", []):
        logger.info(f"  - {mc['model']}: R²={mc['r2']:.4f}, MAE={mc['mae']:.0f}, RMSE={mc['rmse']:.0f}")

    # 特征重要性
    if "feature_importance" in insights:
        logger.info("\n[*] Top 10 重要特征:")
        for i, (feature, importance) in enumerate(insights["feature_importance"]["top_features"][:10], 1):
            logger.info(f"  {i}. {feature}: {importance:.4f}")

    # 业务建议
    logger.info("\n[i] 业务建议:")
    for i, rec in enumerate(insights.get("recommendations", [])[:5], 1):
        logger.info(f"  {i}. {rec}")

    # ============================================
    # 步骤4: 总结项目成果
    # ============================================
    logger.info("\n" + "=" * 70)
    logger.info("步骤4: 项目成果总结")
    logger.info("=" * 70)

    logger.info("\n[ok] 核心功能实现:")
    logger.info("  1. 多源数据适配(CSV/Excel/JSON/DataFrame)")
    logger.info("  2. 数据清洗(缺失值/异常值处理)")
    logger.info("  3. 特征工程(衍生特征/编码/标准化)")
    logger.info("  4. 多种算法自动训练对比")
    logger.info("  5. 特征重要性分析")
    logger.info("  6. 业务洞察生成")

    logger.info("\n 技术亮点:")
    logger.info("  - 模块化设计，易于扩展")
    logger.info("  - 配置驱动，灵活适配不同业务")
    logger.info("  - 完整的日志记录")
    logger.info("  - 支持模型增量更新")

    logger.info("\n[+] 本次运行成果:")
    logger.info(f"  - 训练样本数: {len(sample_data)}")
    logger.info(f"  - 特征数: {len(analyzer.feature_engineer.feature_names)}")
    logger.info(f"  - 最佳模型: {best_model.get('name')}")
    logger.info(f"  - 模型R²: {best_model.get('r2_score'):.4f}")

    # ============================================
    # 总结
    # ============================================
    logger.info("\n" + "=" * 70)
    logger.info("演示完成！")
    logger.info("=" * 70)

    logger.info("\n 结果已保存到: data/retail_analysis/")
    logger.info("   - processed_data.csv: 处理后的数据")
    logger.info("   - best_model.pkl: 训练好的模型")
    logger.info("   - analysis_report.json: 分析报告(JSON)")
    logger.info("   - analysis_summary.txt: 分析摘要(可读)")

    logger.info("\n" + "=" * 70)
    logger.info("下一步建议:")
    logger.info("=" * 70)
    logger.info("1. 替换示例数据为真实业务数据")
    logger.info("2. 根据业务调整特征工程")
    logger.info("3. 收集更多历史数据以提升模型精度")
    logger.info("4. 建立定期模型更新机制")


if __name__ == "__main__":
    main()
